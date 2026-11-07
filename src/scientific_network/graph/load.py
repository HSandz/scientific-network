"""Idempotent Neo4j import with labeled lookups, batched transactions and reconciled counts.

Every node and relationship is written with ``MERGE`` on its deterministic ID, in
batches of ``BATCH_SIZE`` rows that each commit in their own transaction, so an
interrupted import is completed by running the same command again. The final counts
per label and per relation must equal the canonical graph or the import fails.
Foreign or version-conflicting IDs are refused before anything is written.
"""

from collections import Counter
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError, DriverError

from scientific_network.collect.storage import digest, read_config, write_json
from scientific_network.contracts import GraphArtifact, NodeLabel, Relation
from scientific_network.graph.schema import RELATIONSHIPS
from scientific_network.graph.validate import validate_graph, graph_counts

BATCH_SIZE = 5000
PROJECT = "scientific-network"
# The release graph (version ``release-...``) lives only in the isolated
# ``neo4j-five-year`` service. ``.env`` points NEO4J_URI at the pilot service, so a
# forgotten override must fail instead of writing into the pilot database.
RELEASE_GRAPH_PREFIX = "release-"
RELEASE_BOLT_PORT = 7689


def flat(properties: dict) -> dict:
    result = {}
    for key, value in properties.items():
        if isinstance(value, dict) or (isinstance(value, list) and any(isinstance(v, (list, dict)) for v in value)):
            value = json.dumps(value, sort_keys=True)
        result[key] = value
    return result


def batched(rows: list, size: int):
    if size < 1:
        raise ValueError("batch size must be a positive integer")
    for start in range(0, len(rows), size):
        yield rows[start:start + size]


def node_statement(label: NodeLabel) -> str:
    return f"UNWIND $rows AS row MERGE (n:{label.value} {{id: row.id}}) SET n += row.props"


def relation_statement(relation: Relation) -> str:
    """Labeled endpoint lookups use the per-label unique ``id`` indexes."""
    spec = RELATIONSHIPS[relation]
    return (
        "UNWIND $rows AS row "
        f"MATCH (a:{spec.source.value} {{id: row.left, project: $project, graph_version: $version}}) "
        f"MATCH (b:{spec.target.value} {{id: row.right, project: $project, graph_version: $version}}) "
        f"MERGE (a)-[r:{relation.value} {{edge_id: row.edge_id}}]->(b) SET r += row.props"
    )


def conflict_statement(label: NodeLabel) -> str:
    return (
        f"MATCH (n:{label.value}) WHERE n.id IN $ids AND (n.project IS NULL OR n.project <> $project "
        "OR n.graph_version IS NULL OR n.graph_version <> $version) RETURN count(n) AS n"
    )


def node_count_statement(label: NodeLabel) -> str:
    return f"MATCH (n:{label.value} {{project: $project, graph_version: $version}}) RETURN count(n) AS n"


def relation_count_statement(relation: Relation) -> str:
    return (
        f"MATCH ()-[r:{relation.value}]->() WHERE r.project = $project AND r.graph_version = $version "
        "RETURN count(r) AS n"
    )


def check_target(uri: str, graph: GraphArtifact) -> None:
    """Keep release graphs and non-release graphs in separate Neo4j services."""
    is_release = graph.graph_version.startswith(RELEASE_GRAPH_PREFIX) and not graph.is_synthetic
    try:
        port = urlsplit(uri).port
    except ValueError:
        port = None
    if is_release and port != RELEASE_BOLT_PORT:
        raise ValueError(
            f"release graph {graph.graph_version} may only be imported into the isolated neo4j-five-year "
            f"service (bolt port {RELEASE_BOLT_PORT}); set NEO4J_URI=bolt://localhost:{RELEASE_BOLT_PORT}"
        )
    if not is_release and port == RELEASE_BOLT_PORT:
        raise ValueError(
            f"bolt port {RELEASE_BOLT_PORT} is reserved for the release graph; "
            f"{graph.graph_version} is a synthetic or pilot graph"
        )


def _write_chunk(tx, statement: str, rows: list, params: dict) -> None:
    tx.run(statement, rows=rows, **params).consume()


def _run_batches(session, statement: str, rows: list, batch_size: int, **params) -> int:
    transactions = 0
    for chunk in batched(rows, batch_size):
        session.execute_write(_write_chunk, statement, chunk, params)
        transactions += 1
    return transactions


def _count(tx, statement: str, params: dict) -> int:
    return tx.run(statement, **params).single()["n"]


def _stored_counts(session, project: str, version: str) -> tuple[dict, dict]:
    params = {"project": project, "version": version}
    nodes = {label.value: session.execute_read(_count, node_count_statement(label), params) for label in NodeLabel}
    relations = {rel.value: session.execute_read(_count, relation_count_statement(rel), params) for rel in Relation}
    return nodes, relations


def import_graph(session, graph: GraphArtifact, *, project: str = PROJECT, batch_size: int = BATCH_SIZE) -> dict:
    """Write ``graph`` through ``session``; returns the load summary or raises on any mismatch."""
    version = graph.graph_version
    params = {"project": project, "version": version}
    for label in NodeLabel:
        ids = [n.id for n in graph.nodes if n.label == label]
        for chunk in batched(ids, batch_size):
            conflicts = session.execute_read(_count, conflict_statement(label), {**params, "ids": chunk})
            if conflicts:
                raise ValueError(
                    "existing entity IDs belong to another graph/version; use a separate database "
                    "or an explicitly reviewed migration"
                )
    nodes_before = sum(_stored_counts(session, project, version)[0].values())
    transactions = 0
    for label in NodeLabel:
        rows = [{"id": n.id, "props": flat({**n.properties, "name": n.name, "project": project, "graph_version": version})}
                for n in graph.nodes if n.label == label]
        transactions += _run_batches(session, node_statement(label), rows, batch_size)
    for relation in Relation:
        rows = [{"left": e.source_id, "right": e.target_id, "edge_id": e.edge_id,
                 "props": flat({**e.properties, "project": project, "graph_version": version,
                                "method_version": e.method_version, "evidence_kind": e.evidence_kind.value,
                                "evidence_ids": e.evidence_ids, "validation_status": e.validation_status})}
                for e in graph.edges if e.relation == relation]
        transactions += _run_batches(session, relation_statement(relation), rows, batch_size, **params)
    nodes_by_label, relations = _stored_counts(session, project, version)
    expected_nodes = Counter(n.label.value for n in graph.nodes)
    expected_relations = Counter(e.relation.value for e in graph.edges)
    mismatches = [f"{label}: stored {nodes_by_label[label]} != canonical {expected_nodes.get(label, 0)}"
                  for label in nodes_by_label if nodes_by_label[label] != expected_nodes.get(label, 0)]
    mismatches += [f"{rel}: stored {relations[rel]} != canonical {expected_relations.get(rel, 0)}"
                   for rel in relations if relations[rel] != expected_relations.get(rel, 0)]
    if mismatches:
        raise ValueError(
            "Neo4j/canonical table counts disagree (" + "; ".join(mismatches)
            + "); earlier batches are committed, so inspect the database and re-run the same import"
        )
    return {"nodes_before": nodes_before, "nodes_after": sum(nodes_by_label.values()),
            "nodes_by_label": nodes_by_label, "edges_after": sum(relations.values()),
            "edges_by_relation": {rel: n for rel, n in relations.items() if n},
            "batch_size": batch_size, "transactions": transactions}


def build(input_path: Path, output: Path, config_path: Path, *, batch_size: int = BATCH_SIZE) -> dict:
    if output.resolve() in {input_path.resolve(), config_path.resolve()} or output.exists():
        raise ValueError("choose a new report path distinct from graph/config before importing")
    graph = GraphArtifact.model_validate_json(input_path.read_bytes())
    config = read_config(config_path)
    errors = validate_graph(graph, max_topic_labels=config["topics"]["max_labels_per_paper"], require_derived=True,
        researcher_min=config["derived"]["researcher_topic_min_distinct_papers"],
        organization_min=config["derived"]["organization_topic_min_distinct_papers"])
    if errors:
        raise ValueError("import blocked by graph errors: " + "; ".join(errors[:5]))
    load_dotenv(override=False)
    password = os.environ.get("NEO4J_PASSWORD")
    if not password:
        raise ValueError("NEO4J_PASSWORD must be configured in environment or ignored .env")
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    check_target(uri, graph)
    try:
        with GraphDatabase.driver(uri, auth=(os.environ.get("NEO4J_USERNAME", "neo4j"), password),
                                  connection_timeout=15) as driver:
            driver.verify_connectivity()
            with driver.session(database=os.environ.get("NEO4J_DATABASE", "neo4j")) as session:
                for label in NodeLabel:
                    session.run(f"CREATE CONSTRAINT {label.value.lower()}_id IF NOT EXISTS FOR (n:{label.value}) REQUIRE n.id IS UNIQUE").consume()
                result = import_graph(session, graph, batch_size=batch_size)
    except (Neo4jError, DriverError) as exc:
        detail = str(getattr(exc, "message", None) or exc)[:300]
        raise ValueError(f"Neo4j import failed: {type(exc).__name__}: {detail}") from None
    is_release = graph.graph_version.startswith(RELEASE_GRAPH_PREFIX) and not graph.is_synthetic
    endpoint = urlsplit(uri)  # record scheme, host and port only, never userinfo
    report = {"stage": "build", "graph_version": graph.graph_version, "input_sha256": digest(input_path.read_bytes()),
        "quality_config_sha256": digest(config_path.read_bytes()),
        "neo4j_endpoint": f"{endpoint.scheme}://{endpoint.hostname}:{endpoint.port}",
        "is_synthetic": graph.is_synthetic, "counts": graph_counts(graph), "database": result,
        "semantic_accuracy": "not_measured",
        "release_status": "audit_pending" if is_release else "pilot_not_certified"}
    write_json(output, report)
    return report
