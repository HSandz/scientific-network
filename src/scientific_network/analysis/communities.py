"""S3 communities and key individuals (specification 5.3): Leiden/Louvain, stability, hierarchy, c-TF-IDF labels, hubs, brokers, rising researchers, groups.

Presentation rules (work log WORK-2026-11-25-004, dated note in specification 5.3): organizations roll up along PART_OF only, never MEMBER_OF,
and parents whose name contains "ministry" are skipped. Community labels are c-TF-IDF terms only; generated titles belong to M3.
"""

from __future__ import annotations

import math
import random
from collections import Counter, defaultdict

import igraph as ig
import leidenalg
import numpy as np

from .fx_data import YEARS, Inputs


def leiden(g: ig.Graph, resolution: float, seed: int) -> ig.VertexClustering:
    part = leidenalg.find_partition(g, leidenalg.RBConfigurationVertexPartition, weights="weight" if "weight" in g.es.attributes() else None,
                                    resolution_parameter=resolution, seed=seed, n_iterations=-1)
    return ig.VertexClustering(g, part.membership)


def louvain(g: ig.Graph, resolution: float, seed: int) -> ig.VertexClustering:
    random.seed(seed)
    return g.community_multilevel(weights="weight" if "weight" in g.es.attributes() else None, resolution=resolution)


def modularity(g: ig.Graph, membership: list[int], resolution: float) -> float:
    return g.modularity(membership, weights="weight" if "weight" in g.es.attributes() else None, resolution=resolution)


def lcc_summary(g: ig.Graph, membership: list[int], resolution: float) -> dict:
    """Communities and modularity restricted to the largest connected component (the whole-graph figures are inflated by many tiny components)."""
    keep = max(g.connected_components(), key=len)
    sub = g.induced_subgraph(keep)
    m = [membership[v] for v in keep]
    return {"nodes": len(keep), "communities": len(set(m)), "modularity": modularity(sub, m, 1.0), "modularity_at_resolution": modularity(sub, m, resolution)}


def size_summary(membership: list[int]) -> dict:
    sizes = sorted(Counter(membership).values(), reverse=True)
    a = np.asarray(sizes)
    return {"communities": len(sizes), "singletons": int((a == 1).sum()), "largest": sizes[:10], "median": float(np.median(a)), "mean": float(a.mean()),
            "share_in_top10": float(a[:10].sum() / a.sum()), "histogram_log2": {str(2 ** b): int(((a >= 2 ** b) & (a < 2 ** (b + 1))).sum()) for b in range(int(math.log2(a.max())) + 1)}}


def run_partitions(name: str, g: ig.Graph, cfg: dict, log=print) -> dict:
    c = cfg["communities"]
    out = {"network": name, "runs": [], "nmi_across_seeds": {}, "louvain": {}}
    members: dict[tuple[float, int], list[int]] = {}
    for res in c["resolutions"]:
        for seed in c["seeds"]:
            cl = leiden(g, res, seed)
            members[(res, seed)] = cl.membership
            out["runs"].append({"resolution": res, "seed": seed, "modularity": modularity(g, cl.membership, 1.0), "modularity_at_resolution": modularity(g, cl.membership, res),
                                "largest_component": lcc_summary(g, cl.membership, res), **size_summary(cl.membership)})
            log(f"  {name} leiden res={res} seed={seed}: {len(set(cl.membership))} communities, Q(1.0)={out['runs'][-1]['modularity']:.4f}")
        pairs = [(a, b) for i, a in enumerate(c["seeds"]) for b in c["seeds"][i + 1:]]
        nmis = [ig.compare_communities(members[(res, a)], members[(res, b)], method="nmi") for a, b in pairs]
        out["nmi_across_seeds"][str(res)] = {"pairs": [f"{a}-{b}" for a, b in pairs], "values": nmis, "mean": float(np.mean(nmis)), "min": float(np.min(nmis))}
        lv = louvain(g, res, c["seeds"][0])
        out["louvain"][str(res)] = {"seed": c["seeds"][0], "communities": len(lv), "modularity": modularity(g, lv.membership, 1.0),
                                    "nmi_with_leiden_same_seed": ig.compare_communities(members[(res, c["seeds"][0])], lv.membership, method="nmi")}
    out["_members"] = members
    return out


def hierarchy(g: ig.Graph, level0: list[int], resolution: float, seed: int) -> dict:
    """Level 1: Leiden at ``resolution`` on the graph contracted by the level-0 communities, so level 1 nests level 0.

    Resolution 1.0 merges nothing (a converged optimum is stable under aggregation); the config declares a coarser level-1 resolution (change of 2026-11-25).
    """
    agg = g.copy()
    agg.contract_vertices(level0)
    agg.simplify(combine_edges={"weight": "sum"} if "weight" in g.es.attributes() else "sum", loops=False)
    for attr in [a for a in agg.es.attributes() if a != "weight"]:
        del agg.es[attr]
    top = leiden(agg, resolution, seed)
    level1 = [top.membership[c] for c in level0]
    return {"level0_communities": len(set(level0)), "level1_communities": len(set(level1)), "level1_membership": level1,
            "modularity_level1": modularity(g, level1, 1.0), "level1_resolution": resolution}


# --- labels -----------------------------------------------------------------------------------------------------------

def ctfidf(counts_by_class: dict[int, Counter], top_n: int) -> dict[int, list[tuple[str, float]]]:
    """Class-based TF-IDF (Grootendorst, BERTopic): tf = count / class total, idf = log(1 + mean class size / total count of the term)."""
    classes = list(counts_by_class)
    totals = Counter()
    for c in counts_by_class.values():
        totals.update(c)
    mean_size = np.mean([sum(c.values()) for c in counts_by_class.values()]) if classes else 0
    out = {}
    for k, c in counts_by_class.items():
        size = sum(c.values())
        scored = [(t, (n / size) * math.log(1 + mean_size / totals[t])) for t, n in c.items()] if size else []
        out[k] = sorted(scored, key=lambda x: (-x[1], x[0]))[:top_n]
    return out


def community_terms(inputs: Inputs, ids: list[str], membership: list[int], network: str) -> dict[str, dict[int, Counter]]:
    """Per community, term counts over its member papers: Topic, Method, Task, Dataset and Organization."""
    papers_of: dict[str, set[str]] = defaultdict(set)
    if network == "N1":
        for paper, authors in inputs.paper_authors.items():
            for a in authors:
                papers_of[a].add(paper)
    else:
        papers_of = {o: set(p) for o, p in inputs.org_papers.items()}
    counts: dict[str, dict[int, Counter]] = {k: defaultdict(Counter) for k in ("Topic", "Method", "Task", "Dataset", "Organization")}
    for node_id, comm in zip(ids, membership):
        for paper in papers_of.get(node_id, ()):
            counts["Topic"][comm].update(inputs.paper_topics.get(paper, []))
            for kind, items in inputs.paper_entities.get(paper, {}).items():
                counts[kind][comm].update(items)
        if network == "N1":
            counts["Organization"][comm].update({o: 1 for o in inputs.researcher_orgs.get(node_id, {})})
        else:
            counts["Organization"][comm][node_id] += 1
    return counts


def community_labels(inputs: Inputs, ids: list[str], membership: list[int], network: str, top_n: int) -> dict[int, dict[str, list[dict]]]:
    terms = community_terms(inputs, ids, membership, network)
    labels: dict[int, dict[str, list[dict]]] = defaultdict(dict)
    for kind, per_class in terms.items():
        for comm, scored in ctfidf({k: v for k, v in per_class.items() if v}, top_n).items():
            labels[comm][kind] = [{"id": t, "name": inputs.nodes[t]["name"] if t in inputs.nodes else t, "score": round(s, 4), "count": per_class[comm][t]} for t, s in scored]
    return dict(labels)


# --- individuals ------------------------------------------------------------------------------------------------------

def participation_coefficient(g: ig.Graph, membership: list[int]) -> list[float]:
    out = []
    for v in range(g.vcount()):
        nbrs = g.incident(v)
        w = [g.es[e]["weight"] if "weight" in g.es.attributes() else 1.0 for e in nbrs]
        total = sum(w)
        if total == 0:
            out.append(0.0)
            continue
        per = defaultdict(float)
        for e, x in zip(nbrs, w):
            other = g.es[e].source if g.es[e].target == v else g.es[e].target
            per[membership[other]] += x
        out.append(1 - sum((x / total) ** 2 for x in per.values()))
    return out


def key_individuals(g: ig.Graph, membership: list[int], pagerank: list[float], betweenness: list[float], cfg: dict) -> dict[int, dict]:
    """Per community of at least ``minimum_community_size``: hubs by global PageRank, brokers by participation coefficient and by betweenness."""
    ki = cfg["communities"]["key_individuals"]
    pc = participation_coefficient(g, membership)
    by_comm: dict[int, list[int]] = defaultdict(list)
    for v, c in enumerate(membership):
        by_comm[c].append(v)
    out = {}
    for comm, vs in by_comm.items():
        if len(vs) < ki["minimum_community_size"]:
            continue
        n = ki["top_n"]
        # brokers need a minimum degree so a degree-1 node cannot score; participation is zero for single-community neighbours anyway
        out[comm] = {"hubs": [g.vs[v]["id"] for v in sorted(vs, key=lambda v: -pagerank[v])[:n]],
                     "brokers_participation": [g.vs[v]["id"] for v in sorted((v for v in vs if g.degree(v) >= 3), key=lambda v: -pc[v])[:n]],
                     "brokers_betweenness": [g.vs[v]["id"] for v in sorted(vs, key=lambda v: -betweenness[v])[:n]]}
    return out


def rising_researchers(inputs: Inputs, cfg: dict) -> list[dict]:
    """Declared rule: share_ratio >= 2.0, recent papers >= 3 and total papers >= 4 (config rising_researchers); zero base papers = new entrant."""
    r = cfg["rising_researchers"]
    recent_years, base_years = set(r["recent_years"]), set(r["base_years"])
    recent_total = sum(1 for y in inputs.paper_year.values() if y in recent_years)
    base_total = sum(1 for y in inputs.paper_year.values() if y in base_years)
    recent, base = Counter(), Counter()
    for paper, authors in inputs.paper_authors.items():
        y = inputs.paper_year.get(paper)
        for a in set(authors):
            if y in recent_years:
                recent[a] += 1
            elif y in base_years:
                base[a] += 1
    rows = []
    for a, rc in recent.items():
        bc = base.get(a, 0)
        if rc < r["min_recent_papers"] or rc + bc < r["min_total_papers"]:
            continue
        ratio = math.inf if bc == 0 else (rc / recent_total) / (bc / base_total)
        if ratio >= r["min_share_ratio"]:
            rows.append({"id": a, "name": inputs.nodes[a]["name"], "recent_papers": rc, "base_papers": bc, "share_ratio": None if ratio == math.inf else round(ratio, 3),
                         "new_entrant": bc == 0})
    return sorted(rows, key=lambda x: (-x["recent_papers"], x["share_ratio"] is None, -(x["share_ratio"] or 0), x["id"]))


# --- groups -----------------------------------------------------------------------------------------------------------

def labs(inputs: Inputs, ids: list[str], membership: list[int], cfg: dict) -> list[dict]:
    """Organization-anchored N1 communities: at least ``minimum_members`` researchers and one organization affiliating >= ``minimum_top_organization_share`` of them."""
    c = cfg["groups"]["lab"]
    members: dict[int, list[str]] = defaultdict(list)
    for i, comm in zip(ids, membership):
        members[comm].append(i)
    rows = []
    for comm, ms in members.items():
        if len(ms) < c["minimum_members"]:
            continue
        orgs = Counter(o for m in ms for o in inputs.researcher_orgs.get(m, {}))
        if not orgs:
            continue
        org, n = orgs.most_common(1)[0]
        if n / len(ms) >= c["minimum_top_organization_share"]:
            rows.append({"community": comm, "members": len(ms), "organization": org, "organization_name": inputs.nodes[org]["name"], "share": round(n / len(ms), 3),
                         "notable_organization": org in inputs.notable_orgs})
    return sorted(rows, key=lambda r: -r["members"])


def rollup(inputs: Inputs) -> dict:
    """Roll organizations up along PART_OF only; ministry parents (name contains 'ministry') are skipped. Returns parent -> descendant organizations and papers."""
    parents: dict[str, set[str]] = defaultdict(set)
    skipped = 0
    for e in inputs.part_of:
        if e["ministry"]:
            skipped += 1
            continue
        parents[e["child"]].add(e["parent"])
    ancestors: dict[str, set[str]] = {}

    def climb(org: str, seen: frozenset) -> set[str]:
        out = set()
        for p in parents.get(org, ()):
            if p in seen:
                continue
            out.add(p)
            out |= climb(p, seen | {p})
        return out

    for org in list(parents):
        ancestors[org] = climb(org, frozenset({org}))
    children: dict[str, set[str]] = defaultdict(set)
    for org, ancs in ancestors.items():
        for a in ancs:
            children[a].add(org)
    rows = []
    for parent, kids in children.items():
        papers = set(inputs.org_papers.get(parent, set()))
        for k in kids:
            papers |= inputs.org_papers.get(k, set())
        rows.append({"parent": parent, "parent_name": inputs.nodes[parent]["name"], "child_organizations": len(kids), "papers": len(papers),
                     "parent_is_v4_organization": inputs.nodes[parent]["properties"].get("source") != "wikidata_parent", "notable": parent in inputs.notable_orgs})
    return {"part_of_edges": len(inputs.part_of), "ministry_part_of_edges_skipped": skipped, "ministry_part_of_edges_by_class_label": sum(e["ministry_by_class_label"] for e in inputs.part_of),
            "member_of_used": False, "parents": sorted(rows, key=lambda r: (-r["papers"], r["parent"]))}
