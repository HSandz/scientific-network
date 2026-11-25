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


def test_current_prompt_tells_model_to_point_aggregates_to_steps():
    assert CURRENT_ANSWER_PROMPT == "rag-answer-v4"
    assert "[step N]" in _ANSWER_SYS_V4
    assert "NEVER attach paper IDs to aggregate claims" in _ANSWER_SYS_V4


def test_list_head_with_colon_inside_parenthetical_names_the_entity():
    trace = {"steps": [{"step": 1, "tool": "rank", "rows": [{"name": "University of Lübeck", "lift": 22.1088}]}]}
    answer = "The organizations ranked by lift are [step 1]:\n1. University of Lübeck (lift: 22.1088)"
    assert verify_answer_faithfulness(answer, trace, "Which organizations specialize most in Causal inference by lift?") == []
    bad = "1. Invented Institute (lift: 22.1088)"
    assert verify_answer_faithfulness(bad, trace, "q") != []
