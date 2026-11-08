import json
from pathlib import Path

from scientific_network.analysis.figures import generate_report_figures
from scientific_network.analysis.release_metrics import compute_release_metrics
from scientific_network.contracts import GraphArtifact
import yaml


ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_GRAPH = ROOT / "tests/fixtures/synthetic_graph.json"
ANALYSIS_CONFIG = ROOT / "configs/analysis.yaml"


def _fixture_metrics():
    graph = GraphArtifact.model_validate_json(SYNTHETIC_GRAPH.read_bytes())
    for node in graph.nodes:
        if node.id == "paper:p3":
            node.properties["year"] = 2024
    projections = {
        "researcher_collaboration": {
            "top_betweenness": [{"node_id": "researcher:a", "score": 0.5}],
            "weak_or_undirected_component_sizes": [3, 2],
            "communities": [{
                "algorithm": "louvain_networkx",
                "seed": 17,
                "resolution": 0.8,
                "communities": [[
                    "researcher:a", "researcher:b", "researcher:c", "researcher:d", "researcher:e",
                ]],
            }],
        },
        "core_citations": {"centrality_scores": {"pagerank": {"paper:p1": 0.8}}},
    }
    config = yaml.safe_load(ANALYSIS_CONFIG.read_text(encoding="utf-8"))
    return compute_release_metrics(graph, projections, config)


def test_release_metrics_use_core_support_and_fractional_topics():
    metrics = _fixture_metrics()
    by_year = {row["year"]: row for row in metrics["annual_counts"]["rows"]}
    assert by_year[2023] == {
        "year": 2023,
        "paper_count": 2,
        "active_researcher_count": 3,
        "new_collaboration_pair_count": 2,
    }
    assert by_year[2024] == {
        "year": 2024,
        "paper_count": 1,
        "active_researcher_count": 2,
        "new_collaboration_pair_count": 1,
    }

    sectors = metrics["sector_mixing"]
    cell = next(row for row in sectors["matrix"] if row["row_sector"] == "academia" and row["column_sector"] == "industry")
    assert cell["pair_paper_support_count"] == 2
    unknown_country_pair = metrics["country_pair_collaborations"]["rows"][0]
    assert (unknown_country_pair["country_a"], unknown_country_pair["country_b"]) == ("UNKNOWN", "UNKNOWN")
    assert unknown_country_pair["pair_paper_support_count"] == 3

    topic = metrics["topic_shares_by_year_venue"]["rows"]
    topic_2023 = next(row for row in topic if row["year"] == 2023)
    assert topic_2023["paper_count"] == 2
    assert topic_2023["fractional_paper_count"] == 2.0
    assert topic_2023["share_of_fractional_topic_mass"] == 1.0

    assert metrics["cited_papers"]["top_by_in_degree"][0]["paper_id"] == "paper:p1"
    assert metrics["cited_papers"]["top_by_in_degree"][0]["in_degree"] == 2
    assert metrics["bridge_researchers"]["top_researchers"][0]["researcher"] == "Invented Researcher A"
    assert metrics["bridge_researchers"]["top_researchers"][0]["community_top_topics"][0]["paper_count"] == 3
    assert metrics["organization_topic_profiles"][0]["supported_paper_count"] == 3
    assert metrics["organization_topic_profiles"][0]["fractional_topic_portfolio_share"] == 1.0


def test_country_pair_mixing_keeps_unknown_and_is_symmetric():
    graph = GraphArtifact.model_validate_json(SYNTHETIC_GRAPH.read_bytes())
    nodes = {node.id: node for node in graph.nodes}
    nodes["organization:x"].properties["country_code"] = "US"
    nodes["organization:y"].properties["country_code"] = "CN"
    projections = {
        "researcher_collaboration": {"top_betweenness": [], "weak_or_undirected_component_sizes": [], "communities": []},
        "core_citations": {"centrality_scores": {"pagerank": {}}},
    }
    config = yaml.safe_load(ANALYSIS_CONFIG.read_text(encoding="utf-8"))
    metrics = compute_release_metrics(graph, projections, config)
    rows = metrics["country_pair_collaborations"]["rows"]
    counts = {(row["country_a"], row["country_b"]): row["pair_paper_support_count"] for row in rows}
    assert counts[("CN", "US")] == counts[("US", "CN")] == 2
    assert counts[("US", "UNKNOWN")] == counts[("UNKNOWN", "US")] == 1


def test_figures_write_six_png_csv_pairs_and_versioned_captions(tmp_path, monkeypatch):
    analysis = {
        "is_synthetic": False,
        "graph_version": "release-test",
        "release_metrics": {
            "researcher_degree_ccdf": {"rows": [
                {"degree": 0, "researcher_count_at_least": 3, "fraction_at_least": 1.0},
                {"degree": 1, "researcher_count_at_least": 2, "fraction_at_least": 2 / 3},
            ]},
            "researcher_component_sizes": {"sizes_descending": [2, 1]},
            "bridge_researchers": {
                "community_topic_partition": {"seed": 17, "resolution": 0.8},
                "community_topic_profiles_top_20_by_size": [{
                    "community_id": "community:00000", "member_count": 2, "paper_count": 2,
                    "topic_labeled_paper_count": 2,
                    "top_topics": [{
                        "topic_id": "topic:test", "topic": "Test topic", "paper_count": 2,
                        "fractional_paper_count": 2.0, "share_of_fractional_topic_mass": 1.0,
                    }],
                }],
            },
            "sector_mixing": {
                "categories": ["academia", "industry", "government", "nonprofit", "unknown"],
                "matrix": [
                    {"row_sector": row, "column_sector": col, "pair_paper_support_count": int(row == "academia" and col == "industry")}
                    for row in ("academia", "industry", "government", "nonprofit", "unknown")
                    for col in ("academia", "industry", "government", "nonprofit", "unknown")
                ],
            },
            "topic_shares_by_year_venue": {"rows": [{
                "year": 2021, "venue_id": "venue:test", "topic_id": "topic:test", "topic": "Test topic",
                "fractional_paper_count": 1.0, "labeled_paper_count": 1,
            }]},
            "cited_papers": {"top_by_in_degree": [{
                "paper_id": "paper:test", "title": "Test cited paper", "year": 2021,
                "venue": "Test", "doi": None, "official_url": "https://example.org/paper",
                "openalex_id": None, "in_degree": 1, "pagerank": 0.5,
            }]},
        },
    }
    # A topic outside a community's stored top five is unknown in this artifact,
    # and must not be plotted as a measured zero.
    analysis['release_metrics']['bridge_researchers']['community_topic_profiles_top_20_by_size'].append({
        'community_id': 'community:00001', 'member_count': 1, 'paper_count': 1,
        'topic_labeled_paper_count': 1,
        'top_topics': [{'topic_id': 'topic:other', 'topic': 'Other topic', 'paper_count': 1,
                        'fractional_paper_count': 1.0, 'share_of_fractional_topic_mass': 1.0}],
    })
    import matplotlib.axes
    import numpy as np
    original_imshow = matplotlib.axes.Axes.imshow
    captured = []
    def observe(axis, matrix, *args, **kwargs):
        captured.append(np.asarray(matrix, dtype=float))
        return original_imshow(axis, matrix, *args, **kwargs)
    monkeypatch.setattr(matplotlib.axes.Axes, 'imshow', observe)
    analysis_path = tmp_path / "analysis.json"
    analysis_path.write_text(json.dumps(analysis), encoding="utf-8")
    output_dir = tmp_path / "figures"
    paths = generate_report_figures(analysis_path, output_dir)

    community_matrix = next(matrix for matrix in captured if matrix.shape == (2, 2))
    assert np.isnan(community_matrix).sum() == 2
    assert (community_matrix == 0).sum() == 0
    assert len(paths) == 13
    for path in paths:
        assert path.is_file()
    assert (output_dir / "researcher-degree-ccdf.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert "release-test" in (output_dir / "captions.md").read_text(encoding="utf-8")
    assert "grey means outside that stored profile, not zero support" in (output_dir / "captions.md").read_text()
    try:
        generate_report_figures(analysis_path, output_dir)
    except ValueError as exc:
        assert "already exist" in str(exc)
    else:
        raise AssertionError("figure generation must not overwrite existing artifacts")


def test_fractional_metric_outputs_are_stable_across_python_hash_seeds():
    """Exact sums must not change ties or rounded denominators across set orders."""
    import os
    import subprocess
    import sys
    script = '''
import sys,json
sys.path.insert(0,'tests')
from test_analysis_release_metrics import _tie_fixture_metrics
print(json.dumps(_tie_fixture_metrics(),sort_keys=True))
'''
    outputs = []
    for seed in (1, 17, 101):
        result = subprocess.run([sys.executable, '-c', script], cwd=ROOT,
                                env={**os.environ, 'PYTHONHASHSEED': str(seed)},
                                check=True, capture_output=True)
        outputs.append(result.stdout)
    assert outputs[0] == outputs[1] == outputs[2]


def _tie_fixture_metrics():
    from scientific_network.contracts import Node, Edge
    nodes = [Node(id='researcher:tie', label='Researcher', name='Invented researcher')]
    topic_ids = [f'topic:fill{i}' for i in range(4)] + ['topic:a', 'topic:b']
    nodes += [Node(id=t, label='Topic', name=t) for t in topic_ids]
    edges = []
    labels = ([['topic:a', 'topic:fill0', 'topic:fill1']] * 6
              + [['topic:b', 'topic:fill2']] * 4
              + [[f'topic:fill{i}'] for i in range(4) for _ in range(10)])
    for index, topics in enumerate(labels):
        paper = f'paper:invented:{index}'
        nodes.append(Node(id=paper, label='Paper', name=paper, properties={'is_core': True, 'year': 2025}))
        for relation, source, target, kind in [('AUTHORED', 'researcher:tie', paper, 'observed')]+[
            ('HAS_TOPIC', paper, topic, 'inferred_topic') for topic in topics
        ]:
            edges.append(Edge(edge_id=f'edge:{len(edges)}', relation=relation, source_id=source,
                              target_id=target, evidence_kind=kind, evidence_ids=['evidence:invented'],
                              method_version='synthetic', graph_version='synthetic-tie', validation_status='accepted'))
    graph = GraphArtifact(graph_version='synthetic-tie', is_synthetic=True, nodes=nodes, edges=edges, evidence=[])
    projections = {'researcher_collaboration': {'top_betweenness': [], 'weak_or_undirected_component_sizes': [],
                    'communities': [{'algorithm': 'louvain_networkx', 'seed': 17, 'resolution': 0.8,
                                     'communities': [['researcher:tie']]}]},
                   'core_citations': {'centrality_scores': {'pagerank': {}}}}
    config = yaml.safe_load(ANALYSIS_CONFIG.read_text())
    return compute_release_metrics(graph, projections, config)


def test_exact_fractional_topic_ties_use_topic_id_instead_of_float_roundoff():
    metrics = _tie_fixture_metrics()
    top = metrics['bridge_researchers']['community_topic_profiles_top_20_by_size'][0]['top_topics']
    assert len(top) == 5
    assert top[-1]['topic_id'] == 'topic:a'   # six thirds and four halves are exactly equal
    assert top[-1]['fractional_paper_count'] == 2.0
