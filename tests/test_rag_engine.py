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


def test_faithfulness_verifier_placeholders_entities_and_tolerance():
    trace = {
        "steps": [{
            "step": 1,
            "tool": "aggregate",
            "rows": [
                {
                    "entity_id": "organization:cuhk",
                    "entity_name": "Chinese University of Hong Kong",
                    "pre_papers": "0 of 73",
                    "post_papers": "7 of 169",
                    "post_gt_2022_share": 0.0414,
                    "paper_ids": ["paper:aaai:2024:29823"],
                }
            ],
        }]
    }
    q = "Which organizations collaborating with Tsinghua University increased LLM share after 2022?"

    # 1. Placeholder / truncated citations rejected
    ph_errs = verify_answer_faithfulness(
        "* **Chinese University of Hong Kong**: 7 of 169 papers, share 0.0414 [paper:...].",
        trace,
        q,
    )
    assert any("placeholder" in e for e in ph_errs)
    assert any("placeholder" in e for e in verify_answer_faithfulness("See [...] and [paper:aaai:...].", trace, q))

    # 2. Invented organization rejected
    org_errs = verify_answer_faithfulness(
        "* **Mythical Quantum Institute**: share increased to 0.0414 [paper:aaai:2024:29823].",
        trace,
        q,
    )
    assert any("Mythical Quantum Institute" in e for e in org_errs)

    # 3. Correct grounded answer with real entity, real paper ID, and percentage within tolerance passes
    ok_errs = verify_answer_faithfulness(
        "* **Chinese University of Hong Kong**: 7 of 169 papers after 2022 (4.14% share) [paper:aaai:2024:29823].",
        trace,
        q,
    )
    assert ok_errs == []

    # 4. Number outside tolerance rejected
    num_errs = verify_answer_faithfulness(
        "* **Chinese University of Hong Kong**: 99 papers [paper:aaai:2024:29823].",
        trace,
        q,
    )
    assert any("99" in e for e in num_errs)

    # 5. Trailing period after paper ID or newline after entity does not cause false failures
    nl_errs = verify_answer_faithfulness(
        "Chinese University of Hong Kong\n\nSummary: see paper:aaai:2024:29823.",
        trace,
        q,
    )
    assert nl_errs == []

    # 6. Conjoined datasets ("X and Y") accepted only when both parts exist in trace
    ds_trace = {"steps": [{"step": 1, "tool": "rank", "rows": [{"name": "Camelyon16"}, {"name": "TCGA-NSCLC"}]}]}
    assert verify_answer_faithfulness("Evaluated on Camelyon16 and TCGA-NSCLC.", ds_trace, "Datasets?") == []
    fake_ds = verify_answer_faithfulness("Evaluated on Camelyon16 and FakeDataset.", ds_trace, "Datasets?")
    assert any("FakeDataset" in e for e in fake_ds)


def test_compact_trace_for_prompt_preserves_final_step_within_budget():
    from scientific_network.rag.answer import _compact_trace_for_prompt

    verbose_step1_rows = [
        {
            "id": f"organization:{i}",
            "name": f"University {i} " + ("X" * 80),
            "edge_id": f"e:{i}",
            "source_id": "organization:tsinghua",
            "target_id": f"organization:{i}",
            "evidence_ids": [f"ev:{i}:{j}" for j in range(15)],
            "support_paper_ids": [f"paper:aaai:2024:{1000 + j}" for j in range(10)],
            "fractional_weight": 0.5,
            "evidence_kind": "observed",
        }
        for i in range(15)
    ]
    step2_rows = [
        {"entity_id": f"organization:{i}", "entity_name": f"Collaborator {i}", "post_papers": f"{i + 2} of 20", "post_gt_2022_share": 0.1 + 0.01 * i}
        for i in range(15)
    ]
    compacted = _compact_trace_for_prompt(
        {"steps": [
            {"step": 1, "tool": "neighbors", "row_count": 150, "rows": verbose_step1_rows, "paper_ids": [f"paper:aaai:2024:{i}" for i in range(25)]},
            {"step": 2, "tool": "aggregate", "row_count": 37, "rows": step2_rows, "paper_ids": [f"paper:aaai:2024:{200 + i}" for i in range(15)]},
        ]},
        max_rows=15,
        max_chars=5000,
    )
    serialized = json.dumps(compacted, ensure_ascii=False, separators=(",", ":"))
    assert len(serialized) <= 5000
    assert len(compacted["steps"][1]["rows"]) == 15
    assert "edge_id" not in compacted["steps"][0].get("rows", [{}])[0] if compacted["steps"][0]["rows"] else True


def test_worked_example_multihop_end_to_end(tmp_path: Path):
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
    ts = RAGToolset(InMemoryGraphBackend(graph), analysis_dir=tmp_path, rag_dir=tmp_path, min_post_total_papers=1, min_post_subject_papers=1)
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


def test_multikind_subject_linking_and_empty_step_retry(tmp_path: Path):
    from scientific_network.rag.planner import link_entities

    # Both a Method and a Task share the name "clustering", plus a Dataset; Task has more papers,
    # while Method has an organization-linked paper and Task has none (forcing empty-step retry).
    graph = {
        "nodes": [
            {"id": "organization:pku", "label": "Organization", "name": "Peking University", "properties": {}},
            {"id": "researcher:1", "label": "Researcher", "name": "Alice", "properties": {}},
            {"id": "paper:aaai:2024:1", "label": "Paper", "name": "Clustering Method Study", "properties": {"year": 2024}},
            {"id": "method:clust", "label": "Method", "name": "clustering", "properties": {"paper_count": 5}},
            {"id": "task:clust", "label": "Task", "name": "clustering", "properties": {"paper_count": 12}},
        ],
        "edges": [
            {"edge_id": "e1", "relation": "AUTHORED", "source_id": "researcher:1", "target_id": "paper:aaai:2024:1", "evidence_ids": ["ev1"], "properties": {}},
            {"edge_id": "e2", "relation": "AFFILIATED_WITH", "source_id": "researcher:1", "target_id": "organization:pku", "evidence_ids": ["ev2"], "properties": {}},
            {"edge_id": "e3", "relation": "USES_METHOD", "source_id": "paper:aaai:2024:1", "target_id": "method:clust", "evidence_ids": ["ev3"], "properties": {}},
        ],
    }
    ts = RAGToolset(InMemoryGraphBackend(graph), analysis_dir=tmp_path, rag_dir=tmp_path, graph_path=None)

    # 1. Unclear kind picks node with most papers (task:clust, 12) and exposes Method alternative
    parsed = {"entities": [{"text": "clustering", "entity_type": "Method"}], "intent": "ranking"}
    res_unclear = link_entities(parsed, ts, question="Which organizations specialize most in clustering?")
    lk = res_unclear["linked"][0]
    assert lk["id"] == "task:clust"
    assert lk["selection_reason"] == "most_papers"
    assert any(a["id"] == "method:clust" for a in lk["kind_choices"])

    # 2. Implied kind overrides paper count ("clustering method")
    res_implied = link_entities(parsed, ts, question="Which organizations work on the clustering method?")
    assert res_implied["linked"][0]["id"] == "method:clust"
    assert res_implied["linked"][0]["selection_reason"] == "implied_kind:Method"

    # 3. Empty step retries once with the next candidate (task:clust -> method:clust) and records in trace
    out = execute_plan(
        [{"tool": "papers", "args": {"filters": {"task_id": "task:clust"}}}],
        ts,
        linked=res_unclear["linked"],
    )
    assert out["stopped_reason"] is None
    assert out["steps"][0]["row_count"] == 1
    assert out["steps"][0]["retry"]["from_id"] == "task:clust"
    assert out["steps"][0]["retry"]["to_id"] == "method:clust"
    assert out["steps"][0]["retry"]["succeeded"] is True
    assert "retried once" in out["steps"][0]["note"].lower()
