"""Prepare and score a frozen, independently reviewed graph-edge audit.

Three review designs are supported, chosen by ``audit.review_design`` in the quality
config. ``double_review`` (the default) needs two independent reviews of every sampled
edge. ``split_with_overlap`` (release plan section 2.4, D040) reviews each sampled edge
once, split deterministically between two reviewers, with ``overlap_sample_size``
global-sample edges reviewed by both so agreement can be measured. The explicit
``single_reviewer`` fallback assigns each edge once with no overlap.
Complete packets are required unless partial scoring is explicitly requested.

This module validates audit evidence; it cannot establish who supplied reviewer
IDs or whether the review was actually independent. Synthetic inputs stay clearly
separate from any release claim.
"""

import csv
from collections import Counter
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Iterable
from urllib.parse import quote

import yaml

from scientific_network.contracts import GraphArtifact, Relation
from scientific_network.evaluation.precision import precision_interval
from scientific_network.evaluation.review_sheet import CONTEXT_FIELDS, ERROR_CATEGORIES, SheetContext, render_html
from scientific_network.graph.validate import graph_counts, validate_graph


METHOD_VERSION = "edge-audit-v1"
REVIEW_FIELDS = [
    "audit_id", "method_version", "graph_version", "graph_sha256",
    "quality_config_sha256", "readiness_sha256", "frame_sha256", "sampling_seed", "edge_id",
    "in_global_sample", "in_type_sample", "is_type_census", "reviewer_id",
    "endpoints_correct", "predicate_correct", "paper_time_correct",
    "evidence_verifiable", "decision", "reason", "reviewed_at",
]
ADJUDICATION_FIELDS = [
    "audit_id", "method_version", "graph_version", "graph_sha256",
    "quality_config_sha256", "readiness_sha256", "frame_sha256", "edge_id", "adjudicator_id",
    "decision", "reason", "reviewed_at",
]
VERDICTS = {"correct", "incorrect", "unverifiable"}
TRI_STATE = {"true", "false", "unknown"}
CHECK_FIELDS = ("endpoints_correct", "predicate_correct", "paper_time_correct", "evidence_verifiable")
DESIGNS = {"double_review", "split_with_overlap", "single_reviewer"}
# The split-design form adds an error category and reviewer context to the scored columns.
SPLIT_FIELDS = REVIEW_FIELDS + ["error_category"] + CONTEXT_FIELDS


def _read_graph(path: Path) -> tuple[GraphArtifact, bytes, list[str]]:
    raw = path.read_bytes()
    graph = GraphArtifact.model_validate_json(raw)
    errors = validate_graph(graph)
    if errors:
        raise ValueError("graph fails structural validation: " + "; ".join(errors[:10]))
    return graph, raw, errors


def _load_quality(path: Path) -> tuple[dict, dict]:
    raw = path.read_bytes()
    config = yaml.safe_load(raw)
    if not isinstance(config, dict) or not isinstance(config.get("audit"), dict):
        raise ValueError("quality config requires an audit mapping")
    audit = config["audit"]
    for key in ("global_sample_size", "per_type_sample_size", "random_seed", "independent_reviewers"):
        if type(audit.get(key)) is not int or audit[key] < 1:
            raise ValueError(f"audit.{key} must be a positive integer")
    for key in ("confidence_level", "min_precision", "wilson_lower_bound_must_exceed"):
        if type(audit.get(key)) not in (int, float) or not 0 < audit[key] < 1:
            raise ValueError(f"audit.{key} must be between 0 and 1")
    if audit.get("unverifiable_is_incorrect") is not True or audit.get("supplement_is_separate") is not True:
        raise ValueError("quality config must keep unverifiable edges incorrect and supplements separate")
    design = audit.get("review_design", "double_review")
    if design not in DESIGNS:
        raise ValueError(f"audit.review_design must be one of {sorted(DESIGNS)}")
    expected_reviewers = 1 if design == "single_reviewer" else 2
    if audit["independent_reviewers"] != expected_reviewers:
        raise ValueError("audit.independent_reviewers does not match review_design")
    if design in {"split_with_overlap", "single_reviewer"}:
        letters = audit.get("reviewer_ids")
        if (not isinstance(letters, list) or len(letters) != expected_reviewers or len(set(letters)) != expected_reviewers
                or any(not isinstance(letter, str) or not letter.strip() for letter in letters)):
            raise ValueError("audit.reviewer_ids must list the distinct reviewer IDs for this review design")
        overlap = audit.get("overlap_sample_size")
        if design == "single_reviewer" and overlap != 0:
            raise ValueError("single_reviewer requires zero overlap")
        if type(overlap) is not int or not 0 <= overlap <= audit["global_sample_size"]:
            raise ValueError("audit.overlap_sample_size must be an integer between 0 and the global sample size")
    return config, audit


def _rank(seed: int, purpose: str, edge_id: str) -> tuple[bytes, str]:
    return hashlib.sha256(f"{seed}\0{purpose}\0{edge_id}".encode("utf-8")).digest(), edge_id


def _assignments(audit: dict, global_ids: list[str], sampled: set[str]) -> dict[str, tuple[str, ...]]:
    """Deterministic reviewers per sampled edge: overlap edges get both, the rest alternate."""
    if audit.get("review_design") == "single_reviewer":
        return {edge_id: (audit["reviewer_ids"][0],) for edge_id in sampled}
    first, second = audit["reviewer_ids"]
    seed = audit["random_seed"]
    overlap = set(_sample_ids(global_ids, audit["overlap_sample_size"], seed, "overlap"))
    assignments = {edge_id: (first, second) for edge_id in overlap}
    rest = sorted(sampled - overlap, key=lambda edge_id: _rank(seed, "assign", edge_id))
    for index, edge_id in enumerate(rest):
        assignments[edge_id] = (first,) if index % 2 == 0 else (second,)
    return assignments


def cohens_kappa(pairs: list[tuple[str, str]]) -> float | None:
    """Cohen's kappa for two raters' categorical decisions; None when undefined (no variation)."""
    if not pairs:
        return None
    n = len(pairs)
    observed = sum(a == b for a, b in pairs) / n
    expected = sum(
        (sum(a == c for a, _ in pairs) / n) * (sum(b == c for _, b in pairs) / n)
        for c in {value for pair in pairs for value in pair}
    )
    return None if math.isclose(expected, 1.0) else (observed - expected) / (1 - expected)


def _frame(graph: GraphArtifact) -> tuple[list[dict], str]:
    rows = sorted(
        (edge.model_dump(mode="json") for edge in graph.edges),
        key=lambda row: row["edge_id"],
    )
    canonical = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return rows, hashlib.sha256(canonical).hexdigest()


def _sample_ids(edge_ids: Iterable[str], size: int, seed: int, purpose: str) -> list[str]:
    """Return a deterministic hash-ranked sample without replacement.

    Hash ranking acts as a seeded pseudorandom permutation and is stable across
    Python versions, unlike relying on a library PRNG's sampling implementation.
    """
    ranked = sorted(
        set(edge_ids),
        key=lambda edge_id: (
            hashlib.sha256(f"{seed}\0{purpose}\0{edge_id}".encode("utf-8")).digest(),
            edge_id,
        ),
    )
    return sorted(ranked[: min(size, len(ranked))])


def _audit_id(graph_version: str, frame_sha256: str, quality_config_sha256: str, readiness_sha256: str | None, seed: int) -> str:
    identity = f"{METHOD_VERSION}\0{graph_version}\0{frame_sha256}\0{quality_config_sha256}\0{readiness_sha256 or ''}\0{seed}".encode("utf-8")
    return "edge-audit:" + hashlib.sha256(identity).hexdigest()[:24]


def _check_readiness(path: Path | None, graph: GraphArtifact, graph_bytes: bytes) -> str | None:
    """D040: a readiness receipt is optional; when one is supplied for a real graph it must match."""
    if graph.is_synthetic or path is None:
        return None
    receipt_bytes = path.read_bytes()
    receipt = json.loads(receipt_bytes)
    if not isinstance(receipt, dict):
        raise ValueError("post-build audit-readiness receipt must be a JSON object")
    expected = {
        "status": "post_build_audit_ready",
        "graph_version": graph.graph_version,
        "graph_sha256": hashlib.sha256(graph_bytes).hexdigest(),
        "preconstruction_gates_passed": True,
        "graph_construction": "completed",
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise ValueError(f"readiness receipt {key} does not match the required post-build state")
    return hashlib.sha256(receipt_bytes).hexdigest()


def _expected_samples(graph: GraphArtifact, audit: dict, quality_config_sha256: str, readiness_sha256: str | None) -> tuple[dict, dict, list[str], str, str]:
    frame_rows, frame_sha = _frame(graph)
    frame_ids = [row["edge_id"] for row in frame_rows]
    if len(frame_ids) != len(set(frame_ids)):
        raise ValueError("audit frame contains duplicate edge IDs")
    if not frame_ids:
        raise ValueError("audit frame is empty")
    if not graph.is_synthetic and len(frame_ids) < audit["global_sample_size"]:
        raise ValueError("final edge audit requires the configured full global sample size")

    global_ids = _sample_ids(frame_ids, audit["global_sample_size"], audit["random_seed"], "global")
    ids_by_relation: dict[str, list[str]] = {}
    type_samples: dict[str, list[str]] = {}
    for relation in (item.value for item in Relation):
        ids = sorted(row["edge_id"] for row in frame_rows if row["relation"] == relation)
        ids_by_relation[relation] = ids
        if ids:
            type_seed = int.from_bytes(
                hashlib.sha256(f"{audit['random_seed']}\0type\0{relation}".encode("utf-8")).digest()[:8],
                "big",
            )
            type_samples[relation] = _sample_ids(ids, audit["per_type_sample_size"], type_seed, relation)
    return ids_by_relation, type_samples, global_ids, frame_sha, _audit_id(
        graph.graph_version, frame_sha, quality_config_sha256, readiness_sha256, audit["random_seed"]
    )


def _size_gates(graph: GraphArtifact, config: dict) -> dict | None:
    """Size gates of a real graph, each recorded as passed or failed (D040); None if synthetic."""
    if graph.is_synthetic:
        return None
    counts = graph_counts(graph)
    size = config.get("size")
    if not isinstance(size, dict):
        raise ValueError("quality config requires a size mapping")
    actual = {
        "min_domain_nodes": len(graph.nodes),
        "min_resolved_core_researchers": counts["resolved_core_researchers"],
        "min_unique_factual_edges": counts["unique_core_factual_edges"],
        "required_relation_types": len(counts["edges_by_relation"]),
    }
    gates = {}
    for key, value in actual.items():
        threshold = size.get(key)
        if type(threshold) is not int or threshold < 1:
            raise ValueError(f"quality config size.{key} must be a positive integer")
        passed = value == threshold if key == "required_relation_types" else value >= threshold
        gates[key] = {"required": threshold, "actual": value, "status": "passed" if passed else "failed"}
    return {"status": "passed" if all(g["status"] == "passed" for g in gates.values()) else "failed", "gates": gates}


def prepare_edge_audit_sample(
    input_path: Path,
    config_path: Path,
    output_path: Path,
    readiness_path: Path | None = None,
) -> dict:
    """Write deterministic blank forms; release designs also get HTML and assigned packets."""
    protected = {input_path.resolve(), config_path.resolve()}
    if readiness_path:
        protected.add(readiness_path.resolve())
    if output_path.resolve() in protected:
        raise ValueError("audit sample output must differ from graph, config, and readiness inputs")
    if output_path.exists() or output_path.is_symlink():
        raise ValueError("audit sample output already exists; use a new versioned path")

    graph, graph_bytes, _ = _read_graph(input_path)
    config, audit = _load_quality(config_path)
    config_sha = hashlib.sha256(config_path.read_bytes()).hexdigest()
    readiness_sha = _check_readiness(readiness_path, graph, graph_bytes)
    size_gates = _size_gates(graph, config)
    ids_by_relation, type_samples, global_ids, frame_sha, audit_id = _expected_samples(graph, audit, config_sha, readiness_sha)
    graph_sha = hashlib.sha256(graph_bytes).hexdigest()

    type_membership = {edge_id: relation for relation, ids in ids_by_relation.items() for edge_id in ids}
    selected = set(global_ids)
    for ids in type_samples.values():
        selected.update(ids)
    split = audit.get("review_design", "double_review") in {"split_with_overlap", "single_reviewer"}
    assignments = _assignments(audit, global_ids, selected) if split else {}
    contexts = SheetContext(graph) if split else None
    edges = {edge.edge_id: edge for edge in graph.edges} if split else {}
    html_path = output_path.with_suffix(".html")
    if split and (html_path.exists() or html_path.is_symlink()):
        raise ValueError("audit review sheet already exists; use a new versioned path")
    reviewer_paths = {}
    if split and audit.get("review_design") == "split_with_overlap":
        for reviewer in audit["reviewer_ids"]:
            path = output_path.with_stem(output_path.stem + "-reviewer-" + quote(reviewer, safe=""))
            for candidate in (path, path.with_suffix(".html")):
                if candidate.exists() or candidate.is_symlink():
                    raise ValueError("reviewer packet already exists; use a new versioned path")
            reviewer_paths[reviewer] = path
    rows = []
    for edge_id in sorted(selected):
        relation = type_membership[edge_id]
        type_ids = type_samples.get(relation, [])
        base = {
            "audit_id": audit_id,
            "method_version": METHOD_VERSION,
            "graph_version": graph.graph_version,
            "graph_sha256": graph_sha,
            "quality_config_sha256": config_sha,
            "readiness_sha256": readiness_sha or "",
            "frame_sha256": frame_sha,
            "sampling_seed": audit["random_seed"],
            "edge_id": edge_id,
            "in_global_sample": str(edge_id in global_ids).lower(),
            "in_type_sample": str(edge_id in type_ids).lower(),
            "is_type_census": str(bool(ids_by_relation[relation]) and len(type_ids) == len(ids_by_relation[relation])).lower(),
            "reviewer_id": "",
            "endpoints_correct": "",
            "predicate_correct": "",
            "paper_time_correct": "",
            "evidence_verifiable": "",
            "decision": "",
            "reason": "",
            "reviewed_at": "",
        }
        if not split:
            rows.append(base)
            continue
        assigned = assignments[edge_id]
        context, links = contexts.describe(edges[edge_id])
        for ref in edges[edge_id].evidence_ids:
            record = contexts.evidence.get(ref)
            if record is not None and record.kind == "curated_taxonomy":
                source_path = Path(record.source_locator.split("#", 1)[0])
                if source_path.is_file():
                    links.append({"label": "Frozen taxonomy config", "local_taxonomy": True,
                                  "url": os.path.relpath(source_path, output_path.parent)})
        context["is_overlap"] = str(len(assigned) == 2).lower()
        for reviewer in assigned:
            rows.append({**base, "reviewer_id": reviewer, "error_category": "", **context, "_links": links})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = SPLIT_FIELDS if split else REVIEW_FIELDS
    with output_path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "status": "synthetic_protocol_sample" if graph.is_synthetic else "review_form_prepared",
        "method_version": METHOD_VERSION,
        "review_design": audit.get("review_design", "double_review"),
        "graph_version": graph.graph_version,
        "is_synthetic": graph.is_synthetic,
        "graph_sha256": graph_sha,
        "quality_config_sha256": config_sha,
        "readiness_sha256": readiness_sha,
        "size_gates": size_gates,
        "frame_sha256": frame_sha,
        "audit_id": audit_id,
        "global_sample_size": len(global_ids),
        "per_type_sample_sizes": {key: len(value) for key, value in type_samples.items()},
        "union_sample_size": len(selected),
        "sampling_method": "seeded_sha256_rank_without_replacement",
        "review_form": str(output_path),
        "reviewer_ids_and_decisions": "not_supplied",
        "release_audit_performed": False,
    }
    if split:
        sheet_meta = {"audit_id": audit_id, "graph_version": graph.graph_version, "reviewer_ids": audit["reviewer_ids"]}
        sheet_rows = [
            {"review": {key: value for key, value in row.items() if key != "_links"},
             "context": {key: row[key] for key in CONTEXT_FIELDS}, "links": row["_links"]}
            for row in rows
        ]
        html_path.write_text(render_html(sheet_meta, SPLIT_FIELDS, sheet_rows), encoding="utf-8")
        reviewer_packets = {}
        for reviewer, path in reviewer_paths.items():
            assigned_rows = [row for row in rows if row["reviewer_id"] == reviewer]
            with path.open("x", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=SPLIT_FIELDS, extrasaction="ignore", lineterminator="\n")
                writer.writeheader()
                writer.writerows(assigned_rows)
            reviewer_html = path.with_suffix(".html")
            assigned_sheet_rows = [row for row in sheet_rows if row["review"]["reviewer_id"] == reviewer]
            reviewer_html.write_text(render_html({**sheet_meta, "reviewer_ids": [reviewer]}, SPLIT_FIELDS,
                                                 assigned_sheet_rows), encoding="utf-8")
            reviewer_packets[reviewer] = {kind: {"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                                         for kind, p in (("csv", path), ("html", reviewer_html))}
        summary.update({
            "reviewer_packets": reviewer_packets,
            "review_sheet": str(html_path),
            "overlap_sample_size": sum(len(a) == 2 for a in assignments.values()),
            "assigned_rows_per_reviewer": dict(Counter(row["reviewer_id"] for row in rows)),
            "form_rows": len(rows),
        })
    return summary


def _parse_bool(value: str, field: str) -> str:
    normalized = value.strip().lower()
    if normalized not in TRI_STATE:
        raise ValueError(f"{field} must be true, false, or unknown")
    return normalized


def _decision_from_checks(row: dict) -> str:
    checks = [
        _parse_bool(row.get(field, ""), field)
        for field in ("endpoints_correct", "predicate_correct", "paper_time_correct", "evidence_verifiable")
    ]
    if "false" in checks:
        return "incorrect"
    if "unknown" in checks:
        return "unverifiable"
    return "correct"


def _review_decision(row: dict, split: bool) -> tuple[str, str]:
    """Return (decision, error_category) for one review row, enforcing internal consistency."""
    checks = [row.get(field, "").strip() for field in CHECK_FIELDS]
    if split and not any(checks):
        # The release design records the verdict directly; the four legacy checks may stay blank.
        decision = row["decision"].strip().lower()
        if decision not in VERDICTS:
            raise ValueError("review decision must be correct, incorrect, or unverifiable")
    else:
        decision = _decision_from_checks(row)
        if row["decision"].strip().lower() != decision:
            raise ValueError("review decision conflicts with the four recorded review checks")
    category = row.get("error_category", "").strip().lower()
    if split:
        if decision == "correct" and category:
            raise ValueError("error_category must be blank for a correct decision")
        if decision != "correct" and category not in ERROR_CATEGORIES:
            raise ValueError("incorrect/unverifiable decisions need an error_category from " + ", ".join(ERROR_CATEGORIES))
    return decision, category


def _load_csv(path: Path | None, fields: list[str]) -> list[dict]:
    if path is None:
        return []
    # Complete support ledgers can exceed Python's small 128 KiB CSV default.
    # Keep a documented finite cap and restore the process setting after parsing.
    previous_limit = csv.field_size_limit()
    try:
        csv.field_size_limit(max(previous_limit, 64 * 1024 * 1024))
        with path.open(newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream)
            missing = set(fields) - set(reader.fieldnames or [])
            if missing:
                raise ValueError(f"{path} missing columns: " + ", ".join(sorted(missing)))
            rows = list(reader)
            if len(reader.fieldnames or []) != len(set(reader.fieldnames or [])) or any(
                None in row or any(value is None for value in row.values()) for row in rows
            ):
                raise ValueError(f"{path} contains malformed CSV rows or duplicate columns")
            return rows
    except csv.Error as exc:
        raise ValueError(f"{path} contains invalid CSV: {exc}") from exc
    finally:
        csv.field_size_limit(previous_limit)



def evaluate_edge_audit(
    input_path: Path,
    reviews_path: Path | list[Path],
    config_path: Path,
    output_path: Path,
    adjudications_path: Path | None = None,
    readiness_path: Path | None = None,
    *, allow_partial: bool = False,
) -> tuple[dict, int]:
    """Validate frozen assignments and score returned judgments with required adjudications."""
    review_paths = [reviews_path] if isinstance(reviews_path, Path) else list(reviews_path)
    if not review_paths or len({p.resolve() for p in review_paths}) != len(review_paths):
        raise ValueError("supply distinct completed review export paths")
    protected = {input_path.resolve(), config_path.resolve(), *(p.resolve() for p in review_paths)}
    if adjudications_path:
        protected.add(adjudications_path.resolve())
    if readiness_path:
        protected.add(readiness_path.resolve())
    if output_path.resolve() in protected:
        raise ValueError("evaluation output must differ from all inputs")
    if output_path.exists() or output_path.is_symlink():
        raise ValueError("evaluation output already exists; use a new versioned path")

    graph, graph_bytes, _ = _read_graph(input_path)
    config, audit = _load_quality(config_path)
    config_sha = hashlib.sha256(config_path.read_bytes()).hexdigest()
    readiness_sha = _check_readiness(readiness_path, graph, graph_bytes)
    size_gates = _size_gates(graph, config)
    ids_by_relation, type_samples, global_ids, frame_sha, audit_id = _expected_samples(graph, audit, config_sha, readiness_sha)
    graph_sha = hashlib.sha256(graph_bytes).hexdigest()
    if not graph.is_synthetic:
        factual = config.get("size", {}).get("factual_relations", [])
        if len(set(factual)) != 4:
            raise ValueError("quality config must define the four factual relations")

    global_set = set(global_ids)
    type_sets = {relation: set(ids) for relation, ids in type_samples.items()}
    relation_for_edge = {edge_id: relation for relation, ids in ids_by_relation.items() for edge_id in ids}
    expected_union = global_set.union(*(type_sets.values() or [set()]))
    split = audit.get("review_design", "double_review") in {"split_with_overlap", "single_reviewer"}
    assignments = _assignments(audit, global_ids, expected_union) if split else {}
    reviews = [row for path in review_paths for row in _load_csv(path, REVIEW_FIELDS)]
    if not reviews:
        raise ValueError("review packet contains no review rows")
    groups: dict[str, list[dict]] = {}
    reviewer_ids = set()
    for row in reviews:
        edge_id = row["edge_id"].strip()
        if edge_id not in expected_union:
            raise ValueError("review row edge is outside the frozen audit sample")
        expected_type = relation_for_edge[edge_id]
        expected_values = {
            "audit_id": audit_id,
            "method_version": METHOD_VERSION,
            "graph_version": graph.graph_version,
            "graph_sha256": graph_sha,
            "quality_config_sha256": config_sha,
            "readiness_sha256": readiness_sha or "",
            "frame_sha256": frame_sha,
            "sampling_seed": str(audit["random_seed"]),
            "in_global_sample": str(edge_id in global_set).lower(),
            "in_type_sample": str(edge_id in type_sets.get(expected_type, set())).lower(),
            "is_type_census": str(bool(ids_by_relation[expected_type]) and len(type_sets.get(expected_type, set())) == len(ids_by_relation[expected_type])).lower(),
        }
        for field, expected in expected_values.items():
            if row[field].strip().lower() != expected.lower():
                raise ValueError(f"review row {field} does not match the frozen frame/sample")
        reviewer_id = row["reviewer_id"].strip()
        if not reviewer_id:
            raise ValueError("reviewer_id is required; blank sample forms are not completed reviews")
        reviewer_ids.add(reviewer_id)
        decision, category = _review_decision(row, split)
        reviewed_at = datetime.fromisoformat(row["reviewed_at"].strip().replace("Z", "+00:00"))
        if reviewed_at.tzinfo is None or not row["reason"].strip() and decision != "correct":
            raise ValueError("review timestamp needs a timezone; incorrect/unverifiable decisions need a reason")
        row["_decision"], row["_category"] = decision, category
        groups.setdefault(edge_id, []).append(row)

    if split and not reviewer_ids <= set(audit["reviewer_ids"]):
        raise ValueError("review packet contains a reviewer ID outside audit.reviewer_ids")
    if not split and (len(reviewer_ids) > 2 or (not allow_partial and len(reviewer_ids) != 2)):
        raise ValueError("review packet must contain exactly the configured number of distinct reviewer IDs")
    missing_assignments = []
    for edge_id in sorted(expected_union):
        given = [row["reviewer_id"].strip() for row in groups.get(edge_id, [])]
        if len(given) != len(set(given)):
            raise ValueError("duplicate review for the frozen reviewer assignment")
        expected = set(assignments[edge_id]) if split else reviewer_ids
        if not set(given) <= expected:
            raise ValueError("review rows do not match the frozen reviewer assignment")
        missing_count = (len(expected) if split else 2) - len(given)
        if missing_count:
            missing_assignments.append({"edge_id": edge_id, "missing_count": missing_count,
                                        "missing_reviewer_ids": sorted(expected - set(given)),
                                        "unknown_reviewer_slots": missing_count - len(expected - set(given))})
            if not allow_partial:
                message = ("review rows do not match the frozen reviewer assignment for every sampled edge" if split
                           else "every sampled edge must have exactly one review from each of two reviewers")
                raise ValueError(message)
    partial = bool(missing_assignments)

    adjudications = _load_csv(adjudications_path, ADJUDICATION_FIELDS)
    adjudication_by_edge = {}
    adjudication_category = {}
    for row in adjudications:
        edge_id = row["edge_id"].strip()
        if edge_id not in expected_union or edge_id in adjudication_by_edge:
            raise ValueError("adjudication edge must be sampled and appear exactly once")
        for field, expected in {
            "audit_id": audit_id,
            "method_version": METHOD_VERSION,
            "graph_version": graph.graph_version,
            "graph_sha256": graph_sha,
            "quality_config_sha256": config_sha,
            "readiness_sha256": readiness_sha or "",
            "frame_sha256": frame_sha,
        }.items():
            if row[field].strip() != expected:
                raise ValueError(f"adjudication {field} does not match the frozen frame")
        adjudicator = row["adjudicator_id"].strip()
        decision = row["decision"].strip().lower()
        if not adjudicator or decision not in VERDICTS or not row["reason"].strip():
            raise ValueError("adjudication requires an ID, valid decision, and reason")
        timestamp = datetime.fromisoformat(row["reviewed_at"].strip().replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            raise ValueError("adjudication timestamp needs a timezone")
        adjudication_by_edge[edge_id] = decision
        category = row.get("error_category", "").strip().lower()
        if category and (category not in ERROR_CATEGORIES or decision == "correct"):
            raise ValueError("adjudication error_category must be valid and blank for correct decisions")
        adjudication_category[edge_id] = category

    final_decisions = {}
    final_category = {}
    paired = []
    for edge_id, rows in groups.items():
        rows.sort(key=lambda item: item["reviewer_id"].strip())
        if len(rows) == 1:
            if edge_id in adjudication_by_edge:
                raise ValueError("adjudication supplied for an edge without reviewer disagreement")
            final_decisions[edge_id], final_category[edge_id] = rows[0]["_decision"], rows[0]["_category"]
            continue
        decisions = [row["_decision"] for row in rows]
        paired.append((decisions[0], decisions[1]))
        if decisions[0] == decisions[1]:
            if edge_id in adjudication_by_edge:
                raise ValueError("agreed reviews must not have an adjudication row")
            final_decisions[edge_id] = decisions[0]
            final_category[edge_id] = next((row["_category"] for row in rows if row["_category"]), "")
        else:
            if edge_id not in adjudication_by_edge:
                raise ValueError("review disagreement requires one adjudication")
            final_decisions[edge_id] = adjudication_by_edge[edge_id]
            final_category[edge_id] = adjudication_category[edge_id] or next(
                (row["_category"] for row in rows if row["_category"]), "")
    unexpected_adjudications = set(adjudication_by_edge) - {
        edge_id for edge_id, rows in groups.items() if len(rows) == 2 and rows[0]["_decision"] != rows[1]["_decision"]}
    if unexpected_adjudications:
        raise ValueError("adjudication supplied for an edge without reviewer disagreement")

    def metric(edge_ids: set[str], census: bool = False) -> dict:
        planned_ids = edge_ids
        edge_ids = edge_ids & final_decisions.keys()
        census = census and edge_ids == planned_ids
        decisions = [final_decisions[edge_id] for edge_id in sorted(edge_ids)]
        correct = sum(decision == "correct" for decision in decisions)
        result = {
            "planned_total": len(planned_ids),
            "missing_edges": len(planned_ids - edge_ids),
            "correct": correct,
            "incorrect": sum(decision == "incorrect" for decision in decisions),
            "unverifiable": sum(decision == "unverifiable" for decision in decisions),
            "total": len(decisions),
            "precision": correct / len(decisions) if decisions else None,
            "is_census": census,
        }
        result["wilson_95"] = (
            None if census or not decisions
            else precision_interval(correct, len(decisions), audit["confidence_level"])
        )
        return result

    global_metric = metric(global_set, census=len(global_set) == len(relation_for_edge))
    per_type = {}
    for relation, edge_ids in sorted(type_sets.items()):
        all_ids = set(ids_by_relation[relation])
        is_census = len(edge_ids) == len(all_ids)
        item = metric(edge_ids, census=is_census)
        if not is_census and item["total"]:
            item["wilson_95"] = precision_interval(item["correct"], item["total"], audit["confidence_level"])
        per_type[relation] = item
    macro_values = [item["precision"] for item in per_type.values() if item["precision"] is not None]
    point_pass = None if global_metric["precision"] is None else global_metric["precision"] >= audit["min_precision"]
    synthetic = graph.is_synthetic
    interval_pass = (
        None if global_metric["wilson_95"] is None
        else global_metric["wilson_95"]["wilson_lower"] > audit["wilson_lower_bound_must_exceed"]
    )
    # Course threshold (point estimate above 90%) is reported next to the project target.
    course_threshold = audit.get("course_point_estimate_must_exceed")
    course_gate = None if synthetic or course_threshold is None or global_metric["precision"] is None else {
        "threshold": course_threshold,
        "point_estimate": global_metric["precision"],
        "status": "pass" if global_metric["precision"] > course_threshold else "fail",
    }
    agreed = sum(a == b for a, b in paired)
    agreement = {
        "edges_reviewed_by_both": len(paired),
        "agreed": agreed,
        "percent": agreed / len(paired) if paired else None,
        "cohens_kappa": cohens_kappa(paired),
        "availability": "available" if paired else "unavailable: no edges reviewed by both people",
        "kappa_note": None if cohens_kappa(paired) is not None or not paired
        else "undefined: both reviewers used a single category on every overlap edge",
    }

    def categories(edge_ids: set[str]) -> dict:
        counts = Counter(
            final_category[edge_id] or ("unverifiable" if final_decisions[edge_id] == "unverifiable" else "uncategorized")
            for edge_id in edge_ids & final_decisions.keys() if final_decisions[edge_id] != "correct"
        )
        return dict(sorted(counts.items()))
    score_status = (
        "not_applicable_synthetic" if synthetic
        else "partial" if partial
        else "pass" if point_pass and interval_pass
        else "fail"
    )
    result = {
        "status": "synthetic_protocol_only" if synthetic else score_status,
        "method_version": METHOD_VERSION,
        "graph_version": graph.graph_version,
        "is_synthetic": synthetic,
        "release_status": "ineligible_synthetic" if synthetic else "not_certified_by_this_command",
        "reviewer_identity_status": "input_declared_not_independently_verified",
        "input_sha256": hashlib.sha256(graph_bytes).hexdigest(),
        "config_sha256": config_sha,
        "review_design": audit.get("review_design", "double_review"),
        "readiness_sha256": readiness_sha,
        "size_gates": size_gates,
        "review_packet_sha256": hashlib.sha256(review_paths[0].read_bytes()).hexdigest() if len(review_paths) == 1 else None,
        "review_packets": [{"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in review_paths],
        "partial_scoring_opt_in": allow_partial,
        "audit_completion": "partial" if partial else "complete",
        "completion": {
            "planned_assignments": len(reviews) + sum(r["missing_count"] for r in missing_assignments),
            "completed_assignments": len(reviews),
            "missing_assignment_count": sum(r["missing_count"] for r in missing_assignments),
            "missing_assignments": missing_assignments,
            "overlap_planned": sum(len(a) == 2 for a in assignments.values()) if split else len(expected_union),
            "overlap_completed": len(paired),
            "global_reviewed_n": global_metric["total"], "global_planned_n": len(global_set),
            "relation_coverage": {relation: {
                "global_planned": len(global_set & set(ids)),
                "global_reviewed": len(global_set & set(ids) & final_decisions.keys()),
                "supplement_planned": len(type_sets.get(relation, set())),
                "supplement_reviewed": len(type_sets.get(relation, set()) & final_decisions.keys()),
            } for relation, ids in sorted(ids_by_relation.items())},
        },
        "adjudication_packet_sha256": hashlib.sha256(adjudications_path.read_bytes()).hexdigest() if adjudications_path else None,
        "frame_sha256": frame_sha,
        "audit_id": audit_id,
        "sampling_method": "seeded_sha256_rank_without_replacement",
        "global": global_metric,
        "per_type": per_type,
        "macro_per_type_precision": sum(macro_values) / len(macro_values) if macro_values else None,
        "numeric_gate_status": score_status,
        "global_point_precision_gate": None if synthetic else point_pass,
        "global_wilson_lower_gate": None if synthetic else interval_pass,
        "course_gate": course_gate,
        "agreement": agreement,
        "error_categories": {"global_sample": categories(global_set), "all_sampled_edges": categories(set(final_decisions))},
        "sampled_global_edge_ids": len(global_set),
        "sampled_type_edge_ids": {relation: len(ids) for relation, ids in type_sets.items()},
        "reviewers": sorted(reviewer_ids),
        "review_rows_per_reviewer": dict(sorted(Counter(row["reviewer_id"].strip() for row in reviews).items())),
        "limitations": [
            "The command checks packet structure and reports supplied judgments; it cannot verify reviewer identity or independence.",
            "Unverifiable edges count as incorrect. Per-type supplements are separate from the uniform global estimate.",
            *(["Partial audit: only returned completed judgments are scored. Missing reviews are not correct; nonresponse may bias the estimate and interval. The planned full audit was not completed."] if partial else []),
            *(["Single-reviewer fallback: one actual reviewer, no overlap; agreement statistics are unavailable."] if audit.get("review_design") == "single_reviewer" else []),
            *(["Under split_with_overlap only the overlap edges were reviewed by both reviewers; agreement is measured on those, and every other sampled edge was judged by one reviewer."] if audit.get("review_design") == "split_with_overlap" else []),
            "Synthetic fixtures are protocol tests only and cannot support scientific or release claims.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
    return result, 0 if synthetic or score_status == "pass" else 1


def prepare_edge_adjudications(review_paths: list[Path], output_path: Path) -> dict:
    """Prepare blank decisions for returned conflicts; this does not score or certify reviews.

    Final scoring still checks graph/config/frame/assignments. This helper avoids
    manually copying provenance hashes into the adjudication form.
    """
    if output_path.exists() or output_path.is_symlink() or output_path.resolve() in {p.resolve() for p in review_paths}:
        raise ValueError("adjudication form must use an unused output path")
    reviews = [row for path in review_paths for row in _load_csv(path, REVIEW_FIELDS)]
    if not reviews:
        raise ValueError("no completed review rows supplied")
    common_fields = [f for f in ADJUDICATION_FIELDS if f not in {'edge_id', 'adjudicator_id', 'decision', 'reason', 'reviewed_at'}]
    common = {f: reviews[0][f] for f in common_fields}
    groups = {}
    seen = set()
    for row in reviews:
        if any(row[f] != common[f] for f in common_fields):
            raise ValueError("review exports do not belong to the same frozen audit/frame")
        key = (row['edge_id'], row['reviewer_id'])
        if key in seen or not row['reviewer_id'].strip():
            raise ValueError("duplicate or blank reviewer assignment")
        seen.add(key)
        decision, _ = _review_decision(row, 'error_category' in row)
        timestamp = datetime.fromisoformat(row['reviewed_at'].replace('Z', '+00:00'))
        if timestamp.tzinfo is None or (decision != 'correct' and not row['reason'].strip()):
            raise ValueError("completed reviews need timezone timestamps and reasons for errors")
        groups.setdefault(row['edge_id'], []).append((row['reviewer_id'], decision))
    fields = ADJUDICATION_FIELDS + ['error_category', 'returned_judgments']
    rows = []
    for edge, judgments in sorted(groups.items()):
        if len(judgments) > 2:
            raise ValueError("more than two reviewer judgments for an edge")
        if len(judgments) == 2 and judgments[0][1] != judgments[1][1]:
            rows.append({**common, 'edge_id': edge, 'returned_judgments': json.dumps(sorted(judgments), ensure_ascii=False)})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    return {'status': 'blank_adjudication_form_prepared', 'disagreements': len(rows), 'output': str(output_path),
            'frame_assignment_validation': 'performed_by_score_edge_audit', 'release_audit_performed': False}
