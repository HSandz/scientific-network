from pathlib import Path

import pytest

from scientific_network.evaluation.k1_answer import (
    _json_validity,
    _plan_json_validity,
    apply_decision_rule,
    load_config,
    load_dev_questions,
)


def _models(a4, ag, a9):
    def m(v):
        return {"by_hop": {"factual_overall": {"mean_score": v}}}
    return {"qwen3.5-4b": m(a4), "gemma-4-e4b": m(ag), "qwen3.5-9b": m(a9)}


def test_decision_rule_keeps_4b_without_margin():
    d = apply_decision_rule(_models(0.50, 0.45, 0.58))
    assert d["best_eligible_model"] == "qwen3.5-4b"
    assert d["reference_9b_gain_over_best_eligible"] == pytest.approx(0.08)
    assert d["reference_9b_meets_margin"] is False
    assert d["gemma_flag_for_user"] is False
    assert "stays the chosen model" in d["outcome"]


def test_decision_rule_compares_9b_with_best_eligible_not_only_4b():
    d = apply_decision_rule(_models(0.40, 0.55, 0.62))
    assert d["best_eligible_model"] == "gemma-4-e4b"
    assert d["reference_9b_meets_margin"] is False
    assert d["gemma_flag_for_user"] is True
    assert "team decision" in d["outcome"]


def test_decision_rule_flags_9b_margin():
    d = apply_decision_rule(_models(0.40, 0.30, 0.50))
    assert d["reference_9b_meets_margin"] is True


def test_json_validity_counts_first_pass_retry_and_fallback():
    rows = [
        {"llm_calls": [{"prompt_version": "rag-plan-v4", "attempts": 1, "error": None}]},
        {"llm_calls": [{"prompt_version": "rag-plan-v4", "attempts": 2, "error": None}]},
        {"llm_calls": [{"prompt_version": "rag-plan-v4", "attempts": 2, "error": "invalid JSON"},
                       {"prompt_version": "rag-plan-v4-retry", "attempts": 1, "error": None}]},
        {"llm_calls": [{"prompt_version": "rag-plan-v4", "attempts": 2, "error": "invalid JSON"},
                       {"prompt_version": "rag-plan-v4-retry", "attempts": 2, "error": "invalid JSON"}]},
        {"llm_calls": [{"prompt_version": "rag-global-v2", "attempts": 1, "error": None}]},
    ]
    res = _plan_json_validity(rows)
    assert res["questions_reaching_call"] == 4
    assert res["first_pass_valid"]["passed"] == 1
    assert res["valid_after_retries"]["passed"] == 3
    assert res["deterministic_fallback"] == 1
    assert res["rag_plan_v4_retry_used"] == 2
    assert _json_validity(rows, "rag-parse-v2", None)["questions_reaching_call"] == 0


def test_loader_refuses_test_split(tmp_path: Path):
    cfg = load_config(Path("configs/k1-answer-v1.yaml"))
    cfg["benchmark"] = {**cfg["benchmark"], "split": "test"}
    with pytest.raises(ValueError, match="development split only"):
        load_dev_questions(cfg)


def test_loader_returns_only_kept_development_questions():
    ref = Path("data/manifests/qa-benchmark-v1/references-v1.jsonl")
    if not ref.exists():
        pytest.skip("benchmark references not present")
    cfg = load_config(Path("configs/k1-answer-v1.yaml"))
    rows = load_dev_questions(cfg)
    assert len(rows) == 19
    assert {r["split"] for r in rows} == {"development"}
    assert {r["status"] for r in rows} == {"kept"}
