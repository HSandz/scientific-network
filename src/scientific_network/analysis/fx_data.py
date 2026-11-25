"""Final-exam analysis inputs: the graph file of the enriched graph as igraph networks N1-N4 plus lookup tables (specification 5).

The graph FILE is the single input, so every number is reproducible; Neo4j is not read. N1-N3 come from the v4 layer inside the file.
Nothing here modifies the frozen ``analyze`` outputs or any ``reports/release-v*`` file.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path

import igraph as ig

YEARS = (2021, 2022, 2023, 2024, 2025)
ENRICH_KIND_RELATIONS = {"Method": "USES_METHOD", "Task": "ADDRESSES_TASK", "Dataset": "USES_DATASET"}


@dataclass
class Inputs:
    graph_version: str
    graph_sha256: str
    nodes: dict[str, dict]
    networks: dict[str, ig.Graph]
    paper_year: dict[str, int]
    paper_authors: dict[str, list[str]]
    paper_topics: dict[str, list[str]]
    paper_entities: dict[str, dict[str, list[str]]]          # paper -> kind -> entity ids
    subject_papers: dict[str, dict[str, set[str]]]           # kind (Topic, Method, Task, Dataset) -> subject id -> papers
    affiliation_triples: list[tuple[str, str, str]]          # (researcher, paper, organization)
    researcher_orgs: dict[str, dict[str, int]]               # researcher -> organization -> supporting papers
    org_papers: dict[str, set[str]]
    notable_orgs: set[str]
    part_of: list[dict]                                      # {child, parent, parent_classes, ministry}
    counts: dict = field(default_factory=dict)

    def name(self, node_id: str) -> str:
        return self.nodes[node_id]["name"]


def _graph(ids: list[str], edges: list[tuple[str, str]], *, directed: bool, weights: list[float] | None = None, support: list[int] | None = None) -> ig.Graph:
    index = {n: i for i, n in enumerate(ids)}
    g = ig.Graph(n=len(ids), edges=[(index[a], index[b]) for a, b in edges], directed=directed)
    g.vs["id"] = ids
    if weights is not None:
        g.es["weight"] = weights
        g.es["distance"] = [1.0 / w for w in weights]
    if support is not None:
        g.es["support"] = support
    return g


def load_inputs(graph_path: Path, *, expected_sha256: str | None = None, expected_version: str | None = None) -> Inputs:
    raw = graph_path.read_bytes()
    digest = sha256(raw).hexdigest()
    if expected_sha256 and digest != expected_sha256:
        raise ValueError(f"graph file SHA-256 {digest} differs from the declared {expected_sha256}")
    graph = json.loads(raw)
    del raw
    if expected_version and graph["graph_version"] != expected_version:
        raise ValueError(f"graph version {graph['graph_version']} differs from the declared {expected_version}")
    nodes = {n["id"]: n for n in graph["nodes"]}
    label = {i: n["label"] for i, n in nodes.items()}
    by_rel: dict[str, list[dict]] = defaultdict(list)
    for e in graph["edges"]:
        by_rel[e["relation"]].append(e)

    def projection(node_label: str, relation: str, *, directed=False, weighted=True, core_only=False) -> ig.Graph:
        # the v4 layer only: parent-only Organization nodes added by enrichment (source wikidata_parent) are not part of N1-N3
        ids = sorted(i for i, n in nodes.items() if n["label"] == node_label and n["properties"].get("source") != "wikidata_parent"
                     and (not core_only or n["properties"].get("is_core") is True))
        keep = set(ids)
        edges = [e for e in by_rel[relation] if e["source_id"] in keep and e["target_id"] in keep]
        w = [float(e["properties"]["fractional_weight"]) for e in edges] if weighted else None
        s = [int(e["properties"].get("support_count", 1)) for e in edges]
        return _graph(ids, [(e["source_id"], e["target_id"]) for e in edges], directed=directed, weights=w, support=s)

    n1 = projection("Researcher", "COAUTHORED_WITH")
    n2 = projection("Organization", "COLLABORATED_WITH")
    n3 = projection("Paper", "CITES", directed=True, weighted=False, core_only=True)
    ids4 = sorted(nodes)
    idx4 = {n: i for i, n in enumerate(ids4)}
    n4 = ig.Graph(n=len(ids4), edges=[(idx4[e["source_id"]], idx4[e["target_id"]]) for e in graph["edges"]], directed=False)
    n4.vs["id"] = ids4
    n4_multi_edges = n4.ecount()
    n4.simplify(multiple=True, loops=True)

    paper_year = {i: int(n["properties"]["year"]) for i, n in nodes.items() if n["label"] == "Paper" and "year" in n["properties"]}
    for e in by_rel["PUBLISHED_IN"]:
        paper_year.setdefault(e["source_id"], int(e["properties"]["year"]))
    paper_authors: dict[str, list[str]] = defaultdict(list)
    for e in by_rel["AUTHORED"]:
        paper_authors[e["target_id"]].append(e["source_id"])
    paper_topics: dict[str, list[str]] = defaultdict(list)
    for e in by_rel["HAS_TOPIC"]:
        paper_topics[e["source_id"]].append(e["target_id"])
    paper_entities: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    subject_papers: dict[str, dict[str, set[str]]] = {"Topic": defaultdict(set), "Method": defaultdict(set), "Task": defaultdict(set), "Dataset": defaultdict(set)}
    for e in by_rel["HAS_TOPIC"]:
        subject_papers["Topic"][e["target_id"]].add(e["source_id"])
    for kind, rel in ENRICH_KIND_RELATIONS.items():
        for e in by_rel[rel]:
            paper_entities[e["source_id"]][kind].append(e["target_id"])
            subject_papers[kind][e["target_id"]].add(e["source_id"])
    triples = [(a["researcher_id"], a["paper_id"], a["organization_id"]) for a in graph["affiliation_observations"]]
    researcher_orgs: dict[str, dict[str, int]] = defaultdict(dict)
    for e in by_rel["AFFILIATED_WITH"]:
        researcher_orgs[e["source_id"]][e["target_id"]] = int(e["properties"].get("support_paper_count", 1))
    org_papers: dict[str, set[str]] = defaultdict(set)
    for _r, paper, org in triples:
        org_papers[org].add(paper)
    notable = {i for i, props in graph.get("node_enrichments", {}).items() if props.get("wikipedia_url")}
    evidence = {e["id"]: e for e in graph["evidence"] if e["id"].startswith("evidence:wikidata:") or e.get("kind") == "wikidata"}
    part_of = []
    for e in by_rel["PART_OF"]:
        classes = sorted({c for r in e["evidence_ids"] for c in evidence[r].get("parent_instance_of", [])})
        part_of.append({"child": e["source_id"], "parent": e["target_id"], "parent_classes": classes,
                        "ministry": any("ministry" in c.lower() for c in classes)})
    counts = {"nodes": len(nodes), "edges": len(graph["edges"]), "n4_simple_edges": n4.ecount(), "n4_edges_before_simplify": n4_multi_edges,
              "papers_with_year": len(paper_year), "papers_by_year": {str(y): sum(1 for v in paper_year.values() if v == y) for y in YEARS}}
    return Inputs(graph["graph_version"], digest, nodes, {"N1": n1, "N2": n2, "N3": n3, "N4": n4}, paper_year, dict(paper_authors), dict(paper_topics),
                  {p: dict(v) for p, v in paper_entities.items()}, {k: dict(v) for k, v in subject_papers.items()}, triples, dict(researcher_orgs), dict(org_papers),
                  notable, part_of, counts)


# --- cumulative networks for the evolution of L and C ---------------------------------------------------------------------

def cumulative_pairs(inputs: Inputs, network: str) -> dict[int, set[tuple[str, str]]]:
    """Edge sets of the cumulative network up to and including each year, rebuilt from per-paper evidence (N1: co-authors; N2: distinct researchers of two organizations)."""
    by_paper_orgs: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for researcher, paper, org in inputs.affiliation_triples:
        by_paper_orgs[paper][org].add(researcher)
    first: dict[tuple[str, str], int] = {}
    for paper, year in inputs.paper_year.items():
        if network == "N1":
            authors = sorted(set(inputs.paper_authors.get(paper, [])))
            pairs = [(a, b) for i, a in enumerate(authors) for b in authors[i + 1:]]
        else:
            orgs = sorted(by_paper_orgs.get(paper, {}))
            pairs = [(a, b) for i, a in enumerate(orgs) for b in orgs[i + 1:] if by_paper_orgs[paper][a] | by_paper_orgs[paper][b] and
                     any(x != y for x in by_paper_orgs[paper][a] for y in by_paper_orgs[paper][b])]
        for pair in pairs:
            if pair not in first or year < first[pair]:
                first[pair] = year
    return {y: {p for p, f in first.items() if f <= y} for y in YEARS}


def edge_pairs(g: ig.Graph) -> set[tuple[str, str]]:
    ids = g.vs["id"]
    return {tuple(sorted((ids[e.source], ids[e.target]))) for e in g.es}


def sanity_check(inputs: Inputs, v4_analysis: dict) -> dict:
    """Overlapping figures against ``reports/release-v4/analysis.json`` (the frozen v4 networkx analysis)."""
    rows = []

    def add(name, ours, theirs, tol=0.0):
        ok = (ours == theirs) if isinstance(ours, (int, str)) and tol == 0 else abs(ours - theirs) <= max(tol, 1e-9)
        rows.append({"metric": name, "ours": ours, "v4": theirs, "match": bool(ok)})

    for ours, theirs in (("N1", "researcher_collaboration"), ("N2", "organization_collaboration"), ("N3", "core_citations")):
        g, p = inputs.networks[ours], v4_analysis["projections"][theirs]
        add(f"{ours} nodes", g.vcount(), p["node_count"])
        add(f"{ours} edges", g.ecount(), p["edge_count"])
        add(f"{ours} isolates", sum(1 for d in g.degree() if d == 0), p["isolate_count"])
        add(f"{ours} max degree", max(g.degree(mode="all")), p["degree_max"])
        if g.is_directed():
            comps = sorted(g.connected_components(mode="weak").sizes(), reverse=True)
        else:
            comps = sorted(g.connected_components().sizes(), reverse=True)
        theirs_sizes = p["weak_or_undirected_component_sizes"]
        add(f"{ours} largest component", comps[0], theirs_sizes[0] if isinstance(theirs_sizes, list) else max(theirs_sizes))
        add(f"{ours} component count", len(comps), len(theirs_sizes) if isinstance(theirs_sizes, list) else None)
        if g.es and "weight" in g.es.attributes():
            add(f"{ours} strength sum (weighted degree total / 2)", round(sum(g.es["weight"]), 6), round(p["strength_sum"], 6), tol=1e-3)
    return {"all_match": all(r["match"] for r in rows), "rows": rows}
