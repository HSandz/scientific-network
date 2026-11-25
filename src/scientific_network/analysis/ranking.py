"""S2 ranking (specification 5.2): PageRank, personalized PageRank, comparison with other centralities, strict-evidence robustness.

Rules come from ``configs/analysis-final-exam-v1.yaml``. igraph does the computation; NetworkX is used only for cross-checks and the sampled-betweenness fallback.
"""

from __future__ import annotations

import time

import igraph as ig
import numpy as np
import pandas as pd


def pagerank(g: ig.Graph, *, weighted: bool, damping: float = 0.85) -> list[float]:
    return g.pagerank(damping=damping, directed=g.is_directed(), weights="weight" if weighted and "weight" in g.es.attributes() else None)


def personalized_pagerank(g: ig.Graph, seeds: list[int], *, damping: float = 0.85) -> list[float]:
    """PageRank whose restart distribution is uniform over ``seeds`` (vertex indices)."""
    if not seeds:
        raise ValueError("personalized PageRank needs at least one restart vertex")
    return g.personalized_pagerank(reset_vertices=seeds, damping=damping, directed=False)


def _estimate_betweenness_seconds(g: ig.Graph, weights, rng_seed: int, probe: int = 40) -> float:
    rng = np.random.default_rng(rng_seed)
    sources = rng.choice(g.vcount(), size=min(probe, g.vcount()), replace=False).tolist()
    t = time.time()
    g.distances(source=sources, weights=weights)
    return (time.time() - t) / len(sources) * g.vcount()


def betweenness(g: ig.Graph, *, weighted: bool, sources: int, seed: int, max_exact_seconds: float, log=print) -> tuple[list[float], dict]:
    weights = "distance" if weighted and "distance" in g.es.attributes() else None
    estimate = _estimate_betweenness_seconds(g, weights, seed)
    if estimate <= max_exact_seconds:
        t = time.time()
        values = g.betweenness(directed=g.is_directed(), weights=weights)
        return values, {"method": "exact (igraph, Brandes)", "sample_size": None, "estimated_seconds": estimate, "seconds": time.time() - t}
    import networkx as nx
    log(f"  betweenness: exact estimated {estimate:.0f}s > {max_exact_seconds:.0f}s, using source sampling k={sources}")
    G = nx.Graph()
    G.add_nodes_from(range(g.vcount()))
    for e in g.es:
        G.add_edge(e.source, e.target, **({"distance": e["distance"]} if weights else {}))
    t = time.time()
    scores = nx.betweenness_centrality(G, k=min(sources, g.vcount()), weight="distance" if weights else None, normalized=False, seed=seed)
    # networkx rescales the sampled sum by n/k; igraph's undirected exact value divides pair counts by two, so halve it to be comparable
    return [scores[i] / 2 for i in range(g.vcount())], {"method": "networkx source sampling", "sample_size": min(sources, g.vcount()), "estimated_exact_seconds": estimate, "seconds": time.time() - t}


def centralities(g: ig.Graph, cfg: dict, seed: int, *, weighted: bool, betweenness_mode: str, eigenvector: bool = True, log=print) -> tuple[pd.DataFrame, dict]:
    """All scores per vertex plus metadata. ``betweenness_mode``: "exact" (always exact), "auto" (exact when the probe estimate is within 30 minutes, else sampled) or "none"."""
    meta = {}
    data = {"id": g.vs["id"], "degree": g.degree(mode="all"), "pagerank": pagerank(g, weighted=weighted, damping=cfg["ranking"]["pagerank"]["damping"])}
    data["strength"] = g.strength(weights="weight", mode="all") if weighted else data["degree"]
    t = time.time()
    if eigenvector:
        try:
            data["eigenvector"] = g.eigenvector_centrality(directed=g.is_directed(), scale=True, weights="weight" if weighted else None)
        except Exception as error:  # a directed acyclic graph has no leading eigenvector
            data["eigenvector"] = [float("nan")] * g.vcount()
            meta["eigenvector_error"] = str(error)
    else:
        data["eigenvector"] = [float("nan")] * g.vcount()
        meta["eigenvector_skipped"] = True
    if betweenness_mode == "none":
        data["betweenness"] = [float("nan")] * g.vcount()
        meta["betweenness"] = {"method": "not computed"}
    else:
        limit = float("inf") if betweenness_mode == "exact" else 1800.0
        data["betweenness"], meta["betweenness"] = betweenness(g, weighted=weighted, sources=1000, seed=seed, max_exact_seconds=limit, log=log)
    meta["seconds"] = time.time() - t
    return pd.DataFrame(data), meta


def compare(df: pd.DataFrame, k: int = 20) -> dict:
    """Spearman correlation and top-k overlap of PageRank with each other measure."""
    out = {}
    for other in ("degree", "strength", "betweenness", "eigenvector"):
        if df[other].isna().all():
            out[other] = {"spearman": None, f"top{k}_overlap": None, "note": "not computed"}
            continue
        rho = df["pagerank"].rank().corr(df[other].rank())
        top_pr = set(df.nlargest(k, "pagerank", keep="all")["id"].head(k))
        top_other = set(df.nlargest(k, other, keep="all")["id"].head(k))
        out[other] = {"spearman": None if pd.isna(rho) else float(rho), f"top{k}_overlap": len(top_pr & top_other)}
    return out


def strict_subgraph(g: ig.Graph, minimum_support: int) -> ig.Graph:
    keep = [e.index for e in g.es if e["support"] >= minimum_support]
    return g.subgraph_edges(keep, delete_vertices=False)


STRICT_MINIMUM_SUPPORT = 2  # config ranking.robustness.strict_evidence_filter: support_count >= 2


def robustness(g: ig.Graph, k: int = 20, *, weighted: bool = True) -> dict:
    """PageRank on the full network and on the strict-evidence network (support_count >= 2, same vertex set): Spearman and top-k overlap."""
    strict = strict_subgraph(g, STRICT_MINIMUM_SUPPORT)
    full_pr, strict_pr = pagerank(g, weighted=weighted), pagerank(strict, weighted=weighted)
    df = pd.DataFrame({"id": g.vs["id"], "full": full_pr, "strict": strict_pr})
    top_full = set(df.nlargest(k, "full")["id"])
    top_strict = set(df.nlargest(k, "strict")["id"])
    return {"strict_edges": strict.ecount(), "full_edges": g.ecount(), "edges_kept_share": strict.ecount() / g.ecount(),
            "spearman_pagerank": float(df["full"].rank().corr(df["strict"].rank())), f"top{k}_overlap": len(top_full & top_strict),
            "dropped_from_top": sorted(top_full - top_strict), "entered_top": sorted(top_strict - top_full)}
