"""Read-only Neo4j repository with parameterized Cypher, label/relation allowlists, and timeouts."""

from typing import Any
import unicodedata
from urllib.parse import urlsplit

import neo4j
from neo4j import GraphDatabase, Query
from neo4j.exceptions import DriverError, Neo4jError

from ..config import (
    EXPECTED_EDGES_BY_RELATION,
    EXPECTED_GRAPH_VERSION,
    EXPECTED_NODES_BY_LABEL,
    EXPECTED_TOTAL_EDGES,
    EXPECTED_TOTAL_NODES,
    Settings,
)


ALLOWED_LABELS: frozenset[str] = frozenset({
    "Researcher",
    "Paper",
    "Organization",
    "Topic",
    "Venue",
})

ALLOWED_RELATIONS: frozenset[str] = frozenset({
    "AUTHORED",
    "AFFILIATED_WITH",
    "PUBLISHED_IN",
    "CITES",
    "HAS_TOPIC",
    "SUBTOPIC_OF",
    "COAUTHORED_WITH",
    "COLLABORATED_WITH",
    "RESEARCHES_TOPIC",
    "CONTRIBUTES_TO_TOPIC",
})

SYMMETRIC_RELATIONS: frozenset[str] = frozenset({
    "COAUTHORED_WITH",
    "COLLABORATED_WITH",
})

PREFIX_TO_LABEL: dict[str, str] = {
    "researcher:": "Researcher",
    "paper:": "Paper",
    "organization:": "Organization",
    "topic:": "Topic",
    "venue:": "Venue",
}


def validate_labels(labels: list[str] | None) -> list[str]:
    if not labels:
        return sorted(ALLOWED_LABELS)
    cleaned = []
    for label in labels:
        if label not in ALLOWED_LABELS:
            raise ValueError(f"Unsupported node label: {label!r}")
        if label not in cleaned:
            cleaned.append(label)
    return cleaned


def validate_relations(relations: list[str] | None) -> list[str]:
    if not relations:
        return sorted(ALLOWED_RELATIONS)
    cleaned = []
    for rel in relations:
        if rel not in ALLOWED_RELATIONS:
            raise ValueError(f"Unsupported relationship predicate: {rel!r}")
        if rel not in cleaned:
            cleaned.append(rel)
    return cleaned


def label_for_id(node_id: str) -> str | None:
    for prefix, label in PREFIX_TO_LABEL.items():
        if node_id.startswith(prefix):
            return label
    return None


_DIACRITIC_PAIRS: tuple[tuple[str, str], ...] = (
    ("ä", "a"), ("á", "a"), ("à", "a"), ("â", "a"), ("ã", "a"), ("å", "a"), ("ă", "a"), ("ą", "a"),
    ("ë", "e"), ("é", "e"), ("è", "e"), ("ê", "e"), ("ě", "e"), ("ę", "e"), ("ė", "e"), ("ē", "e"),
    ("ï", "i"), ("í", "i"), ("ì", "i"), ("î", "i"), ("ı", "i"), ("ī", "i"),
    ("ö", "o"), ("ó", "o"), ("ò", "o"), ("ô", "o"), ("õ", "o"), ("ø", "o"), ("ő", "o"), ("ō", "o"),
    ("ü", "u"), ("ú", "u"), ("ù", "u"), ("û", "u"), ("ű", "u"), ("ů", "u"), ("ū", "u"),
    ("ñ", "n"), ("ń", "n"), ("ň", "n"),
    ("ç", "c"), ("ć", "c"), ("č", "c"),
    ("ß", "ss"), ("š", "s"), ("ś", "s"), ("ş", "s"), ("ș", "s"),
    ("ž", "z"), ("ź", "z"), ("ż", "z"),
    ("ý", "y"), ("ÿ", "y"),
    ("ğ", "g"), ("đ", "d"), ("ł", "l"), ("ř", "r"), ("ț", "t"), ("æ", "ae"), ("œ", "oe"),
)


def fold_diacritics(text: str) -> str:
    """Fold Unicode diacritics and special Latin characters to lowercase ASCII for search."""
    lowered = text.strip().lower()
    for src, dst in _DIACRITIC_PAIRS:
        lowered = lowered.replace(src, dst)
    decomposed = unicodedata.normalize("NFKD", lowered)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _cypher_fold_expr(prop_expr: str) -> str:
    """Build a Cypher expression that folds common Latin diacritics on a lowercase property."""
    expr = f"toLower(coalesce({prop_expr}, ''))"
    for src, dst in _DIACRITIC_PAIRS:
        expr = f"replace({expr}, '{src}', '{dst}')"
    return expr


class Neo4jRepository:
    """Read-only Neo4j data access layer.

    All sessions use `default_access_mode=neo4j.READ_ACCESS` and bounded query timeouts.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.timeout = settings.query_timeout_seconds
        self._driver: neo4j.Driver | None = None
        self._inventory_cache: dict[str, Any] | None = None

    @property
    def sanitized_endpoint(self) -> str:
        parsed = urlsplit(self.settings.neo4j_uri)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 7689
        scheme = parsed.scheme or "bolt"
        return f"{scheme}://{host}:{port}"

    def get_driver(self) -> neo4j.Driver:
        if self._driver is None:
            if not self.settings.neo4j_password:
                raise RuntimeError(
                    "NEO4J_PASSWORD is not configured. Set NEO4J_PASSWORD in environment or .env."
                )
            # Production Bolt stays on an isolated Docker network with no host port.
            self._driver = GraphDatabase.driver(
                self.settings.neo4j_uri,
                auth=(self.settings.neo4j_username, self.settings.neo4j_password),
                connection_timeout=10.0,
                max_connection_pool_size=8,
                connection_acquisition_timeout=10.0,
                max_transaction_retry_time=5.0,
            )
        return self._driver

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def run_read(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Execute a parameterized read-only Cypher query with a strict timeout."""
        driver = self.get_driver()
        query_obj = Query(cypher, timeout=self.timeout)
        with driver.session(
            database=self.settings.neo4j_database,
            default_access_mode=neo4j.READ_ACCESS,
        ) as session:
            result = session.run(query_obj, parameters=params or {})
            return [dict(record) for record in result]

    def verify_inventory(self, *, use_cache: bool = True) -> dict[str, Any]:
        """Check Neo4j connectivity, counts by label/relation, and expected graph version."""
        if use_cache and self._inventory_cache is not None:
            return self._inventory_cache

        warnings: list[str] = []
        try:
            node_rows = self.run_read(
                "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count ORDER BY count DESC"
            )
            edge_rows = self.run_read(
                "MATCH ()-[r]->() RETURN type(r) AS relation, count(r) AS count ORDER BY relation"
            )
            version_rows = self.run_read(
                "MATCH (n:Venue) RETURN collect(DISTINCT n.graph_version) AS versions"
            )
        except (Neo4jError, DriverError, RuntimeError, OSError) as exc:
            return {
                "connected": False,
                "endpoint": self.sanitized_endpoint,
                "expected_graph_version": EXPECTED_GRAPH_VERSION,
                "observed_graph_versions": [],
                "database_verified": False,
                "nodes_by_label": {},
                "edges_by_relation": {},
                "total_nodes": 0,
                "total_edges": 0,
                "warnings": [f"Database connection failed: {type(exc).__name__}"],
            }

        nodes_by_label = {row["label"]: int(row["count"]) for row in node_rows if row.get("label")}
        edges_by_relation = {row["relation"]: int(row["count"]) for row in edge_rows if row.get("relation")}
        total_nodes = sum(nodes_by_label.values())
        total_edges = sum(edges_by_relation.values())
        versions = version_rows[0]["versions"] if version_rows and version_rows[0].get("versions") else []

        if versions != [EXPECTED_GRAPH_VERSION]:
            warnings.append(
                f"Expected graph_version {EXPECTED_GRAPH_VERSION!r}, observed {versions!r}."
            )
        if total_nodes != EXPECTED_TOTAL_NODES:
            warnings.append(f"Expected {EXPECTED_TOTAL_NODES} total nodes, observed {total_nodes}.")
        if total_edges != EXPECTED_TOTAL_EDGES:
            warnings.append(f"Expected {EXPECTED_TOTAL_EDGES} total edges, observed {total_edges}.")
        for lbl, expected_cnt in EXPECTED_NODES_BY_LABEL.items():
            if nodes_by_label.get(lbl, 0) != expected_cnt:
                warnings.append(f"Label {lbl}: expected {expected_cnt}, observed {nodes_by_label.get(lbl, 0)}.")
        for rel, expected_cnt in EXPECTED_EDGES_BY_RELATION.items():
            if edges_by_relation.get(rel, 0) != expected_cnt:
                warnings.append(f"Relation {rel}: expected {expected_cnt}, observed {edges_by_relation.get(rel, 0)}.")

        verified = len(warnings) == 0
        payload = {
            "connected": True,
            "endpoint": self.sanitized_endpoint,
            "expected_graph_version": EXPECTED_GRAPH_VERSION,
            "observed_graph_versions": versions,
            "database_verified": verified,
            "nodes_by_label": nodes_by_label,
            "edges_by_relation": edges_by_relation,
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "warnings": warnings,
        }
        if verified:
            self._inventory_cache = payload
        return payload

    def get_node_by_id(self, node_id: str) -> dict[str, Any] | None:
        """Fetch a single node by its stable ID using its label index when known."""
        inferred_label = label_for_id(node_id)
        if inferred_label in ALLOWED_LABELS:
            cypher = f"MATCH (n:{inferred_label} {{id: $id}}) RETURN n, labels(n)[0] AS label LIMIT 1"
        else:
            cypher = "MATCH (n {id: $id}) RETURN n, labels(n)[0] AS label LIMIT 1"
        rows = self.run_read(cypher, {"id": node_id})
        if not rows:
            return None
        raw_node = dict(rows[0]["n"])
        raw_node["_label"] = rows[0]["label"]
        return raw_node

    def get_nodes_by_ids(self, node_ids: list[str]) -> dict[str, dict[str, Any]]:
        """Batch fetch nodes by IDs, grouping by label prefix to utilize per-label unique indexes."""
        if not node_ids:
            return {}
        by_label: dict[str, list[str]] = {}
        unlabeled: list[str] = []
        for nid in set(node_ids):
            lbl = label_for_id(nid)
            if lbl in ALLOWED_LABELS:
                by_label.setdefault(lbl, []).append(nid)
            else:
                unlabeled.append(nid)

        results: dict[str, dict[str, Any]] = {}
        for lbl, ids in by_label.items():
            cypher = f"MATCH (n:{lbl}) WHERE n.id IN $ids RETURN n, {lbl!r} AS label"
            for row in self.run_read(cypher, {"ids": ids}):
                props = dict(row["n"])
                props["_label"] = row["label"]
                results[props["id"]] = props

        if unlabeled:
            cypher = "MATCH (n) WHERE n.id IN $ids RETURN n, labels(n)[0] AS label"
            for row in self.run_read(cypher, {"ids": unlabeled}):
                props = dict(row["n"])
                props["_label"] = row["label"]
                results[props["id"]] = props

        return results

    def get_paper_venues(self, paper_ids: list[str]) -> dict[str, str]:
        """Return paper_id -> venue_id for a batch of papers."""
        if not paper_ids:
            return {}
        cypher = (
            "MATCH (p:Paper)-[:PUBLISHED_IN]->(v:Venue) "
            "WHERE p.id IN $ids "
            "RETURN p.id AS paper_id, v.id AS venue_id"
        )
        rows = self.run_read(cypher, {"ids": list(set(paper_ids))})
        return {r["paper_id"]: r["venue_id"] for r in rows}

    def get_papers_with_topic(self, paper_ids: list[str], topic_id: str) -> set[str]:
        rows = self.run_read(
            "MATCH (p:Paper)-[r:HAS_TOPIC]->(:Topic {id: $topic}) "
            "WHERE p.id IN $ids AND r.validation_status = 'accepted' "
            "RETURN DISTINCT p.id AS paper_id", {"ids": paper_ids, "topic": topic_id})
        return {r["paper_id"] for r in rows}

    def get_induced_edges(
        self,
        node_ids: list[str],
        relations: list[str] | None = None,
        min_support: int = 1,
        min_weight: float = 0.0,
        limit: int = 1500,
    ) -> list[dict[str, Any]]:
        """Fetch accepted edges whose both endpoints lie in `node_ids`."""
        if not node_ids:
            return []
        valid_rels = validate_relations(relations)
        rel_pattern = "|".join(valid_rels)
        cypher = (
            f"MATCH (s)-[r:{rel_pattern}]->(t) "
            "WHERE s.id IN $ids AND t.id IN $ids "
            "AND (NOT type(r) IN ['COAUTHORED_WITH', 'COLLABORATED_WITH'] OR coalesce(r.support_count, r.support_paper_count, 1) >= $min_support) "
            "AND (NOT type(r) IN ['COAUTHORED_WITH', 'COLLABORATED_WITH'] OR coalesce(r.fractional_weight, 1.0) >= $min_weight) "
            "RETURN r, type(r) AS relation, s.id AS source_id, s.name AS source_name, "
            "labels(s)[0] AS source_label, t.id AS target_id, t.name AS target_name, "
            "labels(t)[0] AS target_label "
            "ORDER BY coalesce(r.fractional_weight, 0.0) DESC, coalesce(r.support_count, 1) DESC, r.edge_id ASC "
            "LIMIT $limit"
        )
        rows = self.run_read(
            cypher,
            {
                "ids": list(set(node_ids)),
                "min_support": max(1, int(min_support)),
                "min_weight": float(min_weight),
                "limit": min(max(1, int(limit)), 2500),
            },
        )
        return self._format_edge_rows(rows)

    def _format_edge_rows(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        formatted = []
        for row in rows:
            rel_props = dict(row["r"])
            relation = row["relation"]
            edge_id = rel_props.get("edge_id", "")
            formatted.append({
                "edge_id": edge_id,
                "relation": relation,
                "source": row["source_id"],
                "target": row["target_id"],
                "source_name": row.get("source_name"),
                "target_name": row.get("target_name"),
                "source_label": row.get("source_label"),
                "target_label": row.get("target_label"),
                "directed": relation not in SYMMETRIC_RELATIONS,
                "symmetric": relation in SYMMETRIC_RELATIONS,
                "evidence_kind": rel_props.get("evidence_kind", "observed"),
                "evidence_ids": list(rel_props.get("evidence_ids", [])),
                "support_count": int(
                    rel_props.get("support_count", rel_props.get("support_paper_count", 1))
                ),
                "fractional_weight": (
                    float(rel_props["fractional_weight"])
                    if "fractional_weight" in rel_props and rel_props["fractional_weight"] is not None
                    else None
                ),
                "method_version": rel_props.get("method_version", ""),
                "graph_version": rel_props.get("graph_version", ""),
                "validation_status": rel_props.get("validation_status", "accepted"),
                "properties": {
                    k: v
                    for k, v in rel_props.items()
                    if k
                    not in {
                        "edge_id",
                        "evidence_kind",
                        "evidence_ids",
                        "method_version",
                        "graph_version",
                        "validation_status",
                        "project",
                    }
                },
            })
        return formatted

    def search_nodes(
        self,
        query: str,
        *,
        labels: list[str] | None = None,
        year_min: int | None = None,
        year_max: int | None = None,
        venue: str | None = None,
        sector: str | None = None,
        limit: int = 30,
    ) -> tuple[dict[str, int], list[dict[str, Any]]]:
        """Full-database search across all 5 labels with grouped counts and relevance sorting."""
        valid_labels = validate_labels(labels)
        q_clean = query.strip()
        q_lower = q_clean.lower()
        q_folded = fold_diacritics(q_clean)
        params: dict[str, Any] = {
            "q": q_lower,
            "q_folded": q_folded,
            "year_min": year_min,
            "year_max": year_max,
            "venue": venue,
            "sector": sector,
            "limit": min(max(1, limit), self.settings.max_search_limit),
        }

        label_filter = " OR ".join(f"n:{lbl}" for lbl in valid_labels)
        where_clauses = [f"({label_filter})"]
        folded_name_expr = _cypher_fold_expr("n.name")

        if q_clean:
            where_clauses.append(
                f"(toLower(n.name) CONTAINS $q "
                f"OR {folded_name_expr} CONTAINS $q_folded "
                "OR toLower(n.id) CONTAINS $q "
                "OR (n.doi IS NOT NULL AND toLower(n.doi) CONTAINS $q) "
                "OR (n.orcid IS NOT NULL AND toLower(n.orcid) CONTAINS $q) "
                "OR (n.openalex_id IS NOT NULL AND toLower(n.openalex_id) CONTAINS $q))"
            )
        if year_min is not None:
            where_clauses.append("(NOT n:Paper OR n.year >= $year_min)")
        if year_max is not None:
            where_clauses.append("(NOT n:Paper OR n.year <= $year_max)")
        if sector:
            where_clauses.append("(NOT n:Organization OR n.sector = $sector)")
        if venue:
            where_clauses.append("(NOT n:Paper OR EXISTS { MATCH (n)-[:PUBLISHED_IN]->(:Venue {id: $venue}) })")

        where_str = " AND ".join(where_clauses)

        count_cypher = f"MATCH (n) WHERE {where_str} RETURN labels(n)[0] AS label, count(n) AS count"
        count_rows = self.run_read(count_cypher, params)
        grouped_counts = {row["label"]: int(row["count"]) for row in count_rows if row.get("label")}

        search_cypher = (
            f"MATCH (n) WHERE {where_str} "
            "WITH n, labels(n)[0] AS label, "
            "CASE "
            "  WHEN $q = '' THEN 2 "
            f"  WHEN toLower(n.id) = $q OR toLower(n.name) = $q OR {folded_name_expr} = $q_folded THEN 0 "
            f"  WHEN toLower(n.name) STARTS WITH $q OR {folded_name_expr} STARTS WITH $q_folded THEN 1 "
            "  ELSE 2 "
            "END AS match_rank "
            "RETURN n, label, match_rank "
            "ORDER BY match_rank ASC, n.name ASC, n.id ASC "
            "LIMIT $limit"
        )
        rows = self.run_read(search_cypher, params)
        items = []
        for row in rows:
            props = dict(row["n"])
            props["_label"] = row["label"]
            props["_match_rank"] = row["match_rank"]
            items.append(props)
        return grouped_counts, items

    def get_node_relation_counts(self, node_id: str) -> dict[str, int]:
        """Count incident edges by relationship type for a node."""
        lbl = label_for_id(node_id)
        match_clause = f"MATCH (n:{lbl} {{id: $id}})-[r]-()" if lbl in ALLOWED_LABELS else "MATCH (n {id: $id})-[r]-()"
        cypher = f"{match_clause} RETURN type(r) AS relation, count(DISTINCT r) AS count"
        rows = self.run_read(cypher, {"id": node_id})
        return {row["relation"]: int(row["count"]) for row in rows}

    def get_nodes_degree_counts(self, node_ids: list[str]) -> dict[str, int]:
        """Count total incident database edges for a batch of node IDs."""
        if not node_ids:
            return {}
        grouped: dict[str, list[str]] = {}
        for nid in node_ids:
            lbl = label_for_id(nid) or ""
            grouped.setdefault(lbl, []).append(nid)
        counts: dict[str, int] = {}
        for lbl, ids in grouped.items():
            match_clause = (
                f"MATCH (n:{lbl}) WHERE n.id IN $ids"
                if lbl in ALLOWED_LABELS
                else "MATCH (n) WHERE n.id IN $ids"
            )
            cypher = (
                f"{match_clause} "
                "OPTIONAL MATCH (n)-[r]-() "
                "RETURN n.id AS id, count(DISTINCT r) AS deg"
            )
            for row in self.run_read(cypher, {"ids": ids}):
                counts[str(row["id"])] = int(row["deg"])
        return counts

    def get_node_connected_groups(self, node_id: str, per_group_limit: int = 15) -> list[dict[str, Any]]:
        """Retrieve grouped incident relationships and neighbor summaries for the Node Inspector."""
        lbl = label_for_id(node_id)
        node_match = f"(n:{lbl} {{id: $id}})" if lbl in ALLOWED_LABELS else "(n {id: $id})"
        cypher = (
            f"MATCH {node_match}-[r]-(m) "
            "WITH type(r) AS relation, "
            "CASE "
            "  WHEN type(r) IN ['COAUTHORED_WITH', 'COLLABORATED_WITH'] THEN 'undirected' "
            "  WHEN startNode(r) = n THEN 'outgoing' "
            "  ELSE 'incoming' "
            "END AS direction, "
            "r.evidence_kind AS evidence_kind, r, m, labels(m)[0] AS neighbor_label "
            "ORDER BY coalesce(r.fractional_weight, 0.0) DESC, coalesce(r.support_count, 1) DESC, "
            "coalesce(m.year, 0) DESC, m.name ASC "
            "WITH relation, direction, evidence_kind, count(*) AS total_count, "
            "collect({ "
            "  edge_id: r.edge_id, "
            "  neighbor_id: m.id, "
            "  neighbor_name: m.name, "
            "  neighbor_label: neighbor_label, "
            "  year: m.year, "
            "  sector: m.sector, "
            "  support_count: coalesce(r.support_count, r.support_paper_count, 1), "
            "  fractional_weight: r.fractional_weight, "
            "  byline_position: r.byline_position, "
            "  cosine_similarity: r.cosine_similarity "
            "})[0..$limit] AS items "
            "RETURN relation, direction, evidence_kind, total_count, items "
            "ORDER BY total_count DESC, relation ASC"
        )
        return self.run_read(cypher, {"id": node_id, "limit": per_group_limit})

    def get_neighborhood(
        self,
        node_id: str,
        *,
        relations: list[str] | None = None,
        node_labels: list[str] | None = None,
        direction: str = "both",
        year_min: int | None = None,
        year_max: int | None = None,
        venue: str | None = None,
        sector: str | None = None,
        min_support: int = 1,
        min_weight: float = 0.0,
        limit: int = 60,
        include_induced_edges: bool = True,
    ) -> tuple[int, list[dict[str, Any]], list[dict[str, Any]]]:
        """Fetch bounded 1-hop neighborhood of `node_id` plus optional induced edges among neighbors."""
        valid_rels = validate_relations(relations)
        valid_labels = validate_labels(node_labels)
        rel_pattern = "|".join(valid_rels)
        lbl = label_for_id(node_id)
        center_match = f"(c:{lbl} {{id: $id}})" if lbl in ALLOWED_LABELS else "(c {id: $id})"

        if direction == "outgoing":
            pattern = f"{center_match}-[r:{rel_pattern}]->(m)"
        elif direction == "incoming":
            pattern = f"{center_match}<-[r:{rel_pattern}]-(m)"
        else:
            pattern = f"{center_match}-[r:{rel_pattern}]-(m)"

        label_filter = " OR ".join(f"m:{tl}" for tl in valid_labels)
        where_clauses = [
            f"({label_filter})",
            "(NOT type(r) IN ['COAUTHORED_WITH', 'COLLABORATED_WITH'] OR coalesce(r.support_count, r.support_paper_count, 1) >= $min_support)",
            "(NOT type(r) IN ['COAUTHORED_WITH', 'COLLABORATED_WITH'] OR coalesce(r.fractional_weight, 1.0) >= $min_weight)",
        ]
        if year_min is not None:
            where_clauses.append("(NOT m:Paper OR m.year >= $year_min)")
        if year_max is not None:
            where_clauses.append("(NOT m:Paper OR m.year <= $year_max)")
        if sector:
            where_clauses.append("(NOT m:Organization OR m.sector = $sector)")
        if venue:
            where_clauses.append("(NOT m:Paper OR EXISTS { MATCH (m)-[:PUBLISHED_IN]->(:Venue {id: $venue}) })")

        where_str = " AND ".join(where_clauses)
        params = {
            "id": node_id,
            "min_support": max(1, int(min_support)),
            "min_weight": float(min_weight),
            "year_min": year_min,
            "year_max": year_max,
            "venue": venue,
            "sector": sector,
            "limit": min(max(1, int(limit)), self.settings.max_neighbor_limit),
        }

        count_cypher = f"MATCH {pattern} WHERE {where_str} RETURN count(DISTINCT r) AS total_edges"
        count_rows = self.run_read(count_cypher, params)
        total_incident = int(count_rows[0]["total_edges"]) if count_rows else 0

        neighbor_cypher = (
            f"MATCH {pattern} WHERE {where_str} "
            "WITH m, labels(m)[0] AS m_label, r, type(r) AS relation, "
            "startNode(r) AS s, endNode(r) AS t "
            "ORDER BY coalesce(r.fractional_weight, 0.0) DESC, "
            "coalesce(r.support_count, r.support_paper_count, 1) DESC, m.id ASC, r.edge_id ASC "
            "LIMIT $limit "
            "RETURN m, m_label, r, relation, s.id AS source_id, s.name AS source_name, "
            "labels(s)[0] AS source_label, t.id AS target_id, t.name AS target_name, "
            "labels(t)[0] AS target_label"
        )
        rows = self.run_read(neighbor_cypher, params)
        neighbor_nodes_map: dict[str, dict[str, Any]] = {}
        for row in rows:
            m_props = dict(row["m"])
            m_props["_label"] = row["m_label"]
            neighbor_nodes_map[m_props["id"]] = m_props

        edges = self._format_edge_rows(rows)
        if include_induced_edges and len(neighbor_nodes_map) > 1:
            all_ids = [node_id, *neighbor_nodes_map.keys()]
            induced = self.get_induced_edges(
                all_ids,
                relations=valid_rels,
                min_support=min_support,
                min_weight=min_weight,
                limit=800,
            )
            seen_eids = {e["edge_id"] for e in edges}
            for ie in induced:
                if ie["edge_id"] not in seen_eids:
                    edges.append(ie)
                    seen_eids.add(ie["edge_id"])

        return total_incident, list(neighbor_nodes_map.values()), edges

    def get_edge_by_id(self, edge_id: str) -> dict[str, Any] | None:
        """Fetch an accepted edge by its deterministic `edge_id`."""
        cypher = (
            "MATCH (s)-[r]->(t) "
            "WHERE r.edge_id = $edge_id "
            "RETURN r, type(r) AS relation, s, labels(s)[0] AS source_label, "
            "t, labels(t)[0] AS target_label "
            "LIMIT 1"
        )
        rows = self.run_read(cypher, {"edge_id": edge_id})
        if not rows:
            return None
        row = rows[0]
        source_node = dict(row["s"])
        source_node["_label"] = row["source_label"]
        target_node = dict(row["t"])
        target_node["_label"] = row["target_label"]
        edge_row = {
            "r": row["r"],
            "relation": row["relation"],
            "source_id": source_node["id"],
            "source_name": source_node.get("name"),
            "source_label": row["source_label"],
            "target_id": target_node["id"],
            "target_name": target_node.get("name"),
            "target_label": row["target_label"],
        }
        formatted_edge = self._format_edge_rows([edge_row])[0]
        return {
            "edge": formatted_edge,
            "source_node": source_node,
            "target_node": target_node,
        }

    def get_edges_by_ids(self, edge_ids: list[str]) -> list[dict[str, Any]]:
        """Fetch a small batch of base edges by their `edge_id` values."""
        if not edge_ids:
            return []
        cypher = (
            "MATCH (s)-[r]->(t) "
            "WHERE r.edge_id IN $edge_ids "
            "RETURN r, type(r) AS relation, s.id AS source_id, s.name AS source_name, "
            "labels(s)[0] AS source_label, t.id AS target_id, t.name AS target_name, "
            "labels(t)[0] AS target_label "
            "LIMIT 50"
        )
        rows = self.run_read(cypher, {"edge_ids": edge_ids[:50]})
        return self._format_edge_rows(rows)

    def resolve_derived_supporting_papers_cypher(
        self, relation: str, source_id: str, target_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Fallback Cypher query to resolve supporting core papers for derived edges if graph.json is absent."""
        if relation == "COAUTHORED_WITH":
            cypher = (
                "MATCH (a:Researcher {id: $source_id})-[:AUTHORED]->(p:Paper)<-[:AUTHORED]-(b:Researcher {id: $target_id}) "
                "WHERE p.is_core = true "
                "OPTIONAL MATCH (p)-[:PUBLISHED_IN]->(v:Venue) "
                "RETURN p, v.name AS venue_name ORDER BY p.year DESC, p.id ASC LIMIT $limit"
            )
        elif relation == "RESEARCHES_TOPIC":
            cypher = (
                "MATCH (r:Researcher {id: $source_id})-[:AUTHORED]->(p:Paper)-[:HAS_TOPIC]->(t:Topic {id: $target_id}) "
                "WHERE p.is_core = true "
                "OPTIONAL MATCH (p)-[:PUBLISHED_IN]->(v:Venue) "
                "RETURN p, v.name AS venue_name ORDER BY p.year DESC, p.id ASC LIMIT $limit"
            )
        elif relation == "CONTRIBUTES_TO_TOPIC":
            cypher = (
                "MATCH (o:Organization {id: $source_id})<-[:AFFILIATED_WITH]-(r:Researcher)-[:AUTHORED]->(p:Paper)-[:HAS_TOPIC]->(t:Topic {id: $target_id}) "
                "WHERE p.is_core = true "
                "OPTIONAL MATCH (p)-[:PUBLISHED_IN]->(v:Venue) "
                "RETURN DISTINCT p, v.name AS venue_name ORDER BY p.year DESC, p.id ASC LIMIT $limit"
            )
        elif relation == "COLLABORATED_WITH":
            cypher = (
                "MATCH (o1:Organization {id: $source_id})<-[:AFFILIATED_WITH]-(r1:Researcher)-[:AUTHORED]->(p:Paper)<-[:AUTHORED]-(r2:Researcher)-[:AFFILIATED_WITH]->(o2:Organization {id: $target_id}) "
                "WHERE p.is_core = true AND r1.id <> r2.id "
                "OPTIONAL MATCH (p)-[:PUBLISHED_IN]->(v:Venue) "
                "RETURN DISTINCT p, v.name AS venue_name ORDER BY p.year DESC, p.id ASC LIMIT $limit"
            )
        else:
            return []

        rows = self.run_read(cypher, {"source_id": source_id, "target_id": target_id, "limit": limit})
        papers = []
        for row in rows:
            p = dict(row["p"])
            papers.append({
                "paper_id": p["id"],
                "title": p.get("name", p["id"]),
                "year": p.get("year"),
                "venue": row.get("venue_name"),
                "doi": p.get("doi"),
                "official_url": p.get("official_url"),
                "pdf_url": p.get("pdf_url"),
                "openalex_id": p.get("openalex_id"),
            })
        return papers

    def find_shortest_path(
        self,
        source_id: str,
        target_id: str,
        *,
        mode: str = "heterogeneous",
        max_hops: int = 3,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Find a bounded shortest path between two entities respecting directional semantics."""
        hops = min(max(1, int(max_hops)), 4)
        s_lbl = label_for_id(source_id)
        t_lbl = label_for_id(target_id)
        s_match = f"(a:{s_lbl} {{id: $source_id}})" if s_lbl in ALLOWED_LABELS else "(a {id: $source_id})"
        t_match = f"(b:{t_lbl} {{id: $target_id}})" if t_lbl in ALLOWED_LABELS else "(b {id: $target_id})"

        if mode == "collaboration":
            rel_pattern = f"-[r:COAUTHORED_WITH|COLLABORATED_WITH|AUTHORED|AFFILIATED_WITH*1..{hops}]-"
        elif mode == "citation_directed":
            rel_pattern = f"-[r:CITES*1..{hops}]->"
        elif mode == "citation_undirected":
            rel_pattern = f"-[r:CITES*1..{hops}]-"
        else:
            all_rels = "|".join(sorted(ALLOWED_RELATIONS))
            rel_pattern = f"-[r:{all_rels}*1..{hops}]-"

        cypher = (
            f"MATCH p = shortestPath({s_match}{rel_pattern}{t_match}) "
            "RETURN [n IN nodes(p) | {props: properties(n), label: labels(n)[0]}] AS path_nodes, "
            "[rel IN relationships(p) | { "
            "  props: properties(rel), "
            "  relation: type(rel), "
            "  source_id: startNode(rel).id, "
            "  source_name: startNode(rel).name, "
            "  source_label: labels(startNode(rel))[0], "
            "  target_id: endNode(rel).id, "
            "  target_name: endNode(rel).name, "
            "  target_label: labels(endNode(rel))[0] "
            "}] AS path_edges "
            "LIMIT 1"
        )
        rows = self.run_read(cypher, {"source_id": source_id, "target_id": target_id})
        if not rows:
            return [], []

        raw_nodes = rows[0]["path_nodes"]
        raw_edges = rows[0]["path_edges"]
        nodes = []
        for item in raw_nodes:
            p = dict(item["props"])
            p["_label"] = item["label"]
            nodes.append(p)

        edge_rows = [
            {
                "r": item["props"],
                "relation": item["relation"],
                "source_id": item["source_id"],
                "source_name": item["source_name"],
                "source_label": item["source_label"],
                "target_id": item["target_id"],
                "target_name": item["target_name"],
                "target_label": item["target_label"],
            }
            for item in raw_edges
        ]
        return nodes, self._format_edge_rows(edge_rows)

    def get_organization_collaboration_subgraph(
        self,
        *,
        sector: str | None = None,
        cross_sector_only: bool = False,
        country_code: str | None = None,
        min_support: int = 1,
        min_weight: float = 0.0,
        include_topics: bool = False,
        limit: int = 80,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Query COLLABORATED_WITH subgraph with sector, cross-sector, and support filters."""
        where_clauses = [
            "coalesce(r.support_count, 1) >= $min_support",
            "(NOT type(r) IN ['COAUTHORED_WITH', 'COLLABORATED_WITH'] OR coalesce(r.fractional_weight, 1.0) >= $min_weight)",
        ]
        if sector:
            where_clauses.append("(a.sector = $sector OR b.sector = $sector)")
        if cross_sector_only:
            where_clauses.append("a.sector <> b.sector")
        if country_code:
            where_clauses.append("(a.country_code = $country_code OR b.country_code = $country_code)")

        where_str = " AND ".join(where_clauses)
        cypher = (
            "MATCH (a:Organization)-[r:COLLABORATED_WITH]->(b:Organization) "
            f"WHERE {where_str} "
            "RETURN a, b, r, 'COLLABORATED_WITH' AS relation, "
            "a.id AS source_id, a.name AS source_name, 'Organization' AS source_label, "
            "b.id AS target_id, b.name AS target_name, 'Organization' AS target_label "
            "ORDER BY coalesce(r.fractional_weight, 0.0) DESC, coalesce(r.support_count, 1) DESC, r.edge_id ASC "
            "LIMIT $edge_limit"
        )
        rows = self.run_read(
            cypher,
            {
                "sector": sector,
                "country_code": country_code,
                "min_support": max(1, int(min_support)),
                "min_weight": float(min_weight),
                "edge_limit": min(max(10, int(limit) * 4), 800),
            },
        )
        nodes_map: dict[str, dict[str, Any]] = {}
        kept_rows = []
        for row in rows:
            a_props = dict(row["a"])
            a_props["_label"] = "Organization"
            b_props = dict(row["b"])
            b_props["_label"] = "Organization"
            if len(nodes_map) >= limit and (a_props["id"] not in nodes_map or b_props["id"] not in nodes_map):
                continue
            nodes_map[a_props["id"]] = a_props
            nodes_map[b_props["id"]] = b_props
            kept_rows.append(row)

        edges = self._format_edge_rows(kept_rows)

        if include_topics and nodes_map:
            topic_cypher = (
                "MATCH (o:Organization)-[r:CONTRIBUTES_TO_TOPIC]->(t:Topic) "
                "WHERE o.id IN $org_ids AND coalesce(r.support_count, 1) >= $min_support "
                "RETURN o, t, r, 'CONTRIBUTES_TO_TOPIC' AS relation, "
                "o.id AS source_id, o.name AS source_name, 'Organization' AS source_label, "
                "t.id AS target_id, t.name AS target_name, 'Topic' AS target_label "
                "ORDER BY r.support_count DESC, r.edge_id ASC LIMIT 120"
            )
            t_rows = self.run_read(
                topic_cypher,
                {"org_ids": list(nodes_map.keys()), "min_support": max(3, int(min_support))},
            )
            for tr in t_rows:
                t_props = dict(tr["t"])
                t_props["_label"] = "Topic"
                nodes_map[t_props["id"]] = t_props
            edges.extend(self._format_edge_rows(t_rows))

        return list(nodes_map.values()), edges

    def get_citation_subgraph(
        self,
        *,
        year_min: int | None = None,
        year_max: int | None = None,
        venue: str | None = None,
        topic_id: str | None = None,
        limit: int = 80,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Query directional within-corpus CITES subgraph with year, venue, and topic filters."""
        where_clauses = ["a.is_core = true AND b.is_core = true"]
        if year_min is not None:
            where_clauses.append("(a.year >= $year_min AND b.year >= $year_min)")
        if year_max is not None:
            where_clauses.append("(a.year <= $year_max AND b.year <= $year_max)")
        if venue:
            where_clauses.append(
                "EXISTS { MATCH (a)-[:PUBLISHED_IN]->(:Venue {id: $venue}) } "
                "AND EXISTS { MATCH (b)-[:PUBLISHED_IN]->(:Venue {id: $venue}) }"
            )
        if topic_id:
            where_clauses.append(
                "(EXISTS { MATCH (a)-[:HAS_TOPIC]->(:Topic {id: $topic_id}) } "
                "AND EXISTS { MATCH (b)-[:HAS_TOPIC]->(:Topic {id: $topic_id}) })"
            )

        where_str = " AND ".join(where_clauses)
        cypher = (
            "MATCH (a:Paper)-[r:CITES]->(b:Paper) "
            f"WHERE {where_str} "
            "RETURN a, b, r, 'CITES' AS relation, "
            "a.id AS source_id, a.name AS source_name, 'Paper' AS source_label, "
            "b.id AS target_id, b.name AS target_name, 'Paper' AS target_label "
            "ORDER BY b.year ASC, a.year DESC, r.edge_id ASC "
            "LIMIT $edge_limit"
        )
        rows = self.run_read(
            cypher,
            {
                "year_min": year_min,
                "year_max": year_max,
                "venue": venue,
                "topic_id": topic_id,
                "edge_limit": min(max(20, int(limit) * 3), 600),
            },
        )
        nodes_map: dict[str, dict[str, Any]] = {}
        kept_rows = []
        for row in rows:
            a_props = dict(row["a"])
            a_props["_label"] = "Paper"
            b_props = dict(row["b"])
            b_props["_label"] = "Paper"
            if len(nodes_map) >= limit and (a_props["id"] not in nodes_map or b_props["id"] not in nodes_map):
                continue
            nodes_map[a_props["id"]] = a_props
            nodes_map[b_props["id"]] = b_props
            kept_rows.append(row)

        return list(nodes_map.values()), self._format_edge_rows(kept_rows)

    def get_heterogeneous_subgraph(
        self,
        *,
        preset: str = "topic_taxonomy_ecosystem",
        relations: list[str] | None = None,
        node_labels: list[str] | None = None,
        year_min: int | None = None,
        year_max: int | None = None,
        venue: str | None = None,
        sector: str | None = None,
        topic_id: str | None = None,
        limit: int = 120,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Build a bounded heterogeneous knowledge graph across up to 5 labels and 10 predicates."""
        nodes_map: dict[str, dict[str, Any]] = {}
        edge_rows: list[dict[str, Any]] = []

        def add_query_rows(cypher: str, params: dict[str, Any]) -> None:
            for row in self.run_read(cypher, params):
                s_props = dict(row["s"])
                s_props["_label"] = row["source_label"]
                t_props = dict(row["t"])
                t_props["_label"] = row["target_label"]
                nodes_map[s_props["id"]] = s_props
                nodes_map[t_props["id"]] = t_props
                edge_rows.append({
                    "r": row["r"],
                    "relation": row["relation"],
                    "source_id": s_props["id"],
                    "source_name": s_props.get("name"),
                    "source_label": row["source_label"],
                    "target_id": t_props["id"],
                    "target_name": t_props.get("name"),
                    "target_label": row["target_label"],
                })

        params = {
            "year_min": year_min or 2021,
            "year_max": year_max or 2025,
            "venue": venue,
            "sector": sector,
            "topic_id": topic_id,
            "limit": min(max(20, int(limit)), 250),
        }

        if preset == "researcher_paper_topic":
            # Researchers -> AUTHORED -> Papers -> HAS_TOPIC -> Topics -> SUBTOPIC_OF -> Parent Topics + PUBLISHED_IN -> Venue
            p_where = ["p.is_core = true", "p.year >= $year_min", "p.year <= $year_max"]
            if venue:
                p_where.append("v.id = $venue")
            if topic_id:
                p_where.append("t.id = $topic_id")
            w_str = " AND ".join(p_where)
            cypher1 = (
                "MATCH (res:Researcher)-[r1:AUTHORED]->(p:Paper)-[r2:HAS_TOPIC]->(t:Topic) "
                "MATCH (p)-[r3:PUBLISHED_IN]->(v:Venue) "
                f"WHERE {w_str} "
                "WITH res, r1, p, r2, t, r3, v ORDER BY r2.cosine_similarity DESC, p.year DESC, p.id ASC, res.id ASC, t.id ASC LIMIT 35 "
                "UNWIND [ "
                "  {s: res, source_label: 'Researcher', r: r1, relation: 'AUTHORED', t: p, target_label: 'Paper'}, "
                "  {s: p, source_label: 'Paper', r: r2, relation: 'HAS_TOPIC', t: t, target_label: 'Topic'}, "
                "  {s: p, source_label: 'Paper', r: r3, relation: 'PUBLISHED_IN', t: v, target_label: 'Venue'} "
                "] AS item "
                "RETURN item.s AS s, item.source_label AS source_label, item.r AS r, "
                "item.relation AS relation, item.t AS t, item.target_label AS target_label"
            )
            add_query_rows(cypher1, params)
            add_query_rows(
                "MATCH (s:Topic)-[r:SUBTOPIC_OF]->(t:Topic) "
                "RETURN s, 'Topic' AS source_label, r, 'SUBTOPIC_OF' AS relation, t, 'Topic' AS target_label ORDER BY r.edge_id ASC",
                {},
            )

        elif preset == "researcher_organization":
            # Researchers -> AFFILIATED_WITH -> Organizations + AUTHORED -> Papers + COLLABORATED_WITH
            o_where = ["p.is_core = true", "p.year >= $year_min", "p.year <= $year_max"]
            if sector:
                o_where.append("o.sector = $sector")
            w_str = " AND ".join(o_where)
            cypher1 = (
                "MATCH (res:Researcher)-[r1:AFFILIATED_WITH]->(o:Organization) "
                "MATCH (res)-[r2:AUTHORED]->(p:Paper)-[r3:PUBLISHED_IN]->(v:Venue) "
                f"WHERE {w_str} AND r1.support_paper_count >= 3 "
                "WITH res, r1, o, r2, p, r3, v ORDER BY r1.support_paper_count DESC, p.year DESC, p.id ASC, res.id ASC, o.id ASC LIMIT 35 "
                "UNWIND [ "
                "  {s: res, source_label: 'Researcher', r: r1, relation: 'AFFILIATED_WITH', t: o, target_label: 'Organization'}, "
                "  {s: res, source_label: 'Researcher', r: r2, relation: 'AUTHORED', t: p, target_label: 'Paper'}, "
                "  {s: p, source_label: 'Paper', r: r3, relation: 'PUBLISHED_IN', t: v, target_label: 'Venue'} "
                "] AS item "
                "RETURN item.s AS s, item.source_label AS source_label, item.r AS r, "
                "item.relation AS relation, item.t AS t, item.target_label AS target_label"
            )
            add_query_rows(cypher1, params)

        elif preset == "academia_industry_topics":
            # Cross-sector Organization <-> COLLABORATED_WITH <-> Organization + CONTRIBUTES_TO_TOPIC -> Topic + SUBTOPIC_OF
            add_query_rows(
                "MATCH (s:Organization)-[r:COLLABORATED_WITH]->(t:Organization) "
                "WHERE s.sector <> t.sector AND r.support_count >= 2 "
                "RETURN s, 'Organization' AS source_label, r, 'COLLABORATED_WITH' AS relation, "
                "t, 'Organization' AS target_label "
                "ORDER BY r.support_count DESC, r.fractional_weight DESC, r.edge_id ASC LIMIT 45",
                {},
            )
            org_ids = [nid for nid in nodes_map if nid.startswith("organization:")]
            if org_ids:
                add_query_rows(
                    "MATCH (s:Organization)-[r:CONTRIBUTES_TO_TOPIC]->(t:Topic) "
                    "WHERE s.id IN $org_ids AND r.support_count >= 5 "
                    "RETURN s, 'Organization' AS source_label, r, 'CONTRIBUTES_TO_TOPIC' AS relation, "
                    "t, 'Topic' AS target_label ORDER BY r.support_count DESC, r.edge_id ASC LIMIT 60",
                    {"org_ids": org_ids},
                )
            add_query_rows(
                "MATCH (s:Topic)-[r:SUBTOPIC_OF]->(t:Topic) "
                "RETURN s, 'Topic' AS source_label, r, 'SUBTOPIC_OF' AS relation, t, 'Topic' AS target_label ORDER BY r.edge_id ASC",
                {},
            )

        elif preset == "paper_venue_citation":
            # Cited papers + citing papers + venues + topics
            c_where = ["s.is_core = true AND t.is_core = true", "s.year >= $year_min AND s.year <= $year_max"]
            if venue:
                c_where.append("v1.id = $venue")
            w_str = " AND ".join(c_where)
            cypher1 = (
                "MATCH (s:Paper)-[r1:CITES]->(t:Paper) "
                "MATCH (s)-[r2:PUBLISHED_IN]->(v1:Venue) "
                "MATCH (t)-[r3:PUBLISHED_IN]->(v2:Venue) "
                "OPTIONAL MATCH (t)-[r4:HAS_TOPIC]->(top:Topic) "
                f"WHERE {w_str} "
                "WITH s, r1, t, r2, v1, r3, v2, r4, top ORDER BY t.year ASC, s.year DESC, s.id ASC, t.id ASC, top.id ASC LIMIT 40 "
                "UNWIND ( "
                "  [ "
                "    {s: s, source_label: 'Paper', r: r1, relation: 'CITES', t: t, target_label: 'Paper'}, "
                "    {s: s, source_label: 'Paper', r: r2, relation: 'PUBLISHED_IN', t: v1, target_label: 'Venue'}, "
                "    {s: t, source_label: 'Paper', r: r3, relation: 'PUBLISHED_IN', t: v2, target_label: 'Venue'} "
                "  ] + CASE WHEN r4 IS NOT NULL THEN [{s: t, source_label: 'Paper', r: r4, relation: 'HAS_TOPIC', t: top, target_label: 'Topic'}] ELSE [] END "
                ") AS item "
                "RETURN item.s AS s, item.source_label AS source_label, item.r AS r, "
                "item.relation AS relation, item.t AS t, item.target_label AS target_label"
            )
            add_query_rows(cypher1, params)

        elif preset == "full_ten_predicates" or preset == "topic_taxonomy_ecosystem":
            # Showcase all 5 entity labels and all 10 relationship predicates in a cohesive bounded subgraph!
            add_query_rows(
                "MATCH (s:Topic)-[r:SUBTOPIC_OF]->(t:Topic) "
                "RETURN s, 'Topic' AS source_label, r, 'SUBTOPIC_OF' AS relation, t, 'Topic' AS target_label ORDER BY r.edge_id ASC",
                {},
            )
            add_query_rows(
                "MATCH (s:Organization)-[r:CONTRIBUTES_TO_TOPIC]->(t:Topic) "
                "RETURN s, 'Organization' AS source_label, r, 'CONTRIBUTES_TO_TOPIC' AS relation, "
                "t, 'Topic' AS target_label ORDER BY r.support_count DESC, r.edge_id ASC LIMIT 25",
                {},
            )
            add_query_rows(
                "MATCH (s:Researcher)-[r:RESEARCHES_TOPIC]->(t:Topic) "
                "RETURN s, 'Researcher' AS source_label, r, 'RESEARCHES_TOPIC' AS relation, "
                "t, 'Topic' AS target_label ORDER BY r.support_count DESC, r.edge_id ASC LIMIT 25",
                {},
            )
            res_ids = [nid for nid in nodes_map if nid.startswith("researcher:")]
            org_ids = [nid for nid in nodes_map if nid.startswith("organization:")]
            if res_ids:
                add_query_rows(
                    "MATCH (s:Researcher)-[r:AFFILIATED_WITH]->(t:Organization) "
                    "WHERE s.id IN $res_ids "
                    "RETURN s, 'Researcher' AS source_label, r, 'AFFILIATED_WITH' AS relation, "
                    "t, 'Organization' AS target_label ORDER BY r.support_paper_count DESC, r.edge_id ASC LIMIT 25",
                    {"res_ids": res_ids},
                )
                add_query_rows(
                    "MATCH (s:Researcher)-[r:COAUTHORED_WITH]->(t:Researcher) "
                    "WHERE s.id IN $res_ids OR t.id IN $res_ids "
                    "RETURN s, 'Researcher' AS source_label, r, 'COAUTHORED_WITH' AS relation, "
                    "t, 'Researcher' AS target_label ORDER BY r.support_count DESC, r.edge_id ASC LIMIT 20",
                    {"res_ids": res_ids},
                )
            org_ids = [nid for nid in nodes_map if nid.startswith("organization:")]
            if org_ids:
                add_query_rows(
                    "MATCH (s:Organization)-[r:COLLABORATED_WITH]->(t:Organization) "
                    "WHERE s.id IN $org_ids AND t.id IN $org_ids "
                    "RETURN s, 'Organization' AS source_label, r, 'COLLABORATED_WITH' AS relation, "
                    "t, 'Organization' AS target_label ORDER BY r.support_count DESC, r.edge_id ASC LIMIT 25",
                    {"org_ids": org_ids},
                )
            add_query_rows(
                "MATCH (p1:Paper)-[rc:CITES]->(p2:Paper) "
                "MATCH (res:Researcher)-[ra:AUTHORED]->(p1)-[rp:PUBLISHED_IN]->(v:Venue) "
                "MATCH (p1)-[rt:HAS_TOPIC]->(top:Topic) "
                "WHERE res.id IN $res_ids "
                "WITH p1, rc, p2, res, ra, rp, v, rt, top LIMIT 15 "
                "UNWIND [ "
                "  {s: p1, source_label: 'Paper', r: rc, relation: 'CITES', t: p2, target_label: 'Paper'}, "
                "  {s: res, source_label: 'Researcher', r: ra, relation: 'AUTHORED', t: p1, target_label: 'Paper'}, "
                "  {s: p1, source_label: 'Paper', r: rp, relation: 'PUBLISHED_IN', t: v, target_label: 'Venue'}, "
                "  {s: p1, source_label: 'Paper', r: rt, relation: 'HAS_TOPIC', t: top, target_label: 'Topic'} "
                "] AS item "
                "RETURN item.s AS s, item.source_label AS source_label, item.r AS r, "
                "item.relation AS relation, item.t AS t, item.target_label AS target_label",
                {"res_ids": [nid for nid in nodes_map if nid.startswith("researcher:")]},
            )
        else:
            # Custom selection of relations and node labels
            valid_rels = validate_relations(relations)
            valid_labels = set(validate_labels(node_labels))
            per_rel_limit = max(8, min(40, int(limit) // max(1, len(valid_rels))))
            for rel in valid_rels:
                add_query_rows(
                    f"MATCH (s)-[r:{rel}]->(t) "
                    "WHERE labels(s)[0] IN $labels AND labels(t)[0] IN $labels "
                    "RETURN s, labels(s)[0] AS source_label, r, type(r) AS relation, "
                    "t, labels(t)[0] AS target_label "
                    "ORDER BY coalesce(r.support_count, r.support_paper_count, 1) DESC, r.edge_id ASC "
                    "LIMIT $lim",
                    {"labels": list(valid_labels), "lim": per_rel_limit},
                )

        # Deduplicate edges by edge_id
        dedup_edges: dict[str, dict[str, Any]] = {}
        for er in self._format_edge_rows(edge_rows):
            dedup_edges[er["edge_id"]] = er
        return list(nodes_map.values()), list(dedup_edges.values())

    def get_authored_paper_ids(self, researcher_id: str) -> set[str]:
        return {r["id"] for r in self.run_read(
            "MATCH (:Researcher {id: $id})-[r:AUTHORED]->(p:Paper) "
            "WHERE r.validation_status = 'accepted' AND p.is_core = true "
            "RETURN DISTINCT p.id AS id", {"id": researcher_id})}

    def compare_entities(self, left_id: str, right_id: str) -> dict[str, Any]:
        """Find direct edges, shared neighbors, and shared papers between two entities."""
        direct_edges = self.get_induced_edges([left_id, right_id], limit=20)
        l_lbl = label_for_id(left_id)
        r_lbl = label_for_id(right_id)
        l_match = f"(a:{l_lbl} {{id: $left_id}})" if l_lbl in ALLOWED_LABELS else "(a {id: $left_id})"
        r_match = f"(b:{r_lbl} {{id: $right_id}})" if r_lbl in ALLOWED_LABELS else "(b {id: $right_id})"

        # Fetch complete distinct ID sets before bounding presentation lists.
        neighbor_sets = []
        for node_id, label in ((left_id, l_lbl), (right_id, r_lbl)):
            match = f"(n:{label} {{id: $id}})" if label in ALLOWED_LABELS else "(n {id: $id})"
            rows = self.run_read(f"MATCH {match}-[r]-(m) WHERE r.validation_status = 'accepted' "
                                 "AND NOT m.id IN $pair RETURN DISTINCT m.id AS id",
                                 {"id": node_id, "pair": [left_id, right_id]})
            neighbor_sets.append({row["id"] for row in rows})
        left_neighbors, right_neighbors = neighbor_sets
        shared_ids = left_neighbors & right_neighbors
        shared_neighbors = list(self.get_nodes_by_ids(sorted(shared_ids)[:30]).values())

        # Check shared papers (either direct AUTHORED or via AFFILIATED_WITH -> AUTHORED)
        shared_papers: list[dict[str, Any]] = []
        if l_lbl == "Researcher" and r_lbl == "Researcher":
            shared_papers = self.resolve_derived_supporting_papers_cypher("COAUTHORED_WITH", left_id, right_id, limit=15)
        elif l_lbl == "Organization" and r_lbl == "Organization":
            shared_papers = self.resolve_derived_supporting_papers_cypher("COLLABORATED_WITH", left_id, right_id, limit=15)

        return {
            "direct_edges": direct_edges,
            "shared_neighbors": shared_neighbors,
            "neighbor_sets": {"shared": sorted(shared_ids),
                              "left_only": sorted(left_neighbors - right_neighbors),
                              "right_only": sorted(right_neighbors - left_neighbors)},
            "shared_papers": shared_papers,
        }

    def query_table_nodes(
        self,
        *,
        label: str | None = None,
        query: str = "",
        year_min: int | None = None,
        year_max: int | None = None,
        sector: str | None = None,
        venue: str | None = None,
        sort_by: str = "name",
        sort_order: str = "asc",
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[int, list[dict[str, Any]]]:
        """Server-side paginated node table query."""
        valid_labels = validate_labels([label] if label else None)
        label_clause = " OR ".join(f"n:{lbl}" for lbl in valid_labels)
        where_clauses = [f"({label_clause})"]
        q_clean = query.strip().lower()
        q_folded = fold_diacritics(query)
        folded_name_expr = _cypher_fold_expr("n.name")
        if q_clean:
            where_clauses.append(
                f"(toLower(n.name) CONTAINS $q OR {folded_name_expr} CONTAINS $q_folded OR toLower(n.id) CONTAINS $q)"
            )
        if year_min is not None:
            where_clauses.append("(NOT n:Paper OR n.year >= $year_min)")
        if year_max is not None:
            where_clauses.append("(NOT n:Paper OR n.year <= $year_max)")
        if sector:
            where_clauses.append("(NOT n:Organization OR n.sector = $sector)")
        if venue:
            where_clauses.append("(NOT n:Paper OR EXISTS { MATCH (n)-[:PUBLISHED_IN]->(:Venue {id: $venue}) })")

        where_str = " AND ".join(where_clauses)
        order_dir = "DESC" if sort_order.lower() == "desc" else "ASC"
        order_expr = {
            "name": f"n.name {order_dir}, n.id ASC",
            "id": f"n.id {order_dir}",
            "year": f"coalesce(n.year, 0) {order_dir}, n.name ASC",
            "sector": f"coalesce(n.sector, 'zzz') {order_dir}, n.name ASC",
        }.get(sort_by, f"n.name {order_dir}, n.id ASC")

        safe_size = min(max(1, int(page_size)), self.settings.max_table_page_size)
        safe_page = max(1, int(page))
        skip = (safe_page - 1) * safe_size

        params = {
            "q": q_clean,
            "q_folded": q_folded,
            "year_min": year_min,
            "year_max": year_max,
            "sector": sector,
            "venue": venue,
            "skip": skip,
            "limit": safe_size,
        }
        cnt_rows = self.run_read(f"MATCH (n) WHERE {where_str} RETURN count(n) AS total", params)
        total = int(cnt_rows[0]["total"]) if cnt_rows else 0

        rows = self.run_read(
            f"MATCH (n) WHERE {where_str} RETURN n, labels(n)[0] AS label ORDER BY {order_expr} SKIP $skip LIMIT $limit",
            params,
        )
        items = []
        for row in rows:
            p = dict(row["n"])
            p["_label"] = row["label"]
            items.append(p)
        return total, items

    def query_table_edges(
        self,
        *,
        relation: str | None = None,
        evidence_kind: str | None = None,
        query: str = "",
        min_support: int = 1,
        min_weight: float = 0.0,
        sort_by: str = "support_count",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[int, list[dict[str, Any]]]:
        """Server-side paginated edge table query."""
        valid_rels = validate_relations([relation] if relation else None)
        rel_pattern = "|".join(valid_rels)
        where_clauses = [
            "(NOT type(r) IN ['COAUTHORED_WITH', 'COLLABORATED_WITH'] OR coalesce(r.support_count, r.support_paper_count, 1) >= $min_support)",
            "(NOT type(r) IN ['COAUTHORED_WITH', 'COLLABORATED_WITH'] OR coalesce(r.fractional_weight, 1.0) >= $min_weight)",
        ]
        if evidence_kind:
            where_clauses.append("r.evidence_kind = $evidence_kind")
        q_clean = query.strip().lower()
        q_folded = fold_diacritics(query)
        folded_s_expr = _cypher_fold_expr("s.name")
        folded_t_expr = _cypher_fold_expr("t.name")
        if q_clean:
            where_clauses.append(
                f"(toLower(s.name) CONTAINS $q OR {folded_s_expr} CONTAINS $q_folded "
                f"OR toLower(t.name) CONTAINS $q OR {folded_t_expr} CONTAINS $q_folded "
                "OR toLower(r.edge_id) CONTAINS $q)"
            )

        where_str = " AND ".join(where_clauses)
        order_dir = "DESC" if sort_order.lower() == "desc" else "ASC"
        order_expr = {
            "support_count": f"coalesce(r.support_count, r.support_paper_count, 1) {order_dir}, r.edge_id ASC",
            "fractional_weight": f"coalesce(r.fractional_weight, 0.0) {order_dir}, r.edge_id ASC",
            "relation": f"type(r) {order_dir}, r.edge_id ASC",
            "edge_id": f"r.edge_id {order_dir}",
        }.get(sort_by, f"coalesce(r.support_count, 1) {order_dir}, r.edge_id ASC")

        safe_size = min(max(1, int(page_size)), self.settings.max_table_page_size)
        safe_page = max(1, int(page))
        skip = (safe_page - 1) * safe_size

        params = {
            "evidence_kind": evidence_kind,
            "q": q_clean,
            "q_folded": q_folded,
            "min_support": max(1, int(min_support)),
            "min_weight": float(min_weight),
            "skip": skip,
            "limit": safe_size,
        }
        cnt_rows = self.run_read(
            f"MATCH (s)-[r:{rel_pattern}]->(t) WHERE {where_str} RETURN count(r) AS total",
            params,
        )
        total = int(cnt_rows[0]["total"]) if cnt_rows else 0

        rows = self.run_read(
            f"MATCH (s)-[r:{rel_pattern}]->(t) WHERE {where_str} "
            "RETURN r, type(r) AS relation, s.id AS source_id, s.name AS source_name, "
            "labels(s)[0] AS source_label, t.id AS target_id, t.name AS target_name, "
            f"labels(t)[0] AS target_label ORDER BY {order_expr} SKIP $skip LIMIT $limit",
            params,
        )
        return total, self._format_edge_rows(rows)

