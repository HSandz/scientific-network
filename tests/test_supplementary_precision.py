from scientific_network.evaluation.supplementary_precision import extract_items, select_evidence

P1 = "paper:aaai:2023:25411"
P2 = "paper:ijcai:2023:121"


def test_bullets_give_items_with_line_citations():
    ans = f"Tasks:\n*   **Multi-Task Learning** [{P1}]\n*   **Low-Level Vision** (via pre-training) [{P2}]\n"
    items = extract_items(ans)
    assert [i["item_text"] for i in items] == ["Multi-Task Learning", "Low-Level Vision"]
    assert items[0]["cited_paper_ids"] == [P1]


def test_inline_list_after_colon():
    ans = "Transformer is applied to the following tasks: Time Series Forecasting, Crowd Counting, and Visual Tracking."
    assert [i["item_text"] for i in extract_items(ans)] == ["Time Series Forecasting", "Crowd Counting", "Visual Tracking"]


def test_abstention_with_paper_ids_and_quotes_gives_no_items():
    ans = (f"It is impossible to identify them. The excerpts mention PPO [{P1}], and [{P2}], but do not list authors. "
           f'The excerpt [{P1}] states: "We evaluate our method on MNIST and CIFAR10."')
    assert extract_items(ans) == []


def test_evidence_selection_rules():
    meta = {P1: {"title": "Crowd counting with transformers", "abstract": "We study crowd counting."},
            P2: {"title": "Other", "abstract": "Unrelated."}}
    it = {"item_text": "Crowd Counting", "cited_paper_ids": []}
    assert select_evidence(it, [P2, P1], meta) == ([P1], "shown_paper_mentions_item")
    assert select_evidence({"item_text": "Pose", "cited_paper_ids": [P2]}, [P1], meta) == ([P2], "cited_on_item_line")
    assert select_evidence({"item_text": "Tracking", "cited_paper_ids": []}, [P2], meta) == ([P2], "first_shown_papers_no_mention")
    assert select_evidence({"item_text": "Tracking", "cited_paper_ids": []}, [], meta) == ([], "no_paper_shown")
