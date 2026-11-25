"""``research-network final-analysis <stage>``: S1-S3 and trend metrics of the final exam (specification 5), from the enriched graph file.

Stages: sanity, smallworld, ranking, communities, trends, all. Every stage needs explicit --config, --graph and --output paths. Nothing here touches
the frozen ``analyze`` outputs, ``configs/analysis-release-v1.yaml`` or ``reports/release-v*``.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import resource
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from . import communities as comm
from . import ranking, smallworld, trends
from .fx_data import YEARS, Inputs, cumulative_pairs, load_inputs, sanity_check

STAGES = ("sanity", "smallworld", "ranking", "communities", "trends", "report", "all")


def add_fx_parser(commands) -> None:
    p = commands.add_parser("final-analysis", help="final-exam network analysis S1-S3 and trend metrics (D042, specification 5)")
    p.add_argument("stage", choices=STAGES)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--graph", type=Path, required=True, help="enriched graph file (graph.json)")
    p.add_argument("--v4-analysis", type=Path, help="frozen v4 analysis.json for the sanity check (default: the path in the config)")
    p.add_argument("--reuse-baselines", type=Path, help="optional previous smallworld.json on the exact same graph+seed to reuse expensive baseline replicates while recomputing evolution and tails")
    p.add_argument("--output", type=Path, required=True)


def _json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=1, sort_keys=False, default=lambda o: None if o != o else float(o)) + "\n", encoding="utf-8")


def _csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or list(rows[0]) if rows else (fields or [])
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "wt", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if v is None else v) for k, v in r.items()})


class Context:
    def __init__(self, args):
        self.args = args
        self.cfg = yaml.safe_load(args.config.read_text())
        self.out: Path = args.output
        self.seed = self.cfg["random_seed"]
        self.inputs: Inputs = load_inputs(args.graph, expected_sha256=self.cfg["input"]["graph_sha256"], expected_version=self.cfg["input"]["graph_version"])
        self.v4_path = args.v4_analysis or Path(self.cfg["input"]["v4_analysis_for_sanity_check"])
        self._scores: dict[str, pd.DataFrame] = {}
        self._headline: dict[str, list[int]] = {}
        self.metadata: dict = {"stages": {}}

    def log(self, message: str) -> None:
        print(message, flush=True)

    def headline(self, name: str) -> list[int]:
        if name not in self._headline:
            h = self.cfg["communities"]["headline"]
            self._headline[name] = comm.leiden(self.inputs.networks[name], h["resolution"], h["seed"]).membership
        return self._headline[name]

    def scores(self, name: str) -> pd.DataFrame:
        if name not in self._scores:
            path = self.out / "ranking" / f"scores-{name}.csv.gz"
            if not path.exists():
                raise FileNotFoundError(f"{path} is missing: run the ranking stage first")
            self._scores[name] = pd.read_csv(path)
        return self._scores[name]


def _timed(ctx: Context, stage: str, fn):
    t = time.time()
    result = fn(ctx)
    ctx.metadata["stages"][stage] = {"seconds": round(time.time() - t, 1), "peak_rss_mb_so_far": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)}
    ctx.log(f"[{stage}] {ctx.metadata['stages'][stage]}")
    return result


# --- sanity -------------------------------------------------------------------------------------------------------------

def stage_sanity(ctx: Context) -> dict:
    result = sanity_check(ctx.inputs, json.loads(ctx.v4_path.read_text()))
    result.update({"graph_version": ctx.inputs.graph_version, "graph_sha256": ctx.inputs.graph_sha256, "v4_analysis": str(ctx.v4_path), "graph_counts": ctx.inputs.counts,
                   "note": "N1-N3 are rebuilt from the v4 layer inside the enriched graph file and compared with the frozen v4 networkx analysis"})
    _json(ctx.out / "sanity-v4.json", result)
    if not result["all_match"]:
        raise RuntimeError(f"v4 sanity check failed: {[r for r in result['rows'] if not r['match']]}")
    return result


# --- S1 ------------------------------------------------------------------------------------------------------------------

def stage_smallworld(ctx: Context) -> dict:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    cfg, inputs = ctx.cfg, ctx.inputs
    results, tails = {}, {}
    reuse_path = getattr(ctx.args, "reuse_baselines", None) if hasattr(ctx, "args") else None
    reused_networks = None
    if reuse_path is not None:
        prev = json.loads(Path(reuse_path).read_text(encoding="utf-8"))
        if prev.get("graph_version") != inputs.graph_version or prev.get("seed") != ctx.seed:
            raise ValueError(f"--reuse-baselines mismatch: expected {inputs.graph_version} seed={ctx.seed}, got {prev.get('graph_version')} seed={prev.get('seed')}")
        reused_networks = prev["networks"]
    for index, name in enumerate(cfg["small_world"]["networks"]):
        if reused_networks and name in reused_networks:
            results[name] = reused_networks[name]
        else:
            results[name] = smallworld.small_world(name, inputs.networks[name], cfg, ctx.seed + 100000 * index, log=ctx.log)
        degrees = [d for d in inputs.networks[name].degree() if d >= 1]
        tails[name] = smallworld.degree_tail(degrees, cfg["small_world"]["degree_tail"]["alpha_for_preference"])
        ctx.log(f"  {name} tail: xmin={tails[name]['xmin']} alpha={tails[name]['alpha']:.2f} claim={tails[name]['power_law_claim_allowed']} {tails[name]['comparisons']}")
    evolution = {}
    for name in cfg["small_world"]["evolution"]["networks"]:
        pairs = cumulative_pairs(inputs, name)
        evolution[name] = smallworld.evolution(pairs)
        evolution[name].append({"check": f"cumulative edges 2025 {len(pairs[2025])} vs network edges {inputs.networks[name].ecount()}", "match": len(pairs[2025]) == inputs.networks[name].ecount()})
    out = ctx.out / "smallworld"
    _json(out / "smallworld.json", {"config_version": cfg["version"], "graph_version": inputs.graph_version, "seed": ctx.seed, "networks": results})
    _json(out / "degree-tail.json", tails)
    _json(out / "evolution.json", evolution)
    _csv(out / "summary.csv", [{
        "network": n, "lcc_nodes": r["lcc_nodes"], "lcc_edges": r["lcc_edges"], "mean_degree": r["mean_degree"], "L": r["real"]["L"], "diameter": r["real"]["diameter"],
        "C_avg_local": r["real"]["clustering"]["average_local"], "transitivity": r["real"]["clustering"]["transitivity"],
        "L_rand_er": r["baselines"]["erdos_renyi_gnm"]["L_rand_mean"], "C_rand_er": r["baselines"]["erdos_renyi_gnm"]["C_rand_mean"], "sigma_er": r["baselines"]["erdos_renyi_gnm"]["sigma_from_means"],
        "L_rand_rewired": r["baselines"]["degree_preserving_rewiring"]["L_rand_mean"], "C_rand_rewired": r["baselines"]["degree_preserving_rewiring"]["C_rand_mean"],
        "sigma_rewired": r["baselines"]["degree_preserving_rewiring"]["sigma_from_means"], "small_world_holds": r["decision"]["small_world_holds"]} for n, r in results.items()])
    # figures
    fig, axes = plt.subplots(1, len(results), figsize=(4.2 * len(results), 3.2), sharey=True)
    for ax, (n, r) in zip(np.atleast_1d(axes), results.items()):
        h = r["real"]["histogram"]
        total = sum(h.values())
        ax.bar([int(k) for k in h], [v / total for v in h.values()], color="#3b6ea5")
        ax.set_title(f"{n}: L={r['real']['L']:.2f}, diameter {r['real']['diameter']}")
        ax.set_xlabel("shortest path length")
    np.atleast_1d(axes)[0].set_ylabel("share of node pairs")
    fig.tight_layout()
    fig.savefig(out / "path-length-histograms.svg")
    plt.close(fig)
    fig, axes = plt.subplots(1, len(tails), figsize=(4.2 * len(tails), 3.2))
    for ax, (n, t) in zip(np.atleast_1d(axes), tails.items()):
        counts = {int(k): v for k, v in t["degree_counts"].items()}
        ks = sorted(counts)
        tail = np.cumsum([counts[k] for k in reversed(ks)])[::-1] / t["n"]
        ax.loglog(ks, tail, ".", color="#3b6ea5", ms=3)
        ax.axvline(t["xmin"], color="#aa4444", lw=0.8, ls=":")
        ax.set_title(f"{n}: degree CCDF (xmin={t['xmin']:.0f})")
        ax.set_xlabel("degree k")
    np.atleast_1d(axes)[0].set_ylabel("P(degree >= k)")
    fig.tight_layout()
    fig.savefig(out / "degree-distributions.svg")
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.2))
    for n, rows in evolution.items():
        rows = [r for r in rows if "year" in r]
        axes[0].plot([r["year"] for r in rows], [r["L"] for r in rows], "o-", label=n)
        axes[1].plot([r["year"] for r in rows], [r["C"] for r in rows], "o-", label=n)
    axes[0].set_title("L of the largest component, cumulative")
    axes[1].set_title("average clustering C, cumulative")
    for ax in axes:
        ax.set_xticks(list(YEARS))
        ax.legend()
    fig.tight_layout()
    fig.savefig(out / "evolution.svg")
    plt.close(fig)
    return {"networks": {n: r["decision"]["statement"] for n, r in results.items()}}


# --- S2 ------------------------------------------------------------------------------------------------------------------

NETWORK_SETUP = {"N1": ("auto", True, True), "N2": ("exact", True, True), "N3": ("none", False, False), "N4": ("none", False, True)}  # (betweenness mode, weighted, eigenvector)


def _table(inputs: Inputs, df: pd.DataFrame, k: int, label: str | None = None, include_citations: bool = False) -> list[dict]:
    d = df if label is None else df[df["label"] == label]
    top = d.nlargest(k, "pagerank")
    rows = []
    for _i, r in top.iterrows():
        row = {"rank": int(r["pagerank_rank"]), "id": r["id"], "name": r["name"], "label": r["label"], "pagerank": float(r["pagerank"]),
               "degree": int(r["degree"]), "strength": float(r["strength"]),
               "community": (None if pd.isna(r.get("community")) else int(r["community"]))}
        if include_citations and "in_corpus_citations" in r:
            row["in_corpus_citations"] = int(r["in_corpus_citations"])
            row["out_corpus_citations"] = int(r["out_corpus_citations"])
        rows.append(row)
    return rows


def stage_ranking(ctx: Context) -> dict:
    cfg, inputs = ctx.cfg, ctx.inputs
    out = ctx.out / "ranking"
    k = cfg["ranking"]["top_k_tables"]
    summary = {}
    for name, (mode, weighted, eigen) in NETWORK_SETUP.items():
        g = inputs.networks[name]
        ctx.log(f"ranking {name}: {g.vcount()} nodes, {g.ecount()} edges, betweenness={mode}")
        df, meta = ranking.centralities(g, cfg, ctx.seed, weighted=weighted, betweenness_mode=mode, eigenvector=eigen, log=ctx.log)
        df["name"] = [inputs.nodes[i]["name"] for i in df["id"]]
        df["label"] = [inputs.nodes[i]["label"] for i in df["id"]]
        df["community"] = ctx.headline(name) if name in ("N1", "N2") else np.nan
        df["pagerank_rank"] = df["pagerank"].rank(ascending=False, method="min").astype(int)
        if name == "N3":
            df["in_corpus_citations"] = g.degree(mode="in")
            df["out_corpus_citations"] = g.degree(mode="out")
        ctx._scores[name] = df
        _csv(out / f"scores-{name}.csv.gz", df.to_dict("records"))
        entry = {"nodes": g.vcount(), "edges": g.ecount(), "directed": g.is_directed(), "weighted_pagerank": weighted, "meta": meta, "comparison_with_pagerank": ranking.compare(df, k)}
        if name in ("N1", "N2"):
            entry["robustness_strict_support_ge_2"] = ranking.robustness(g, k)
        if name == "N3":
            n_iso = sum(1 for d in g.degree(mode="all") if d == 0)
            lcc_sz = max(g.connected_components(mode="weak").sizes())
            entry["sparsity_note"] = (
                f"{g.ecount()} directed CITES edges across {g.vcount()} core papers "
                f"(largest weak component {lcc_sz}, {n_iso} isolated papers). "
                "Within-corpus citation PageRank is fragile on sparse directed links; read alongside in_corpus_citations."
            )
            entry["top"] = _table(inputs, df, k, include_citations=True)
        elif name == "N4":
            entry["top_by_label"] = {lab: _table(inputs, df, k, lab) for lab in ("Researcher", "Organization", "Paper", "Topic", "Method", "Task", "Dataset")}
        else:
            entry["top"] = _table(inputs, df, k)
        _json(out / f"ranking-{name}.json", entry)
        summary[name] = entry
    # personalized PageRank on N4
    g4 = inputs.networks["N4"]
    index = {v: i for i, v in enumerate(g4.vs["id"])}
    n4_df = ctx.scores("N4")
    global_n4_pr = dict(zip(n4_df["id"], n4_df["pagerank"]))
    sp = inputs.subject_papers
    chosen = {"Topic": sorted(sp["Topic"], key=lambda s: (-len(sp["Topic"][s]), s))}
    for kind in ("Method", "Task", "Dataset"):
        chosen[kind] = sorted(sp[kind], key=lambda s: (-len(sp[kind][s]), s))[:30]
    ppr = {}
    pcfg = cfg["ranking"]["personalized"]
    sizes = pcfg["top_k_per_kind"]
    min_sp = pcfg.get("min_subject_papers")
    fallback_n = int(pcfg.get("min_subject_papers_fallback_if_fewer_than", 5))
    for kind, subjects in chosen.items():
        for s in subjects:
            ppr.setdefault(kind, {})[s] = personalized_summary(
                inputs, g4, index, kind, s, sizes,
                global_pagerank=global_n4_pr, min_subject_papers=min_sp,
                fallback_if_fewer_than=fallback_n,
            )
    _json(out / "personalized-pagerank.json", {
        "damping": 0.85, "network": "N4",
        "primary_rank_by": pcfg.get("primary_rank_by", "raw_ppr"),
        "min_subject_papers": min_sp,
        "restart": "uniform over the subject's papers; seed papers are excluded from the Paper list",
        "subjects": ppr,
    })
    summary["personalized_subjects"] = {k_: len(v) for k_, v in ppr.items()}
    return {n: (v["comparison_with_pagerank"] if isinstance(v, dict) and "comparison_with_pagerank" in v else v) for n, v in summary.items()}


def personalized_summary(
    inputs: Inputs, g4, index: dict, kind: str, subject: str, sizes: dict, damping: float = 0.85,
    *, global_pagerank: dict[str, float] | None = None, min_subject_papers: dict[str, int] | None = None,
    fallback_if_fewer_than: int = 5,
) -> dict:
    """Personalized PageRank on N4 restarting uniformly over the papers of one topic/method/task/dataset; ranks Organizations/Researchers by lift when global_pagerank is supplied."""
    papers = sorted(inputs.subject_papers[kind][subject])
    scores = ranking.personalized_pagerank(g4, [index[p] for p in papers], damping=damping)
    seeds = set(papers)
    total_corpus = max(len(inputs.paper_year), 1)
    subject_share = len(seeds) / total_corpus

    by_label: dict[str, list[tuple[float, str]]] = defaultdict(list)
    for i, s in enumerate(scores):
        node = g4.vs[i]["id"]
        label = inputs.nodes[node]["label"]
        if label in sizes and node not in seeds and node != subject:
            by_label[label].append((float(s), node))

    top: dict[str, list[dict]] = {}
    top_by_raw_ppr: dict[str, list[dict]] = {}
    filter_notes: dict[str, str] = {}
    for label, v in by_label.items():
        raw_sorted = sorted(v, key=lambda x: (-x[0], x[1]))[:sizes[label]]
        raw_rows = [{"id": n, "name": inputs.nodes[n]["name"], "score": float(s)} for s, n in raw_sorted]
        if global_pagerank and label in ("Organization", "Researcher"):
            entity_papers_map = inputs.org_papers if label == "Organization" else inputs.researcher_papers
            min_req = int((min_subject_papers or {}).get(label, 1))
            enriched_rows = []
            for s, n in v:
                gpr = global_pagerank.get(n, 0.0)
                ep = entity_papers_map.get(n, set())
                sp_cnt = len(ep & seeds)
                tot_cnt = len(ep)
                lift = (s / gpr) if gpr > 0 else 0.0
                rca = ((sp_cnt / tot_cnt) / subject_share) if (tot_cnt > 0 and subject_share > 0) else 0.0
                enriched_rows.append({
                    "id": n,
                    "name": inputs.nodes[n]["name"],
                    "score": float(s),
                    "ppr_score": float(s),
                    "global_pagerank": float(gpr),
                    "lift": round(lift, 4),
                    "rca": round(rca, 4),
                    "subject_papers": sp_cnt,
                    "total_papers": tot_cnt,
                })
            qualified = [r for r in enriched_rows if r["subject_papers"] >= min_req]
            if len(qualified) < fallback_if_fewer_than and min_req > 1:
                qualified = [r for r in enriched_rows if r["subject_papers"] >= 1]
                filter_notes[label] = f"fallback to >=1 subject paper ({len(qualified)} qualified; fewer than {fallback_if_fewer_than} met min_subject_papers={min_req})"
            else:
                filter_notes[label] = f"min_subject_papers>={min_req} ({len(qualified)} qualified)"
            qualified.sort(key=lambda r: (-r["lift"], -r["subject_papers"], -r["ppr_score"], r["id"]))
            top[label] = qualified[:sizes[label]]
            # Also annotate raw PPR rows with lift/rca/subject_papers
            by_id = {r["id"]: r for r in enriched_rows}
            top_by_raw_ppr[label] = [by_id[r["id"]] for r in raw_rows if r["id"] in by_id]
        else:
            top[label] = raw_rows

    out = {"name": inputs.nodes[subject]["name"], "papers": len(papers), "top": top}
    if top_by_raw_ppr:
        out["top_by_raw_ppr"] = top_by_raw_ppr
        out["filter_notes"] = filter_notes
    return out


# --- S3 ------------------------------------------------------------------------------------------------------------------

def stage_communities(ctx: Context) -> dict:
    cfg, inputs = ctx.cfg, ctx.inputs
    out = ctx.out / "communities"
    summary = {}
    all_labels: dict[str, dict[int, dict[str, list[dict]]]] = {}
    for name in cfg["communities"]["networks"]:
        g = inputs.networks[name]
        ctx.log(f"communities {name}")
        runs = comm.run_partitions(name, g, cfg, log=ctx.log)
        members = runs.pop("_members")
        h = cfg["communities"]["headline"]
        level0 = members[(h["resolution"], h["seed"])]
        hier = comm.hierarchy(g, level0, cfg["communities"]["hierarchy_level1_resolution"], h["seed"])
        level1 = hier.pop("level1_membership")
        df = ctx.scores(name)
        ids = g.vs["id"]
        labels = comm.community_labels(inputs, ids, level0, name, cfg["communities"]["labels"]["top_n"])
        all_labels[name] = labels
        key = comm.key_individuals(g, level0, df["pagerank"].tolist(), df["betweenness"].tolist(), cfg)
        sizes = Counter(level0)
        first_member: dict[int, int] = {}
        for v, c in enumerate(level0):
            first_member.setdefault(c, v)
        rows = []
        for c, n in sorted(sizes.items(), key=lambda x: (-x[1], x[0])):
            if n < cfg["communities"]["key_individuals"]["minimum_community_size"]:
                continue
            rows.append({"community": c, "level1": level1[first_member[c]], "size": n,
                         **{f"label_{kind.lower()}": "; ".join(t["name"] for t in labels.get(c, {}).get(kind, [])) for kind in ("Topic", "Method", "Task", "Organization")},
                         "hubs": "; ".join(inputs.nodes[i]["name"] for i in key.get(c, {}).get("hubs", [])),
                         "brokers_participation": "; ".join(inputs.nodes[i]["name"] for i in key.get(c, {}).get("brokers_participation", [])),
                         "brokers_betweenness": "; ".join(inputs.nodes[i]["name"] for i in key.get(c, {}).get("brokers_betweenness", []))})
        _csv(out / f"communities-{name}.csv", rows)
        _csv(out / f"membership-{name}.csv.gz", [{"id": i, "level0": a, "level1": b} for i, a, b in zip(ids, level0, level1)])
        _json(out / f"communities-{name}.json", {"network": name, "headline": h, **runs, "hierarchy": hier, "labels": {str(c): v for c, v in labels.items() if sizes[c] >= cfg["communities"]["key_individuals"]["minimum_community_size"]},
                                                  "key_individuals": {str(c): v for c, v in key.items()}})
        summary[name] = {"headline_communities": len(sizes), "communities_ge_min_size": len(rows), "hierarchy": hier, "runs": [(r["resolution"], r["seed"], r["communities"], round(r["modularity"], 4)) for r in runs["runs"]],
                         "nmi": {k_: round(v["mean"], 4) for k_, v in runs["nmi_across_seeds"].items()}}
    rising = comm.rising_researchers(inputs, cfg)
    n1_df = ctx.scores("N1").set_index("id")
    for r in rising:
        r["community"] = int(n1_df.loc[r["id"], "community"]) if r["id"] in n1_df.index else None
    _csv(out / "rising-researchers.csv", rising)
    summary["rising_researchers"] = {"count": len(rising), "new_entrants": sum(r["new_entrant"] for r in rising)}
    # groups
    n1 = ctx.inputs.networks["N1"]
    n1_labels = all_labels.get("N1", {})
    lab_rows = comm.organization_anchored_communities(inputs, n1.vs["id"], ctx.headline("N1"), cfg, labels=n1_labels)
    org_rows = sorted(({"id": o, "name": inputs.nodes[o]["name"], "papers": len(p), "researchers": sum(1 for r in inputs.researcher_orgs.values() if o in r),
                        "sector": inputs.nodes[o]["properties"].get("sector"), "notable": o in inputs.notable_orgs} for o, p in inputs.org_papers.items()), key=lambda r: (-r["papers"], r["id"]))
    roll = comm.rollup(inputs, cfg)
    is_v2_groups = "organization_anchored_community" in cfg["groups"]
    if is_v2_groups:
        _csv(out / "groups-org-anchored-communities.csv", lab_rows)
    else:
        _csv(out / "groups-labs.csv", lab_rows)
    _csv(out / "groups-organizations.csv", org_rows)
    _csv(out / "groups-rollup.csv", roll["parents"])
    grp_summary = {
        "organizations": len(org_rows),
        "notable_organizations": sum(r["notable"] for r in org_rows),
        "organization_anchored_communities": len(lab_rows),
        "large_organization_anchored_communities": sum(1 for r in lab_rows if r.get("size_tier") == "large"),
        "rollup": {k_: v for k_, v in roll.items() if k_ != "parents"} | {"parents_with_children": len(roll["parents"])},
    }
    if not is_v2_groups:
        grp_summary["labs"] = len(lab_rows)
    _json(out / "groups-summary.json", grp_summary)
    summary["groups"] = {"organizations": len(org_rows), "notable": sum(r["notable"] for r in org_rows),
                         "organization_anchored_communities": len(lab_rows), "rollup_parents": len(roll["parents"]),
                         "ministry_part_of_skipped": roll["ministry_part_of_edges_skipped"], "ministry_by_class_label": roll["ministry_part_of_edges_by_class_label"]}
    return summary


# --- trends --------------------------------------------------------------------------------------------------------------

def _flat(row: dict) -> dict:
    flat = {k: v for k, v in row.items() if not isinstance(v, dict)}
    for y in YEARS:
        flat[f"papers_{y}"] = row["papers_by_year"][str(y)]
        flat[f"share_{y}"] = row["share_by_year"][str(y)]
    for y, v in row["yoy_change_of_share"].items():
        flat[f"yoy_{y}"] = v
    return flat


def stage_trends(ctx: Context) -> dict:
    cfg, inputs = ctx.cfg, ctx.inputs
    out = ctx.out / "trends"
    summary = {"classification_note": cfg["trends"].get("classes_description", trends.DESCRIPTIVE_CLASS_NOTE), "caveats": trends.CAVEATS, "classes": {}}
    for kind in ("Topic", "Method", "Task", "Dataset"):
        rows = trends.subject_trends(inputs, kind, cfg)
        _csv(out / f"trends-{kind.lower()}.csv", [_flat(r) for r in rows])
        summary["classes"][kind] = dict(Counter(r["class"] for r in rows)) | {"subjects": len(rows)}
        for label in ("rising", "emerging", "declining"):
            top = [r for r in rows if r["class"] == label]
            top.sort(key=lambda r: (-(r["recent_window_papers"]), r["id"]))
            summary.setdefault("examples", {}).setdefault(kind, {})[label] = [{"name": r["name"], "total": r["total_papers"], "base": r["base_window_papers"], "recent": r["recent_window_papers"],
                                                                                "slope": r["slope_of_share"], "p": r["slope_p_value"]} for r in top[:8]]
    gi = cfg["trends"]["group_interest"]
    groups: dict[str, set[str]] = {f"organization:{inputs.nodes[o]['name']} ({o})": set(p) for o, p in inputs.org_papers.items() if len(p) >= 30}
    n1 = inputs.networks["N1"]
    papers_of: dict[str, set[str]] = defaultdict(set)
    for paper, authors in inputs.paper_authors.items():
        for a in authors:
            papers_of[a].add(paper)
    members: dict[int, list[str]] = defaultdict(list)
    for i, c in zip(n1.vs["id"], ctx.headline("N1")):
        members[c].append(i)
    for c, ms in members.items():
        if len(ms) >= 50:
            groups[f"n1_community:{c}"] = set().union(*(papers_of.get(m, set()) for m in ms))
    all_rows = []
    for kind in ("Topic", "Method", "Task"):
        for r in trends.group_interest(inputs, kind, groups, cfg):
            r["kind"] = kind
            all_rows.append(r)
    _csv(out / "group-interest.csv", all_rows)
    summary["group_interest"] = {"groups": len(groups), "rows": len(all_rows), "organizations": sum(g.startswith("organization:") for g in groups), "n1_communities": sum(g.startswith("n1_") for g in groups),
                                 "kinds": ["Topic", "Method", "Task"], "note": "datasets are skipped for group interest (12% coverage leaves most cells at 0 or 1 paper)"}
    if cfg["trends"].get("display_aliases"):
        aliases = trends.build_display_aliases(inputs)
        _json(out / "display-aliases.json", aliases)
        summary["display_alias_groups"] = aliases["group_count"]
    _json(out / "trends-summary.json", summary)
    return summary


def stage_report(ctx: Context) -> dict:
    from . import fx_report
    fx_report.figures(ctx.out)
    text = fx_report.build_readme(ctx.out, ctx.cfg)
    (ctx.out / "README.md").write_text(text + "\n", encoding="utf-8")
    return {"readme_lines": text.count("\n") + 1}


def run_final_analysis(args) -> tuple[dict, int]:
    ctx = Context(args)
    ctx.out.mkdir(parents=True, exist_ok=True)
    stages = ("sanity", "smallworld", "ranking", "communities", "trends", "report") if args.stage == "all" else (args.stage,)
    fns = {"sanity": stage_sanity, "smallworld": stage_smallworld, "ranking": stage_ranking, "communities": stage_communities, "trends": stage_trends, "report": stage_report}
    result = {}
    for s in stages:
        result[s] = _timed(ctx, s, fns[s])
    ctx.metadata.update({"config": ctx.cfg["version"], "graph_version": ctx.inputs.graph_version, "graph_sha256": ctx.inputs.graph_sha256,
                         "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)})
    meta_path = ctx.out / "run-metadata.json"
    previous = json.loads(meta_path.read_text()) if meta_path.exists() else {"stages": {}}
    previous["stages"].update(ctx.metadata["stages"])
    previous.update({k: v for k, v in ctx.metadata.items() if k != "stages"})
    _json(meta_path, previous)
    return result, 0
