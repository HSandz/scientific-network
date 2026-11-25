"""Tests for the closed 9-tool RAG layer (M3 Phase 2).

Includes synthetic Neo4j-free fixture tests covering every tool, plus an optional
live integration test against neo4j-enriched (port 7690).
"""

import json
import os
from pathlib import Path

import pytest

from scientific_network.rag.tools import InMemoryGraphBackend, Neo4jToolBackend, RAGToolset


def _synthetic_graph() -> dict:
    return {
        "graph_version": "enriched-synth",
        "nodes": [
            {"id": "researcher:1", "label": "Researcher", "name": "Wei Zhang", "properties": {}},
            {"id": "researcher:2", "label": "Researcher", "name": "Wei Zhang", "properties": {}},
            {"id": "organization:1", "label": "Organization", "name": "Tsinghua University", "properties": {"sector": "academia", "country_code": "CN"}},
            {"id": "organization:2", "label": "Organization", "name": "Peking University", "properties": {"sector": "academia", "country_code": "CN"}},
            {"id": "paper:1", "label": "Paper", "name": "LLM Reasoning at Scale", "properties": {"year": 2024}},
            {"id": "paper:2", "label": "Paper", "name": "Vision Transformers Earlier", "properties": {"year": 2021}},
            {"id": "method:llm", "label": "Method", "name": "Large Language Models (LLMs)", "properties": {"key": "language model", "paper_count": 10, "surfaces": {"large language models": 5}}},
            {"id": "task:nc1", "label": "Task", "name": "node classification", "properties": {"key": "node classification", "paper_count": 10}},
            {"id": "task:nc2", "label": "Task", "name": "node classification tasks", "properties": {"key": "node classification task", "paper_count": 5}},
            {"id": "dataset:cora", "label": "Dataset", "name": "Cora", "properties": {"key": "cora", "paper_count": 8}},
            {"id": "topic:nlp", "label": "Topic", "name": "Natural language processing and language models", "properties": {}},
            {"id": "venue:aaai", "label": "Venue", "name": "AAAI", "properties": {}},
        ],
        "edges": [
            {"edge_id": "e1", "relation": "AUTHORED", "source_id": "researcher:1", "target_id": "paper:1", "evidence_ids": ["ev:1"], "properties": {}},
            {"edge_id": "e2", "relation": "AUTHORED", "source_id": "researcher:2", "target_id": "paper:2", "evidence_ids": ["ev:2"], "properties": {}},
            {"edge_id": "e3", "relation": "AFFILIATED_WITH", "source_id": "researcher:1", "target_id": "organization:1", "evidence_ids": ["ev:3"], "properties": {}},
            {"edge_id": "e4", "relation": "AFFILIATED_WITH", "source_id": "researcher:2", "target_id": "organization:2", "evidence_ids": ["ev:4"], "properties": {}},
            {"edge_id": "e5", "relation": "COLLABORATED_WITH", "source_id": "organization:1", "target_id": "organization:2", "evidence_ids": ["ev:5"], "properties": {"support_count": 3}},
            {"edge_id": "e6", "relation": "USES_METHOD", "source_id": "paper:1", "target_id": "method:llm", "evidence_ids": ["ev:6"], "properties": {}},
            {"edge_id": "e7", "relation": "ADDRESSES_TASK", "source_id": "paper:1", "target_id": "task:nc1", "evidence_ids": ["ev:7"], "properties": {}},
            {"edge_id": "e8", "relation": "USES_DATASET", "source_id": "paper:1", "target_id": "dataset:cora", "evidence_ids": ["ev:8"], "properties": {}},
            {"edge_id": "e9", "relation": "HAS_TOPIC", "source_id": "paper:1", "target_id": "topic:nlp", "evidence_ids": ["ev:9"], "properties": {}},
            {"edge_id": "e10", "relation": "PUBLISHED_IN", "source_id": "paper:1", "target_id": "venue:aaai", "evidence_ids": ["ev:10"], "properties": {}},
            {"edge_id": "e11", "relation": "PUBLISHED_IN", "source_id": "paper:2", "target_id": "venue:aaai", "evidence_ids": ["ev:11"], "properties": {}},
        ],
    }


def _make_artifacts(tmp_path: Path) -> tuple[Path, Path]:
    a_dir = tmp_path / "analysis"
    r_dir = tmp_path / "rag"
    (a_dir / "ranking").mkdir(parents=True)
    (a_dir / "communities").mkdir(parents=True)
    (a_dir / "trends").mkdir(parents=True)
    r_dir.mkdir(parents=True)

    (a_dir / "ranking" / "ranking-N2.json").write_text(json.dumps({
        "nodes": 2, "edges": 1, "top": [{"rank": 1, "id": "organization:1", "name": "Tsinghua University", "pagerank": 0.5, "degree": 1}],
    }))
    (a_dir / "ranking" / "personalized-pagerank.json").write_text(json.dumps({
        "subjects": {"Method": {"method:llm": {"name": "Large Language Models (LLMs)", "papers": 1,
                                               "top": {"Organization": [{"id": "organization:1", "name": "Tsinghua University", "lift": 2.5, "subject_papers": 1}]}}}}
    }))
    (a_dir / "communities" / "communities-N1.json").write_text(json.dumps({
        "labels": {"0": {"Topic": [{"name": "NLP"}]}},
        "key_individuals": {"0": {"hubs": ["researcher:1"]}},
    }))
    import gzip
    with gzip.open(a_dir / "communities" / "membership-N1.csv.gz", "wt") as f:
        f.write("id,level0,level1\nresearcher:1,0,0\nresearcher:2,0,0\n")
    (a_dir / "trends" / "trends-summary.json").write_text(json.dumps({
        "classification_note": "descriptive (p <= 0.10 per subject, no multiple-testing correction)",
        "caveats": ["two venues only"],
    }))
    (a_dir / "trends" / "display-aliases.json").write_text(json.dumps({
        "by_kind": {"Task": [{"canonical_key": "node classification", "members": [{"id": "task:nc1", "name": "node classification", "papers": 10}, {"id": "task:nc2", "name": "node classification tasks", "papers": 5}]}]},
    }))
    (a_dir / "trends" / "trends-task.csv").write_text(
        "kind,id,name,class,total_papers,base_window_papers,recent_window_papers,cagr_of_share_2021_2025,slope_of_share,slope_p_value,papers_2021,papers_2022,papers_2023,papers_2024,papers_2025,share_2021,share_2022,share_2023,share_2024,share_2025\n"
        "Task,task:nc1,node classification,rising,10,2,8,0.5,0.01,0.05,1,1,0,4,4,0.1,0.1,0.0,0.2,0.2\n"
    )
    (r_dir / "community-reports.json").write_text(json.dumps({
        "reports": [{"community_id": "research:L1:0", "title": "LLM Reasoning", "summary": "Test", "key_findings": [{"claim": "LLM papers", "paper_ids": ["paper:1"]}], "centrality_rating": 8}]
    }))
    return a_dir, r_dir


def test_tools_all_nine_on_synthetic_fixture(tmp_path: Path):
    a_dir, r_dir = _make_artifacts(tmp_path)
    ts = RAGToolset(InMemoryGraphBackend(_synthetic_graph()), analysis_dir=a_dir, rag_dir=r_dir)

    # 1. find: same-name researcher returns ambiguous choice list, never auto-merged
    res_find = ts.find("Researcher", "Wei Zhang")
    assert res_find.ambiguous is True and len(res_find.rows) == 2

    # find: surface form matches LLM
    res_llm = ts.find("Method", "large language model")
    assert not res_llm.empty and res_llm.ids == ["method:llm"]

    # 2. neighbors: method->task uses paper co-occurrence with shared paper_ids
    res_nb = ts.neighbors("method:llm", predicates=["APPLIED_TO"], filters={"target_labels": ["Task"]})
    assert not res_nb.empty
    assert res_nb.source_kind == "paper_cooccurrence"
    assert "paper:1" in res_nb.paper_ids

    # 3. path
    res_path = ts.path("organization:1", "organization:2", max_len=2, predicates=["COLLABORATED_WITH"])
    assert not res_path.empty and len(res_path.rows) == 1

    # 4. papers
    res_p = ts.papers({"organization_id": "organization:1", "method_id": "method:llm", "year_min": 2023})
    assert res_p.ids == ["paper:1"]

    # 5. aggregate (both by year and organization_year share_growth; test threshold enforcement)
    res_agg_filtered = ts.aggregate(["organization:1"], by="organization_year", metric="share_growth", filters={"method_id": "method:llm", "after_year": 2022})
    assert res_agg_filtered.empty is True  # 1 paper < default min_post_total_papers=10
    res_agg = ts.aggregate(
        ["organization:1"],
        by="organization_year",
        metric="share_growth",
        filters={"method_id": "method:llm", "after_year": 2022, "min_post_total_papers": 1, "min_post_subject_papers": 1},
    )
    assert res_agg.rows[0]["post_gt_2022_share"] == 1.0
    assert res_agg.rows[0]["post_papers"] == "1 of 1"
    assert res_agg.rows[0]["paper_ids"] == ["paper:1"]

    # 6. rank (global + subject-specific lift)
    assert ts.rank("N2").rows[0]["id"] == "organization:1"
    assert ts.rank("N2", scope="method:llm").rows[0]["lift"] == 2.5

    # 7. community
    res_comm = ts.community("researcher:1", network="N1")
    assert not res_comm.empty and res_comm.rows[0]["community"] == 0

    # 8. community_report
    res_rep = ts.community_report("research:L1:0")
    assert not res_rep.empty and res_rep.paper_ids == ["paper:1"]

    # 9. trend (resolves display alias "node classification tasks" -> task:nc1)
    res_tr = ts.trend("node classification tasks")
    assert not res_tr.empty and res_tr.rows[0]["id"] == "task:nc1"

    # Reject disallowed labels/predicates
    with pytest.raises(ValueError):
        ts.find("ArbitraryLabel", "x")
    with pytest.raises(ValueError):
        ts.neighbors("organization:1", predicates=["DROP_TABLE"])


def test_live_neo4j_tools_integration():
    if not os.environ.get("NEO4J_PASSWORD"):
        from dotenv import load_dotenv
        load_dotenv(".env")
    if not os.environ.get("NEO4J_PASSWORD"):
        pytest.skip("NEO4J_PASSWORD unavailable")
    backend = Neo4jToolBackend()
    try:
        rows = backend.run_read("RETURN 1 AS ok")
        assert rows == [{"ok": 1}]
    except Exception as exc:
        backend.close()
        pytest.skip(f"neo4j-enriched 7690 unavailable: {exc}")
    try:
        ts = RAGToolset(backend)
        f = ts.find("Organization", "Tsinghua University")
        assert not f.empty and f.ids[0] == "organization:I99065089"
        co = ts.neighbors("method:Q3621696", filters={"target_labels": ["Task"]}, limit=10)
        assert not co.empty and len(co.paper_ids) > 0
        tr = ts.trend("node classification tasks")
        assert not tr.empty
    finally:
        backend.close()
