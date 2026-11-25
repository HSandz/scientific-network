"""Final-exam analysis tests (specification 5, section 7). Every graph and series here is invented; none of it is a measured result."""

import random
from pathlib import Path
from types import SimpleNamespace

import igraph as ig
import networkx as nx
import pytest
import yaml

from scientific_network.analysis import communities, ranking, smallworld, trends
from scientific_network.analysis.fx_data import YEARS

CFG = yaml.safe_load((Path(__file__).parents[1] / "configs" / "analysis-final-exam-v1.yaml").read_text())
SMALL = {**CFG, "small_world": {**CFG["small_world"], "baselines": {"erdos_renyi_gnm": 4, "degree_preserving_rewiring": 4, "rewiring_swaps_per_edge": 10},
                                "baseline_l": {"exact_when_nodes_at_most": 30000, "pivots": 50}}}


def _quiet(*_):
    pass


def test_small_world_sigma_direction_lattice_vs_er():
    random.seed(3)
    ws = ig.Graph.Watts_Strogatz(1, 600, 4, 0.05)
    ws.simplify()
    holds = smallworld.small_world("ws", ws, SMALL, 5, log=_quiet)
    assert holds["decision"]["small_world_holds"]
    assert holds["baselines"]["erdos_renyi_gnm"]["sigma_from_means"] > 5
    # a pure ring lattice is clustered but its paths are far longer than random: L / L_rand fails the declared bound
    ring = ig.Graph.Watts_Strogatz(1, 600, 4, 0.0)  # ring lattice, no rewiring
    lattice = smallworld.small_world("ring", ring, SMALL, 5, log=_quiet)
    assert lattice["baselines"]["erdos_renyi_gnm"]["L_over_L_rand"] > 2
    assert not lattice["decision"]["small_world_holds"]
    # an Erdos-Renyi graph has no excess clustering: sigma stays near 1 and the rule does not hold
    random.seed(4)
    er = ig.Graph.Erdos_Renyi(n=600, m=1800)
    result = smallworld.small_world("er", er, SMALL, 7, log=_quiet)
    assert abs(result["baselines"]["erdos_renyi_gnm"]["sigma_from_means"] - 1) < 0.5
    assert not result["decision"]["small_world_holds"]


def test_exact_paths_known_graph():
    path = ig.Graph.Lattice([5], circular=False)  # path on 5 nodes: distances 1x4, 2x3, 3x2, 4x1
    r = smallworld.exact_paths(path)
    assert r["histogram"] == {1: 4, 2: 3, 3: 2, 4: 1}
    assert r["diameter"] == 4
    assert r["L"] == pytest.approx((4 + 6 + 6 + 4) / 10)
    triangle_tail = ig.Graph([(0, 1), (1, 2), (0, 2), (2, 3)])
    c = smallworld.clustering(triangle_tail)
    assert c["average_local"] == pytest.approx((1 + 1 + 1 / 3 + 0) / 4)
    assert c["transitivity"] == pytest.approx(3 / 5)


def test_pagerank_matches_networkx_and_known_values():
    cycle = ig.Graph([(0, 1), (1, 2), (2, 0)], directed=True)
    assert ranking.pagerank(cycle, weighted=False) == pytest.approx([1 / 3] * 3)
    g = ig.Graph([(0, 1), (0, 2), (0, 3), (3, 4)])
    g.es["weight"] = [1.0, 1.0, 1.0, 3.0]
    ours = ranking.pagerank(g, weighted=True)
    nxg = nx.Graph()
    nxg.add_weighted_edges_from([(e.source, e.target, e["weight"]) for e in g.es])
    theirs = nx.pagerank(nxg, alpha=0.85, weight="weight")
    assert ours == pytest.approx([theirs[i] for i in range(5)], abs=1e-6)
    assert ours[3] == max(ours)  # the heavy edge 3-4 and the hub's edge make node 3 the highest


def test_personalized_pagerank_concentrates_on_seeds():
    g = ig.Graph.Lattice([10], circular=False)
    scores = ranking.personalized_pagerank(g, [0])
    assert scores[0] > scores[5] > scores[9]
    assert scores[0] > ranking.pagerank(g, weighted=False)[0]
    with pytest.raises(ValueError):
        ranking.personalized_pagerank(g, [])


def test_strict_filter_and_centralities_shape():
    g = ig.Graph([(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)])
    g.es["weight"] = [1.0] * 5
    g.es["distance"] = [1.0] * 5
    g.es["support"] = [2, 1, 2, 1, 3]
    g.vs["id"] = list("abcd")
    assert ranking.strict_subgraph(g, 2).ecount() == 3
    df, meta = ranking.centralities(g, CFG, 1, weighted=True, betweenness_mode="exact")
    assert list(df["id"]) == list("abcd") and meta["betweenness"]["method"].startswith("exact")
    cmp = ranking.compare(df, k=2)
    assert set(cmp) == {"degree", "strength", "betweenness", "eigenvector"}


def _two_cliques():
    edges = [(a, b) for lo in (0, 6) for a in range(lo, lo + 6) for b in range(a + 1, lo + 6)] + [(5, 6)]
    g = ig.Graph(edges)
    g.es["weight"] = [1.0] * g.ecount()
    g.vs["id"] = [f"n{i}" for i in range(12)]
    return g


def test_leiden_determinism_and_structure():
    g = _two_cliques()
    a, b = communities.leiden(g, 1.0, 17).membership, communities.leiden(g, 1.0, 17).membership
    assert a == b
    assert len(set(a)) == 2 and a[0] == a[5] and a[6] == a[11] and a[0] != a[6]
    assert ig.compare_communities(a, communities.louvain(g, 1.0, 17).membership, method="nmi") == pytest.approx(1.0)
    h = communities.hierarchy(g, a, 0.25, 17)
    assert h["level0_communities"] == 2 and h["level1_communities"] <= 2
    pc = communities.participation_coefficient(g, a)
    assert pc[5] > pc[0] == 0  # the bridge node has a neighbour in the other community; an interior node has none


def test_ctfidf_prefers_distinctive_terms():
    counts = {0: {"common": 10, "alpha": 8}, 1: {"common": 10, "beta": 6}}
    from collections import Counter
    out = communities.ctfidf({k: Counter(v) for k, v in counts.items()}, 2)
    assert out[0][0][0] == "alpha" and out[1][0][0] == "beta"


def _inputs_for_rules():
    nodes = {n: {"name": n, "label": "Organization", "properties": {}} for n in "ABCDMX"}
    nodes["P"] = {"name": "Parent University", "label": "Organization", "properties": {"source": "wikidata_parent"}}
    nodes["M"]["name"] = "Ministry of Education"
    part_of = [{"child": "A", "parent": "P", "ministry": False, "ministry_by_class_label": False},
               {"child": "B", "parent": "A", "ministry": False, "ministry_by_class_label": False},
               {"child": "C", "parent": "M", "ministry": True, "ministry_by_class_label": True},
               {"child": "D", "parent": "X", "ministry": False, "ministry_by_class_label": True}]
    org_papers = {"A": {"p1"}, "B": {"p2"}, "C": {"p3"}, "D": {"p4"}}
    return SimpleNamespace(part_of=part_of, nodes=nodes, org_papers=org_papers, notable_orgs={"P"})


def test_rollup_part_of_only_skips_ministries_and_never_uses_member_of():
    r = communities.rollup(_inputs_for_rules())
    parents = {row["parent"]: row for row in r["parents"]}
    assert "M" not in parents and r["ministry_part_of_edges_skipped"] == 1 and r["member_of_used"] is False
    assert parents["P"]["child_organizations"] == 2 and parents["P"]["papers"] == 2  # A and its child B roll up to P
    assert parents["A"]["child_organizations"] == 1
    assert parents["X"]["papers"] == 1  # flagged by class label only: stays in the roll-up under the declared name rule


def test_rising_researchers_rule():
    # 4 base papers (2021-2023) and 4 recent papers (2024-2025) in the invented corpus
    year = {f"p{i}": y for i, y in enumerate([2021, 2022, 2023, 2023, 2024, 2024, 2025, 2025])}
    papers = {
        "p0": ["steady"], "p1": ["steady"], "p2": ["steady"], "p3": ["steady"],
        "p4": ["new", "steady"], "p5": ["new", "steady"], "p6": ["new", "steady"], "p7": ["new", "few", "steady"],
    }
    inputs = SimpleNamespace(paper_year=year, paper_authors=papers, nodes={a: {"name": a} for a in ("new", "steady", "few", "grower")})
    rows = communities.rising_researchers(inputs, CFG)
    # 'steady' keeps a flat share (ratio 1), 'few' has one recent paper; 'new' has 4 recent papers and none before: a flagged new entrant
    assert [r["id"] for r in rows] == ["new"]
    assert rows[0]["new_entrant"] is True and rows[0]["share_ratio"] is None
    # a researcher with 1 base and 3 recent papers: ratio 3 >= 2 and total 4: rising, not a new entrant
    papers["p0"].append("grower")
    for p in ("p5", "p6", "p7"):
        papers[p].append("grower")
    rows = communities.rising_researchers(inputs, CFG)
    grower = next(r for r in rows if r["id"] == "grower")
    assert grower["new_entrant"] is False and grower["share_ratio"] == pytest.approx(3.0)


TOTALS = {2021: 100, 2022: 100, 2023: 150, 2024: 250, 2025: 300}


def _series(*counts):
    return dict(zip(YEARS, counts))


def test_trend_classification_on_invented_series():
    assert trends.classify(_series(4, 6, 10, 25, 40), TOTALS, CFG)["class"] == "rising"
    assert trends.classify(_series(1, 1, 2, 10, 20), TOTALS, CFG)["class"] == "emerging"
    assert trends.classify(_series(30, 25, 20, 15, 10), TOTALS, CFG)["class"] == "declining"
    assert trends.classify(_series(10, 10, 15, 25, 30), TOTALS, CFG)["class"] == "stable"  # share is constant at 10%
    assert trends.classify(_series(1, 1, 1, 2, 2), TOTALS, CFG)["class"] == "insufficient_data"
    flat = trends.classify(_series(10, 10, 15, 25, 30), TOTALS, CFG)
    assert flat["slope_of_share"] == pytest.approx(0, abs=1e-12) and flat["cagr_of_share_2021_2025"] == pytest.approx(0, abs=1e-12)
    # raw counts rise 3x here while the share is flat: the default measure (share) must not call it rising
    r = trends.classify(_series(4, 6, 10, 25, 40), TOTALS, CFG)
    assert r["cagr_of_share_2021_2025"] == pytest.approx((r["share_by_year"]["2025"] / r["share_by_year"]["2021"]) ** 0.25 - 1)


def test_group_interest_rca():
    inputs = SimpleNamespace(subject_papers={"Topic": {"t1": {f"p{i}" for i in range(20)}}}, paper_year={f"p{i}": 2021 + i % 5 for i in range(100)},
                             nodes={"t1": {"name": "T1"}})
    rows = trends.group_interest(inputs, "Topic", {"g": {f"p{i}" for i in range(10)}}, CFG)
    assert rows[0]["group_papers_in_subject"] == 10 and rows[0]["share_of_group"] == 1.0
    assert rows[0]["rca"] == pytest.approx(1.0 / 0.2)


def test_eigenvector_computed_on_undirected_and_not_fatal_on_dag():
    g = _two_cliques()
    g.es["distance"] = [1.0] * g.ecount()
    df, meta = ranking.centralities(g, CFG, 1, weighted=True, betweenness_mode="none")
    assert df["eigenvector"].notna().all() and "eigenvector_error" not in meta
    dag = ig.Graph([(0, 1), (1, 2)], directed=True)
    dag.vs["id"] = ["a", "b", "c"]
    df, _meta = ranking.centralities(dag, CFG, 1, weighted=False, betweenness_mode="none")  # must not raise
    assert len(df) == 3


def test_phase0_evolution_clustering_equals_headline():
    # Two-year synthetic cumulative network where LCC < full graph in year 2024 and equals full graph in 2025
    pairs = {
        2024: {("a", "b"), ("b", "c"), ("a", "c"), ("x", "y")},
        2025: {("a", "b"), ("b", "c"), ("a", "c"), ("c", "d"), ("d", "e"), ("c", "e")},
    }
    evo = smallworld.evolution(pairs)
    g2025 = ig.Graph(n=5, edges=[(0, 1), (1, 2), (0, 2), (2, 3), (3, 4), (2, 4)])
    lcc = smallworld.largest_component(g2025)
    headline_c = smallworld.clustering(lcc)["average_local"]
    assert evo[-1]["year"] == 2025
    assert evo[-1]["C"] == pytest.approx(headline_c)
    assert evo[-1]["C"] == evo[-1]["C_lcc"]


def test_phase0_ppr_lift_ranking_and_min_papers():
    from scientific_network.analysis.fx_cli import personalized_summary
    # Star-like graph: org_big is connected to many papers, org_spec only to subject papers
    nodes = {
        "t1": {"id": "t1", "label": "Topic", "name": "Topic 1"},
        "org_big": {"id": "org_big", "label": "Organization", "name": "Big Org"},
        "org_spec": {"id": "org_spec", "label": "Organization", "name": "Spec Org"},
        "r1": {"id": "r1", "label": "Researcher", "name": "R1"},
        "r2": {"id": "r2", "label": "Researcher", "name": "R2"},
    }
    for i in range(6):
        nodes[f"p{i}"] = {"id": f"p{i}", "label": "Paper", "name": f"Paper {i}"}
    ids = list(nodes)
    idx = {n: i for i, n in enumerate(ids)}
    edges = [
        (idx["p0"], idx["org_spec"]), (idx["p1"], idx["org_spec"]), (idx["p2"], idx["org_spec"]),
        (idx["p0"], idx["org_big"]), (idx["p3"], idx["org_big"]), (idx["p4"], idx["org_big"]), (idx["p5"], idx["org_big"]),
        (idx["p0"], idx["r1"]), (idx["p1"], idx["r1"]), (idx["p2"], idx["r2"]),
    ]
    g4 = ig.Graph(n=len(ids), edges=edges, directed=False)
    g4.vs["id"] = ids
    global_pr = dict(zip(ids, ranking.pagerank(g4, weighted=False)))
    inputs = SimpleNamespace(
        nodes=nodes,
        subject_papers={"Topic": {"t1": {"p0", "p1", "p2"}}},
        paper_year={f"p{i}": 2024 for i in range(6)},
        org_papers={"org_spec": {"p0", "p1", "p2"}, "org_big": {"p0", "p3", "p4", "p5"}},
        researcher_papers={"r1": {"p0", "p1"}, "r2": {"p2"}},
    )
    res = personalized_summary(
        inputs, g4, idx, "Topic", "t1", {"Organization": 5, "Researcher": 5},
        global_pagerank=global_pr, min_subject_papers={"Organization": 3, "Researcher": 2},
        fallback_if_fewer_than=1,
    )
    assert [o["id"] for o in res["top"]["Organization"]] == ["org_spec"]  # org_big has only 1 subject paper (<3)
    assert res["top"]["Organization"][0]["lift"] > 1.0
    assert res["top"]["Organization"][0]["rca"] == pytest.approx(2.0)
    assert [r["id"] for r in res["top"]["Researcher"]] == ["r1"]
    assert "top_by_raw_ppr" in res


def test_phase0_government_body_rollup_rule():
    cfg_v2 = yaml.safe_load((Path(__file__).parents[1] / "configs" / "analysis-final-exam-v2.yaml").read_text())
    nodes = {
        "c1": {"name": "Inst A", "label": "Organization", "properties": {}},
        "c2": {"name": "Lab B", "label": "Organization", "properties": {}},
        "c3": {"name": "Dept C", "label": "Organization", "properties": {}},
        "sc": {"name": "State Council of the People's Republic of China", "label": "Organization", "properties": {"source": "wikidata_parent"}},
        "cas": {"name": "Chinese Academy of Sciences", "label": "Organization", "properties": {}},
        "tsinghua": {"name": "Tsinghua University", "label": "Organization", "properties": {}},
    }
    part_of = [
        {"child": "c1", "parent": "sc", "parent_classes": ["cabinet", "executive branch", "state level institution"], "ministry": False, "ministry_by_class_label": False},
        {"child": "c2", "parent": "cas", "parent_classes": ["academy of sciences", "academic institution"], "ministry": False, "ministry_by_class_label": False},
        {"child": "c3", "parent": "tsinghua", "parent_classes": ["higher education institution directly under Ministry of Education of the People's Republic of China", "public university"], "ministry": False, "ministry_by_class_label": True},
    ]
    inputs = SimpleNamespace(part_of=part_of, nodes=nodes, org_papers={"c1": {"p1"}, "c2": {"p2"}, "c3": {"p3"}}, notable_orgs=set())
    r = communities.rollup(inputs, cfg_v2)
    parents = {row["parent"]: row for row in r["parents"]}
    assert "sc" not in parents
    assert "cas" in parents and "tsinghua" in parents
    assert [e["parent"] for e in r["excluded_parents"]] == ["sc"]


def test_phase0_org_anchored_communities_and_display_aliases():
    cfg_v2 = yaml.safe_load((Path(__file__).parents[1] / "configs" / "analysis-final-exam-v2.yaml").read_text())
    # Two communities anchored to the same org (one >100 members -> large), with different top topics
    ids = [f"r{i}" for i in range(115)]
    membership = [0] * 105 + [1] * 10
    nodes = {"org1": {"name": "Korea University"}}
    researcher_orgs = {f"r{i}": {"org1": 1} for i in range(115)}
    labels = {
        0: {"Topic": [{"name": "Computer vision"}]},
        1: {"Topic": [{"name": "Natural language processing"}]},
    }
    inputs = SimpleNamespace(nodes=nodes, researcher_orgs=researcher_orgs, notable_orgs={"org1"})
    rows = communities.organization_anchored_communities(inputs, ids, membership, cfg_v2, labels=labels)
    assert len(rows) == 2
    assert rows[0]["size_tier"] == "large" and rows[1]["size_tier"] == "standard"
    assert rows[0]["display_name"] == "Korea University — Computer vision"
    assert rows[1]["display_name"] == "Korea University — Natural language processing"

    alias_inputs = SimpleNamespace(
        nodes={
            "task:1": {"name": "node classification"},
            "task:2": {"name": "node classification tasks"},
            "method:1": {"name": "Large Language Models (LLMs)"},
            "method:2": {"name": "large language model"},
        },
        subject_papers={
            "Task": {"task:1": {"p1", "p2"}, "task:2": {"p3"}},
            "Method": {"method:1": {"p4", "p5"}, "method:2": {"p6"}},
        },
    )
    aliases = trends.build_display_aliases(alias_inputs)
    assert aliases["group_count"] == 2
    task_aliases = aliases["by_kind"]["Task"][0]["aliases"]
    assert set(task_aliases) == {"node classification", "node classification tasks"}
