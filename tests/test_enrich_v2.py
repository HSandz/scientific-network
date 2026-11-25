"""Enrichment v2 rules on synthetic fixtures (invented items, not project measurements)."""

import copy

from scientific_network.enrich.entities import entity_id
from scientific_network.enrich.graph5 import build_enriched_graph, validate_enriched, SCHEMA_VERSION_V2
from scientific_network.enrich.link import apply_threshold, narrower_page
from scientific_network.enrich.part_of_rule import apply_rule, judge_edge, member_of_edges
from scientific_network.enrich.relations import edge_id, entity_relation_edges
from test_enrich_graph5 import BASE, enrichment
from test_enrich_relations import TEXTS, mention, rel

RULE = {
    "superclass_depth": 2,
    "allowed_classes": {"ORG": "organization"},
    "excluded_classes": {"INDEX": "stock market index", "LIST": "list"},
    "consortium_classes_direct_instance_of_only": {"CONSORTIUM": "consortium"},
    "whole_organization_classes_via_closure": {"UNI": "university"},
    "subordinate_classes_direct_instance_of_only": {"FACULTY": "faculty"},
}


def facts(types=None, supers=None, statements=None):
    return {"types": types or {}, "superclasses": supers or {}, "statements": statements or {}, "class_labels": {}}


def stmt(prop, target, end=None, rank="normal"):
    return {"prop": prop, "target": target, "rank": rank, "start": None, "end": end}


def test_part_of_rule_drops_an_index_target_and_an_end_dated_statement():
    f = facts(types={"Q_firm": {"COMPANY": "company"}, "Q_sp": {"INDEX": "stock market index"}, "Q_old": {"ORG": "organization"}},
              supers={"COMPANY": {"ORG": "organization"}},
              statements={"Q_firm": [stmt("P361", "Q_sp")], "Q_child": [stmt("P749", "Q_old", end="2019-01-01T00:00:00Z")]})
    assert judge_edge("Q_firm", "Q_sp", f, RULE)["reason"] == "excluded_class"
    assert judge_edge("Q_child", "Q_old", f, RULE)["reason"] == "end_dated"
    assert judge_edge("Q_child", "Q_old", facts(statements={"Q_child": [stmt("P749", "Q_old", rank="deprecated")]}), RULE)["reason"] == "end_dated"


def test_part_of_rule_flags_reversed_direction_and_implausible_type_order():
    f = facts(types={"Q_uni": {"UNI": "university"}, "Q_fac": {"FACULTY": "faculty", "ORG": "organization"}, "Q_lab": {"ORG": "organization"}},
              statements={"Q_uni": [stmt("P749", "Q_fac")], "Q_fac": [stmt("P749", "Q_uni")]})
    # the faculty says it is part of the university, and the statement under test says the university is part of the faculty
    assert judge_edge("Q_uni", "Q_fac", f, RULE)["reason"] == "reversed_direction"
    only_order = facts(types=f["types"], statements={"Q_uni": [stmt("P749", "Q_fac")]})
    assert judge_edge("Q_uni", "Q_fac", only_order, RULE)["reason"] == "implausible_type_order"
    ok = facts(types=f["types"], statements={"Q_fac": [stmt("P749", "Q_uni")]})
    assert judge_edge("Q_fac", "Q_uni", {**ok, "types": {**ok["types"], "Q_uni": {"UNI": "university", "ORG": "organization"}}}, RULE)["decision"] == "keep"
    # the child lists the parent as its subsidiary: reversed as well
    sub = facts(types={"Q_a": {"ORG": "organization"}, "Q_b": {"ORG": "organization"}},
                statements={"Q_a": [stmt("P749", "Q_b"), stmt("P355", "Q_b")]})
    assert judge_edge("Q_a", "Q_b", sub, RULE)["reason"] == "reversed_direction"


def test_consortium_goes_to_member_of_by_direct_class_only_and_p749_is_preferred():
    f = facts(types={"Q_u": {"UNI": "university"}, "Q_c": {"CONSORTIUM": "consortium", "ORG": "organization"},
                     "Q_soc": {"SOC": "society"}}, supers={"SOC": {"CONSORTIUM": "consortium"}, "CONSORTIUM": {"ORG": "organization"}},
              statements={"Q_u": [stmt("P361", "Q_c"), stmt("P749", "Q_c"), stmt("P361", "Q_soc")]})
    decision = judge_edge("Q_u", "Q_c", f, RULE)
    assert decision["decision"] == "member_of" and decision["property"] == "P749"
    # Q_soc reaches "consortium" only through a superclass: not a direct instance, so it stays a PART_OF candidate (kept), never a member_of
    assert judge_edge("Q_u", "Q_soc", f, RULE)["decision"] == "keep"


def test_member_of_edges_carry_their_own_evidence_and_leave_part_of_alone():
    f = facts(types={"Q_u": {"UNI": "university"}, "Q_c": {"CONSORTIUM": "consortium", "ORG": "organization"}},
              statements={"Q_u": [stmt("P361", "Q_c")]})
    part = [{"edge_id": "edge:p", "relation": "PART_OF", "source_id": "organization:u", "target_id": "organization:wikidata:Q_c",
             "evidence_ids": ["e1"], "properties": {"wikidata_property": "P361", "parent_in_v4": False}}]
    ev = {"e1": {"id": "e1", "wikidata_item": "Q_u", "parent_item": "Q_c", "property": "P361"}}
    decisions = apply_rule(part, ev, f, RULE)
    assert decisions["counts"] == {"member_of:consortium_or_association": 1}
    edges, evidence = member_of_edges(part, ev, decisions["decisions"], f, {("Q_u", "Q_c", "P361"): {"raw_response_sha256": "ab", "retrieved_at": "t"}},
                                      "part_of_v2:consortium_or_association", method_version="m", graph_version="g")
    assert edges[0]["relation"] == "MEMBER_OF" and edges[0]["edge_id"] == edge_id("MEMBER_OF", "organization:u", "organization:wikidata:Q_c", "m")
    assert evidence[0]["raw_sha256"] == "ab" and evidence[0]["parent_instance_of"] == ["consortium", "organization"] and part[0]["relation"] == "PART_OF"


LOOKUP = {("Method", "gnn"): "m:A", ("Task", "link prediction"): "t:B", ("Dataset", "cora"): "d:C"}
MENTIONS = [mention(p, t, k) for p in ("p1", "p2", "p3") for t, k in (("Method", "gnn"), ("Task", "link prediction"), ("Dataset", "cora"))]


def test_single_paper_same_sentence_edge_is_marked_and_a_cross_sentence_pair_is_not_admitted():
    rels = [rel("p1", "EVALUATED_ON", "Method", "gnn", "Dataset", "cora", same=True),
            rel("p1", "APPLIED_TO", "Method", "gnn", "Task", "link prediction", same=True),
            rel("p2", "APPLIED_TO", "Method", "gnn", "Task", "link prediction", same=False)]
    thresholds = {"APPLIED_TO": 2, "EVALUATED_ON": 2}
    v1, _, _ = entity_relation_edges(rels, LOOKUP, MENTIONS, TEXTS, min_papers=thresholds, method_version="m", graph_version="g")
    assert [(e["relation"], e["properties"]["support_count"]) for e in v1] == [("APPLIED_TO", 2)] and "support_rule" not in v1[0]["properties"]
    v2, ev, stats = entity_relation_edges(rels, LOOKUP, MENTIONS, TEXTS, min_papers=thresholds, method_version="m", graph_version="g",
                                          single_paper_same_sentence=frozenset({"EVALUATED_ON"}))
    rules = {e["relation"]: e["properties"]["support_rule"] for e in v2}
    assert rules == {"APPLIED_TO": "two_or_more_papers", "EVALUATED_ON": "single_paper_same_sentence"}
    single = next(e for e in v2 if e["relation"] == "EVALUATED_ON")
    assert single["properties"]["support_count"] == 1 and stats["admitted_by_rule"] == {"APPLIED_TO:two_or_more_papers": 1, "EVALUATED_ON:single_paper_same_sentence": 1}
    cross_only = [rel("p1", "EVALUATED_ON", "Method", "gnn", "Dataset", "cora", same=False)]
    none, _, _ = entity_relation_edges(cross_only, LOOKUP, MENTIONS, TEXTS, min_papers=thresholds, method_version="m", graph_version="g",
                                       single_paper_same_sentence=frozenset({"EVALUATED_ON"}))
    assert none == []
    off, _, _ = entity_relation_edges(rels[:1], LOOKUP, MENTIONS, TEXTS, min_papers=thresholds, method_version="m", graph_version="g",
                                      single_paper_same_sentence=frozenset())
    assert off == []  # a relation the rule was not adopted for keeps the two-paper threshold


def test_validator_accepts_single_paper_same_sentence_only_with_same_sentence_evidence():
    data = enrichment()
    task_id = entity_id("Task", "link prediction")
    ev = {"id": "evidence:extracted:single", "kind": "extracted", "paper_id": "paper:1", "same_sentence": True}
    data["evidence"].append(ev)
    data["edges"].append({"edge_id": edge_id("EVALUATED_ON", "method:Q1", task_id, "e1"), "relation": "APPLIED_TO", "source_id": "method:Q1",
                          "target_id": task_id, "evidence_kind": "extracted", "evidence_ids": [ev["id"]], "method_version": "e1", "graph_version": "tmp",
                          "validation_status": "accepted", "properties": {"support_count": 1, "support_paper_ids": ["paper:1"], "support_rule": "single_paper_same_sentence"}})
    data["edges"][-1]["edge_id"] = edge_id("APPLIED_TO", "method:Q1", task_id, "e1x")  # unique id for a second edge between the same nodes
    data["edges"][-1]["method_version"] = "e1x"
    graph = build_enriched_graph(copy.deepcopy(BASE), data, base_file_sha256="ff", enrichment_version="e1", schema_version=SCHEMA_VERSION_V2)
    errors = " | ".join(validate_enriched(graph))
    assert "several method versions" in errors and "support below" not in errors and "not same-sentence" not in errors
    bad = copy.deepcopy(graph)
    next(e for e in bad["evidence"] if e["id"] == "evidence:extracted:single")["same_sentence"] = False
    assert "not same-sentence" in " | ".join(validate_enriched(bad))
    unknown = copy.deepcopy(graph)
    unknown["edges"][-1]["properties"]["support_rule"] = "made_up"
    assert "unknown support_rule" in " | ".join(validate_enriched(unknown))


def test_validator_knows_member_of_endpoints():
    data = enrichment()
    data["nodes"].append({"id": "organization:wikidata:Q5", "label": "Organization", "name": "Consortium", "properties": {"source": "wikidata_parent", "is_core": False}})
    ev = {"id": "evidence:wikidata:m", "kind": "wikidata"}
    data["evidence"].append(ev)
    data["edges"].append({"edge_id": edge_id("MEMBER_OF", "organization:A", "organization:wikidata:Q5", "e1"), "relation": "MEMBER_OF",
                          "source_id": "organization:A", "target_id": "organization:wikidata:Q5", "evidence_kind": "wikidata", "evidence_ids": [ev["id"]],
                          "method_version": "e1", "graph_version": "tmp", "validation_status": "accepted", "properties": {"wikidata_property": "P361"}})
    graph = build_enriched_graph(copy.deepcopy(BASE), data, base_file_sha256="ff", enrichment_version="e1", schema_version=SCHEMA_VERSION_V2)
    assert validate_enriched(graph) == []
    wrong = copy.deepcopy(graph)
    wrong["edges"][-1]["source_id"] = "paper:1"
    assert "MEMBER_OF endpoints" in " | ".join(validate_enriched(wrong))


def test_link_guard_rejects_a_page_narrower_than_the_entity_but_not_equal_or_broader_pages():
    assert narrower_page("reinforcement learning", "Reinforcement learning from human feedback")
    assert narrower_page("game theory", "Combinatorial game theory") and narrower_page("captioning", "Closed captioning")
    assert not narrower_page("batch normalization", "Batch normalization")           # same tokens
    assert not narrower_page("attention", "Attention (machine learning)")            # parenthetical removed
    assert not narrower_page("Large Language Models (LLMs)", "Language model")       # a broader page is not caught by this guard
    assert not narrower_page("PCA", "Principal component analysis")                   # an acronym is not a token subset
    candidate = {"wikibase_item": "Q1", "excluded": False, "name_in_page": True, "title_match": True, "score": 0.9, "title": "Combinatorial game theory",
                 "url": "u", "revision_id": 1}
    links = [{"id": "e1", "name": "game theory", "candidates": [candidate]}]
    assert apply_threshold(links, threshold=0.4)[0]["linked"] is True
    guarded = apply_threshold(links, threshold=0.4, reject_narrower_page=True)[0]
    assert guarded["linked"] is False and guarded["wikibase_item"] is None and guarded["rejected_narrower_page"] == "Combinatorial game theory"
