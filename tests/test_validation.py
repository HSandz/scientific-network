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


# --- Indexed per-node checks (release plan Phase 1, item 1) ---------------------------


def _edge(payload, relation, source, target, kind="observed"):
    """A well-formed fixture-compatible edge using existing evidence of the same kind."""
    evidence_id = next(e["id"] for e in payload["evidence"] if e["kind"] == kind)
    return {
        "edge_id": edge_id(relation, source, target), "relation": relation, "source_id": source,
        "target_id": target, "evidence_kind": kind, "evidence_ids": [evidence_id],
        "method_version": "m", "graph_version": payload["graph_version"],
        "validation_status": "accepted", "properties": {},
    }


def _errors(payload, **kwargs):
    return validate_graph(GraphArtifact.model_validate(payload), **kwargs)


def test_core_paper_without_or_with_two_venues_is_flagged_per_paper(graph_payload):
    graph_payload["edges"] = [
        e for e in graph_payload["edges"]
        if not (e["relation"] == "PUBLISHED_IN" and e["source_id"] == "paper:p1")
    ]
    graph_payload["nodes"].append({"id": "venue:other", "label": "Venue", "name": "Other", "properties": {}})
    graph_payload["edges"].append(_edge(graph_payload, "PUBLISHED_IN", "paper:p2", "venue:other"))
    errors = _errors(graph_payload)
    assert "paper:p1: core paper requires exactly one primary venue" in errors
    assert "paper:p2: core paper requires exactly one primary venue" in errors
    assert not any(error.startswith("paper:p3:") for error in errors)


def test_non_core_paper_may_have_no_venue(graph_payload):
    paper = next(n for n in graph_payload["nodes"] if n["id"] == "paper:p3")
    paper["properties"]["is_core"] = False
    graph_payload["edges"] = [
        e for e in graph_payload["edges"]
        if not (e["relation"] == "PUBLISHED_IN" and e["source_id"] == "paper:p3")
    ]
    assert not any("primary venue" in error for error in _errors(graph_payload))


def test_core_paper_needs_authorship_or_a_documented_unresolved_reason(graph_payload):
    graph_payload["edges"] = [
        e for e in graph_payload["edges"] if not (e["relation"] == "AUTHORED" and e["target_id"] == "paper:p3")
    ]
    assert "paper:p3: core paper needs authorship or documented unresolved exception" in _errors(graph_payload)
    paper = next(n for n in graph_payload["nodes"] if n["id"] == "paper:p3")
    paper["properties"]["unresolved_author_reason"] = "author_count_mismatch"
    assert not any("needs authorship" in error for error in _errors(graph_payload))


def test_topic_label_limit_counts_each_paper_separately(graph_payload):
    for index in range(3):
        topic = f"topic:extra{index}"
        graph_payload["nodes"].append({
            "id": topic, "label": "Topic", "name": topic,
            "properties": {"level": "leaf", "taxonomy_version": "t"},
        })
        graph_payload["edges"].append(_edge(graph_payload, "HAS_TOPIC", "paper:p1", topic, "inferred_topic"))
    errors = _errors(graph_payload)
    assert "paper:p1: too many accepted topic labels" in errors
    assert not any(error.startswith(("paper:p2: too many", "paper:p3: too many")) for error in errors)
    assert _errors(graph_payload, max_topic_labels=4).count("paper:p1: too many accepted topic labels") == 0


def test_leaf_topic_needs_exactly_one_parent(graph_payload):
    graph_payload["nodes"].append({
        "id": "topic:orphan", "label": "Topic", "name": "Orphan",
        "properties": {"level": "leaf", "taxonomy_version": "t"},
    })
    assert "topic:orphan: leaf topic requires exactly one parent" in _errors(graph_payload)
    graph_payload["nodes"].append({
        "id": "topic:parent2", "label": "Topic", "name": "Parent 2",
        "properties": {"level": "parent", "taxonomy_version": "t"},
    })
    graph_payload["edges"].append(
        _edge(graph_payload, "SUBTOPIC_OF", "topic:nlp-language-models", "topic:parent2", "curated_taxonomy")
    )
    assert "topic:nlp-language-models: leaf topic requires exactly one parent" in _errors(graph_payload)


def _large_invented_graph(papers: int) -> GraphArtifact:
    """Invented graph for timing only: four resolved authors and one venue per paper."""
    evidence = {
        "id": "evidence:x", "kind": "observed", "source_url": "https://example.org",
        "raw_sha256": "0" * 64, "source_locator": "x", "retrieved_at": "2026-11-01T00:00:00+00:00",
    }
    nodes = [{"id": "venue:v", "label": "Venue", "name": "V", "properties": {}}]
    edges = []

    def add(relation, source, target):
        edges.append({
            "edge_id": edge_id(relation, source, target), "relation": relation, "source_id": source,
            "target_id": target, "evidence_kind": "observed", "evidence_ids": ["evidence:x"],
            "method_version": "m", "graph_version": "g", "validation_status": "accepted", "properties": {},
        })

    for i in range(papers):
        paper = f"paper:{i:06d}"
        nodes.append({
            "id": paper, "label": "Paper", "name": paper,
            "properties": {"is_core": True, "year": 2023, "official_url": "https://example.org", "track": "main"},
        })
        add("PUBLISHED_IN", paper, "venue:v")
        for a in range(4):
            researcher = f"researcher:{i:06d}-{a}"
            nodes.append({"id": researcher, "label": "Researcher", "name": researcher,
                          "properties": {"resolution_status": "resolved"}})
            add("AUTHORED", researcher, paper)
    return GraphArtifact.model_validate({
        "graph_version": "g", "is_synthetic": True, "nodes": nodes, "edges": edges,
        "evidence": [evidence], "affiliation_observations": [],
    })


def test_validator_scales_linearly_on_a_10k_paper_invented_graph():
    import time

    graph = _large_invented_graph(10_000)
    started = time.perf_counter()
    errors = validate_graph(graph)
    elapsed = time.perf_counter() - started
    assert errors == []
    # Measured 0.3 s on 8 Nov 2026; the old per-node edge scans took 7 s at 4k papers
    # and would need over 40 s here, so this bound catches a quadratic regression.
    assert elapsed < 5.0
