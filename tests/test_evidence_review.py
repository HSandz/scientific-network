"""Invented source conflicts: no identity merge follows from a byline correction."""
import json
from pathlib import Path

import pytest

from scientific_network.collect.acquire import names_compatible, official_metadata


def acl_row():
    return dict(venue_id='venue:eacl', title='Invented Study', authors=['Alice Example', 'Bob X. Sample'],
                year=2023, official_url='https://example.org/paper', source_locator='a[href=paper]',
                parser_version='official-roster-families-v2', pdf_url=None)


def test_unicode_names_retain_distinguishing_characters_and_need_nonempty_tokens():
    assert names_compatible('泽浩 刘', '刘, 泽浩')
    assert not names_compatible('泽浩 刘', '泽明 刘')
    assert not names_compatible('刘', '李')
    assert not names_compatible('刘', 'Liu')  # transliteration is not an identity decision
    assert names_compatible('Gaël Example', 'Gael Example')
    assert not names_compatible('', '')


def test_acl_visible_byline_retains_conflicting_citation_names_without_alias_merge():
    body = b'''<meta name="citation_title" content="Invented Study">
      <meta name="citation_author" content="Alice Example"><meta name="citation_author" content="Bob Sample">
      <p class="lead"><a href="/people/a/">Alice Example</a>, <a href="/people/b/">Bob X. Sample</a></p>'''
    paper = official_metadata(body, acl_row())
    assert paper['authors'] == acl_row()['authors']
    assert paper['citation_authors'] == ['Alice Example', 'Bob Sample']
    assert len(paper['byline_discrepancies']) == 2
    assert paper['author_locator'] == 'p.lead a[href^="/people/"]'
    assert not paper['authors_from_roster']
    assert not names_compatible('Bob Sample', 'Bob X. Sample')


@pytest.mark.parametrize('byline', [
    '<a href="/people/a/">Different Example</a>, <a href="/people/b/">Bob X. Sample</a>',
    '<a href="/people/b/">Bob X. Sample</a>, <a href="/people/a/">Alice Example</a>',
    '<a href="/people/a/">Alice Example</a>',
])
def test_acl_visible_disagreement_missing_author_or_order_still_blocks_acquisition(byline):
    with pytest.raises(ValueError, match='byline mismatch'):
        official_metadata(('<p class="lead">'+byline+'</p>').encode(), acl_row())


def test_acl_ambiguous_visible_bylines_are_not_arbitrarily_selected():
    body = b'<p class="lead"><a href="/people/a/">Alice</a></p><p class="lead"><a href="/people/b/">Bob</a></p>'
    with pytest.raises(ValueError, match='ambiguous ACL'):
        official_metadata(body, acl_row())


def test_citation_metadata_is_used_when_visible_byline_is_absent():
    row = acl_row()
    body = b'<meta name="citation_author" content="Alice Example"><meta name="citation_author" content="Bob X. Sample">'
    paper = official_metadata(body, row)
    assert paper['authors'] == row['authors']
    assert paper['author_locator'] == 'meta[name=citation_author]'


def test_retry_reuses_matching_diagnostics_without_network_and_rejects_changed_membership(tmp_path, monkeypatch):
    from scientific_network.collect.acquire import acquire
    from scientific_network.collect.storage import SourceCache, digest
    import yaml

    def no_network(*args, **kwargs):
        raise AssertionError('reused diagnostics must not make requests')
    monkeypatch.setattr(SourceCache, 'get', no_network)
    config = tmp_path / 'config.yaml'
    config.write_text(yaml.safe_dump({'retrieval': {'timeout_seconds': 1, 'max_attempts': 1}}))
    row = {'paper_id': 'paper:invented', 'title': 'Invented Study'}
    manifest = tmp_path / 'manifest.jsonl'
    manifest.write_text(json.dumps(row) + '\n')
    splits = tmp_path / 'splits'
    splits.mkdir()
    membership = splits / 'membership.jsonl'
    membership.write_text(json.dumps({'paper_id': row['paper_id'], 'split': 'development',
                                     'is_pilot': True, 'leakage_group': 'invented'}) + '\n')
    hashes = {'manifest_sha256': digest(manifest.read_bytes()),
              'membership_sha256': digest(membership.read_bytes()),
              'corpus_config_sha256': digest(config.read_bytes())}
    (splits / 'summary.json').write_text(json.dumps(hashes))
    old = tmp_path / 'old'
    old.mkdir()
    (old / 'inputs.json').write_text(json.dumps(hashes))
    record = {'paper_id': row['paper_id'], 'status': 'acquired', 'roster': {**row, 'venue_id': 'venue:invented'},
              'official': {'abstract': 'Invented example'}}
    # Roster equality is required, not just a matching paper ID.
    previous = old / 'papers.json'
    previous.write_text(json.dumps([record]))
    with pytest.raises(ValueError, match='differs from the frozen roster'):
        acquire(manifest, membership, tmp_path / 'bad', tmp_path / 'cache', config, previous)
    record['roster'] = row
    record['roster']['venue_id'] = 'venue:invented'
    manifest.write_text(json.dumps(row) + '\n')
    hashes['manifest_sha256'] = digest(manifest.read_bytes())
    (splits / 'summary.json').write_text(json.dumps(hashes))
    (old / 'inputs.json').write_text(json.dumps(hashes))
    previous.write_text(json.dumps([record]))
    result = acquire(manifest, membership, tmp_path / 'out', tmp_path / 'cache', config, previous)
    assert result['acquired'] == result['previous_acquired_reused'] == 1
    assert json.loads((tmp_path / 'out/papers.json').read_text()) == [record]
    (old / 'inputs.json').write_text(json.dumps({**hashes, 'membership_sha256': '0'*64}))
    with pytest.raises(ValueError, match='frozen manifest/membership'):
        acquire(manifest, membership, tmp_path / 'bad2', tmp_path / 'cache', config, previous)


def test_source_review_withholds_core_and_is_bound_to_exact_input_and_evidence(tmp_path):
    from scientific_network.collect.storage import digest
    from scientific_network.resolve.pilot import resolve
    cache = tmp_path / 'cache'
    (cache / 'objects').mkdir(parents=True)
    body = b'invented source evidence'
    sha = digest(body)
    (cache / 'objects' / sha).write_bytes(body)
    record = {'paper_id': 'paper:invented', 'status': 'acquired',
              'roster': {'year': 2023, 'track': 'main', 'venue_id': 'venue:eacl'},
              'official': {'title': 'Invented Study'}}
    source = tmp_path / 'papers.json'
    source.write_text(json.dumps([record]))
    data = {'reviewed_input_sha256': digest(source.read_bytes()), 'decisions': [
        {'decision_id': 'invented-decision', 'paper_id': record['paper_id'],
         'record_sha256': digest(json.dumps(record, sort_keys=True, ensure_ascii=False).encode()),
         'disposition': 'withhold_core', 'reason': 'invented contradictory printed byline',
         'evidence': [{'sha256': sha}]}]}
    decisions = tmp_path / 'decisions.json'
    decisions.write_text(json.dumps(data))
    config = Path(__file__).resolve().parents[1] / 'configs/corpus-extended-v2.yaml'
    result = resolve(source, tmp_path / 'resolved', cache, config, decisions)
    assert result['counts']['core_papers'] == 0
    queue = json.loads((tmp_path / 'resolved/review-queue.json').read_text())
    assert queue[0]['decision_id'] == 'invented-decision'
    source.write_text(source.read_text() + '\n')
    with pytest.raises(ValueError, match='does not match the resolution input'):
        resolve(source, tmp_path / 'bad', cache, config, decisions)
    data['reviewed_input_sha256'] = digest(source.read_bytes())
    data['decisions'][0]['disposition'] = 'force_identity_merge'
    decisions.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='cannot override identities'):
        resolve(source, tmp_path / 'bad', cache, config, decisions)
    data['decisions'][0]['disposition'] = 'withhold_core'
    decisions.write_text(json.dumps(data))
    (cache / 'objects' / sha).write_bytes(b'corrupted')
    with pytest.raises(ValueError, match='evidence hash mismatch'):
        resolve(source, tmp_path / 'bad', cache, config, decisions)


@pytest.mark.parametrize('change,error', [
    ({'byline_position': 2}, 'position/name'),
    ({'printed_institution': 'University Y', 'openalex_institution_id': 'https://openalex.org/I2'}, 'authorship-specific'),
    ({'pdf_sha256': 'b'*64}, 'paper PDF'),
    ({'printed_institution': 'Univ X'}, 'authorship-specific'),
])
def test_reviewed_affiliation_cannot_use_another_author_or_an_unreviewed_alias(change, error):
    from scientific_network.resolve.pilot import reviewed_institution
    record = {'official': {'authors': ['Alice Example', 'Bob Example']}, 'pdf_source': {'sha256': 'a'*64},
              'openalex_work': {'authorships': [
                  {'institutions': [{'id': 'https://openalex.org/I1', 'display_name': 'University X'}]},
                  {'institutions': [{'id': 'https://openalex.org/I2', 'display_name': 'University Y'}]}]}}
    decision = {'decision_id': 'invented-review', 'byline_position': 1, 'raw_name': 'Alice Example',
                'printed_institution': 'University X', 'openalex_institution_id': 'https://openalex.org/I1',
                'pdf_sha256': 'a'*64, 'source_locator': 'Invented PDF p1 author block'}
    assert reviewed_institution(decision, record)['id'].endswith('/I1')
    with pytest.raises(ValueError, match=error):
        reviewed_institution({**decision, **change}, record)


def test_parser_failure_keeps_download_hash_for_later_source_review(tmp_path, monkeypatch):
    import httpx
    from scientific_network.collect.storage import SourceCache
    from scientific_network.preprocess.extract import extract
    from scientific_network.collect.storage import digest
    monkeypatch.setattr(SourceCache, 'get', lambda *args, **kwargs: (b'%PDF invented', {'sha256': digest(b'%PDF invented'), 'url': 'https://example.org/paper.pdf'}))
    def fail(*args, **kwargs):
        raise httpx.ConnectError('invented local parser failure')
    monkeypatch.setattr('scientific_network.preprocess.extract.request_header', fail)
    source = tmp_path / 'papers.json'
    source.write_text(json.dumps([{'paper_id': 'paper:invented', 'status': 'acquired',
                                  'official': {'pdf_url': 'https://example.org/paper.pdf'}}]))
    config = Path(__file__).resolve().parents[1] / 'configs/corpus-extended-v2.yaml'
    result = extract(source, tmp_path / 'headers', tmp_path / 'cache', config)
    record = json.loads((tmp_path / 'headers/papers.json').read_text())[0]
    assert result['by_status'] == {'review': 1}
    assert record['pdf_source']['sha256'] == digest(b'%PDF invented')
    assert record['extraction_reason'] == 'ConnectError'


@pytest.mark.parametrize('corroborated', [True, False])
def test_reviewed_triples_need_identity_and_deduplicate_automatic_support(tmp_path, monkeypatch, corroborated):
    from scientific_network.resolve import pilot
    from scientific_network.collect.storage import digest

    pdf = b'%PDF invented publication'
    sha = digest(pdf)
    cache = tmp_path / 'cache'
    (cache / 'objects').mkdir(parents=True)
    (cache / 'objects' / sha).write_bytes(pdf)
    proof = {'url': 'https://example.org/invented', 'sha256': sha,
             'retrieved_at': '2026-11-04T00:00:00Z'}
    inst = {'id': 'https://openalex.org/I1', 'display_name': 'University X'}
    record = {'status': 'acquired', 'paper_id': 'paper:invented',
              'roster': {'year': 2023, 'track': 'main', 'venue_id': 'venue:eacl',
                         'official_url': proof['url'], 'source_url': proof['url'],
                         'source_sha256': sha, 'retrieved_at': proof['retrieved_at'],
                         'source_locator': 'invented roster'},
              'official': {'title': 'Invented publication', 'abstract': '',
                           'authors': ['Alice Example', 'Bob Example']},
              'official_source': proof, 'openalex_source': proof,
              'pdf_source': proof, 'tei_source': proof,
              'header_authors': [{'name': 'Alice Example', 'affiliations': [
                  {'institutions': ['University X'], 'locator': 'invented TEI'}]}],
              'openalex_work': {'id': 'W1', 'authorships': [
                  {'author': {'id': 'A1', 'orcid': 'https://orcid.org/0000-0000-0000-0001'},
                   'institutions': [inst]},
                  {'author': {'id': 'A2'}, 'institutions': [
                      {'id': 'https://openalex.org/I2', 'display_name': 'University Y'}]}]}}

    class FakeCache:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def get(self, url):
            title = 'Invented publication' if corroborated else 'Different work'
            return f'<works><group><title>{title}</title></group></works>'.encode(), {**proof, 'url': url}

    monkeypatch.setattr(pilot, 'SourceCache', FakeCache)
    source = tmp_path / 'papers.json'
    source.write_text(json.dumps([record]))
    decision = {'decision_id': 'invented-printed-review', 'paper_id': record['paper_id'],
                'record_sha256': digest(json.dumps(record, sort_keys=True, ensure_ascii=False).encode()),
                'byline_position': 1, 'raw_name': 'Alice Example', 'pdf_sha256': sha,
                'source_locator': 'invented PDF p1 author block',
                'printed_institution': 'University X', 'openalex_institution_id': inst['id']}
    decisions = tmp_path / 'decisions.json'
    decisions.write_text(json.dumps({'reviewed_input_sha256': digest(source.read_bytes()),
                                     'decisions': [], 'reviewed_affiliations': [decision]}))
    config = Path(__file__).resolve().parents[1] / 'configs/corpus-extended-v2.yaml'
    result = pilot.resolve(source, tmp_path / 'resolved', cache, config, decisions)
    graph = json.loads((tmp_path / 'resolved/graph.json').read_text())
    assert result['reviewed_affiliation_decisions_applied'] == int(corroborated)
    assert len(graph['affiliation_observations']) == int(corroborated)
    assert sum(e['relation'] == 'AFFILIATED_WITH' for e in graph['edges']) == int(corroborated)
    if corroborated:
        obs = graph['affiliation_observations'][0]
        assert obs['organization_id'] == 'organization:I1'
        assert obs['researcher_id'].endswith('0001')
        assert len(obs['evidence_ids']) == 3  # provider + printed review + automatic TEI
        assert not any(n['id'] == 'organization:I2' for n in graph['nodes'])


def test_offline_review_rejects_changed_split_hashes_and_held_out_groups(tmp_path):
    from scientific_network.resolve.review import review_evidence
    from scientific_network.collect.storage import digest

    def save(name, value):
        path = tmp_path / name
        path.write_text(json.dumps(value))
        return path

    acquired = save('acquired.json', [{'paper_id': 'paper:invented', 'status': 'failed'}])
    headers = save('headers.json', [{'paper_id': 'paper:invented'}])
    graph = save('graph.json', {'graph_version': 'invented-review-test', 'is_synthetic': True,
                                'nodes': [], 'edges': [], 'evidence': []})
    queue = save('queue.json', [])
    manifest = save('manifest.jsonl', {'paper_id': 'paper:invented',
                                      'official_url': 'https://example.org/not-cached', 'authors': ['Alice Example']})
    membership = save('membership.jsonl', {'paper_id': 'paper:invented', 'is_pilot': True,
                                           'split': 'development', 'leakage_group': 'invented-group'})
    config = save('config.json', {})

    def freeze():
        save('summary.json', {'manifest_sha256': digest(manifest.read_bytes()),
                              'membership_sha256': digest(membership.read_bytes()),
                              'corpus_config_sha256': digest(config.read_bytes())})

    args = (acquired, headers, graph, queue, manifest, membership, tmp_path / 'cache')
    freeze()
    result = review_evidence(*args, tmp_path / 'review', config)
    assert result['diagnostic_papers'] == 1
    assert result['byline_decisions'] == {'retain_withheld': 1}
    assert result['graph_overrides_applied'] == 0
    assert result['semantic_accuracy'] == 'not_measured'
    membership.write_text(membership.read_text() + '\n')
    with pytest.raises(ValueError, match='frozen split hashes'):
        review_evidence(*args, tmp_path / 'bad-hash', config)
    save('membership.jsonl', {'paper_id': 'paper:invented', 'is_pilot': True,
                             'split': 'test', 'leakage_group': 'invented-group'})
    freeze()
    with pytest.raises(ValueError, match='held-out paper/group'):
        review_evidence(*args, tmp_path / 'bad-held-out', config)
    assert not (tmp_path / 'bad-held-out').exists()
