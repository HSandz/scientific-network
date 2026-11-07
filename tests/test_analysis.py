import json
import hashlib
from pathlib import Path

import networkx as nx
import yaml

from scientific_network.analysis.analyze import _pagerank, analyze_graph
from scientific_network.cli import main


ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "tests/fixtures/synthetic_graph.json"
ANALYSIS = ROOT / "configs/analysis.yaml"
QUALITY = ROOT / "configs/quality.yaml"
RELEASE_ANALYSIS = ROOT / "configs/analysis-release-v1.yaml"
RELEASE_QUALITY = ROOT / "configs/quality-release-v1.yaml"


def test_synthetic_analysis_emits_named_projections_without_release_claim(tmp_path):
    output = tmp_path / "analysis.json"
    assert main([
        "analyze", "--input", str(GRAPH), "--config", str(ANALYSIS),
        "--output", str(output),
    ]) == 0
    result = json.loads(output.read_text())
    assert result["status"] == "synthetic_protocol_only"
    assert result["release_status"] == "ineligible_synthetic"
    assert set(result["projections"]) == {
        "researcher_collaboration", "organization_collaboration", "core_citations",
        "paper_topics", "organization_topics",
    }
    assert result["projections"]["researcher_collaboration"]["node_count"] == 5
    assert result["projections"]["researcher_collaboration"]["edge_count"] == 3
    assert result["projections"]["organization_collaboration"]["edge_count"] == 2
    citations = result["projections"]["core_citations"]
    assert citations["directed"] is True
    assert citations["edge_count"] == 2
    assert citations["strength_sum"] == 2.0
    assert abs(sum(item["score"] for item in citations["top_pagerank"]) - 1.0) < 1e-9
    assert len(result["projections"]["researcher_collaboration"]["communities"]) == 6
    assert result["projections"]["paper_topics"]["communities_applicable"] is False
    assert result["robustness"]["sensitivity_comparison"] == "not_computed"
    assert result["robustness"]["strict_evidence_filter_sha256"] is None
    assert result["business_findings"]["status"] == "not_generated"


def test_synthetic_metrics_replay_identically_and_outputs_do_not_overwrite(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    one = analyze_graph(GRAPH, ANALYSIS, first)
    two = analyze_graph(GRAPH, ANALYSIS, second)
    one.pop("run_at")
    two.pop("run_at")
    assert one == two
    assert main([
        "analyze", "--input", str(GRAPH), "--config", str(ANALYSIS),
        "--output", str(first),
    ]) == 1
    assert json.loads(first.read_text())["status"] == "synthetic_protocol_only"


def test_frozen_strict_filter_runs_sensitivity_comparison_on_synthetic_only(tmp_path):
    config = yaml.safe_load(ANALYSIS.read_text())
    config["robustness"]["stricter_evidence_filter_status"] = "frozen"
    config["robustness"]["strict_evidence_filter"] = {"minimum_support_count": 2}
    config_path = tmp_path / "analysis.yaml"
    config_path.write_text(yaml.safe_dump(config))
    output = tmp_path / "analysis.json"
    result = analyze_graph(GRAPH, config_path, output)
    assert result["status"] == "synthetic_protocol_only"
    assert result["robustness"]["sensitivity_comparison"] == "computed"
    canonical_filter = json.dumps(
        {"minimum_support_count": 2}, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    assert result["robustness"]["strict_evidence_filter_sha256"] == hashlib.sha256(canonical_filter).hexdigest()
    assert set(result["strict_projections"]) == set(result["projections"])
    assert result["robustness"]["per_projection"]["researcher_collaboration"]["edge_retention_fraction"] == 0.0


def test_non_synthetic_graph_requires_frozen_config_and_strict_filter(tmp_path, capsys):
    graph_value = json.loads(GRAPH.read_text())
    graph_value["is_synthetic"] = False
    graph = tmp_path / "graph.json"
    graph.write_text(json.dumps(graph_value))
    output = tmp_path / "analysis.json"
    assert main([
        "analyze", "--input", str(graph), "--config", str(ANALYSIS),
        "--output", str(output),
    ]) == 1
    assert not output.exists()
    error = json.loads(capsys.readouterr().err)
    assert "frozen analysis configuration" in error["message"]

    frozen = yaml.safe_load(ANALYSIS.read_text())
    frozen["status"] = "frozen"
    frozen_path = tmp_path / "frozen-analysis.yaml"
    frozen_path.write_text(yaml.safe_dump(frozen))
    assert main([
        "analyze", "--input", str(graph), "--config", str(frozen_path),
        "--quality-config", str(QUALITY), "--output", str(output),
    ]) == 1
    assert not output.exists()
    assert "frozen strict evidence-filter" in json.loads(capsys.readouterr().err)["message"]


def test_pagerank_power_iteration_handles_dangling_nodes():
    graph = nx.DiGraph()
    graph.add_nodes_from(("a", "b", "c"))
    graph.add_edge("a", "b", strength=2.0)
    scores = _pagerank(graph)
    assert set(scores) == {"a", "b", "c"}
    assert all(score > 0 for score in scores.values())
    assert abs(sum(scores.values()) - 1.0) < 1e-12


def _real_graph(tmp_path):
    value = json.loads(GRAPH.read_text())
    value["is_synthetic"] = False
    path = tmp_path / "graph.json"
    path.write_text(json.dumps(value))
    return path


def test_real_graph_analysis_needs_no_readiness_receipt_and_records_failed_size_gates(tmp_path):
    output = tmp_path / "analysis.json"
    result = analyze_graph(_real_graph(tmp_path), RELEASE_ANALYSIS, output, None, RELEASE_QUALITY)
    assert result["status"] == "analysis_metrics_only"
    assert result["release_status"] == "not_certified"
    assert result["readiness_sha256"] is None
    assert result["analysis_config_status"] == "frozen"
    assert result["size_gates"]["status"] == "failed"
    gates = result["size_gates"]["gates"]
    assert gates["min_domain_nodes"] == {"required": 2000, "actual": 14, "status": "failed"}
    assert gates["min_resolved_core_researchers"]["actual"] == 5
    assert gates["required_relation_types"] == {"required": 10, "actual": 10, "status": "passed"}
    # a failed gate is reported, and the analysis itself still ran
    assert result["projections"]["researcher_collaboration"]["edge_count"] == 3
    assert result["robustness"]["sensitivity_comparison"] == "computed"
    assert json.loads(output.read_text())["size_gates"] == result["size_gates"]


def test_real_graph_size_gates_pass_when_thresholds_are_met(tmp_path):
    quality = yaml.safe_load(RELEASE_QUALITY.read_text())
    quality["size"].update(min_domain_nodes=14, min_resolved_core_researchers=5,
                           min_unique_factual_edges=16, required_relation_types=10)
    quality_path = tmp_path / "quality.yaml"
    quality_path.write_text(yaml.safe_dump(quality))
    result = analyze_graph(_real_graph(tmp_path), RELEASE_ANALYSIS, tmp_path / "analysis.json", None, quality_path)
    assert result["size_gates"]["status"] == "passed"
    assert {gate["status"] for gate in result["size_gates"]["gates"].values()} == {"passed"}


def test_real_graph_still_requires_a_quality_config_and_verifies_a_supplied_receipt(tmp_path):
    graph = _real_graph(tmp_path)
    try:
        analyze_graph(graph, RELEASE_ANALYSIS, tmp_path / "a.json")
    except ValueError as exc:
        assert "quality config is required" in str(exc)
    else:
        raise AssertionError("expected a quality config requirement")
    receipt = tmp_path / "readiness.json"
    receipt.write_text("[]")
    try:
        analyze_graph(graph, RELEASE_ANALYSIS, tmp_path / "b.json", receipt, RELEASE_QUALITY)
    except ValueError as exc:
        assert "readiness receipt" in str(exc)
    else:
        raise AssertionError("a supplied receipt must still match")
    assert not (tmp_path / "b.json").exists()


def test_synthetic_analysis_does_not_compute_size_gates(tmp_path):
    result = analyze_graph(GRAPH, ANALYSIS, tmp_path / "analysis.json", None, QUALITY)
    assert result["size_gates"] is None
