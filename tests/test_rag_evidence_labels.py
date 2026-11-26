from scientific_network.rag.answer import (
    _ANSWER_SYS_V4,
    CURRENT_ANSWER_PROMPT,
    check_step_references,
    chunk_paper_ids,
    label_answer_evidence,
    verify_answer_faithfulness,
)

P1 = "paper:aaai:2024:111"
P2 = "paper:ijcai:2023:222"
P3 = "paper:aaai:2022:333"


def _cooccurrence_steps():
    return [
        {
            "step": 1,
            "tool": "neighbors",
            "rows": [
                {"neighbor_id": "task:abc", "neighbor_name": "Image generation", "support_count": 40, "paper_ids": [P1, P2]},
            ],
            "paper_ids": [P1, P2],
        },
        {
            "step": 2,
            "tool": "papers",
            "rows": [{"id": P3, "name": "A diffusion paper", "year": 2022}],
            "paper_ids": [P3],
        },
    ]


def test_aggregate_paper_ids_move_to_step_reference():
    answer = f"Image generation co-occurs with diffusion models in 40 papers [{P1}, {P2}]."
    res = label_answer_evidence(answer, _cooccurrence_steps())
    assert P1 not in res["answer"] and P2 not in res["answer"]
    assert "[step 1]" in res["answer"]
    assert res["citations"] == []
    assert {m["paper_id"] for m in res["moved_inline_paper_ids"]} == {P1, P2}
    step1 = next(r for r in res["result_papers"] if r["step"] == 1)
    assert step1["paper_ids"] == [P1, P2]
    assert step1["role"] == "papers_in_result"


def test_paper_row_is_a_citation_for_its_sentence():
    answer = f"Image generation leads with 40 papers [{P1}]. One example is A diffusion paper from 2022 [{P3}]."
    res = label_answer_evidence(answer, _cooccurrence_steps())
    assert res["citations"] == [
        {"paper_id": P3, "step": 2, "sentence": f"One example is A diffusion paper from 2022 [{P3}]."}
    ]
    assert "[step 1]" in res["answer"]


def test_mixed_bracket_keeps_direct_and_moves_aggregate():
    answer = f"Examples [{P3}, {P1}]."
    res = label_answer_evidence(answer, _cooccurrence_steps())
    assert f"[{P3}]" in res["answer"] and "[step 1]" in res["answer"]
    assert [c["paper_id"] for c in res["citations"]] == [P3]


def test_local_chunk_papers_are_direct():
    context = f"## Abstract sentence chunks\n- [{P1}] We propose a diffusion model for images.\n"
    assert chunk_paper_ids(context) == {P1}
    steps = [{"step": 1, "tool": "local_search", "rows": [{"section": "chunks"}], "paper_ids": [P1, P2]}]
    answer = f"One paper proposes a diffusion model for images [{P1}]. Others relate [{P2}]."
    res = label_answer_evidence(answer, steps, extra_direct={1: chunk_paper_ids(context)})
    assert [c["paper_id"] for c in res["citations"]] == [P1]
    assert P2 not in res["answer"]


def test_global_answer_has_no_citations():
    steps = [{"step": 1, "tool": "community_report", "rows": [{"claim": "x", "importance": 5, "paper_ids": [P1]}], "paper_ids": [P1]}]
    res = label_answer_evidence(f"Community A covers graph learning [{P1}].", steps)
    assert res["citations"] == []
    assert res["answer"] == "Community A covers graph learning [step 1]."


def test_rewritten_answer_still_passes_faithfulness():
    steps = _cooccurrence_steps()
    trace = {"steps": steps}
    answer = f"Image generation co-occurs with diffusion models in 40 papers [{P1}]."
    assert verify_answer_faithfulness(answer, trace, "Which tasks co-occur with diffusion models?") == []
    res = label_answer_evidence(answer, steps)
    assert verify_answer_faithfulness(res["answer"], trace, "Which tasks co-occur with diffusion models?") == []


def test_step_reference_must_exist():
    trace = {"steps": [{"step": 1}, {"step": 2}]}
    assert check_step_references("Counts come from [step 2].", trace) == []
    assert check_step_references("Counts come from [step 3].", trace) == ["step reference 3 not in trace"]
    assert check_step_references("See [steps 1, 2].", trace) == []


def test_answer_without_brackets_is_unchanged():
    res = label_answer_evidence("No matching records were found.", [])
    assert res["answer"] == "No matching records were found."
    assert res["citations"] == [] and res["result_papers"] == []


def test_v4_prompt_tells_model_to_point_aggregates_to_steps():
    assert "[step N]" in _ANSWER_SYS_V4
    assert "NEVER attach paper IDs to aggregate claims" in _ANSWER_SYS_V4


def test_current_prompt_is_summary_first_and_keeps_v4_evidence_rules():
    from scientific_network.rag.answer import (
        CURRENT_LOCAL_ANSWER_PROMPT,
        _ANSWER_SYS_V5,
        _ANSWER_SYSTEMS,
        _STEP_REF_PROMPTS,
    )

    assert CURRENT_ANSWER_PROMPT == "rag-answer-v5"
    assert CURRENT_LOCAL_ANSWER_PROMPT == "rag-local-answer-v4"
    assert _ANSWER_SYSTEMS["rag-answer-v5"] is _ANSWER_SYS_V5
    # Older versions stay registered so frozen benchmark runs remain reproducible.
    assert _ANSWER_SYSTEMS["rag-answer-v3"] is not _ANSWER_SYS_V5
    assert _ANSWER_SYSTEMS["rag-answer-v4"] is _ANSWER_SYS_V4
    assert "ONE plain sentence" in _ANSWER_SYS_V5
    assert "top 3 to 5 items" in _ANSWER_SYS_V5
    assert "The full ranking of K is in the table." in _ANSWER_SYS_V5
    assert "[step N]" in _ANSWER_SYS_V5
    assert "NEVER attach paper IDs to aggregate claims" in _ANSWER_SYS_V5
    assert {"rag-answer-v5", "rag-local-answer-v4"} <= _STEP_REF_PROMPTS


def test_local_v5_prompt_asks_for_no_step_references():
    from scientific_network.rag.answer import _ANSWER_SYSTEMS, _LOCAL_ANSWER_SYS_V5

    assert _ANSWER_SYSTEMS["rag-local-answer-v4"] is _LOCAL_ANSWER_SYS_V5
    assert "Do NOT write [step N] references" in _LOCAL_ANSWER_SYS_V5
    assert "ONE plain sentence" in _LOCAL_ANSWER_SYS_V5


def test_v5_percentage_wording_passes_faithfulness():
    trace = {
        "steps": [
            {
                "step": 2,
                "tool": "aggregate",
                "rows": [{"entity_name": "Shenzhen University", "post_papers": "5 of 140", "share_delta": 0.0357, "post_gt_2022_share": 0.0357}],
                "note": "threshold: post_total >= 10, post_subject >= 2",
            }
        ]
    }
    answer = (
        "Shenzhen University grew its share the most [step 2].\n"
        "- Shenzhen University: 5 of 140 papers after 2022, share 3.6%, share change +3.6 points"
    )
    assert verify_answer_faithfulness(answer, trace, "Which organizations increased their share after 2022?") == []


def test_list_head_with_colon_inside_parenthetical_names_the_entity():
    trace = {"steps": [{"step": 1, "tool": "rank", "rows": [{"name": "University of Lübeck", "lift": 22.1088}]}]}
    answer = "The organizations ranked by lift are [step 1]:\n1. University of Lübeck (lift: 22.1088)"
    assert verify_answer_faithfulness(answer, trace, "Which organizations specialize most in Causal inference by lift?") == []
    bad = "1. Invented Institute (lift: 22.1088)"
    assert verify_answer_faithfulness(bad, trace, "q") != []
