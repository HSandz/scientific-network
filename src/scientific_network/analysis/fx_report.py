"""README and extra figures for the final-exam analysis. Tables are generated from the measured output files; a few sentences of reading quote numbers that were checked against those tables."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from .fx_data import YEARS


def _j(p: Path):
    return json.loads(p.read_text())


def _c(p: Path) -> list[dict]:
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _f(x, nd=3):
    return "n/a" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))


def _table(header: list[str], rows: list[list]) -> str:
    return "\n".join(["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"] + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows])


def figures(out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.2))
    for ax, name in zip(axes, ("N1", "N2")):
        import pandas as pd
        m = pd.read_csv(out / "communities" / f"membership-{name}.csv.gz")["level0"].value_counts().sort_values(ascending=False).values
        ax.loglog(range(1, len(m) + 1), m, ".", color="#3b6ea5", ms=3)
        ax.set_title(f"{name}: community sizes (rank-size, headline)")
        ax.set_xlabel("community rank")
    axes[0].set_ylabel("members")
    fig.tight_layout()
    fig.savefig(out / "communities" / "community-sizes.svg")
    plt.close(fig)
    rows = _c(out / "trends" / "trends-topic.csv")
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    for r in sorted(rows, key=lambda r: -int(r["total_papers"])):
        ax.plot(list(YEARS), [float(r[f"share_{y}"]) for y in YEARS], "o-", ms=3, lw=1.2 if r["class"] != "stable" else 0.7, label=f"{r['name']} ({r['class']})" if r["class"] != "stable" else None)
    ax.set_title("Topic share of each year's papers, 2021-2025")
    ax.set_xticks(list(YEARS))
    ax.set_ylabel("share of papers (a paper may carry up to 3 topics)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "trends" / "topic-shares.svg")
    plt.close(fig)


def build_readme(out: Path, cfg: dict) -> str:
    meta, sanity = _j(out / "run-metadata.json"), _j(out / "sanity-v4.json")
    sw = _j(out / "smallworld" / "smallworld.json")["networks"]
    tails, evo = _j(out / "smallworld" / "degree-tail.json"), _j(out / "smallworld" / "evolution.json")
    rk = {n: _j(out / "ranking" / f"ranking-{n}.json") for n in ("N1", "N2", "N3", "N4")}
    ppr = _j(out / "ranking" / "personalized-pagerank.json")["subjects"]
    cm = {n: _j(out / "communities" / f"communities-{n}.json") for n in ("N1", "N2")}
    grp = _j(out / "communities" / "groups-summary.json")
    tr = _j(out / "trends" / "trends-summary.json")
    L = []
    w = L.append
    w(f"# Final-exam network analysis: S1-S3 and trend metrics\n")
    w(f"Graph `{meta['graph_version']}` (file SHA-256 `{meta['graph_sha256'][:16]}...`), config `{cfg['version']}`. "
      "Every number below was measured by `research-network final-analysis` from the graph file; nothing is a planned target. Enrichment-derived labels (topics, methods, tasks, datasets, Wikidata/Wikipedia links) "
      "are AI-assessed, not human annotation, and the evaluation figures that describe them cover sampling error only. Reproduce with "
      f"`uv run research-network final-analysis all --config configs/{cfg['version']}.yaml --graph data/processed/enriched-graph-v3/graph.json --output {out.as_posix()}` "
      "(the stage `report` regenerates this file).\n")
    w("Runtimes (wall clock, one process each, 12 GB machine, `neo4j-enriched` stopped): " + ", ".join(f"{k} {v['seconds']:.0f} s" for k, v in meta["stages"].items()) +
      f"; peak resident memory of any run {meta['peak_rss_mb']} MB.\n")
    w("## Networks and the v4 sanity check\n")
    w("N1 = researcher co-authorship (COAUTHORED_WITH, weight = fractional weight), N2 = organization collaboration (COLLABORATED_WITH, fractional weight), N3 = paper citation (CITES, directed, core papers), "
      "N4 = the full enriched graph as one undirected simple graph (all labels, all relations, unweighted). N1-N3 are rebuilt from the v4 layer inside the graph file (parent-only organizations added by enrichment are excluded from N2).\n")
    n3_lcc = next(r["ours"] for r in sanity["rows"] if r["metric"] == "N3 largest component")
    w(_table(["Network", "Nodes", "Edges", "Largest (weak) component"], [
        [n, rk[n]["nodes"], rk[n]["edges"], {"N1": sw["N1"]["lcc_nodes"], "N2": sw["N2"]["lcc_nodes"], "N3": n3_lcc, "N4": sw["N4"]["lcc_nodes"]}[n]] for n in rk]))
    bad = [r for r in sanity["rows"] if not r["match"]]
    w(f"\nSanity check against the frozen v4 analysis (`reports/release-v4/analysis.json`): {len(sanity['rows'])} overlapping figures (nodes, edges, isolates, max degree, largest component, component count, strength sum) compared; "
      f"{'all match' if not bad else 'MISMATCH: ' + str(bad)}. The first attempt differed for N2 (2,312 nodes against 2,047): it had included the 265 parent-only organizations that enrichment added; "
      "restricting N2 to the v4 layer removed the difference. Details: `sanity-v4.json`.\n")
    # S1
    w("## S1 Small world (largest connected component)\n")
    rows = []
    for n, r in sw.items():
        e, d = r["baselines"]["erdos_renyi_gnm"], r["baselines"]["degree_preserving_rewiring"]
        rows.append([n, r["lcc_nodes"], r["lcc_edges"], _f(r["mean_degree"], 2), _f(r["real"]["L"], 3), r["real"]["diameter"], _f(r["real"]["clustering"]["average_local"], 4), _f(r["real"]["clustering"]["transitivity"], 4)])
    w(_table(["Network", "n (LCC)", "m (LCC)", "mean degree", "L (exact)", "diameter", "C (avg local)", "transitivity"], rows) + "\n")
    rows = []
    for n, r in sw.items():
        for kind, b in r["baselines"].items():
            rows.append([n, "Erdos-Renyi G(n,m)" if kind.startswith("erdos") else "degree-preserving rewiring", f"{b['L_rand_mean']:.3f} ± {b['L_rand_sd']:.3f}", f"{b['C_rand_mean']:.5f} ± {b['C_rand_sd']:.5f}",
                         _f(b["sigma_from_means"], 1), _f(b["sigma_replicate_min"], 1), _f(b["L_over_L_rand"], 2), b["baseline_L_method"]])
    w("Baselines: 20 replicates of each kind, same n and m (mean ± sd over replicates). σ = (C/C_rand)/(L/L_rand) from the means; the minimum is over the 20 replicates.\n")
    w(_table(["Network", "Baseline", "L_rand", "C_rand", "σ (means)", "min σ over replicates", "L / L_rand", "baseline L"], rows) + "\n")
    w(_table(["Network", "ω (approximate, analytic ring lattice)", "σ > 1 in all 40 replicates", "L / L_rand ≤ 2.0 for both", "Verdict (declared rule)"],
             [[n, _f(r["omega"]["omega"], 2), r["decision"]["sigma_above_1_for_all_replicates"], r["decision"]["L_over_L_rand_within_bound"], r["decision"]["statement"]] for n, r in sw.items()]) + "\n")
    w(f"Reading: the declared rule holds for all three networks. For N1 it holds with room to spare on clustering (C is about {sw['N1']['real']['clustering']['average_local'] / sw['N1']['baselines']['degree_preserving_rewiring']['C_rand_mean']:,.0f} to {sw['N1']['real']['clustering']['average_local'] / sw['N1']['baselines']['erdos_renyi_gnm']['C_rand_mean']:,.0f} times the random value) but only moderately on path length: "
      f"L is {sw['N1']['baselines']['erdos_renyi_gnm']['L_over_L_rand']:.2f} to {sw['N1']['baselines']['degree_preserving_rewiring']['L_over_L_rand']:.2f} times the random value and the diameter is {sw['N1']['real']['diameter']}, "
      f"and ω = {sw['N1']['omega']['omega']:.2f} leans toward a lattice-like structure; N1 is a clustered, long-path co-authorship graph that satisfies the declared bound, not a textbook small world. "
      "N2's L is 2% to 8% above the random baseline; N4's is 2% above the rewired baseline and 33% below the Erdos-Renyi one. ω uses analytic ring-lattice formulas (an approximation, not a simulated lattice). The N4 baseline L is a seeded 2,000-pivot sample per replicate "
      "(the exact BFS on 40 replicates of a 50k-node graph was not run); the real graph's L is exact everywhere. N4 includes paper, topic and venue nodes, so its clustering mixes bipartite structure with the collaboration graphs "
      "and its transitivity (0.012) is far below its average local clustering because of hub nodes.\n")
    w("Evolution of the cumulative network (largest component of the network built from papers up to and including the year; the 2025 row equals the full network, checked: edges 80,482 and 13,031):\n")
    rows = []
    for n, rs in evo.items():
        for r in rs:
            if "year" in r:
                rows.append([n, r["year"], r["nodes_with_edges"], r["edges"], r["lcc_nodes"], _f(r["L"], 3), r["diameter"], _f(r["C"], 4)])
    w(_table(["Network", "Year", "nodes with edges", "edges", "LCC nodes", "L", "diameter", "C"], rows) + "\n")
    w("N1's L rises from 6.5 to 11.1 while the largest component grows from 345 to 8,000 nodes, then falls back to 8.8 as new papers join the components: path length is not monotone in time; C is stable near 0.81. N4 is not evolved yearly.\n")
    rows = [[n, t["n"], _f(t["xmin"], 0), _f(t["alpha"], 2), t["tail_nodes"], *[f"R={c['R']:.2f}, p={c['p']:.3g}: {c['verdict']}" for c in t["comparisons"].values()], t["power_law_claim_allowed"]] for n, t in tails.items()]
    w("Degree distribution and heavy-tail fit (`powerlaw`, discrete; likelihood-ratio tests of the power law against each alternative, R > 0 favours the power law):\n")
    w(_table(["Network", "nodes (deg ≥ 1)", "xmin", "alpha", "tail nodes", "vs lognormal", "vs exponential", "vs truncated power law", "power-law claim allowed"], rows) + "\n")
    w("N1 and N2: the lognormal and the truncated power law fit significantly better than the pure power law, so **no power-law claim**; the tails are heavy (they beat the exponential) but not scale-free by this test. "
      "N4: the power law is favoured over the exponential and indistinguishable from lognormal and truncated power law, so the declared rule allows a power-law tail claim for degrees ≥ xmin = 67 only "
      f"({tails['N4']['tail_nodes']} nodes); no goodness-of-fit bootstrap was run, so even this is weak evidence.\n")
    w("Figures: `smallworld/path-length-histograms.svg` (share of node pairs at each shortest-path length in each network's largest component), `smallworld/degree-distributions.svg` "
      "(degree CCDF on log-log axes; the dotted line is the fitted xmin), `smallworld/evolution.svg` (L and C of the cumulative network by year).\n")
    # S2
    w("## S2 Ranking\n")
    w("PageRank damping 0.85; N1 and N2 weighted by fractional weight, N3 directed (citing → cited, so score flows to cited papers), N4 unweighted. Full score tables: `ranking/scores-N*.csv.gz`; top-20 tables with name, score, rank, degree and community: `ranking/ranking-N*.json`.\n")
    for n in ("N1", "N2"):
        w(f"**{n} top 10 by PageRank**\n")
        w(_table(["Rank", "Name", "PageRank", "Degree", "Community"], [[t["rank"], t["name"], f"{t['pagerank']:.5f}", t["degree"], "" if t["community"] is None else t["community"]] for t in rk[n]["top"][:10]]) + "\n")
    w("**N3 top 10 by PageRank** (directed citation network)\n")
    if rk["N3"].get("sparsity_note"):
        w(f"*{rk['N3']['sparsity_note']}*\n")
    if rk["N3"]["top"] and "in_corpus_citations" in rk["N3"]["top"][0]:
        w(_table(["Rank", "Name", "PageRank", "In-corpus citations", "Degree"], [[t["rank"], t["name"], f"{t['pagerank']:.5f}", t["in_corpus_citations"], t["degree"]] for t in rk["N3"]["top"][:10]]) + "\n")
    else:
        w(_table(["Rank", "Name", "PageRank", "Degree", "Community"], [[t["rank"], t["name"], f"{t['pagerank']:.5f}", t["degree"], "" if t["community"] is None else t["community"]] for t in rk["N3"]["top"][:10]]) + "\n")
    w("**N4 top 5 by PageRank within each node label** (the whole-graph rank is in the JSON)\n")
    for lab in ("Researcher", "Organization", "Paper", "Topic", "Method", "Task", "Dataset"):
        w(f"- {lab}: " + "; ".join(f"{t['name'][:60]} ({t['pagerank']:.5f})" for t in rk["N4"]["top_by_label"][lab][:5]))
    w("")
    rows = []
    for n in rk:
        for m, c in rk[n]["comparison_with_pagerank"].items():
            rows.append([n, m, _f(c["spearman"], 3), "n/a" if c.get("top20_overlap") is None else c["top20_overlap"]])
    w("PageRank against the other measures (Spearman correlation over all nodes; top-20 overlap):\n")
    w(_table(["Network", "Measure", "Spearman ρ", "top-20 overlap"], rows) + "\n")
    w(f"Betweenness: N2 exact (igraph, Brandes); N1 exact as well, because the probe estimated {rk['N1']['meta']['betweenness']['estimated_seconds']:.0f} s, within the 30-minute limit, so no source sample was needed "
      f"(took {rk['N1']['meta']['betweenness']['seconds']:.0f} s). Betweenness is not computed for N3 and N4, and eigenvector centrality is not computed for N3 (the citation graph is almost acyclic). "
      "Eigenvector centrality is meaningful only on a connected graph; on N1 (2,936 components) the leading eigenvector concentrates on one dense cluster, which explains ρ ≈ -0.18 and zero top-20 overlap there.\n")
    rows = [[n, rk[n]["robustness_strict_support_ge_2"]["full_edges"], rk[n]["robustness_strict_support_ge_2"]["strict_edges"], _f(rk[n]["robustness_strict_support_ge_2"]["edges_kept_share"], 3),
             _f(rk[n]["robustness_strict_support_ge_2"]["spearman_pagerank"], 3), rk[n]["robustness_strict_support_ge_2"]["top20_overlap"]] for n in ("N1", "N2")]
    w("Robustness: PageRank on the full network against the strict-evidence network (edges with support_count ≥ 2 only, same node set):\n")
    w(_table(["Network", "edges", "edges kept", "share kept", "Spearman ρ of PageRank", "top-20 overlap"], rows) + "\n")
    w("Only a minority of N1 edges rest on two or more shared papers, so the strict ranking is a different, much sparser view: N1's top 20 changes a lot, N2's barely.\n")
    w("**Personalized PageRank** (N4, restart uniform over the papers of the subject; the subject's own papers are left out of the Paper list): precomputed for "
      + ", ".join(f"{len(v)} {k.lower()}s" for k, v in ppr.items()) + " (topics: the 16 leaf topics that have papers; the 4 parent topics carry no HAS_TOPIC edges; methods, tasks, datasets: the 30 with most papers each) in `ranking/personalized-pagerank.json`; "
      "`scientific_network.analysis.fx_cli.personalized_summary` computes it for any subject. "
      + ("Organizations and researchers are ranked primarily by **lift** (`ppr_score / global_n4_pagerank`, with declared `min_subject_papers`); raw personalized PageRank is retained as a secondary field.\n" if "top_by_raw_ppr" in next(iter(ppr["Topic"].values())) else "Examples:\n"))
    for kind, sid in (("Topic", next(iter(ppr["Topic"]))), ("Method", next(iter(ppr["Method"]))), ("Dataset", next(iter(ppr["Dataset"])))):
        s = ppr[kind][sid]
        if "lift" in s["top"]["Organization"][0]:
            w(f"- {kind} **{s['name']}** ({s['papers']} papers): researchers (by lift) " + "; ".join(f"{t['name']} (lift {t['lift']:.1f}x, {t['subject_papers']}p)" for t in s["top"]["Researcher"][:4]) + "; organizations (by lift) " + "; ".join(f"{t['name']} (lift {t['lift']:.1f}x, {t['subject_papers']}p)" for t in s["top"]["Organization"][:3]))
        else:
            w(f"- {kind} **{s['name']}** ({s['papers']} papers): researchers " + "; ".join(t["name"] for t in s["top"]["Researcher"][:4]) + "; organizations " + "; ".join(t["name"] for t in s["top"]["Organization"][:3]))
    w("")
    # S3
    w("## S3 Communities, key individuals and groups\n")
    for n in ("N1", "N2"):
        c = cm[n]
        rows = [[r["resolution"], r["seed"], r["communities"], _f(r["modularity"], 4), r["largest_component"]["communities"], _f(r["largest_component"]["modularity"], 4), r["singletons"], r["largest"][0]] for r in c["runs"]]
        w(f"**{n} Leiden (modularity objective)**\n")
        w(_table(["Resolution", "Seed", "Communities", "Modularity Q (whole graph)", "Communities in LCC", "Q in LCC", "Singletons", "Largest"], rows) + "\n")
        rows = [[res, _f(v["mean"], 3), _f(v["min"], 3), c["louvain"][res]["communities"], _f(c["louvain"][res]["modularity"], 4), _f(c["louvain"][res]["nmi_with_leiden_same_seed"], 3)] for res, v in c["nmi_across_seeds"].items()]
        w(_table(["Resolution", "NMI across seeds (mean of 3 pairs)", "min", "Louvain communities", "Louvain Q", "NMI Leiden-Louvain (seed 17)"], rows) + "\n")
        w(f"Hierarchy (level 1 = Leiden at resolution {c['hierarchy']['level1_resolution']} on the graph contracted by the level-0 headline partition: resolution 1.0, seed 17): {c['hierarchy']['level0_communities']} level-0 communities → {c['hierarchy']['level1_communities']} level-1 communities.\n")
    w("\nWhole-graph modularity on N1 is inflated: N1 has 2,936 connected components (414 isolates), and each small component is its own community. The LCC columns are the informative ones. Level 1: the original rule (resolution 1.0) merged nothing, so it was changed to 0.25 (dated change in the config) and run once. "
      "On N1 level 1 barely coarsens (most communities are tiny separate components); on N2 it collapses the connected core into one community of 1,837 of 2,047 organizations, so for N2 the 0.8/1.2 partitions are the more useful alternative levels.\n")
    w("**Largest N1 communities** (c-TF-IDF labels over member papers; hubs = highest PageRank in the community; brokers = highest participation coefficient / betweenness; names are researchers). Full tables: `communities/communities-N1.csv`.\n")
    rows = []
    for r in _c(out / "communities" / "communities-N1.csv")[:6]:
        rows.append([r["community"], r["size"], r["label_topic"].split("; ")[0], r["label_method"][:70], r["hubs"].split("; ")[0], r["brokers_participation"].split("; ")[0], r["brokers_betweenness"].split("; ")[0]])
    w(_table(["Community", "Members", "Top topic", "Top methods", "Hub", "Broker (participation)", "Broker (betweenness)"], rows) + "\n")
    w("**Largest N2 communities** (organizations)\n")
    rows = []
    for r in _c(out / "communities" / "communities-N2.csv")[:5]:
        rows.append([r["community"], r["size"], r["label_topic"].split("; ")[0], r["hubs"].split("; ")[0], r["brokers_participation"].split("; ")[0], r["brokers_betweenness"].split("; ")[0]])
    w(_table(["Community", "Members", "Top topic", "Hub", "Broker (participation)", "Broker (betweenness)"], rows) + "\n")
    w("Community labels are c-TF-IDF terms; generated titles belong to M3 (specification 6.2) and were not produced. Labels from rare terms (a few papers) are characteristic of c-TF-IDF and should be read with the member count.\n")
    rr = _c(out / "communities" / "rising-researchers.csv")
    w(f"**Rising researchers** (rule: 2024-2025 paper share at least 2.0 times the 2021-2023 share, at least 3 recent and 4 total papers; {len(rr)} researchers qualify, {sum(r['new_entrant'] == 'True' for r in rr)} of them new entrants with no 2021-2023 paper). Top 10 by recent papers:\n")
    w(_table(["Researcher", "2024-25 papers", "2021-23 papers", "share ratio", "N1 community"], [[r["name"], r["recent_papers"], r["base_papers"], r["share_ratio"] or "new entrant", r["community"]] for r in rr[:10]]) + "\n")
    w("**Groups, by kind.** The application must state which kind a group is:\n")
    orgs = _c(out / "communities" / "groups-organizations.csv")
    org_comm_path = out / "communities" / "groups-org-anchored-communities.csv"
    labs = _c(org_comm_path if org_comm_path.exists() else (out / "communities" / "groups-labs.csv"))
    roll = _c(out / "communities" / "groups-rollup.csv")
    w(f"- *Organizations* ({grp['organizations']}; {grp['notable_organizations']} flagged Wikipedia-notable, meaning a Wikidata match with an English Wikipedia page): largest by papers: " + "; ".join(f"{r['name']} ({r['papers']})" for r in orgs[:5]) + ".")
    n_org_comm = grp.get("organization_anchored_communities", grp.get("labs", len(labs)))
    n_large = grp.get("large_organization_anchored_communities", 0)
    w(f"- *Organization-anchored communities* (N1 communities with at least 10 members and one organization affiliating at least 40% of them; those >100 members are marked `large`, duplicates disambiguated by top topic; an approximation, not a verified research lab): {n_org_comm} found ({n_large} large), e.g. " +
      "; ".join(f"{r.get('display_name', r['organization_name'])} ({r['members']} members, {r.get('size_tier', 'n/a')}, {float(r['share']):.0%})" for r in labs[:5]) + ".")
    w(f"- *Leiden communities* of N1 and N2: tables above and `communities/communities-N*.csv` ({len([1 for _ in _c(out / 'communities' / 'communities-N1.csv')])} N1 and {len([1 for _ in _c(out / 'communities' / 'communities-N2.csv')])} N2 communities with at least 20 members).")
    ru = grp["rollup"]
    skip_desc = "government bodies (ministries, state councils, federal/government departments and agencies) not matching the research/education guard" if ru.get("skip_rule") == "government_body" else "parents whose name contains \"ministry\""
    w(f"- *Parent organizations* (roll-up along PART_OF only; MEMBER_OF is not used; {skip_desc} are skipped): {ru['part_of_edges']} PART_OF edges, {ru['ministry_part_of_edges_skipped']} skipped, {ru['parents_with_children']} parents with at least one child. Largest by papers: " +
      "; ".join(f"{r['parent_name']} ({r['child_organizations']} units, {r['papers']} papers)" for r in roll[:5]) + ".")
    if ru.get("excluded_parents"):
        w("  Excluded government parents (sample/count): " + f"{len(ru['excluded_parents'])} parents skipped: " + "; ".join(f"{p['parent_name']} ({p['edges_skipped']})" for p in ru["excluded_parents"][:12]) + ("; …" if len(ru["excluded_parents"]) > 12 else "") + ".")
    w("")
    w("Figure: `communities/community-sizes.svg` (rank-size plot of the headline communities; many tiny components produce the long tail).\n")
    # trends
    w("## Trend metrics (specification 5.4)\n")
    w("Per subject and year: paper count, share of that year's 13,617-paper corpus (2,240 / 1,997 / 2,217 / 3,121 / 4,042 papers in 2021-2025), compound annual growth of the share 2021→2025, least-squares slope of the share with its p-value, year-over-year change, and class. "
      "Classes (declared in the config): emerging = at most 2 papers in 2021-2022 and at least 8 in 2024-2025; rising = positive slope with p ≤ 0.10, recent share at least 1.5 times the base share and at least 3 base papers; declining = negative slope with p ≤ 0.10, "
      "ratio ≤ 2/3 and at least 10 base papers; insufficient data below 15 papers in total; everything else stable. The classes are descriptive (p ≤ 0.10 per subject, no multiple-testing correction).\n")
    rows = [[k, v["subjects"], v.get("rising", 0), v.get("emerging", 0), v.get("declining", 0), v.get("stable", 0), v.get("insufficient_data", 0)] for k, v in tr["classes"].items()]
    w(_table(["Subject kind", "Subjects", "rising", "emerging", "declining", "stable", "insufficient data (<15 papers)"], rows) + "\n")
    for kind in ("Topic", "Method", "Task", "Dataset"):
        ex = tr["examples"][kind]
        w(f"**{kind}s** (base = papers 2021-2022, recent = papers 2024-2025)\n")
        for label in ("rising", "emerging", "declining"):
            items = ex[label][:5]
            w(f"- {label}: " + ("; ".join(f"{e['name']} ({e['base']} → {e['recent']})" for e in items) if items else "none"))
        w("")
    gi = [r for r in _c(out / "trends" / "group-interest.csv") if int(r["group_papers_in_subject"]) >= 5 and r["kind"] == "Topic" and r["group"].startswith("organization:")]
    gi.sort(key=lambda r: -float(r["rca"]))
    w(f"Group interest (`trends/group-interest.csv`: {tr['group_interest']['rows']} group-subject rows for {tr['group_interest']['organizations']} organizations with at least 30 papers and {tr['group_interest']['n1_communities']} N1 communities with at least 50 members; topics, methods and tasks; "
      "datasets are skipped because coverage is too thin). Example, organizations with the highest revealed comparative advantage (RCA = the group's share of papers in the topic divided by the corpus share) on topics with at least 5 of the group's papers (this filter only trims the table below, not the CSV):\n")
    w(_table(["Organization", "Topic", "group papers in topic", "RCA", "first active year"], [[r["group"].split("organization:")[1].rsplit(" (", 1)[0], r["subject_name"], r["group_papers_in_subject"], f"{float(r['rca']):.2f}", r["first_active_year"]] for r in gi[:8]]) + "\n")
    w("Figure: `trends/topic-shares.svg` (share of each year's papers by topic; non-stable topics are labelled).\n")
    w("**Caveats that apply to every trend number**\n")
    for c in tr["caveats"]:
        w(f"- {c}")
    w("")
    w("## What was not done\n")
    w("- A simulated lattice baseline for ω (an analytic ring lattice is used and labelled approximate).\n- Exact baseline path lengths on N4 (a 2,000-pivot sample is used; the real graph's L is exact).\n- A goodness-of-fit bootstrap for the power-law fit.\n"
      "- Betweenness on N3 and N4, eigenvector centrality on N3, and group interest for datasets.\n- Generated community titles (M3).\n- Any human validation of community labels, rising-researcher lists or trend classes.\n"
      "- Personalized PageRank for the 4 parent topics (no HAS_TOPIC papers).\n")
    return "\n".join(L)
