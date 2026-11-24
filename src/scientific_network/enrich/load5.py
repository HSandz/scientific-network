"""Idempotent Neo4j import of the v5-enriched graph into the isolated ``neo4j-enriched`` service (port 7690 only).

The v4 layer goes through the frozen v4 importer (its count reconciliation stays in force); the enrichment
layer is added with labeled lookups and 5,000-row transactions, then per-label and per-relation counts
are reconciled against the canonical file. v4 nodes only gain properties from ``node_enrichments``.
"""

import os
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j.exceptions import DriverError, Neo4jError

from scientific_network.collect.storage import digest, write_json
from scientific_network.contracts import GraphArtifact
from scientific_network.enrich.graph5 import ENRICH_LABELS, RELATION_SPEC, enriched_counts, split_layers, validate_enriched
from scientific_network.graph.load import BATCH_SIZE, _count, _run_batches, flat, import_graph

ENRICHED_BOLT_PORT = 7690
PROJECT = "scientific-network"


def check_enriched_target(uri: str) -> None:
    try:
        port = urlsplit(uri).port
    except ValueError:
        port = None
    if port != ENRICHED_BOLT_PORT:
        raise ValueError(f"the v5-enriched graph may only be imported into the isolated neo4j-enriched service "
                         f"(bolt port {ENRICHED_BOLT_PORT}); set NEO4J_URI=bolt://localhost:{ENRICHED_BOLT_PORT}")


def edge_groups(graph: dict) -> dict[tuple[str, str, str], list[dict]]:
    """Enrichment edges grouped by (relation, source label, target label) so each lookup uses a label index."""
    label = {n["id"]: n["label"] for n in graph["nodes"]}
    groups: dict[tuple[str, str, str], list[dict]] = {}
    for edge in graph["edges"]:
        if edge["relation"] in RELATION_SPEC:
            groups.setdefault((edge["relation"], label[edge["source_id"]], label[edge["target_id"]]), []).append(edge)
    return groups


def edge_statement(relation: str, source: str, target: str) -> str:
    return ("UNWIND $rows AS row "
            f"MATCH (a:{source} {{id: row.left}}) MATCH (b:{target} {{id: row.right}}) "
            f"MERGE (a)-[r:{relation} {{edge_id: row.edge_id}}]->(b) SET r += row.props")


def import_enrichment(session, graph: dict, *, batch_size: int = BATCH_SIZE) -> dict:
    version = graph["graph_version"]
    _, enrich = split_layers(graph)
    transactions = 0
    for label in (*ENRICH_LABELS, "Organization"):
        rows = [{"id": n["id"], "props": flat({**(n.get("properties") or {}), "name": n["name"], "project": PROJECT, "graph_version": version})}
                for n in enrich["nodes"] if n["label"] == label]
        if rows:
            transactions += _run_batches(session, f"UNWIND $rows AS row MERGE (n:{label} {{id: row.id}}) SET n += row.props", rows, batch_size)
    rows = [{"id": node_id, "props": flat(props)}
            for node_id, props in graph.get("node_enrichments", {}).items()]
    if rows:
        transactions += _run_batches(session, "UNWIND $rows AS row MATCH (n:Organization {id: row.id}) SET n += row.props", rows, batch_size)
    for (relation, source, target), edges in sorted(edge_groups(graph).items()):
        rows = [{"left": e["source_id"], "right": e["target_id"], "edge_id": e["edge_id"],
                 "props": flat({**e["properties"], "project": PROJECT, "graph_version": version, "method_version": e["method_version"],
                                "evidence_kind": e["evidence_kind"], "evidence_ids": e["evidence_ids"],
                                "validation_status": e["validation_status"]})} for e in edges]
        transactions += _run_batches(session, edge_statement(relation, source, target), rows, batch_size)
    stored_nodes = {label: session.execute_read(_count, f"MATCH (n:{label} {{project: $project, graph_version: $version}}) RETURN count(n) AS n",
                                                {"project": PROJECT, "version": version}) for label in (*ENRICH_LABELS, "Organization")}
    stored_edges = {rel: session.execute_read(_count, f"MATCH ()-[r:{rel}]->() WHERE r.project = $project AND r.graph_version = $version RETURN count(r) AS n",
                                              {"project": PROJECT, "version": version}) for rel in RELATION_SPEC}
    expected_nodes = Counter(n["label"] for n in enrich["nodes"])
    expected_edges = Counter(e["relation"] for e in enrich["edges"])
    mismatches = [f"{k}: stored {v} != canonical {expected_nodes.get(k, 0)}" for k, v in stored_nodes.items() if v != expected_nodes.get(k, 0)]
    mismatches += [f"{k}: stored {v} != canonical {expected_edges.get(k, 0)}" for k, v in stored_edges.items() if v != expected_edges.get(k, 0)]
    if mismatches:
        raise ValueError("Neo4j/canonical enrichment counts disagree (" + "; ".join(mismatches) + ")")
    return {"enrichment_nodes_by_label": stored_nodes, "enrichment_edges_by_relation": {k: v for k, v in stored_edges.items() if v},
            "transactions": transactions}


def build(graph_path: Path, report_path: Path, *, batch_size: int = BATCH_SIZE) -> dict:
    import json
    if report_path.exists() or report_path.resolve() == graph_path.resolve():
        raise ValueError("choose a new report path")
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    errors = validate_enriched(graph)
    if errors:
        raise ValueError("import blocked by enriched-graph errors: " + "; ".join(errors[:5]))
    load_dotenv(override=False)
    password = os.environ.get("NEO4J_PASSWORD")
    if not password:
        raise ValueError("NEO4J_PASSWORD must be configured in environment or ignored .env")
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    check_enriched_target(uri)
    base, _ = split_layers(graph)
    artifact = GraphArtifact.model_validate(base)
    try:
        with GraphDatabase.driver(uri, auth=(os.environ.get("NEO4J_USERNAME", "neo4j"), password), connection_timeout=15) as driver:
            driver.verify_connectivity()
            with driver.session(database=os.environ.get("NEO4J_DATABASE", "neo4j")) as session:
                for label in ("Researcher", "Organization", "Paper", "Topic", "Venue", *ENRICH_LABELS):
                    session.run(f"CREATE CONSTRAINT {label.lower()}_id IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE").consume()
                v4 = import_graph(session, artifact, batch_size=batch_size)
                added = import_enrichment(session, graph, batch_size=batch_size)
    except (Neo4jError, DriverError) as exc:
        raise ValueError(f"Neo4j import failed: {type(exc).__name__}: {str(getattr(exc, 'message', None) or exc)[:300]}") from None
    endpoint = urlsplit(uri)
    report = {"stage": "load-enriched", "graph_version": graph["graph_version"], "base_graph_version": graph["base_graph_version"],
              "input_sha256": digest(graph_path.read_bytes()), "neo4j_endpoint": f"{endpoint.scheme}://{endpoint.hostname}:{endpoint.port}",
              "counts": enriched_counts(graph), "v4_layer_database": v4, "enrichment_layer_database": added,
              "vector_index": "not created here; created with the embedding index (specification §6.2)",
              "semantic_accuracy": "not_measured_by_this_stage"}
    write_json(report_path, report)
    return report
