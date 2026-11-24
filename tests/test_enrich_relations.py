from scientific_network.enrich.relations import (edge_id, entity_relation_edges, paper_entity_edges, part_of_edges,
                                                 related_to_edges)

M = dict(extractor="x", retyped_from=None, in_encoder_baseline=True, n_mentions=1, confidence=0.9, sentence=1, start=3, end=9)
TEXTS = {"p1": "t1", "p2": "t2", "p3": "t3"}


def mention(paper, typ, key, **kw):
    return {**M, "paper_id": paper, "type": typ, "key": key, "text": key, "status": "kept", **kw}


def test_paper_edges_one_per_paper_entity_and_deterministic():
    mentions = [mention("p1", "Method", "gnn"), mention("p1", "Method", "graph neural network", confidence=0.95),
                mention("p1", "Task", "link prediction"), mention("p1", "Method", "rare"),
                mention("p2", "Method", "gnn", status="dropped")]
    lookup = {("Method", "gnn"): "method:A", ("Method", "graph neural network"): "method:A", ("Task", "link prediction"): "task:B"}
    edges, ev = paper_entity_edges(mentions, lookup, TEXTS, method_version="m", graph_version="g")
    assert sorted((e["relation"], e["target_id"]) for e in edges) == [("ADDRESSES_TASK", "task:B"), ("USES_METHOD", "method:A")]
    assert all(e["evidence_ids"] and e["graph_version"] == "g" for e in edges) and len(ev) == 2
    again, _ = paper_entity_edges(mentions, lookup, TEXTS, method_version="m", graph_version="g")
    assert [e["edge_id"] for e in again] == [e["edge_id"] for e in edges]
    assert edge_id("USES_METHOD", "p1", "method:A", "m") in {e["edge_id"] for e in edges}


def rel(paper, relation, ht, hk, tt, tk, same=True):
    return {"paper_id": paper, "relation": relation, "head_type": ht, "head_key": hk, "tail_type": tt, "tail_key": tk,
            "head_sentence": 1, "tail_sentence": 1 if same else 2, "same_sentence": same}


def test_entity_relations_need_two_distinct_papers_and_ignore_repeats():
    lookup = {("Method", "gnn"): "m:A", ("Task", "link prediction"): "t:B", ("Dataset", "cora"): "d:C"}
    mentions = [mention(p, t, k) for p in ("p1", "p2") for t, k in (("Method", "gnn"), ("Task", "link prediction"), ("Dataset", "cora"))]
    rels = [rel("p1", "APPLIED_TO", "Method", "gnn", "Task", "link prediction"),
            rel("p1", "APPLIED_TO", "Method", "gnn", "Task", "link prediction"),  # repeated in the same paper
            rel("p2", "APPLIED_TO", "Method", "gnn", "Task", "link prediction", same=False),
            rel("p1", "EVALUATED_ON", "Method", "gnn", "Dataset", "cora")]
    edges, ev, stats = entity_relation_edges(rels, lookup, mentions, TEXTS, min_papers={"APPLIED_TO": 2, "EVALUATED_ON": 2},
                                             method_version="m", graph_version="g")
    assert [(e["relation"], e["properties"]["support_count"]) for e in edges] == [("APPLIED_TO", 2)]
    assert edges[0]["properties"]["same_sentence_papers"] == 1 and len(ev) == 2 and stats["pairs_below_threshold"] == 1


def test_part_of_uses_v4_and_parent_only_nodes_and_skips_self():
    matches = {"organization:1": {"qid": "Q1", "parents": [{"qid": "Q2", "property": "P749"}, {"qid": "Q9", "property": "P361"}]},
               "organization:2": {"qid": "Q2", "parents": [{"qid": "Q2", "property": "P749"}]}}
    parents = {"Q9": {"id": "organization:wikidata:Q9"}}
    edges, ev = part_of_edges(matches, {"organization:1", "organization:2"}, parents, {"sha256": "ab", "retrieved_at": "t"},
                              method_version="m", graph_version="g")
    assert sorted((e["source_id"], e["target_id"]) for e in edges) == [("organization:1", "organization:2"),
                                                                       ("organization:1", "organization:wikidata:Q9")]
    assert all(e["evidence_kind"] == "wikidata" for e in edges) and len(ev) == 2


def test_related_to_requires_wikipedia_link_and_three_papers_with_canonical_orientation():
    linked = {"m:B": "Beta", "m:A": "Alpha", "t:C": "Gamma"}
    links = {"Beta": {"Alpha", "Other"}, "Alpha": set(), "Gamma": {"Alpha"}}
    papers = {"p1": {"m:A", "m:B"}, "p2": {"m:A", "m:B", "t:C"}, "p3": {"m:A", "m:B"}, "p4": {"m:A", "t:C"}}
    edges, ev, stats = related_to_edges(linked, links, papers, min_papers=3, method_version="m", graph_version="g")
    assert [(e["source_id"], e["target_id"], e["properties"]["support_count"]) for e in edges] == [("m:A", "m:B", 3)]
    assert edges[0]["properties"]["wikipedia_link"] == ["b_links_a"] and stats["linked_pairs_with_wikipedia_link"] == 2
