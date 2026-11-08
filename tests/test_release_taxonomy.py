"""Frozen taxonomy correction preserves all scientific predictions and support."""

from hashlib import sha256
import json
from pathlib import Path

import pytest
import yaml

from scientific_network.contracts import GraphArtifact
from scientific_network.resolve.release_taxonomy import (
    compare_correction, correct_release_taxonomy, synchronize_taxonomy, validate_taxonomy,
)
from scientific_network.resolve.release_topics import build_release_graph_v2
from test_release_graph import build, row, authorship

ROOT = Path(__file__).resolve().parents[1]
QUALITY = ROOT / 'configs/quality-release-v1.yaml'


def test_normal_builder_and_deterministic_correction_use_frozen_taxonomy(tmp_path, monkeypatch):
    rows = [row(n, ['Ann One'], [authorship('A1', 'Ann One')]) for n in range(50)]
    graph, _, _ = build(tmp_path, rows)
    base = tmp_path / 'graph/graph.json'
    works = tmp_path / 'works.jsonl'
    test = tmp_path / 'test.jsonl'
    test.write_text(''.join(json.dumps({'paper_id': r['paper_id']}) + '\n' for r in rows))
    taxonomy = yaml.safe_load((ROOT / 'configs/topics-release-v1.yaml').read_text())
    taxonomy['test_manifest'] = str(test)
    taxonomy['calibration'].update(
        topic_test_sha256=sha256(test.read_bytes()).hexdigest(),
        works_sha256=sha256(works.read_bytes()).hexdigest(),
    )
    config = tmp_path / 'frozen.yaml'
    config.write_text(yaml.safe_dump(taxonomy, allow_unicode=True))
    predictions = [{
        'paper_id': r['paper_id'], 'decision': 'labeled', 'text_source': 'abstract',
        'predictions': [{'topic_id': 'topic:graph-ml', 'similarity': 0.87654321,
                         'text_source': 'abstract', 'start': 0, 'end': 10, 'excerpt': 'A quoted “graph”, tên.\nEvidence.'}],
    } for r in rows]
    monkeypatch.setattr('scientific_network.resolve.release_topics.predict_topics', lambda *a, **k: predictions)
    built_summary = tmp_path / 'built-summary.json'
    build_release_graph_v2(base, works, config, QUALITY, tmp_path / 'built', built_summary, model=object())
    corrected_builder = GraphArtifact.model_validate_json((tmp_path / 'built/graph.json').read_bytes())
    assert validate_taxonomy(corrected_builder, config) == []
    node = next(n for n in corrected_builder.nodes if n.id == 'topic:graph-ml')
    assert node.properties['definition'] == next(t['definition'] for t in taxonomy['leaves'] if t['id'] == node.id)
    assert node.properties['taxonomy_version'] == 'taxonomy-release-v1'
    assert all(r.raw_sha256 == sha256(config.read_bytes()).hexdigest() and str(config) in r.source_locator
               for r in corrected_builder.evidence if r.kind == 'curated_taxonomy')
    # Reproduce the old defect without running inference again.
    stale = corrected_builder.model_copy(deep=True)
    for n in stale.nodes:
        if n.label == 'Topic':
            n.properties['taxonomy_version'] = 'taxonomy-v0.1'
            n.properties['definition'] = 'Old definition'
    assert validate_taxonomy(stale, config)
    source = tmp_path / 'stale.json'
    source.write_text(stale.model_dump_json() + '\n')
    doc = json.loads(built_summary.read_text())
    doc['graph_sha256'] = sha256(source.read_bytes()).hexdigest()
    source_summary = tmp_path / 'source-summary.json'
    source_summary.write_text(json.dumps(doc))
    freeze = tmp_path / 'freeze.json'
    freeze.write_text(json.dumps({'graph_version': stale.graph_version, 'graph_sha256': doc['graph_sha256'],
        'config_hashes': {str(p): sha256(p.read_bytes()).hexdigest() for p in (config, QUALITY)}}))
    hashes_before = {p: sha256(p.read_bytes()).hexdigest() for p in (source, source_summary, freeze, config)}
    # Correction must never call the classifier.
    monkeypatch.setattr('scientific_network.resolve.release_topics.predict_topics',
                        lambda *a, **k: pytest.fail('correction ran inference'))
    for suffix in ('one', 'two'):
        result = correct_release_taxonomy(source, config, QUALITY, source_summary, freeze,
                                         tmp_path / suffix, tmp_path / f'{suffix}.json')
        assert result['preservation']['status'] == 'preserved'
    assert (tmp_path / 'one/graph.json').read_bytes() == (tmp_path / 'two/graph.json').read_bytes()
    new = GraphArtifact.model_validate_json((tmp_path / 'one/graph.json').read_bytes())
    assert new.graph_version != stale.graph_version and all(e.graph_version == new.graph_version for e in new.edges)
    assert validate_taxonomy(new, config) == []
    assert all(sha256(p.read_bytes()).hexdigest() == h for p, h in hashes_before.items())
    with pytest.raises(ValueError, match='unused versioned'):
        correct_release_taxonomy(source, config, QUALITY, source_summary, freeze, tmp_path / 'one', tmp_path / 'oops.json')
    # Scores/support/affiliation facts cannot silently drift.
    changed = new.model_copy(deep=True)
    next(e for e in changed.edges if e.relation == 'HAS_TOPIC').properties['cosine_similarity'] = 0.99
    with pytest.raises(ValueError, match='non_taxonomy_edges'):
        compare_correction(stale, changed)
