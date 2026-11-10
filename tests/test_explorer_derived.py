"""Invented fixtures validate descriptive definitions, never measured research results."""
from pathlib import Path
import json

import pytest

from scientific_network.analysis.explorer_derived import build, derive


def example():
    def node(id, label, year=None):
        return {"id": id, "label": label, "name": id, "properties": {"year": year, "is_core": label == "Paper"}}
    result = {"graph_version": "synthetic-only", "nodes": [node("p1", "Paper", 2021), node("p2", "Paper", 2021), node("p3", "Paper", 2022), node("o1", "Organization"), node("o2", "Organization"), node("t1", "Topic"), node("t2", "Topic")], "edges": [
        {"relation": "PUBLISHED_IN", "source_id": p, "target_id": "venue:test"} for p in ("p1", "p2", "p3")
    ] + [
        {"relation": "CITES", "source_id": "p3", "target_id": "p1"},
        {"relation": "HAS_TOPIC", "source_id": "p1", "target_id": "t1"},
        {"relation": "HAS_TOPIC", "source_id": "p1", "target_id": "t2"},
        {"relation": "COLLABORATED_WITH", "source_id": "o1", "target_id": "o2", "edge_id": "e1", "evidence_ids": ["ev1", "ev2"]},
    ], "evidence": [{"id": "ev1", "support_paper_ids": ["p1", "p3"]}, {"id": "ev2", "support_paper_ids": ["p1", "outside"]}]}
    for edge in result["edges"]:
        edge["validation_status"] = "accepted"
    return result



def test_cohorts_include_uncited_ties_and_distinct_persistence_support():
    result = derive(example(), {"years": [2021, 2022, 2023], "pair_limit": 25})
    cohort = result["citation_cohorts"][0]
    assert cohort["paper_denominator"] == 2
    assert cohort["zero_in_degree_count"] == 1
    assert cohort["distribution"] == [{"in_degree": 0, "paper_count": 1}, {"in_degree": 1, "paper_count": 1}]
    leaders = {r["paper_id"]: r for r in result["cohort_leaders"]}
    assert leaders["p2"]["empirical_percentile_including_ties"] == .5
    assert leaders["p3"]["empirical_percentile_including_ties"] == 1
    pair = result["organization_pair_persistence"][0]
    assert pair["distinct_support_papers"] == 2
    assert pair["active_year_count"] == 2
    assert pair["by_year"][-1] == {"year": 2023, "distinct_support_papers": 0}
    assert [t["distinct_support_papers"] for t in pair["inferred_topics"]] == [1, 1]


def test_derived_output_is_deterministic_hash_bound_and_refuses_overwrite(tmp_path):
    graph = tmp_path / "graph.json"
    graph.write_text(json.dumps(example()))
    config = Path("configs/explorer-analysis-release-v1.yaml")
    first, second = tmp_path / "one.json", tmp_path / "two.json"
    build(graph, config, first)
    build(graph, config, second)
    assert first.read_bytes() == second.read_bytes()
    data = json.loads(first.read_bytes())
    assert len(data["graph_sha256"]) == len(data["config_sha256"]) == 64
    with pytest.raises(FileExistsError):
        build(graph, config, first)


def test_unaccepted_edges_do_not_change_descriptive_counts():
    graph = example()
    expected = derive(graph, {"years": [2021, 2022], "pair_limit": 25})
    graph["edges"].append({"relation": "CITES", "source_id": "p1", "target_id": "p3", "validation_status": "review"})
    assert derive(graph, {"years": [2021, 2022], "pair_limit": 25}) == expected
