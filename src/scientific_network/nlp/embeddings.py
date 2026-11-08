"""Lazy CPU sentence-embedding topic assignment for the D040 release."""

from __future__ import annotations

from collections import defaultdict
import math
import re
from typing import Any
from pathlib import Path
import hashlib
import json

import numpy as np

METHOD_VERSION = "release-embedding-topics-v1"
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_development_documents(
    works_path: Path,
    roster_path: Path,
    membership_path: Path,
    leakage_path: Path,
    topic_test_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Load only release-core non-test documents for threshold calibration.

    All existing split test groups are excluded, not just the 30 IJCAI IDs sampled for
    topic annotation. The new AAAI sample and every declared version in its holdout group
    are excluded before any title or abstract is returned to the caller.
    """
    def jsonl(path: Path):
        with path.open(encoding="utf-8") as handle:
            for number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid JSONL at {path}:{number}: {exc}") from exc

    roster = {}
    for row in jsonl(roster_path):
        if (row.get("status") == "included" and row.get("venue_id") in {"venue:aaai", "venue:ijcai"}
                and row.get("year") in {2021, 2022, 2023, 2024, 2025}):
            paper_id = row.get("paper_id")
            if not paper_id or paper_id in roster:
                raise ValueError(f"missing or duplicate included roster paper ID: {paper_id}")
            roster[paper_id] = row

    membership = {}
    group_ids: dict[str, set[str]] = defaultdict(set)
    test_rows = []
    for row in jsonl(membership_path):
        paper_id = row.get("paper_id")
        if not paper_id or paper_id in membership:
            raise ValueError(f"missing or duplicate membership paper ID: {paper_id}")
        membership[paper_id] = row
        group_ids[row["leakage_group"]].add(paper_id)
        if row.get("split") == "test":
            test_rows.append(row)

    leakage_by_id = {}
    for row in jsonl(leakage_path):
        for paper_id in row.get("candidate_paper_ids", [row.get("paper_id")]):
            if paper_id:
                leakage_by_id[paper_id] = row

    def expand_candidate_versions(seed_ids: set[str]) -> set[str]:
        expanded, pending = set(seed_ids), list(seed_ids)
        while pending:
            paper_id = pending.pop()
            leakage = leakage_by_id.get(paper_id)
            if not leakage:
                continue
            for candidate_id in leakage.get("candidate_paper_ids") or []:
                if candidate_id not in expanded:
                    expanded.add(candidate_id)
                    pending.append(candidate_id)
        return expanded

    heldout = set()
    for row in test_rows:
        heldout.update(expand_candidate_versions(group_ids[row["leakage_group"]]))
    manifest_rows = list(jsonl(topic_test_path))
    source_hashes = {
        "roster_sha256": _sha256(roster_path),
        "membership_sha256": _sha256(membership_path),
        "leakage_sha256": _sha256(leakage_path),
    }
    if not manifest_rows:
        raise ValueError("frozen topic test manifest is empty")
    for row in manifest_rows:
        if any(row.get(key) != value for key, value in source_hashes.items()):
            raise ValueError("topic test manifest source hashes do not match current inputs")
        if row.get("paper_id") not in roster:
            raise ValueError(f"topic test ID is outside the release roster: {row.get('paper_id')}")
        heldout.update(expand_candidate_versions(set(row.get("heldout_paper_ids") or [row["paper_id"]])))

    development_ids = set(roster) - heldout
    documents = []
    seen = set()
    for row in jsonl(works_path):
        paper_id = row.get("paper_id")
        if paper_id not in development_ids:
            continue
        if paper_id in seen:
            raise ValueError(f"duplicate works row for development paper: {paper_id}")
        seen.add(paper_id)
        matched = row.get("match", {}).get("status") == "matched"
        openalex = row.get("openalex") if matched else None
        documents.append({
            "paper_id": paper_id, "title": row["roster"]["title"],
            "abstract": (openalex or {}).get("abstract"), "venue_id": row["venue_id"],
            "year": row["year"], "match_status": row.get("match", {}).get("status"),
        })
    if seen != development_ids:
        missing = sorted(development_ids - seen)
        raise ValueError(f"works input is missing {len(missing)} non-test release papers")
    if seen & heldout:
        raise ValueError("development documents intersect the frozen test/version holdouts")

    report = {
        "method_version": METHOD_VERSION,
        "eligible_release_papers": len(roster),
        "existing_reserved_test_papers": len({row["paper_id"] for row in test_rows if row["paper_id"] in roster}),
        "new_topic_test_papers": len(manifest_rows),
        "development_papers": len(documents),
        "development_abstracts": sum(bool(row["abstract"]) for row in documents),
        "heldout_release_paper_ids_including_versions": len(heldout & set(roster)),
        "works_sha256": _sha256(works_path),
        "topic_test_sha256": _sha256(topic_test_path),
        **source_hashes,
    }
    return documents, report


def load_sentence_model(config: dict[str, Any]):
    """Load the pinned Sentence Transformers model only when the nlp extra is installed."""
    model = config.get("model", {})
    name, revision = model.get("name"), model.get("revision")
    if not name or not revision:
        raise ValueError("topic model name and immutable revision are required")
    device = model.get("device", "cpu")
    if device != "cpu":
        raise ValueError("release topic inference is pinned to CPU")
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError("install the pinned CPU model dependencies with `uv sync --extra nlp`") from exc
    return SentenceTransformer(name, revision=revision, device=device)


def label_text(leaf: dict[str, Any]) -> str:
    """Build the exact concept text used by the frozen taxonomy."""
    parts = [leaf["name"], leaf.get("definition", "")]
    include = leaf.get("include") or []
    synonyms = leaf.get("synonyms") or []
    if include:
        parts.append("Includes: " + "; ".join(include))
    if synonyms:
        parts.append("Synonyms: " + "; ".join(synonyms))
    return "\n".join(part.strip() for part in parts if part and part.strip())


def split_sentences(text: str) -> list[tuple[str, int, int]]:
    """Split text without losing source offsets for evidence locators."""
    sentences = []
    for match in _SENTENCE_BOUNDARY.finditer(text):
        start = 0 if not sentences else sentences[-1][2]
        end = match.start()
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        if start < end:
            sentences.append((text[start:end], start, end))
        start = match.end()
    start = 0 if not sentences else sentences[-1][2]
    while start < len(text) and text[start].isspace():
        start += 1
    end = len(text.rstrip())
    if start < end:
        sentences.append((text[start:end], start, end))
    return sentences or ([(text, 0, len(text))] if text else [])


def select_labels(similarities, leaves: list[dict[str, Any]], tau: float, delta: float) -> list[dict[str, Any]]:
    """Select the top label plus at most two close labels, or abstain below tau."""
    if not math.isfinite(tau) or not -1 <= tau <= 1:
        raise ValueError("tau must be a finite cosine threshold in [-1, 1]")
    if not math.isfinite(delta) or not 0 <= delta <= 2:
        raise ValueError("delta must be a finite nonnegative cosine margin no greater than 2")
    scores = np.asarray(similarities, dtype=np.float64)
    if scores.ndim != 1 or len(scores) != len(leaves) or not np.isfinite(scores).all():
        raise ValueError("similarity vector must contain one finite score per leaf topic")
    order = sorted(range(len(leaves)), key=lambda index: (-float(scores[index]), leaves[index]["id"]))
    if not order or float(scores[order[0]]) < tau:
        return []
    top = float(scores[order[0]])
    selected = []
    for index in order:
        score = float(scores[index])
        if score < tau or top - score > delta:
            continue
        selected.append({"topic_id": leaves[index]["id"], "similarity": score})
        if len(selected) == 3:
            break
    return selected


def score_documents(documents: list[dict[str, Any]], taxonomy: dict[str, Any], model, *, batch_size: int = 64):
    """Return document-to-leaf cosine scores for a caller-filtered split."""
    if type(batch_size) is not int or batch_size < 1:
        raise ValueError("batch_size must be a positive integer")
    leaves = taxonomy.get("leaves") or []
    if not leaves:
        raise ValueError("taxonomy requires at least one leaf topic")
    ids = [row.get("paper_id") for row in documents]
    if any(not paper_id for paper_id in ids) or len(ids) != len(set(ids)):
        raise ValueError("documents require unique paper_id values")
    label_vectors = np.asarray(model.encode(
        [label_text(leaf) for leaf in leaves], batch_size=batch_size,
        normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False,
    ), dtype=np.float32)
    if label_vectors.ndim != 2 or label_vectors.shape[0] != len(leaves):
        raise ValueError("model returned an invalid topic embedding matrix")
    if not documents:
        return np.empty((0, len(leaves)), dtype=np.float32), label_vectors
    texts = []
    for row in documents:
        title = str(row.get("title") or "").strip()
        abstract = str(row.get("abstract") or "").strip()
        if not title and not abstract:
            raise ValueError(f"paper has neither title nor abstract: {row['paper_id']}")
        texts.append(title + ("\n" + abstract if abstract else ""))
    paper_vectors = np.asarray(model.encode(
        texts, batch_size=batch_size, normalize_embeddings=True,
        convert_to_numpy=True, show_progress_bar=False,
    ), dtype=np.float32)
    if (paper_vectors.ndim != 2 or paper_vectors.shape[0] != len(documents)
            or paper_vectors.shape[1] != label_vectors.shape[1]):
        raise ValueError("model returned an invalid paper embedding matrix")
    return paper_vectors @ label_vectors.T, label_vectors


def predict_topics(
    documents: list[dict[str, Any]],
    taxonomy: dict[str, Any],
    model,
    *,
    tau: float,
    delta: float,
    batch_size: int = 64,
) -> list[dict[str, Any]]:
    """Predict topics and supporting excerpts for supplied documents.

    The caller is responsible for passing only the intended split. Development code
    must construct its input through `load_development_documents` first.
    """
    if type(batch_size) is not int or batch_size < 1:
        raise ValueError("batch_size must be a positive integer")
    leaves = taxonomy.get("leaves") or []
    if not leaves:
        raise ValueError("taxonomy requires at least one leaf topic")
    ids = [row.get("paper_id") for row in documents]
    if any(not paper_id for paper_id in ids) or len(ids) != len(set(ids)):
        raise ValueError("documents require unique paper_id values")
    if not documents:
        return []
    paper_scores, label_vectors = score_documents(documents, taxonomy, model, batch_size=batch_size)
    source_sentences = []
    for row in documents:
        title = str(row.get("title") or "").strip()
        abstract = str(row.get("abstract") or "").strip()
        if not title and not abstract:
            raise ValueError(f"paper has neither title nor abstract: {row['paper_id']}")
        source_text, source = (abstract, "abstract") if abstract else (title, "title")
        source_sentences.append((source, split_sentences(source_text)))

    chosen = [select_labels(paper_scores[index], leaves, tau, delta) for index in range(len(documents))]
    sentence_texts, sentence_owner = [], []
    for paper_index, labels in enumerate(chosen):
        if labels:
            for sentence_index, (sentence, start, end) in enumerate(source_sentences[paper_index][1]):
                sentence_texts.append(sentence)
                sentence_owner.append((paper_index, sentence_index, start, end))
    sentence_scores: dict[tuple[int, int], list[tuple[float, int, int, int]]] = defaultdict(list)
    if sentence_texts:
        sentence_vectors = np.asarray(model.encode(
            sentence_texts, batch_size=batch_size, normalize_embeddings=True,
            convert_to_numpy=True, show_progress_bar=False,
        ), dtype=np.float32)
        if sentence_vectors.ndim != 2 or sentence_vectors.shape[0] != len(sentence_texts) or sentence_vectors.shape[1] != label_vectors.shape[1]:
            raise ValueError("model returned an invalid sentence embedding matrix")
        scores = sentence_vectors @ label_vectors.T
        for vector_index, (paper_index, sentence_index, start, end) in enumerate(sentence_owner):
            for label_index in range(len(leaves)):
                sentence_scores[(paper_index, label_index)].append(
                    (float(scores[vector_index, label_index]), sentence_index, start, end))

    results = []
    for paper_index, row in enumerate(documents):
        predictions = []
        source, sentences = source_sentences[paper_index]
        for prediction in chosen[paper_index]:
            label_index = next(i for i, leaf in enumerate(leaves) if leaf["id"] == prediction["topic_id"])
            best = max(sentence_scores[(paper_index, label_index)], key=lambda item: (item[0], -item[1]))
            sentence_index, start, end = best[1], best[2], best[3]
            predictions.append({
                **prediction, "excerpt": sentences[sentence_index][0],
                "text_source": source, "start": start, "end": end,
            })
        results.append({"paper_id": row["paper_id"], "predictions": predictions,
                        "text_source": source, "decision": "labeled" if predictions else "abstain"})
    return results


def calibrate_topic_thresholds(
    documents: list[dict[str, Any]],
    taxonomy: dict[str, Any],
    model,
    *,
    target_coverage: float = 0.85,
    seed: int,
    sample_size: int = 30,
    batch_size: int = 64,
) -> dict[str, Any]:
    """Summarize development-only tau/delta candidates and a blinded-to-test sample."""
    if not 0.8 <= target_coverage <= 0.9:
        raise ValueError("target topic coverage must be between 0.80 and 0.90")
    if type(sample_size) is not int or sample_size < 1 or sample_size > len(documents):
        raise ValueError("sample_size must be between 1 and the number of development documents")
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    scores, _ = score_documents(documents, taxonomy, model, batch_size=batch_size)
    if len(scores) < 1:
        raise ValueError("no development documents were supplied")
    top_scores = np.max(scores, axis=1)
    tau = float(np.quantile(top_scores, 1 - target_coverage, method="higher"))
    observed_coverage = float(np.mean(top_scores >= tau))

    sorted_scores = np.sort(scores, axis=1)[:, ::-1]
    second_gap = top_scores - sorted_scores[:, 1] if scores.shape[1] > 1 else np.full(len(scores), 2.0)
    candidates = {0.02, 0.05, 0.10}
    for quantile in (0.1, 0.25, 0.5):
        candidates.add(float(np.clip(np.quantile(second_gap[top_scores >= tau], quantile), 0, 0.25)))
    delta_sweep = []
    for delta in sorted(candidates):
        assignments = [select_labels(row, taxonomy["leaves"], tau, delta) for row in scores]
        labeled = sum(bool(row) for row in assignments)
        multilabel = sum(len(row) > 1 for row in assignments)
        delta_sweep.append({
            "delta": delta, "labeled_papers": labeled,
            "coverage": labeled / len(documents),
            "multi_label_papers": multilabel,
            "mean_labels_per_paper": float(np.mean([len(row) for row in assignments])),
        })

    sample = sorted(documents, key=lambda row: (
        hashlib.sha256(f"{seed}\0{row['paper_id']}".encode("utf-8")).hexdigest(), row["paper_id"],
    ))[:sample_size]
    sample_predictions = predict_topics(sample, taxonomy, model, tau=tau, delta=0.05, batch_size=batch_size)
    sample_rows = [{
        "paper_id": row["paper_id"], "decision": row["decision"],
        "topic_ids": [item["topic_id"] for item in row["predictions"]],
        "similarities": [round(item["similarity"], 6) for item in row["predictions"]],
        "text_source": row["text_source"],
    } for row in sample_predictions]
    return {
        "method_version": METHOD_VERSION, "development_papers": len(documents),
        "target_coverage": target_coverage, "tau": tau, "observed_coverage": observed_coverage,
        "delta_sweep": delta_sweep, "sample_seed": seed, "sample_size": sample_size,
        "development_sample": sample_rows,
        "test_predictions_computed": False,
    }
