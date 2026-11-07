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


def test_non_synthetic_graph_requires_frozen_config_and_post_build_readiness(tmp_path, capsys):
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
