"""Read-only adapter for local release artifacts (analysis, summary, network views, and evidence ledger)."""

from collections import defaultdict
import json
from pathlib import Path
import threading
from typing import Any

import yaml

from backend.config import REPO_ROOT


class ArtifactStore:
    """Thread-safe, read-only store over precomputed analysis and evidence artifacts.

    Loads small/medium summary and analysis files eagerly (~0.5s) and indexes the 213 MB
    full graph.json evidence/affiliation ledger lazily or in a background warmup thread.
    """

    def __init__(
        self,
        *,
        summary_path: Path,
        analysis_path: Path,
        network_views_path: Path,
        audit_results_path: Path,
        graph_artifact_path: Path,
        quality_config_path: Path | None = None,
        topic_eval_path: Path | None = None,
        historical_topic_reuse_path: Path | None = None,
    ) -> None:
        self.summary_path = summary_path
        self.analysis_path = analysis_path
        self.network_views_path = network_views_path
        self.audit_results_path = audit_results_path
        self.graph_artifact_path = graph_artifact_path
        self.quality_config_path = quality_config_path or (
            REPO_ROOT / "configs" / "quality-agent-release-v2.yaml"
        )
        self.topic_eval_path = topic_eval_path or (
            REPO_ROOT / "reports" / "release-v3" / "topic-eval-agent.json"
        )
        self.historical_topic_reuse_path = historical_topic_reuse_path or (
            REPO_ROOT / "reports" / "release-v4" / "historical-topic-reuse-v2.json"
        )

        self.summary_data: dict[str, Any] = {}
        self.analysis_data: dict[str, Any] = {}
        self.network_views_data: dict[str, Any] = {}
        self.audit_results_data: dict[str, Any] = {}
        self.quality_config_data: dict[str, Any] = {}
        self.topic_eval_data: dict[str, Any] = {}
        self.historical_topic_reuse_data: dict[str, Any] = {}

        # Indexed full-projection metrics by node_id
        self.node_metrics: dict[str, dict[str, Any]] = {}
        # Researcher communities: community_id -> list of member researcher_ids
        self.researcher_communities: dict[str, list[str]] = {}
        self.researcher_community_profiles: dict[str, dict[str, Any]] = {}
        # Organization communities: community_id -> list of member organization_ids
        self.organization_communities: dict[str, list[str]] = {}
        # Organization topic profiles: organization_id -> list of topic profile dicts
        self.org_topic_profiles: dict[str, list[dict[str, Any]]] = defaultdict(list)

        # Lazy evidence & affiliation ledger from data/processed/release-graph-v4/graph.json
        self._ledger_lock = threading.Lock()
        self._ledger_loaded = False
        self.evidence_by_id: dict[str, dict[str, Any]] = {}
        self.affiliations_by_researcher_org: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        self.affiliations_by_paper: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.affiliations_by_researcher: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.affiliations_by_org: dict[str, list[dict[str, Any]]] = defaultdict(list)

        self._load_fast_artifacts()

    def _load_fast_artifacts(self) -> None:
        if self.summary_path.exists():
            self.summary_data = json.loads(self.summary_path.read_bytes())
        if self.network_views_path.exists():
            self.network_views_data = json.loads(self.network_views_path.read_bytes())
        if self.audit_results_path.exists():
            self.audit_results_data = json.loads(self.audit_results_path.read_bytes())
        if self.quality_config_path.exists():
            self.quality_config_data = yaml.safe_load(self.quality_config_path.read_text(encoding="utf-8")) or {}
        if self.topic_eval_path.exists():
            self.topic_eval_data = json.loads(self.topic_eval_path.read_bytes())
        if self.historical_topic_reuse_path.exists():
            self.historical_topic_reuse_data = json.loads(self.historical_topic_reuse_path.read_bytes())
        if self.analysis_path.exists():
            self.analysis_data = json.loads(self.analysis_path.read_bytes())
            self._index_analysis()

    def _index_analysis(self) -> None:
        projections = self.analysis_data.get("projections", {})
        rm = self.analysis_data.get("release_metrics", {})

        # Index community profiles from bridge_researchers
        for prof in rm.get("bridge_researchers", {}).get("community_topic_profiles_top_20_by_size", []):
            cid = prof.get("community_id")
            if cid:
                self.researcher_community_profiles[cid] = prof

        # Index organization topic profiles
        for prof in rm.get("organization_topic_profiles", []):
            oid = prof.get("organization_id")
            if oid:
                self.org_topic_profiles[oid].append(prof)

        # 1. Researcher collaboration metrics & Louvain communities
        res_proj = projections.get("researcher_collaboration", {})
        res_scores = res_proj.get("centrality_scores", {})
        res_deg = res_scores.get("degree_strength", {})
        res_bet = res_scores.get("betweenness", {})
        res_pr = res_scores.get("pagerank", {})

        res_comm_map: dict[str, tuple[str, int, int]] = {}
        res_comm_runs = res_proj.get("communities", [])
        if res_comm_runs:
            raw_groups = res_comm_runs[0].get("communities", [])
            # Rank communities by descending member count
            indexed_groups = [( f"community:{idx:05d}", members) for idx, members in enumerate(raw_groups)]
            sorted_by_size = sorted(indexed_groups, key=lambda item: (-len(item[1]), item[0]))
            rank_map = {cid: rank + 1 for rank, (cid, _) in enumerate(sorted_by_size)}
            for cid, members in indexed_groups:
                self.researcher_communities[cid] = members
                size = len(members)
                rk = rank_map[cid]
                for nid in members:
                    res_comm_map[nid] = (cid, size, rk)

        for nid in set(res_deg) | set(res_bet) | set(res_pr) | set(res_comm_map):
            cid, csize, crank = res_comm_map.get(nid, (None, None, None))
            self.node_metrics[nid] = {
                "projection": "researcher_collaboration",
                "degree_strength": res_deg.get(nid, 0.0),
                "betweenness": res_bet.get(nid, 0.0),
                "pagerank": res_pr.get(nid, 0.0),
                "community_id": cid,
                "community_size": csize,
                "community_rank": crank,
            }

        # 2. Organization collaboration metrics & Louvain communities
        org_proj = projections.get("organization_collaboration", {})
        org_scores = org_proj.get("centrality_scores", {})
        org_deg = org_scores.get("degree_strength", {})
        org_bet = org_scores.get("betweenness", {})
        org_pr = org_scores.get("pagerank", {})

        org_comm_map: dict[str, tuple[str, int, int]] = {}
        org_comm_runs = org_proj.get("communities", [])
        if org_comm_runs:
            raw_groups = org_comm_runs[0].get("communities", [])
            indexed_groups = [(f"org-community:{idx:05d}", members) for idx, members in enumerate(raw_groups)]
            sorted_by_size = sorted(indexed_groups, key=lambda item: (-len(item[1]), item[0]))
            rank_map = {cid: rank + 1 for rank, (cid, _) in enumerate(sorted_by_size)}
            for cid, members in indexed_groups:
                self.organization_communities[cid] = members
                size = len(members)
                rk = rank_map[cid]
                for nid in members:
                    org_comm_map[nid] = (cid, size, rk)

        for nid in set(org_deg) | set(org_bet) | set(org_pr) | set(org_comm_map):
            cid, csize, crank = org_comm_map.get(nid, (None, None, None))
            self.node_metrics[nid] = {
                "projection": "organization_collaboration",
                "degree_strength": org_deg.get(nid, 0.0),
                "betweenness": org_bet.get(nid, 0.0),
                "pagerank": org_pr.get(nid, 0.0),
                "community_id": cid,
                "community_size": csize,
                "community_rank": crank,
            }

        # 3. Core citations metrics for Papers
        cit_proj = projections.get("core_citations", {})
        cit_scores = cit_proj.get("centrality_scores", {})
        cit_deg = cit_scores.get("degree_strength", {})
        cit_bet = cit_scores.get("betweenness", {})
        cit_pr = cit_scores.get("pagerank", {})
        for nid in set(cit_deg) | set(cit_bet) | set(cit_pr):
            self.node_metrics[nid] = {
                "projection": "core_citations",
                "degree_strength": cit_deg.get(nid, 0.0),
                "betweenness": cit_bet.get(nid, 0.0),
                "pagerank": cit_pr.get(nid, 0.0),
            }

        # 4. Paper topics metrics for Topics
        top_proj = projections.get("paper_topics", {})
        top_scores = top_proj.get("centrality_scores", {})
        top_deg = top_scores.get("degree_strength", {})
        top_pr = top_scores.get("pagerank", {})
        for nid in set(top_deg) | set(top_pr):
            if nid.startswith("topic:"):
                self.node_metrics[nid] = {
                    "projection": "paper_topics",
                    "degree_strength": top_deg.get(nid, 0.0),
                    "betweenness": top_scores.get("betweenness", {}).get(nid, 0.0),
                    "pagerank": top_pr.get(nid, 0.0),
                }

    def start_background_ledger_warmup(self) -> None:
        """Warm up the evidence ledger in a background daemon thread."""
        if not self.graph_artifact_path.exists() or self._ledger_loaded:
            return
        thread = threading.Thread(target=self.ensure_ledger_loaded, daemon=True)
        thread.start()

    def ensure_ledger_loaded(self) -> bool:
        """Ensure evidence and affiliation observations from graph.json are indexed."""
        if self._ledger_loaded:
            return bool(self.evidence_by_id)
        with self._ledger_lock:
            if self._ledger_loaded:
                return bool(self.evidence_by_id)
            if not self.graph_artifact_path.exists():
                self._ledger_loaded = True
                return False
            try:
                raw = json.loads(self.graph_artifact_path.read_bytes())
                for ev in raw.get("evidence", []):
                    self.evidence_by_id[ev["id"]] = ev
                for obs in raw.get("affiliation_observations", []):
                    rid = obs["researcher_id"]
                    oid = obs["organization_id"]
                    pid = obs["paper_id"]
                    self.affiliations_by_researcher_org[(rid, oid)].append(obs)
                    self.affiliations_by_paper[pid].append(obs)
                    self.affiliations_by_researcher[rid].append(obs)
                    self.affiliations_by_org[oid].append(obs)
            except Exception:
                # Fall back cleanly to Neo4j if artifact file cannot be parsed
                pass
            finally:
                self._ledger_loaded = True
        return bool(self.evidence_by_id)

    def get_node_metrics(self, node_id: str) -> dict[str, Any] | None:
        return self.node_metrics.get(node_id)

    def get_top_node_ids(self, projection: str, metric: str = "degree_strength", limit: int = 100) -> list[str]:
        proj = self.analysis_data.get("projections", {}).get(projection, {})
        scores = proj.get("centrality_scores", {}).get(metric, {})
        if not scores:
            return []
        return [
            nid
            for nid, _ in sorted(scores.items(), key=lambda item: (-float(item[1]), item[0]))[:limit]
        ]

    def get_available_communities(self, mode: str, limit: int = 25) -> list[dict[str, Any]]:
        if mode == "researchers":
            items = []
            sorted_comms = sorted(
                self.researcher_communities.items(),
                key=lambda item: (-len(item[1]), item[0]),
            )[:limit]
            for rank, (cid, members) in enumerate(sorted_comms, 1):
                prof = self.researcher_community_profiles.get(cid, {})
                top_topics = prof.get("top_topics", [])
                top_topic_names = [t["topic"] for t in top_topics[:2]]
                label_suffix = f" ({', '.join(top_topic_names)})" if top_topic_names else ""
                items.append({
                    "community_id": cid,
                    "rank": rank,
                    "member_count": len(members),
                    "paper_count": prof.get("paper_count"),
                    "top_topics": top_topics,
                    "label": f"#{rank} · {cid} · {len(members)} researchers{label_suffix}",
                })
            return items
        if mode == "organizations":
            sorted_comms = sorted(
                self.organization_communities.items(),
                key=lambda item: (-len(item[1]), item[0]),
            )[:limit]
            return [
                {
                    "community_id": cid,
                    "rank": rank,
                    "member_count": len(members),
                    "label": f"#{rank} · {cid} · {len(members)} organizations",
                }
                for rank, (cid, members) in enumerate(sorted_comms, 1)
            ]
        return []
