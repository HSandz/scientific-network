"""Read-only inventory and full typed-property fingerprints; compatible with the retained dump baseline.

Sort entity references before projecting large property maps to bound server memory.
No credentials are written into the inventory.
"""
from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
import logging
from pathlib import Path
import sys
from typing import Any
from zoneinfo import ZoneInfo

import os
from neo4j import GraphDatabase, READ_ACCESS, unit_of_work

logging.getLogger("neo4j").setLevel(logging.ERROR)

LABELS = ["Organization", "Paper", "Researcher", "Topic", "Venue"]
RELATIONS = [
    "AUTHORED", "AFFILIATED_WITH", "PUBLISHED_IN", "CITES", "HAS_TOPIC",
    "SUBTOPIC_OF", "COAUTHORED_WITH", "COLLABORATED_WITH",
    "RESEARCHES_TOPIC", "CONTRIBUTES_TO_TOPIC",
]
SCHEMA_FIELDS = (
    "name", "type", "entityType", "labelsOrTypes", "properties", "ownedIndex",
    "ownedType", "owningConstraint", "indexProvider", "provider", "options",
    "createStatement", "state",
)


def canonical(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): canonical(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (list, tuple)):
        return [canonical(v) for v in value]
    if isinstance(value, (bytes, bytearray)):
        return {"__bytes_sha256__": sha256(value).hexdigest(), "length": len(value)}
    if hasattr(value, "iso_format"):
        return value.iso_format()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def digest(value: Any) -> str:
    raw = json.dumps(canonical(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return sha256(raw).hexdigest()


def typed_value(value: Any) -> Any:
    """Encode property datatypes as well as values for exact graph fingerprints."""
    if value is None:
        return {"type": "null"}
    if isinstance(value, list):
        return {"type": "list", "items": [typed_value(item) for item in value]}
    return {"type": type(value).__name__, "value": canonical(value)}


def typed_properties(properties: dict[str, Any]) -> dict[str, Any]:
    return {key: typed_value(value) for key, value in sorted(properties.items())}


def graph_fingerprints(tx) -> dict[str, Any]:
    node_total = int(tx.run("MATCH (n) RETURN count(n) AS n").single()["n"])
    node_ids = tx.run(
        "MATCH (n) RETURN count(n.id) AS with_id, count(DISTINCT n.id) AS distinct_ids"
    ).single()
    node_hash = sha256()
    node_count = 0
    for row in tx.run(
        "MATCH (n) WITH n ORDER BY n.id RETURN labels(n) AS labels, properties(n) AS props"
    ):
        item = {"labels": sorted(row["labels"]), "properties": typed_properties(row["props"])}
        node_hash.update(json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode())
        node_hash.update(b"\n")
        node_count += 1

    rel_counts = tx.run(
        "MATCH ()-[r]->() RETURN count(r) AS total, count(r.edge_id) AS with_edge_id, "
        "count(DISTINCT r.edge_id) AS distinct_edge_ids"
    ).single()
    rel_hash = sha256()
    rel_count = 0
    for row in tx.run(
        "MATCH (s)-[r]->(t) WITH s,r,t ORDER BY r.edge_id,s.id,t.id,type(r) RETURN labels(s) AS source_labels, s.id AS source_id, "
        "type(r) AS type, labels(t) AS target_labels, t.id AS target_id, "
        "properties(r) AS props"
    ):
        item = {
            "source_labels": sorted(row["source_labels"]),
            "source_id": row["source_id"],
            "type": row["type"],
            "target_labels": sorted(row["target_labels"]),
            "target_id": row["target_id"],
            "properties": typed_properties(row["props"]),
        }
        rel_hash.update(json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode())
        rel_hash.update(b"\n")
        rel_count += 1
    return {
        "node_stream_count": node_count,
        "nodes_with_id": int(node_ids["with_id"]),
        "distinct_node_ids": int(node_ids["distinct_ids"]),
        "node_stream_sha256": node_hash.hexdigest(),
        "relationship_stream_count": rel_count,
        "relationships_with_edge_id": int(rel_counts["with_edge_id"]),
        "distinct_edge_ids": int(rel_counts["distinct_edge_ids"]),
        "relationship_stream_sha256": rel_hash.hexdigest(),
    }


def records(tx, query: str) -> list[dict[str, Any]]:
    return [canonical(rec.data()) for rec in tx.run(query)]


def build_inventory(tx, database: str, current_user: str | None = None) -> dict[str, Any]:
    total_nodes = int(tx.run("MATCH (n) RETURN count(n) AS n").single()["n"])
    total_edges = int(tx.run("MATCH ()-[r]->() RETURN count(r) AS n").single()["n"])
    nodes = {r["label"]: int(r["count"]) for r in records(
        tx, "MATCH (n) UNWIND labels(n) AS label RETURN label, count(*) AS count ORDER BY label"
    )}
    edges = {r["type"]: int(r["count"]) for r in records(
        tx, "MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS count ORDER BY type"
    )}
    node_versions = records(tx, "MATCH (n) RETURN n.graph_version AS version, count(*) AS count ORDER BY version")
    edge_versions = records(tx, "MATCH ()-[r]->() RETURN r.graph_version AS version, count(*) AS count ORDER BY version")
    node_projects = records(tx, "MATCH (n) RETURN n.project AS project, count(*) AS count ORDER BY project")
    edge_projects = records(tx, "MATCH ()-[r]->() RETURN r.project AS project, count(*) AS count ORDER BY project")
    samples: dict[str, Any] = {"nodes": {}, "relationships": {}}
    for label in LABELS:
        row = tx.run(
            f"MATCH (n:`{label}`) WHERE n.id IS NOT NULL "
            "RETURN labels(n) AS labels, properties(n) AS props ORDER BY n.id LIMIT 1"
        ).single()
        if row:
            props = canonical(row["props"])
            samples["nodes"][label] = {
                "labels": sorted(row["labels"]), "id": props.get("id"),
                "name": props.get("name"), "year": props.get("year"),
                "graph_version": props.get("graph_version"),
                "property_keys": sorted(props), "properties_sha256": digest(props),
            }
    for relation in RELATIONS:
        row = tx.run(
            f"MATCH (s)-[r:`{relation}`]->(t) "
            "RETURN s.id AS source_id, t.id AS target_id, properties(r) AS props "
            "ORDER BY r.edge_id LIMIT 1"
        ).single()
        if row:
            props = canonical(row["props"])
            samples["relationships"][relation] = {
                "source_id": row["source_id"], "target_id": row["target_id"],
                "edge_id": props.get("edge_id"), "type": relation,
                "property_keys": sorted(props), "properties_sha256": digest(props),
                "property_value_types": {
                    key: ("null" if value is None else "array" if isinstance(value, list) else type(value).__name__)
                    for key, value in sorted(props.items())
                },
                "weights_and_support": {
                    key: value for key, value in props.items()
                    if any(term in key.lower() for term in ("weight", "support", "count"))
                    and isinstance(value, (int, float, str, bool))
                },
                "evidence_ids_count": len(props.get("evidence_ids", []))
                    if isinstance(props.get("evidence_ids"), list) else None,
                "evidence_ids_sha256": digest(props.get("evidence_ids")) if "evidence_ids" in props else None,
            }
    return {
        "captured_at": datetime.now(ZoneInfo("Asia/Bangkok")).isoformat(),
        "database": database,
        "current_user_confirmed": current_user is not None,
        "total_nodes": total_nodes,
        "total_relationships": total_edges,
        "nodes_by_label": nodes,
        "relationships_by_type": edges,
        "node_graph_versions": node_versions,
        "relationship_graph_versions": edge_versions,
        "node_projects": node_projects,
        "relationship_projects": edge_projects,
        "samples": samples,
    }


def scan(uri: str, username: str, password: str, database: str) -> dict[str, Any]:
    driver = None
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password), connection_timeout=10.0)
        driver.verify_connectivity()
        # These system-database catalog procedures are read-only but must use
        # the server's default transaction mode; graph inspection below is READ_ACCESS.
        with driver.session(database="system") as sys_session:
            db_rows = [canonical(r.data()) for r in sys_session.run(
                "SHOW DATABASES YIELD name, currentStatus, requestedStatus, default, home "
                "RETURN name, currentStatus, requestedStatus, default, home"
            )]
            user_row = sys_session.run("CALL dbms.showCurrentUser() YIELD username RETURN username").single()
            current_user = str(user_row["username"]) if user_row else None
        available = {row.get("name"): row.get("currentStatus") for row in db_rows}
        resolved_db = database
        if resolved_db not in available:
            if "neo4j" in available and available["neo4j"] == "online":
                resolved_db = "neo4j"
            else:
                return {"connected": True, "authenticated": True, "database": database,
                        "databases": db_rows, "current_user_confirmed": current_user is not None,
                        "error_class": "ConfiguredDatabaseNotFound"}
        if available.get(resolved_db) != "online":
            return {"connected": True, "authenticated": True, "database": resolved_db,
                    "databases": db_rows, "current_user_confirmed": current_user is not None,
                    "error_class": "DatabaseNotOnline"}
        with driver.session(database=resolved_db, default_access_mode=READ_ACCESS) as session:
            inv = session.execute_read(unit_of_work(timeout=300)(build_inventory), resolved_db, current_user)
            inv["graph_fingerprints"] = session.execute_read(unit_of_work(timeout=300)(graph_fingerprints))
        # SHOW schema commands do not mutate data; run them as read-only
        # auto-commit statements because Neo4j forbids them inside READ_ACCESS tx.
        with driver.session(database=resolved_db) as session:
            constraint_rows = [canonical(r.data()) for r in session.run("SHOW CONSTRAINTS YIELD * RETURN * ORDER BY name")]
            index_rows = [canonical(r.data()) for r in session.run("SHOW INDEXES YIELD * RETURN * ORDER BY name")]
        inv["constraints"] = [{k: row.get(k) for k in SCHEMA_FIELDS if k in row} for row in constraint_rows]
        inv["indexes"] = [{k: row.get(k) for k in SCHEMA_FIELDS if k in row} for row in index_rows]
        inv["all_indexes_online"] = all(row.get("state") == "ONLINE" for row in inv["indexes"])
        inv.update({"connected": True, "authenticated": True, "resolved_database": resolved_db,
                    "database_catalog": db_rows,
                    "configured_database_matches": resolved_db == database,
                    "authenticated_username_matches_configured": current_user == username,
                    "current_user_confirmed": current_user is not None})
        return inv
    except Exception as exc:
        return {"connected": False, "authenticated": False, "error_class": type(exc).__name__,
                "error_code": getattr(exc, "code", None), "databases": []}
    finally:
        if driver is not None:
            driver.close()


def main():
    password = os.environ.get("NEO4J_PASSWORD", "")
    if not password:
        raise SystemExit("NEO4J_PASSWORD is required")
    data = scan(os.environ.get("EXPLORER_NEO4J_URI", "bolt://neo4j:7687"),
                os.environ.get("NEO4J_USERNAME", "neo4j"), password,
                os.environ.get("NEO4J_DATABASE", "neo4j"))
    print(json.dumps(data, indent=2, ensure_ascii=False))
    if not data.get("connected") or not data.get("all_indexes_online"):
        raise SystemExit(1)

if __name__ == "__main__":
    main()
