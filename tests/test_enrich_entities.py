import numpy as np

from scientific_network.enrich.entities import (aggregate_entities, entity_id, merge_surfaces, paper_mentions,
                                                paper_relations)

TEXT = ("Graph contrastive learning for link prediction\n"
        "We propose GraphMix, a pre-training method for a graph neural network (GNN). GraphMix is evaluated on Cora and Citeseer.")


def encoded(entities, relations=()):
    return {"id": "p1", "entities": entities, "relations": list(relations)}


def ent(text, label, score, start=None):
    start = TEXT.find(text) if start is None else start
    return {"text": text, "label": label, "score": score, "start": start, "end": start + len(text)}


def slm(kept, dropped=(), relations=()):
    return {"valid": True, "entities": kept, "dropped": list(dropped), "relations": list(relations)}


def test_mentions_keep_dropped_spans_with_reasons_and_baseline_flag():
    enc = encoded([ent("GraphMix", "method", 0.95), ent("link prediction", "task", 0.5), ent("Cora", "dataset", 0.45)])
    verdict = slm([{"id": 2, "type": "Method", "text": "GraphMix", "retyped_from": None},
                   {"id": 3, "type": "Dataset", "text": "Cora", "retyped_from": None}],
                  dropped=[{"id": 1, "reason": "slm_drop", "text": "link prediction", "type": "Task"}])
    rows = paper_mentions("p1", TEXT, enc, verdict, entity_threshold=0.4, baseline_threshold=0.7, extractor="x", method_version="v")
    by = {r["text"]: r for r in rows}
    assert by["GraphMix"]["status"] == "kept" and by["GraphMix"]["in_encoder_baseline"] is True
    assert by["link prediction"]["status"] == "dropped" and by["link prediction"]["drop_reason"] == "slm_drop"
    assert by["Cora"]["status"] == "kept" and by["Cora"]["in_encoder_baseline"] is False
    assert by["GraphMix"]["sentence"] == 1 and by["link prediction"]["sentence"] == 0 and by["GraphMix"]["start"] == TEXT.find("GraphMix")


def test_mentions_expand_acronyms_and_never_treat_missing_verdict_as_kept():
    enc = encoded([ent("GNN", "method", 0.9, TEXT.find("GNN"))])
    rows = paper_mentions("p1", TEXT, enc, slm([]), entity_threshold=0.4, baseline_threshold=0.7, extractor="x", method_version="v")
    assert rows[0]["key"] == "graph neural network" and rows[0]["text"].lower() == "graph neural network"
    assert rows[0]["status"] == "dropped" and rows[0]["drop_reason"] == "no_decision"


def test_relations_resolve_to_kept_mentions_and_flag_sentence_agreement():
    enc = encoded([ent("GraphMix", "method", 0.95), ent("Cora", "dataset", 0.9)])
    verdict = slm([{"id": 1, "type": "Method", "text": "GraphMix", "retyped_from": None},
                   {"id": 2, "type": "Dataset", "text": "Cora", "retyped_from": None}],
                  relations=[{"head": "GraphMix", "relation": "EVALUATED_ON", "tail": "Cora"},
                             {"head": "GraphMix", "relation": "EVALUATED_ON", "tail": "Unknown"}])
    rows = paper_mentions("p1", TEXT, enc, verdict, entity_threshold=0.4, baseline_threshold=0.7, extractor="x", method_version="v")
    rels = paper_relations("p1", TEXT, verdict, rows)
    assert len(rels) == 1 and rels[0]["relation"] == "EVALUATED_ON" and rels[0]["same_sentence"] is False and rels[0]["head_sentence"] == 1 and rels[0]["tail_sentence"] == 2


def test_merge_only_same_type_and_shared_head_token():
    v = lambda *x: np.array(x, dtype=np.float32) / np.linalg.norm(x)
    vectors = {("Method", "graph neural network"): v(1, 0.05), ("Method", "graph neural networks model"): v(1, 0.06),
               ("Task", "graph neural network"): v(1, 0.05), ("Method", "transformer"): v(1, 0.05)}
    keys = {"Method": ["graph neural network", "graph neural networks model", "transformer"], "Task": ["graph neural network"]}
    merged = merge_surfaces(keys, vectors, threshold=0.99)
    assert merged == {}  # head tokens differ ("network" vs "model"; "transformer"), and types never mix
    vectors[("Method", "deep graph neural network")] = v(1, 0.04)
    keys["Method"].append("deep graph neural network")
    merged = merge_surfaces(keys, vectors, threshold=0.99)
    assert merged[("Method", "graph neural network")] == merged[("Method", "deep graph neural network")] == ("Method", "deep graph neural network")


def test_node_threshold_counts_distinct_papers_not_mentions():
    base = {"status": "kept", "type": "Method", "key": "diffusion model", "text": "Diffusion model"}
    mentions = [{**base, "paper_id": "a"}, {**base, "paper_id": "a"}, {**base, "paper_id": "b"},
                {**base, "paper_id": "c", "text": "diffusion models"},
                {"status": "kept", "type": "Task", "key": "rare task", "text": "rare task", "paper_id": "a"},
                {**base, "status": "dropped", "paper_id": "d"}]
    out = aggregate_entities(mentions, {}, min_papers=3)
    assert [n["name"] for n in out["nodes"]] == ["Diffusion model"] and out["nodes"][0]["paper_count"] == 3
    assert out["nodes"][0]["id"] == entity_id("Method", "diffusion model") and out["below_threshold"] == 1
    assert entity_id("Method", "x") != entity_id("Task", "x")


def test_finalize_merges_nodes_that_link_to_the_same_qid():
    from scientific_network.enrich.finalize import finalize_entities
    def m(paper, key):
        return {"status": "kept", "type": "Method", "key": key, "text": key, "paper_id": paper}
    mentions = [m("a", "transformer"), m("b", "transformer"), m("c", "transformer model"), m("d", "transformer model"),
                m("e", "transformer model"), m("f", "lonely")]
    pre = [{"id": "p1", "type": "Method", "keys": ["transformer"], "paper_count": 2},
           {"id": "p2", "type": "Method", "keys": ["transformer model"], "paper_count": 3}]
    links = {"p1": {"linked": True, "wikibase_item": "Q42", "wikipedia_title": "Transformer", "wikipedia_url": "u", "revision_id": 1, "link_score": 0.7},
             "p2": {"linked": True, "wikibase_item": "Q42", "wikipedia_title": "Transformer", "wikipedia_url": "u", "revision_id": 1, "link_score": 0.8}}
    out = finalize_entities(mentions, {}, pre, links, min_papers=3, enrichment_version="e1")
    assert [(n["id"], n["properties"]["paper_count"]) for n in out["nodes"]] == [("method:Q42", 5)]
    assert out["lookup"][("Method", "transformer")] == out["lookup"][("Method", "transformer model")] == "method:Q42"
    unlinked = finalize_entities(mentions, {}, pre, {}, min_papers=3, enrichment_version="e1")
    assert [n["properties"]["paper_count"] for n in unlinked["nodes"]] == [3] and not unlinked["nodes"][0]["properties"]["linked"]
