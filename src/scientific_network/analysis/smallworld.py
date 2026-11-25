"""S1 small world (specification 5.1): exact L, diameter, path-length histogram, clustering, random baselines, sigma, omega, evolution, degree tail.

All rules come from ``configs/analysis-final-exam-v1.yaml``. The real graph's L is always exact; baseline L is exact up to a stated node count
and otherwise comes from a seeded pivot sample with a standard error.
"""

from __future__ import annotations

import math
import random
import statistics
import warnings

import igraph as ig
import numpy as np


def largest_component(g: ig.Graph) -> ig.Graph:
    sizes = g.connected_components().sizes()
    if len(sizes) == 1:
        return g
    return g.connected_components().giant()


def exact_paths(g: ig.Graph) -> dict:
    """Exact mean shortest path length, diameter and the unordered-pair path-length histogram (BFS from every node)."""
    hist = g.path_length_hist(directed=False)
    bins = {int(left): int(count) for left, _right, count in hist.bins()}
    pairs = sum(bins.values())
    mean = sum(d * c for d, c in bins.items()) / pairs
    return {"method": "exact", "L": mean, "diameter": max(bins), "histogram": dict(sorted(bins.items())), "pairs": pairs, "unconnected_pairs": int(hist.unconnected)}


def pivot_paths(g: ig.Graph, pivots: int, rng: random.Random, chunk: int = 250) -> dict:
    """Mean path length from ``pivots`` seeded source nodes to all other nodes; standard error over the pivots (per-source means)."""
    n = g.vcount()
    sources = rng.sample(range(n), min(pivots, n))
    per_source = []
    for start in range(0, len(sources), chunk):
        d = np.asarray(g.distances(source=sources[start:start + chunk]), dtype=float)
        d[d == 0] = np.nan
        d[np.isinf(d)] = np.nan
        per_source.extend(np.nanmean(d, axis=1).tolist())
    mean = float(np.mean(per_source))
    return {"method": "pivot_sample", "L": mean, "pivots": len(sources), "standard_error": float(np.std(per_source, ddof=1) / math.sqrt(len(per_source)))}


def clustering(g: ig.Graph) -> dict:
    return {"average_local": float(g.transitivity_avglocal_undirected(mode="zero")), "transitivity": float(g.transitivity_undirected())}


def replicate(g: ig.Graph, kind: str, seed: int, swaps_per_edge: int) -> ig.Graph:
    random.seed(seed)
    if kind == "erdos_renyi_gnm":
        r = ig.Graph.Erdos_Renyi(n=g.vcount(), m=g.ecount())
    elif kind == "degree_preserving_rewiring":
        r = g.copy()
        r.rewire(n=swaps_per_edge * g.ecount())
    else:
        raise ValueError(kind)
    return largest_component(r)


def lattice_omega(n: int, mean_degree: float, L: float, C: float, L_rand: float) -> dict:
    """Approximate omega (Telesford et al.) with analytic ring-lattice values; only a secondary figure."""
    k = mean_degree
    c_latt = 3 * (k - 2) / (4 * (k - 1)) if k > 2 else float("nan")
    l_latt = n / (2 * k)
    return {"C_lattice_analytic": c_latt, "L_lattice_analytic": l_latt, "omega": (L_rand / L - C / c_latt) if k > 2 else None,
            "note": "approximate: analytic ring-lattice formulas, k = mean degree of the component; omega near 0 means small world, negative lattice-like, positive random-like"}


def small_world(name: str, g_full: ig.Graph, cfg: dict, seed: int, log=print) -> dict:
    sw = cfg["small_world"]
    g = largest_component(g_full)
    n, m = g.vcount(), g.ecount()
    real_paths = exact_paths(g)
    real_clust = clustering(g)
    log(f"{name}: LCC {n} nodes {m} edges, L={real_paths['L']:.4f} diameter={real_paths['diameter']} C={real_clust['average_local']:.4f}")
    exact_baseline = n <= sw["baseline_l"]["exact_when_nodes_at_most"]
    pivots = sw["baseline_l"]["pivots"]
    out_baselines = {}
    for kind_index, kind in enumerate(("erdos_renyi_gnm", "degree_preserving_rewiring")):
        reps = []
        for i in range(sw["baselines"][kind]):
            s = seed + 1000 * kind_index + i
            r = replicate(g, kind, s, sw["baselines"]["rewiring_swaps_per_edge"])
            paths = exact_paths(r) if exact_baseline else pivot_paths(r, pivots, random.Random(s))
            c = clustering(r)
            sigma = (real_clust["average_local"] / c["average_local"]) / (real_paths["L"] / paths["L"]) if c["average_local"] > 0 else None
            reps.append({"seed": s, "nodes": r.vcount(), "edges": r.ecount(), "L": paths["L"], "C": c["average_local"], "transitivity": c["transitivity"], "sigma": sigma,
                         **({"standard_error": paths["standard_error"]} if "standard_error" in paths else {})})
        Ls, Cs = [r["L"] for r in reps], [r["C"] for r in reps]
        sigmas = [r["sigma"] for r in reps]
        mean_l, mean_c = statistics.mean(Ls), statistics.mean(Cs)
        out_baselines[kind] = {
            "replicates": reps, "L_rand_mean": mean_l, "L_rand_sd": statistics.stdev(Ls), "C_rand_mean": mean_c, "C_rand_sd": statistics.stdev(Cs),
            "sigma_from_means": (real_clust["average_local"] / mean_c) / (real_paths["L"] / mean_l) if mean_c > 0 else None,
            "sigma_replicate_mean": statistics.mean(s for s in sigmas if s is not None) if all(s is not None for s in sigmas) else None,
            "sigma_replicate_min": min(s for s in sigmas if s is not None) if any(s is not None for s in sigmas) else None,
            "sigma_replicate_sd": statistics.stdev(s for s in sigmas if s is not None) if sum(s is not None for s in sigmas) > 1 else None,
            "L_over_L_rand": real_paths["L"] / mean_l, "C_over_C_rand": (real_clust["average_local"] / mean_c) if mean_c > 0 else None,
            "baseline_L_method": "exact" if exact_baseline else f"seeded pivot sample ({pivots} sources per replicate)",
            **({"L_rand_pivot_standard_error_mean": statistics.mean(r["standard_error"] for r in reps)} if not exact_baseline else {})}
        b = out_baselines[kind]
        fmt = lambda x, spec: "n/a" if x is None else format(x, spec)
        log(f"  {kind}: L_rand={mean_l:.4f} C_rand={mean_c:.5f} sigma(means)={fmt(b['sigma_from_means'], '.2f')} min replicate sigma={fmt(b['sigma_replicate_min'], '.2f')}")
    rule = sw["decision_rule"]
    sigma_all = all(s is not None and s > rule["sigma_greater_than"] for b in out_baselines.values() for s in [r["sigma"] for r in b["replicates"]])
    ratio_ok = all(b["L_over_L_rand"] <= rule["max_l_over_l_rand"] for b in out_baselines.values())
    mean_degree = 2 * m / n
    return {"network": name, "lcc_nodes": n, "lcc_edges": m, "full_nodes": g_full.vcount(), "full_edges": g_full.ecount(), "lcc_share_of_nodes": n / g_full.vcount(),
            "mean_degree": mean_degree, "real": {**real_paths, "clustering": real_clust}, "baselines": out_baselines,
            "omega": lattice_omega(n, mean_degree, real_paths["L"], real_clust["average_local"], statistics.mean(b["L_rand_mean"] for b in out_baselines.values())),
            "decision": {"rule": rule, "sigma_above_1_for_all_replicates": sigma_all, "L_over_L_rand_within_bound": ratio_ok, "small_world_holds": bool(sigma_all and ratio_ok),
                         "statement": f"small world {'holds' if sigma_all and ratio_ok else 'does not hold'} for {name} under the declared rule"}}


def evolution(pairs_by_year: dict[int, set[tuple[str, str]]]) -> list[dict]:
    rows = []
    for year, pairs in sorted(pairs_by_year.items()):
        ids = sorted({x for p in pairs for x in p})
        index = {v: i for i, v in enumerate(ids)}
        g = ig.Graph(n=len(ids), edges=[(index[a], index[b]) for a, b in pairs])
        lcc = largest_component(g)
        paths = exact_paths(lcc)
        rows.append({"year": year, "nodes_with_edges": g.vcount(), "edges": g.ecount(), "lcc_nodes": lcc.vcount(), "L": paths["L"], "diameter": paths["diameter"],
                     "C": clustering(g)["average_local"], "C_lcc": clustering(lcc)["average_local"]})
    return rows


def degree_tail(degrees: list[int], alpha: float = 0.05) -> dict:
    """Heavy-tail fit with likelihood-ratio comparisons (power law against lognormal, exponential and truncated power law)."""
    import powerlaw
    data = [d for d in degrees if d >= 1]
    warnings.filterwarnings("ignore")
    fit = powerlaw.Fit(data, discrete=True, verbose=False)
    comparisons = {}
    for alt in ("lognormal", "exponential", "truncated_power_law"):
        r, p = fit.distribution_compare("power_law", alt, normalized_ratio=True)
        verdict = "power law favoured" if r > 0 and p < alpha else ("alternative favoured" if r < 0 and p < alpha else "indistinguishable")
        comparisons[alt] = {"R": float(r), "p": float(p), "verdict": verdict}
    favoured_over_exp = comparisons["exponential"]["verdict"] == "power law favoured"
    not_rejected_vs_lognormal = comparisons["lognormal"]["verdict"] != "alternative favoured"
    claim = bool(favoured_over_exp and not_rejected_vs_lognormal)
    counts: dict[int, int] = {}
    for d in data:
        counts[d] = counts.get(d, 0) + 1
    return {"n": len(data), "xmin": float(fit.power_law.xmin), "alpha": float(fit.power_law.alpha), "ks_distance": float(fit.power_law.D), "tail_nodes": int(sum(1 for d in data if d >= fit.power_law.xmin)),
            "comparisons": comparisons, "power_law_claim_allowed": claim,
            "statement": ("a power-law tail is supported by the declared rule (favoured over exponential and not rejected against lognormal; no goodness-of-fit bootstrap was run)" if claim
                          else "no power-law claim: the declared rule is not met (see the comparisons); the distribution is described as heavy-tailed only where the comparisons show it"),
            "degree_counts": dict(sorted(counts.items()))}
