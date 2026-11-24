import copy

from scientific_network.enrich.entities import entity_id
from scientific_network.enrich.graph5 import (build_enriched_graph, enriched_counts, split_layers, v4_layer_sha256,
                                              validate_enriched)
from scientific_network.enrich.relations import edge_id

BASE = {
    "schema_version": "0.1.0", "graph_version": "release-x", "is_synthetic": False,
    "nodes": [{"id": "paper:1", "label": "Paper", "name": "p1", "properties": {"is_core": True}},
              {"id": "paper:2", "label": "Paper", "name": "p2", "properties": {"is_core": True}},
              {"id": "paper:3", "label": "Paper", "name": "p3", "properties": {"is_core": True}},
              {"id": "organization:A", "label": "Organization", "name": "A", "properties": {}}],
    "edges": [{"edge_id": "edge:v4", "relation": "AUTHORED", "source_id": "r", "target_id": "paper:1", "evidence_kind": "observed",
               "evidence_ids": ["evidence:o"], "method_version": "m4", "graph_version": "release-x", "validation_status": "accepted",
               "properties": {}}],
    "evidence": [{"id": "evidence:o", "kind": "observed"}], "affiliation_observations": [],
}


def enrichment():
    method = {"id": f"method:Q1", "label": "Method", "name": "GNN", "properties": {"key": "gnn", "paper_count": 3, "linked": True, "wikidata_qid": "Q1"}}
    task_id = entity_id("Task", "link prediction")
    task = {"id": task_id, "label": "Task", "name": "link prediction", "properties": {"key": "link prediction", "paper_count": 3, "linked": False}}
    edges, evidence = [], []
    for paper in ("paper:1", "paper:2", "paper:3"):
        for target, rel in (("method:Q1", "USES_METHOD"), (task_id, "ADDRESSES_TASK")):
            ev = {"id": f"evidence:extracted:{paper}{target}", "kind": "extracted", "paper_id": paper}
            evidence.append(ev)
            edges.append({"edge_id": edge_id(rel, paper, target, "e1"), "relation": rel, "source_id": paper, "target_id": target,
                          "evidence_kind": "extracted", "evidence_ids": [ev["id"]], "method_version": "e1", "graph_version": "tmp",
                          "validation_status": "accepted", "properties": {"support_count": 1}})
    ev = [{"id": f"evidence:extracted:r{p}", "kind": "extracted", "paper_id": p} for p in ("paper:1", "paper:2")]
    evidence += ev
    edges.append({"edge_id": edge_id("APPLIED_TO", "method:Q1", task_id, "e1"), "relation": "APPLIED_TO", "source_id": "method:Q1",
                  "target_id": task_id, "evidence_kind": "extracted", "evidence_ids": [e["id"] for e in ev], "method_version": "e1",
                  "graph_version": "tmp", "validation_status": "accepted",
                  "properties": {"support_count": 2, "support_paper_ids": ["paper:1", "paper:2"]}})
    return {"nodes": [method, task], "edges": edges, "evidence": evidence, "node_enrichments": {"organization:A": {"wikidata_qid": "Q9"}}}


def build():
    return build_enriched_graph(copy.deepcopy(BASE), enrichment(), base_file_sha256="ff", enrichment_version="e1")


def test_valid_graph_has_no_errors_and_counts_layers_separately():
    graph = build()
    assert validate_enriched(graph) == []
    counts = enriched_counts(graph)
    assert counts["v4_layer"]["nodes"] == 4 and counts["enrichment_layer"]["nodes"] == 2
    assert counts["enrichment_layer"]["edges_by_evidence_kind"] == {"extracted": 7}
    assert counts["total"]["nodes"] == 6 and v4_layer_sha256(split_layers(graph)[0]) == graph["base_layer_sha256"]


def test_changing_a_v4_node_is_detected():
    graph = build()
    graph["nodes"][0]["name"] = "changed"
    assert any("v4 layer differs" in e for e in validate_enriched(graph))


def test_rules_endpoint_support_evidence_and_determinism():
    graph = build()
    applied = next(e for e in graph["edges"] if e["relation"] == "APPLIED_TO")
    applied["properties"]["support_count"] = 1
    uses = next(e for e in graph["edges"] if e["relation"] == "USES_METHOD")
    uses["target_id"] = entity_id("Task", "link prediction")
    graph["edges"][-2]["evidence_ids"] = ["evidence:missing"]
    errors = " | ".join(validate_enriched(graph))
    assert "support below 2" in errors and "not allowed" in errors and "not deterministic" in errors and "unresolved" in errors


def test_node_rules_threshold_linked_flag_and_id():
    graph = build()
    graph["nodes"][-2]["properties"]["paper_count"] = 2
    graph["nodes"][-1]["properties"]["linked"] = True
    errors = " | ".join(validate_enriched(graph))
    assert "fewer than 3" in errors and "linked flag and wikidata_qid disagree" in errors
