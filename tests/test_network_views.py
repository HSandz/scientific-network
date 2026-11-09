"""The presentation must preserve accepted projection semantics and public boundaries."""
from copy import deepcopy
import json
from hashlib import sha256

import pytest

from scientific_network.reporting.network_views import VIEWS, generate_network_views, network_payload


def fixture_graph():
    nodes = []
    edges = []
    evidence = []
    projections = {}
    for key, (label, relation, projection, _) in VIEWS.items():
        for i in range(4):
            nodes.append({'id': f'{key}:{i}', 'label': label, 'name': f'Name {i}',
                          'properties': {'official_url': f'https://example.org/{key}/{i}',
                                         'abstract': 'PRIVATE TEXT', 'year': 2021+i, 'sector': 'academia'}})
        # One isolate is counted in the full projection, excluded from this view.
        for i, j in ((0, 1), (2, 1)):
            eid = f'{key}:{i}-{j}'
            edges.append({'edge_id': eid, 'source_id': f'{key}:{i}', 'target_id': f'{key}:{j}',
                          'relation': relation, 'properties': {'fractional_weight': .5, 'support_count': 1},
                          'validation_status': 'accepted', 'method_version': 'test', 'evidence_kind': 'derived',
                          'evidence_ids': [eid]})
            evidence.append({'id': eid, 'source_url': 'https://example.org/source', 'raw_sha256': 'abc',
                             'source_locator': 'references[1]', 'excerpt': 'PRIVATE TEXT',
                             'support_paper_ids': ['citations:0']})
        projections[projection] = {'node_count': 4, 'edge_count': 2, 'communities': []}
    graph = {'graph_version': 'test-v1', 'is_synthetic': True, 'nodes': nodes, 'edges': edges, 'evidence': evidence}
    analysis = {'graph_version': 'test-v1', 'input_sha256': 'hash', 'projections': projections}
    return graph, analysis


def test_views_are_induced_directional_bound_and_public():
    graph, analysis = fixture_graph()
    result = network_payload(graph, analysis, 'hash')
    assert result['is_synthetic'] is True
    assert 'PRIVATE TEXT' not in json.dumps(result)
    for key, view in result['views'].items():
        assert view['full_node_count'] == 4
        assert len(view['nodes']) == 3
        assert view['full_edge_count'] == len(view['edges']) == 2
        assert view['directed'] == (key == 'citations')
        assert {e['edge_id'] for e in view['edges']} == {e['edge_id'] for e in graph['edges'] if e['relation'] == view['relation']}
        assert all(e['fractional_weight'] == .5 for e in view['edges'])
    cited = next(n for n in result['views']['citations']['nodes'] if n['id'] == 'citations:1')
    assert cited['score'] == 2
    assert all(e['target'] == 'citations:1' for e in result['views']['citations']['edges'])
    assert result['views']['researchers']['edges'][0]['source_links'][0]['paper_id'] == 'citations:0'
    # Serialization order must not change selection or layout.
    for name in ('nodes', 'edges', 'evidence'):
        graph[name].reverse()
    assert network_payload(graph, analysis, 'hash') == result


def test_bounded_selection_keeps_only_induced_edges(monkeypatch):
    graph, analysis = fixture_graph()
    monkeypatch.setitem(VIEWS, 'citations', ('Paper', 'CITES', 'core_citations', 2))
    view = network_payload(graph, analysis, 'hash')['views']['citations']
    assert {n['id'] for n in view['nodes']} == {'citations:0', 'citations:1'}
    assert len(view['edges']) == 1
    assert view['full_edge_count'] == 2


def test_reject_stale_analysis_inventory_and_unaccepted_edges():
    graph, analysis = fixture_graph()
    with pytest.raises(ValueError, match='exact graph'):
        network_payload(graph, analysis, 'wrong')
    wrong = deepcopy(analysis)
    wrong['projections']['core_citations']['edge_count'] = 3
    with pytest.raises(ValueError, match='inventory'):
        network_payload(graph, wrong, 'hash')
    graph['edges'][0]['validation_status'] = 'ambiguous'
    with pytest.raises(ValueError, match='accepted'):
        network_payload(graph, analysis, 'hash')


def test_generation_refuses_stale_freeze_and_existing_output(tmp_path):
    graph, analysis = fixture_graph()
    gp, ap, fp = [tmp_path / n for n in ('graph.json', 'analysis.json', 'freeze.json')]
    gp.write_text(json.dumps(graph))
    analysis['input_sha256'] = sha256(gp.read_bytes()).hexdigest()
    ap.write_text(json.dumps(analysis))
    fp.write_text(json.dumps({'graph_sha256': 'wrong', 'graph_version': 'test-v1'}))
    output = tmp_path / 'output'
    with pytest.raises(ValueError, match='freeze'):
        generate_network_views(gp, ap, fp, output)
    assert not output.exists()
    output.mkdir()
    with pytest.raises(ValueError, match='unused'):
        generate_network_views(gp, ap, fp, output)
    output.rmdir()
    output.symlink_to(tmp_path / 'missing')
    with pytest.raises(ValueError, match='unused'):
        generate_network_views(gp, ap, fp, output)
