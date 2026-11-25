"""Offline unit tests for GraphRAG index, grounding validation, SQLite vectors, and local/global retrieval (M3 Phase 3)."""

import json
from pathlib import Path

import numpy as np

from scientific_network.rag.index import (
    build_research_communities,
    generate_community_reports,
    validate_report_grounding,
)
from scientific_network.rag.llm import LLMResult
from scientific_network.rag.retrieval import global_search, local_search
from scientific_network.rag.sqlite_vectors import SQLiteVectorStore
from scientific_network.rag.tools import InMemoryGraphBackend, RAGToolset


class _MockLLMConfig:
    model = "mock-4b"


class _FakeLLM:
    def __init__(self, responses: list[dict | str]) -> None:
        self.responses = list(responses)
        self.calls: list[str] = []
        self.config = _MockLLMConfig()

    def complete(self, *, prompt_version: str, system: str, user: str, schema=None, schema_name="answer", max_tokens=None):
        self.calls.append(prompt_version)
        val = self.responses.pop(0)
        raw = json.dumps(val) if isinstance(val, dict) else str(val)
        return LLMResult(
            content=raw,
            parsed=val if isinstance(val, dict) else None,
            prompt_tokens=10,
            completion_tokens=10,
            finish_reason="stop",
            cache_hit=False,
            attempts=1,
            input_sha256="in",
            output_sha256="out",
        )


def test_validate_report_grounding_catches_invented_paper_and_number():
    payload = {"community_id": "research:L1:0", "size": 12, "paper_count": 40, "top_papers": [{"id": "paper:aaai:2024:1", "title": "A"}]}
    bad_paper = {
        "title": "Test",
        "summary": "Covers 12 entities across 40 papers.",
        "key_findings": [{"claim": "Found in 40 papers.", "paper_ids": ["paper:aaai:2024:999"]}],
        "centrality_rating": 7,
        "centrality_rationale": "Central across 40 papers.",
    }
    errs1 = validate_report_grounding(bad_paper, {"paper:aaai:2024:1"}, payload)
    assert any("ungrounded paper_ids" in e for e in errs1)

    bad_num = {
        "title": "Test",
        "summary": "Covers 999 entities.",
        "key_findings": [{"claim": "Found in 40 papers.", "paper_ids": ["paper:aaai:2024:1"]}],
        "centrality_rating": 7,
        "centrality_rationale": "Central.",
    }
    errs2 = validate_report_grounding(bad_num, {"paper:aaai:2024:1"}, payload)
    assert any("ungrounded number 999" in e for e in errs2)


def test_generate_reports_retries_once_then_drops():
    cfg = {"communities": {"research_graph": {"min_members_for_report": 2}}, "reports": {"prompt_version": "v1", "ai_generated_label": "AI-generated from graph data"}}
    research_comms = {
        "communities": {
            "research:L1:0": {"level": 1, "size": 5, "paper_count": 10, "papers_by_year": {"2024": 10}, "top_entities": [], "top_organizations": [], "top_papers": [{"id": "paper:aaai:2024:1", "title": "A"}]},
            "research:L1:1": {"level": 1, "size": 5, "paper_count": 8, "papers_by_year": {"2024": 8}, "top_entities": [], "top_organizations": [], "top_papers": [{"id": "paper:aaai:2024:2", "title": "B"}]},
        }
    }
    # First community fails once with bad number 777, succeeds on retry; second fails twice -> dropped
    good = {"title": "OK", "summary": "10 papers.", "key_findings": [{"claim": "10 papers.", "paper_ids": ["paper:aaai:2024:1"]}], "centrality_rating": 6, "centrality_rationale": "5 entities."}
    bad1 = {"title": "Bad", "summary": "777 papers.", "key_findings": [{"claim": "10 papers.", "paper_ids": ["paper:aaai:2024:1"]}], "centrality_rating": 6, "centrality_rationale": "5 entities."}
    bad2 = {"title": "Bad", "summary": "888 papers.", "key_findings": [{"claim": "8 papers.", "paper_ids": ["paper:aaai:2024:2"]}], "centrality_rating": 6, "centrality_rationale": "5 entities."}
    llm = _FakeLLM([bad1, good, bad2, bad2])
    reports, stats = generate_community_reports(research_comms, [], cfg, llm)
    assert len(reports) == 1 and reports[0]["community_id"] == "research:L1:0"
    assert stats["succeeded_retry"] == 1 and stats["dropped"] == 1


def test_sqlite_vector_store_and_local_global_retrieval(tmp_path: Path):
    db = SQLiteVectorStore(tmp_path / "vectors.sqlite")
    v1 = np.zeros(384, dtype=np.float32)
    v1[0] = 1.0
    v2 = np.zeros(384, dtype=np.float32)
    v2[1] = 1.0
    counts = db.write([
        {"kind": "community_report", "id": "research:L1:0", "text": "LLM reasoning report", "metadata": {"paper_ids": ["paper:aaai:2024:1"]}, "embedding": v1},
        {"kind": "entity_description", "id": "method:llm", "text": "Large Language Models", "metadata": {"label": "Method"}, "embedding": v1},
        {"kind": "abstract_chunk", "id": "paper:aaai:2024:1#s0", "text": "We study LLM reasoning.", "metadata": {"paper_id": "paper:aaai:2024:1"}, "embedding": v1},
        {"kind": "abstract_chunk", "id": "paper:aaai:2024:2#s0", "text": "Vision task.", "metadata": {"paper_id": "paper:aaai:2024:2"}, "embedding": v2},
    ])
    assert counts["abstract_chunk"] == 2
    hits = db.search("abstract_chunk", v1, top_k=1)
    assert hits[0]["id"] == "paper:aaai:2024:1#s0"

    graph = {
        "nodes": [
            {"id": "method:llm", "label": "Method", "name": "Large Language Models", "properties": {}},
            {"id": "paper:aaai:2024:1", "label": "Paper", "name": "LLM Paper", "properties": {"year": 2024}},
        ],
        "edges": [
            {"edge_id": "e1", "relation": "USES_METHOD", "source_id": "paper:aaai:2024:1", "target_id": "method:llm", "evidence_ids": ["ev1"], "properties": {}},
        ],
    }
    ts = RAGToolset(InMemoryGraphBackend(graph), analysis_dir=tmp_path, rag_dir=tmp_path)
    loc = local_search("LLM", toolset=ts, vector_store=db, embed_fn=lambda _: v1, char_budget=5000)
    assert "method:llm" in loc["linked_entity_ids"] and "paper:aaai:2024:1" in loc["paper_ids"]

    rep_path = tmp_path / "community-reports.json"
    rep_path.write_text(json.dumps({"reports": [{"community_id": "research:L1:0", "network": "research", "level": 1, "title": "LLM", "summary": "S", "key_findings": [{"claim": "C", "paper_ids": ["paper:aaai:2024:1"]}], "paper_count": 10, "centrality_rating": 8}]}))
    llm = _FakeLLM([{"points": [{"claim": "LLM growth", "importance": 9, "paper_ids": ["paper:aaai:2024:1"]}]}, "LLM research grew [paper:aaai:2024:1]."])
    glob = global_search("What are main directions?", llm=llm, reports_path=rep_path, vector_store=db, embed_fn=lambda _: v1)
    assert "paper:aaai:2024:1" in glob["paper_ids"] and glob["ai_generated_label"] == "AI-generated from graph data"


def test_research_communities_strict_nesting(tmp_path: Path):
    # Two disconnected cliques of 30 Method nodes connected weakly -> L1 splits into 2 or 1, L0 nests inside L1
    nodes = [{"id": f"method:{i}", "label": "Method", "name": f"M{i}", "properties": {}} for i in range(12)]
    nodes += [{"id": f"paper:{i}", "label": "Paper", "name": f"P{i}", "properties": {"year": 2024}} for i in range(12)]
    edges = []
    for i in range(6):
        for j in range(6):
            edges.append({"edge_id": f"e{i}_{j}", "relation": "USES_METHOD", "source_id": f"paper:{i}", "target_id": f"method:{j}", "properties": {}})
    for i in range(6, 12):
        for j in range(6, 12):
            edges.append({"edge_id": f"e{i}_{j}", "relation": "USES_METHOD", "source_id": f"paper:{i}", "target_id": f"method:{j}", "properties": {}})
    # Bridge paper connecting both
    edges.append({"edge_id": "eb1", "relation": "USES_METHOD", "source_id": "paper:0", "target_id": "method:6", "properties": {}})
    graph = {"graph_version": "synth", "nodes": nodes, "edges": edges, "affiliation_observations": []}
    (tmp_path / "trends").mkdir()
    cfg = {
        "communities": {"research_graph": {"labels": ["Method", "Task", "Dataset", "Topic"], "min_edge_weight": 1, "seed": 17, "level1_resolution": 1.0, "level0_resolution": 1.2, "level0_split_min_size": 5, "min_members_for_report": 2}},
        "reports": {"max_entities_in_input": 10, "max_papers_in_input": 5},
    }
    res = build_research_communities(graph, cfg, tmp_path)
    assert res["level1_count"] >= 1 and res["level0_count"] >= res["level1_count"]
    for cid, c in res["communities"].items():
        if c["level"] == 0:
            assert c["parent_id"] in res["communities"]
