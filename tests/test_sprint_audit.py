"""Invented units test diagnostic estimands and review integrity, never accuracy."""
import pytest
from scientific_network.quality.sprint_audit import draw, human_subset, summarize


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
