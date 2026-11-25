"""Closed, typed, read-only tool layer for GraphRAG and multi-hop reasoning (spec §6.3).

Tools:
  find, neighbors, path, papers, aggregate, rank, community, community_report, trend

Every graph query uses parameterized, read-only Cypher (neo4j.READ_ACCESS, bounded
timeouts and LIMITs) or an in-memory graph backend for Neo4j-free tests. Analytical
tools read precomputed artifacts under ``reports/final-exam/analysis-v2/`` and
``reports/final-exam/rag-v1/``. Every result carries evidence IDs and paper IDs.
"""

from __future__ import annotations

from collections import Counter, defaultdict, deque
import csv
import gzip
import json
import os
from pathlib import Path
import re
from typing import Any, Callable, Protocol

from dotenv import load_dotenv
import neo4j
from neo4j import Query
from pydantic import BaseModel, Field

from scientific_network.enrich.load5 import ENRICHED_BOLT_PORT

ALLOWED_LABELS: frozenset[str] = frozenset({
    "Researcher", "Paper", "Organization", "Topic", "Venue", "Method", "Task", "Dataset",
})

ALLOWED_RELATIONS: frozenset[str] = frozenset({
    "AUTHORED", "AFFILIATED_WITH", "PUBLISHED_IN", "CITES", "HAS_TOPIC", "SUBTOPIC_OF",
    "COAUTHORED_WITH", "COLLABORATED_WITH", "RESEARCHES_TOPIC", "CONTRIBUTES_TO_TOPIC",
    "USES_METHOD", "ADDRESSES_TASK", "USES_DATASET", "APPLIED_TO", "EVALUATED_ON",
    "PART_OF", "MEMBER_OF", "RELATED_TO",
})

COOCCURRENCE_PAIRS: dict[tuple[str, str], tuple[str, str, str]] = {
    ("Method", "Task"): ("USES_METHOD", "ADDRESSES_TASK", "APPLIED_TO"),
    ("Task", "Method"): ("ADDRESSES_TASK", "USES_METHOD", "APPLIED_TO"),
    ("Method", "Dataset"): ("USES_METHOD", "USES_DATASET", "EVALUATED_ON"),
    ("Dataset", "Method"): ("USES_DATASET", "USES_METHOD", "EVALUATED_ON"),
    ("Task", "Dataset"): ("ADDRESSES_TASK", "USES_DATASET", "EVALUATED_ON"),
    ("Dataset", "Task"): ("USES_DATASET", "ADDRESSES_TASK", "EVALUATED_ON"),
}


class ToolResult(BaseModel):
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    paper_ids: list[str] = Field(default_factory=list)
    subgraph_nodes: list[dict[str, Any]] = Field(default_factory=list)
    subgraph_edges: list[dict[str, Any]] = Field(default_factory=list)
    source_kind: str = "graph"
    ambiguous: bool = False
    empty: bool = False
    note: str = ""


class GraphBackend(Protocol):
    def find_nodes(self, entity_type: str | None, text: str, limit: int = 10) -> list[dict[str, Any]]: ...
    def get_nodes_by_ids(self, node_ids: list[str]) -> list[dict[str, Any]]: ...
    def researcher_context(self, researcher_ids: list[str]) -> dict[str, dict[str, Any]]: ...
    def neighbors(
        self,
        node_id: str,
        *,
        predicates: list[str] | None = None,
        target_labels: list[str] | None = None,
        direction: str = "both",
        year_min: int | None = None,
        year_max: int | None = None,
        venue: str | None = None,
        min_support: int = 1,
        limit: int = 50,
    ) -> dict[str, Any]: ...
    def cooccurrence_partners(
        self,
        entity_id: str,
        entity_label: str,
        partner_label: str,
        *,
        year_min: int | None = None,
        year_max: int | None = None,
        venue: str | None = None,
        min_papers: int = 1,
        limit: int = 50,
    ) -> list[dict[str, Any]]: ...
    def shortest_path(
        self,
        source_id: str,
        target_id: str,
        *,
        max_len: int = 4,
        predicates: list[str] | None = None,
    ) -> dict[str, Any]: ...
    def query_papers(self, filters: dict[str, Any], limit: int = 50) -> list[dict[str, Any]]: ...
    def aggregate_papers(
        self,
        entity_ids: list[str],
        *,
        by: str,
        filters: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]: ...
    def year_totals(self, filters: dict[str, Any] | None = None) -> dict[int, int]: ...


def _parse_surfaces(raw: Any) -> list[str]:
    if isinstance(raw, dict):
        return [str(k) for k in raw]
    if isinstance(raw, list):
        return [str(x) for x in raw]
    if isinstance(raw, str) and raw.startswith("{"):
        try:
            d = json.loads(raw)
            if isinstance(d, dict):
                return [str(k) for k in d]
        except json.JSONDecodeError:
            pass
    return []


def _stem_variants(text: str) -> set[str]:
    norm = re.sub(r"[-_]+", " ", text.strip().lower())
    t = " ".join(norm.split())
    out = {t, " ".join(text.strip().lower().split())}
    for cand in list(out):
        if cand.endswith("s") and not cand.endswith(("ss", "us", "is")):
            out.add(cand[:-1])
        else:
            out.add(cand + "s")
    for suffix in (" tasks", " task", " methods", " method", " models", " model"):
        if t.endswith(suffix) and len(t) > len(suffix) + 2:
            stem = t[: -len(suffix)].strip()
            out.add(stem)
            out.add(stem + "s")
    return out


def _validate_label(label: str | None) -> str | None:
    if label is None:
        return None
    if label not in ALLOWED_LABELS:
        raise ValueError(f"Unsupported entity_type/label: {label!r}")
    return label


def _validate_predicates(predicates: list[str] | None) -> list[str] | None:
    if not predicates:
        return None
    cleaned = []
    for p in predicates:
        if p not in ALLOWED_RELATIONS:
            raise ValueError(f"Unsupported relationship predicate: {p!r}")
        if p not in cleaned:
            cleaned.append(p)
    return cleaned


class Neo4jToolBackend:
    """Read-only Neo4j backend (default_access_mode=READ_ACCESS, query timeout, LIMIT caps)."""

    def __init__(
        self,
        uri: str | None = None,
        username: str | None = None,
        password: str | None = None,
        database: str = "neo4j",
        timeout: float = 15.0,
    ) -> None:
        load_dotenv(override=False)
        self.uri = uri or os.environ.get("EXPLORER_ENRICHED_NEO4J_URI") or f"bolt://127.0.0.1:{ENRICHED_BOLT_PORT}"
        self.username = username or os.environ.get("NEO4J_USERNAME", "neo4j")
        self.password = password if password is not None else os.environ.get("NEO4J_PASSWORD", "")
        self.database = database
        self.timeout = timeout
        self._driver: neo4j.Driver | None = None

    def _get_driver(self) -> neo4j.Driver:
        if self._driver is None:
            if not self.password:
                raise RuntimeError("NEO4J_PASSWORD is not configured.")
            self._driver = neo4j.GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
                connection_timeout=10.0,
                max_connection_pool_size=8,
            )
        return self._driver

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def run_read(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        driver = self._get_driver()
        q = Query(cypher, timeout=self.timeout)
        with driver.session(database=self.database, default_access_mode=neo4j.READ_ACCESS) as session:
            return [dict(r) for r in session.run(q, parameters=params or {})]

    def find_nodes(self, entity_type: str | None, text: str, limit: int = 10) -> list[dict[str, Any]]:
        label = _validate_label(entity_type)
        lim = max(1, min(int(limit), 50))
        q_low = " ".join(re.sub(r"[-_]+", " ", text.strip().lower()).split())
        variants = sorted(_stem_variants(text))
        lab_expr = f":{label}" if label else ""
        # Exact/key/surface/substring search via parameterized Cypher
        cypher = (
            f"MATCH (n{lab_expr}) "
            "WHERE toLower(coalesce(n.name, '')) IN $variants "
            "   OR toLower(coalesce(n.key, '')) IN $variants "
            "   OR toLower(coalesce(n.name, '')) CONTAINS $q_low "
            "   OR toLower(coalesce(n.surfaces, '')) CONTAINS $q_low "
            "RETURN n.id AS id, labels(n)[0] AS label, n.name AS name, n.key AS key, "
            "       n.surfaces AS surfaces, n.year AS year, n.sector AS sector, n.country_code AS country_code, "
            "       n.openalex_id AS openalex_id, coalesce(n.paper_count, 0) AS paper_count, "
            "       n.wikipedia_url AS wikipedia_url "
            "ORDER BY "
            "  CASE WHEN toLower(coalesce(n.name, '')) = $q_low THEN 0 "
            "       WHEN toLower(coalesce(n.name, '')) IN $variants OR toLower(coalesce(n.key, '')) IN $variants THEN 1 "
            "       ELSE 2 END, "
            "  paper_count DESC, id ASC "
            "LIMIT $limit"
        )
        rows = self.run_read(cypher, {"q_low": q_low, "variants": variants, "limit": lim})
        for r in rows:
            r["surfaces"] = _parse_surfaces(r.get("surfaces"))
        return rows

    def get_nodes_by_ids(self, node_ids: list[str]) -> list[dict[str, Any]]:
        if not node_ids:
            return []
        rows = self.run_read(
            "MATCH (n) WHERE n.id IN $ids "
            "RETURN n.id AS id, labels(n)[0] AS label, n.name AS name, n.year AS year, "
            "       n.sector AS sector, n.country_code AS country_code, n.wikipedia_url AS wikipedia_url, "
            "       coalesce(n.paper_count, 0) AS paper_count",
            {"ids": list(dict.fromkeys(node_ids))[:100]},
        )
        return rows

    def researcher_context(self, researcher_ids: list[str]) -> dict[str, dict[str, Any]]:
        if not researcher_ids:
            return {}
        rows = self.run_read(
            "MATCH (r:Researcher) WHERE r.id IN $ids "
            "OPTIONAL MATCH (r)-[:AFFILIATED_WITH]->(o:Organization) "
            "OPTIONAL MATCH (r)-[:AUTHORED]->(p:Paper) "
            "WITH r, collect(DISTINCT o.name)[0..3] AS orgs, count(DISTINCT p) AS papers "
            "RETURN r.id AS id, orgs, papers",
            {"ids": researcher_ids[:25]},
        )
        return {r["id"]: {"affiliations": r["orgs"], "paper_count": int(r["papers"])} for r in rows}

    def neighbors(
        self,
        node_id: str,
        *,
        predicates: list[str] | None = None,
        target_labels: list[str] | None = None,
        direction: str = "both",
        year_min: int | None = None,
        year_max: int | None = None,
        venue: str | None = None,
        min_support: int = 1,
        limit: int = 50,
    ) -> dict[str, Any]:
        preds = _validate_predicates(predicates)
        t_labs = [_validate_label(l) for l in (target_labels or []) if l]
        lim = max(1, min(int(limit), 250))

        center_rows = self.run_read(
            "MATCH (c {id: $id}) RETURN c.id AS id, labels(c)[0] AS label, c.name AS name, c.year AS year, c.sector AS sector LIMIT 1",
            {"id": node_id},
        )
        if not center_rows:
            return {"center": None, "rows": []}
        center = center_rows[0]

        rel_pat = "|".join(preds) if preds else "|".join(sorted(ALLOWED_RELATIONS))
        if direction == "outgoing":
            pat = f"-[r:{rel_pat}]->"
        elif direction == "incoming":
            pat = f"<-[r:{rel_pat}]-"
        else:
            pat = f"-[r:{rel_pat}]-"

        where_parts = ["coalesce(r.support_count, 1) >= $min_support"]
        params: dict[str, Any] = {"id": node_id, "min_support": int(min_support), "limit": lim}
        if t_labs:
            where_parts.append("labels(nb)[0] IN $target_labels")
            params["target_labels"] = t_labs
        if year_min is not None:
            where_parts.append("(NOT 'Paper' IN labels(nb) OR toInteger(nb.year) >= $year_min)")
            params["year_min"] = int(year_min)
        if year_max is not None:
            where_parts.append("(NOT 'Paper' IN labels(nb) OR toInteger(nb.year) <= $year_max)")
            params["year_max"] = int(year_max)
        if venue:
            where_parts.append("(NOT 'Paper' IN labels(nb) OR EXISTS { MATCH (nb)-[:PUBLISHED_IN]->(v:Venue) WHERE toLower(v.name) CONTAINS $venue_q OR v.id = $venue_id })")
            params["venue_q"] = venue.strip().lower()
            params["venue_id"] = f"venue:{venue.strip().lower()}"

        cypher = (
            f"MATCH (c {{id: $id}}){pat}(nb) "
            f"WHERE {' AND '.join(where_parts)} "
            "RETURN c.id AS center_id, type(r) AS relation, startNode(r).id AS source_id, endNode(r).id AS target_id, "
            "       r.edge_id AS edge_id, coalesce(r.support_count, 1) AS support_count, "
            "       r.fractional_weight AS fractional_weight, r.evidence_ids AS evidence_ids, "
            "       r.support_paper_ids AS support_paper_ids, r.evidence_kind AS evidence_kind, "
            "       nb.id AS neighbor_id, labels(nb)[0] AS neighbor_label, nb.name AS neighbor_name, "
            "       nb.year AS neighbor_year, nb.sector AS neighbor_sector, nb.country_code AS neighbor_country_code "
            "ORDER BY support_count DESC, neighbor_id ASC "
            "LIMIT $limit"
        )
        rows = self.run_read(cypher, params)
        return {"center": center, "rows": rows}

    def cooccurrence_partners(
        self,
        entity_id: str,
        entity_label: str,
        partner_label: str,
        *,
        year_min: int | None = None,
        year_max: int | None = None,
        venue: str | None = None,
        min_papers: int = 1,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        _validate_label(entity_label)
        _validate_label(partner_label)
        spec = COOCCURRENCE_PAIRS.get((entity_label, partner_label))
        if spec is None:
            return []
        rel_in, rel_out, _ = spec
        lim = max(1, min(int(limit), 200))
        where_parts = []
        params: dict[str, Any] = {"id": entity_id, "min_papers": int(min_papers), "limit": lim}
        if year_min is not None:
            where_parts.append("toInteger(p.year) >= $year_min")
            params["year_min"] = int(year_min)
        if year_max is not None:
            where_parts.append("toInteger(p.year) <= $year_max")
            params["year_max"] = int(year_max)
        if venue:
            where_parts.append("EXISTS { MATCH (p)-[:PUBLISHED_IN]->(v:Venue) WHERE toLower(v.name) CONTAINS $venue_q OR v.id = $venue_id }")
            params["venue_q"] = venue.strip().lower()
            params["venue_id"] = f"venue:{venue.strip().lower()}"
        where_clause = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
        cypher = (
            f"MATCH (a:{entity_label} {{id: $id}})<-[:{rel_in}]-(p:Paper)-[:{rel_out}]->(b:{partner_label}) "
            f"{where_clause} "
            "WITH b, collect(DISTINCT p.id) AS paper_ids, collect(DISTINCT toInteger(p.year)) AS years "
            "WHERE size(paper_ids) >= $min_papers "
            "RETURN b.id AS id, labels(b)[0] AS label, b.name AS name, size(paper_ids) AS shared_papers, "
            "       paper_ids[0..25] AS paper_ids, years "
            "ORDER BY shared_papers DESC, id ASC LIMIT $limit"
        )
        return self.run_read(cypher, params)

    def shortest_path(
        self,
        source_id: str,
        target_id: str,
        *,
        max_len: int = 4,
        predicates: list[str] | None = None,
    ) -> dict[str, Any]:
        preds = _validate_predicates(predicates)
        hops = max(1, min(int(max_len), 4))
        rel_pat = ("|" .join(preds)) if preds else "|".join(sorted(ALLOWED_RELATIONS))
        cypher = (
            f"MATCH (a {{id: $src}}), (b {{id: $dst}}), "
            f"p = shortestPath((a)-[r:{rel_pat}*1..{hops}]-(b)) "
            "RETURN [n IN nodes(p) | {id: n.id, label: labels(n)[0], name: n.name, year: n.year}] AS nodes, "
            "       [e IN relationships(p) | {edge_id: e.edge_id, relation: type(e), source: startNode(e).id, target: endNode(e).id, "
            "                                    support_count: coalesce(e.support_count, 1), evidence_ids: e.evidence_ids}] AS edges "
            "LIMIT 1"
        )
        rows = self.run_read(cypher, {"src": source_id, "dst": target_id})
        if not rows:
            return {"found": False, "nodes": [], "edges": []}
        return {"found": True, "nodes": rows[0]["nodes"], "edges": rows[0]["edges"]}

    def query_papers(self, filters: dict[str, Any], limit: int = 50) -> list[dict[str, Any]]:
        lim = max(1, min(int(limit), 200))
        match_parts = ["(p:Paper)"]
        where_parts = []
        params: dict[str, Any] = {"limit": lim}
        if filters.get("topic_id"):
            match_parts.append("(p)-[:HAS_TOPIC]->(:Topic {id: $topic_id})")
            params["topic_id"] = filters["topic_id"]
        if filters.get("method_id"):
            match_parts.append("(p)-[:USES_METHOD]->(:Method {id: $method_id})")
            params["method_id"] = filters["method_id"]
        if filters.get("task_id"):
            match_parts.append("(p)-[:ADDRESSES_TASK]->(:Task {id: $task_id})")
            params["task_id"] = filters["task_id"]
        if filters.get("dataset_id"):
            match_parts.append("(p)-[:USES_DATASET]->(:Dataset {id: $dataset_id})")
            params["dataset_id"] = filters["dataset_id"]
        if filters.get("researcher_id"):
            match_parts.append("(:Researcher {id: $researcher_id})-[:AUTHORED]->(p)")
            params["researcher_id"] = filters["researcher_id"]
        if filters.get("organization_id"):
            match_parts.append("(:Organization {id: $organization_id})<-[:AFFILIATED_WITH]-(:Researcher)-[:AUTHORED]->(p)")
            params["organization_id"] = filters["organization_id"]
        if filters.get("venue"):
            match_parts.append("(p)-[:PUBLISHED_IN]->(v:Venue)")
            where_parts.append("(toLower(v.name) CONTAINS $venue_q OR v.id = $venue_id)")
            params["venue_q"] = str(filters["venue"]).strip().lower()
            params["venue_id"] = f"venue:{str(filters['venue']).strip().lower()}"
        if filters.get("year_min") is not None:
            where_parts.append("toInteger(p.year) >= $year_min")
            params["year_min"] = int(filters["year_min"])
        if filters.get("year_max") is not None:
            where_parts.append("toInteger(p.year) <= $year_max")
            params["year_max"] = int(filters["year_max"])
        if filters.get("query_text"):
            where_parts.append("toLower(coalesce(p.name, '')) CONTAINS $q_low")
            params["q_low"] = str(filters["query_text"]).strip().lower()

        cypher = (
            "MATCH " + ", ".join(match_parts) + " "
            + (("WHERE " + " AND ".join(where_parts) + " ") if where_parts else "")
            + "OPTIONAL MATCH (p)-[:PUBLISHED_IN]->(pv:Venue) "
            "OPTIONAL MATCH (citing:Paper)-[:CITES]->(p) "
            "WITH DISTINCT p, pv, count(DISTINCT citing) AS in_citations "
            "RETURN p.id AS id, p.name AS title, toInteger(p.year) AS year, pv.id AS venue_id, pv.name AS venue, "
            "       p.doi AS doi, p.official_url AS official_url, in_citations "
            "ORDER BY in_citations DESC, year DESC, id ASC LIMIT $limit"
        )
        return self.run_read(cypher, params)

    def aggregate_papers(
        self,
        entity_ids: list[str],
        *,
        by: str,
        filters: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        lim = max(1, min(int(limit), 250))
        flt = filters or {}
        params: dict[str, Any] = {"entity_ids": list(entity_ids)[:200], "limit": lim}
        extra_match = []
        where_parts = []
        if flt.get("topic_id"):
            extra_match.append("(p)-[:HAS_TOPIC]->(:Topic {id: $topic_id})")
            params["topic_id"] = flt["topic_id"]
        if flt.get("method_id"):
            extra_match.append("(p)-[:USES_METHOD]->(:Method {id: $method_id})")
            params["method_id"] = flt["method_id"]
        if flt.get("task_id"):
            extra_match.append("(p)-[:ADDRESSES_TASK]->(:Task {id: $task_id})")
            params["task_id"] = flt["task_id"]
        if flt.get("dataset_id"):
            extra_match.append("(p)-[:USES_DATASET]->(:Dataset {id: $dataset_id})")
            params["dataset_id"] = flt["dataset_id"]
        if flt.get("year_min") is not None:
            where_parts.append("toInteger(p.year) >= $year_min")
            params["year_min"] = int(flt["year_min"])
        if flt.get("year_max") is not None:
            where_parts.append("toInteger(p.year) <= $year_max")
            params["year_max"] = int(flt["year_max"])

        # Anchor papers through entity_ids (Paper, Organization, Researcher, Topic, Method, Task, Dataset)
        if entity_ids:
            if all(i.startswith("paper:") for i in entity_ids):
                anchor = "MATCH (p:Paper) WHERE p.id IN $entity_ids "
            elif all(i.startswith("organization:") for i in entity_ids):
                anchor = (
                    "MATCH (e:Organization) WHERE e.id IN $entity_ids "
                    "MATCH (e)<-[:AFFILIATED_WITH]-(:Researcher)-[:AUTHORED]->(p:Paper) "
                )
            else:
                anchor = "MATCH (e) WHERE e.id IN $entity_ids MATCH (e)-[:AUTHORED|HAS_TOPIC|USES_METHOD|ADDRESSES_TASK|USES_DATASET]-(p:Paper) "
        else:
            anchor = "MATCH (p:Paper) "

        extra_clause = ("MATCH " + ", ".join(extra_match) + " ") if extra_match else ""
        where_clause = ("WHERE " + " AND ".join(where_parts) + " ") if where_parts else ""

        if by == "year":
            group_cypher = (
                f"{anchor}{extra_clause}{where_clause}"
                "WITH toInteger(p.year) AS key, collect(DISTINCT p.id) AS pids "
                "RETURN key AS group_key, toString(key) AS label, size(pids) AS paper_count, pids[0..15] AS paper_ids "
                "ORDER BY key ASC LIMIT $limit"
            )
        elif by == "organization_year":
            params["limit"] = max(lim, len(entity_ids) * 6, 300)
            # Also returns org total papers per year so caller can compute org-specific share & growth
            if all(i.startswith("organization:") for i in entity_ids):
                group_cypher = (
                    "MATCH (o:Organization) WHERE o.id IN $entity_ids "
                    "MATCH (o)<-[:AFFILIATED_WITH]-(:Researcher)-[:AUTHORED]->(p:Paper) "
                    + extra_clause + where_clause +
                    "WITH o, toInteger(p.year) AS yr, collect(DISTINCT p.id) AS pids "
                    "RETURN o.id AS entity_id, o.name AS entity_name, yr AS year, size(pids) AS paper_count, pids[0..10] AS paper_ids "
                    "ORDER BY o.id ASC, yr ASC LIMIT $limit"
                )
            else:
                group_cypher = (
                    f"{anchor}{extra_clause}{where_clause}"
                    "MATCH (p)<-[:AUTHORED]-(:Researcher)-[:AFFILIATED_WITH]->(o:Organization) "
                    "WITH o, toInteger(p.year) AS yr, collect(DISTINCT p.id) AS pids "
                    "RETURN o.id AS entity_id, o.name AS entity_name, yr AS year, size(pids) AS paper_count, pids[0..10] AS paper_ids "
                    "ORDER BY paper_count DESC, o.id ASC LIMIT $limit"
                )
        elif by in ("topic", "method", "task", "dataset", "organization", "researcher", "venue"):
            rel_target = {
                "topic": "(p)-[:HAS_TOPIC]->(g:Topic)",
                "method": "(p)-[:USES_METHOD]->(g:Method)",
                "task": "(p)-[:ADDRESSES_TASK]->(g:Task)",
                "dataset": "(p)-[:USES_DATASET]->(g:Dataset)",
                "venue": "(p)-[:PUBLISHED_IN]->(g:Venue)",
                "organization": "(p)<-[:AUTHORED]-(:Researcher)-[:AFFILIATED_WITH]->(g:Organization)",
                "researcher": "(p)<-[:AUTHORED]-(g:Researcher)",
            }[by]
            group_cypher = (
                f"{anchor}{extra_clause}{where_clause}"
                f"MATCH {rel_target} "
                "WITH g, collect(DISTINCT p.id) AS pids "
                "RETURN g.id AS group_key, g.name AS label, size(pids) AS paper_count, pids[0..15] AS paper_ids "
                "ORDER BY paper_count DESC, g.id ASC LIMIT $limit"
            )
        else:
            raise ValueError(f"Unsupported aggregate grouping {by!r}")
        return self.run_read(group_cypher, params)

    def year_totals(self, filters: dict[str, Any] | None = None) -> dict[int, int]:
        rows = self.run_read(
            "MATCH (p:Paper) WHERE p.year IS NOT NULL RETURN toInteger(p.year) AS year, count(p) AS cnt ORDER BY year"
        )
        return {int(r["year"]): int(r["cnt"]) for r in rows}


class InMemoryGraphBackend:
    """Neo4j-free in-memory graph backend over a graph.json dictionary for fast offline tests."""

    def __init__(self, graph: dict[str, Any]) -> None:
        self.nodes: dict[str, dict[str, Any]] = {n["id"]: n for n in graph.get("nodes", [])}
        self.edges: list[dict[str, Any]] = list(graph.get("edges", []))
        self.out_edges: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.in_edges: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.paper_venue: dict[str, tuple[str, str]] = {}
        self.paper_citations: Counter = Counter()
        for e in self.edges:
            if e.get("validation_status", "accepted") != "accepted":
                continue
            self.out_edges[e["source_id"]].append(e)
            self.in_edges[e["target_id"]].append(e)
            if e["relation"] == "PUBLISHED_IN":
                vn = self.nodes.get(e["target_id"]) or {}
                self.paper_venue[e["source_id"]] = (e["target_id"], vn.get("name", ""))
            elif e["relation"] == "CITES":
                self.paper_citations[e["target_id"]] += 1

    def find_nodes(self, entity_type: str | None, text: str, limit: int = 10) -> list[dict[str, Any]]:
        label = _validate_label(entity_type)
        q_low = " ".join(re.sub(r"[-_]+", " ", text.strip().lower()).split())
        variants = _stem_variants(text)
        scored: list[tuple[int, int, str, dict[str, Any]]] = []
        for nid, n in self.nodes.items():
            if label and n["label"] != label:
                continue
            props = n.get("properties") or {}
            name_l = str(n["name"]).strip().lower()
            key_l = str(props.get("key") or "").strip().lower()
            surfs = _parse_surfaces(props.get("surfaces"))
            surfs_l = {s.lower() for s in surfs}
            if name_l == q_low:
                rank = 0
            elif name_l in variants or key_l in variants or (surfs_l & variants):
                rank = 1
            elif q_low in name_l or any(q_low in s for s in surfs_l):
                rank = 2
            else:
                continue
            pc = int(props.get("paper_count") or 0)
            scored.append((rank, -pc, nid, {
                "id": nid,
                "label": n["label"],
                "name": n["name"],
                "key": props.get("key"),
                "surfaces": surfs,
                "year": props.get("year"),
                "sector": props.get("sector"),
                "country_code": props.get("country_code"),
                "openalex_id": props.get("openalex_id"),
                "paper_count": pc,
                "wikipedia_url": props.get("wikipedia_url"),
            }))
        scored.sort(key=lambda x: (x[0], x[1], x[2]))
        return [x[3] for x in scored[:limit]]

    def get_nodes_by_ids(self, node_ids: list[str]) -> list[dict[str, Any]]:
        out = []
        for nid in dict.fromkeys(node_ids):
            n = self.nodes.get(nid)
            if n:
                props = n.get("properties") or {}
                out.append({
                    "id": nid, "label": n["label"], "name": n["name"],
                    "year": props.get("year"), "sector": props.get("sector"),
                    "country_code": props.get("country_code"),
                    "wikipedia_url": props.get("wikipedia_url"),
                    "paper_count": int(props.get("paper_count") or 0),
                })
        return out

    def researcher_context(self, researcher_ids: list[str]) -> dict[str, dict[str, Any]]:
        out = {}
        for rid in researcher_ids:
            orgs = [self.nodes[e["target_id"]]["name"] for e in self.out_edges.get(rid, [])
                    if e["relation"] == "AFFILIATED_WITH" and e["target_id"] in self.nodes]
            papers = {e["target_id"] for e in self.out_edges.get(rid, []) if e["relation"] == "AUTHORED"}
            out[rid] = {"affiliations": orgs[:3], "paper_count": len(papers)}
        return out

    def _paper_matches(self, pid: str, year_min: int | None, year_max: int | None, venue: str | None) -> bool:
        n = self.nodes.get(pid)
        if not n or n["label"] != "Paper":
            return True
        yr = (n.get("properties") or {}).get("year")
        if year_min is not None and (yr is None or int(yr) < year_min):
            return False
        if year_max is not None and (yr is None or int(yr) > year_max):
            return False
        if venue:
            vid, vname = self.paper_venue.get(pid, ("", ""))
            vq = venue.strip().lower()
            if vq not in vname.lower() and vid != f"venue:{vq}":
                return False
        return True

    def neighbors(
        self,
        node_id: str,
        *,
        predicates: list[str] | None = None,
        target_labels: list[str] | None = None,
        direction: str = "both",
        year_min: int | None = None,
        year_max: int | None = None,
        venue: str | None = None,
        min_support: int = 1,
        limit: int = 50,
    ) -> dict[str, Any]:
        preds = set(_validate_predicates(predicates) or ALLOWED_RELATIONS)
        t_labs = set(_validate_label(l) for l in (target_labels or []) if l)
        c = self.nodes.get(node_id)
        if not c:
            return {"center": None, "rows": []}
        center = {"id": c["id"], "label": c["label"], "name": c["name"],
                  "year": (c.get("properties") or {}).get("year"),
                  "sector": (c.get("properties") or {}).get("sector")}
        candidates = []
        if direction in ("both", "outgoing"):
            for e in self.out_edges.get(node_id, []):
                candidates.append((e, e["target_id"]))
        if direction in ("both", "incoming"):
            for e in self.in_edges.get(node_id, []):
                if direction == "both" and e["source_id"] == e["target_id"]:
                    continue
                candidates.append((e, e["source_id"]))

        rows = []
        seen_edge_nb: set[tuple[str, str]] = set()
        for e, nb_id in candidates:
            if e["relation"] not in preds:
                continue
            key = (e["edge_id"], nb_id)
            if key in seen_edge_nb:
                continue
            seen_edge_nb.add(key)
            props = e.get("properties") or {}
            sup = int(props.get("support_count", 1))
            if sup < min_support:
                continue
            nb = self.nodes.get(nb_id)
            if not nb:
                continue
            if t_labs and nb["label"] not in t_labs:
                continue
            if nb["label"] == "Paper" and not self._paper_matches(nb_id, year_min, year_max, venue):
                continue
            nb_props = nb.get("properties") or {}
            rows.append({
                "center_id": node_id,
                "relation": e["relation"],
                "source_id": e["source_id"],
                "target_id": e["target_id"],
                "edge_id": e["edge_id"],
                "support_count": sup,
                "fractional_weight": props.get("fractional_weight"),
                "evidence_ids": e.get("evidence_ids") or [],
                "support_paper_ids": props.get("support_paper_ids") or [],
                "evidence_kind": e.get("evidence_kind"),
                "neighbor_id": nb_id,
                "neighbor_label": nb["label"],
                "neighbor_name": nb["name"],
                "neighbor_year": nb_props.get("year"),
                "neighbor_sector": nb_props.get("sector"),
                "neighbor_country_code": nb_props.get("country_code"),
            })
        rows.sort(key=lambda r: (-int(r["support_count"]), r["neighbor_id"]))
        return {"center": center, "rows": rows[:limit]}

    def cooccurrence_partners(
        self,
        entity_id: str,
        entity_label: str,
        partner_label: str,
        *,
        year_min: int | None = None,
        year_max: int | None = None,
        venue: str | None = None,
        min_papers: int = 1,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        spec = COOCCURRENCE_PAIRS.get((entity_label, partner_label))
        if spec is None:
            return []
        rel_in, rel_out, _ = spec
        papers = [e["source_id"] for e in self.in_edges.get(entity_id, []) if e["relation"] == rel_in]
        by_partner: dict[str, list[str]] = defaultdict(list)
        for pid in papers:
            if not self._paper_matches(pid, year_min, year_max, venue):
                continue
            for e in self.out_edges.get(pid, []):
                if e["relation"] == rel_out:
                    b = self.nodes.get(e["target_id"])
                    if b and b["label"] == partner_label:
                        by_partner[b["id"]].append(pid)
        out = []
        for bid, pids in by_partner.items():
            uniq = sorted(set(pids))
            if len(uniq) < min_papers:
                continue
            b = self.nodes[bid]
            yrs = sorted({int((self.nodes[p].get("properties") or {}).get("year")) for p in uniq if (self.nodes[p].get("properties") or {}).get("year")})
            out.append({
                "id": bid, "label": partner_label, "name": b["name"],
                "shared_papers": len(uniq), "paper_ids": uniq[:25], "years": yrs,
            })
        out.sort(key=lambda r: (-r["shared_papers"], r["id"]))
        return out[:limit]

    def shortest_path(
        self,
        source_id: str,
        target_id: str,
        *,
        max_len: int = 4,
        predicates: list[str] | None = None,
    ) -> dict[str, Any]:
        if source_id not in self.nodes or target_id not in self.nodes:
            return {"found": False, "nodes": [], "edges": []}
        preds = set(_validate_predicates(predicates) or ALLOWED_RELATIONS)
        hops = max(1, min(int(max_len), 4))
        if source_id == target_id:
            n = self.nodes[source_id]
            return {"found": True, "nodes": [{"id": n["id"], "label": n["label"], "name": n["name"]}], "edges": []}
        q = deque([(source_id, [])])
        seen = {source_id}
        while q:
            cur, path_edges = q.popleft()
            if len(path_edges) >= hops:
                continue
            for e in self.out_edges.get(cur, []) + self.in_edges.get(cur, []):
                if e["relation"] not in preds:
                    continue
                nxt = e["target_id"] if e["source_id"] == cur else e["source_id"]
                new_edges = path_edges + [e]
                if nxt == target_id:
                    nids = [source_id]
                    for pe in new_edges:
                        nids.append(pe["target_id"] if pe["source_id"] == nids[-1] else pe["source_id"])
                    return {
                        "found": True,
                        "nodes": [{"id": self.nodes[i]["id"], "label": self.nodes[i]["label"], "name": self.nodes[i]["name"],
                                   "year": (self.nodes[i].get("properties") or {}).get("year")} for i in nids],
                        "edges": [{"edge_id": pe["edge_id"], "relation": pe["relation"], "source": pe["source_id"],
                                   "target": pe["target_id"], "support_count": int((pe.get("properties") or {}).get("support_count", 1)),
                                   "evidence_ids": pe.get("evidence_ids") or []} for pe in new_edges],
                    }
                if nxt not in seen:
                    seen.add(nxt)
                    q.append((nxt, new_edges))
        return {"found": False, "nodes": [], "edges": []}

    def _matching_papers(self, filters: dict[str, Any]) -> list[str]:
        res = [nid for nid, n in self.nodes.items() if n["label"] == "Paper"]
        if filters.get("topic_id"):
            keep = {e["source_id"] for e in self.in_edges.get(filters["topic_id"], []) if e["relation"] == "HAS_TOPIC"}
            res = [p for p in res if p in keep]
        if filters.get("method_id"):
            keep = {e["source_id"] for e in self.in_edges.get(filters["method_id"], []) if e["relation"] == "USES_METHOD"}
            res = [p for p in res if p in keep]
        if filters.get("task_id"):
            keep = {e["source_id"] for e in self.in_edges.get(filters["task_id"], []) if e["relation"] == "ADDRESSES_TASK"}
            res = [p for p in res if p in keep]
        if filters.get("dataset_id"):
            keep = {e["source_id"] for e in self.in_edges.get(filters["dataset_id"], []) if e["relation"] == "USES_DATASET"}
            res = [p for p in res if p in keep]
        if filters.get("researcher_id"):
            keep = {e["target_id"] for e in self.out_edges.get(filters["researcher_id"], []) if e["relation"] == "AUTHORED"}
            res = [p for p in res if p in keep]
        if filters.get("organization_id"):
            rids = {e["source_id"] for e in self.in_edges.get(filters["organization_id"], []) if e["relation"] == "AFFILIATED_WITH"}
            keep = {e["target_id"] for r in rids for e in self.out_edges.get(r, []) if e["relation"] == "AUTHORED"}
            res = [p for p in res if p in keep]
        q_low = str(filters.get("query_text") or "").strip().lower()
        out = []
        for pid in res:
            if not self._paper_matches(pid, filters.get("year_min"), filters.get("year_max"), filters.get("venue")):
                continue
            if q_low and q_low not in str(self.nodes[pid]["name"]).lower():
                continue
            out.append(pid)
        return out

    def query_papers(self, filters: dict[str, Any], limit: int = 50) -> list[dict[str, Any]]:
        pids = self._matching_papers(filters)
        rows = []
        for pid in pids:
            n = self.nodes[pid]
            props = n.get("properties") or {}
            vid, vname = self.paper_venue.get(pid, (None, None))
            rows.append({
                "id": pid, "title": n["name"], "year": props.get("year"), "venue_id": vid, "venue": vname,
                "doi": props.get("doi"), "official_url": props.get("official_url"),
                "in_citations": self.paper_citations.get(pid, 0),
            })
        rows.sort(key=lambda r: (-int(r["in_citations"]), -(int(r["year"] or 0)), r["id"]))
        return rows[:limit]

    def aggregate_papers(
        self,
        entity_ids: list[str],
        *,
        by: str,
        filters: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        flt = dict(filters or {})
        base_papers = set(self._matching_papers(flt))

        def _papers_for_entity(eid: str) -> set[str]:
            if eid.startswith("paper:"):
                return {eid} & base_papers
            if eid.startswith("organization:"):
                rids = {e["source_id"] for e in self.in_edges.get(eid, []) if e["relation"] == "AFFILIATED_WITH"}
                return {e["target_id"] for r in rids for e in self.out_edges.get(r, []) if e["relation"] == "AUTHORED"} & base_papers
            ps = set()
            for e in self.out_edges.get(eid, []):
                if e["relation"] == "AUTHORED":
                    ps.add(e["target_id"])
            for e in self.in_edges.get(eid, []):
                if e["relation"] in ("HAS_TOPIC", "USES_METHOD", "ADDRESSES_TASK", "USES_DATASET"):
                    ps.add(e["source_id"])
            return ps & base_papers

        if by == "organization_year":
            rows = []
            org_ids = [i for i in entity_ids if i.startswith("organization:")]
            for oid in org_ids:
                by_yr: dict[int, set[str]] = defaultdict(set)
                for pid in _papers_for_entity(oid):
                    yr = (self.nodes[pid].get("properties") or {}).get("year")
                    if yr is not None:
                        by_yr[int(yr)].add(pid)
                for yr, pids in sorted(by_yr.items()):
                    rows.append({
                        "entity_id": oid,
                        "entity_name": self.nodes[oid]["name"],
                        "year": yr,
                        "paper_count": len(pids),
                        "paper_ids": sorted(pids)[:10],
                    })
            return rows[:limit]

        anchored = set().union(*(_papers_for_entity(i) for i in entity_ids)) if entity_ids else base_papers
        groups: dict[Any, set[str]] = defaultdict(set)
        labels: dict[Any, str] = {}
        for pid in anchored:
            if by == "year":
                yr = (self.nodes[pid].get("properties") or {}).get("year")
                if yr is not None:
                    groups[int(yr)].add(pid)
                    labels[int(yr)] = str(yr)
            elif by == "venue":
                vid, vname = self.paper_venue.get(pid, (None, None))
                if vid:
                    groups[vid].add(pid)
                    labels[vid] = vname or vid
            elif by in ("topic", "method", "task", "dataset"):
                rel = {"topic": "HAS_TOPIC", "method": "USES_METHOD", "task": "ADDRESSES_TASK", "dataset": "USES_DATASET"}[by]
                for e in self.out_edges.get(pid, []):
                    if e["relation"] == rel and e["target_id"] in self.nodes:
                        groups[e["target_id"]].add(pid)
                        labels[e["target_id"]] = self.nodes[e["target_id"]]["name"]
            elif by == "organization":
                rids = {e["source_id"] for e in self.in_edges.get(pid, []) if e["relation"] == "AUTHORED"}
                for r in rids:
                    for e in self.out_edges.get(r, []):
                        if e["relation"] == "AFFILIATED_WITH" and e["target_id"] in self.nodes:
                            groups[e["target_id"]].add(pid)
                            labels[e["target_id"]] = self.nodes[e["target_id"]]["name"]
            elif by == "researcher":
                for e in self.in_edges.get(pid, []):
                    if e["relation"] == "AUTHORED" and e["source_id"] in self.nodes:
                        groups[e["source_id"]].add(pid)
                        labels[e["source_id"]] = self.nodes[e["source_id"]]["name"]
            else:
                raise ValueError(f"Unsupported aggregate grouping {by!r}")
        out = [{"group_key": k, "label": labels[k], "paper_count": len(pids), "paper_ids": sorted(pids)[:15]}
               for k, pids in groups.items()]
        out.sort(key=(lambda r: r["group_key"]) if by == "year" else (lambda r: (-r["paper_count"], str(r["group_key"]))))
        return out[:limit]

    def year_totals(self, filters: dict[str, Any] | None = None) -> dict[int, int]:
        counts: Counter = Counter()
        for n in self.nodes.values():
            if n["label"] == "Paper":
                yr = (n.get("properties") or {}).get("year")
                if yr is not None:
                    counts[int(yr)] += 1
        return dict(sorted(counts.items()))


class RAGToolset:
    """Unified closed 9-tool interface over GraphBackend + precomputed analysis/RAG artifacts."""

    TOOL_NAMES = ("find", "neighbors", "path", "papers", "aggregate", "rank", "community", "community_report", "trend")

    def __init__(
        self,
        backend: GraphBackend,
        *,
        analysis_dir: Path = Path("reports/final-exam/analysis-v2"),
        rag_dir: Path = Path("reports/final-exam/rag-v1"),
        vector_search_fn: Callable[[str, str | None, int], list[dict[str, Any]]] | None = None,
    ) -> None:
        self.backend = backend
        self.analysis_dir = analysis_dir
        self.rag_dir = rag_dir
        self.vector_search_fn = vector_search_fn
        self._aliases: dict[str, list[dict[str, Any]]] | None = None
        self._ppr_cache: dict[str, Any] | None = None
        self._trends_cache: dict[str, list[dict[str, Any]]] = {}
        self._reports_cache: dict[str, dict[str, Any]] | None = None
        self._research_comms_cache: dict[str, Any] | None = None

    def _load_json(self, path: Path) -> Any:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

    def _load_csv(self, path: Path) -> list[dict[str, str]]:
        if not path.exists():
            return []
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rt", newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def _display_alias_map(self) -> dict[str, list[dict[str, Any]]]:
        if self._aliases is None:
            data = self._load_json(self.analysis_dir / "trends" / "display-aliases.json") or {}
            by_name: dict[str, list[dict[str, Any]]] = {}
            for _kind, groups in (data.get("by_kind") or {}).items():
                for g in groups:
                    for m in g.get("members", []):
                        by_name[m["name"].lower()] = g["members"]
            self._aliases = by_name
        return self._aliases

    # 1. find(type, text)
    def find(self, entity_type: str | None, text: str, limit: int = 10) -> ToolResult:
        _validate_label(entity_type)
        lim = max(1, min(int(limit), 25))
        rows = self.backend.find_nodes(entity_type, text, limit=lim)

        # Fallback to display alias map if no direct match
        if not rows and text.strip():
            alias_hits = self._display_alias_map().get(text.strip().lower(), [])
            if alias_hits:
                rows = self.backend.get_nodes_by_ids([m["id"] for m in alias_hits[:lim]])

        # Fallback to embedding match when configured
        source_kind = "graph"
        if not rows and self.vector_search_fn is not None and text.strip():
            vec_hits = self.vector_search_fn(text, entity_type, lim)
            if vec_hits:
                rows = vec_hits
                source_kind = "embedding_match"

        # Same-name Researcher disambiguation: never auto-merge
        ambiguous = False
        note = ""
        if entity_type == "Researcher" or any(r.get("label") == "Researcher" for r in rows):
            r_rows = [r for r in rows if r.get("label") == "Researcher"]
            if len(r_rows) > 1:
                ctx = self.backend.researcher_context([r["id"] for r in r_rows])
                for r in r_rows:
                    info = ctx.get(r["id"], {})
                    r["affiliations"] = info.get("affiliations", [])
                    r["paper_count"] = info.get("paper_count", r.get("paper_count", 0))
                exact_same = [r for r in r_rows if str(r.get("name", "")).strip().lower() == text.strip().lower()]
                if len(exact_same) > 1 or (len(r_rows) > 1 and entity_type == "Researcher"):
                    ambiguous = True
                    note = f"Multiple researchers match {text!r}; choose a specific OpenAlex-resolved researcher ID (never auto-merged)."

        return ToolResult(
            tool="find",
            args={"entity_type": entity_type, "text": text, "limit": lim},
            rows=rows,
            ids=[r["id"] for r in rows],
            subgraph_nodes=[{"id": r["id"], "label": r["label"], "name": r["name"]} for r in rows],
            source_kind=source_kind,
            ambiguous=ambiguous,
            empty=len(rows) == 0,
            note=note or ("No matching entity found." if not rows else f"Found {len(rows)} entity match(es)."),
        )

    # 2. neighbors(id, predicates, filters)
    def neighbors(
        self,
        node_id: str | list[str],
        predicates: list[str] | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 50,
    ) -> ToolResult:
        flt = filters or {}
        lim = max(1, min(int(limit), 250))

        # Support batched expansion when an earlier step yields '$stepK.ids'
        if isinstance(node_id, (list, tuple)):
            seed_ids = [str(x) for x in node_id if x][:25]
            if not seed_ids:
                return ToolResult(tool="neighbors", args={"node_id": [], "predicates": predicates, "filters": flt},
                                  empty=True, note="No input node IDs provided.")
            merged_rows: list[dict[str, Any]] = []
            seen_nb: set[tuple[str, str]] = set()
            ev_ids: list[str] = []
            paper_ids: list[str] = []
            sub_nodes: dict[str, dict[str, Any]] = {}
            sub_edges: list[dict[str, Any]] = []
            for sid in seed_ids:
                sub = self.neighbors(sid, predicates=predicates, filters=flt, limit=min(lim, 20))
                for n in sub.subgraph_nodes:
                    sub_nodes.setdefault(n["id"], n)
                sub_edges.extend(sub.subgraph_edges)
                ev_ids.extend(sub.evidence_ids)
                paper_ids.extend(sub.paper_ids)
                for r in sub.rows:
                    key = (r.get("neighbor_id", ""), r.get("relation", ""))
                    if key not in seen_nb:
                        seen_nb.add(key)
                        merged_rows.append(r)
            merged_rows.sort(key=lambda r: (-int(r.get("support_count", 1)), str(r.get("neighbor_id", ""))))
            merged_rows = merged_rows[:lim]
            return ToolResult(
                tool="neighbors",
                args={"node_id": seed_ids, "predicates": predicates, "filters": flt, "limit": lim},
                rows=merged_rows,
                ids=[r["neighbor_id"] for r in merged_rows],
                evidence_ids=list(dict.fromkeys(ev_ids))[:100],
                paper_ids=list(dict.fromkeys(paper_ids))[:100],
                subgraph_nodes=list(sub_nodes.values())[:100],
                subgraph_edges=sub_edges[:150],
                source_kind="graph" if merged_rows else "empty",
                empty=len(merged_rows) == 0,
                note=f"Batched expansion across {len(seed_ids)} node(s): {len(merged_rows)} unique neighbor(s).",
            )

        res = self.backend.neighbors(
            node_id,
            predicates=predicates,
            target_labels=flt.get("target_labels"),
            direction=flt.get("direction", "both"),
            year_min=flt.get("year_min"),
            year_max=flt.get("year_max"),
            venue=flt.get("venue"),
            min_support=int(flt.get("min_support", 1)),
            limit=lim,
        )
        center = res["center"]
        if center is None:
            return ToolResult(tool="neighbors", args={"node_id": node_id, "predicates": predicates, "filters": flt},
                              empty=True, note=f"Entity {node_id!r} not found.")

        rows = []
        ev_ids: list[str] = []
        paper_ids: list[str] = []
        sub_nodes: dict[str, dict[str, Any]] = {center["id"]: {"id": center["id"], "label": center["label"], "name": center["name"]}}
        sub_edges: list[dict[str, Any]] = []

        for r in res["rows"]:
            r_out = dict(r)
            r_out["source_kind"] = "extracted_edge" if r["relation"] in ("APPLIED_TO", "EVALUATED_ON") else "graph_edge"
            rows.append(r_out)
            ev_ids.extend(r.get("evidence_ids") or [])
            paper_ids.extend(r.get("support_paper_ids") or [])
            if r["neighbor_label"] == "Paper":
                paper_ids.append(r["neighbor_id"])
            sub_nodes[r["neighbor_id"]] = {"id": r["neighbor_id"], "label": r["neighbor_label"], "name": r["neighbor_name"]}
            sub_edges.append({
                "edge_id": r["edge_id"], "relation": r["relation"],
                "source": r["source_id"], "target": r["target_id"],
                "support_count": r["support_count"],
            })

        # Paper co-occurrence supplement for Method/Task/Dataset queries:
        # Use co-occurrence when predicates omitted, include_cooccurrence is set, or explicit APPLIED_TO/EVALUATED_ON returned 0 edges.
        c_lab = center["label"]
        t_labs = list(flt.get("target_labels") or [])
        preds_set = set(predicates or [])
        direct_n = len(rows)
        want_cooccur = (not preds_set) or bool(flt.get("include_cooccurrence")) or (
            bool(preds_set & {"APPLIED_TO", "EVALUATED_ON"}) and direct_n == 0
        )
        cooccur_targets: list[str] = []
        if c_lab in ("Method", "Task", "Dataset") and want_cooccur:
            if t_labs:
                cooccur_targets = [tl for tl in t_labs if (c_lab, tl) in COOCCURRENCE_PAIRS]
            elif "APPLIED_TO" in preds_set:
                cooccur_targets = ["Task"] if c_lab == "Method" else (["Method"] if c_lab == "Task" else [])
            elif "EVALUATED_ON" in preds_set:
                cooccur_targets = ["Dataset"] if c_lab in ("Method", "Task") else ["Method", "Task"]

        cooccur_count = 0
        for p_lab in cooccur_targets:
            partners = self.backend.cooccurrence_partners(
                node_id, c_lab, p_lab,
                year_min=flt.get("year_min"), year_max=flt.get("year_max"),
                venue=flt.get("venue"), min_papers=int(flt.get("min_cooccurrence_papers", 1)),
                limit=lim,
            )
            for p in partners:
                cooccur_count += 1
                pids = p.get("paper_ids") or []
                paper_ids.extend(pids)
                rows.append({
                    "center_id": node_id,
                    "relation": "COOCCURS_IN_PAPERS",
                    "neighbor_id": p["id"],
                    "neighbor_label": p["label"],
                    "neighbor_name": p["name"],
                    "support_count": p["shared_papers"],
                    "paper_ids": pids,
                    "years": p.get("years", []),
                    "source_kind": "paper_cooccurrence",
                })
                sub_nodes[p["id"]] = {"id": p["id"], "label": p["label"], "name": p["name"]}
                sub_edges.append({
                    "edge_id": f"cooccur:{node_id}:{p['id']}",
                    "relation": "COOCCURS_IN_PAPERS",
                    "source": node_id, "target": p["id"],
                    "support_count": p["shared_papers"],
                })

        notes = []
        if direct_n:
            notes.append(f"{direct_n} direct graph edges")
        if cooccur_count:
            notes.append(f"{cooccur_count} paper co-occurrence partners (shared papers as evidence)")
        return ToolResult(
            tool="neighbors",
            args={"node_id": node_id, "predicates": predicates, "filters": flt, "limit": lim},
            rows=rows,
            ids=[r["neighbor_id"] for r in rows],
            evidence_ids=list(dict.fromkeys(ev_ids))[:100],
            paper_ids=list(dict.fromkeys(paper_ids))[:100],
            subgraph_nodes=list(sub_nodes.values()),
            subgraph_edges=sub_edges,
            source_kind="mixed" if (direct_n and cooccur_count) else ("paper_cooccurrence" if cooccur_count else "graph"),
            empty=len(rows) == 0,
            note="; ".join(notes) if notes else "No matching neighbors found.",
        )

    # 3. path(a, b, max_len, predicates)
    def path(self, source_id: str, target_id: str, max_len: int = 4, predicates: list[str] | None = None) -> ToolResult:
        res = self.backend.shortest_path(source_id, target_id, max_len=max_len, predicates=predicates)
        if not res["found"]:
            return ToolResult(
                tool="path",
                args={"source_id": source_id, "target_id": target_id, "max_len": max_len, "predicates": predicates},
                empty=True,
                note=f"No path within {min(int(max_len), 4)} hops.",
            )
        ev_ids = [eid for e in res["edges"] for eid in (e.get("evidence_ids") or [])]
        paper_ids = [n["id"] for n in res["nodes"] if n.get("label") == "Paper"]
        return ToolResult(
            tool="path",
            args={"source_id": source_id, "target_id": target_id, "max_len": max_len, "predicates": predicates},
            rows=res["edges"],
            ids=[n["id"] for n in res["nodes"]],
            evidence_ids=list(dict.fromkeys(ev_ids)),
            paper_ids=paper_ids,
            subgraph_nodes=res["nodes"],
            subgraph_edges=res["edges"],
            source_kind="graph",
            empty=False,
            note=f"Found path of {len(res['edges'])} hop(s).",
        )

    # 4. papers(filter)
    def papers(self, filters: dict[str, Any] | None = None, limit: int = 50) -> ToolResult:
        flt = filters or {}
        lim = max(1, min(int(limit), 200))
        rows = self.backend.query_papers(flt, limit=lim)
        pids = [r["id"] for r in rows]
        return ToolResult(
            tool="papers",
            args={"filters": flt, "limit": lim},
            rows=rows,
            ids=pids,
            paper_ids=pids,
            subgraph_nodes=[{"id": r["id"], "label": "Paper", "name": r["title"], "year": r.get("year")} for r in rows[:50]],
            source_kind="graph",
            empty=len(rows) == 0,
            note=f"Matched {len(rows)} paper(s).",
        )

    # 5. aggregate(entity_set, by, metric)
    def aggregate(
        self,
        entity_ids: list[str],
        by: str = "year",
        metric: str = "paper_count",
        filters: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> ToolResult:
        flt = filters or {}
        if by == "organization_year" or metric == "share_growth":
            # Compute per-org yearly subject papers vs org total papers for growth comparisons (e.g. > 2022)
            subject_rows = self.backend.aggregate_papers(entity_ids, by="organization_year", filters=flt, limit=500)
            total_rows = self.backend.aggregate_papers(entity_ids, by="organization_year", filters={}, limit=500)
            cutoff = int(flt.get("after_year", 2022))
            subj_by_org_yr: dict[str, dict[int, int]] = defaultdict(dict)
            tot_by_org_yr: dict[str, dict[int, int]] = defaultdict(dict)
            org_names: dict[str, str] = {}
            all_pids: list[str] = []
            for r in total_rows:
                tot_by_org_yr[r["entity_id"]][int(r["year"])] = int(r["paper_count"])
                org_names[r["entity_id"]] = r["entity_name"]
            for r in subject_rows:
                subj_by_org_yr[r["entity_id"]][int(r["year"])] = int(r["paper_count"])
                org_names[r["entity_id"]] = r["entity_name"]
                all_pids.extend(r.get("paper_ids") or [])

            summary_rows = []
            for oid in dict.fromkeys(entity_ids):
                if oid not in org_names:
                    continue
                s_map = subj_by_org_yr[oid]
                t_map = tot_by_org_yr[oid]
                pre_s = sum(v for y, v in s_map.items() if y <= cutoff)
                pre_t = sum(v for y, v in t_map.items() if y <= cutoff)
                post_s = sum(v for y, v in s_map.items() if y > cutoff)
                post_t = sum(v for y, v in t_map.items() if y > cutoff)
                pre_share = (pre_s / pre_t) if pre_t else 0.0
                post_share = (post_s / post_t) if post_t else 0.0
                delta = post_share - pre_share
                if flt.get("only_increased") and not (post_s > 0 and delta > 0):
                    continue
                summary_rows.append({
                    "entity_id": oid,
                    "entity_name": org_names[oid],
                    f"pre_le_{cutoff}_subject_papers": pre_s,
                    f"pre_le_{cutoff}_total_papers": pre_t,
                    f"pre_le_{cutoff}_share": round(pre_share, 4),
                    f"post_gt_{cutoff}_subject_papers": post_s,
                    f"post_gt_{cutoff}_total_papers": post_t,
                    f"post_gt_{cutoff}_share": round(post_share, 4),
                    "share_delta": round(delta, 4),
                })
            summary_rows.sort(key=lambda r: (-r["share_delta"], -r[f"post_gt_{cutoff}_subject_papers"], r["entity_id"]))
            return ToolResult(
                tool="aggregate",
                args={"entity_ids": entity_ids, "by": by, "metric": metric, "filters": flt},
                rows=summary_rows[:limit],
                ids=[r["entity_id"] for r in summary_rows[:limit]],
                paper_ids=list(dict.fromkeys(all_pids))[:100],
                source_kind="graph",
                empty=len(summary_rows) == 0,
                note=f"Computed share growth across cutoff year > {cutoff} for {len(summary_rows)} organization(s).",
            )

        rows = self.backend.aggregate_papers(entity_ids, by=by, filters=flt, limit=limit)
        if by == "year" and metric in ("share", "paper_share"):
            totals = self.backend.year_totals(flt)
            for r in rows:
                tot = totals.get(int(r["group_key"]), 0)
                r["year_total_papers"] = tot
                r["share"] = round(r["paper_count"] / tot, 6) if tot else None
        if by == "year":
            total_papers = sum(int(r.get("paper_count", 0)) for r in rows)
            for r in rows:
                r["total_papers"] = total_papers
            note_str = f"Aggregated {len(rows)} year(s); total_papers={total_papers}."
        else:
            note_str = f"Aggregated {len(rows)} group(s) by {by}."

        pids = [p for r in rows for p in (r.get("paper_ids") or [])]
        return ToolResult(
            tool="aggregate",
            args={"entity_ids": entity_ids, "by": by, "metric": metric, "filters": flt},
            rows=rows,
            ids=[str(r["group_key"]) for r in rows],
            paper_ids=list(dict.fromkeys(pids))[:100],
            source_kind="graph",
            empty=len(rows) == 0,
            note=note_str,
        )

    # 6. rank(network, scope, measure)
    def rank(self, network: str = "N1", scope: str | None = None, measure: str = "pagerank", limit: int = 20) -> ToolResult:
        lim = max(1, min(int(limit), 50))
        if scope:
            if self._ppr_cache is None:
                self._ppr_cache = self._load_json(self.analysis_dir / "ranking" / "personalized-pagerank.json") or {}
            subjects = self._ppr_cache.get("subjects", {})
            q_low = scope.strip().lower()
            matched_subj = None
            matched_kind = None
            matched_id = None
            for kind, items in subjects.items():
                if scope in items:
                    matched_kind, matched_id, matched_subj = kind, scope, items[scope]
                    break
                for sid, sdata in items.items():
                    if sdata.get("name", "").lower() == q_low:
                        matched_kind, matched_id, matched_subj = kind, sid, sdata
                        break
                if matched_subj:
                    break
            if not matched_subj:
                return ToolResult(tool="rank", args={"network": network, "scope": scope, "measure": measure},
                                  empty=True, note=f"No precomputed personalized PageRank entry for scope {scope!r}.")
            target_label = "Organization" if network == "N2" else ("Researcher" if network == "N1" else "Organization")
            rows = list(matched_subj.get("top", {}).get(target_label, []))[:lim]
            return ToolResult(
                tool="rank",
                args={"network": network, "scope": scope, "measure": "lift" if measure == "pagerank" else measure},
                rows=rows,
                ids=[r["id"] for r in rows],
                source_kind="precomputed_analysis_v2",
                empty=len(rows) == 0,
                note=f"Subject-specific ranking for {matched_kind} {matched_subj['name']!r} ({matched_subj['papers']} papers), ranked by lift.",
            )

        data = self._load_json(self.analysis_dir / "ranking" / f"ranking-{network}.json")
        if not data:
            return ToolResult(tool="rank", args={"network": network, "measure": measure}, empty=True,
                              note=f"Ranking artifact for {network!r} unavailable.")
        if network == "N4":
            rows = [r for lab_rows in (data.get("top_by_label") or {}).values() for r in lab_rows[:5]][:lim]
        else:
            rows = list(data.get("top") or [])[:lim]
        return ToolResult(
            tool="rank",
            args={"network": network, "scope": scope, "measure": measure},
            rows=rows,
            ids=[r["id"] for r in rows],
            source_kind="precomputed_analysis_v2",
            empty=len(rows) == 0,
            note=data.get("sparsity_note") or f"Global ranking on {network} ({data.get('nodes')} nodes, {data.get('edges')} edges).",
        )

    # 7. community(id)
    def community(self, node_or_community_id: str, network: str | None = None) -> ToolResult:
        # Check research communities (Phase 3) first, then N1/N2 S3 communities
        if self._research_comms_cache is None:
            self._research_comms_cache = self._load_json(self.rag_dir / "research-communities.json") or {}

        cid_q = node_or_community_id.strip()
        if cid_q.startswith("research:") or (self._research_comms_cache and cid_q in (self._research_comms_cache.get("communities") or {})):
            comms = self._research_comms_cache.get("communities") or {}
            c = comms.get(cid_q)
            if c:
                return ToolResult(
                    tool="community",
                    args={"id": cid_q, "network": "research"},
                    rows=[c],
                    ids=[m["id"] for m in c.get("members", [])],
                    paper_ids=[p["id"] for p in c.get("top_papers", [])],
                    source_kind="precomputed_rag_v1",
                    empty=False,
                    note=f"Research-graph community {cid_q} (level {c.get('level')}, {c.get('size')} entities).",
                )

        # Check N1/N2 membership CSVs and communities JSON
        nets = [network] if network in ("N1", "N2") else ["N1", "N2"]
        for net in nets:
            cm = self._load_json(self.analysis_dir / "communities" / f"communities-{net}.json")
            if not cm:
                continue
            target_comm: str | None = None
            if cid_q.isdigit():
                target_comm = cid_q
            elif cid_q.startswith(f"{net.lower()}:") or cid_q.startswith(f"{net}:"):
                target_comm = cid_q.split(":", 1)[1]
            else:
                # Look up node ID in membership CSV
                for row in self._load_csv(self.analysis_dir / "communities" / f"membership-{net}.csv.gz"):
                    if row["id"] == cid_q:
                        target_comm = row["level0"]
                        break
            if target_comm is not None:
                labels = (cm.get("labels") or {}).get(target_comm, {})
                ki = (cm.get("key_individuals") or {}).get(target_comm, {})
                members_rows = [r["id"] for r in self._load_csv(self.analysis_dir / "communities" / f"membership-{net}.csv.gz") if r["level0"] == target_comm]
                if members_rows:
                    row = {
                        "network": net,
                        "community_id": f"{net}:{target_comm}",
                        "community": int(target_comm),
                        "size": len(members_rows),
                        "labels": labels,
                        "key_individuals": ki,
                        "sample_member_ids": members_rows[:25],
                    }
                    return ToolResult(
                        tool="community",
                        args={"id": cid_q, "network": net},
                        rows=[row],
                        ids=members_rows[:50],
                        source_kind="precomputed_analysis_v2",
                        empty=False,
                        note=f"{net} Leiden community {target_comm} ({len(members_rows)} members).",
                    )

        return ToolResult(tool="community", args={"id": cid_q, "network": network}, empty=True,
                          note=f"No community found for {cid_q!r}.")

    # 8. community_report(cid)
    def community_report(self, cid: str) -> ToolResult:
        if self._reports_cache is None:
            data = self._load_json(self.rag_dir / "community-reports.json") or {}
            self._reports_cache = {r["community_id"]: r for r in data.get("reports", [])}
        rep = self._reports_cache.get(cid)
        if not rep:
            return ToolResult(tool="community_report", args={"cid": cid}, empty=True,
                              note=f"Community report {cid!r} not found.")
        pids = [pid for kf in rep.get("key_findings", []) for pid in kf.get("paper_ids", [])]
        return ToolResult(
            tool="community_report",
            args={"cid": cid},
            rows=[rep],
            ids=[cid],
            paper_ids=list(dict.fromkeys(pids)),
            source_kind="precomputed_rag_v1",
            empty=False,
            note=f"AI-generated community report for {cid} ({rep.get('title')}).",
        )

    # 9. trend(subject, period)
    def trend(
        self,
        subject_or_kind: str,
        period: tuple[int, int] | list[int] | None = None,
        trend_class: str | None = None,
        limit: int = 25,
    ) -> ToolResult:
        lim = max(1, min(int(limit), 100))
        q = subject_or_kind.strip()
        q_low = q.lower()
        kinds = ("Topic", "Method", "Task", "Dataset")
        summary = self._load_json(self.analysis_dir / "trends" / "trends-summary.json") or {}
        caveats = summary.get("caveats", [])
        class_note = summary.get("classification_note", "descriptive (p <= 0.10 per subject, no multiple-testing correction)")

        def _rows_for(kind: str) -> list[dict[str, Any]]:
            if kind not in self._trends_cache:
                self._trends_cache[kind] = self._load_csv(self.analysis_dir / "trends" / f"trends-{kind.lower()}.csv")
            return self._trends_cache[kind]

        # Case A: asking for a whole kind (e.g. "Method", "Task", "Topic", "Dataset")
        matched_kind = next((k for k in kinds if k.lower() in (q_low, q_low.rstrip("s"))), None)
        if matched_kind is not None:
            raw = _rows_for(matched_kind)
            filtered = [r for r in raw if (not trend_class or r["class"] == trend_class)]
            if trend_class in ("rising", "emerging"):
                filtered.sort(key=lambda r: (-int(r["recent_window_papers"]), -float(r.get("slope_of_share") or 0), r["id"]))
            elif trend_class == "declining":
                filtered.sort(key=lambda r: (float(r.get("slope_of_share") or 0), -int(r["total_papers"]), r["id"]))
            else:
                filtered.sort(key=lambda r: (-int(r["total_papers"]), r["id"]))
            rows = [self._format_trend_row(r, period) for r in filtered[:lim]]
            return ToolResult(
                tool="trend",
                args={"subject_or_kind": subject_or_kind, "period": period, "trend_class": trend_class},
                rows=rows,
                ids=[r["id"] for r in rows],
                source_kind="precomputed_analysis_v2",
                empty=len(rows) == 0,
                note=f"{matched_kind} trends ({class_note}). Caveats: {'; '.join(caveats[:2])}",
            )

        # Case B: specific subject name/ID or display alias
        alias_ids = {m["id"] for m in self._display_alias_map().get(q_low, [])}
        variants = _stem_variants(q_low)
        matches = []
        for kind in kinds:
            for r in _rows_for(kind):
                nm_l = r["name"].strip().lower()
                if r["id"] == q or nm_l == q_low or r["id"] in alias_ids or nm_l in variants:
                    matches.append(self._format_trend_row(r, period))
        if not matches:
            for kind in kinds:
                for r in _rows_for(kind):
                    if q_low in r["name"].strip().lower():
                        matches.append(self._format_trend_row(r, period))
        matches.sort(key=lambda r: (-r["total_papers"], r["id"]))
        return ToolResult(
            tool="trend",
            args={"subject_or_kind": subject_or_kind, "period": period},
            rows=matches[:lim],
            ids=[r["id"] for r in matches[:lim]],
            source_kind="precomputed_analysis_v2",
            empty=len(matches) == 0,
            note=f"Matched {len(matches)} subject trend(s) ({class_note}).",
        )

    def _format_trend_row(self, r: dict[str, str], period: Any) -> dict[str, Any]:
        if isinstance(period, dict):
            y_lo = int(period.get("year_min") or 2021)
            y_hi = int(period.get("year_max") or 2025)
        elif isinstance(period, str) and "-" in period:
            parts = [p.strip() for p in period.split("-", 1)]
            y_lo, y_hi = (int(parts[0]), int(parts[1])) if all(p.isdigit() for p in parts) else (2021, 2025)
        elif isinstance(period, (list, tuple)) and len(period) == 2:
            y_lo, y_hi = int(period[0]), int(period[1])
        else:
            y_lo, y_hi = 2021, 2025
        years = [y for y in range(2021, 2026) if y_lo <= y <= y_hi]
        return {
            "kind": r["kind"],
            "id": r["id"],
            "name": r["name"],
            "class": r["class"],
            "total_papers": int(r["total_papers"]),
            "base_window_papers": int(r["base_window_papers"]),
            "recent_window_papers": int(r["recent_window_papers"]),
            "cagr_of_share_2021_2025": float(r["cagr_of_share_2021_2025"]) if r.get("cagr_of_share_2021_2025") else None,
            "slope_of_share": float(r["slope_of_share"]) if r.get("slope_of_share") else None,
            "slope_p_value": float(r["slope_p_value"]) if r.get("slope_p_value") else None,
            "papers_by_year": {str(y): int(r[f"papers_{y}"]) for y in years},
            "share_by_year": {str(y): float(r[f"share_{y}"]) for y in years},
        }

    def call(self, tool_name: str, **kwargs) -> ToolResult:
        if tool_name not in self.TOOL_NAMES:
            raise ValueError(f"Unknown tool {tool_name!r}; allowed: {self.TOOL_NAMES}")
        return getattr(self, tool_name)(**kwargs)
