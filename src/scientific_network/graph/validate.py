"""Offline structural checks. This cannot establish semantic extraction accuracy."""

from collections import Counter
from math import isclose

from scientific_network.contracts import EvidenceKind as K, GraphArtifact, NodeLabel as N, Relation as R
from scientific_network.graph.schema import RELATIONSHIPS, edge_id


def validate_graph(graph: GraphArtifact, max_topic_labels: int = 3, *, require_derived: bool = False,
                   researcher_min: int = 2, organization_min: int = 3) -> list[str]:
    errors: list[str] = []
    for label, identifiers in (
        ("node", [n.id for n in graph.nodes]),
        ("edge", [e.edge_id for e in graph.edges]),
        ("evidence", [e.id for e in graph.evidence]),
        ("affiliation observation", [a.id for a in graph.affiliation_observations]),
    ):
        errors.extend(f"duplicate {label} ID: {key}" for key, count in Counter(identifiers).items() if count > 1)
    nodes = {node.id: node for node in graph.nodes}
    evidence = {item.id: item for item in graph.evidence}
    edges = {item.edge_id: item for item in graph.edges}
    semantic_keys: set[tuple] = set()
    authored = {(e.source_id, e.target_id) for e in graph.edges if e.relation == R.AUTHORED}
    affiliations = {(a.researcher_id, a.organization_id) for a in graph.affiliation_observations}

    for node in graph.nodes:
        props = node.properties
        if node.label == N.RESEARCHER and props.get("resolution_status") not in {"resolved", "provisional", "unresolved"}:
            errors.append(f"{node.id}: missing/invalid resolution_status")
        if node.label == N.PAPER:
            if not isinstance(props.get("is_core"), bool) or type(props.get("year")) is not int:
                errors.append(f"{node.id}: Paper requires boolean is_core and integer year")
            if not props.get("official_url") or not props.get("track"):
                errors.append(f"{node.id}: Paper requires official_url and track")
        if node.label == N.TOPIC and (props.get("level") not in {"leaf", "parent"} or not props.get("taxonomy_version")):
            errors.append(f"{node.id}: Topic requires level and taxonomy_version")
        if node.label == N.ORGANIZATION and props.get("sector") not in {"academia", "industry", "government", "nonprofit", "unknown"}:
            errors.append(f"{node.id}: missing/invalid sector; use unknown for missing data")

    for edge in graph.edges:
        spec = RELATIONSHIPS[edge.relation]
        key = (edge.relation, edge.source_id, edge.target_id)
        if key in semantic_keys:
            errors.append(f"duplicate semantic edge: {key}")
        semantic_keys.add(key)
        if edge.source_id == edge.target_id:
            errors.append(f"{edge.edge_id}: forbidden self-loop")
        if spec.symmetric and edge.source_id >= edge.target_id:
            errors.append(f"{edge.edge_id}: symmetric pair must use canonical ID order")
        if edge.edge_id != edge_id(edge.relation, edge.source_id, edge.target_id):
            errors.append(f"{edge.edge_id}: incorrect deterministic edge ID")
        if edge.graph_version != graph.graph_version:
            errors.append(f"{edge.edge_id}: graph version mismatch")
        if edge.evidence_kind != spec.kind:
            errors.append(f"{edge.edge_id}: incorrect evidence class")
        for identifier in edge.evidence_ids:
            item = evidence.get(identifier)
            if item is None or item.kind != spec.kind:
                errors.append(f"{edge.edge_id}: missing or incompatible evidence {identifier}")
        source, target = nodes.get(edge.source_id), nodes.get(edge.target_id)
        if source is None or target is None or (source.label, target.label) != (spec.source, spec.target):
            errors.append(f"{edge.edge_id}: invalid endpoint labels or missing nodes")
            continue
        if edge.relation == R.AUTHORED and source.properties.get("resolution_status") != "resolved":
            errors.append(f"{edge.edge_id}: accepted authorship requires a resolved researcher")
        if edge.relation in {R.HAS_TOPIC, R.RESEARCHES_TOPIC, R.CONTRIBUTES_TO_TOPIC} and target.properties.get("level") != "leaf":
            errors.append(f"{edge.edge_id}: topic assignment requires a leaf topic")
        if edge.relation == R.SUBTOPIC_OF and (source.properties.get("level"), target.properties.get("level")) != ("leaf", "parent"):
            errors.append(f"{edge.edge_id}: hierarchy must connect leaf to parent")
        if edge.relation == R.AFFILIATED_WITH and (source.id, target.id) not in affiliations:
            errors.append(f"{edge.edge_id}: affiliation has no author-paper-organization observation")

    for observation in graph.affiliation_observations:
        valid_types = (
            (observation.researcher_id, N.RESEARCHER),
            (observation.paper_id, N.PAPER),
            (observation.organization_id, N.ORGANIZATION),
        )
        if any(identifier not in nodes or nodes[identifier].label != label for identifier, label in valid_types):
            errors.append(f"{observation.id}: invalid affiliation triple endpoints")
        if (observation.researcher_id, observation.paper_id) not in authored:
            errors.append(f"{observation.id}: researcher has no accepted authorship of this paper")
        if (R.AFFILIATED_WITH, observation.researcher_id, observation.organization_id) not in semantic_keys:
            errors.append(f"{observation.id}: missing aggregated affiliation edge")
        if any(identifier not in evidence or evidence[identifier].kind != K.OBSERVED for identifier in observation.evidence_ids):
            errors.append(f"{observation.id}: missing observed affiliation evidence")

    for item in graph.evidence:
        if item.kind != K.DERIVED:
            continue
        if any(identifier not in edges or edges[identifier].evidence_kind == K.DERIVED for identifier in item.support_edge_ids):
            errors.append(f"{item.id}: derived support must resolve to accepted base edges")
        if any(identifier not in nodes or nodes[identifier].label != N.PAPER or nodes[identifier].properties.get("is_core") is not True for identifier in item.support_paper_ids):
            errors.append(f"{item.id}: derived support requires core papers")

    for node in graph.nodes:
        if node.label == N.PAPER and node.properties.get("is_core") is True:
            venues = [e for e in graph.edges if e.relation == R.PUBLISHED_IN and e.source_id == node.id]
            if len(venues) != 1:
                errors.append(f"{node.id}: core paper requires exactly one primary venue")
            if not any(paper == node.id for _, paper in authored) and not node.properties.get("unresolved_author_reason"):
                errors.append(f"{node.id}: core paper needs authorship or documented unresolved exception")
        if node.label == N.PAPER:
            label_count = sum(e.relation == R.HAS_TOPIC and e.source_id == node.id for e in graph.edges)
            if label_count > max_topic_labels:
                errors.append(f"{node.id}: too many accepted topic labels")
        if node.label == N.TOPIC and node.properties.get("level") == "leaf":
            parents = [e for e in graph.edges if e.relation == R.SUBTOPIC_OF and e.source_id == node.id]
            if len(parents) != 1:
                errors.append(f"{node.id}: leaf topic requires exactly one parent")
    if not errors and (require_derived or any(e.evidence_kind == K.DERIVED for e in graph.edges)):
        from scientific_network.graph.materialize import materialize
        expected = materialize(graph, researcher_min, organization_min)
        expected_edges = {e.edge_id: e for e in expected.edges if e.evidence_kind == K.DERIVED}
        actual_edges = {e.edge_id: e for e in graph.edges if e.evidence_kind == K.DERIVED}
        if expected_edges.keys() != actual_edges.keys():
            errors.append("derived edge inventory differs from recomputed accepted core support")
        expected_evidence = {e.id: e for e in expected.evidence}
        for identifier in expected_edges.keys() & actual_edges.keys():
            actual, wanted = actual_edges[identifier], expected_edges[identifier]
            if actual.properties.get("support_count") != wanted.properties["support_count"]:
                errors.append(f"{identifier}: derived distinct-paper count mismatch")
            if "fractional_weight" in wanted.properties:
                value = actual.properties.get("fractional_weight")
                if not isinstance(value, (int, float)) or not isclose(value, wanted.properties["fractional_weight"], abs_tol=1e-9):
                    errors.append(f"{identifier}: derived fractional weight mismatch")
            actual_inputs = {s for ref in actual.evidence_ids for s in evidence[ref].support_edge_ids}
            actual_papers = {p for ref in actual.evidence_ids for p in evidence[ref].support_paper_ids}
            wanted_record = expected_evidence[wanted.evidence_ids[0]]
            if actual_inputs != set(wanted_record.support_edge_ids) or actual_papers != set(wanted_record.support_paper_ids):
                errors.append(f"{identifier}: derived support ledger mismatch")
    return errors


def graph_counts(graph: GraphArtifact) -> dict:
    core_papers = {n.id for n in graph.nodes if n.label == N.PAPER and n.properties.get("is_core") is True}
    resolved = {n.id for n in graph.nodes if n.label == N.RESEARCHER and n.properties.get("resolution_status") == "resolved"}
    core_researchers = {e.source_id for e in graph.edges if e.relation == R.AUTHORED and e.target_id in core_papers} & resolved
    supported_affiliations = {(a.researcher_id, a.organization_id) for a in graph.affiliation_observations if a.paper_id in core_papers}
    factual_core = [e for e in graph.edges if e.evidence_kind == K.OBSERVED and (
        (e.relation == R.AUTHORED and e.source_id in core_researchers and e.target_id in core_papers)
        or (e.relation == R.AFFILIATED_WITH and (e.source_id, e.target_id) in supported_affiliations)
        or (e.relation == R.PUBLISHED_IN and e.source_id in core_papers)
        or (e.relation == R.CITES and e.source_id in core_papers and e.target_id in core_papers)
    )]
    return {
        "nodes_by_label": dict(Counter(n.label for n in graph.nodes)),
        "edges_by_relation": dict(Counter(e.relation for e in graph.edges)),
        "edges_by_evidence_kind": dict(Counter(e.evidence_kind for e in graph.edges)),
        "core_papers": len(core_papers),
        "resolved_core_researchers": len(core_researchers),
        "unique_core_factual_edges": len({e.edge_id for e in factual_core}),
    }
