import csv
import json
from pathlib import Path

import yaml

from scientific_network.cli import main
from scientific_network.evaluation.edge_audit import (
    ADJUDICATION_FIELDS,
    REVIEW_FIELDS,
    _check_readiness,
    prepare_edge_audit_sample,
)


ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "tests/fixtures/synthetic_graph.json"
QUALITY = ROOT / "configs/quality.yaml"


def _config(path: Path, *, global_size=5, per_type_size=2):
    config = yaml.safe_load(QUALITY.read_text())
    config["audit"]["global_sample_size"] = global_size
    config["audit"]["per_type_sample_size"] = per_type_size
    path.write_text(yaml.safe_dump(config))
    return path


def _sample(tmp_path):
    config = _config(tmp_path / "quality.yaml")
    sample = tmp_path / "sample.csv"
    result = prepare_edge_audit_sample(GRAPH, config, sample)
    return config, sample, result


def _write_reviews(sample: Path, output: Path, disagreement_edge: str | None = None):
    with sample.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    completed = []
    for row in rows:
        for reviewer in ("synthetic-reviewer-a", "synthetic-reviewer-b"):
            review = dict(row)
            review["reviewer_id"] = reviewer
            review["endpoints_correct"] = "true"
            review["predicate_correct"] = "true"
            review["paper_time_correct"] = "true"
            review["evidence_verifiable"] = "true"
            review["decision"] = "correct"
            review["reason"] = ""
            review["reviewed_at"] = "2026-11-07T14:00:00+00:00"
            if row["edge_id"] == disagreement_edge and reviewer == "synthetic-reviewer-b":
                review["evidence_verifiable"] = "false"
                review["decision"] = "incorrect"
                review["reason"] = "invented disagreement fixture"
            completed.append(review)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(completed)
    return rows


def test_freeze_edge_audit_sample_is_bound_and_synthetic(tmp_path):
    _, sample, result = _sample(tmp_path)
    assert b"\r\n" not in sample.read_bytes()
    with sample.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert result["status"] == "synthetic_protocol_sample"
    assert result["release_audit_performed"] is False
    assert result["global_sample_size"] == 5
    assert result["union_sample_size"] == len(rows)
    assert len({row["edge_id"] for row in rows}) == len(rows)
    assert all(not row["reviewer_id"] and not row["decision"] for row in rows)
    assert all(not row["readiness_sha256"] for row in rows)
    assert all(row["frame_sha256"] == result["frame_sha256"] for row in rows)


def test_edge_audit_requires_two_reviews_and_marks_synthetic(tmp_path):
    config, sample, _ = _sample(tmp_path)
    reviews = tmp_path / "reviews.csv"
    rows = _write_reviews(sample, reviews)
    output = tmp_path / "evaluation.json"
    assert main([
        "score-edge-audit", "--input", str(GRAPH), "--reviews", str(reviews),
        "--config", str(config), "--output", str(output),
    ]) == 0
    result = json.loads(output.read_text())
    assert result["status"] == "synthetic_protocol_only"
    assert result["release_status"] == "ineligible_synthetic"
    assert result["reviewer_identity_status"] == "input_declared_not_independently_verified"
    assert result["global"]["total"] == 5
    assert result["global"]["correct"] == 5
    assert len(result["reviewers"]) == 2
    assert len(rows) >= result["sampled_global_edge_ids"]


def test_synthetic_census_has_no_wilson_or_release_claim(tmp_path):
    config = _config(tmp_path / "quality.yaml", global_size=1000, per_type_size=1000)
    sample = tmp_path / "sample.csv"
    prepare_edge_audit_sample(GRAPH, config, sample)
    reviews = tmp_path / "reviews.csv"
    _write_reviews(sample, reviews)
    output = tmp_path / "evaluation.json"
    assert main([
        "score-edge-audit", "--input", str(GRAPH), "--reviews", str(reviews),
        "--config", str(config), "--output", str(output),
    ]) == 0
    result = json.loads(output.read_text())
    assert result["status"] == "synthetic_protocol_only"
    assert result["numeric_gate_status"] == "not_applicable_synthetic"
    assert result["global"]["total"] == 27
    assert result["global"]["is_census"] is True
    assert result["global"]["wilson_95"] is None
    assert result["global_point_precision_gate"] is None
    assert result["global_wilson_lower_gate"] is None
    assert all(metric["wilson_95"] is None for metric in result["per_type"].values())


def test_disagreement_requires_adjudication_and_unverifiable_is_not_correct(tmp_path):
    config, sample, _ = _sample(tmp_path)
    with sample.open(newline="", encoding="utf-8") as stream:
        sample_rows = list(csv.DictReader(stream))
    target = next(row["edge_id"] for row in sample_rows if row["in_global_sample"] == "true")
    reviews = tmp_path / "reviews.csv"
    _write_reviews(sample, reviews, disagreement_edge=target)
    output = tmp_path / "evaluation.json"
    common = ["score-edge-audit", "--input", str(GRAPH), "--reviews", str(reviews),
              "--config", str(config), "--output", str(output)]
    assert main(common) == 1
    assert not output.exists()

    adjudications = tmp_path / "adjudications.csv"
    with adjudications.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=ADJUDICATION_FIELDS)
        writer.writeheader()
        writer.writerow({
            "audit_id": sample_rows[0]["audit_id"],
            "method_version": sample_rows[0]["method_version"],
            "graph_version": sample_rows[0]["graph_version"],
            "graph_sha256": sample_rows[0]["graph_sha256"],
            "quality_config_sha256": sample_rows[0]["quality_config_sha256"],
            "readiness_sha256": sample_rows[0]["readiness_sha256"],
            "frame_sha256": sample_rows[0]["frame_sha256"],
            "edge_id": target,
            "adjudicator_id": "synthetic-adjudicator",
            "decision": "unverifiable",
            "reason": "invented synthetic adjudication",
            "reviewed_at": "2026-11-07T14:05:00+00:00",
        })
    assert main([*common, "--adjudications", str(adjudications)]) == 0
    result = json.loads(output.read_text())
    assert result["status"] == "synthetic_protocol_only"
    assert result["global"]["unverifiable"] + result["global"]["incorrect"] >= 1


def _real_graph(tmp_path, *, drop_relation: str | None = None) -> Path:
    artifact = json.loads(GRAPH.read_text())
    artifact["is_synthetic"] = False
    if drop_relation:
        artifact["edges"] = [e for e in artifact["edges"] if e["relation"] != drop_relation]
    graph = tmp_path / "graph.json"
    graph.write_text(json.dumps(artifact))
    return graph


def test_real_graph_sample_needs_no_readiness_receipt_and_records_failed_size_gates(tmp_path, capsys):
    graph = _real_graph(tmp_path)
    config = _config(tmp_path / "quality.yaml")
    output = tmp_path / "sample.csv"
    assert main(["freeze-audit-sample", "--input", str(graph), "--config", str(config),
                 "--output", str(output)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "review_form_prepared"
    assert result["readiness_sha256"] is None
    assert result["size_gates"]["status"] == "failed"
    gates = result["size_gates"]["gates"]
    assert gates["min_domain_nodes"] == {"required": 2000, "actual": 14, "status": "failed"}
    assert gates["required_relation_types"] == {"required": 10, "actual": 10, "status": "passed"}
    with output.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert rows and all(row["readiness_sha256"] == "" for row in rows)


def test_size_gates_are_recorded_as_passed_when_thresholds_are_met(tmp_path, capsys):
    graph = _real_graph(tmp_path)
    config = _config(tmp_path / "quality.yaml")
    value = yaml.safe_load(config.read_text())
    value["size"].update(min_domain_nodes=14, min_resolved_core_researchers=5,
                         min_unique_factual_edges=16, required_relation_types=10)
    config.write_text(yaml.safe_dump(value))
    assert main(["freeze-audit-sample", "--input", str(graph), "--config", str(config),
                 "--output", str(tmp_path / "sample.csv")]) == 0
    assert json.loads(capsys.readouterr().out)["size_gates"]["status"] == "passed"


def test_empty_relation_is_sampled_around_not_a_reason_to_stop(tmp_path, capsys):
    graph = _real_graph(tmp_path, drop_relation="CITES")
    config = _config(tmp_path / "quality.yaml")
    output = tmp_path / "sample.csv"
    assert main(["freeze-audit-sample", "--input", str(graph), "--config", str(config),
                 "--output", str(output)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert "CITES" not in result["per_type_sample_sizes"]
    assert result["size_gates"]["gates"]["required_relation_types"]["status"] == "failed"


def test_a_supplied_readiness_receipt_must_still_match_the_graph(tmp_path):
    graph = _real_graph(tmp_path)
    config = _config(tmp_path / "quality.yaml")
    output = tmp_path / "sample.csv"
    readiness = tmp_path / "readiness.json"
    readiness.write_text("[]")
    assert main(["freeze-audit-sample", "--input", str(graph), "--config", str(config),
                 "--readiness", str(readiness), "--output", str(output)]) == 1
    assert not output.exists()


def test_readiness_receipt_hash_is_returned_for_exact_graph(tmp_path):
    import hashlib

    from scientific_network.contracts import GraphArtifact

    artifact = json.loads(GRAPH.read_text())
    artifact["is_synthetic"] = False
    graph_bytes = json.dumps(artifact).encode("utf-8")
    graph = GraphArtifact.model_validate_json(graph_bytes)
    receipt = {
        "status": "post_build_audit_ready",
        "graph_version": graph.graph_version,
        "graph_sha256": hashlib.sha256(graph_bytes).hexdigest(),
        "preconstruction_gates_passed": True,
        "graph_construction": "completed",
    }
    receipt_bytes = json.dumps(receipt).encode("utf-8")
    path = tmp_path / "readiness.json"
    path.write_bytes(receipt_bytes)
    assert _check_readiness(path, graph, graph_bytes) == hashlib.sha256(receipt_bytes).hexdigest()


def test_review_packet_is_rejected_when_frame_hash_changes(tmp_path):
    config, sample, _ = _sample(tmp_path)
    reviews = tmp_path / "reviews.csv"
    _write_reviews(sample, reviews)
    with reviews.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    rows[0]["frame_sha256"] = "0" * 64
    with reviews.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    output = tmp_path / "evaluation.json"
    assert main([
        "score-edge-audit", "--input", str(GRAPH), "--reviews", str(reviews),
        "--config", str(config), "--output", str(output),
    ]) == 1
    assert not output.exists()
