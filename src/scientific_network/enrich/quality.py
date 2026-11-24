"""E4: frozen AI-assessed audit of the enrichment layer (specification §4.5).

``freeze_audit`` draws every sample from the frozen graph and the 200 test papers with a seeded hash
ranking, writes the sample (IDs, seed, graph hash) and evaluator packets, and hashes them before any
judgement. Packets show the evidence text and the claim, never an extractor confidence or score.
``score_audit`` reads the answer files and reports point estimates with Wilson 95% intervals, per type
and per predicate, plus Cohen's kappa on the A/B overlap. Intervals exclude evaluator error.
"""

import json
import math
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

from scientific_network.enrich.k1 import read_jsonl
from scientific_network.enrich.textutil import normalize, sentence_index, split_sentences
from scientific_network.evaluation.edge_audit import cohens_kappa

TYPES = ("Method", "Task", "Dataset")
VERDICTS = ("correct", "incorrect", "unclear")
VARIANTS = ("default", "encoder_only", "slm_only")


def wilson(successes: int, total: int, z: float = 1.959964) -> dict:
    if total == 0:
        return {"n": 0, "k": 0, "estimate": None, "low": None, "high": None}
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return {"n": total, "k": successes, "estimate": round(p, 4), "low": round(max(0.0, centre - half), 4),
            "high": round(min(1.0, centre + half), 4)}


def rank(seed: int, purpose: str, key: str) -> str:
    return sha256(f"{seed}\0{purpose}\0{key}".encode()).hexdigest()


def draw(keys: list[str], size: int, seed: int, purpose: str) -> list[str]:
    return sorted(keys, key=lambda k: rank(seed, purpose, k))[:size]


def item_id(axis: str, *parts: str) -> str:
    return f"{axis}:" + sha256("\0".join(parts).encode()).hexdigest()[:16]


def evidence_sentence(text: str, start: int, surface: str) -> tuple[str, int]:
    spans = split_sentences(text)
    if start < 0:
        start = text.lower().find(surface.lower())
    index = sentence_index(spans, start) if start >= 0 else -1
    return (text[spans[index][0]:spans[index][1]] if index >= 0 else ""), index


def variant_rows(variant: str, mentions: list[dict], slm_only: dict[str, dict], texts: dict[str, str], test: set[str]) -> list[dict]:
    rows = []
    if variant == "default":
        for m in mentions:
            if m["paper_id"] in test and m["status"] == "kept":
                rows.append({"paper_id": m["paper_id"], "type": m["type"], "text": m["text"], "start": m["start"]})
    elif variant == "encoder_only":
        for m in mentions:
            if m["paper_id"] in test and m["in_encoder_baseline"]:
                rows.append({"paper_id": m["paper_id"], "type": m["proposed_type"], "text": m["text"], "start": m["start"]})
    else:
        for paper_id, record in slm_only.items():
            for e in record.get("entities", []):
                rows.append({"paper_id": paper_id, "type": e["type"], "text": e["text"], "start": texts[paper_id].lower().find(e["text"].lower())})
    seen, unique = set(), []
    for r in rows:
        key = (r["paper_id"], r["type"], normalize(r["text"]))
        if key not in seen and key[2]:
            seen.add(key)
            unique.append(r)
    return unique


def entity_items(pools: dict[str, list[dict]], texts: dict[str, str], seed: int, per_type: int) -> tuple[dict, dict]:
    """Per-variant per-type samples, merged into unique items that remember which variants drew them."""
    items: dict[str, dict] = {}
    sampled: dict[str, dict[str, list[str]]] = {}
    for variant, rows in pools.items():
        sampled[variant] = {}
        for entity_type in TYPES:
            of_type = {item_id("entity", r["paper_id"], r["type"], normalize(r["text"])): r for r in rows if r["type"] == entity_type}
            chosen = draw(list(of_type), per_type, seed, f"entity|{variant}|{entity_type}")
            sampled[variant][entity_type] = chosen
            for key in chosen:
                r = of_type[key]
                sentence, index = evidence_sentence(texts[r["paper_id"]], r["start"], r["text"])
                items.setdefault(key, {"item_id": key, "axis": "entity", "paper_id": r["paper_id"], "mention": r["text"],
                                       "claimed_type": r["type"], "sentence": sentence, "sentence_index": index})
    return items, sampled


def paper_edge_items(edges: list[dict], texts: dict[str, str], evidence: dict[str, dict], test: set[str], seed: int, size: int,
                     key_to_surface: dict[str, str]) -> tuple[dict, dict]:
    """USES_METHOD / ADDRESSES_TASK / USES_DATASET edges of test papers; the claim is that the paper uses/addresses the entity."""
    items, sampled = {}, {}
    for relation in ("USES_METHOD", "ADDRESSES_TASK", "USES_DATASET"):
        pool = {e["edge_id"]: e for e in edges if e["relation"] == relation and e["source_id"] in test}
        chosen = draw(list(pool), size, seed, f"paper-edge|{relation}")
        sampled[relation] = chosen
        for edge_id in chosen:
            e = pool[edge_id]
            ev = evidence[e["evidence_ids"][0]]
            text = texts[e["source_id"]]
            surface = ev.get("surface", "")
            sentence, index = evidence_sentence(text, ev["start"], surface)
            items[item_id("pedge", edge_id)] = {"item_id": item_id("pedge", edge_id), "axis": "paper_edge", "relation": relation,
                                                "paper_id": e["source_id"], "entity": key_to_surface.get(e["target_id"], surface),
                                                "mention": surface, "sentence": sentence, "sentence_index": index}
    return items, sampled


def instructions(axis: str) -> str:
    base = ("You are an independent evaluator. Judge only from the text shown. Do not open other files in the repository, do not "
            "look at other evaluators' answers, and do not guess what the extractor was confident about. Answer correct, incorrect or "
            "unclear (unclear only when the text cannot decide it) and give a note of at most 20 words. ")
    return base + {
        "entity": "Entity: is the mention a real, specific Method, Task or Dataset of the claimed type under docs/final-exam/enrichment-labeling-guideline-v1.md (read only that file)?",
        "paper_edge": "Paper edge: does the title and abstract show that the paper uses or proposes (Method), addresses (Task) or uses for experiments (Dataset) the named entity?",
        "relation": "Relation: do the shown abstracts support the stated relation between the two entities? Report how many of the shown papers support it (supported_in).",
        "related": "Related: would a researcher consider the two concepts closely related (e.g. one is a variant, component, application or neighbouring technique of the other)?",
        "link": "Link: is the Wikipedia page the right concept for the entity, not just a broader or related page?",
        "part_of": "Part of: is the first organization a part, unit, subsidiary or member of the second?",
    }[axis]


# ---------------------------------------------------------------------------
# Sampling for the remaining axes

def support_text(texts: dict[str, str], paper_id: str, spans: list[list[int]]) -> dict:
    text = texts[paper_id]
    sentences = split_sentences(text)
    marked = sorted({sentence_index(sentences, s[0]) for s in spans if s and s[0] >= 0} - {-1})
    return {"paper_id": paper_id, "title_and_abstract": text, "marked_sentence_indices": marked}


def relation_items(graph: dict, texts: dict[str, str], seed: int, size: int) -> tuple[dict, dict]:
    nodes = {n["id"]: n for n in graph["nodes"]}
    evidence = {e["id"]: e for e in graph["evidence"]}
    items, sampled = {}, {}
    for relation in ("APPLIED_TO", "EVALUATED_ON"):
        pool = {e["edge_id"]: e for e in graph["edges"] if e["relation"] == relation}
        chosen = draw(list(pool), size, seed, f"relation|{relation}")
        sampled[relation] = chosen
        for edge_id in chosen:
            e = pool[edge_id]
            shown = []
            for ref in e["evidence_ids"][:2]:
                ev = evidence[ref]
                shown.append(support_text(texts, ev["paper_id"], [ev["head_span"], ev["tail_span"]]))
            items[item_id("rel", edge_id)] = {
                "item_id": item_id("rel", edge_id), "axis": "relation", "relation": relation,
                "head": f"{nodes[e['source_id']]['name']} ({nodes[e['source_id']]['label']})",
                "tail": f"{nodes[e['target_id']]['name']} ({nodes[e['target_id']]['label']})", "papers": shown}
    return items, sampled


def related_items(graph: dict, leads: dict[str, str], seed: int, size: int) -> tuple[dict, dict]:
    nodes = {n["id"]: n for n in graph["nodes"]}
    pool = {e["edge_id"]: e for e in graph["edges"] if e["relation"] == "RELATED_TO"}
    chosen = draw(list(pool), size, seed, "related")
    items = {}
    for edge_id in chosen:
        e = pool[edge_id]
        a, b = nodes[e["source_id"]], nodes[e["target_id"]]
        items[item_id("rel2", edge_id)] = {"item_id": item_id("rel2", edge_id), "axis": "related", "a": f"{a['name']} ({a['label']})",
                                           "b": f"{b['name']} ({b['label']})", "a_page": a["properties"].get("wikipedia_title"),
                                           "b_page": b["properties"].get("wikipedia_title"),
                                           "a_lead": leads.get(a["properties"].get("wikipedia_title"), "")[:400],
                                           "b_lead": leads.get(b["properties"].get("wikipedia_title"), "")[:400]}
    return items, {"RELATED_TO": chosen}


def link_items(graph: dict, texts: dict[str, str], leads: dict[str, str], seed: int, size: int) -> tuple[dict, dict]:
    papers_of: dict[str, list[str]] = defaultdict(list)
    for e in graph["edges"]:
        if e["relation"] in ("USES_METHOD", "ADDRESSES_TASK", "USES_DATASET"):
            papers_of[e["target_id"]].append(e["source_id"])
    pool = {n["id"]: n for n in graph["nodes"] if n["label"] in TYPES and n["properties"].get("linked")}
    chosen = draw(list(pool), size, seed, "link")
    items = {}
    for node_id in chosen:
        n = pool[node_id]
        titles = [texts[p].split("\n")[0] for p in sorted(papers_of[node_id])[:3]]
        items[item_id("link", node_id)] = {"item_id": item_id("link", node_id), "axis": "link", "entity": n["name"], "type": n["label"],
                                           "example_paper_titles": titles, "wikipedia_title": n["properties"]["wikipedia_title"],
                                           "wikipedia_lead": leads.get(n["properties"]["wikipedia_title"], "")[:500]}
    return items, {"link": chosen}


def part_of_items(graph: dict, seed: int, size: int) -> tuple[dict, dict]:
    nodes = {n["id"]: n for n in graph["nodes"]}
    extra = graph.get("node_enrichments", {})
    pool = {e["edge_id"]: e for e in graph["edges"] if e["relation"] == "PART_OF"}
    chosen = draw(list(pool), size, seed, "part_of")
    items = {}
    for edge_id in chosen:
        e = pool[edge_id]
        child, parent = nodes[e["source_id"]], nodes[e["target_id"]]
        items[item_id("part", edge_id)] = {"item_id": item_id("part", edge_id), "axis": "part_of", "organization": child["name"],
                                           "organization_description": (extra.get(child["id"]) or {}).get("wikidata_description"),
                                           "parent": parent["name"],
                                           "parent_description": (extra.get(parent["id"]) or {}).get("wikidata_description")}
    return items, {"PART_OF": chosen}


def recall_papers(test: list[str], seed: int, size: int) -> list[str]:
    return draw(sorted(test), size, seed, "recall")


# ---------------------------------------------------------------------------
# Freeze: sample, packets, hashes

def assign(item_ids: list[str], seed: int, overlap_share: float = 0.2) -> dict[str, list[str]]:
    """Deterministic evaluator channels: a seeded 20% of items go to both A and B, the rest alternate."""
    ordered = sorted(item_ids)
    overlap = set(draw(ordered, round(len(ordered) * overlap_share), seed, "overlap"))
    out = {i: ["A", "B"] for i in overlap}
    for index, i in enumerate(sorted(set(ordered) - overlap, key=lambda k: rank(seed, "assign", k))):
        out[i] = ["A"] if index % 2 == 0 else ["B"]
    return out


def write_packets(items: dict[str, dict], assignments: dict[str, list[str]], recall: list[dict], out_dir: Path, shard_size: int) -> list[dict]:
    packets = []
    for channel in ("A", "B"):
        mine = sorted((i for i in items if channel in assignments[i]), key=lambda i: (items[i]["axis"], i))
        shards = [mine[k:k + shard_size] for k in range(0, len(mine), shard_size)]
        recall_mine = [r for r in recall if channel in r["channels"]]
        for index, shard in enumerate(shards):
            body = {"channel": channel, "shard": index + 1, "kind": "judgement",
                    "instructions": {axis: instructions(axis) for axis in sorted({items[i]["axis"] for i in shard})},
                    "answer_format": {"file": f"answers/{channel}-{index + 1}.jsonl",
                                      "line": {"item_id": "...", "verdict": "correct|incorrect|unclear", "supported_in": "relation items only: integer", "note": "<=20 words"}},
                    "items": [items[i] for i in shard]}
            path = out_dir / "packets" / f"{channel}-{index + 1}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(body, indent=1, ensure_ascii=False))
            packets.append({"path": str(path), "channel": channel, "items": len(shard), "sha256": sha256(path.read_bytes()).hexdigest()})
        if recall_mine:
            body = {"channel": channel, "kind": "recall",
                    "instructions": "For each paper, list every Method, Task and Dataset named in the title and abstract, copied as written, following docs/final-exam/enrichment-labeling-guideline-v1.md (read only that file). No system output is shown.",
                    "answer_format": {"file": f"answers/{channel}-recall.jsonl", "line": {"paper_id": "...", "entities": [{"text": "...", "type": "Method|Task|Dataset"}]}},
                    "papers": [{"paper_id": r["paper_id"], "title_and_abstract": r["text"]} for r in recall_mine]}
            path = out_dir / "packets" / f"{channel}-recall.json"
            path.write_text(json.dumps(body, indent=1, ensure_ascii=False))
            packets.append({"path": str(path), "channel": channel, "papers": len(recall_mine), "sha256": sha256(path.read_bytes()).hexdigest()})
    return packets


def freeze_audit(*, graph_path: Path, mentions_path: Path, texts_path: Path, test_path: Path, link_dir: Path, slm_only_path: Path | None,
                 out_dir: Path, seed: int, per_type: int = 100, relation_size: int = 100, part_of_size: int = 50, recall_size: int = 50,
                 shard_size: int = 120) -> dict:
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    texts = {r["id"]: r["text"] for r in read_jsonl(texts_path)}
    test = {json.loads(line)["paper_id"] for line in test_path.read_text(encoding="utf-8").splitlines() if line.strip()} & set(texts)
    mentions = read_jsonl(mentions_path)
    slm_only = {r["id"]: r for r in read_jsonl(slm_only_path)} if slm_only_path else {}
    leads_path = link_dir / "link-leads.jsonl"
    leads = {r["id"]: r["text"] for r in read_jsonl(leads_path)} if leads_path.exists() else {}
    evidence = {e["id"]: e for e in graph["evidence"]}
    pools = {v: variant_rows(v, mentions, slm_only, texts, test) for v in VARIANTS if v != "slm_only" or slm_only}
    items, ent_sample = entity_items(pools, texts, seed, per_type)
    key_to_surface = {n["id"]: n["name"] for n in graph["nodes"]}
    pe_items, pe_sample = paper_edge_items(graph["edges"], texts, evidence, test, seed, relation_size, key_to_surface)
    rel_items, rel_sample = relation_items(graph, texts, seed, relation_size)
    rel2_items, rel2_sample = related_items(graph, leads, seed, relation_size)
    lk_items, lk_sample = link_items(graph, texts, leads, seed, relation_size)
    po_items, po_sample = part_of_items(graph, seed, part_of_size)
    for part in (pe_items, rel_items, rel2_items, lk_items, po_items):
        items.update(part)
    assignments = assign(list(items), seed)
    recall_ids = recall_papers(sorted(test), seed, recall_size)
    recall_channels = assign(recall_ids, seed + 1)
    recall = [{"paper_id": p, "text": texts[p], "channels": recall_channels[p]} for p in recall_ids]
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "answers").mkdir(exist_ok=True)
    packets = write_packets(items, assignments, recall, out_dir, shard_size)
    sample = {"seed": seed, "graph_version": graph["graph_version"], "graph_sha256": sha256(graph_path.read_bytes()).hexdigest(),
              "mentions_sha256": sha256(mentions_path.read_bytes()).hexdigest(), "test_papers": len(test),
              "entity_sample": ent_sample, "paper_edge_sample": pe_sample, "relation_sample": rel_sample, "related_sample": rel2_sample,
              "link_sample": lk_sample, "part_of_sample": po_sample, "recall_papers": recall_ids,
              "variant_pool_sizes": {v: dict(Counter(r["type"] for r in rows)) for v, rows in pools.items()},
              "assignments": assignments, "recall_channels": recall_channels,
              "item_axes": dict(Counter(i["axis"] for i in items.values())), "items_total": len(items)}
    sample_path = out_dir / "sample.json"
    sample_path.write_text(json.dumps(sample, indent=1, ensure_ascii=False, sort_keys=True))
    items_path = out_dir / "items.json"
    items_path.write_text(json.dumps(items, ensure_ascii=False, sort_keys=True))
    receipt = {"frozen": True, "purpose": "E4 AI-assessed audit sample, written before any judgement",
               "sample_sha256": sha256(sample_path.read_bytes()).hexdigest(), "items_sha256": sha256(items_path.read_bytes()).hexdigest(),
               "packets": packets, "graph_version": graph["graph_version"], "seed": seed}
    (out_dir / "freeze-receipt.json").write_text(json.dumps(receipt, indent=1, sort_keys=True))
    return receipt


# ---------------------------------------------------------------------------
# Scoring

def load_answers(answers_dir: Path) -> tuple[dict[str, dict[str, dict]], dict[str, dict[str, list]]]:
    """item -> channel -> answer; paper -> channel -> listed entities. Files are named ``<channel>-<n>.jsonl``."""
    judged: dict[str, dict[str, dict]] = defaultdict(dict)
    listed: dict[str, dict[str, list]] = defaultdict(dict)
    for path in sorted(answers_dir.glob("*.jsonl")):
        channel = path.name.split("-")[0]
        for row in read_jsonl(path):
            if "entities" in row:
                listed[row["paper_id"]][channel] = row["entities"]
            elif row.get("verdict") in VERDICTS:
                judged[row["item_id"]].setdefault(channel, row)
    return judged, listed


def final_verdict(answers: dict[str, dict]) -> dict | None:
    return answers.get("A") or answers.get("B")


def precision(ids: list[str], judged: dict, field: str = "verdict", positive: str = "correct") -> dict:
    counted = [final_verdict(judged[i]) for i in ids if i in judged]
    decided = [a for a in counted if a[field] in ("correct", "incorrect")]
    result = wilson(sum(a[field] == positive for a in decided), len(decided))
    result.update({"sampled": len(ids), "judged": len(counted), "unclear": len(counted) - len(decided)})
    return result


def relation_precision(ids: list[str], judged: dict, items: dict) -> dict:
    """An edge is correct when the relation holds in at least half of the shown papers (rounded up); also report all-shown."""
    lenient, strict, n = 0, 0, 0
    for i in ids:
        answer = final_verdict(judged.get(i, {})) if i in judged else None
        if not answer or answer["verdict"] == "unclear":
            continue
        shown = len(items[i]["papers"])
        supported = int(answer.get("supported_in", shown if answer["verdict"] == "correct" else 0))
        n += 1
        lenient += supported >= math.ceil(shown / 2)
        strict += supported >= shown
    return {"all_shown_papers_support": wilson(strict, n), "at_least_half_support": wilson(lenient, n), "sampled": len(ids)}


def agreement(items: dict, assignments: dict, judged: dict) -> dict:
    pairs = [(judged[i]["A"]["verdict"], judged[i]["B"]["verdict"]) for i in assignments
             if len(assignments[i]) == 2 and i in judged and "A" in judged[i] and "B" in judged[i]]
    return {"overlap_items_judged_by_both": len(pairs), "observed_agreement": round(sum(a == b for a, b in pairs) / len(pairs), 4) if pairs else None,
            "cohens_kappa": None if (k := cohens_kappa(pairs)) is None else round(k, 4)}


def recall_scores(listed: dict, pools: dict[str, list[dict]]) -> dict:
    from scientific_network.enrich.textutil import jaccard
    out = {}
    for variant, rows in pools.items():
        by_paper: dict[str, list[dict]] = defaultdict(list)
        for r in rows:
            by_paper[r["paper_id"]].append(r)
        matched, total = Counter(), Counter()
        for paper_id, channels in listed.items():
            answer = channels.get("A") or channels.get("B") or []
            for e in answer:
                total[e["type"]] += 1
                if any(r["type"] == e["type"] and jaccard(r["text"], e["text"]) >= 0.5 for r in by_paper.get(paper_id, [])):
                    matched[e["type"]] += 1
        out[variant] = {t: wilson(matched[t], total[t]) for t in TYPES} | {"all": wilson(sum(matched.values()), sum(total.values()))}
    return out


def structure_and_coverage(graph: dict, validation_errors: list[str]) -> dict:
    nodes = [n for n in graph["nodes"] if n["label"] in TYPES]
    by_qid: dict[tuple[str, str], list[str]] = defaultdict(list)
    for n in nodes:
        if n["properties"].get("wikidata_qid"):
            by_qid[(n["label"], n["properties"]["wikidata_qid"])].append(n["id"])
    by_key: dict[str, set[str]] = defaultdict(set)
    for n in nodes:
        by_key[n["properties"]["key"]].add(n["label"])
    incoming = Counter(e["target_id"] for e in graph["edges"] if e["relation"] in ("USES_METHOD", "ADDRESSES_TASK", "USES_DATASET"))
    core = {n["id"] for n in graph["nodes"] if n["label"] == "Paper" and (n.get("properties") or {}).get("is_core")}
    has = {t: set() for t in TYPES}
    for e in graph["edges"]:
        target = {"USES_METHOD": "Method", "ADDRESSES_TASK": "Task", "USES_DATASET": "Dataset"}.get(e["relation"])
        if target:
            has[target].add(e["source_id"])
    orgs = [n["id"] for n in graph["nodes"] if n["label"] == "Organization" and (n.get("properties") or {}).get("source") != "wikidata_parent"]
    extra = graph.get("node_enrichments", {})
    return {"validator_errors": len(validation_errors),
            "entity_nodes": len(nodes), "orphan_entity_nodes": sum(1 for n in nodes if incoming[n["id"]] == 0),
            "duplicate_entities_same_qid_under_two_ids": sum(1 for ids in by_qid.values() if len(ids) > 1),
            "keys_with_type_conflict": sum(1 for types in by_key.values() if len(types) > 1),
            "coverage": {"core_papers": len(core),
                         **{f"papers_with_{t.lower()}": round(len(has[t] & core) / len(core), 4) for t in TYPES},
                         "papers_with_method_task_and_dataset": round(len(has["Method"] & has["Task"] & has["Dataset"] & core) / len(core), 4),
                         "organizations": len(orgs), "organizations_with_wikidata_qid": sum(1 for o in orgs if "wikidata_qid" in extra.get(o, {})),
                         "organizations_with_wikipedia_page": sum(1 for o in orgs if "wikipedia_url" in extra.get(o, {}))}}


def score_audit(*, audit_dir: Path, graph_path: Path, mentions_path: Path, texts_path: Path, test_path: Path,
                slm_only_path: Path | None, output: Path) -> dict:
    from scientific_network.enrich.graph5 import validate_enriched
    sample = json.loads((audit_dir / "sample.json").read_text())
    receipt = json.loads((audit_dir / "freeze-receipt.json").read_text())
    if sha256((audit_dir / "sample.json").read_bytes()).hexdigest() != receipt["sample_sha256"]:
        raise ValueError("sample.json differs from the frozen receipt")
    if sha256(graph_path.read_bytes()).hexdigest() != sample["graph_sha256"]:
        raise ValueError("graph differs from the graph the sample was frozen on")
    items = json.loads((audit_dir / "items.json").read_text())
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    texts = {r["id"]: r["text"] for r in read_jsonl(texts_path)}
    test = {json.loads(line)["paper_id"] for line in test_path.read_text(encoding="utf-8").splitlines() if line.strip()} & set(texts)
    mentions = read_jsonl(mentions_path)
    slm_only = {r["id"]: r for r in read_jsonl(slm_only_path)} if slm_only_path else {}
    judged, listed = load_answers(audit_dir / "answers")
    answered = sum(1 for i in items if i in judged)
    entity = {v: {t: precision(ids, judged) for t, ids in by_type.items()} for v, by_type in sample["entity_sample"].items()}
    for v, by_type in sample["entity_sample"].items():
        entity[v]["all_types"] = precision([i for ids in by_type.values() for i in ids], judged)
    paper_edges = {r: precision(ids, judged) for r, ids in sample["paper_edge_sample"].items()}
    pools = {v: variant_rows(v, mentions, slm_only, texts, test) for v in sample["variant_pool_sizes"]}
    report = {
        "evaluation_kind": "ai_assessed", "graph_version": sample["graph_version"], "graph_sha256": sample["graph_sha256"], "seed": sample["seed"],
        "items_frozen": len(items), "items_with_an_answer": answered,
        "entity_precision_by_variant": entity,
        "predicate_precision": {"paper_edges": paper_edges,
                                "entity_relations": {r: relation_precision(ids, judged, items) for r, ids in sample["relation_sample"].items()},
                                "related_to": {r: precision(ids, judged) for r, ids in sample["related_sample"].items()},
                                "part_of": {r: precision(ids, judged) for r, ids in sample["part_of_sample"].items()}},
        "linking_accuracy": {r: precision(ids, judged) for r, ids in sample["link_sample"].items()},
        "recall_estimate_by_variant": recall_scores({p: c for p, c in listed.items() if p in sample["recall_papers"]}, pools),
        "recall_papers_answered": len([p for p in sample["recall_papers"] if p in listed]),
        "agreement": agreement(items, {i: a for i, a in sample["assignments"].items()}, judged),
        "structure_and_coverage": structure_and_coverage(graph, validate_enriched(graph)),
        "targets": {"entity_precision": 0.85, "relation_precision": 0.80, "linking_accuracy": 0.85},
        "interpretation": "AI-assessed by an agent evaluator from a different model family than the extractors; not human annotation and not independently validated gold labels. Wilson 95% intervals exclude evaluator error.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=1, ensure_ascii=False, sort_keys=True) + "\n")
    return report
