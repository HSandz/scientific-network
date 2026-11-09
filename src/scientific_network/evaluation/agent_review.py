"""Hash-bound agent provenance checks around the unchanged release scorers.

These checks establish declared provenance and file integrity, not authenticity
of an agent's source interpretation or statistical evaluator independence.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from typing import Any

import yaml

from scientific_network.evaluation import edge_audit, topic_eval


AI_METADATA = {
    "evaluation_kind": "ai_agent_review",
    "human_validation": "not_performed",
    "reviewer_independence": "not_established",
    "verified_course_accuracy": "not_established",
    "numeric_gate_scope": "ai_assessed_only",
}
DEPTHS = {"primary_source", "secondary_source_only", "internal_only", "unavailable"}
SOURCE_KINDS = {"same_source_as_construction", "independent_source"}
LEDGER_FIELDS = {
    "unit_id", "reviewer_id", "reviewer_kind", "evaluator_run_id", "decision",
    "reason", "source_url", "source_locator", "source_sha256", "evidence_depth",
    "source_independence", "reviewed_at",
}


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _time(value: Any, field: str) -> datetime:
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be an ISO timestamp with timezone") from exc
    if result.tzinfo is None:
        raise ValueError(f"{field} must have a timezone")
    return result


def _bindings(items: Any, description: str) -> dict[Path, str]:
    if not isinstance(items, list) or not items:
        raise ValueError(f"{description} must list hash-bound files")
    result = {}
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not item["path"]:
            raise ValueError(f"invalid {description} binding")
        path = Path(item["path"]).resolve()
        digest = item.get("sha256", "")
        if path in result or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError(f"duplicate or invalid {description} binding")
        if not path.is_file() or _digest(path) != digest:
            raise ValueError(f"{description} hash mismatch: {path}")
        result[path] = digest
    return result


def _require_bindings(paths: list[Path], bindings: dict[Path, str], description: str) -> None:
    for path in paths:
        if path.resolve() not in bindings:
            raise ValueError(f"{description} does not bind required input: {path}")


def _runs(freeze: dict, created: datetime) -> dict[str, dict]:
    runs = freeze.get("evaluator_runs")
    if not isinstance(runs, list) or not runs:
        raise ValueError("freeze requires actual evaluator_runs metadata")
    result = {}
    owners: dict[str, str] = {}
    for run in runs:
        fields = ("reviewer_id", "evaluator_run_id", "context_id", "model", "provider", "started_at")
        if not isinstance(run, dict) or any(not isinstance(run.get(key), str) or not run[key].strip() for key in fields):
            raise ValueError("evaluator run metadata is incomplete; use explicit unknown for unavailable model/provider")
        reviewer, run_id = run["reviewer_id"], run["evaluator_run_id"]
        if reviewer not in {"A", "B", "ADJ"} or run_id in result or run_id == "unknown" or run["context_id"] == "unknown":
            raise ValueError("evaluator runs must have distinct actual IDs and known reviewer channels")
        if run.get("reviewer_kind") != "ai_agent":
            raise ValueError("evaluator reviewer_kind must be ai_agent")
        context_id = run["context_id"]
        if context_id in owners and owners[context_id] != reviewer:
            raise ValueError("reviewer channels must not share an evaluator context")
        owners[context_id] = reviewer
        if _time(run["started_at"], "run started_at") < created:
            raise ValueError("evaluation freeze must precede evaluator run start")
        result[run_id] = run
    if not {"A", "B"} <= {run["reviewer_id"] for run in result.values()}:
        raise ValueError("isolated agent review requires both A and B evaluator runs")
    return result


def _assignments(freeze: dict, kind: str) -> set[tuple[str, str]]:
    assignments = freeze.get("assignments", {}).get(kind)
    if not isinstance(assignments, dict) or set(assignments) != {"A", "B"}:
        raise ValueError(f"freeze {kind} assignments must define A and B")
    result = set()
    for reviewer, ids in assignments.items():
        if not isinstance(ids, list) or any(not isinstance(i, str) or not i for i in ids) or len(ids) != len(set(ids)):
            raise ValueError(f"freeze {kind} assignments must contain unique unit IDs")
        result.update((unit, reviewer) for unit in ids)
    return result


def _source(row: dict, source_digests: dict[Path, str]) -> None:
    depth = row["evidence_depth"]
    if depth not in DEPTHS or row["source_independence"] not in SOURCE_KINDS:
        raise ValueError("invalid evidence depth or source independence category")
    supported = depth in {"primary_source", "secondary_source_only"}
    if supported and (not row["source_url"].strip() or not row["source_locator"].strip()
                      or not re.fullmatch(r"[0-9a-f]{64}", row["source_sha256"])):
        raise ValueError("source-backed judgments require URL, locator and source SHA-256")
    # Local cache locators use path#record-pointer. A URL or conceptual locator
    # cannot be authenticated here; its declared digest remains auditable data.
    locator = row["source_locator"].split("#", 1)[0]
    if locator and "://" not in locator:
        source = Path(locator)
        if supported and locator.startswith(("/", "./", "data/", "configs/", "reports/")) and not source.is_file():
            raise ValueError(f"local source locator is unavailable: {source}")
        if source.is_file() and (supported or row["source_sha256"]):
            source = source.resolve()
            if source not in source_digests:
                source_digests[source] = _digest(source)
            if source_digests[source] != row["source_sha256"]:
                raise ValueError(f"local source hash mismatch: {source}")


def _ledger(path: Path, *, kind: str, runs: dict[str, dict], expected: set[tuple[str, str]],
            topic_completed: datetime, edge_started: datetime, allow_partial: bool) -> dict[tuple[str, str], dict]:
    rows = {}
    source_digests = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict) or LEDGER_FIELDS - row.keys():
            raise ValueError("evidence ledger row is missing required provenance fields")
        if any(not isinstance(row[key], str) for key in LEDGER_FIELDS):
            raise ValueError("evidence ledger provenance fields must be strings")
        key = (row["unit_id"], row["reviewer_id"])
        if key in rows or key not in expected:
            raise ValueError("ledger has duplicate or unassigned reviewer/unit join")
        run = runs.get(row["evaluator_run_id"])
        if not run or run["reviewer_id"] != row["reviewer_id"] or row["reviewer_kind"] != "ai_agent":
            raise ValueError("ledger evaluator run does not match its reviewer")
        timestamp = _time(row["reviewed_at"], "ledger reviewed_at")
        if timestamp < _time(run["started_at"], "run started_at"):
            raise ValueError("judgment precedes evaluator start")
        if kind == "topics" and timestamp > topic_completed or kind != "topics" and timestamp < edge_started:
            raise ValueError("topic completion must precede edge review")
        decisions = {"reviewed", "unreviewable"} if kind == "topics" else edge_audit.VERDICTS
        if row["decision"] not in decisions or not row["reason"].strip():
            raise ValueError("ledger requires a valid decision and nonempty rationale")
        _source(row, source_digests)
        if row["evidence_depth"] in {"internal_only", "unavailable"}:
            required = "unreviewable" if kind == "topics" else "unverifiable"
            if row["decision"] != required:
                raise ValueError("internal-only or unavailable evidence requires an unreviewable/unverifiable verdict")
        rows[key] = row
    if not allow_partial and set(rows) != expected:
        raise ValueError("ledger does not cover every frozen reviewer assignment")
    return rows


def _join_csv(rows: list[dict], ledger: dict, *, kind: str) -> None:
    seen = set()
    for row in rows:
        key = (row["paper_id"], row["labeler"]) if kind == "topics" else (
            row["edge_id"], row.get("reviewer_id", row.get("adjudicator_id")))
        if key in seen or key not in ledger:
            raise ValueError("CSV and ledger reviewer/unit joins differ")
        seen.add(key)
        entry = ledger[key]
        if kind == "topics":
            labels = [row[f"label_{i}"].strip() for i in range(1, 4) if row[f"label_{i}"].strip()]
            if entry["decision"] == "unreviewable" and labels:
                raise ValueError("unreviewable topics must not contain reference labels")
            if "labels" not in entry or (not isinstance(entry["labels"], list)
                                      or any(not isinstance(label, str) for label in entry["labels"])
                                      or len(entry["labels"]) != len(set(entry["labels"]))
                                      or set(entry["labels"]) != set(labels)):
                raise ValueError("topic CSV labels differ from the source ledger")
        elif row["decision"].strip().lower() != entry["decision"]:
            raise ValueError("edge CSV decision differs from the source ledger")
        if kind != "topics" and (_time(row["reviewed_at"], "CSV reviewed_at") != _time(entry["reviewed_at"], "ledger reviewed_at")
                                  or row["reason"].strip() != entry["reason"].strip()):
            raise ValueError("edge CSV rationale/timestamp differs from the source ledger")
    if seen != set(ledger):
        raise ValueError("CSV and ledger reviewer/unit joins differ")


def _topic_missingness(result: dict, csv_rows: dict[str, list[dict]], ledger: dict,
                       graph_v1: Path, graph: Path, taxonomy: Path, *, allow_partial: bool) -> None:
    """Exclude unavailable references, retaining half weight per planned overlap slot."""
    unreviewable = {key for key, row in ledger.items() if row["decision"] == "unreviewable"}
    if unreviewable and not allow_partial:
        raise ValueError("unreviewable topics require explicit partial scoring opt-in")
    labels = {reviewer: {
        row["paper_id"]: {row[f"label_{i}"].strip() for i in range(1, 4) if row[f"label_{i}"].strip()}
        for row in rows if (row["paper_id"], reviewer) not in unreviewable
    } for reviewer, rows in csv_rows.items()}
    counts = Counter(row["paper_id"] for rows in csv_rows.values() for row in rows)
    annotations = [(unit, values, 1 / counts[unit]) for mapping in labels.values() for unit, values in mapping.items()]
    topics = sorted(leaf["id"] for leaf in yaml.safe_load(taxonomy.read_text())["leaves"])
    paper_ids = set(counts)
    for name, path in (("phrase_baseline", graph_v1), ("embedding_classifier", graph)):
        artifact, _ = topic_eval._read_graph(path)
        predictions = topic_eval._predictions(artifact, paper_ids, set(topics))
        result["models"][name]["paper_normalized_review_metrics"] = topic_eval._score_annotations(annotations, predictions, topics)
        result["models"][name]["by_reviewer"] = {
            reviewer: topic_eval._score_annotations([(unit, values, 1.0) for unit, values in mapping.items()], predictions, topics)
            for reviewer, mapping in labels.items()
        }
    overlap = sorted(set(labels["A"]) & set(labels["B"]))
    result["reviewer_agreement_on_overlap"] = topic_eval._agreement(overlap, labels["A"], labels["B"], topics)
    result["annotation_judgment_count"] = len(annotations)
    result["weighting"]["effective_paper_weight"] = sum(weight for _, _, weight in annotations)
    result["completion"] = {
        "planned_assignments": sum(counts.values()), "reviewed_assignments": len(annotations),
        "unreviewable_assignments": len(unreviewable), "unreviewable": [
            {"unit_id": unit, "reviewer_id": reviewer} for unit, reviewer in sorted(unreviewable)],
        "reviewed_papers": len({unit for unit, _, _ in annotations}),
        "fully_unreviewable_papers": len(paper_ids - {unit for unit, _, _ in annotations}),
    }
    result["status"] = "partial_ai_assessed" if unreviewable else "scored_ai_assessed"
    result["partial_scoring_opt_in"] = allow_partial


def score_agent_review(*, evaluation_freeze: Path, completion_receipt: Path, protocol: Path,
                       topic_ledger: Path, edge_ledger: Path, graph: Path, quality: Path,
                       graph_v1: Path, topic_test: Path, taxonomy: Path, allocation: Path,
                       master_sheet: Path, topic_reviewer_a: Path, topic_reviewer_b: Path,
                       graph_freeze: Path, graph_summary: Path, edge_reviews: list[Path],
                       edge_output: Path, topic_output: Path, adjudications: Path | None = None,
                       adjudication_ledger: Path | None = None, allow_partial: bool = False) -> tuple[dict, int]:
    """Validate all bindings before scoring; publish only explicitly AI-scoped results."""
    static = [protocol, graph, quality, graph_v1, topic_test, taxonomy, allocation, master_sheet, graph_freeze, graph_summary]
    completed = [topic_ledger, edge_ledger, topic_reviewer_a, topic_reviewer_b, *edge_reviews]
    if bool(adjudications) != bool(adjudication_ledger):
        raise ValueError("adjudication CSV and provenance ledger must be supplied together")
    if adjudications:
        completed.extend([adjudications, adjudication_ledger])
    protected = {p.resolve() for p in [*static, *completed, evaluation_freeze, completion_receipt]}
    if edge_output.resolve() == topic_output.resolve():
        raise ValueError("agent scoring outputs must be distinct")
    for path in (edge_output, topic_output):
        if path.resolve() in protected or path.exists() or path.is_symlink():
            raise ValueError("refusing to overwrite an agent scoring input or output")
    freeze = json.loads(evaluation_freeze.read_text())
    if freeze.get("review_design") != "isolated_agent_A_B":
        raise ValueError("this wrapper supports the frozen isolated_agent_A_B design")
    if any(freeze.get(key) != AI_METADATA[key] for key in ("evaluation_kind", "human_validation", "reviewer_independence")):
        raise ValueError("evaluation freeze must declare truthful AI evaluation metadata")
    created = _time(freeze.get("created_at"), "freeze created_at")
    runs = _runs(freeze, created)
    bindings = _bindings(freeze.get("input_files"), "evaluation freeze")
    _require_bindings(static, bindings, "evaluation freeze")
    contract = yaml.safe_load(protocol.read_text())
    if any(contract.get(key) != AI_METADATA[key] for key in ("evaluation_kind", "human_validation", "reviewer_independence")):
        raise ValueError("protocol must declare truthful AI evaluation metadata")
    receipt = json.loads(completion_receipt.read_text())
    if receipt.get("evaluation_freeze_sha256") != _digest(evaluation_freeze):
        raise ValueError("completion receipt does not bind the evaluation freeze")
    outputs = _bindings(receipt.get("output_files"), "completion receipt")
    _require_bindings(completed, outputs, "completion receipt")
    topic_completed = _time(receipt.get("topic_completed_at"), "topic_completed_at")
    edge_started = _time(receipt.get("edge_started_at"), "edge_started_at")
    if not created <= topic_completed <= edge_started:
        raise ValueError("topic completion must precede edge review and follow the freeze")
    topic_assignments = _assignments(freeze, "topics")
    edge_assignments = _assignments(freeze, "edges")
    artifact, graph_bytes, _ = edge_audit._read_graph(graph)
    _, audit = edge_audit._load_quality(quality)
    if audit.get("review_design") != "split_with_overlap" or set(audit.get("reviewer_ids", [])) != {"A", "B"}:
        raise ValueError("isolated_agent_A_B requires the split_with_overlap A/B edge design")
    _, type_samples, global_ids, _, _ = edge_audit._expected_samples(artifact, audit, _digest(quality), None)
    selected = set(global_ids).union(*type_samples.values())
    canonical_edges = {(unit, reviewer) for unit, reviewers in edge_audit._assignments(audit, global_ids, selected).items() for reviewer in reviewers}
    del artifact, graph_bytes
    if edge_assignments != canonical_edges:
        raise ValueError("evaluation freeze edge assignments differ from the configured deterministic sample")
    allocation_doc = json.loads(allocation.read_text())
    actual_topic_assignments = {(unit, reviewer) for reviewer, ids in allocation_doc.get("reviewer_paper_ids", {}).items() for unit in ids}
    if topic_assignments != actual_topic_assignments:
        raise ValueError("evaluation freeze topic assignments differ from the frozen allocation")
    topic_rows = {"A": topic_eval._read_csv(topic_reviewer_a), "B": topic_eval._read_csv(topic_reviewer_b)}
    topics = _ledger(topic_ledger, kind="topics", runs=runs, expected=topic_assignments,
                     topic_completed=topic_completed, edge_started=edge_started, allow_partial=False)
    _join_csv([row for rows in topic_rows.values() for row in rows], topics, kind="topics")
    edges = _ledger(edge_ledger, kind="edges", runs=runs, expected=edge_assignments,
                    topic_completed=topic_completed, edge_started=edge_started, allow_partial=allow_partial)
    edge_rows = [row for path in edge_reviews for row in edge_audit._load_csv(path, edge_audit.REVIEW_FIELDS)]
    _join_csv(edge_rows, edges, kind="edges")
    adjudicated = {}
    if adjudications:
        adjudication_rows = edge_audit._load_csv(adjudications, edge_audit.ADJUDICATION_FIELDS)
        expected = {(row["edge_id"], row["adjudicator_id"]) for row in adjudication_rows}
        if any(reviewer != "ADJ" for _, reviewer in expected):
            raise ValueError("agent adjudications must use the frozen ADJ reviewer channel")
        adjudicated = _ledger(adjudication_ledger, kind="adjudications", runs=runs, expected=expected,
                              topic_completed=topic_completed, edge_started=edge_started, allow_partial=False)
        _join_csv(adjudication_rows, adjudicated, kind="adjudications")
        for (unit, _), row in adjudicated.items():
            earlier = [entry for (edge_id, _), entry in edges.items() if edge_id == unit]
            if any(_time(row["reviewed_at"], "adjudicated_at") < _time(entry["reviewed_at"], "reviewed_at") for entry in earlier):
                raise ValueError("adjudication must follow both initial judgments")
    provenance = {
        "evaluation_freeze": {"path": str(evaluation_freeze), "sha256": _digest(evaluation_freeze)},
        "completion_receipt": {"path": str(completion_receipt), "sha256": _digest(completion_receipt)},
        "evaluator_runs": freeze["evaluator_runs"],
        "ledgers": [{"path": str(p), "sha256": _digest(p)} for p in [topic_ledger, edge_ledger, *([adjudication_ledger] if adjudication_ledger else [])]],
    }
    # Legacy scorers fully validate their frozen graph/config/packet contracts.
    # Temporary outputs prevent publication of an unqualified intermediate result.
    with TemporaryDirectory(prefix="scientific-network-agent-scoring-") as temporary:
        temporary = Path(temporary)
        edge_result, exit_code = edge_audit.evaluate_edge_audit(graph, edge_reviews, quality, temporary / "edge.json", adjudications, allow_partial=allow_partial)
        topic_result = topic_eval.score_topic_review(graph_v1, graph, topic_test, taxonomy, allocation,
            master_sheet, topic_reviewer_a, topic_reviewer_b, graph_freeze, graph_summary, temporary / "topic.json")
        _topic_missingness(topic_result, topic_rows, topics, graph_v1, graph, taxonomy, allow_partial=allow_partial)
    for result, ledger, metric in ((edge_result, edges, "AI-assessed edge precision"), (topic_result, topics, "topic agreement with AI-assigned reference labels")):
        result.update(AI_METADATA)
        result["metric_name"] = metric
        result["agent_provenance"] = provenance
        result["evidence_depth_counts"] = dict(Counter(row["evidence_depth"] for row in ledger.values()))
        result["source_independence_counts"] = dict(Counter(row["source_independence"] for row in ledger.values()))
        result.setdefault("limitations", []).extend([
            "AI judgments are source-backed declarations; file/ledger validation does not authenticate their correctness.",
            "Human validation was not performed and evaluator independence is not established, including between fresh contexts.",
            "Wilson intervals exclude evaluator error and shared-model/source bias; verified course accuracy is not established.",
        ])
    edge_result["ai_assessed_numeric_checks"] = {
        "project_status": edge_result["numeric_gate_status"], "course_point_check": edge_result["course_gate"],
    }
    if edge_result["course_gate"] is not None:
        edge_result["course_gate"]["scope"] = "ai_assessed_only"
    topic_result["reference_label_provenance"] = "ai_assigned_not_human_validated"
    edge_result["adjudication_evidence_depth_counts"] = dict(Counter(row["evidence_depth"] for row in adjudicated.values()))
    for path, result in ((edge_output, edge_result), (topic_output, topic_result)):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    return {**AI_METADATA, "edge_results": str(edge_output), "topic_results": str(topic_output),
            "edge_status": edge_result["status"], "topic_status": topic_result["status"]}, exit_code
