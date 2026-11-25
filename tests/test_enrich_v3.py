"""Enrichment v3: PART_OF adoption, one-of PART_OF/MEMBER_OF, integrity checks and the offline link-guard stage (synthetic fixtures)."""

import copy
import json

import pytest

from scientific_network.enrich.e3 import run_guard_links
from scientific_network.enrich.graph5 import SCHEMA_VERSION_V3, build_enriched_graph, validate_enriched
from scientific_network.enrich.k1 import write_jsonl
from scientific_network.enrich.part_of_rule import apply_rule, check_integrity, kept_part_of
from scientific_network.enrich.relations import edge_id
from scientific_network.enrich.v3 import applied_to_candidates
from test_enrich_graph5 import BASE, enrichment
from test_enrich_v2 import RULE, facts, stmt

RULE_V3 = {**RULE, "id": "part_of_v2"}


def org_edge(relation, child, parent, evidence_ids, prop="P749"):
    return {"edge_id": edge_id(relation, f"organization:{child}", f"organization:wikidata:{parent}", "e1"), "relation": relation,
            "source_id": "organization:A", "target_id": f"organization:wikidata:{parent}", "evidence_kind": "wikidata", "evidence_ids": evidence_ids,
            "method_version": "e1", "graph_version": "tmp", "validation_status": "accepted", "properties": {"wikidata_property": prop}}


def org_ev(ev_id, child, parent, prop="P749", rule=None):
    return {"id": ev_id, "kind": "wikidata", "wikidata_item": child, "parent_item": parent, "property": prop, **({"rule": rule} if rule else {})}


FACTS = facts(types={"Q_a": {"ORG": "organization"}, "Q_org": {"ORG": "organization"}, "Q_sp": {"INDEX": "stock market index"},
                     "Q_con": {"CONSORTIUM": "consortium", "ORG": "organization"}},
              statements={"Q_a": [stmt("P749", "Q_org"), stmt("P749", "Q_sp"), stmt("P749", "Q_con")]})


def test_part_of_rule_adopted_keeps_one_edge_per_pair_and_all_its_evidence_and_counts_the_dropped():
    part = [org_edge("PART_OF", "A", "Q_org", ["e_org", "e_org2"]), org_edge("PART_OF", "A", "Q_sp", ["e_sp"]), org_edge("PART_OF", "A", "Q_con", ["e_con"])]
    ev = {"e_org": org_ev("e_org", "Q_a", "Q_org"), "e_org2": org_ev("e_org2", "Q_a", "Q_org", "P361"),
          "e_sp": org_ev("e_sp", "Q_a", "Q_sp"), "e_con": org_ev("e_con", "Q_a", "Q_con")}
    decisions = apply_rule(part, ev, FACTS, RULE_V3)
    assert decisions["kept"] == 1 and decisions["member_of"] == 1 and decisions["dropped"] == 1
    edges, evidence, dropped = kept_part_of(part, ev, decisions["decisions"], FACTS, "part_of_v2")
    assert [e["target_id"] for e in edges] == ["organization:wikidata:Q_org"]
    assert sorted(e["id"] for e in evidence) == ["e_org", "e_org2"]       # every evidence record of a kept edge, not only the first
    assert all(e["rule"] == "part_of_v2" for e in evidence)
    assert dict(dropped) == {"excluded_class": 1}                         # the index target is dropped, the consortium is not counted as dropped


def v3_graph(*edges_and_evidence):
    data = enrichment()
    for parent in ("Q_org", "Q_sp", "Q_con"):
        data["nodes"].append({"id": f"organization:wikidata:{parent}", "label": "Organization", "name": parent,
                              "properties": {"source": "wikidata_parent", "is_core": False}})
    for edge, ev in edges_and_evidence:
        data["edges"].append(edge)
        data["evidence"].extend(ev)
    return build_enriched_graph(copy.deepcopy(BASE), data, base_file_sha256="ff", enrichment_version="e1", schema_version=SCHEMA_VERSION_V3)


def test_integrity_check_flags_part_of_to_an_excluded_class_and_a_pair_the_rule_would_move():
    good = v3_graph((org_edge("PART_OF", "A", "Q_org", ["e1"]), [org_ev("e1", "Q_a", "Q_org", rule="part_of_v2")]),
                    (org_edge("MEMBER_OF", "A", "Q_con", ["e2"]), [org_ev("e2", "Q_a", "Q_con", rule="part_of_v2:consortium_or_association")]))
    assert validate_enriched(good) == [] and check_integrity(good, FACTS, RULE_V3) == []
    index = v3_graph((org_edge("PART_OF", "A", "Q_sp", ["e1"]), [org_ev("e1", "Q_a", "Q_sp", rule="part_of_v2")]))
    assert any("excluded class" in e for e in check_integrity(index, FACTS, RULE_V3))
    consortium_as_part = v3_graph((org_edge("PART_OF", "A", "Q_con", ["e1"]), [org_ev("e1", "Q_a", "Q_con", rule="part_of_v2")]))
    assert any("the rule gives member_of" in e for e in check_integrity(consortium_as_part, FACTS, RULE_V3))


def test_v3_validator_requires_one_of_part_of_and_member_of_per_pair_and_the_rule_marker():
    both = v3_graph((org_edge("PART_OF", "A", "Q_con", ["e1"]), [org_ev("e1", "Q_a", "Q_con", rule="part_of_v2")]),
                    (org_edge("MEMBER_OF", "A", "Q_con", ["e2"]), [org_ev("e2", "Q_a", "Q_con", rule="part_of_v2:consortium_or_association")]))
    assert any("carries both PART_OF and MEMBER_OF" in e for e in validate_enriched(both))
    unmarked = v3_graph((org_edge("PART_OF", "A", "Q_org", ["e1"]), [org_ev("e1", "Q_a", "Q_org")]))
    assert any("without the part_of_v2 rule marker" in e for e in validate_enriched(unmarked))
    # the same pair under the v2 schema is allowed to carry both (v2 kept the v1 PART_OF edges)
    v2 = copy.deepcopy(both)
    v2["schema_version"] = "0.3.0-enrichment"
    assert not any("carries both" in e for e in validate_enriched(v2))


def link(name, title, item="Q1", score=0.9):
    return {"id": f"task:{name}", "name": name, "candidates": [{"wikibase_item": item, "excluded": False, "name_in_page": True, "title_match": True,
                                                                 "score": score, "title": title, "url": "u", "revision_id": 1}]}


def test_guard_links_stage_is_offline_removes_only_narrower_pages_and_restricts_the_page_cache(tmp_path):
    src, out = tmp_path / "v1", tmp_path / "v3"
    src.mkdir()
    all_links = [link("game theory", "Combinatorial game theory", "Q1"), link("batch normalization", "Batch normalization", "Q2"),
                 link("odd one", "Odd one", "Q3", score=0.1)]
    write_jsonl(src / "links-all.jsonl", all_links)
    from scientific_network.enrich.link import apply_threshold
    write_jsonl(src / "links.jsonl", apply_threshold(all_links, threshold=0.4))
    (src / "page-links.json").write_text(json.dumps({"Combinatorial game theory": ["x"], "Batch normalization": ["y"]}))
    report = run_guard_links(src, out, threshold=0.4, reject_narrower_page=True)
    assert (report["linked_before"], report["linked_after"]) == (2, 1)
    assert [l["name"] for l in report["lost"]] == ["game theory"] and report["gained_unexpectedly"] == []
    assert json.loads((out / "page-links.json").read_text()) == {"Batch normalization": ["y"]}
    off = run_guard_links(src, tmp_path / "off", threshold=0.4, reject_narrower_page=False)
    assert off["identical_to_input_links"] is True and off["lost"] == []       # guard off reproduces the input links exactly
    (src / "page-links.json").write_text(json.dumps({"Batch normalization": ["y"]}))
    with pytest.raises(ValueError, match="not in the cached page-links"):       # a page that is not cached would need a fetch: refuse
        run_guard_links(src, tmp_path / "off2", threshold=0.4, reject_narrower_page=False)


def test_applied_to_candidates_are_only_single_paper_same_sentence_edges():
    graph = {"nodes": [{"id": "m", "name": "M"}, {"id": "t", "name": "T"}],
             "evidence": [{"id": "ev1", "paper_id": "paper:1"}],
             "edges": [{"edge_id": "e1", "relation": "APPLIED_TO", "source_id": "m", "target_id": "t", "evidence_ids": ["ev1"],
                        "properties": {"support_rule": "single_paper_same_sentence"}},
                       {"edge_id": "e2", "relation": "APPLIED_TO", "source_id": "m", "target_id": "t", "evidence_ids": ["ev1"],
                        "properties": {"support_rule": "two_or_more_papers"}},
                       {"edge_id": "e3", "relation": "EVALUATED_ON", "source_id": "m", "target_id": "t", "evidence_ids": ["ev1"],
                        "properties": {"support_rule": "single_paper_same_sentence"}}]}
    assert [c["edge_id"] for c in applied_to_candidates(graph)] == ["e1"]
