"""Prospective, hash-bound edge-only AI assessment of a frozen graph.

This deliberately has no topic inputs or topic-completion claim. Historical topic
references remain attributable to the contexts that actually produced them.
"""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from scientific_network.evaluation import agent_review, edge_audit


def score_agent_edge_review(
    *, evaluation_freeze: Path, completion_receipt: Path, protocol: Path,
    edge_ledger: Path, graph: Path, quality: Path, graph_freeze: Path,
    graph_summary: Path, rubric: Path, edge_packets: list[Path],
    edge_reviews: list[Path], edge_output: Path, adjudications: Path | None = None,
    adjudication_ledger: Path | None = None,
    adjudication_start_receipt: Path | None = None, allow_partial: bool = False,
) -> tuple[dict, int]:
    """Validate isolated A/B edge provenance, then retain the legacy numeric gates.

    ``input_files`` binds every static argument, including the rubric and all
    packets supplied to reviewers. The completion receipt binds the actual CSVs
    and ledgers and records ``edge_started_at`` / ``edge_completed_at``. Optional
    adjudications also require ``adjudication_completed_at`` and an isolated ADJ
    run starting after A/B exports were completed. Its actual run metadata can be
    supplied in an immutable ``adjudication_start_receipt`` created after A/B
    completion, binding ``initial_exports`` and the evaluation freeze. The main
    freeze declares the policy without inventing a future run. The final receipt
    binds this start receipt as another output. Times are timezone-aware.
    """
    if not edge_packets or len({p.resolve() for p in edge_packets}) != len(edge_packets):
        raise ValueError("supply distinct frozen edge source/review packets")
    if bool(adjudications) != bool(adjudication_ledger):
        raise ValueError("adjudication CSV and provenance ledger must be supplied together")
    if adjudication_start_receipt and not adjudications:
        raise ValueError("adjudication start receipt requires adjudication CSV and ledger")
    static = [protocol, graph, quality, graph_freeze, graph_summary, rubric, *edge_packets]
    completed = [edge_ledger, *edge_reviews]
    if adjudications:
        completed.extend([adjudications, adjudication_ledger])
    if adjudication_start_receipt:
        completed.append(adjudication_start_receipt)
    protected = {p.resolve() for p in [*static, *completed, evaluation_freeze, completion_receipt]}
    if edge_output.resolve() in protected or edge_output.exists() or edge_output.is_symlink():
        raise ValueError("refusing to overwrite an agent scoring input or output")

    freeze = json.loads(evaluation_freeze.read_text())
    contract = yaml.safe_load(protocol.read_text())
    for name, document in (("evaluation freeze", freeze), ("protocol", contract)):
        if not isinstance(document, dict) or document.get("evaluation_scope") != "edge_only":
            raise ValueError(f"{name} must declare evaluation_scope=edge_only")
        if any(document.get(key) != value for key, value in agent_review.AI_METADATA.items()):
            raise ValueError(f"{name} must declare truthful AI evaluation metadata")
    if freeze.get("review_design") != "isolated_agent_A_B":
        raise ValueError("edge-only scoring requires the frozen isolated_agent_A_B design")
    if "topics" in freeze.get("assignments", {}):
        raise ValueError("edge-only freeze must not attribute topic assignments to new contexts")
    created = agent_review._time(freeze.get("created_at"), "freeze created_at")
    runs = agent_review._runs(freeze, created)
    bindings = agent_review._bindings(freeze.get("input_files"), "evaluation freeze")
    agent_review._require_bindings(static, bindings, "evaluation freeze")

    receipt = json.loads(completion_receipt.read_text())
    if receipt.get("evaluation_freeze_sha256") != agent_review._digest(evaluation_freeze):
        raise ValueError("completion receipt does not bind the evaluation freeze")
    if "topic_completed_at" in receipt:
        raise ValueError("edge-only completion must not claim topic completion")
    outputs = agent_review._bindings(receipt.get("output_files"), "completion receipt")
    agent_review._require_bindings(completed, outputs, "completion receipt")
    started = agent_review._time(receipt.get("edge_started_at"), "edge_started_at")
    finished = agent_review._time(receipt.get("edge_completed_at"), "edge_completed_at")
    if not created <= started <= finished:
        raise ValueError("edge completion must follow edge start and the evaluation freeze")
    adjudication_created = finished
    if adjudication_start_receipt:
        if freeze.get("adjudication_policy") != "separate_source_review_after_frozen_exports":
            raise ValueError("evaluation freeze must declare separate adjudication after frozen exports")
        if any(run["reviewer_id"] == "ADJ" for run in runs.values()):
            raise ValueError("separate adjudication start receipt must not replace a predeclared ADJ run")
        adjudication_start = json.loads(adjudication_start_receipt.read_text())
        if adjudication_start.get("evaluation_freeze_sha256") != agent_review._digest(evaluation_freeze):
            raise ValueError("adjudication start receipt does not bind the evaluation freeze")
        initial = agent_review._bindings(adjudication_start.get("initial_exports"), "adjudication initial exports")
        agent_review._require_bindings([edge_ledger, *edge_reviews], initial, "adjudication initial exports")
        run = adjudication_start.get("evaluator_run")
        if not isinstance(run, dict) or run.get("reviewer_id") != "ADJ":
            raise ValueError("adjudication start receipt requires actual ADJ evaluator_run metadata")
        # Reuse all run-ID, model/provider and context-isolation checks for the
        # actual later run; the original evaluation freeze stays unchanged.
        runs = agent_review._runs({**freeze, "evaluator_runs": [*freeze["evaluator_runs"], run]}, created)
        adjudication_created = agent_review._time(adjudication_start.get("created_at"), "adjudication start created_at")
        if not finished <= agent_review._time(run["started_at"], "ADJ run started_at") <= adjudication_created:
            raise ValueError("ADJ run must start after frozen A/B exports and before its start receipt")

    artifact, graph_bytes, _ = edge_audit._read_graph(graph)
    graph_sha = agent_review._digest(graph)
    for name, document in (("evaluation freeze", freeze),
                           ("graph freeze", json.loads(graph_freeze.read_text())),
                           ("graph summary", json.loads(graph_summary.read_text()))):
        if (document.get("graph_version") != artifact.graph_version
                or document.get("graph_sha256") != graph_sha):
            raise ValueError(f"{name} does not identify the frozen graph version/hash")
    _, audit = edge_audit._load_quality(quality)
    if (audit.get("review_design") != "split_with_overlap"
            or audit.get("reviewer_ids") != ["A", "B"]):
        raise ValueError("isolated_agent_A_B requires the split_with_overlap A/B edge design")
    if any(audit.get(key) != value for key, value in {
        "confidence_level": 0.95, "min_precision": 0.95,
        "wilson_lower_bound_must_exceed": 0.9, "course_point_estimate_must_exceed": 0.9,
    }.items()):
        raise ValueError("edge-only scoring must preserve the D040 precision thresholds and confidence level")
    # Small, explicitly synthetic fixtures exercise the same allocation algorithm.
    if not artifact.is_synthetic and any(audit.get(key) != value for key, value in {
        "global_sample_size": 200, "per_type_sample_size": 10, "overlap_sample_size": 50,
    }.items()):
        raise ValueError("release edge-only design requires 200 global / 10 per type / 50 overlap")
    _, type_samples, global_ids, _, _ = edge_audit._expected_samples(
        artifact, audit, agent_review._digest(quality), None)
    selected = set(global_ids).union(*type_samples.values())
    canonical = {(unit, reviewer) for unit, reviewers in
                 edge_audit._assignments(audit, global_ids, selected).items()
                 for reviewer in reviewers}
    expected = agent_review._assignments(freeze, "edges")
    if expected != canonical:
        raise ValueError("evaluation freeze edge assignments differ from the configured deterministic sample")
    del artifact, graph_bytes

    edges = agent_review._ledger(
        edge_ledger, kind="edges", runs=runs, expected=expected,
        topic_completed=created, edge_started=started, allow_partial=allow_partial)
    edge_rows = [row for path in edge_reviews
                 for row in edge_audit._load_csv(path, edge_audit.REVIEW_FIELDS)]
    agent_review._join_csv(edge_rows, edges, kind="edges")
    if any(agent_review._time(row["reviewed_at"], "reviewed_at") > finished
           for row in edges.values()):
        raise ValueError("edge judgment follows the frozen A/B completion time")

    adjudicated = {}
    if adjudications:
        adjudication_finished = agent_review._time(
            receipt.get("adjudication_completed_at"), "adjudication_completed_at")
        if adjudication_finished < adjudication_created:
            raise ValueError("adjudication completion must follow frozen A/B exports and its start receipt")
        adjudication_rows = edge_audit._load_csv(adjudications, edge_audit.ADJUDICATION_FIELDS)
        expected_adjudications = {(row["edge_id"], row["adjudicator_id"])
                                  for row in adjudication_rows}
        if any(reviewer != "ADJ" for _, reviewer in expected_adjudications):
            raise ValueError("agent adjudications must use the frozen ADJ reviewer channel")
        adjudicated = agent_review._ledger(
            adjudication_ledger, kind="adjudications", runs=runs,
            expected=expected_adjudications, topic_completed=created,
            edge_started=finished, allow_partial=False)
        agent_review._join_csv(adjudication_rows, adjudicated, kind="adjudications")
        for (unit, _), row in adjudicated.items():
            votes = [entry for (edge_id, _), entry in edges.items() if edge_id == unit]
            if ({entry["reviewer_id"] for entry in votes} != {"A", "B"}
                    or len({entry["decision"] for entry in votes}) != 2):
                raise ValueError("adjudication requires both initial judgments and actual disagreement")
            run = runs[row["evaluator_run_id"]]
            if agent_review._time(run["started_at"], "ADJ run started_at") < finished:
                raise ValueError("ADJ run must start after frozen A/B exports")
            timestamp = agent_review._time(row["reviewed_at"], "adjudicated_at")
            if (not adjudication_created <= timestamp <= adjudication_finished or any(timestamp < agent_review._time(
                    vote["reviewed_at"], "reviewed_at") for vote in votes)):
                raise ValueError("adjudication must follow both initial judgments and its start receipt and precede completion")

    with TemporaryDirectory(prefix="scientific-network-agent-edge-scoring-") as temporary:
        result, exit_code = edge_audit.evaluate_edge_audit(
            graph, edge_reviews, quality, Path(temporary) / "edges.json", adjudications,
            allow_partial=allow_partial)
    result.update(agent_review.AI_METADATA)
    result["evaluation_scope"] = "edge_only"
    result["metric_name"] = "AI-assessed edge precision"
    result["agent_provenance"] = {
        "evaluation_freeze": {"path": str(evaluation_freeze), "sha256": agent_review._digest(evaluation_freeze)},
        "completion_receipt": {"path": str(completion_receipt), "sha256": agent_review._digest(completion_receipt)},
        "evaluator_runs": list(runs.values()),
        "ledgers": [{"path": str(p), "sha256": agent_review._digest(p)}
                    for p in [edge_ledger, *([adjudication_ledger] if adjudication_ledger else [])]],
    }
    if adjudication_start_receipt:
        result["agent_provenance"]["adjudication_start_receipt"] = {
            "path": str(adjudication_start_receipt), "sha256": agent_review._digest(adjudication_start_receipt),
        }
    result["evidence_depth_counts"] = dict(Counter(row["evidence_depth"] for row in edges.values()))
    result["source_independence_counts"] = dict(Counter(row["source_independence"] for row in edges.values()))
    result["adjudication_evidence_depth_counts"] = dict(Counter(row["evidence_depth"] for row in adjudicated.values()))
    result["ai_assessed_numeric_checks"] = {
        "project_status": result["numeric_gate_status"], "course_point_check": result["course_gate"],
    }
    if result["course_gate"] is not None:
        result["course_gate"]["scope"] = "ai_assessed_only"
    result.setdefault("limitations", []).extend([
        "AI judgments are source-backed declarations; file/ledger validation does not authenticate their correctness.",
        "Human validation was not performed and evaluator independence is not established, including between fresh contexts.",
        "Wilson intervals exclude evaluator error and shared-model/source bias; verified course accuracy is not established.",
        "Edge-only review creates no new topic references, topic evaluation or untouched topic holdout.",
    ])
    edge_output.parent.mkdir(parents=True, exist_ok=True)
    with edge_output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return {**agent_review.AI_METADATA, "evaluation_scope": "edge_only",
            "edge_results": str(edge_output), "edge_status": result["status"]}, exit_code
