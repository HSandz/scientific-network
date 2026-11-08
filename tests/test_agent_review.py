"""Invented fixtures exercise binding refusal and preserve legacy scoring semantics."""

import csv
from hashlib import sha256
import json
from pathlib import Path

import pytest
import yaml

from scientific_network.evaluation.agent_review import AI_METADATA, score_agent_review
from scientific_network.evaluation.edge_audit import SPLIT_FIELDS, prepare_edge_audit_sample
from scientific_network.evaluation.topic_review import FIELDS, prepare_topic_review_packets

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value))
    return path


def write_csv(path, rows, fields):
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_jsonl(path, rows):
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    return path


@pytest.fixture
def agent_package(tmp_path):
    papers = [{'paper_id': f'paper:invented:{i}', 'venue_id': 'venue:aaai' if i < 20 else 'venue:ijcai'} for i in range(50)]
    topic_test = write_jsonl(tmp_path / 'test.jsonl', [{**p, 'seed': 20261108} for p in papers])
    catalog = [{'id': f'topic:invented:{i}', 'name': f'Invented {i}', 'definition': 'Invented definition'} for i in range(16)]
    taxonomy = tmp_path / 'taxonomy.yaml'
    taxonomy.write_text(yaml.safe_dump({'status': 'frozen', 'calibration': {'topic_test_sha256': digest(topic_test)}, 'leaves': catalog}))
    rows = [{**p, 'year': '2025', 'title': 'Invented title', 'abstract': 'Invented abstract',
             'topic_catalog': json.dumps(catalog, ensure_ascii=False, separators=(',', ':')),
             'label_1': '', 'label_2': '', 'label_3': '', 'labeler': '', 'notes': ''} for p in papers]
    master = write_csv(tmp_path / 'master.csv', rows, FIELDS)
    packets = tmp_path / 'packets'
    prepare_topic_review_packets(master, topic_test, taxonomy, packets)
    allocation = packets / 'topic-review-allocation.json'
    allocation_doc = json.loads(allocation.read_text())
    graph_doc = json.loads((ROOT / 'tests/fixtures/synthetic_graph.json').read_text())
    graph_doc['nodes'].extend({'id': p['paper_id'], 'label': 'Paper', 'name': 'Invented paper',
        'properties': {'is_core': False, 'year': 2025, 'official_url': 'https://example.invalid', 'track': 'main'}} for p in papers)
    graph = write_json(tmp_path / 'graph.json', graph_doc)
    graph_v1 = write_json(tmp_path / 'baseline.json', graph_doc)
    graph_summary = write_json(tmp_path / 'summary.json', {
        'graph_v1_version': graph_doc['graph_version'], 'graph_version': graph_doc['graph_version'],
        'graph_sha256': digest(graph), 'inputs_sha256': {'graph_v1_sha256': digest(graph_v1)}})
    graph_freeze = write_json(tmp_path / 'graph-freeze.json', {
        'graph_version': graph_doc['graph_version'], 'graph_sha256': digest(graph),
        'topic_test_manifest_sha256': digest(topic_test), 'taxonomy_config': {'sha256': digest(taxonomy)},
        'review_packet': {'topic_review_assignment': {'allocation_manifest': {'sha256': digest(allocation)},
            'reviewer_sheets': allocation_doc['reviewer_sheets']}}})
    quality = tmp_path / 'quality.yaml'
    quality_doc = yaml.safe_load((ROOT / 'configs/quality-release-v1.yaml').read_text())
    quality_doc['audit'].update(global_sample_size=10, per_type_sample_size=2, overlap_sample_size=4)
    quality.write_text(yaml.safe_dump(quality_doc))
    blank = tmp_path / 'edges.csv'
    prepare_edge_audit_sample(graph, quality, blank)
    with blank.open(newline='') as stream:
        edge_rows = list(csv.DictReader(stream))
    for row in edge_rows:
        row.update(decision='correct', reason='Invented supported finding', reviewed_at='2026-11-09T02:00:00+07:00')
    edge_reviews = [write_csv(tmp_path / 'completed-edges.csv', edge_rows, SPLIT_FIELDS)]
    source = tmp_path / 'source.json'
    source.write_text('{"invented": true}')
    def ledger(unit, reviewer, kind):
        return {'unit_id': unit, 'reviewer_id': reviewer, 'reviewer_kind': 'ai_agent',
            'evaluator_run_id': f'run-{reviewer}', 'decision': 'reviewed' if kind == 'topic' else 'correct',
            'reason': 'Invented supported finding', 'source_url': 'https://example.invalid/invented',
            'source_locator': str(source) + '#invented', 'source_sha256': digest(source),
            'evidence_depth': 'secondary_source_only', 'source_independence': 'same_source_as_construction',
            'reviewed_at': '2026-11-09T01:00:00+07:00' if kind == 'topic' else '2026-11-09T02:00:00+07:00'}
    topic_rows = []
    topic_reviews = {}
    for reviewer in ('A', 'B'):
        with (packets / f'topic-label-sheet-reviewer-{reviewer}.csv').open(newline='', encoding='utf-8-sig') as stream:
            answered = list(csv.DictReader(stream))
        for row in answered:
            row.update(label_1='topic:invented:0', notes='Invented supported finding')
            topic_rows.append(ledger(row['paper_id'], reviewer, 'topic'))
        topic_reviews[reviewer] = write_csv(tmp_path / f'topics-{reviewer}.csv', answered, FIELDS)
    topic_ledger = write_jsonl(tmp_path / 'topics.jsonl', topic_rows)
    edge_ledger = write_jsonl(tmp_path / 'edges.jsonl', [ledger(row['edge_id'], row['reviewer_id'], 'edge') for row in edge_rows])
    protocol = tmp_path / 'protocol.yaml'
    protocol.write_text(yaml.safe_dump(AI_METADATA))
    static = [protocol, graph, quality, graph_v1, topic_test, taxonomy, allocation, master, graph_freeze, graph_summary]
    evaluation_freeze = write_json(tmp_path / 'evaluation-freeze.json', {
        **AI_METADATA,
        'review_design': 'isolated_agent_A_B', 'created_at': '2026-11-09T00:00:00+07:00',
        'input_files': [{'path': str(p), 'sha256': digest(p)} for p in static],
        'evaluator_runs': [{'reviewer_id': r, 'reviewer_kind': 'ai_agent', 'evaluator_run_id': f'run-{r}',
            'context_id': f'context-{r}', 'model': 'unknown', 'provider': 'unknown',
            'started_at': '2026-11-09T00:10:00+07:00'} for r in ('A', 'B')],
        'assignments': {'topics': allocation_doc['reviewer_paper_ids'], 'edges': {
            r: [row['edge_id'] for row in edge_rows if row['reviewer_id'] == r] for r in ('A', 'B')}}})
    completed = [topic_ledger, edge_ledger, *topic_reviews.values(), *edge_reviews]
    completion_receipt = write_json(tmp_path / 'completion.json', {
        'evaluation_freeze_sha256': digest(evaluation_freeze), 'topic_completed_at': '2026-11-09T01:10:00+07:00',
        'edge_started_at': '2026-11-09T01:20:00+07:00',
        'output_files': [{'path': str(p), 'sha256': digest(p)} for p in completed]})
    return dict(evaluation_freeze=evaluation_freeze, completion_receipt=completion_receipt,
        protocol=protocol, topic_ledger=topic_ledger, edge_ledger=edge_ledger, graph=graph, quality=quality,
        graph_v1=graph_v1, topic_test=topic_test, taxonomy=taxonomy, allocation=allocation, master_sheet=master,
        topic_reviewer_a=topic_reviews['A'], topic_reviewer_b=topic_reviews['B'], graph_freeze=graph_freeze,
        graph_summary=graph_summary, edge_reviews=edge_reviews,
        edge_output=tmp_path / 'edge-result.json', topic_output=tmp_path / 'topic-result.json')


def rebind(package):
    freeze = json.loads(package['evaluation_freeze'].read_text())
    for item in freeze['input_files']:
        item['sha256'] = digest(Path(item['path']))
    write_json(package['evaluation_freeze'], freeze)
    receipt = json.loads(package['completion_receipt'].read_text())
    receipt['evaluation_freeze_sha256'] = digest(package['evaluation_freeze'])
    for item in receipt['output_files']:
        item['sha256'] = digest(Path(item['path']))
    write_json(package['completion_receipt'], receipt)


def test_agent_scoring_validates_before_creating_truthfully_scoped_results(agent_package):
    summary, code = score_agent_review(**agent_package)
    assert code == 0  # Synthetic graph remains explicitly synthetic through the legacy scorer.
    assert summary['evaluation_kind'] == 'ai_agent_review'
    edges = json.loads(agent_package['edge_output'].read_text())
    topics = json.loads(agent_package['topic_output'].read_text())
    for result in (edges, topics):
        assert {k: result[k] for k in AI_METADATA} == AI_METADATA
        assert result['source_independence_counts']['same_source_as_construction'] > 0
    assert edges['status'] == 'synthetic_protocol_only'
    assert edges['global']['correct'] == edges['global']['total'] == 10
    assert topics['weighting']['effective_paper_weight'] == 50
    assert topics['annotation_judgment_count'] == 60
    assert topics['reviewer_agreement_on_overlap']['overlap_paper_count'] == 10


@pytest.mark.parametrize('mutation,match', [
    ('shared_context', 'share an evaluator context'), ('duplicate_run', 'distinct actual IDs'),
    ('missing_model', 'metadata is incomplete'), ('late_freeze', 'freeze must precede'),
    ('wrong_assignment', 'edge assignments differ'), ('wrong_receipt', 'does not bind the evaluation freeze'),
    ('changed_static', 'hash mismatch'), ('changed_export', 'hash mismatch'),
    ('edge_before_topics', 'topic completion must precede'), ('wrong_join', 'unassigned reviewer/unit'),
    ('wrong_run', 'run does not match'), ('internal_correct', 'unreviewable/unverifiable'),
    ('empty_reason', 'nonempty rationale'), ('source_hash', 'local source hash mismatch'),
    ('csv_decision', 'decision differs'), ('topic_labels', 'labels differ'),
    ('missing_edge', 'every frozen reviewer assignment'),
])
def test_agent_scoring_refuses_invalid_provenance_without_outputs(agent_package, mutation, match):
    p = agent_package
    freeze = json.loads(p['evaluation_freeze'].read_text())
    receipt = json.loads(p['completion_receipt'].read_text())
    edges = [json.loads(line) for line in p['edge_ledger'].read_text().splitlines()]
    topics = [json.loads(line) for line in p['topic_ledger'].read_text().splitlines()]
    if mutation == 'shared_context': freeze['evaluator_runs'][1]['context_id'] = 'context-A'
    elif mutation == 'duplicate_run': freeze['evaluator_runs'][1]['evaluator_run_id'] = 'run-A'
    elif mutation == 'missing_model': del freeze['evaluator_runs'][0]['model']
    elif mutation == 'late_freeze': freeze['created_at'] = '2026-11-09T00:30:00+07:00'
    elif mutation == 'wrong_assignment': freeze['assignments']['edges']['A'].append('edge:invented-unknown')
    elif mutation == 'edge_before_topics': receipt['edge_started_at'] = '2026-11-09T00:30:00+07:00'
    elif mutation == 'wrong_join': edges[0]['unit_id'] = 'edge:unassigned'
    elif mutation == 'wrong_run': edges[0]['evaluator_run_id'] = 'not-a-real-run'
    elif mutation == 'internal_correct': edges[0]['evidence_depth'] = 'internal_only'
    elif mutation == 'empty_reason': edges[0]['reason'] = ''
    elif mutation == 'source_hash': edges[0]['source_sha256'] = '0' * 64
    elif mutation == 'csv_decision': edges[0]['decision'] = 'incorrect'
    elif mutation == 'topic_labels': topics[0]['labels'] = ['topic:invented:1']
    elif mutation == 'missing_edge': edges.pop()
    write_json(p['evaluation_freeze'], freeze)
    write_json(p['completion_receipt'], receipt)
    write_jsonl(p['edge_ledger'], edges)
    write_jsonl(p['topic_ledger'], topics)
    rebind(p)
    if mutation == 'wrong_receipt':
        receipt = json.loads(p['completion_receipt'].read_text())
        receipt['evaluation_freeze_sha256'] = '0' * 64
        write_json(p['completion_receipt'], receipt)
    elif mutation == 'changed_static': p['graph_summary'].write_text('{}')
    elif mutation == 'changed_export': p['topic_reviewer_a'].write_text('changed')
    with pytest.raises(ValueError, match=match):
        score_agent_review(**p)
    assert not p['edge_output'].exists()
    assert not p['topic_output'].exists()


def test_unreviewable_topic_is_missing_reference_and_retains_planned_overlap_weight(agent_package):
    p = agent_package
    ledger = [json.loads(line) for line in p['topic_ledger'].read_text().splitlines()]
    shared = set(json.loads(p['evaluation_freeze'].read_text())['assignments']['topics']['A']) & set(json.loads(p['evaluation_freeze'].read_text())['assignments']['topics']['B'])
    unit = sorted(shared)[0]
    entry = next(row for row in ledger if row['unit_id'] == unit and row['reviewer_id'] == 'A')
    entry.update(decision='unreviewable', evidence_depth='unavailable', reason='Invented unavailable source')
    write_jsonl(p['topic_ledger'], ledger)
    with p['topic_reviewer_a'].open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        if row['paper_id'] == unit: row.update(label_1='', notes='Unreviewable source')
    write_csv(p['topic_reviewer_a'], rows, FIELDS)
    rebind(p)
    with pytest.raises(ValueError, match='partial scoring opt-in'):
        score_agent_review(**p)
    score_agent_review(**p, allow_partial=True)
    result = json.loads(p['topic_output'].read_text())
    assert result['completion']['unreviewable_assignments'] == 1
    assert result['annotation_judgment_count'] == 59
    assert result['weighting']['effective_paper_weight'] == 49.5
    assert result['reviewer_agreement_on_overlap']['overlap_paper_count'] == 9
    assert result['models']['phrase_baseline']['paper_normalized_review_metrics']['micro']['false_negative'] == 49.5
