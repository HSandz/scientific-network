"""Invented units test diagnostic estimands and review integrity, never accuracy."""
import pytest
from scientific_network.contracts import Relation
from scientific_network.evaluation.review_sheet import CORRECT_WHEN, render_html
from scientific_network.quality.sprint_audit import (
    draw, human_selection, human_subset, summarize, update_sampling_manifest,
)


def edge(i, relation='AUTHORED', status='accepted'):
    return {'edge_id': str(i), 'relation': relation, 'validation_status': status}


def test_draw_is_order_invariant_and_records_small_stratum_census():
    frame = [edge(i) for i in range(30)] + [edge('t', 'SUBTOPIC_OF'), edge('x', status='review')]
    sample, strata = draw(frame)
    assert draw(list(reversed(frame))) == (sample, strata)
    assert strata['AUTHORED']['inclusion_probability'] == 8 / 30
    assert strata['SUBTOPIC_OF'] == {'population': 1, 'sample': 1, 'inclusion_probability': 1, 'census': True}
    assert 'x' not in {r['edge_id'] for r in sample}
    with pytest.raises(ValueError, match='duplicate'):
        draw([edge(1), edge(1)])


def test_human_random_is_separate_from_diagnostic_risk_selection():
    sample = [edge(i, 'HAS_TOPIC') for i in range(80)]
    random, risk = human_subset(sample)
    assert len(random) == 20 and len(risk) == 6 and not set(random) & set(risk)
    assert human_subset(list(reversed(sample))) == (random, risk)


def test_flagged_diagnostics_are_additive_and_keep_overlapping_selection_tags():
    sample = [edge(i, 'HAS_TOPIC') for i in range(80)]
    random_ids, risk_ids = human_subset(sample)
    remaining = next(row['edge_id'] for row in sample
                     if row['edge_id'] not in set(random_ids) | set(risk_ids))
    flagged = [random_ids[0], risk_ids[0], remaining]
    selection = human_selection(sample, flagged)

    assert selection['random_ids'] == random_ids
    assert selection['diagnostic_ids'] == risk_ids
    assert selection['flagged_diagnostic_ids'] == flagged
    assert len(selection['unique_review_ids']) == 27
    assert len(selection['unique_review_ids']) == len(set(selection['unique_review_ids']))
    assert selection['selection_tags'][random_ids[0]] == ['random', 'flagged_diagnostic']
    assert selection['selection_tags'][risk_ids[0]] == ['risk_diagnostic', 'flagged_diagnostic']
    assert selection['probability_sample_ids'] == random_ids
    assert set(selection['diagnostic_only_ids']).isdisjoint(random_ids)
    assert selection['selection_summary'] == {
        'random_total': 20, 'random_flagged_overlap': 1, 'risk_total': 6,
        'risk_flagged_overlap': 1, 'flagged_total': 3, 'unique_total': 27,
    }
    with pytest.raises(ValueError, match='outside the frozen sample'):
        human_selection(sample, ['not-in-frame'])
    with pytest.raises(ValueError, match='duplicate edge IDs'):
        human_selection(sample, [flagged[0], flagged[0]])


def test_human_packet_renderer_explains_selection_and_source_identity_limits():
    row = {
        'review': {'reviewer_id': 'member-1', 'edge_id': 'edge-x', 'decision': ''},
        'context': {'relation': 'AUTHORED', 'selection_tags': ['random', 'flagged_diagnostic']},
        'links': [],
    }
    page = render_html({
        'graph_version': 'v4', 'audit_id': 'packet-v2', 'reviewer_ids': ['member-1'],
        'selection_summary': {'random_total': 20, 'flagged_total': 4},
        'packet_note': 'Initial review only.',
    }, ['decision'], [row])
    assert 'Source consistency is not automatically independent semantic verification' in page
    assert 'Flagged diagnostic cases' in page and 'Prespecified random sample' in page
    assert 'selection_tags' in page and 'flagged_diagnostic' in page
    assert 'Initial review only.' in page
    assert '"decision":""' in page


@pytest.mark.parametrize('relation', [
    Relation.AUTHORED, Relation.COAUTHORED_WITH, Relation.AFFILIATED_WITH,
    Relation.COLLABORATED_WITH, Relation.RESEARCHES_TOPIC, Relation.CONTRIBUTES_TO_TOPIC,
])
def test_identity_dependent_rubric_distinguishes_source_consistency(relation):
    text = CORRECT_WHEN[relation]
    assert 'Source-consistent relationship:' in text
    assert 'Independently verified relationship:' in text
    assert 'identity' in text.lower()


def test_sampling_manifest_is_extended_without_changing_frozen_random_selection(tmp_path):
    packet_root = tmp_path / 'packet'
    packet_root.mkdir()
    allocation = {
        'random_ids': ['r1'], 'diagnostic_ids': ['d1'], 'random_conditional_probability': 0.25,
        'flagged_diagnostic_ids': ['r1', 'f1'], 'unique_review_ids': ['r1', 'd1', 'f1'],
        'selection_tags': {'r1': ['random', 'flagged_diagnostic'], 'd1': ['risk_diagnostic'], 'f1': ['flagged_diagnostic']},
        'probability_sample_ids': ['r1'], 'diagnostic_only_ids': ['d1', 'f1'],
        'reviewer_case_ids': {'member-1': ['r1', 'd1', 'f1'], 'member-2': ['r1', 'd1', 'f1']},
        'initial_answers': 'blank', 'reviewer_ids': ['member-1', 'member-2'],
    }
    frozen = {'human_random_ids': ['r1'], 'human_diagnostic_ids': ['d1'],
              'human_random_conditional_probability': 0.25, 'sample_sha256': 'frozen-sample-hash'}
    manifest_path = tmp_path / 'sampling-manifest.json'
    manifest_path.write_text(__import__('json').dumps(frozen))
    issues_path = tmp_path / 'issues.json'
    issues_path.write_text('[]')
    names = [f'human-{member}.{suffix}' for member in allocation['reviewer_ids'] for suffix in ('csv', 'html')]
    names += ['human-allocation.json'] + [f'human-{member}-flagged-post-blind.html' for member in allocation['reviewer_ids']]
    for name in names:
        (packet_root / name).write_text(name)

    updated = update_sampling_manifest(manifest_path, allocation, issues_path, packet_root, 'frozen-sample-hash')
    assert updated['human_random_ids'] == frozen['human_random_ids']
    assert updated['human_diagnostic_ids'] == frozen['human_diagnostic_ids']
    assert updated['human_random_conditional_probability'] == frozen['human_random_conditional_probability']
    assert updated['sample_sha256'] == frozen['sample_sha256']
    assert updated['human_packet_v2']['probability_sample_ids'] == ['r1']
    assert updated['human_packet_v2']['diagnostic_only_ids'] == ['d1', 'f1']
    assert updated['human_packet_v2']['packet_sha256'].keys() == set(names)
    with pytest.raises(ValueError, match='generated edge sample differs'):
        update_sampling_manifest(manifest_path, allocation, issues_path, packet_root, 'changed-sample-hash')


def test_unknowns_are_retained_and_review_joins_fail_closed():
    units = [edge(1)]
    review = {'edge_id': '1', 'relation': 'AUTHORED', 'decision': 'unknown',
              'reviewer_kind': 'ai', 'reviewer_model': 'gpt-6-luna', 'reasoning_effort': 'high',
              'reason': 'Invented missing source', 'evidence_ids': [], 'source_locators': []}
    result = summarize(units, [review])
    assert result['per_relation']['AUTHORED']['unknown'] == 1
    assert result['pooled_accuracy'] is None
    for rows in ([], [review, review], [{**review, 'relation': 'CITES'}],
                 [{**review, 'reviewer_kind': 'human'}], [{**review, 'decision': 'supported'}]):
        with pytest.raises(ValueError):
            summarize(units, rows)
