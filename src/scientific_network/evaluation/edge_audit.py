"""Prepare and score a frozen, independently reviewed graph-edge audit.

This module validates audit evidence; it cannot establish who supplied reviewer
IDs or whether the review was actually independent. Synthetic inputs stay clearly
separate from any release claim.
"""

import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Iterable

import yaml

from scientific_network.contracts import GraphArtifact, Relation
from scientific_network.evaluation.precision import precision_interval
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
    if audit["independent_reviewers"] != 2:
        raise ValueError("the edge audit contract requires exactly two independent reviewers")
    if audit.get("unverifiable_is_incorrect") is not True or audit.get("supplement_is_separate") is not True:
        raise ValueError("quality config must keep unverifiable edges incorrect and supplements separate")
    return config, audit


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
    if graph.is_synthetic:
        return None
    if path is None:
        raise ValueError("a post-build audit-readiness receipt is required for non-synthetic graphs")
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
    if not graph.is_synthetic:
        missing = sorted(relation for relation, ids in ids_by_relation.items() if not ids)
        if missing:
            raise ValueError("final audit frame lacks required relation types: " + ", ".join(missing))
    return ids_by_relation, type_samples, global_ids, frame_sha, _audit_id(
        graph.graph_version, frame_sha, quality_config_sha256, readiness_sha256, audit["random_seed"]
    )


def _check_release_size(graph: GraphArtifact, config: dict) -> None:
    if graph.is_synthetic:
        return
    counts = graph_counts(graph)
    size = config.get("size")
    if not isinstance(size, dict):
        raise ValueError("quality config requires a size mapping")
    checks = {
        "min_domain_nodes": len(graph.nodes),
        "min_resolved_core_researchers": counts["resolved_core_researchers"],
        "min_unique_factual_edges": counts["unique_core_factual_edges"],
        "required_relation_types": len(counts["edges_by_relation"]),
    }
    for key, actual in checks.items():
        threshold = size.get(key)
        if type(threshold) is not int or threshold < 1:
            raise ValueError(f"quality config size.{key} must be a positive integer")
        if actual < threshold:
            raise ValueError(f"post-build graph fails configured size gate {key}: {actual} < {threshold}")
    if len(counts["edges_by_relation"]) != size["required_relation_types"]:
        raise ValueError("post-build graph does not contain every required relation type")


def prepare_edge_audit_sample(
    input_path: Path,
    config_path: Path,
    output_path: Path,
    readiness_path: Path | None = None,
) -> dict:
    """Write a blank review form for the deterministic samples of a frozen graph."""
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
    _check_release_size(graph, config)
    ids_by_relation, type_samples, global_ids, frame_sha, audit_id = _expected_samples(graph, audit, config_sha, readiness_sha)
    graph_sha = hashlib.sha256(graph_bytes).hexdigest()

    type_membership = {edge_id: relation for relation, ids in ids_by_relation.items() for edge_id in ids}
    selected = set(global_ids)
    for ids in type_samples.values():
        selected.update(ids)
    rows = []
    for edge_id in sorted(selected):
        relation = type_membership[edge_id]
        type_ids = type_samples.get(relation, [])
        rows.append({
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
        })
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return {
        "status": "synthetic_protocol_sample" if graph.is_synthetic else "review_form_prepared",
        "method_version": METHOD_VERSION,
        "graph_version": graph.graph_version,
        "is_synthetic": graph.is_synthetic,
        "graph_sha256": graph_sha,
        "quality_config_sha256": config_sha,
        "readiness_sha256": readiness_sha,
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


def _load_csv(path: Path | None, fields: list[str]) -> list[dict]:
    if path is None:
        return []
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        missing = set(fields) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path} missing columns: " + ", ".join(sorted(missing)))
        return [{key: value or "" for key, value in row.items()} for row in reader]


def evaluate_edge_audit(
    input_path: Path,
    reviews_path: Path,
    config_path: Path,
    output_path: Path,
    adjudications_path: Path | None = None,
    readiness_path: Path | None = None,
) -> tuple[dict, int]:
    """Validate the frame/sample and score two reviews plus required adjudications."""
    protected = {input_path.resolve(), reviews_path.resolve(), config_path.resolve()}
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
    _check_release_size(graph, config)
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
    reviews = _load_csv(reviews_path, REVIEW_FIELDS)
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
        decision = _decision_from_checks(row)
        if row["decision"].strip().lower() != decision:
            raise ValueError("review decision conflicts with the four recorded review checks")
        reviewed_at = datetime.fromisoformat(row["reviewed_at"].strip().replace("Z", "+00:00"))
        if reviewed_at.tzinfo is None or not row["reason"].strip() and decision != "correct":
            raise ValueError("review timestamp needs a timezone; incorrect/unverifiable decisions need a reason")
        row["_decision"] = decision
        groups.setdefault(edge_id, []).append(row)

    if len(reviewer_ids) != audit["independent_reviewers"]:
        raise ValueError("review packet must contain exactly the configured number of distinct reviewer IDs")
    for edge_id in expected_union:
        edge_rows = groups.get(edge_id, [])
        ids = [row["reviewer_id"].strip() for row in edge_rows]
        if len(edge_rows) != 2 or len(set(ids)) != 2 or set(ids) != reviewer_ids:
            raise ValueError("every sampled edge must have exactly one review from each of two reviewers")

    adjudications = _load_csv(adjudications_path, ADJUDICATION_FIELDS)
    adjudication_by_edge = {}
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

    final_decisions = {}
    for edge_id, rows in groups.items():
        decisions = [row["_decision"] for row in rows]
        if decisions[0] == decisions[1]:
            if edge_id in adjudication_by_edge:
                raise ValueError("agreed reviews must not have an adjudication row")
            final_decisions[edge_id] = decisions[0]
        else:
            if edge_id not in adjudication_by_edge:
                raise ValueError("review disagreement requires one adjudication")
            final_decisions[edge_id] = adjudication_by_edge[edge_id]
    unexpected_adjudications = set(adjudication_by_edge) - {edge_id for edge_id, rows in groups.items() if rows[0]["_decision"] != rows[1]["_decision"]}
    if unexpected_adjudications:
        raise ValueError("adjudication supplied for an edge without reviewer disagreement")

    def metric(edge_ids: set[str], census: bool = False) -> dict:
        decisions = [final_decisions[edge_id] for edge_id in sorted(edge_ids)]
        correct = sum(decision == "correct" for decision in decisions)
        result = {
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
    point_pass = global_metric["precision"] >= audit["min_precision"]
    synthetic = graph.is_synthetic
    interval_pass = (
        None if global_metric["wilson_95"] is None
        else global_metric["wilson_95"]["wilson_lower"] > audit["wilson_lower_bound_must_exceed"]
    )
    score_status = (
        "not_applicable_synthetic" if synthetic
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
        "readiness_sha256": readiness_sha,
        "review_packet_sha256": hashlib.sha256(reviews_path.read_bytes()).hexdigest(),
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
        "sampled_global_edge_ids": len(global_set),
        "sampled_type_edge_ids": {relation: len(ids) for relation, ids in type_sets.items()},
        "reviewers": sorted(reviewer_ids),
        "limitations": [
            "The command checks packet structure and reports supplied judgments; it cannot verify reviewer identity or independence.",
            "Unverifiable edges count as incorrect. Per-type supplements are separate from the uniform global estimate.",
            "Synthetic fixtures are protocol tests only and cannot support scientific or release claims.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
    return result, 0 if synthetic or score_status == "pass" else 1
