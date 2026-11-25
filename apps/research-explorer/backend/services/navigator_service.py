"""Read-only Research Trend Navigator service (trends, subjects, groups, communities, S1-S3, Node360, Ask)."""

from __future__ import annotations

import csv
from collections import defaultdict
import gzip
import json
from pathlib import Path
import sys
from typing import Any, Iterator

import yaml

from backend.config import REPO_ROOT, Settings

SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from scientific_network.rag.answer import run_ask, stream_ask  # noqa: E402
from scientific_network.rag.dev_eval import SCRIPTED_DEMO_QUESTIONS  # noqa: E402
from scientific_network.rag.llm import LLMClient, LLMConfig  # noqa: E402
from scientific_network.rag.sqlite_vectors import SQLiteVectorStore  # noqa: E402
from scientific_network.rag.tools import (  # noqa: E402
    InMemoryGraphBackend,
    Neo4jToolBackend,
    RAGToolset,
)

ENRICHED_LABELS: tuple[str, ...] = (
    "Researcher",
    "Paper",
    "Organization",
    "Topic",
    "Venue",
    "Method",
    "Task",
    "Dataset",
)

ENRICHED_PREDICATES: tuple[dict[str, str], ...] = (
    {"relation": "AUTHORED", "kind": "observed", "source": "Researcher", "target": "Paper"},
    {"relation": "AFFILIATED_WITH", "kind": "observed", "source": "Researcher", "target": "Organization"},
    {"relation": "PUBLISHED_IN", "kind": "observed", "source": "Paper", "target": "Venue"},
    {"relation": "CITES", "kind": "observed", "source": "Paper", "target": "Paper"},
    {"relation": "HAS_TOPIC", "kind": "inferred_topic", "source": "Paper", "target": "Topic"},
    {"relation": "SUBTOPIC_OF", "kind": "curated_taxonomy", "source": "Topic", "target": "Topic"},
    {"relation": "COAUTHORED_WITH", "kind": "derived", "source": "Researcher", "target": "Researcher"},
    {"relation": "COLLABORATED_WITH", "kind": "derived", "source": "Organization", "target": "Organization"},
    {"relation": "RESEARCHES_TOPIC", "kind": "derived", "source": "Researcher", "target": "Topic"},
    {"relation": "CONTRIBUTES_TO_TOPIC", "kind": "derived", "source": "Organization", "target": "Topic"},
    {"relation": "USES_METHOD", "kind": "extracted", "source": "Paper", "target": "Method"},
    {"relation": "ADDRESSES_TASK", "kind": "extracted", "source": "Paper", "target": "Task"},
    {"relation": "USES_DATASET", "kind": "extracted", "source": "Paper", "target": "Dataset"},
    {"relation": "APPLIED_TO", "kind": "extracted", "source": "Method", "target": "Task"},
    {"relation": "EVALUATED_ON", "kind": "extracted", "source": "Method", "target": "Dataset"},
    {"relation": "PART_OF", "kind": "wikidata", "source": "Organization", "target": "Organization"},
    {"relation": "MEMBER_OF", "kind": "wikidata", "source": "Organization", "target": "Organization"},
    {"relation": "RELATED_TO", "kind": "aggregated", "source": "Topic/Entity", "target": "Topic/Entity"},
)

METRIC_DEFINITIONS: dict[str, dict[str, str]] = {
    "share": {
        "name": "Annual paper share",
        "definition": "Fraction of main-track AAAI+IJCAI papers in year Y connected to subject S.",
        "denominator": "All main-track papers in year Y (or selected venue Y): 2,240 (2021) to 4,042 (2025).",
        "network": "N4 / bipartite paper-subject",
        "graph_version": "enriched-cb371912e308",
    },
    "ppr_lift": {
        "name": "Personalized PageRank Lift",
        "definition": "Topic-personalized PageRank divided by global N4 PageRank (alpha=0.85, subject min-paper filter).",
        "denominator": "Global PageRank score of that node in unweighted N4.",
        "network": "N4 (full heterogeneous graph)",
        "graph_version": "enriched-cb371912e308",
    },
    "rca": {
        "name": "Revealed Comparative Advantage (RCA)",
        "definition": "Subject's share within an organization's papers divided by subject's share across the full corpus.",
        "denominator": "Global corpus paper share of subject S.",
        "network": "Organization-Paper-Subject",
        "graph_version": "enriched-cb371912e308",
    },
    "small_world_sigma": {
        "name": "Small-world sigma (σ)",
        "definition": "(C / C_rand) / (L / L_rand), where C is igraph average local clustering (mode='zero') on LCC and L is exact LCC average shortest path.",
        "denominator": "20 Erdos-Renyi G(n,m) and 20 degree-preserving rewired baselines on the LCC.",
        "network": "N1 / N2 / N4 LCC",
        "graph_version": "enriched-cb371912e308",
    },
    "leiden_nmi": {
        "name": "Leiden NMI Stability",
        "definition": "Mean pairwise Normalized Mutual Information across 3 random seeds at fixed resolution.",
        "denominator": "Maximum partition entropy across seed pairs.",
        "network": "N1 / N2 / Research co-occurrence",
        "graph_version": "enriched-cb371912e308",
    },
}


def _read_json(path: Path) -> Any:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _as_float(val: Any, default: float = 0.0) -> float:
    try:
        if val in (None, "", "nan", "NaN"):
            return default
        return float(val)
    except (TypeError, ValueError):
        return default


def _as_int(val: Any, default: int = 0) -> int:
    try:
        if val in (None, "", "nan", "NaN"):
            return default
        return int(float(val))
    except (TypeError, ValueError):
        return default


class NavigatorService:
    """Read-only analytical + GraphRAG + multi-hop QA backend service."""

    def __init__(
        self,
        settings: Settings,
        *,
        repo: Any | None = None,
        store: Any | None = None,
        toolset: RAGToolset | None = None,
        llm: LLMClient | None = None,
    ) -> None:
        self.settings = settings
        self.repo = repo
        self.store = store
        self._injected_toolset = toolset
        self._injected_llm = llm
        self._rag_cfg: dict[str, Any] = {}
        if settings.rag_config_path.is_file():
            self._rag_cfg = yaml.safe_load(settings.rag_config_path.read_text(encoding="utf-8")) or {}

        self.analysis_dir = settings.analysis_v2_dir
        self.rag_dir = settings.rag_reports_dir

        # Preload lightweight analysis-v2 tables
        self.trends_summary: dict[str, Any] = _read_json(self.analysis_dir / "trends" / "trends-summary.json") or {}
        self.display_aliases: dict[str, Any] = _read_json(self.analysis_dir / "trends" / "display-aliases.json") or {}
        self.alias_lookup: dict[str, list[str]] = self._build_alias_lookup()

        self.trends_by_kind: dict[str, list[dict[str, Any]]] = {
            kind: self._parse_trend_rows(_read_csv(self.analysis_dir / "trends" / f"trends-{kind.lower()}.csv"))
            for kind in ("Topic", "Method", "Task", "Dataset")
        }
        self.subject_trend_index: dict[str, dict[str, Any]] = {
            row["id"]: row for rows in self.trends_by_kind.values() for row in rows
        }

        self.ppr_data: dict[str, Any] = _read_json(self.analysis_dir / "ranking" / "personalized-pagerank.json") or {}
        self.groups_summary: dict[str, Any] = _read_json(self.analysis_dir / "communities" / "groups-summary.json") or {}
        self.groups_orgs: list[dict[str, Any]] = [
            {
                "id": r["id"],
                "name": r["name"],
                "papers": _as_int(r.get("papers")),
                "researchers": _as_int(r.get("researchers")),
                "sector": r.get("sector") or "unknown",
                "notable": str(r.get("notable", "")).lower() == "true",
            }
            for r in _read_csv(self.analysis_dir / "communities" / "groups-organizations.csv")
        ]
        self.org_anchored_communities: list[dict[str, Any]] = [
            {
                "community": r["community"],
                "members": _as_int(r.get("members")),
                "size_tier": r.get("size_tier") or ("large" if _as_int(r.get("members")) >= 100 else "standard"),
                "organization_id": r.get("organization", ""),
                "organization_name": r.get("organization_name", ""),
                "top_topic": r.get("top_topic", ""),
                "display_name": r.get("display_name") or f"{r.get('organization_name', '')} — {r.get('top_topic', '')}",
                "share": _as_float(r.get("share")),
                "notable_organization": str(r.get("notable_organization", "")).lower() == "true",
            }
            for r in _read_csv(self.analysis_dir / "communities" / "groups-org-anchored-communities.csv")
        ]
        self.groups_rollup: list[dict[str, Any]] = [
            {
                "parent": r["parent"],
                "parent_name": r["parent_name"],
                "child_organizations": _as_int(r.get("child_organizations")),
                "papers": _as_int(r.get("papers")),
                "parent_is_v4_organization": str(r.get("parent_is_v4_organization", "")).lower() == "true",
                "notable": str(r.get("notable", "")).lower() == "true",
            }
            for r in _read_csv(self.analysis_dir / "communities" / "groups-rollup.csv")
        ]
        self.group_interest_rows: list[dict[str, Any]] = [
            {
                "group": r["group"],
                "subject": r["subject"],
                "subject_name": r["subject_name"],
                "kind": r.get("kind", "Topic"),
                "group_papers": _as_int(r.get("group_papers")),
                "group_papers_in_subject": _as_int(r.get("group_papers_in_subject")),
                "share_of_group": _as_float(r.get("share_of_group")),
                "rca": _as_float(r.get("rca")),
                "first_active_year": _as_int(r.get("first_active_year"), 0) or None,
                "share_2021_2022_mean": _as_float(r.get("share_2021_2022_mean")),
                "share_2024_2025_mean": _as_float(r.get("share_2024_2025_mean")),
                "growth_late_minus_early": _as_float(r.get("growth_late_minus_early")),
            }
            for r in _read_csv(self.analysis_dir / "trends" / "group-interest.csv")
        ]

        self.rising_researchers: list[dict[str, Any]] = [
            {
                "id": r["id"],
                "name": r["name"],
                "recent_papers": _as_int(r.get("recent_papers")),
                "base_papers": _as_int(r.get("base_papers")),
                "share_ratio": _as_float(r.get("share_ratio")),
                "new_entrant": str(r.get("new_entrant", "")).lower() == "true",
                "community": r.get("community", ""),
            }
            for r in _read_csv(self.analysis_dir / "communities" / "rising-researchers.csv")
        ]
        self.n1_csv: list[dict[str, str]] = _read_csv(self.analysis_dir / "communities" / "communities-N1.csv")
        self.n2_csv: list[dict[str, str]] = _read_csv(self.analysis_dir / "communities" / "communities-N2.csv")

        self.smallworld: dict[str, Any] = _read_json(self.analysis_dir / "smallworld" / "smallworld.json") or {}
        self.evolution: dict[str, Any] = _read_json(self.analysis_dir / "smallworld" / "evolution.json") or {}
        self.degree_tail: dict[str, Any] = _read_json(self.analysis_dir / "smallworld" / "degree-tail.json") or {}
        self.rankings: dict[str, Any] = {
            n: (_read_json(self.analysis_dir / "ranking" / f"ranking-{n}.json") or {})
            for n in ("N1", "N2", "N3", "N4")
        }
        self.communities_n1: dict[str, Any] = _read_json(self.analysis_dir / "communities" / "communities-N1.json") or {}
        self.communities_n2: dict[str, Any] = _read_json(self.analysis_dir / "communities" / "communities-N2.json") or {}

        self.enrichment_summary: dict[str, Any] = _read_json(settings.enrichment_summary_path) or {}
        self.enrichment_quality: dict[str, Any] = _read_json(settings.enrichment_quality_path) or {}
        self.cooccurrence: dict[str, Any] = _read_json(settings.cooccurrence_path) or {}

        # Lazy caches for large/optional files & live Neo4j queries
        self._node_names_cache: dict[str, dict[str, str]] = {}
        self._venue_trend_cache: dict[tuple[str, str], dict[str, dict[int, float]]] = {}
        self._vector_store: SQLiteVectorStore | None = None
        self._rag_toolset: RAGToolset | None = None

    def _build_alias_lookup(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = defaultdict(list)
        by_kind = self.display_aliases.get("by_kind", {})
        for kind_groups in by_kind.values():
            if not isinstance(kind_groups, list):
                continue
            for grp in kind_groups:
                members = grp.get("members", []) or grp.get("aliases", []) or []
                names = [str(m.get("name", "")) for m in members if isinstance(m, dict) and m.get("name")]
                ids = [str(m.get("id", "")) for m in members if isinstance(m, dict) and m.get("id")]
                if not names and grp.get("names"):
                    names = [str(n) for n in grp["names"]]
                for mid in ids:
                    if mid:
                        out[mid] = [n for n in names if n]
        return out

    def _parse_trend_rows(self, rows: list[dict[str, str]]) -> list[dict[str, Any]]:
        out = []
        for r in rows:
            sid = r["id"]
            aliases = [a for a in self.alias_lookup.get(sid, []) if a.lower() != r["name"].lower()]
            yearly = [
                {
                    "year": yr,
                    "papers": _as_int(r.get(f"papers_{yr}")),
                    "share": _as_float(r.get(f"share_{yr}")),
                    "yoy": _as_float(r.get(f"yoy_{yr}"), 0.0) if yr > 2021 else None,
                }
                for yr in (2021, 2022, 2023, 2024, 2025)
            ]
            out.append(
                {
                    "kind": r["kind"],
                    "id": sid,
                    "name": r["name"],
                    "class": r["class"],
                    "total_papers": _as_int(r.get("total_papers")),
                    "base_window_papers": _as_int(r.get("base_window_papers")),
                    "recent_window_papers": _as_int(r.get("recent_window_papers")),
                    "base_share": _as_float(r.get("base_share")),
                    "recent_share": _as_float(r.get("recent_share")),
                    "recent_over_base_share": _as_float(r.get("recent_over_base_share")),
                    "slope_of_share": _as_float(r.get("slope_of_share")),
                    "slope_p_value": _as_float(r.get("slope_p_value")),
                    "cagr_of_share_2021_2025": _as_float(r.get("cagr_of_share_2021_2025")),
                    "yearly": yearly,
                    "display_aliases": aliases,
                }
            )
        return out

    def _has_live_neo4j(self) -> bool:
        return self.repo is not None and hasattr(self.repo, "get_driver")

    def _run_read(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if self.repo is None:
            return []
        if hasattr(self.repo, "run_read"):
            try:
                return self.repo.run_read(cypher, params or {})
            except TypeError:
                return self.repo.run_read(cypher)
        return []

    def _load_rag_reports(self) -> dict[str, Any]:
        return _read_json(self.rag_dir / "community-reports.json") or {}

    def _load_research_communities(self) -> dict[str, Any]:
        return _read_json(self.rag_dir / "research-communities.json") or {}

    def _load_entity_descriptions(self) -> dict[str, dict[str, Any]]:
        raw = _read_json(self.rag_dir / "entity-descriptions.json")
        if not raw:
            return {}
        items = raw.get("descriptions", []) if isinstance(raw, dict) else raw
        return {str(d["id"]): d for d in items if isinstance(d, dict) and d.get("id")}

    def _load_demo_cache(self) -> dict[str, Any]:
        return _read_json(self.rag_dir / "demo-cache.json") or {}

    def _get_toolset(self) -> RAGToolset:
        if self._injected_toolset is not None:
            return self._injected_toolset
        if self._rag_toolset is None:
            if self._has_live_neo4j():
                backend = Neo4jToolBackend(
                    uri=self.settings.neo4j_uri,
                    username=self.settings.neo4j_username,
                    password=self.settings.neo4j_password,
                    database=self.settings.neo4j_database,
                    timeout=max(float(self.settings.query_timeout_seconds), 15.0),
                )
            else:
                backend = InMemoryGraphBackend({"nodes": [], "edges": []})
            sg_cfg = self._rag_cfg.get("share_growth", {})
            self._rag_toolset = RAGToolset(
                backend,
                analysis_dir=self.analysis_dir,
                rag_dir=self.rag_dir,
                min_post_total_papers=int(sg_cfg.get("min_post_total_papers", 10)),
                min_post_subject_papers=int(sg_cfg.get("min_post_subject_papers", 2)),
            )
        return self._rag_toolset

    def _get_llm(self) -> LLMClient:
        if self._injected_llm is not None:
            return self._injected_llm
        llm_cfg = self._rag_cfg.get("llm", {})
        cfg = LLMConfig(
            base_url=str(llm_cfg.get("base_url", "http://127.0.0.1:8080/v1")),
            model=str(llm_cfg.get("model", "qwen3.5-4b-q4_k_m")),
            temperature=float(llm_cfg.get("temperature", 0.0)),
            seed=int(llm_cfg.get("seed", 0)),
            max_tokens=int(llm_cfg.get("ask_max_tokens", 900)),
            enable_thinking=bool(llm_cfg.get("enable_thinking", False)),
            timeout=float(llm_cfg.get("timeout", 60.0)),
        )
        return LLMClient(cfg)

    def _get_vector_store(self) -> SQLiteVectorStore | None:
        if self._vector_store is None and self.settings.rag_vectors_sqlite.is_file():
            self._vector_store = SQLiteVectorStore(self.settings.rag_vectors_sqlite)
        return self._vector_store

    # ── 1. Trends ─────────────────────────────────────────────────────────────

    def _venue_yearly_shares(self, kind: str, venue: str) -> dict[str, list[dict[str, Any]]]:
        key = (kind, venue)
        if key in self._venue_trend_cache:
            return self._venue_trend_cache[key]  # type: ignore[return-value]
        if not self._has_live_neo4j():
            return {}
        rel_map = {
            "Topic": "HAS_TOPIC",
            "Method": "USES_METHOD",
            "Task": "ADDRESSES_TASK",
            "Dataset": "USES_DATASET",
        }
        rel = rel_map[kind]
        totals_rows = self._run_read(
            "MATCH (p:Paper)-[:PUBLISHED_IN]->(v:Venue {name: $venue}) "
            "RETURN p.year AS year, count(DISTINCT p) AS total ORDER BY year",
            {"venue": venue},
        )
        year_totals = {int(r["year"]): int(r["total"]) for r in totals_rows if r.get("year")}
        rows = self._run_read(
            f"MATCH (s:{kind})<-[:{rel}]-(p:Paper)-[:PUBLISHED_IN]->(v:Venue {{name: $venue}}) "
            "RETURN s.id AS sid, p.year AS year, count(DISTINCT p) AS c",
            {"venue": venue},
        )
        counts_by_sub: dict[str, dict[int, int]] = defaultdict(dict)
        for r in rows:
            if r.get("sid") and r.get("year"):
                counts_by_sub[str(r["sid"])][int(r["year"])] = int(r["c"])
        out: dict[str, list[dict[str, Any]]] = {}
        for sid, ymap in counts_by_sub.items():
            series = []
            for yr in (2021, 2022, 2023, 2024, 2025):
                tot = year_totals.get(yr, 0)
                cnt = ymap.get(yr, 0)
                series.append({"year": yr, "papers": cnt, "share": (cnt / tot) if tot else 0.0, "yoy": None})
            out[sid] = series
        self._venue_trend_cache[key] = out  # type: ignore[assignment]
        return out

    def get_trends(
        self,
        *,
        kind: str = "Method",
        venue: str = "all",
        period: str = "2021-2025",
        trend_class: str | None = None,
        q: str = "",
        limit: int = 50,
    ) -> dict[str, Any]:
        norm_kind = kind if kind in self.trends_by_kind else "Method"
        period_years_map = {
            "2021-2025": (2021, 2025),
            "2021-2023": (2021, 2023),
            "2022-2025": (2022, 2025),
            "2023-2025": (2023, 2025),
        }
        start_y, end_y = period_years_map.get(period, (2021, 2025))
        rows = [dict(r) for r in self.trends_by_kind.get(norm_kind, [])]
        venue_note = None
        if venue in ("AAAI", "IJCAI"):
            v_map = self._venue_yearly_shares(norm_kind, venue)
            if v_map:
                for r in rows:
                    if r["id"] in v_map:
                        r["yearly"] = v_map[r["id"]]
                        r["total_papers"] = sum(pt["papers"] for pt in r["yearly"])
            else:
                venue_note = f"Venue breakdown for {venue} unavailable offline; showing combined AAAI+IJCAI shares."

        for r in rows:
            ys = [pt for pt in r["yearly"] if start_y <= pt["year"] <= end_y]
            r["period_yearly"] = ys
            if ys:
                r["period_papers"] = sum(pt["papers"] for pt in ys)
                r["period_delta_pp"] = round((ys[-1]["share"] - ys[0]["share"]) * 100.0, 2)

        ql = q.strip().lower()
        if ql:
            rows = [
                r
                for r in rows
                if ql in r["name"].lower()
                or ql in r["id"].lower()
                or any(ql in a.lower() for a in r.get("display_aliases", []))
            ]
        if trend_class:
            rows = [r for r in rows if r["class"] == trend_class]

        rising = sorted(
            [r for r in rows if r["class"] == "rising"],
            key=lambda x: (-x["slope_of_share"], -x["total_papers"]),
        )[:10]
        emerging = sorted(
            [r for r in rows if r["class"] == "emerging"],
            key=lambda x: (-x["recent_window_papers"], -x["slope_of_share"]),
        )[:10]
        declining = sorted(
            [r for r in rows if r["class"] == "declining"],
            key=lambda x: (x["slope_of_share"], -x["total_papers"]),
        )[:10]
        heatmap_rows = sorted(rows, key=lambda x: (-x["total_papers"], x["name"]))[:25]

        return {
            "kind": norm_kind,
            "venue": venue,
            "venue_note": venue_note,
            "period": f"{start_y}-{end_y}",
            "classification_note": self.trends_summary.get(
                "classification_note",
                "descriptive (p <= 0.10 per subject, no multiple-testing correction)",
            ),
            "caveats": self.trends_summary.get("caveats", []),
            "classes": self.trends_summary.get("classes", {}).get(norm_kind, {}),
            "total_matching": len(rows),
            "leaderboards": {"rising": rising, "emerging": emerging, "declining": declining},
            "heatmap": [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "class": r["class"],
                    "years": r["period_yearly"],
                }
                for r in heatmap_rows
            ],
            "items": rows[:limit],
            "metric_definitions": {
                "share": METRIC_DEFINITIONS["share"],
            },
        }

    # ── 2. Subjects (Topic / Method / Task / Dataset) ─────────────────────────

    def list_subjects(self, *, kind: str | None = None, q: str = "", limit: int = 40) -> dict[str, Any]:
        ql = q.strip().lower()
        ppr_subjects = self.ppr_data.get("subjects", {})
        items: list[dict[str, Any]] = []
        seen: set[str] = set()
        kinds = [kind] if kind in self.trends_by_kind else ["Topic", "Method", "Task", "Dataset"]
        for k in kinds:
            ppr_kind = ppr_subjects.get(k, {})
            for r in self.trends_by_kind.get(k, []):
                sid = r["id"]
                if sid in seen:
                    continue
                if ql and not (
                    ql in r["name"].lower()
                    or ql in sid.lower()
                    or any(ql in a.lower() for a in r.get("display_aliases", []))
                ):
                    continue
                seen.add(sid)
                items.append(
                    {
                        "id": sid,
                        "name": r["name"],
                        "kind": k,
                        "class": r["class"],
                        "total_papers": r["total_papers"],
                        "recent_share": r["recent_share"],
                        "cagr": r["cagr_of_share_2021_2025"],
                        "has_ppr": sid in ppr_kind,
                        "display_aliases": r.get("display_aliases", []),
                    }
                )
        items.sort(key=lambda x: (-int(x["has_ppr"]), -int(x["total_papers"]), x["name"]))
        return {
            "total": len(items),
            "items": items[:limit],
            "classification_note": self.trends_summary.get("classification_note", ""),
        }

    def get_subject_detail(self, subject_id: str) -> dict[str, Any] | None:
        trend = self.subject_trend_index.get(subject_id)
        ppr_entry = None
        subject_kind = trend["kind"] if trend else None
        for k, kmap in (self.ppr_data.get("subjects", {}) or {}).items():
            if subject_id in kmap:
                ppr_entry = kmap[subject_id]
                subject_kind = subject_kind or k
                break
        if trend is None and ppr_entry is None:
            return None

        top_block = (ppr_entry or {}).get("top", {})
        top_orgs = sorted(
            top_block.get("Organization", []),
            key=lambda x: (-_as_float(x.get("lift")), -_as_float(x.get("ppr_score"))),
        )
        top_res = sorted(
            top_block.get("Researcher", []),
            key=lambda x: (-_as_float(x.get("lift")), -_as_float(x.get("ppr_score"))),
        )
        related_methods = top_block.get("Method", [])
        related_tasks = top_block.get("Task", [])
        related_datasets = top_block.get("Dataset", [])

        # Augment related co-occurring pairs if live Neo4j available
        if self._has_live_neo4j() and subject_kind in ("Topic", "Method", "Task", "Dataset"):
            rel_in = {
                "Topic": "HAS_TOPIC",
                "Method": "USES_METHOD",
                "Task": "ADDRESSES_TASK",
                "Dataset": "USES_DATASET",
            }[subject_kind]
            papers_rows = self._run_read(
                f"MATCH (s {{id: $sid}})<-[:{rel_in}]-(p:Paper) "
                "OPTIONAL MATCH (p)-[:PUBLISHED_IN]->(v:Venue) "
                "OPTIONAL MATCH (p)<-[c:CITES]-(:Paper) "
                "WITH p, v.name AS venue, count(DISTINCT c) AS cit "
                "RETURN p.id AS paper_id, p.name AS title, p.year AS year, venue, cit AS in_corpus_citations "
                "ORDER BY in_corpus_citations DESC, p.year DESC LIMIT 12",
                {"sid": subject_id},
            )
            if not related_tasks and subject_kind == "Method":
                related_tasks = self._run_read(
                    "MATCH (s:Method {id: $sid})<-[:USES_METHOD]-(p:Paper)-[:ADDRESSES_TASK]->(t:Task) "
                    "RETURN t.id AS id, t.name AS name, count(DISTINCT p) AS co_papers "
                    "ORDER BY co_papers DESC LIMIT 10",
                    {"sid": subject_id},
                )
        else:
            papers_rows = []

        # Matching communities + AI summary
        reports_payload = self._load_rag_reports()
        reports = reports_payload.get("reports", []) if isinstance(reports_payload, dict) else []
        res_comms = (self._load_research_communities().get("communities") or {})
        matching_cids: set[str] = set()
        for cid, comm in res_comms.items():
            if any(m.get("id") == subject_id for m in comm.get("members", [])):
                matching_cids.add(cid)

        matching_communities = []
        subject_name = (trend or {}).get("name") or (ppr_entry or {}).get("name") or subject_id
        sname_low = subject_name.lower()
        for rep in reports:
            cid = str(rep.get("community_id", ""))
            title = str(rep.get("title", "")).lower()
            summary = str(rep.get("summary", "")).lower()
            if cid in matching_cids or sname_low in title or sname_low in summary:
                matching_communities.append(
                    {
                        "community_id": cid,
                        "source": rep.get("network"),
                        "level": rep.get("level"),
                        "title": rep.get("title"),
                        "summary": rep.get("summary"),
                        "key_findings": rep.get("key_findings", []),
                        "rating": rep.get("centrality_rating"),
                        "ai_generated_label": rep.get("ai_generated_label", "AI-generated from graph data"),
                    }
                )
            if len(matching_communities) >= 8:
                break

        edesc = self._load_entity_descriptions().get(subject_id)
        if matching_communities:
            top_rep = matching_communities[0]
            ai_summary = {
                "text": top_rep["summary"],
                "findings": top_rep.get("key_findings", [])[:3],
                "source_community_id": top_rep["community_id"],
                "label": "AI-generated from graph data",
            }
        elif edesc:
            ai_summary = {
                "text": edesc.get("description", ""),
                "findings": [],
                "source_community_id": None,
                "label": edesc.get("provenance_label")
                or ("Wikipedia" if edesc.get("source_kind") == "wikipedia" else "AI-generated from mentions"),
                "source_kind": edesc.get("source_kind"),
                "wikipedia_url": edesc.get("wikipedia_url"),
                "wikipedia_revision_id": edesc.get("wikipedia_revision_id"),
                "attribution": edesc.get("attribution"),
                "license": edesc.get("license"),
            }
        else:
            ai_summary = None

        return {
            "id": subject_id,
            "name": subject_name,
            "kind": subject_kind,
            "trend": trend,
            "classification_note": self.trends_summary.get("classification_note", ""),
            "display_aliases": self.alias_lookup.get(subject_id, []),
            "ppr_primary_rank_by": self.ppr_data.get("primary_rank_by", "lift"),
            "filter_notes": (ppr_entry or {}).get("filter_notes", {}),
            "top_organizations": top_orgs,
            "top_researchers": top_res,
            "related_methods": related_methods,
            "related_tasks": related_tasks,
            "related_datasets": related_datasets,
            "communities": matching_communities,
            "most_cited_papers": papers_rows,
            "summary": ai_summary,
            "metric_definitions": {
                "ppr_lift": METRIC_DEFINITIONS["ppr_lift"],
                "rca": METRIC_DEFINITIONS["rca"],
                "share": METRIC_DEFINITIONS["share"],
            },
        }

    # ── 3. Groups & Organization Rollups ──────────────────────────────────────

    def list_groups(
        self,
        *,
        sector: str | None = None,
        country: str | None = None,
        notable_only: bool = False,
        q: str = "",
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        # Optional live Neo4j enrichment attributes (country_code, wiki_type, parent_name)
        org_meta: dict[str, dict[str, Any]] = {}
        if self._has_live_neo4j():
            rows = self._run_read(
                "MATCH (o:Organization) "
                "OPTIONAL MATCH (o)-[:PART_OF]->(par:Organization) "
                "RETURN o.id AS id, o.country_code AS country_code, o.sector AS sector, "
                "o.wikipedia_url AS wikipedia_url, o.wikidata_qid AS wikidata_qid, "
                "collect(DISTINCT par.name)[..3] AS parents"
            )
            for r in rows:
                org_meta[str(r["id"])] = dict(r)

        ql = q.strip().lower()
        filtered_orgs: list[dict[str, Any]] = []
        sectors: dict[str, int] = defaultdict(int)
        countries: dict[str, int] = defaultdict(int)
        for o in self.groups_orgs:
            meta = org_meta.get(o["id"], {})
            cc = meta.get("country_code") or ""
            sec = meta.get("sector") or o["sector"]
            sectors[sec] += 1
            if cc:
                countries[cc] += 1
            if sector and sec != sector:
                continue
            if country and cc != country:
                continue
            if notable_only and not o["notable"]:
                continue
            if ql and ql not in o["name"].lower() and ql not in o["id"].lower():
                continue
            filtered_orgs.append(
                {
                    **o,
                    "sector": sec,
                    "country_code": cc or None,
                    "wikidata_qid": meta.get("wikidata_qid"),
                    "wikipedia_url": meta.get("wikipedia_url"),
                    "parents": meta.get("parents", []),
                }
            )

        filtered_anchored = [
            c
            for c in self.org_anchored_communities
            if not ql or ql in c["display_name"].lower() or ql in c["organization_name"].lower()
        ]

        # Build compact Org x Topic RCA matrix for top 18 filtered/overall orgs and top 12 Topics
        top_org_ids = {o["id"] for o in filtered_orgs[:18]}
        topic_totals: dict[str, int] = defaultdict(int)
        org_topic_cells: list[dict[str, Any]] = []
        org_names = {o["id"]: o["name"] for o in self.groups_orgs}
        for row in self.group_interest_rows:
            if row["kind"] != "Topic":
                continue
            gid = row["group"]
            # group string may look like "organization:Foo (organization:I123)" or bare id
            matched_oid = next((oid for oid in top_org_ids if oid in gid), None)
            if not matched_oid:
                continue
            topic_totals[row["subject_name"]] += row["group_papers_in_subject"]
            org_topic_cells.append(
                {
                    "organization_id": matched_oid,
                    "organization_name": org_names.get(matched_oid, matched_oid),
                    "subject_id": row["subject"],
                    "subject_name": row["subject_name"],
                    "papers": row["group_papers_in_subject"],
                    "share": row["share_of_group"],
                    "rca": row["rca"],
                }
            )
        top_topics = [t for t, _ in sorted(topic_totals.items(), key=lambda kv: -kv[1])[:12]]
        matrix_cells = [c for c in org_topic_cells if c["subject_name"] in set(top_topics)]

        return {
            "summary": self.groups_summary,
            "government_exclusion_note": (
                "Government bodies (55 Wikidata parent classes / 112 edges, including the State Council of the PRC) "
                "are excluded from PART_OF roll-ups; research universities and academies such as CAS and Tsinghua are retained."
            ),
            "sectors": [{"name": k, "count": v} for k, v in sorted(sectors.items(), key=lambda kv: -kv[1])],
            "countries": [{"code": k, "count": v} for k, v in sorted(countries.items(), key=lambda kv: -kv[1])[:40]],
            "total_organizations": len(filtered_orgs),
            "organizations": filtered_orgs[offset : offset + limit],
            "org_anchored_communities": filtered_anchored[:60],
            "rollup": self.groups_rollup[:40],
            "matrix": {
                "organizations": [org_names[oid] for oid in [o["id"] for o in filtered_orgs[:18]] if oid in org_names],
                "topics": top_topics,
                "cells": matrix_cells,
            },
            "metric_definitions": {"rca": METRIC_DEFINITIONS["rca"]},
        }

    def get_group_detail(self, group_id: str) -> dict[str, Any] | None:
        base = next((o for o in self.groups_orgs if o["id"] == group_id), None)
        if base is None and not self._has_live_neo4j():
            return None
        profile: dict[str, Any] = dict(base) if base else {"id": group_id, "name": group_id}
        partners: list[dict[str, Any]] = []
        top_papers: list[dict[str, Any]] = []
        child_units: list[dict[str, Any]] = []
        if self._has_live_neo4j():
            rows = self._run_read(
                "MATCH (o:Organization {id: $gid}) "
                "OPTIONAL MATCH (o)-[:PART_OF]->(p:Organization) "
                "RETURN o.name AS name, o.sector AS sector, o.country_code AS country_code, "
                "o.wikidata_qid AS wikidata_qid, o.wikipedia_url AS wikipedia_url, "
                "collect(DISTINCT {id: p.id, name: p.name}) AS parents",
                {"gid": group_id},
            )
            if not rows and base is None:
                return None
            if rows:
                profile.update({k: v for k, v in rows[0].items() if v is not None})
            partners = self._run_read(
                "MATCH (o:Organization {id: $gid})-[r:COLLABORATED_WITH]-(other:Organization) "
                "RETURN other.id AS id, other.name AS name, other.sector AS sector, "
                "other.country_code AS country_code, r.support_count AS papers, r.fractional_weight AS weight "
                "ORDER BY papers DESC, weight DESC LIMIT 20",
                {"gid": group_id},
            )
            child_units = self._run_read(
                "MATCH (c:Organization)-[:PART_OF]->(o:Organization {id: $gid}) "
                "RETURN c.id AS id, c.name AS name, c.sector AS sector LIMIT 25",
                {"gid": group_id},
            )
            top_papers = self._run_read(
                "MATCH (o:Organization {id: $gid})<-[:AFFILIATED_WITH]-(:Researcher)-[:AUTHORED]->(p:Paper) "
                "OPTIONAL MATCH (p)-[:PUBLISHED_IN]->(v:Venue) "
                "RETURN DISTINCT p.id AS paper_id, p.name AS title, p.year AS year, v.name AS venue "
                "ORDER BY p.year DESC LIMIT 15",
                {"gid": group_id},
            )

        specializations = sorted(
            [
                row
                for row in self.group_interest_rows
                if group_id in row["group"]
            ],
            key=lambda x: (-x["rca"], -x["group_papers_in_subject"]),
        )[:30]
        anchored = [c for c in self.org_anchored_communities if c["organization_id"] == group_id]
        edesc = self._load_entity_descriptions().get(group_id)

        return {
            "profile": profile,
            "description": edesc,
            "specializations": specializations,
            "partners": partners,
            "child_units": child_units,
            "org_anchored_communities": anchored,
            "top_papers": top_papers,
        }

    # ── 4. Communities (Super-nodes & S3 + GraphRAG Reports) ──────────────────

    def _build_community_catalog(self) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
        reports_payload = self._load_rag_reports()
        rep_by_cid = {
            r["community_id"]: r
            for r in (reports_payload.get("reports", []) if isinstance(reports_payload, dict) else [])
            if r.get("community_id")
        }
        res_comm_doc = self._load_research_communities()
        res_comms_map = res_comm_doc.get("communities", {}) if isinstance(res_comm_doc, dict) else {}
        rising_by_cid: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for rr in self.rising_researchers:
            rising_by_cid[f"N1:{rr['community']}"].append(rr)

        nodes: list[dict[str, Any]] = []
        by_id: dict[str, dict[str, Any]] = {}

        # Research L1 & L0 communities
        for cid, comm in res_comms_map.items():
            lvl_num = int(comm.get("level", 0))
            src_tag = "research_L1" if lvl_num == 1 else "research_L0"
            rep = rep_by_cid.get(cid, {})
            members_list = comm.get("members", [])
            member_ids = [m["id"] if isinstance(m, dict) else str(m) for m in members_list]
            item = {
                "community_id": cid,
                "source": src_tag,
                "level": lvl_num,
                "size": int(comm.get("size", len(member_ids))),
                "size_tier": "large" if int(comm.get("size", 0)) >= 100 else "standard",
                "title": rep.get("title") or ", ".join(m.get("name", "") for m in comm.get("top_entities", [])[:3]) or cid,
                "summary": rep.get("summary", ""),
                "key_findings": rep.get("key_findings", []),
                "centrality_rating": rep.get("centrality_rating"),
                "centrality_rationale": rep.get("centrality_rationale"),
                "dominant_topics": comm.get("top_entities", [])[:6],
                "papers_by_year": comm.get("papers_by_year", {}),
                "top_papers": comm.get("top_papers", [])[:8],
                "top_orgs": comm.get("top_organizations", [])[:6],
                "members": members_list,
                "member_ids": member_ids,
                "parent_id": comm.get("parent_id"),
                "children": comm.get("children", []),
                "hubs": [],
                "brokers": [],
                "rising_researchers": [],
                "ai_generated_label": rep.get("ai_generated_label", "AI-generated from graph data") if rep else None,
            }
            nodes.append(item)
            by_id[cid] = item

        # N1 & N2 S3 communities
        n1_labels = self.communities_n1.get("labels", {})
        n1_keys = self.communities_n1.get("key_individuals", {})
        for r in self.n1_csv:
            raw_cid = r["community"]
            cid = f"N1:{raw_cid}"
            rep = rep_by_cid.get(cid, {})
            size = _as_int(r.get("size"))
            item = {
                "community_id": cid,
                "source": "N1",
                "level": 1,
                "size": size,
                "size_tier": "large" if size >= 100 else "standard",
                "title": rep.get("title") or f"N1 Community {raw_cid}: {r.get('label_topic', '').split(';')[0].strip()}",
                "summary": rep.get("summary", ""),
                "key_findings": rep.get("key_findings", []),
                "centrality_rating": rep.get("centrality_rating"),
                "dominant_topics": [t.strip() for t in r.get("label_topic", "").split(";") if t.strip()][:5],
                "label_method": r.get("label_method", ""),
                "label_task": r.get("label_task", ""),
                "label_organization": r.get("label_organization", ""),
                "hubs": [x.strip() for x in r.get("hubs", "").split(";") if x.strip()],
                "brokers": [x.strip() for x in r.get("brokers_participation", "").split(";") if x.strip()],
                "brokers_betweenness": [x.strip() for x in r.get("brokers_betweenness", "").split(";") if x.strip()],
                "hub_ids": (n1_keys.get(raw_cid, {}) or {}).get("hubs", []),
                "broker_ids": (n1_keys.get(raw_cid, {}) or {}).get("brokers_participation", []),
                "topic_details": (n1_labels.get(raw_cid, {}) or {}).get("Topic", []),
                "rising_researchers": rising_by_cid.get(cid, []),
                "ai_generated_label": "AI-generated from graph data" if rep else None,
            }
            nodes.append(item)
            by_id[cid] = item

        for r in self.n2_csv:
            raw_cid = r["community"]
            cid = f"N2:{raw_cid}"
            rep = rep_by_cid.get(cid, {})
            size = _as_int(r.get("size"))
            item = {
                "community_id": cid,
                "source": "N2",
                "level": 1,
                "size": size,
                "size_tier": "large" if size >= 100 else "standard",
                "title": rep.get("title") or f"N2 Community {raw_cid}: {r.get('label_topic', '').split(';')[0].strip()}",
                "summary": rep.get("summary", ""),
                "key_findings": rep.get("key_findings", []),
                "centrality_rating": rep.get("centrality_rating"),
                "dominant_topics": [t.strip() for t in r.get("label_topic", "").split(";") if t.strip()][:5],
                "label_method": r.get("label_method", ""),
                "label_organization": r.get("label_organization", ""),
                "hubs": [x.strip() for x in r.get("hubs", "").split(";") if x.strip()],
                "brokers": [x.strip() for x in r.get("brokers_participation", "").split(";") if x.strip()],
                "brokers_betweenness": [x.strip() for x in r.get("brokers_betweenness", "").split(";") if x.strip()],
                "rising_researchers": [],
                "ai_generated_label": "AI-generated from graph data" if rep else None,
            }
            nodes.append(item)
            by_id[cid] = item

        return nodes, by_id

    def list_communities(self, *, source: str = "research_L1", q: str = "", limit: int = 100) -> dict[str, Any]:
        all_nodes, _ = self._build_community_catalog()
        filtered = [n for n in all_nodes if n["source"] == source]
        ql = q.strip().lower()
        if ql:
            filtered = [
                n
                for n in filtered
                if ql in n["title"].lower()
                or ql in n["community_id"].lower()
                or ql in str(n.get("summary", "")).lower()
                or any(ql in str(t).lower() for t in n.get("dominant_topics", []))
            ]
        filtered.sort(key=lambda x: (-x["size"], x["community_id"]))

        # Super-node edges (parent hierarchy for research_L0 or topic overlap for visual layout)
        edges: list[dict[str, Any]] = []
        shown = filtered[:limit]
        shown_ids = {n["community_id"] for n in shown}
        if source in ("research_L1", "N1", "N2"):
            for i in range(len(shown)):
                ti = {str(x.get("name", x) if isinstance(x, dict) else x).lower() for x in shown[i].get("dominant_topics", [])}
                for j in range(i + 1, min(i + 12, len(shown))):
                    tj = {str(x.get("name", x) if isinstance(x, dict) else x).lower() for x in shown[j].get("dominant_topics", [])}
                    overlap = ti & tj
                    if overlap:
                        edges.append(
                            {
                                "source": shown[i]["community_id"],
                                "target": shown[j]["community_id"],
                                "weight": len(overlap),
                                "shared": sorted(overlap)[:3],
                            }
                        )
        elif source == "research_L0":
            for n in shown:
                if n.get("parent_id") and n["parent_id"] in shown_ids:
                    edges.append({"source": n["community_id"], "target": n["parent_id"], "weight": 1, "shared": ["hierarchy"]})

        counts_by_source: dict[str, int] = defaultdict(int)
        for n in all_nodes:
            counts_by_source[n["source"]] += 1

        return {
            "source": source,
            "counts_by_source": dict(counts_by_source),
            "n2_resolution_note": "S3 N2 res=1.2 yields 15 non-singleton communities (>=10 members); res=1.0 collapses into 1 giant cluster.",
            "supernodes": shown,
            "edges": edges,
            "rising_researchers": self.rising_researchers[:30],
        }

    def get_community_detail(self, community_id: str) -> dict[str, Any] | None:
        _, by_id = self._build_community_catalog()
        return by_id.get(community_id)

    def get_community_members(self, community_id: str, *, limit: int = 40, offset: int = 0) -> dict[str, Any] | None:
        _, by_id = self._build_community_catalog()
        comm = by_id.get(community_id)
        if comm is None:
            return None

        members: list[dict[str, Any]] = []
        if community_id.startswith("research:"):
            raw_members = comm.get("members", [])
            total = len(raw_members)
            page_items = raw_members[offset : offset + limit]
            members = [
                {
                    "id": m["id"],
                    "name": m.get("name", m["id"]),
                    "label": m.get("label", m["id"].split(":")[0].title()),
                    "papers": m.get("papers"),
                    "trend_class": m.get("trend_class"),
                }
                if isinstance(m, dict)
                else {"id": str(m), "name": str(m), "label": str(m).split(":")[0].title()}
                for m in page_items
            ]
            return {"community_id": community_id, "total": total, "members": members}

        if community_id.startswith("N1:") or community_id.startswith("N2:"):
            net, raw_cid = community_id.split(":", 1)
            mem_path = self.analysis_dir / "communities" / f"membership-{net}.csv.gz"
            matched_ids: list[str] = []
            if mem_path.is_file():
                with gzip.open(mem_path, "rt", encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        if row.get("level0") == raw_cid:
                            matched_ids.append(row["id"])
            total = len(matched_ids)
            page_ids = matched_ids[offset : offset + limit]
            if page_ids and self._has_live_neo4j():
                rows = self._run_read(
                    "MATCH (n) WHERE n.id IN $ids RETURN n.id AS id, n.name AS name, labels(n)[0] AS label",
                    {"ids": page_ids},
                )
                row_map = {str(r["id"]): r for r in rows}
                members = [
                    {
                        "id": mid,
                        "name": row_map.get(mid, {}).get("name", mid),
                        "label": row_map.get(mid, {}).get("label", "Researcher" if net == "N1" else "Organization"),
                    }
                    for mid in page_ids
                ]
            else:
                lbl = "Researcher" if net == "N1" else "Organization"
                members = [{"id": mid, "name": mid, "label": lbl} for mid in page_ids]
            return {"community_id": community_id, "total": total, "members": members}

        return {"community_id": community_id, "total": 0, "members": []}

    # ── 5. Network Science (S1–S3) ────────────────────────────────────────────

    def get_network_science(self) -> dict[str, Any]:
        return {
            "config_version": self.smallworld.get("config_version", "analysis-final-exam-v2"),
            "graph_version": self.smallworld.get("graph_version", "enriched-cb371912e308"),
            "clustering_definition": "igraph average local clustering, mode='zero', evaluated on the largest connected component (LCC).",
            "smallworld": self.smallworld,
            "evolution": self.evolution,
            "degree_tail": self.degree_tail,
            "ranking": {
                n: {
                    "nodes": r.get("nodes"),
                    "edges": r.get("edges"),
                    "directed": r.get("directed"),
                    "weighted_pagerank": r.get("weighted_pagerank"),
                    "sparsity_note": r.get("sparsity_note"),
                    "comparison_with_pagerank": r.get("comparison_with_pagerank"),
                    "top": r.get("top") or r.get("top_by_label"),
                }
                for n, r in self.rankings.items()
            },
            "communities_summary": {
                "N1": {
                    "headline": self.communities_n1.get("headline"),
                    "nmi_across_seeds": self.communities_n1.get("nmi_across_seeds"),
                    "runs": self.communities_n1.get("runs"),
                },
                "N2": {
                    "headline": self.communities_n2.get("headline"),
                    "nmi_across_seeds": self.communities_n2.get("nmi_across_seeds"),
                    "runs": self.communities_n2.get("runs"),
                },
            },
            "metric_definitions": METRIC_DEFINITIONS,
        }

    # ── 6. Node 360 ───────────────────────────────────────────────────────────

    def get_node360(self, node_id: str) -> dict[str, Any] | None:
        props: dict[str, Any] | None = None
        neighbors: list[dict[str, Any]] = []
        papers: list[dict[str, Any]] = []
        sparkline: list[dict[str, Any]] = []

        if self._has_live_neo4j():
            rows = self._run_read(
                "MATCH (n {id: $nid}) RETURN labels(n) AS labels, properties(n) AS props LIMIT 1",
                {"nid": node_id},
            )
            if not rows:
                return None
            labels = [lbl for lbl in (rows[0].get("labels") or []) if not lbl.startswith("Rag")]
            props = dict(rows[0]["props"] or {})
            props["_label"] = labels[0] if labels else "Entity"

            neighbors = self._run_read(
                "MATCH (n {id: $nid})-[r]-(m) WHERE NOT any(l IN labels(m) WHERE l STARTS WITH 'Rag') "
                "RETURN type(r) AS relation, startNode(r).id = $nid AS outgoing, "
                "m.id AS id, m.name AS name, labels(m)[0] AS label, "
                "r.support_count AS support_count, r.evidence_kind AS evidence_kind "
                "LIMIT 45",
                {"nid": node_id},
            )
            label0 = props["_label"]
            if label0 == "Paper":
                sparkline = [{"year": props.get("year"), "papers": 1}] if props.get("year") else []
            else:
                year_rows = self._run_read(
                    "MATCH (n {id: $nid})-[]-(p:Paper) "
                    "OPTIONAL MATCH (p)-[:PUBLISHED_IN]->(v:Venue) "
                    "WITH p.year AS year, collect(DISTINCT {paper_id: p.id, title: p.name, year: p.year, venue: v.name}) AS plist "
                    "RETURN year, size(plist) AS papers, plist[..5] AS sample ORDER BY year",
                    {"nid": node_id},
                )
                ycounts = {int(r["year"]): int(r["papers"]) for r in year_rows if r.get("year")}
                sparkline = [{"year": y, "papers": ycounts.get(y, 0)} for y in range(2021, 2026)]
                for r in year_rows:
                    papers.extend(r.get("sample") or [])
                papers = papers[:15]
        elif self.repo is not None and hasattr(self.repo, "get_node_by_id"):
            node = self.repo.get_node_by_id(node_id)
            if node is None:
                return None
            props = dict(node)
        else:
            return None

        # Lookup precomputed ranking / community metrics if available
        metrics: dict[str, Any] = {}
        label0 = str(props.get("_label", ""))
        for net_key, rk in self.rankings.items():
            top_block = rk.get("top") or rk.get("top_by_label") or {}
            candidates = top_block if isinstance(top_block, list) else top_block.get(label0, [])
            for item in candidates:
                if item.get("id") == node_id:
                    metrics[net_key] = item
                    break

        edesc = self._load_entity_descriptions().get(node_id)
        if edesc:
            description = {
                "text": edesc.get("description", ""),
                "label": edesc.get("provenance_label")
                or ("Wikipedia" if edesc.get("source_kind") == "wikipedia" else "AI-generated from mentions"),
                "source_kind": edesc.get("source_kind"),
                "wikipedia_url": edesc.get("wikipedia_url"),
                "wikipedia_revision_id": edesc.get("wikipedia_revision_id"),
                "attribution": edesc.get("attribution"),
                "license": edesc.get("license"),
            }
        elif props.get("wikipedia_url"):
            description = {
                "text": f"Linked to Wikipedia/Wikidata ({props.get('wikidata_qid', '')}).",
                "label": f"Wikipedia (rev {props.get('wikipedia_revision_id', '—')}, CC BY-SA 4.0)",
                "source_kind": "wikipedia",
                "wikipedia_url": props.get("wikipedia_url"),
                "wikipedia_revision_id": props.get("wikipedia_revision_id"),
                "attribution": "Text from English Wikipedia contributors, licensed under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/).",
                "license": "CC BY-SA 4.0",
            }
        else:
            description = None

        return {
            "id": node_id,
            "label": label0,
            "name": props.get("name", node_id),
            "properties": props,
            "description": description,
            "metrics": metrics,
            "trend": self.subject_trend_index.get(node_id),
            "sparkline": sparkline,
            "neighbors": neighbors,
            "papers": papers,
        }

    # ── 7. About the Data (E1-E4 & Versions) ──────────────────────────────────

    def get_about_data(self) -> dict[str, Any]:
        rag_summary = _read_json(self.rag_dir / "index-summary.json") or {}
        rag_stats = _read_json(self.rag_dir / "report-stats.json") or {}
        return {
            "versions": {
                "v4_base": self.enrichment_summary.get("base_graph_version", "release-d3c788c3114a"),
                "v5_enriched": self.enrichment_summary.get("graph_version", "enriched-cb371912e308"),
                "v5_sha256": self.enrichment_summary.get("graph_sha256"),
                "analysis": self.smallworld.get("config_version", "analysis-final-exam-v2"),
                "rag": self._rag_cfg.get("version", "rag-v1"),
            },
            "counts": self.enrichment_summary.get("counts", {}),
            "e4_v3_quality": self.enrichment_quality.get("e4_v3", {}),
            "counts_v1_v2_v3": self.enrichment_quality.get("counts_v1_v2_v3", {}),
            "rag_index": rag_summary,
            "rag_reports": rag_stats,
            "runtime_model": {
                "model_id": "Qwen/Qwen3.5-4B (Q4_K_M, llama.cpp)",
                "temperature": 0.0,
                "enable_thinking": False,
                "embeddings": "sentence-transformers/all-MiniLM-L6-v2",
            },
            "ai_assessment_disclosure": (
                "All quality estimates (Wilson 95% confidence intervals) and GraphRAG summaries in this release "
                "are AI-assessed or AI-generated from graph data. They are not human annotations or independently validated gold labels."
            ),
        }

    # ── 8. Extended Enriched Explorer ─────────────────────────────────────────

    def get_explorer_enriched_schema(self) -> dict[str, Any]:
        return {
            "graph_version": "enriched-cb371912e308",
            "labels": list(ENRICHED_LABELS),
            "predicates": list(ENRICHED_PREDICATES),
        }

    def search_explorer_enriched(self, q: str = "", labels: list[str] | None = None, limit: int = 30) -> dict[str, Any]:
        allowed = [lbl for lbl in (labels or ENRICHED_LABELS) if lbl in ENRICHED_LABELS]
        if not self._has_live_neo4j():
            return {"query": q, "results": []}
        rows = self._run_read(
            "MATCH (n) WHERE labels(n)[0] IN $labels "
            "AND ($q = '' OR toLower(coalesce(n.name, '')) CONTAINS toLower($q) OR toLower(n.id) CONTAINS toLower($q)) "
            "RETURN n.id AS id, coalesce(n.name, n.id) AS name, labels(n)[0] AS label, "
            "n.year AS year, n.sector AS sector LIMIT $limit",
            {"labels": allowed, "q": q.strip(), "limit": limit},
        )
        return {"query": q, "results": rows}

    def get_explorer_enriched_neighbors(
        self,
        node_id: str,
        *,
        relations: list[str] | None = None,
        limit: int = 40,
    ) -> dict[str, Any]:
        allowed_rels = [p["relation"] for p in ENRICHED_PREDICATES]
        filter_rels = [r for r in (relations or allowed_rels) if r in set(allowed_rels)]
        if not self._has_live_neo4j():
            return {"center_id": node_id, "nodes": [], "edges": []}
        rows = self._run_read(
            "MATCH (c {id: $nid})-[r]-(m) "
            "WHERE type(r) IN $rels AND NOT any(l IN labels(m) WHERE l STARTS WITH 'Rag') "
            "RETURN c.id AS c_id, coalesce(c.name, c.id) AS c_name, labels(c)[0] AS c_label, "
            "m.id AS id, coalesce(m.name, m.id) AS name, labels(m)[0] AS label, "
            "type(r) AS relation, startNode(r).id AS source, endNode(r).id AS target, "
            "coalesce(r.support_count, 1) AS support_count, coalesce(r.evidence_kind, 'extracted') AS evidence_kind "
            "LIMIT $limit",
            {"nid": node_id, "rels": filter_rels, "limit": limit},
        )
        nodes_map: dict[str, dict[str, Any]] = {}
        edges: list[dict[str, Any]] = []
        for idx, r in enumerate(rows):
            nodes_map[r["c_id"]] = {"id": r["c_id"], "name": r["c_name"], "label": r["c_label"]}
            nodes_map[r["id"]] = {"id": r["id"], "name": r["name"], "label": r["label"]}
            edges.append(
                {
                    "id": f"e:{r['relation']}:{r['source']}:{r['target']}:{idx}",
                    "relation": r["relation"],
                    "source": r["source"],
                    "target": r["target"],
                    "support_count": r["support_count"],
                    "evidence_kind": r["evidence_kind"],
                }
            )
        return {"center_id": node_id, "nodes": list(nodes_map.values()), "edges": edges}

    # ── 9. Ask (Demos + Live Multi-hop / GraphRAG) ────────────────────────────

    def _get_embed_fn(self):
        if getattr(self, "_embed_fn", None) is None and self.settings.rag_vectors_sqlite.is_file():
            from sentence_transformers import SentenceTransformer
            model_name = (self._rag_cfg.get("embeddings") or {}).get("model_name", "sentence-transformers/all-MiniLM-L6-v2")
            model = SentenceTransformer(model_name, device="cpu")
            self._embed_fn = lambda text: model.encode([text], normalize_embeddings=True, show_progress_bar=False)[0]
        return getattr(self, "_embed_fn", None)

    @staticmethod
    def _normalize_ask_result(res: dict[str, Any]) -> dict[str, Any]:
        out = dict(res)
        if "subgraph" not in out:
            out["subgraph"] = {
                "nodes": list(out.get("subgraph_nodes") or []),
                "edges": list(out.get("subgraph_edges") or []),
            }
        if "citations" not in out:
            out["citations"] = list(out.get("paper_ids") or [])
        if "faithfulness" not in out:
            out["faithfulness"] = {
                "passed": bool(out.get("faithfulness_passed", True)),
                "errors": list(out.get("faithfulness_errors") or []),
            }
        if "ambiguous" not in out:
            raw_dis = out.get("disambiguation") or []
            out["ambiguous"] = [
                {
                    "slot": d.get("mention", d.get("slot", "")),
                    "query": d.get("mention", d.get("query", "")),
                    "candidates": d.get("candidates", []),
                }
                for d in raw_dis
            ]
        out.setdefault("ai_generated_label", "AI-generated from graph data")
        return out

    def list_ask_demos(self) -> dict[str, Any]:
        cache_payload = self._load_demo_cache()
        cached_by_id = {d["demo_id"]: d for d in cache_payload.get("demos", []) if isinstance(d, dict)}
        demos = []
        for d in SCRIPTED_DEMO_QUESTIONS:
            c = cached_by_id.get(d["demo_id"], {})
            res = self._normalize_ask_result(c["result"]) if c.get("result") else None
            demos.append(
                {
                    **d,
                    "cached": bool(res),
                    "result": res,
                    "latency_seconds": c.get("total_latency_s") or c.get("latency_seconds"),
                }
            )
        return {"demos": demos, "generated_at": cache_payload.get("generated_at")}

    def _lookup_cached_demo(self, question: str) -> dict[str, Any] | None:
        cache_payload = self._load_demo_cache()
        ql = question.strip().lower()
        for d in cache_payload.get("demos", []):
            if isinstance(d, dict) and str(d.get("question", "")).strip().lower() == ql and d.get("result"):
                res = self._normalize_ask_result(d["result"])
                res["cached_demo_id"] = d.get("demo_id")
                res["from_cache"] = True
                return res
        return None

    def ask(
        self,
        *,
        question: str,
        mode: str = "auto",
        use_cache: bool = False,
        resolved_overrides: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        if use_cache and not resolved_overrides:
            cached = self._lookup_cached_demo(question)
            if cached is not None:
                return cached
        res = run_ask(
            question,
            toolset=self._get_toolset(),
            llm=self._get_llm(),
            mode=mode,
            resolved_overrides=resolved_overrides,
            vector_store=self._get_vector_store(),
            embed_fn=self._get_embed_fn(),
            reports_path=self.rag_dir / "community-reports.json",
        )
        res = self._normalize_ask_result(res)
        res["from_cache"] = False
        return res

    def stream_ask_events(
        self,
        *,
        question: str,
        mode: str = "auto",
        use_cache: bool = False,
        resolved_overrides: dict[str, str] | None = None,
    ) -> Iterator[dict[str, Any]]:
        if use_cache and not resolved_overrides:
            cached = self._lookup_cached_demo(question)
            if cached is not None:
                yield {"event": "status", "data": {"stage": "cached", "mode": cached.get("mode", mode)}}
                yield {"event": "parsed", "data": {"parsed": cached.get("parsed", {}), "linked": cached.get("linked", [])}}
                yield {"event": "plan", "data": {"plan": cached.get("plan", []), "linked": cached.get("linked", [])}}
                for st in cached.get("steps", []):
                    yield {"event": "step", "data": st}
                yield {"event": "subgraph", "data": cached.get("subgraph", {"nodes": [], "edges": []})}
                ans = cached.get("answer", "")
                if ans:
                    yield {"event": "token", "data": {"text": ans}}
                yield {"event": "citations", "data": {"paper_ids": cached.get("citations", [])}}
                yield {"event": "final", "data": cached}
                return

        for ev in stream_ask(
            question,
            toolset=self._get_toolset(),
            llm=self._get_llm(),
            mode=mode,
            resolved_overrides=resolved_overrides,
            vector_store=self._get_vector_store(),
            embed_fn=self._get_embed_fn(),
            reports_path=self.rag_dir / "community-reports.json",
        ):
            etype = ev.get("event")
            data = ev.get("data")
            if etype == "stage":
                yield {"event": "status", "data": data}
            elif etype == "disambiguate":
                yield {"event": "ambiguous", "data": self._normalize_ask_result(data)}
            elif etype == "done":
                norm = self._normalize_ask_result(data)
                norm["from_cache"] = False
                yield {"event": "final", "data": norm}
            elif etype in ("parsed", "plan", "step", "subgraph", "token", "citations"):
                yield {"event": etype, "data": data}
