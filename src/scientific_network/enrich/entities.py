"""E2 steps 2-5: verified mentions, normalization, surface-form merging, node threshold (specification §4.2).

Inputs are the encoder output, the SLM verification output and the paper texts. Everything is
deterministic given those files and the frozen config. Mentions of dropped spans are kept with the
reason; the encoder-only baseline membership is recorded on every mention.
"""

import re
from collections import Counter, defaultdict
from hashlib import sha256

import numpy as np

from scientific_network.enrich.candidates import merge_entities
from scientific_network.enrich.k1 import encoder_candidates
from scientific_network.enrich.textutil import normalize, split_sentences, sentence_index


_TRAILING_ACRONYM = re.compile(r"\s*\(\s*[A-Za-z][A-Za-z0-9\-]{1,9}s?\s*\)\s*$")
_LETTER_DIGIT = re.compile(r"([a-z])(\d)")


def entity_key(surface: str) -> str:
    """Normalized key for an entity: lemmatized, lowercase, no trailing acronym in parentheses, letters and digits split.

    "Large Language Models (LLMs)" and "large language model" share a key; "CIFAR10" and "CIFAR-10" share a key.
    """
    stripped = _TRAILING_ACRONYM.sub("", surface)
    return normalize(_LETTER_DIGIT.sub(r"\1 \2", stripped.lower())) or normalize(surface)


def entity_id(entity_type: str, key: str) -> str:
    """Deterministic ID for an entity without a Wikidata QID: type plus normalized name."""
    digest = sha256(f"{entity_type}\0{key}".encode()).hexdigest()[:16]
    return f"{entity_type.lower()}:{digest}"


def paper_mentions(paper_id: str, text: str, encoded: dict, slm: dict, *, entity_threshold: float,
                   baseline_threshold: float, extractor: str, method_version: str) -> list[dict]:
    """One record per candidate span of a paper: kept (possibly retyped) or dropped with a reason."""
    candidates = {e["id"]: e for e in merge_entities(encoded, text, threshold=entity_threshold)}
    baseline = {(e["type"], normalize(e["text"])) for e in merge_entities(encoded, text, threshold=baseline_threshold)}
    spans = split_sentences(text)
    kept = {e["id"]: e for e in slm["entities"]}
    dropped = {e["id"]: e for e in slm["dropped"]}
    records = []
    for cid, cand in candidates.items():
        verdict = kept.get(cid)
        status = "kept" if verdict else "dropped"
        final_type = verdict["type"] if verdict else cand["type"]
        starts = [m["start"] for m in cand["mentions"] if m["start"] >= 0]
        first = min(starts) if starts else -1
        first_mention = next((m for m in cand["mentions"] if m["start"] == first), cand["mentions"][0])
        records.append({
            "paper_id": paper_id, "type": final_type, "proposed_type": cand["type"], "text": cand["text"],
            "key": entity_key(cand["text"]), "status": status,
            "drop_reason": None if verdict else (dropped.get(cid) or {}).get("reason", "no_decision"),
            "retyped_from": verdict["retyped_from"] if verdict else None,
            "start": first_mention["start"], "end": first_mention["end"],
            "sentence": sentence_index(spans, first) if first >= 0 else -1,
            "n_mentions": len(cand["mentions"]), "confidence": cand["score"],
            "in_encoder_baseline": (cand["type"], normalize(cand["text"])) in baseline,
            "extractor": extractor, "method_version": method_version,
        })
    return records


def paper_relations(paper_id: str, text: str, slm: dict, mentions: list[dict]) -> list[dict]:
    """SLM relations resolved to mention keys, with the sentences of both endpoints as evidence."""
    by_key = {m["key"]: m for m in mentions if m["status"] == "kept"}
    out = []
    for rel in slm["relations"]:
        head, tail = by_key.get(entity_key(rel["head"])), by_key.get(entity_key(rel["tail"]))
        if head is None or tail is None:
            continue
        out.append({"paper_id": paper_id, "relation": rel["relation"], "head_type": head["type"], "head_key": head["key"],
                    "tail_type": tail["type"], "tail_key": tail["key"], "head_sentence": head["sentence"],
                    "tail_sentence": tail["sentence"], "same_sentence": head["sentence"] == tail["sentence"] and head["sentence"] >= 0})
    return out


def head_token(key: str) -> str:
    return key.split()[-1] if key else ""


def merge_surfaces(keys_by_type: dict[str, list[str]], vectors: dict[tuple[str, str], np.ndarray], *, threshold: float,
                   block: int = 2048) -> dict[tuple[str, str], tuple[str, str]]:
    """Union surface forms of the same type whose embeddings are close and that share a head token.

    Returns {(type, key): (type, representative key)}; the representative is the lexicographically
    smallest key of the group so the mapping is deterministic.
    """
    parent: dict[tuple[str, str], tuple[str, str]] = {}

    def find(x):
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for entity_type, keys in keys_by_type.items():
        keys = sorted(set(keys))
        if len(keys) < 2:
            continue
        matrix = np.stack([vectors[(entity_type, k)] for k in keys])
        heads = [head_token(k) for k in keys]
        for start in range(0, len(keys), block):
            sims = matrix[start:start + block] @ matrix.T
            rows, cols = np.where(sims >= threshold)
            for r, c in zip(rows.tolist(), cols.tolist()):
                i = start + r
                if i < c and heads[i] == heads[c]:
                    a, b = find((entity_type, keys[i])), find((entity_type, keys[c]))
                    if a != b:
                        low, high = sorted((a, b))
                        parent[high] = low
    return {node: find(node) for node in list(parent)}


def aggregate_entities(mentions: list[dict], merge: dict[tuple[str, str], tuple[str, str]], *, min_papers: int) -> dict:
    """Group kept mentions into canonical entities; entities with >= min_papers distinct papers become nodes."""
    groups: dict[tuple[str, str], dict] = {}
    for m in mentions:
        if m["status"] != "kept":
            continue
        node = merge.get((m["type"], m["key"]), (m["type"], m["key"]))
        group = groups.setdefault(node, {"type": node[0], "key": node[1], "papers": set(), "surfaces": Counter(), "keys": set()})
        group["papers"].add(m["paper_id"])
        group["surfaces"][m["text"]] += 1
        group["keys"].add(m["key"])
    nodes, below = [], 0
    for (entity_type, key), group in sorted(groups.items()):
        if len(group["papers"]) < min_papers:
            below += 1
            continue
        display = sorted(group["surfaces"].items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        nodes.append({"id": entity_id(entity_type, key), "type": entity_type, "name": display, "key": key,
                      "keys": sorted(group["keys"]), "paper_count": len(group["papers"]),
                      "surfaces": dict(group["surfaces"].most_common(8))})
    return {"nodes": nodes, "below_threshold": below, "groups": len(groups)}
