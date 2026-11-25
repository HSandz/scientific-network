"""Offline unit tests for the Phase 4 multi-hop reasoning engine (planner, executor, faithfulness)."""

import json
from pathlib import Path

from scientific_network.rag.answer import compose_grounded_answer, run_ask, verify_answer_faithfulness
from scientific_network.rag.executor import execute_plan
from scientific_network.rag.llm import LLMResult
from scientific_network.rag.tools import InMemoryGraphBackend, RAGToolset


class _MockCfg:
    model = "mock-4b"


class _FakeLLM:
    def __init__(self, responses: list[dict | str]) -> None:
        self.responses = list(responses)
        self.calls: list[str] = []
        self.config = _MockCfg()

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


def _synth_toolset(tmp_path: Path) -> RAGToolset:
    graph = {
        "nodes": [
            {"id": "researcher:1", "label": "Researcher", "name": "Bo An", "properties": {}},
            {"id": "researcher:2", "label": "Researcher", "name": "Bo An", "properties": {}},
            {"id": "organization:tsinghua", "label": "Organization", "name": "Tsinghua University", "properties": {}},
            {"id": "organization:pku", "label": "Organization", "name": "Peking University", "properties": {}},
            {"id": "paper:aaai:2024:1", "label": "Paper", "name": "LLM Study", "properties": {"year": 2024}},
            {"id": "paper:aaai:2021:2", "label": "Paper", "name": "Old Study", "properties": {"year": 2021}},
            {"id": "method:llm", "label": "Method", "name": "Large Language Models (LLMs)", "properties": {"key": "language model", "paper_count": 1}},
        ],
        "edges": [
            {"edge_id": "e1", "relation": "COLLABORATED_WITH", "source_id": "organization:tsinghua", "target_id": "organization:pku", "evidence_ids": ["ev1"], "properties": {"support_count": 2}},
            {"edge_id": "e2", "relation": "AFFILIATED_WITH", "source_id": "researcher:1", "target_id": "organization:pku", "evidence_ids": ["ev2"], "properties": {}},
            {"edge_id": "e3", "relation": "AUTHORED", "source_id": "researcher:1", "target_id": "paper:aaai:2024:1", "evidence_ids": ["ev3"], "properties": {}},
            {"edge_id": "e4", "relation": "AUTHORED", "source_id": "researcher:1", "target_id": "paper:aaai:2021:2", "evidence_ids": ["ev4"], "properties": {}},
            {"edge_id": "e5", "relation": "USES_METHOD", "source_id": "paper:aaai:2024:1", "target_id": "method:llm", "evidence_ids": ["ev5"], "properties": {}},
        ],
    }
    return RAGToolset(InMemoryGraphBackend(graph), analysis_dir=tmp_path, rag_dir=tmp_path)


def test_disambiguation_halts_for_same_name_researcher(tmp_path: Path):
    ts = _synth_toolset(tmp_path)
    llm = _FakeLLM([{"entities": [{"text": "Bo An", "entity_type": "Researcher"}], "intent": "lookup"}])
    res = run_ask("Which papers did Bo An write?", toolset=ts, llm=llm)
    assert res["status"] == "needs_disambiguation"
    assert len(res["disambiguation"][0]["candidates"]) == 2


def test_empty_step_stops_execution_without_guessing(tmp_path: Path):
    ts = _synth_toolset(tmp_path)
    steps = [
        {"tool": "find", "args": {"entity_type": "Organization", "text": "Nonexistent University"}},
        {"tool": "neighbors", "args": {"node_id": "$step1.first_id"}},
    ]
    out = execute_plan(steps, ts)
    assert out["stopped_reason"] == "empty_step"
    assert out["stopped_at_step"] == 1
    assert len(out["steps"]) == 1  # second step never executed


def test_faithfulness_verifier_rejects_retry_and_fallback():
    trace = {"rows": [{"entity": "Peking University", "post_gt_2022_share": 1.0, "paper_id": "paper:aaai:2024:1"}]}
    assert verify_answer_faithfulness("Peking University reached 1.0 share [paper:aaai:2024:1].", trace, "Q") == []
    errs = verify_answer_faithfulness("Peking University reached 99% [paper:aaai:2024:999].", trace, "Q")
    assert len(errs) == 2

    llm = _FakeLLM(["Hallucinated 42 papers.", "Still hallucinated 77 papers."])
    res = compose_grounded_answer("How many?", trace, llm)
    assert res["faithfulness_passed"] is False
    assert "Could not compose a faithful answer" in res["answer"]


def test_worked_example_multihop_end_to_end(tmp_path: Path):
    ts = _synth_toolset(tmp_path)
    llm = _FakeLLM([
        {"entities": [{"text": "Tsinghua University", "entity_type": "Organization"}, {"text": "large language model", "entity_type": "Method"}], "after_year": 2022, "intent": "lookup"},
        {"steps": [
            {"tool": "neighbors", "args": {"node_id": "organization:tsinghua", "predicates": ["COLLABORATED_WITH"], "filters": {"target_labels": ["Organization"]}}},
            {"tool": "aggregate", "args": {"entity_ids": "$step1.ids", "by": "organization_year", "metric": "share_growth", "filters": {"method_id": "method:llm", "after_year": 2022, "only_increased": True}}},
        ]},
        "Peking University increased its share of LLM papers after 2022 to 1.0 [paper:aaai:2024:1].",
    ])
    res = run_ask(
        "Which organizations collaborating with Tsinghua University increased their share of large language model papers after 2022?",
        toolset=ts,
        llm=llm,
    )
    assert res["status"] == "ok" and res["mode"] == "multi_hop" and res["faithfulness_passed"]
    assert len(res["steps"]) == 2
    assert res["subgraph_nodes"] and res["subgraph_nodes"][0]["hop"] == 1
