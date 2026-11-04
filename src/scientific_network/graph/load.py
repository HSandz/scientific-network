"""Transactional idempotent Neo4j import, refusing foreign/version-conflicting IDs."""

from collections import Counter
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError, DriverError

from scientific_network.collect.storage import digest, read_config, write_json
from scientific_network.contracts import GraphArtifact, NodeLabel, Relation
from scientific_network.graph.validate import validate_graph, graph_counts


def flat(properties: dict) -> dict:
    result = {}
    for key, value in properties.items():
        if isinstance(value, dict) or (isinstance(value, list) and any(isinstance(v, (list, dict)) for v in value)):
            value = json.dumps(value, sort_keys=True)
        result[key] = value
    return result


def build(input_path: Path, output: Path, config_path: Path) -> dict:
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
    project = "scientific-network"
    version = graph.graph_version

    def transaction(tx):
        ids = [n.id for n in graph.nodes]
        conflicts = tx.run("MATCH (n) WHERE n.id IN $ids AND (n.project IS NULL OR n.project <> $project OR n.graph_version IS NULL OR n.graph_version <> $version) RETURN count(n) AS n",
            ids=ids, project=project, version=version).single()["n"]
        if conflicts:
            raise ValueError("existing entity IDs belong to another graph/version; use a separate database or an explicitly reviewed migration")
        before = tx.run("MATCH (n {project:$project,graph_version:$version}) RETURN count(n) AS n", project=project, version=version).single()["n"]
        for label in NodeLabel:
            rows = [{"id": n.id, "props": flat({**n.properties, "name": n.name, "project": project, "graph_version": version})}
                    for n in graph.nodes if n.label == label]
            if rows:
                tx.run(f"UNWIND $rows AS row MERGE (n:{label} {{id:row.id}}) SET n += row.props", rows=rows).consume()
        for relation in Relation:
            rows = [{"left": e.source_id, "right": e.target_id, "edge_id": e.edge_id,
                "props": flat({**e.properties, "project": project, "graph_version": version,
                    "method_version": e.method_version, "evidence_kind": e.evidence_kind,
                    "evidence_ids": e.evidence_ids, "validation_status": e.validation_status})}
                for e in graph.edges if e.relation == relation]
            if rows:
                tx.run(f"UNWIND $rows AS row MATCH (a {{id:row.left,project:$project,graph_version:$version}}), (b {{id:row.right,project:$project,graph_version:$version}}) MERGE (a)-[r:{relation} {{edge_id:row.edge_id}}]->(b) SET r += row.props",
                    rows=rows, project=project, version=version).consume()
        node_count = tx.run("MATCH (n {project:$project,graph_version:$version}) RETURN count(n) AS n", project=project, version=version).single()["n"]
        relations = {r["relation"]: r["n"] for r in tx.run("MATCH ()-[r {project:$project,graph_version:$version}]->() RETURN type(r) AS relation,count(r) AS n", project=project, version=version)}
        if node_count != len(graph.nodes) or relations != dict(Counter(e.relation for e in graph.edges)):
            raise ValueError("Neo4j/canonical table counts disagree; transaction rolled back")
        return {"nodes_before": before, "nodes_after": node_count, "edges_after": sum(relations.values()), "edges_by_relation": relations}

    try:
        with GraphDatabase.driver(os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
            auth=(os.environ.get("NEO4J_USERNAME", "neo4j"), password), connection_timeout=15) as driver:
            driver.verify_connectivity()
            with driver.session(database=os.environ.get("NEO4J_DATABASE", "neo4j")) as session:
                for label in NodeLabel:
                    session.run(f"CREATE CONSTRAINT {label.lower()}_id IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE").consume()
                result = session.execute_write(transaction)
    except (Neo4jError, DriverError) as exc:
        raise ValueError(f"Neo4j import failed: {type(exc).__name__}") from None
    report = {"stage": "build", "graph_version": version, "input_sha256": digest(input_path.read_bytes()),
        "quality_config_sha256": digest(config_path.read_bytes()),
        "is_synthetic": graph.is_synthetic, "counts": graph_counts(graph), "database": result,
        "semantic_accuracy": "not_measured", "release_status": "pilot_not_certified"}
    write_json(output, report)
    return report
