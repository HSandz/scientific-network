"""Score the frozen topic test against the D040 partial-overlap reviewer design."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any

import yaml

from scientific_network.contracts import GraphArtifact, Relation
from scientific_network.evaluation.topic_review import FIELDS, _jsonl


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _read_graph(path: Path) -> tuple[GraphArtifact, str]:
    raw = path.read_bytes()
    return GraphArtifact.model_validate_json(raw), sha256(raw).hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            raise ValueError(f"unexpected topic review CSV schema: {path}")
        rows = list(reader)
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError(f"malformed topic review CSV row: {path}")
    return rows


def _read_topic_labels(
    path: Path,
    *,
    reviewer: str,
    expected_ids: set[str],
    master_rows: dict[str, dict[str, str]],
    allowed_topics: set[str],
) -> dict[str, set[str]]:
    rows = _read_csv(path)
    labels: dict[str, set[str]] = {}
    for row in rows:
        paper_id = row.get("paper_id", "")
        if paper_id not in expected_ids or paper_id in labels:
            raise ValueError(f"reviewer {reviewer} CSV has an unknown or duplicate paper ID")
        if row.get("labeler") != reviewer:
            raise ValueError(f"reviewer {reviewer} CSV has a mismatched labeler field")
        source = master_rows[paper_id]
        for key in ("venue_id", "year", "title", "abstract", "topic_catalog"):
            if row.get(key) != source.get(key):
                raise ValueError(f"reviewer {reviewer} changed frozen paper field {key!r}")
        selected = [row.get(f"label_{slot}", "").strip() for slot in range(1, 4)]
        selected = [value for value in selected if value]
        if len(selected) != len(set(selected)):
            raise ValueError(f"reviewer {reviewer} repeated a topic label on {paper_id}")
        if not selected and not row.get("notes", "").strip():
            raise ValueError(f"reviewer {reviewer} left {paper_id} unreviewed; explain an empty label set in Notes")
        unknown = set(selected) - allowed_topics
        if unknown:
            raise ValueError(f"reviewer {reviewer} used topic IDs outside the frozen taxonomy: {sorted(unknown)}")
        labels[paper_id] = set(selected)
    if set(labels) != expected_ids:
        raise ValueError(
            f"reviewer {reviewer} CSV does not match assigned papers "
            f"(missing={len(expected_ids - set(labels))}, extra={len(set(labels) - expected_ids)})"
        )
    return labels


def _counts(labels: set[str], predicted: set[str], weight: float) -> tuple[float, float, float]:
    return (
        weight * len(labels & predicted),
        weight * len(predicted - labels),
        weight * len(labels - predicted),
    )


def _prf(tp: float, fp: float, fn: float) -> dict[str, float | None]:
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    denominator = 2 * tp + fp + fn
    f1 = 2 * tp / denominator if denominator else None
    return {
        "true_positive": round(tp, 8),
        "false_positive": round(fp, 8),
        "false_negative": round(fn, 8),
        "precision": round(precision, 8) if precision is not None else None,
        "recall": round(recall, 8) if recall is not None else None,
        "f1": round(f1, 8) if f1 is not None else None,
    }


def _score_annotations(
    annotations: list[tuple[str, set[str], float]],
    predictions: dict[str, set[str]],
    topic_ids: list[str],
) -> dict[str, Any]:
    tp = fp = fn = 0.0
    per_label: dict[str, dict[str, Any]] = {}
    macro: dict[str, list[float]] = defaultdict(list)
    for paper_id, labels, weight in annotations:
        local_tp, local_fp, local_fn = _counts(labels, predictions[paper_id], weight)
        tp += local_tp
        fp += local_fp
        fn += local_fn
    for topic_id in topic_ids:
        label_tp = label_fp = label_fn = gold_support = predicted_support = 0.0
        for paper_id, labels, weight in annotations:
            gold_positive = topic_id in labels
            predicted_positive = topic_id in predictions[paper_id]
            label_tp += weight * (gold_positive and predicted_positive)
            label_fp += weight * (not gold_positive and predicted_positive)
            label_fn += weight * (gold_positive and not predicted_positive)
            gold_support += weight * gold_positive
            predicted_support += weight * predicted_positive
        metrics = _prf(label_tp, label_fp, label_fn)
        metrics["gold_support"] = round(gold_support, 8)
        metrics["predicted_support"] = round(predicted_support, 8)
        per_label[topic_id] = metrics
        if gold_support or predicted_support:
            for key in ("precision", "recall", "f1"):
                macro[key].append(0.0 if metrics[key] is None else metrics[key])
    return {
        "annotation_rows": len(annotations),
        "effective_paper_weight": round(math.fsum(weight for _, _, weight in annotations), 8),
        "micro": _prf(tp, fp, fn),
        "per_label": per_label,
        "macro": {
            key: round(math.fsum(values) / len(values), 8) if values else None
            for key, values in sorted(macro.items())
        },
    }


def _cohen_kappa(first: list[bool], second: list[bool]) -> float | None:
    if len(first) != len(second) or not first:
        return None
    n = len(first)
    observed = sum(a == b for a, b in zip(first, second)) / n
    first_positive = sum(first) / n
    second_positive = sum(second) / n
    expected = first_positive * second_positive + (1 - first_positive) * (1 - second_positive)
    return round((observed - expected) / (1 - expected), 8) if expected < 1 else None


def _agreement(
    overlap_ids: list[str],
    labels_a: dict[str, set[str]],
    labels_b: dict[str, set[str]],
    topic_ids: list[str],
) -> dict[str, Any]:
    exact = sum(labels_a[paper_id] == labels_b[paper_id] for paper_id in overlap_ids)
    jaccards = []
    for paper_id in overlap_ids:
        left, right = labels_a[paper_id], labels_b[paper_id]
        union = left | right
        jaccards.append(len(left & right) / len(union) if union else 1.0)
    per_topic = {}
    for topic_id in topic_ids:
        left = [topic_id in labels_a[paper_id] for paper_id in overlap_ids]
        right = [topic_id in labels_b[paper_id] for paper_id in overlap_ids]
        per_topic[topic_id] = {
            "cohen_kappa": _cohen_kappa(left, right),
            "positive_agreement_count": sum(a and b for a, b in zip(left, right)),
            "reviewer_a_positive_count": sum(left),
            "reviewer_b_positive_count": sum(right),
        }
    return {
        "overlap_paper_count": len(overlap_ids),
        "exact_set_agreement_count": exact,
        "exact_set_agreement_fraction": round(exact / len(overlap_ids), 8) if overlap_ids else None,
        "mean_jaccard": round(math.fsum(jaccards) / len(jaccards), 8) if jaccards else None,
        "per_topic": per_topic,
    }


def _predictions(graph: GraphArtifact, paper_ids: set[str], topic_ids: set[str]) -> dict[str, set[str]]:
    paper_nodes = {node.id for node in graph.nodes if node.label.value == "Paper"}
    if not paper_ids <= paper_nodes:
        raise ValueError(f"graph {graph.graph_version} is missing frozen topic-test paper nodes")
    result = {paper_id: set() for paper_id in paper_ids}
    for edge in graph.edges:
        if edge.relation == Relation.HAS_TOPIC and edge.source_id in paper_ids:
            if edge.target_id not in topic_ids:
                raise ValueError(f"graph {graph.graph_version} predicts a topic outside the frozen leaf taxonomy")
            result[edge.source_id].add(edge.target_id)
    if any(len(values) > 3 for values in result.values()):
        raise ValueError(f"graph {graph.graph_version} assigns more than three topics to a test paper")
    return result


def score_topic_review(
    graph_v1_path: Path,
    graph_v2_path: Path,
    topic_test_path: Path,
    taxonomy_path: Path,
    allocation_path: Path,
    master_sheet_path: Path,
    reviewer_a_path: Path,
    reviewer_b_path: Path,
    freeze_path: Path,
    graph_v2_summary_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Compare phrase and embedding labels using paper-normalized reviewer judgments.

    Each paper contributes total weight one. A single-review paper has weight one;
    each annotation on an overlap paper has weight one half. Independent overlap
    labels also supply exact-set agreement and per-label Cohen's kappa.
    """
    inputs = (
        graph_v1_path, graph_v2_path, topic_test_path, taxonomy_path, allocation_path,
        master_sheet_path, reviewer_a_path, reviewer_b_path, freeze_path,
        graph_v2_summary_path,
    )
    if output_path.resolve() in {path.resolve() for path in inputs}:
        raise ValueError("topic evaluation output must not overwrite an input")
    if output_path.exists() or output_path.is_symlink():
        raise ValueError(f"refusing to overwrite topic evaluation output: {output_path}")

    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    allocation = json.loads(allocation_path.read_text(encoding="utf-8"))
    summary = json.loads(graph_v2_summary_path.read_text(encoding="utf-8"))
    taxonomy = yaml.safe_load(taxonomy_path.read_text(encoding="utf-8"))
    assignment_freeze = freeze.get("review_packet", {}).get("topic_review_assignment", {})
    if assignment_freeze.get("allocation_manifest", {}).get("sha256") != _digest(allocation_path):
        raise ValueError("topic allocation manifest does not match the graph freeze")
    if freeze.get("topic_test_manifest_sha256") != _digest(topic_test_path):
        raise ValueError("topic test manifest does not match the graph freeze")
    if allocation.get("topic_test_manifest", {}).get("sha256") != _digest(topic_test_path):
        raise ValueError("topic allocation manifest does not bind to this test set")
    if allocation.get("master_sheet", {}).get("sha256") != _digest(master_sheet_path):
        raise ValueError("topic master sheet hash differs from the allocation manifest")
    if allocation.get("taxonomy", {}).get("sha256") != _digest(taxonomy_path):
        raise ValueError("topic taxonomy hash differs from the allocation manifest")
    if taxonomy.get("status") != "frozen" or taxonomy.get("calibration", {}).get("topic_test_sha256") != _digest(topic_test_path):
        raise ValueError("topic classifier or test manifest is not frozen together")
    taxonomy_binding = freeze.get("taxonomy_config", {}).get("sha256")
    if taxonomy_binding is None:  # Historical freezes used the canonical config key.
        taxonomy_binding = freeze.get("config_hashes", {}).get(str(taxonomy_path),
            freeze.get("config_hashes", {}).get("configs/topics-release-v1.yaml"))
    if taxonomy_binding != _digest(taxonomy_path):
        raise ValueError("topic taxonomy hash differs from the graph freeze")

    test_rows = list(_jsonl(topic_test_path))
    paper_ids_list = [row.get("paper_id") for row in test_rows]
    paper_ids = set(paper_ids_list)
    if len(paper_ids_list) != 50 or len(paper_ids) != 50 or any(not value for value in paper_ids):
        raise ValueError("topic evaluation requires the exact frozen 50-paper test set")
    topic_ids = sorted(leaf["id"] for leaf in taxonomy.get("leaves", []))
    topic_id_set = set(topic_ids)
    if len(topic_ids) != 16 or len(topic_id_set) != 16:
        raise ValueError("topic evaluation requires the frozen 16-leaf taxonomy")
    if allocation.get("assignment_method_version") != "d040-topic-review-allocation-v1":
        raise ValueError("topic allocation method is not the frozen D040 assignment")
    if allocation.get("predictions_included") is not False:
        raise ValueError("topic reviewer packets must be prediction-blind")

    with master_sheet_path.open(encoding="utf-8-sig", newline="") as handle:
        master_reader = csv.DictReader(handle)
        if master_reader.fieldnames != FIELDS:
            raise ValueError("topic master sheet has an unexpected schema")
        master_rows = list(master_reader)
    master_by_id = {row["paper_id"]: row for row in master_rows}
    if set(master_by_id) != paper_ids or len(master_rows) != 50:
        raise ValueError("topic master sheet differs from the frozen test frame")
    expected_catalog = json.dumps(
        [{key: leaf[key] for key in ("id", "name", "definition")} for leaf in taxonomy["leaves"]],
        ensure_ascii=False, separators=(",", ":"),
    )
    if any(
        row["topic_catalog"] != expected_catalog
        or any(row.get(field, "").strip() for field in ("label_1", "label_2", "label_3", "labeler", "notes"))
        for row in master_rows
    ):
        raise ValueError("topic master sheet must contain only the frozen catalog and blank annotation fields")

    assignment_ids = allocation.get("reviewer_paper_ids", {})
    if set(assignment_ids) != {"A", "B"}:
        raise ValueError("topic allocation must define reviewers A and B")
    ids_a, ids_b = assignment_ids["A"], assignment_ids["B"]
    if len(ids_a) != 30 or len(set(ids_a)) != 30 or len(ids_b) != 30 or len(set(ids_b)) != 30:
        raise ValueError("topic allocation must list 30 unique paper IDs per reviewer")
    assigned_a, assigned_b = set(ids_a), set(ids_b)
    if allocation.get("paper_count") != 50 or assigned_a | assigned_b != paper_ids:
        raise ValueError("topic allocation must assign 30 papers to each reviewer and cover all 50")
    overlap_ids = sorted(assigned_a & assigned_b)
    if len(overlap_ids) != 10:
        raise ValueError("topic allocation must have exactly 10 overlapping papers")
    expected_overlap = set(allocation.get("overlap_paper_ids", []))
    if set(overlap_ids) != expected_overlap:
        raise ValueError("topic allocation overlap IDs do not match reviewer assignments")
    master_venues = {paper_id: row["venue_id"] for paper_id, row in master_by_id.items()}
    venue_counts = {
        reviewer: dict(Counter(master_venues[paper_id] for paper_id in assigned))
        for reviewer, assigned in (("A", assigned_a), ("B", assigned_b))
    }
    expected_venue_counts = {
        "A": {"venue:aaai": 12, "venue:ijcai": 18},
        "B": {"venue:aaai": 12, "venue:ijcai": 18},
    }
    if venue_counts != expected_venue_counts or allocation.get("venue_counts") != expected_venue_counts:
        raise ValueError("topic reviewer allocation is not balanced across the frozen venues")
    if dict(Counter(master_venues[p] for p in overlap_ids)) != {"venue:aaai": 4, "venue:ijcai": 6}:
        raise ValueError("topic overlap must contain four AAAI and six IJCAI papers")
    labels_a = _read_topic_labels(
        reviewer_a_path, reviewer="A", expected_ids=assigned_a, master_rows=master_by_id,
        allowed_topics=topic_id_set,
    )
    labels_b = _read_topic_labels(
        reviewer_b_path, reviewer="B", expected_ids=assigned_b, master_rows=master_by_id,
        allowed_topics=topic_id_set,
    )

    freeze_sheets = assignment_freeze.get("reviewer_sheets", {})
    for reviewer in ("A", "B"):
        manifest_sheets = allocation.get("reviewer_sheets", {}).get(reviewer, {})
        frozen_sheets = freeze_sheets.get(reviewer, {})
        for kind in ("csv", "html"):
            item = manifest_sheets.get(kind, {})
            frozen_item = frozen_sheets.get(kind, {})
            packet_path = Path(item.get("path", ""))
            if not item.get("sha256") or frozen_item.get("sha256") != item.get("sha256"):
                raise ValueError(f"reviewer {reviewer} {kind} packet hash differs from the graph freeze")
            if not packet_path.is_file() or _digest(packet_path) != item["sha256"]:
                raise ValueError(f"reviewer {reviewer} {kind} packet no longer matches its frozen hash")

    graph_v1, graph_v1_hash = _read_graph(graph_v1_path)
    graph_v1_version = graph_v1.graph_version
    if graph_v1_hash != summary.get("inputs_sha256", {}).get("graph_v1_sha256"):
        raise ValueError("phrase-baseline graph hash differs from the v2 build summary")
    if graph_v1_version != summary.get("graph_v1_version"):
        raise ValueError("phrase-baseline graph version differs from the v2 build summary")
    phrase_predictions = _predictions(graph_v1, paper_ids, topic_id_set)
    del graph_v1

    graph_v2, graph_v2_hash = _read_graph(graph_v2_path)
    if graph_v2_hash != freeze.get("graph_sha256") or graph_v2_hash != summary.get("graph_sha256"):
        raise ValueError("embedding graph hash differs from the frozen release graph")
    if graph_v2.graph_version != freeze.get("graph_version") or graph_v2.graph_version != summary.get("graph_version"):
        raise ValueError("embedding graph version differs from the graph freeze")
    embedding_predictions = _predictions(graph_v2, paper_ids, topic_id_set)
    del graph_v2

    reviewer_labels = {"A": labels_a, "B": labels_b}
    assignment_count = Counter(paper_id for values in assignment_ids.values() for paper_id in values)
    weighted_annotations: list[tuple[str, set[str], float]] = []
    per_reviewer_annotations: dict[str, list[tuple[str, set[str], float]]] = {}
    for reviewer, paper_map in reviewer_labels.items():
        per_reviewer_annotations[reviewer] = [
            (paper_id, labels, 1.0) for paper_id, labels in paper_map.items()
        ]
        weighted_annotations.extend(
            (paper_id, labels, 1.0 / assignment_count[paper_id])
            for paper_id, labels in paper_map.items()
        )

    model_predictions = {
        "phrase_baseline": phrase_predictions,
        "embedding_classifier": embedding_predictions,
    }
    metrics = {}
    for model_name, predictions in model_predictions.items():
        metrics[model_name] = {
            "test_paper_coverage": {
                "eligible_papers": len(paper_ids),
                "labeled_papers": sum(bool(predictions[paper_id]) for paper_id in paper_ids),
                "coverage_fraction": round(sum(bool(predictions[paper_id]) for paper_id in paper_ids) / len(paper_ids), 8),
            },
            "paper_normalized_review_metrics": _score_annotations(weighted_annotations, predictions, topic_ids),
            "by_reviewer": {
                reviewer: _score_annotations(annotations, predictions, topic_ids)
                for reviewer, annotations in per_reviewer_annotations.items()
            },
        }

    result = {
        "status": "scored_pending_release_edge_audit",
        "evaluation_method_version": "d040-topic-partial-overlap-v1",
        "topic_test_paper_count": len(paper_ids),
        "annotation_judgment_count": sum(len(values) for values in assignment_ids.values()),
        "reviewer_assignment": {
            "A": len(assigned_a), "B": len(assigned_b), "overlap": len(overlap_ids),
            "union": len(assigned_a | assigned_b),
        },
        "weighting": {
            "method": "inverse_reviewer_count_per_paper",
            "description": "Each paper contributes total weight one; each reviewer label on a shared paper contributes one half.",
            "effective_paper_weight": round(math.fsum(weight for _, _, weight in weighted_annotations), 8),
        },
        "reviewer_agreement_on_overlap": _agreement(overlap_ids, labels_a, labels_b, topic_ids),
        "models": metrics,
        "inputs": {
            "topic_test_manifest": {"path": str(topic_test_path), "sha256": _digest(topic_test_path)},
            "taxonomy": {"path": str(taxonomy_path), "sha256": _digest(taxonomy_path)},
            "allocation_manifest": {"path": str(allocation_path), "sha256": _digest(allocation_path)},
            "master_sheet": {"path": str(master_sheet_path), "sha256": _digest(master_sheet_path)},
            "reviewer_a_export": {"path": str(reviewer_a_path), "sha256": _digest(reviewer_a_path)},
            "reviewer_b_export": {"path": str(reviewer_b_path), "sha256": _digest(reviewer_b_path)},
            "graph_v1_phrase_baseline": {"path": str(graph_v1_path), "sha256": graph_v1_hash, "graph_version": graph_v1_version},
            "graph_v2_embedding": {"path": str(graph_v2_path), "sha256": graph_v2_hash, "graph_version": freeze["graph_version"]},
            "graph_freeze": {"path": str(freeze_path), "sha256": _digest(freeze_path)},
            "graph_v2_summary": {"path": str(graph_v2_summary_path), "sha256": _digest(graph_v2_summary_path)},
        },
        "limitations": [
            "Reviewer identity and independence are input-declared and not authenticated by this program.",
            "Forty papers have one review and ten have two; agreement is reported only on the overlap.",
            "Paper-normalized metrics give each annotation on an overlap paper half weight; disagreement is retained as reviewer-level evidence rather than adjudicated into a synthetic consensus label.",
            "This topic evaluation is separate from the global/per-relation edge audit and does not certify the release.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return result
