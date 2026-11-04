import pytest
from pydantic import ValidationError

from scientific_network.contracts import GraphArtifact, Relation
from scientific_network.graph.schema import edge_id
from scientific_network.graph.validate import graph_counts, validate_graph


def test_invented_example_covers_ten_predicates_without_claiming_release(graph):
    assert graph.is_synthetic
    assert {edge.relation for edge in graph.edges} == set(Relation)
    assert validate_graph(graph) == []
    assert graph_counts(graph)["resolved_core_researchers"] == 5
    assert graph_counts(graph)["unique_core_factual_edges"] == 16


def test_missing_paper_specific_observations_block_affiliation_edges(graph_payload):
    graph_payload["affiliation_observations"] = []
    errors = validate_graph(GraphArtifact.model_validate(graph_payload))
    assert any("no author-paper-organization observation" in error for error in errors)


def test_duplicate_source_confirmations_do_not_create_another_semantic_edge(graph_payload):
    graph_payload["edges"].append(dict(graph_payload["edges"][0]))
    errors = validate_graph(GraphArtifact.model_validate(graph_payload))
    assert any("duplicate semantic edge" in error for error in errors)


def test_reverse_social_edge_is_rejected_even_with_canonical_hash(graph_payload):
    edge = next(e for e in graph_payload["edges"] if e["relation"] == "COAUTHORED_WITH")
    edge["source_id"], edge["target_id"] = edge["target_id"], edge["source_id"]
    errors = validate_graph(GraphArtifact.model_validate(graph_payload))
    assert any("canonical ID order" in error for error in errors)


def test_accepted_authorship_cannot_point_to_unresolved_name_placeholder(graph_payload):
    person = next(n for n in graph_payload["nodes"] if n["label"] == "Researcher")
    person["properties"]["resolution_status"] = "unresolved"
    errors = validate_graph(GraphArtifact.model_validate(graph_payload))
    assert any("requires a resolved researcher" in error for error in errors)


def test_derived_evidence_cannot_reference_missing_edges(graph_payload):
    item = next(e for e in graph_payload["evidence"] if e["kind"] == "derived")
    item["support_edge_ids"] = ["edge:missing"]
    errors = validate_graph(GraphArtifact.model_validate(graph_payload))
    assert any("support must resolve" in error for error in errors)


def test_source_evidence_without_locator_is_not_accepted(graph_payload):
    graph_payload["evidence"][0]["source_locator"] = None
    with pytest.raises(ValidationError, match="source evidence requires"):
        GraphArtifact.model_validate(graph_payload)


def test_context_papers_cannot_inflate_core_counts(graph_payload):
    paper = next(n for n in graph_payload["nodes"] if n["id"] == "paper:p3")
    paper["properties"]["is_core"] = False
    counts = graph_counts(GraphArtifact.model_validate(graph_payload))
    assert counts["resolved_core_researchers"] == 3
    assert counts["unique_core_factual_edges"] == 10


def test_version_matching_self_citations_are_rejected(graph_payload):
    edge = next(e for e in graph_payload["edges"] if e["relation"] == "CITES")
    edge["target_id"] = edge["source_id"]
    edge["edge_id"] = edge_id(Relation.CITES, edge["source_id"], edge["target_id"])
    errors = validate_graph(GraphArtifact.model_validate(graph_payload))
    assert any("forbidden self-loop" in error for error in errors)
