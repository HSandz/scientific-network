import json

from scientific_network.enrich.quality import (agreement, assign, draw, entity_items, final_verdict, precision, recall_scores,
                                               relation_precision, wilson)


def test_wilson_matches_reference_values_and_handles_empty():
    w = wilson(85, 100)
    assert (w["low"], w["high"]) == (0.7672, 0.9086) or abs(w["low"] - 0.7672) < 0.002
    assert wilson(0, 0)["estimate"] is None
    assert wilson(10, 10)["high"] == 1.0 and wilson(10, 10)["low"] > 0.69


def test_sampling_is_deterministic_and_assignment_overlaps_a_fifth():
    keys = [f"k{i}" for i in range(100)]
    assert draw(keys, 10, 1, "x") == draw(list(reversed(keys)), 10, 1, "x") and draw(keys, 10, 1, "x") != draw(keys, 10, 2, "x")
    a = assign(keys, 7)
    assert sum(len(v) == 2 for v in a.values()) == 20 and all(v in (["A"], ["B"], ["A", "B"]) for v in a.values())
    assert a == assign(list(reversed(keys)), 7)


def test_entity_items_merge_variants_and_cap_per_type():
    text = "Title\nWe use GraphMix on Cora for link prediction."
    texts = {"p": text}
    rows = [{"paper_id": "p", "type": "Method", "text": "GraphMix", "start": text.find("GraphMix")},
            {"paper_id": "p", "type": "Dataset", "text": "Cora", "start": text.find("Cora")}]
    items, sampled = entity_items({"default": rows, "encoder_only": rows[:1]}, texts, 1, 100)
    assert len(items) == 2 and sampled["encoder_only"]["Method"] == sampled["default"]["Method"] and sampled["encoder_only"]["Dataset"] == []
    assert all("score" not in json.dumps(i) and "confidence" not in json.dumps(i) for i in items.values())


def test_precision_excludes_unclear_and_prefers_channel_a_and_kappa_on_overlap():
    judged = {"1": {"A": {"verdict": "correct"}, "B": {"verdict": "correct"}}, "2": {"A": {"verdict": "incorrect"}, "B": {"verdict": "correct"}},
              "3": {"B": {"verdict": "unclear"}}, "4": {"A": {"verdict": "correct"}}}
    p = precision(["1", "2", "3", "4", "5"], judged)
    assert (p["k"], p["n"], p["unclear"], p["judged"], p["sampled"]) == (2, 3, 1, 4, 5)
    assert final_verdict(judged["2"])["verdict"] == "incorrect"
    ag = agreement({}, {"1": ["A", "B"], "2": ["A", "B"], "4": ["A"]}, judged)
    assert ag["overlap_items_judged_by_both"] == 2 and ag["observed_agreement"] == 0.5


def test_relation_precision_is_stratified_and_every_shown_paper_is_primary():
    items = {k: {"papers": [1, 2]} for k in ("r1", "r2", "r3", "r4")}
    judged = {"r1": {"A": {"verdict": "correct", "supported_in": 2}}, "r2": {"A": {"verdict": "correct", "supported_in": 1}},
              "r3": {"A": {"verdict": "incorrect", "supported_in": 0}}, "r4": {"A": {"verdict": "unclear"}}}
    sample = {"population": {"same_sentence": 10, "cross_sentence": 90}, "ids": {"same_sentence": ["r1", "r2"], "cross_sentence": ["r3", "r4"]}}
    out = relation_precision(sample, judged, items)
    same, cross = out["strata"]["same_sentence"], out["strata"]["cross_sentence"]
    assert same["every_shown_paper_supports"]["k"] == 1 and same["at_least_half_support"]["k"] == 2 and same["every_shown_paper_supports"]["n"] == 2
    assert cross["unclear"] == 1 and cross["every_shown_paper_supports"]["n"] == 1 and cross["sensitivity_unclear_as_incorrect"]["n"] == 2
    assert out["population_weighted_estimate"]["every_shown_paper_supports"] == 0.05  # 0.5 * 10/100 + 0.0 * 90/100


def test_adjudicator_c_decides_disagreements_and_sensitivity_counts_unclear():
    judged = {"1": {"A": {"verdict": "correct"}, "B": {"verdict": "incorrect"}, "C": {"verdict": "incorrect"}},
              "2": {"A": {"verdict": "correct"}, "B": {"verdict": "incorrect"}}, "3": {"A": {"verdict": "unclear"}}}
    assert final_verdict(judged["1"])["verdict"] == "incorrect" and final_verdict(judged["2"])["verdict"] == "correct"
    p = precision(["1", "2", "3"], judged)
    assert p["k"] == 1 and p["n"] == 2 and p["unclear"] == 1 and p["sensitivity_unclear_as_incorrect"]["n"] == 3


def test_recall_matches_by_type_and_lenient_overlap():
    listed = {"p": {"A": [{"text": "graph neural network", "type": "Method"}, {"text": "Cora", "type": "Dataset"}, {"text": "link prediction", "type": "Task"}]}}
    pools = {"default": [{"paper_id": "p", "type": "Method", "text": "graph neural networks"}, {"paper_id": "p", "type": "Task", "text": "Cora"}]}
    out = recall_scores(listed, pools)["default"]
    assert out["Method"]["k"] == 1 and out["Dataset"]["k"] == 0 and out["Task"]["k"] == 0 and out["all"]["n"] == 3
