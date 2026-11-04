"""Report safety and evidence mappings, using invented data only."""
import json
from pathlib import Path

import pytest
import yaml

from scientific_network.collect.storage import digest
from scientific_network.contracts import GraphArtifact
from scientific_network.graph.validate import graph_counts
from scientific_network.reporting.html import render_report, report_payload

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def inputs(tmp_path, graph_payload):
    # Invented malicious display text and private/unapproved properties must stay inert.
    graph_payload['nodes'][0]['name'] = '</script><script>alert("fixture")</script>'
    graph_payload['nodes'][0]['properties']['private_note'] = 'NEVER_EXPORT_THIS'
    paper = next(n for n in graph_payload['nodes'] if n['label'] == 'Paper')
    paper['properties']['abstract'] = 'NEVER_EXPORT_ABSTRACT'
    graph = tmp_path / 'graph.json'
    graph.write_text(json.dumps(graph_payload))
    quality = tmp_path / 'quality.yaml'
    quality.write_bytes((ROOT / 'configs/quality.yaml').read_bytes())
    scope = tmp_path / 'scope.yaml'
    venues = [n for n in graph_payload['nodes'] if n['label'] == 'Venue']
    scope.write_text(yaml.safe_dump({'editions': [{'venue_id': n['id'], 'name': n['name']} for n in venues]}))
    metrics = tmp_path / 'metrics.json'
    # All counts here describe the synthetic fixture, never a project outcome.
    metrics.write_text(json.dumps({
        'versions': {k: {'sha256': digest(p.read_bytes())} for k, p in
                     [('graph', graph), ('quality_config', quality), ('corpus_config', scope)]},
        'graph_version': graph_payload['graph_version'],
        'counts': graph_counts(GraphArtifact.model_validate(graph_payload)),
        'by_venue': [{'venue_id': n['id'], 'status': 'collected', 'included_roster': 3,
                      'excluded_roster': 0} for n in venues],
        'recorded_at': '2026-11-03T00:00:00+07:00', 'scope': {}, 'splits': {},
        'collection': {}, 'coverage': {}, 'unresolved_sources': [],
        'verification': {}, 'methods': {'fixture': 'invented'}, 'classifier_method': 'synthetic',
        'extraction': {'by_status': {}, 'papers_with_header_affiliations': 0},
    }))
    return graph, metrics, quality, scope


def test_standalone_export_escapes_untrusted_names_and_omits_abstracts(inputs, tmp_path):
    out = tmp_path / 'report.html'
    result = render_report(*inputs, out)
    html = out.read_text()
    assert result['standalone'] and result['semantic_accuracy'] == 'not_measured_by_this_report'
    assert '</script><script>alert' not in html
    assert 'NEVER_EXPORT_THIS' not in html and 'NEVER_EXPORT_ABSTRACT' not in html
    embedded = html.split('<script id="report-data" type="application/json">')[1].split('</script>')[0]
    data = json.loads(embedded)
    assert data['is_synthetic'] is True
    assert data['nodes'][0]['properties'].get('private_note') is None
    assert any(n['name'].startswith('</script>') for n in data['nodes'])
    assert '@font-face' in html and 'data:font/ttf;base64,' in html
    assert '<script src=' not in html and '<link rel="stylesheet"' not in html
    assert 'SIL OPEN FONT LICENSE' in html


@pytest.mark.parametrize('target', [0, 2, 3])
def test_mismatched_graph_or_configs_fail_before_output(inputs, tmp_path, target):
    inputs[target].write_bytes(inputs[target].read_bytes() + b'\n')
    with pytest.raises(ValueError, match='does not match'):
        render_report(*inputs, tmp_path / 'not-written.html')
    assert not (tmp_path / 'not-written.html').exists()


def test_metrics_counts_cannot_be_silently_reused(inputs):
    data = json.loads(inputs[1].read_text())
    data['counts']['unique_core_factual_edges'] += 1
    inputs[1].write_text(json.dumps(data))
    with pytest.raises(ValueError, match='version/counts differ'):
        report_payload(*inputs)


def test_existing_outputs_and_symlinks_are_preserved(inputs, tmp_path):
    out = tmp_path / 'existing.html'
    out.write_text('existing user report')
    symlink = tmp_path / 'link.html'
    symlink.symlink_to(out)
    dangling = tmp_path / 'dangling.html'
    dangling.symlink_to(tmp_path / 'missing')
    for p in [out, symlink, dangling, inputs[0]]:
        with pytest.raises(ValueError, match='new HTML output path'):
            render_report(*inputs, p)
    assert out.read_text() == 'existing user report'


def test_affiliation_and_derived_support_keep_exact_papers(inputs):
    payload = report_payload(*inputs)
    original = json.loads(inputs[0].read_text())
    for edge in payload['edges']:
        if edge['relation'] == 'AFFILIATED_WITH':
            expected = {t['paper_id'] for t in original['affiliation_observations']
                        if (t['researcher_id'], t['organization_id']) == (edge['source_id'], edge['target_id'])}
            assert set(edge['support_papers']) == expected
        if edge['evidence_kind'] == 'derived':
            expected = {p for eid in edge['evidence_ids'] for p in payload['evidence'][eid]['support_paper_ids']}
            assert set(edge['support_papers']) == expected
    assert set(payload['layouts']['coauthors']) == {n['id'] for n in payload['nodes'] if n['label'] == 'Researcher'}
    assert sum(t['papers'] for t in payload['topics']) == sum(e['relation'] == 'HAS_TOPIC' for e in payload['edges'])


def test_unavailable_rosters_are_unknown_not_measured_zeros(inputs):
    data = json.loads(inputs[1].read_text())
    data['by_venue'][0]['status'] = 'unresolved_source'
    data['by_venue'][0]['included_roster'] = 0
    inputs[1].write_text(json.dumps(data))
    row = report_payload(*inputs)['by_venue'][0]
    assert row['included_roster'] is None and row['excluded_roster'] is None
