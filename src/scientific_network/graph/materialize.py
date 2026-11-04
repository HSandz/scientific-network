"""Recompute R7–R10 from accepted, core, paper-specific support only."""

from collections import defaultdict
from itertools import combinations

from scientific_network.contracts import GraphArtifact, Edge, EvidenceRecord, Relation as R
from scientific_network.graph.derive import organization_contributions
from scientific_network.graph.schema import edge_id


def materialize(graph: GraphArtifact, researcher_min: int = 2, organization_min: int = 3) -> GraphArtifact:
    graph = graph.model_copy(deep=True)
    graph.edges = [e for e in graph.edges if e.evidence_kind != "derived"]
    graph.evidence = [e for e in graph.evidence if e.kind != "derived"]
    base = {(e.relation, e.source_id, e.target_id): e.edge_id for e in graph.edges}
    core = {n.id: n for n in graph.nodes if n.label == "Paper" and n.properties.get("is_core") is True}
    authors, topics, observations = defaultdict(set), defaultdict(set), defaultdict(list)
    for relation, left, right in base:
        if relation == R.AUTHORED and right in core:
            authors[right].add(left)
        if relation == R.HAS_TOPIC and left in core:
            topics[left].add(right)
    for observation in graph.affiliation_observations:
        if observation.paper_id in core:
            observations[observation.paper_id].append((observation.researcher_id, observation.organization_id))
    records = {}

    def support(relation, left, right, paper, inputs, weight=0.0):
        key = (relation, left, right)
        item = records.setdefault(key, {"papers": set(), "inputs": set(), "weight": 0.0})
        if paper not in item["papers"]:
            item["weight"] += weight
        item["papers"].add(paper)
        item["inputs"].update(inputs)

    for paper, node in core.items():
        people = sorted(authors[paper])
        official_count = node.properties.get("official_author_count", len(people))
        if official_count < len(people):
            raise ValueError("resolved authors exceed official byline count")
        for left, right in combinations(people, 2):
            support(R.COAUTHORED_WITH, left, right, paper,
                [base[R.AUTHORED, left, paper], base[R.AUTHORED, right, paper]], 1 / (official_count - 1))
        pairs = organization_contributions(observations[paper])
        for (left, right), weight in sorted(pairs.items()):
            inputs = set()
            for (person_a, org_a), (person_b, org_b) in combinations(observations[paper], 2):
                if person_a != person_b and tuple(sorted((org_a, org_b))) == (left, right):
                    inputs.update([base[R.AUTHORED, person_a, paper], base[R.AUTHORED, person_b, paper],
                        base[R.AFFILIATED_WITH, person_a, org_a], base[R.AFFILIATED_WITH, person_b, org_b]])
            support(R.COLLABORATED_WITH, left, right, paper, inputs, weight)
        for person in people:
            for topic in topics[paper]:
                support(R.RESEARCHES_TOPIC, person, topic, paper,
                    [base[R.AUTHORED, person, paper], base[R.HAS_TOPIC, paper, topic]])
        for person, organization in observations[paper]:
            for topic in topics[paper]:
                support(R.CONTRIBUTES_TO_TOPIC, organization, topic, paper,
                    [base[R.AUTHORED, person, paper], base[R.AFFILIATED_WITH, person, organization], base[R.HAS_TOPIC, paper, topic]])
    for (relation, left, right), item in sorted(records.items()):
        minimum = researcher_min if relation == R.RESEARCHES_TOPIC else organization_min if relation == R.CONTRIBUTES_TO_TOPIC else 1
        if len(item["papers"]) < minimum:
            continue
        identifier = edge_id(relation, left, right)
        evidence_id = "evidence:derived:" + identifier.removeprefix("edge:")
        graph.evidence.append(EvidenceRecord(id=evidence_id, kind="derived",
            support_edge_ids=sorted(item["inputs"]), support_paper_ids=sorted(item["papers"])))
        props = {"support_count": len(item["papers"])}
        if relation in {R.COAUTHORED_WITH, R.COLLABORATED_WITH}:
            props["fractional_weight"] = item["weight"]
        graph.edges.append(Edge(edge_id=identifier, relation=relation, source_id=left, target_id=right,
            evidence_kind="derived", evidence_ids=[evidence_id], method_version="core-derivation-v1",
            graph_version=graph.graph_version, validation_status="accepted", properties=props))
    graph.edges.sort(key=lambda e: e.edge_id)
    graph.evidence.sort(key=lambda e: e.id)
    return graph
