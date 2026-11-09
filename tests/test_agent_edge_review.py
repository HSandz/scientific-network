"""Invented provenance packets; no real source judgments or artifacts are changed."""

import csv
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path

import pytest
import yaml

from scientific_network.evaluation import edge_audit
from scientific_network.evaluation.agent_edge_review import score_agent_edge_review
from scientific_network.evaluation.agent_review import AI_METADATA


_spec = spec_from_file_location("combined_agent_fixture", Path(__file__).with_name("test_agent_review.py"))
_legacy = module_from_spec(_spec)
_spec.loader.exec_module(_legacy)
digest, write_json, write_jsonl, write_csv = (
    _legacy.digest, _legacy.write_json, _legacy.write_jsonl, _legacy.write_csv)


def rebind(package):
    _legacy.rebind(package)


@pytest.fixture
def edge_package(tmp_path):
    combined = _legacy.agent_package.__wrapped__(tmp_path)
    keys = ("evaluation_freeze", "completion_receipt", "protocol", "edge_ledger", "graph",
            "quality", "graph_freeze", "graph_summary", "edge_reviews", "edge_output")
    package = {key: combined[key] for key in keys}
    rubric = tmp_path / "edge-rubric.md"
    rubric.write_text("Invented edge-only source rubric; no topic assessment.\n")
    package.update(rubric=rubric, edge_packets=[tmp_path / "edges.csv"])
    package["protocol"].write_text(yaml.safe_dump({**AI_METADATA, "evaluation_scope": "edge_only"}))
    freeze = json.loads(package["evaluation_freeze"].read_text())
    freeze.update(evaluation_scope="edge_only", graph_sha256=digest(package["graph"]),
                  graph_version=json.loads(package["graph"].read_text())["graph_version"])
    freeze["assignments"].pop("topics")
    freeze["input_files"] = [{"path": str(package[key]), "sha256": digest(package[key])}
                             for key in ("protocol", "graph", "quality", "graph_freeze", "graph_summary", "rubric")]
    freeze["input_files"].extend({"path": str(path), "sha256": digest(path)} for path in package["edge_packets"])
    write_json(package["evaluation_freeze"], freeze)
    write_json(package["completion_receipt"], {
        "evaluation_freeze_sha256": digest(package["evaluation_freeze"]),
        "edge_started_at": "2026-11-09T00:10:00+07:00",
        "edge_completed_at": "2026-11-09T02:05:00+07:00",
        "output_files": [{"path": str(path), "sha256": digest(path)}
                         for path in [package["edge_ledger"], *package["edge_reviews"]]],
    })
    # No historical topic inputs are available to the edge-only scorer.
    for key in ("topic_ledger", "topic_reviewer_a", "topic_reviewer_b", "graph_v1", "topic_test", "taxonomy", "allocation", "master_sheet"):
        combined[key].unlink()
    return package


def read_rows(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def ledger_rows(package):
    return [json.loads(line) for line in package["edge_ledger"].read_text().splitlines()]


def test_edge_only_scores_without_topic_inputs_and_keeps_ai_limits(edge_package):
    summary, code = score_agent_edge_review(**edge_package)
    result = json.loads(edge_package["edge_output"].read_text())
    assert code == 0
    assert summary["evaluation_scope"] == result["evaluation_scope"] == "edge_only"
    assert {key: result[key] for key in AI_METADATA} == AI_METADATA
    assert result["status"] == "synthetic_protocol_only"
    assert result["global"]["correct"] == result["global"]["total"] == 10
    assert result["agreement"]["edges_reviewed_by_both"] == 4
    assert result["source_independence_counts"]["same_source_as_construction"] > 0
    assert result["evidence_depth_counts"]["secondary_source_only"] > 0
    assert len(result["agent_provenance"]["ledgers"]) == 1
    assert any("Wilson intervals exclude evaluator error" in item for item in result["limitations"])
    assert not any("topic" in run for run in result["agent_provenance"]["evaluator_runs"])


@pytest.mark.parametrize("mutation,match", [
    ("freeze_scope", "evaluation_scope=edge_only"), ("protocol_scope", "evaluation_scope=edge_only"),
    ("same_context", "share an evaluator context"), ("same_run", "distinct actual IDs"),
    ("late_freeze", "freeze must precede"), ("assignment", "edge assignments differ"),
    ("unbound_rubric", "does not bind required input"), ("unbound_packet", "does not bind required input"),
    ("packet_hash", "hash mismatch"), ("receipt_hash", "does not bind the evaluation freeze"),
    ("graph_binding", "frozen graph version/hash"), ("summary_binding", "frozen graph version/hash"),
    ("invented_topics", "must not attribute topic assignments"),
    ("topic_completion", "must not claim topic completion"),
    ("completion_before_vote", "follows the frozen A/B completion time"),
    ("vote_before_run", "judgment precedes evaluator start"),
    ("bad_source", "local source hash mismatch"), ("bad_csv", "decision differs"),
    ("missing_vote", "every frozen reviewer assignment"),
    ("wrong_reviewer", "unassigned reviewer/unit"),
])
def test_edge_only_refuses_invalid_provenance_without_output(edge_package, mutation, match):
    p = edge_package
    freeze = json.loads(p["evaluation_freeze"].read_text())
    receipt = json.loads(p["completion_receipt"].read_text())
    ledger = ledger_rows(p)
    if mutation == "freeze_scope": freeze.pop("evaluation_scope")
    elif mutation == "protocol_scope": p["protocol"].write_text(yaml.safe_dump(AI_METADATA))
    elif mutation == "same_context": freeze["evaluator_runs"][1]["context_id"] = "context-A"
    elif mutation == "same_run": freeze["evaluator_runs"][1]["evaluator_run_id"] = "run-A"
    elif mutation == "late_freeze": freeze["created_at"] = "2026-11-09T00:30:00+07:00"
    elif mutation == "assignment": freeze["assignments"]["edges"]["A"].append("edge:unassigned")
    elif mutation in {"unbound_rubric", "unbound_packet"}:
        removed = p["rubric"] if mutation == "unbound_rubric" else p["edge_packets"][0]
        freeze["input_files"] = [item for item in freeze["input_files"] if item["path"] != str(removed)]
    elif mutation == "graph_binding": freeze["graph_sha256"] = "0" * 64
    elif mutation == "summary_binding": write_json(p["graph_summary"], {})
    elif mutation == "invented_topics": freeze["assignments"]["topics"] = {"A": [], "B": []}
    elif mutation == "topic_completion": receipt["topic_completed_at"] = "2026-11-09T01:00:00+07:00"
    elif mutation == "completion_before_vote": receipt["edge_completed_at"] = "2026-11-09T01:00:00+07:00"
    elif mutation == "vote_before_run": ledger[0]["reviewed_at"] = "2026-11-09T00:05:00+07:00"
    elif mutation == "bad_source": ledger[0]["source_sha256"] = "0" * 64
    elif mutation == "bad_csv": ledger[0]["decision"] = "incorrect"
    elif mutation == "missing_vote": ledger.pop()
    elif mutation == "wrong_reviewer": ledger[0]["reviewer_id"] = "ADJ"
    write_json(p["evaluation_freeze"], freeze)
    write_json(p["completion_receipt"], receipt)
    write_jsonl(p["edge_ledger"], ledger)
    rebind(p)
    if mutation == "packet_hash": p["edge_packets"][0].write_text("changed")
    elif mutation == "receipt_hash":
        receipt = json.loads(p["completion_receipt"].read_text())
        receipt["evaluation_freeze_sha256"] = "0" * 64
        write_json(p["completion_receipt"], receipt)
    with pytest.raises(ValueError, match=match):
        score_agent_edge_review(**p)
    assert not p["edge_output"].exists()


def test_partial_opt_in_preserves_missing_assignment_denominators(edge_package):
    p = edge_package
    rows = read_rows(p["edge_reviews"][0])
    removed = next(row for row in rows if row["is_overlap"] == "false" and row["in_global_sample"] == "true")
    key = (removed["edge_id"], removed["reviewer_id"])
    write_csv(p["edge_reviews"][0], [row for row in rows if row is not removed], edge_audit.SPLIT_FIELDS)
    write_jsonl(p["edge_ledger"], [row for row in ledger_rows(p) if (row["unit_id"], row["reviewer_id"]) != key])
    rebind(p)
    with pytest.raises(ValueError, match="every frozen reviewer assignment"):
        score_agent_edge_review(**p)
    score_agent_edge_review(**p, allow_partial=True)
    result = json.loads(p["edge_output"].read_text())
    assert result["completion"]["missing_assignment_count"] == 1
    assert result["global"]["total"] == 9
    assert result["global"]["planned_total"] == 10


def with_adjudication(p, invalid=None):
    rows = read_rows(p["edge_reviews"][0])
    conflict = next(row for row in rows if row["is_overlap"] == "true" and row["reviewer_id"] == "B")
    conflict.update(decision="incorrect", error_category="wrong_topic", reason="Invented disagreement")
    write_csv(p["edge_reviews"][0], rows, edge_audit.SPLIT_FIELDS)
    ledger = ledger_rows(p)
    entry = next(row for row in ledger if row["unit_id"] == conflict["edge_id"] and row["reviewer_id"] == "B")
    entry.update(decision="incorrect", reason=conflict["reason"])
    if invalid == "missing_vote":
        ledger = [row for row in ledger if not (row["unit_id"] == conflict["edge_id"] and row["reviewer_id"] == "A")]
        rows = [row for row in rows if not (row["edge_id"] == conflict["edge_id"] and row["reviewer_id"] == "A")]
        write_csv(p["edge_reviews"][0], rows, edge_audit.SPLIT_FIELDS)
    write_jsonl(p["edge_ledger"], ledger)
    adjudication = {key: conflict.get(key, "") for key in edge_audit.ADJUDICATION_FIELDS}
    adjudication.update(adjudicator_id="ADJ", decision="unverifiable", reason="Invented unresolved claim",
                        reviewed_at="2026-11-09T02:15:00+07:00")
    if invalid == "judgment_before_exports": adjudication["reviewed_at"] = "2026-11-09T02:01:00+07:00"
    p["adjudications"] = write_csv(p["edge_output"].parent / "adjudications.csv", [adjudication], edge_audit.ADJUDICATION_FIELDS)
    adj = {**entry, "reviewer_id": "ADJ", "evaluator_run_id": "run-ADJ", "decision": adjudication["decision"],
           "reason": adjudication["reason"], "reviewed_at": adjudication["reviewed_at"]}
    if invalid == "source": adj["source_sha256"] = "0" * 64
    p["adjudication_ledger"] = write_jsonl(p["edge_output"].parent / "adjudication.jsonl", [adj])
    freeze = json.loads(p["evaluation_freeze"].read_text())
    freeze["evaluator_runs"].append({**freeze["evaluator_runs"][0], "reviewer_id": "ADJ",
        "evaluator_run_id": "run-ADJ", "context_id": "context-ADJ",
        "started_at": "2026-11-09T02:10:00+07:00" if invalid != "run_before_exports" else "2026-11-09T02:00:00+07:00"})
    write_json(p["evaluation_freeze"], freeze)
    receipt = json.loads(p["completion_receipt"].read_text())
    receipt["adjudication_completed_at"] = "2026-11-09T02:20:00+07:00"
    receipt["output_files"].extend({"path": str(p[key]), "sha256": digest(p[key])} for key in ("adjudications", "adjudication_ledger"))
    write_json(p["completion_receipt"], receipt)
    rebind(p)
    return p


@pytest.mark.parametrize("invalid", [None, "run_before_exports", "judgment_before_exports", "source", "missing_vote"])
def test_adjudication_needs_separate_source_and_both_frozen_votes(edge_package, invalid):
    p = with_adjudication(edge_package, invalid)
    if invalid:
        with pytest.raises(ValueError, match={"run_before_exports": "ADJ run must start", "judgment_before_exports": "judgment precedes evaluator start",
                                             "source": "local source hash", "missing_vote": "requires both initial judgments"}[invalid]):
            score_agent_edge_review(**p, allow_partial=True)
        assert not p["edge_output"].exists()
    else:
        score_agent_edge_review(**p)
        result = json.loads(p["edge_output"].read_text())
        assert result["global"]["unverifiable"] == 1
        assert result["global"]["correct"] == 9
        assert result["adjudication_evidence_depth_counts"] == {"secondary_source_only": 1}


@pytest.fixture
def post_export_package(edge_package):
    p = with_adjudication(edge_package)
    freeze = json.loads(p["evaluation_freeze"].read_text())
    actual_run = freeze["evaluator_runs"].pop()
    freeze["adjudication_policy"] = "separate_source_review_after_frozen_exports"
    write_json(p["evaluation_freeze"], freeze)
    p["adjudication_start_receipt"] = write_json(p["edge_output"].parent / "adjudication-start.json", {
        "evaluation_freeze_sha256": digest(p["evaluation_freeze"]),
        "created_at": "2026-11-09T02:11:00+07:00", "evaluator_run": actual_run,
        "initial_exports": [{"path": str(path), "sha256": digest(path)}
                            for path in [p["edge_ledger"], *p["edge_reviews"]]],
    })
    receipt = json.loads(p["completion_receipt"].read_text())
    receipt["output_files"].append({"path": str(p["adjudication_start_receipt"]),
                                    "sha256": digest(p["adjudication_start_receipt"])})
    write_json(p["completion_receipt"], receipt)
    rebind(p)
    return p


def test_adjudication_metadata_can_be_recorded_after_exports_without_changing_freeze(post_export_package):
    p = post_export_package
    original = p["evaluation_freeze"].read_bytes()
    assert {run["reviewer_id"] for run in json.loads(original)["evaluator_runs"]} == {"A", "B"}
    score_agent_edge_review(**p)
    result = json.loads(p["edge_output"].read_text())
    assert p["evaluation_freeze"].read_bytes() == original
    assert {run["reviewer_id"] for run in result["agent_provenance"]["evaluator_runs"]} == {"A", "B", "ADJ"}
    assert result["agent_provenance"]["adjudication_start_receipt"]["sha256"] == digest(p["adjudication_start_receipt"])
    assert result["global"]["unverifiable"] == 1


@pytest.mark.parametrize("mutation,match", [
    ("changed_initial_hash", "initial exports hash mismatch"),
    ("missing_initial_csv", "initial exports does not bind required input"),
    ("early_start", "ADJ run must start after frozen A/B exports"),
    ("reused_context", "share an evaluator context"),
    ("reused_run", "distinct actual IDs"),
    ("premature_receipt", "before its start receipt"),
    ("judgment_before_receipt", "follow both initial judgments and its start receipt"),
    ("unbound_start_receipt", "completion receipt does not bind required input"),
    ("wrong_freeze", "start receipt does not bind the evaluation freeze"),
    ("missing_policy", "must declare separate adjudication"),
    ("predeclared_run", "must not replace a predeclared ADJ"),
])
def test_post_export_receipt_rejects_changed_sources_and_false_run_chronology(post_export_package, mutation, match):
    p = post_export_package
    start = json.loads(p["adjudication_start_receipt"].read_text())
    receipt = json.loads(p["completion_receipt"].read_text())
    freeze = json.loads(p["evaluation_freeze"].read_text())
    if mutation == "changed_initial_hash": start["initial_exports"][0]["sha256"] = "0" * 64
    elif mutation == "missing_initial_csv": start["initial_exports"].pop()
    elif mutation == "early_start": start["evaluator_run"]["started_at"] = "2026-11-09T02:00:00+07:00"
    elif mutation == "reused_context": start["evaluator_run"]["context_id"] = "context-A"
    elif mutation == "reused_run": start["evaluator_run"]["evaluator_run_id"] = "run-A"
    elif mutation == "premature_receipt": start["created_at"] = "2026-11-09T02:09:00+07:00"
    elif mutation == "judgment_before_receipt": start["created_at"] = "2026-11-09T02:16:00+07:00"
    elif mutation == "unbound_start_receipt": receipt["output_files"].pop()
    elif mutation == "wrong_freeze": start["evaluation_freeze_sha256"] = "0" * 64
    elif mutation == "missing_policy": freeze.pop("adjudication_policy")
    elif mutation == "predeclared_run": freeze["evaluator_runs"].append(start["evaluator_run"])
    write_json(p["evaluation_freeze"], freeze)
    write_json(p["adjudication_start_receipt"], start)
    write_json(p["completion_receipt"], receipt)
    rebind(p)
    with pytest.raises(ValueError, match=match):
        score_agent_edge_review(**p)
    assert not p["edge_output"].exists()


def test_output_refuses_overwrite_and_dangling_symlink(edge_package):
    p = edge_package
    p["edge_output"].symlink_to(p["edge_output"].parent / "missing")
    with pytest.raises(ValueError, match="refusing to overwrite"):
        score_agent_edge_review(**p)
    p["edge_output"].unlink()
    p["edge_output"].write_text("protected")
    with pytest.raises(ValueError, match="refusing to overwrite"):
        score_agent_edge_review(**p)
    assert p["edge_output"].read_text() == "protected"


def test_release_sample_sizes_cannot_use_the_small_fixture_design(edge_package, monkeypatch):
    read_graph = edge_audit._read_graph
    def release_design(*args):
        artifact, raw, errors = read_graph(*args)
        # Only exercise the release-design guard. No result is scored or emitted.
        return artifact.model_copy(update={"is_synthetic": False}), raw, errors
    monkeypatch.setattr(edge_audit, "_read_graph", release_design)
    with pytest.raises(ValueError, match="200 global / 10 per type / 50 overlap"):
        score_agent_edge_review(**edge_package)
    assert not edge_package["edge_output"].exists()


def test_numeric_thresholds_cannot_be_lowered(edge_package):
    p = edge_package
    quality = yaml.safe_load(p["quality"].read_text())
    quality["audit"]["min_precision"] = 0.8
    p["quality"].write_text(yaml.safe_dump(quality))
    rebind(p)
    with pytest.raises(ValueError, match="preserve the D040 precision thresholds"):
        score_agent_edge_review(**p)
    assert not p["edge_output"].exists()


def test_failed_numeric_gate_exit_is_preserved_and_ai_scoped(edge_package, monkeypatch):
    evaluate = edge_audit.evaluate_edge_audit
    def failed_gate(*args, **kwargs):
        result, _ = evaluate(*args, **kwargs)
        # Exercise the wrapper boundary without misrepresenting an invented graph
        # as measured release data or bypassing any provenance checks.
        result.update(status="fail", numeric_gate_status="fail", course_gate={"status": "fail"})
        return result, 1
    monkeypatch.setattr(edge_audit, "evaluate_edge_audit", failed_gate)
    summary, code = score_agent_edge_review(**edge_package)
    result = json.loads(edge_package["edge_output"].read_text())
    assert code == 1
    assert summary["edge_status"] == result["ai_assessed_numeric_checks"]["project_status"] == "fail"
    assert result["course_gate"]["scope"] == "ai_assessed_only"
