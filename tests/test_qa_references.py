"""Offline unit tests for deterministic QA benchmark reference computation (M3 Phase 1)."""

import json
from pathlib import Path

import pytest

from scientific_network.evaluation.qa_references import compute_references, resolve_slot_from_rows


class _FakeSession:
    def __init__(self, graph_version: str = "enriched-cb371912e308") -> None:
        self.graph_version = graph_version

    def execute_read(self, fn):
        class _FakeTx:
            def __init__(self, outer):
                self.outer = outer

            def run(self, query: str, **params):
                class _Res:
                    def __init__(self, rows):
                        self._rows = rows

                    def data(self):
                        return self._rows

                if "collect(DISTINCT m.graph_version)" in query:
                    return _Res([{"vs": [self.outer.graph_version]}])
                if "MATCH (n:Method)" in query:
                    return _Res([
                        {"id": "method:Q3621696", "name": "Large Language Models (LLMs)", "key": "language model",
                         "surfaces": '{"large language models": 13, "Large Language Model (LLM)": 13}', "paper_count": 136},
                        {"id": "method:1", "name": "Transformer", "key": "transformer", "surfaces": "{}", "paper_count": 200},
                    ])
                if "MATCH (n:Task)" in query:
                    return _Res([{"id": "task:1", "name": "image classification", "key": "image classification", "surfaces": "{}", "paper_count": 100}])
                if "MATCH (n:Dataset)" in query:
                    return _Res([{"id": "dataset:1", "name": "ImageNet", "key": "imagenet", "surfaces": "{}", "paper_count": 155}])
                if "MATCH (n:Organization)" in query:
                    return _Res([{"id": "organization:I1", "name": "Tsinghua University", "key": None, "surfaces": None, "paper_count": 485}])
                if "MATCH (n:Topic)" in query:
                    return _Res([{"id": "topic:cv", "name": "Computer vision", "key": None, "surfaces": None, "paper_count": 1000}])
                if "[:APPLIED_TO]->(t:Task)" in query:
                    if params.get("method_id") == "method:1":
                        return _Res([{"id": "task:1", "name": "image classification"}])
                    return _Res([])
                if "[:USES_METHOD]->(m:Method" in query and "count(DISTINCT p)" in query:
                    return _Res([{"count": 136}])
                return _Res([])

        return fn(_FakeTx(self))


def test_resolve_slot_handles_surfaces_and_plural():
    rows = [
        {"id": "method:Q3621696", "name": "Large Language Models (LLMs)", "key": "language model",
         "surfaces": '{"large language models": 13}', "paper_count": 136},
    ]
    hit = resolve_slot_from_rows(rows, "large language model")
    assert hit is not None and hit["id"] == "method:Q3621696"


def test_compute_references_drops_missing_and_empty_never_replaces(tmp_path: Path):
    q_path = tmp_path / "questions.jsonl"
    questions = [
        {"question_id": "q1", "split": "test", "hops": "1", "template_id": "T1a", "intent": "lookup",
         "judged": "set_f1", "answer_type": "set", "slots": {"method": "transformer"}, "text": "Which tasks is transformer applied to?"},
        {"question_id": "q2", "split": "test", "hops": "1", "template_id": "T1a", "intent": "lookup",
         "judged": "set_f1", "answer_type": "set", "slots": {"method": "large language model"}, "text": "Which tasks is large language model applied to?"},
        {"question_id": "q3", "split": "development", "hops": "1", "template_id": "T1c", "intent": "count",
         "judged": "exact", "answer_type": "number", "slots": {"method": "nonexistent method"}, "text": "How many papers use nonexistent method?"},
    ]
    q_path.write_text("".join(json.dumps(q) + "\n" for q in questions), encoding="utf-8")
    analysis_dir = tmp_path / "analysis"
    (analysis_dir / "trends").mkdir(parents=True)
    (analysis_dir / "trends" / "trends-summary.json").write_text('{"classification_note": "descriptive", "caveats": []}', encoding="utf-8")

    out_path = tmp_path / "references-v1.jsonl"
    rcp_path = tmp_path / "references-v1-receipt.json"
    receipt = compute_references(
        questions_path=q_path,
        analysis_dir=analysis_dir,
        output_path=out_path,
        receipt_path=rcp_path,
        min_kept_test=1,
        session_override=_FakeSession(),
    )
    assert receipt["kept_test"] == 1
    assert receipt["dropped_test"] == 1
    assert receipt["dropped_development"] == 1
    rows = [json.loads(l) for l in out_path.read_text().splitlines()]
    assert rows[0]["status"] == "kept" and rows[0]["reference_answer"] == [{"id": "task:1", "name": "image classification"}]
    assert rows[1]["status"] == "dropped" and rows[1]["drop_reason"] == "empty_reference_result"
    assert rows[2]["status"] == "dropped" and "missing_entity" in rows[2]["drop_reason"]
    assert "T1a" in receipt["query_hashes"]
