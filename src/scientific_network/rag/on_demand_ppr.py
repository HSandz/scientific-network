"""On-demand topic/entity-personalized PageRank and lift over N4 (analysis-final-exam-v2 definition)."""

from __future__ import annotations

from collections import defaultdict
import csv
import gc
import gzip
import json
from pathlib import Path
from typing import Any

import igraph as ig

DAMPING = 0.85
MIN_SUBJECT_PAPERS: dict[str, int] = {"Organization": 3, "Researcher": 2}
FALLBACK_IF_FEWER_THAN = 5
TOP_K_PER_KIND: dict[str, int] = {
    "Researcher": 20,
    "Organization": 20,
    "Paper": 20,
    "Method": 10,
    "Task": 10,
    "Dataset": 10,
}
SUBJECT_RELATIONS: dict[str, str] = {
    "Topic": "HAS_TOPIC",
    "Method": "USES_METHOD",
    "Task": "ADDRESSES_TASK",
    "Dataset": "USES_DATASET",
}


class OnDemandPPRCompute:
    """Compute and cache personalized PageRank + lift on N4 using the exact analysis-final-exam-v2 rules."""

    def __init__(
        self,
        *,
        graph_path: Path | None = Path("data/processed/enriched-graph-v3/graph.json"),
        analysis_dir: Path = Path("reports/final-exam/analysis-v2"),
        backend: Any | None = None,
    ) -> None:
        self.graph_path = graph_path
        self.analysis_dir = analysis_dir
        self.backend = backend
        self._ready = False
        self._unavailable = False
        self._g4: ig.Graph | None = None
        self._ids4: list[str] = []
        self._idx4: dict[str, int] = {}
        self._nodes: dict[str, tuple[str, str]] = {}
        self._subject_papers: dict[str, set[str]] = {}
        self._org_papers: dict[str, set[str]] = {}
        self._researcher_papers: dict[str, set[str]] = {}
        self._global_pagerank: dict[str, float] = {}
        self._total_papers: int = 0
        self._cache: dict[str, dict[str, Any]] = {}

    def is_cached(self, subject_id: str) -> bool:
        return subject_id in self._cache

    def _load_global_pagerank(self, g4: ig.Graph, ids4: list[str]) -> dict[str, float]:
        scores_csv = self.analysis_dir / "ranking" / "scores-N4.csv.gz"
        if scores_csv.is_file() and g4.vcount() >= 40000:
            with gzip.open(scores_csv, "rt", encoding="utf-8") as fh:
                return {r["id"]: float(r["pagerank"]) for r in csv.DictReader(fh)}
        vals = g4.pagerank(damping=DAMPING, directed=False)
        return dict(zip(ids4, (float(v) for v in vals)))

    def _build_from_in_memory(self) -> bool:
        nodes_dict = getattr(self.backend, "nodes", None)
        edges_list = getattr(self.backend, "edges", None)
        if not isinstance(nodes_dict, dict) or not isinstance(edges_list, list) or not nodes_dict:
            return False

        nodes: dict[str, tuple[str, str]] = {
            nid: (str(n["label"]), str(n["name"]))
            for nid, n in nodes_dict.items()
        }
        ids4 = sorted(nodes)
        idx4 = {nid: i for i, nid in enumerate(ids4)}
        edge_pairs = [
            (idx4[e["source_id"]], idx4[e["target_id"]])
            for e in edges_list
            if e.get("validation_status", "accepted") == "accepted"
            and e["source_id"] in idx4
            and e["target_id"] in idx4
        ]
        g4 = ig.Graph(n=len(ids4), edges=edge_pairs, directed=False)
        g4.vs["id"] = ids4
        g4.simplify(multiple=True, loops=True)

        subj_papers: dict[str, set[str]] = defaultdict(set)
        res_papers: dict[str, set[str]] = defaultdict(set)
        res_orgs: dict[str, set[str]] = defaultdict(set)
        rel_to_kind = set(SUBJECT_RELATIONS.values())
        for e in edges_list:
            if e.get("validation_status", "accepted") != "accepted":
                continue
            rel = e["relation"]
            if rel in rel_to_kind:
                subj_papers[e["target_id"]].add(e["source_id"])
            elif rel == "AUTHORED":
                res_papers[e["source_id"]].add(e["target_id"])
            elif rel == "AFFILIATED_WITH":
                res_orgs[e["source_id"]].add(e["target_id"])

        org_papers: dict[str, set[str]] = defaultdict(set)
        for rid, oids in res_orgs.items():
            pids = res_papers.get(rid, set())
            for oid in oids:
                org_papers[oid].update(pids)

        self._finish_init(nodes, ids4, idx4, g4, subj_papers, org_papers, res_papers)
        return True

    def _build_from_graph_file(self) -> bool:
        if self.graph_path is None or not self.graph_path.is_file():
            return False
        raw = self.graph_path.read_bytes()
        graph = json.loads(raw)
        del raw

        nodes: dict[str, tuple[str, str]] = {
            str(n["id"]): (str(n["label"]), str(n["name"]))
            for n in graph.get("nodes", [])
        }
        ids4 = sorted(nodes)
        idx4 = {nid: i for i, nid in enumerate(ids4)}
        raw_edges = graph.get("edges", [])
        edge_pairs = [
            (idx4[e["source_id"]], idx4[e["target_id"]])
            for e in raw_edges
            if e["source_id"] in idx4 and e["target_id"] in idx4
        ]
        g4 = ig.Graph(n=len(ids4), edges=edge_pairs, directed=False)
        g4.vs["id"] = ids4
        g4.simplify(multiple=True, loops=True)
        del edge_pairs

        subj_papers: dict[str, set[str]] = defaultdict(set)
        res_papers: dict[str, set[str]] = defaultdict(set)
        rel_set = set(SUBJECT_RELATIONS.values())
        for e in raw_edges:
            rel = e["relation"]
            if rel in rel_set:
                subj_papers[e["target_id"]].add(e["source_id"])
            elif rel == "AUTHORED":
                res_papers[e["source_id"]].add(e["target_id"])

        org_papers: dict[str, set[str]] = defaultdict(set)
        for a in graph.get("affiliation_observations", []):
            org_papers[a["organization_id"]].add(a["paper_id"])

        del graph, raw_edges
        gc.collect()
        self._finish_init(nodes, ids4, idx4, g4, subj_papers, org_papers, res_papers)
        return True

    def _build_from_neo4j(self) -> bool:
        if self.backend is None or not hasattr(self.backend, "run_read"):
            return False
        node_rows = self.backend.run_read(
            "MATCH (n) WHERE NOT any(l IN labels(n) WHERE l STARTS WITH 'Rag') "
            "RETURN n.id AS id, labels(n)[0] AS label, n.name AS name"
        )
        if not node_rows:
            return False
        nodes: dict[str, tuple[str, str]] = {
            str(r["id"]): (str(r["label"]), str(r["name"] or r["id"]))
            for r in node_rows
            if r.get("id") and r.get("label")
        }
        ids4 = sorted(nodes)
        idx4 = {nid: i for i, nid in enumerate(ids4)}

        edge_rows = self.backend.run_read(
            "MATCH (a)-[r]->(b) "
            "WHERE NOT any(l IN labels(a) WHERE l STARTS WITH 'Rag') "
            "  AND NOT any(l IN labels(b) WHERE l STARTS WITH 'Rag') "
            "RETURN a.id AS src, type(r) AS rel, b.id AS dst"
        )
        edge_pairs: list[tuple[int, int]] = []
        subj_papers: dict[str, set[str]] = defaultdict(set)
        res_papers: dict[str, set[str]] = defaultdict(set)
        res_orgs: dict[str, set[str]] = defaultdict(set)
        rel_set = set(SUBJECT_RELATIONS.values())
        for r in edge_rows:
            src, rel, dst = r.get("src"), r.get("rel"), r.get("dst")
            if src in idx4 and dst in idx4:
                edge_pairs.append((idx4[src], idx4[dst]))
            if rel in rel_set:
                subj_papers[dst].add(src)
            elif rel == "AUTHORED":
                res_papers[src].add(dst)
            elif rel == "AFFILIATED_WITH":
                res_orgs[src].add(dst)

        g4 = ig.Graph(n=len(ids4), edges=edge_pairs, directed=False)
        g4.vs["id"] = ids4
        g4.simplify(multiple=True, loops=True)

        org_papers: dict[str, set[str]] = defaultdict(set)
        for rid, oids in res_orgs.items():
            pids = res_papers.get(rid, set())
            for oid in oids:
                org_papers[oid].update(pids)

        self._finish_init(nodes, ids4, idx4, g4, subj_papers, org_papers, res_papers)
        return True

    def _finish_init(
        self,
        nodes: dict[str, tuple[str, str]],
        ids4: list[str],
        idx4: dict[str, int],
        g4: ig.Graph,
        subj_papers: dict[str, set[str]],
        org_papers: dict[str, set[str]],
        res_papers: dict[str, set[str]],
    ) -> None:
        self._nodes = nodes
        self._ids4 = ids4
        self._idx4 = idx4
        self._g4 = g4
        self._subject_papers = dict(subj_papers)
        self._org_papers = dict(org_papers)
        self._researcher_papers = dict(res_papers)
        self._total_papers = sum(1 for lbl, _ in nodes.values() if lbl == "Paper")
        self._global_pagerank = self._load_global_pagerank(g4, ids4)
        self._ready = True

    def _ensure_index(self) -> bool:
        if self._ready:
            return True
        if self._unavailable:
            return False
        try:
            if self._build_from_in_memory():
                return True
            if self._build_from_graph_file():
                return True
            if self._build_from_neo4j():
                return True
        except Exception:
            self._unavailable = True
            return False
        self._unavailable = True
        return False

    def compute(self, subject_id: str, *, kind: str | None = None) -> dict[str, Any] | None:
        """Compute (or return cached) N4 personalized PageRank and lift summary for ``subject_id``."""
        if subject_id in self._cache:
            return self._cache[subject_id]
        if not self._ensure_index() or self._g4 is None:
            return None
        node_info = self._nodes.get(subject_id)
        if node_info is None:
            return None
        subj_label, subj_name = node_info
        subj_kind = kind or subj_label
        papers = sorted(p for p in self._subject_papers.get(subject_id, set()) if p in self._idx4)
        if not papers:
            return None

        scores = self._g4.personalized_pagerank(
            reset_vertices=[self._idx4[p] for p in papers],
            damping=DAMPING,
            directed=False,
        )
        seeds = set(papers)
        subject_share = len(seeds) / max(self._total_papers, 1)

        by_label: dict[str, list[tuple[float, str]]] = defaultdict(list)
        for i, s in enumerate(scores):
            nid = self._ids4[i]
            lbl, _ = self._nodes[nid]
            if lbl in TOP_K_PER_KIND and nid not in seeds and nid != subject_id:
                by_label[lbl].append((float(s), nid))

        top: dict[str, list[dict[str, Any]]] = {}
        top_by_raw_ppr: dict[str, list[dict[str, Any]]] = {}
        filter_notes: dict[str, str] = {}

        for lbl, vec in by_label.items():
            raw_sorted = sorted(vec, key=lambda x: (-x[0], x[1]))[: TOP_K_PER_KIND[lbl]]
            raw_rows = [{"id": nid, "name": self._nodes[nid][1], "score": float(s)} for s, nid in raw_sorted]
            if lbl in ("Organization", "Researcher"):
                ep_map = self._org_papers if lbl == "Organization" else self._researcher_papers
                min_req = MIN_SUBJECT_PAPERS[lbl]
                enriched: list[dict[str, Any]] = []
                for s, nid in vec:
                    gpr = self._global_pagerank.get(nid, 0.0)
                    ep = ep_map.get(nid, set())
                    sp_cnt = len(ep & seeds)
                    tot_cnt = len(ep)
                    lift = (s / gpr) if gpr > 0 else 0.0
                    rca = ((sp_cnt / tot_cnt) / subject_share) if (tot_cnt > 0 and subject_share > 0) else 0.0
                    enriched.append({
                        "id": nid,
                        "name": self._nodes[nid][1],
                        "score": float(s),
                        "ppr_score": float(s),
                        "global_pagerank": float(gpr),
                        "lift": round(lift, 4),
                        "rca": round(rca, 4),
                        "subject_papers": sp_cnt,
                        "total_papers": tot_cnt,
                    })
                qualified = [r for r in enriched if r["subject_papers"] >= min_req]
                if len(qualified) < FALLBACK_IF_FEWER_THAN and min_req > 1:
                    qualified = [r for r in enriched if r["subject_papers"] >= 1]
                    filter_notes[lbl] = (
                        f"fallback to >=1 subject paper ({len(qualified)} qualified; "
                        f"fewer than {FALLBACK_IF_FEWER_THAN} met min_subject_papers={min_req})"
                    )
                else:
                    filter_notes[lbl] = f"min_subject_papers>={min_req} ({len(qualified)} qualified)"
                qualified.sort(key=lambda r: (-r["lift"], -r["subject_papers"], -r["ppr_score"], r["id"]))
                top[lbl] = qualified[: TOP_K_PER_KIND[lbl]]
                by_id = {r["id"]: r for r in enriched}
                top_by_raw_ppr[lbl] = [by_id[r["id"]] for r in raw_rows if r["id"] in by_id]
            else:
                top[lbl] = raw_rows

        result = {
            "id": subject_id,
            "name": subj_name,
            "kind": subj_kind,
            "papers": len(papers),
            "top": top,
            "top_by_raw_ppr": top_by_raw_ppr,
            "filter_notes": filter_notes,
            "computed_on_demand": True,
            "method_note": (
                "Computed on demand on N4 (damping=0.85, uniform restart over subject papers, "
                "same definition as analysis-final-exam-v2)."
            ),
        }
        self._cache[subject_id] = result
        return result
