"""Invented source snippets; no network access or measured project statistics."""
from pathlib import Path
import json
import httpx
import pytest

from scientific_network.collect.discover import parse_index, discover
from scientific_network.collect.rosters import parse_roster
from scientific_network.collect.extended import allocate_extended
from scientific_network.collect.splits import title_group
from scientific_network.collect.storage import SourceCache
from scientific_network.collect.acquire import choose_work

SOURCE = {'url':'https://example.org/2023/', 'sha256':'a'*64, 'retrieved_at':'2026-11-03T00:00:00Z'}

def edition(adapter, **kwargs):
    return dict(venue_id='venue:sample',name='Sample',year=2023,adapter=adapter,
        official_index='https://example.org/2023/',include_tracks=['main'],exclude_tracks=['nonresearch'],**kwargs)


def test_query_parameters_survive_canonicalization_and_cache_replay(tmp_path):
    calls=[]
    def handler(request):
        calls.append(request)
        assert request.url.params['day']=='all'
        assert request.url.params['limit']=='10'
        return httpx.Response(200,text='2023 all papers')
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        cache=SourceCache(tmp_path,client=client,delay=0)
        a=cache.get('https://example.org/2023?day=all',params={'limit':'10'})
        assert cache.get('https://example.org/2023',params={'day':'all','limit':'10'})==a
        assert len(calls)==1
        with pytest.raises(ValueError,match='credentials'):
            cache.get('https://example.org/?api_key=do-not-log')


def test_pmlr_nonresearch_sections_and_wrong_volume_are_not_main_papers():
    html=b'''<h2>Volume 195, 2023</h2><h3>Original Papers</h3>
    <div class="paper"><p class="title">Research Example</p><span class="authors">Alpha Person, Beta Person</span><a href="/v195/research23.html">abs</a></div>
    <h3>Open Problems</h3><div class="paper"><p class="title">An open problem</p><span class="authors">Gamma Person</span><a href="/v195/problem23.html">abs</a></div>'''
    rows=parse_roster(html,edition('pmlr',volume=195),SOURCE)
    assert [r['status'] for r in rows]==['included','excluded']
    with pytest.raises(ValueError,match='missing title or record link'):
        parse_roster(html,edition('pmlr',volume=206),SOURCE)


def test_ijcai_section_boundary_excludes_survey_and_unknown_sections():
    def paper(i): return f'<div class="paper_wrapper"><a class="title" href="/2023/{i}">Example {i}</a><div class="authors"><a>Alpha Person</a></div></div>'
    rows=parse_roster(('2023'+paper(0)+'<h3>Main Track</h3>'+paper(1)+'<h3>Survey Track</h3>'+paper(2)).encode(),edition('ijcai'),SOURCE)
    assert [r['status'] for r in rows]==['review','included','excluded']


@pytest.mark.parametrize('family,html,extras',[
 ('mlsys','2023<div class="paper-content"><a href="/2023/hash/abc-Abstract.html">Example</a><span class="paper-authors">Alpha Person, Beta Person</span></div>',{}),
 ('rss','2023<table><tr><td><a href="p001.html">Example</a><i>Alpha Person, Beta Person</i></td></tr></table>',{}),
 ('kr','2023<h2>Main Track</h2><li><div class="track_paperinfo__test"><a href="/2023/1/">Example</a><ol><li>Alpha Person</li><li>Beta Person</li></ol></div></li>',{}),
 ('cvf','2023<dl><dt class="ptitle"><a href="/2023/example.html">Example</a></dt><dd><a>Alpha Person</a><a>Beta Person</a></dd></dl>',{}),
 ('acl','2023<span class="d-block"><strong><a href="/2023.acl-long.1/">Example</a></strong><a href="/people/a/">Alpha Person</a><a href="/people/b/">Beta Person</a></span>',{'collection':'2023.acl-long'}),
])
def test_source_families_preserve_ordered_individual_bylines(family,html,extras):
    rows=parse_index(html.encode(),edition(family,**extras),SOURCE)
    assert len(rows)==1 and rows[0]['status']=='included'
    assert rows[0]['authors']==['Alpha Person','Beta Person']
    assert rows[0]['paper_id'].startswith('paper:sample:2023:')


def test_extended_splits_preserve_legacy_roles_and_quarantine_cross_venue_versions():
    rows=[dict(paper_id=f'new-{i}',title=f'Unique {i}',venue_id='new',status='included') for i in range(120)]
    legacy=[]
    for i,role in enumerate(['test','development','pool']):
        r=dict(paper_id=f'old-{i}',title=f'Old {i}',venue_id='old',status='included');rows.append(r)
        legacy.append(dict(paper_id=r['paper_id'],venue_id='old',leakage_group=title_group(r['title']),split=role,is_pilot=role=='development'))
        rows.append(dict(r,paper_id=f'new-version-{i}',venue_id='new'))
    rows.extend([dict(paper_id=f'collision-{i}',title='Cross Venue',venue_id=f'other{i}',status='included') for i in range(2)])
    a=allocate_extended(rows,legacy,seed=17,diagnostic_per_venue=10,eligible_venues={'new'})
    assert a==allocate_extended(list(reversed(rows)),legacy,seed=17,diagnostic_per_venue=10,eligible_venues={'new'})
    byid={r['paper_id']:r for r in a}
    assert all(byid[r['paper_id']]==r for r in legacy)
    assert byid['new-version-0']['split']=='test'
    assert byid['new-version-1']['split']==byid['new-version-2']['split']=='review'
    assert byid['collision-0']['split']=='review'
    assert sum(r['is_pilot'] for r in a)==11
    assert sum(r['split']=='test' for r in a)==62
    assert not any(r['is_pilot'] and r['split']=='test' for r in a)


def test_small_edition_allocation_is_prospective_and_test_never_acquired():
    rows=[dict(paper_id=str(i),title=f'Example {i}',venue_id='small',status='included') for i in range(50)]
    assignments=allocate_extended(rows,[],seed=19,diagnostic_per_venue=10,eligible_venues={'small'})
    assert sum(r['split']=='test' for r in assignments)==10
    assert sum(r['split']=='development' for r in assignments)==10
    assert sum(r['is_pilot'] for r in assignments)==10
    assert all(r['split']=='development' for r in assignments if r['is_pilot'])


def test_work_year_window_follows_edition_instead_of_hardcoded_pilot_year():
    paper={'title':'Example','authors':['Alpha Person'],'year':2026}
    work={'id':'W1','title':'Example','publication_year':2027,'authorships':[{'author':{'display_name':'Alpha Person'}}]}
    assert choose_work([work],paper,'https://example.org/')[0]==work
    assert choose_work([dict(work,publication_year=2023)],paper,'https://example.org/')[0] is None


def test_repeated_official_dom_records_deduplicate_but_conflicts_fail():
    paper='<div class="paper"><p class="title">Research</p><span class="authors">Alpha Person</span><a href="/v229/example.html">abs</a></div>'
    assert len(parse_roster(('2023'+paper+paper).encode(),edition('pmlr',volume=229),SOURCE))==1
    with pytest.raises(ValueError,match='conflicting duplicate'):
        parse_roster(('2023'+paper+paper.replace('Research','Different')).encode(),edition('pmlr',volume=229),SOURCE)


def test_acl_frontmatter_is_excluded_and_miccai_byline_must_wait_for_frozen_sample():
    html=b'2023<span class="d-block"><strong><a href="/2023.acl-long.0/">Proceedings</a></strong><a href="/people/a/">Editor Person</a></span>'
    assert parse_roster(html,edition('acl',collection='2023.acl-long'),SOURCE)[0]['status']=='excluded'
    row=parse_roster(b'2023<a href="/2023/papers/001-Paper0123.html">Research</a>',edition('miccai'),SOURCE)[0]
    assert row['status']=='included' and row['authors']==[]
    from scientific_network.collect.acquire import official_metadata
    with pytest.raises(ValueError,match='no authoritative byline'):
        official_metadata(b'<h1>Research</h1>',row)


def test_aamas_extended_abstract_posters_do_not_enter_main_research_roster():
    def paper(page): return f'<p><a href="../pdfs/p{page}.pdf">Research</a><font face="Times New Roman"><br>Alpha Person<i>(Example University)</i><br>Beta Person<i>(Example Lab)</i></font></p>'
    rows=parse_roster(('2023<strong>Session 1A: Learning</strong>'+paper(5)+'<strong>Poster Session I</strong>'+paper(6)).encode(),edition('aamas'),SOURCE)
    assert [r['status'] for r in rows]==['included','excluded']
    assert rows[0]['authors']==['Alpha Person','Beta Person']


def test_discovery_ledgers_blocked_and_no_edition_without_claiming_complete(tmp_path,monkeypatch):
    import yaml
    from scientific_network.collect.storage import digest,SourceError
    legacy=tmp_path/'legacy.jsonl';legacy.write_text('')
    config=tmp_path/'corpus.yaml';config.write_text(yaml.safe_dump(dict(collection_authorized=True,
        legacy_manifest=str(legacy),legacy_manifest_sha256=digest(legacy.read_bytes()),
        retrieval={'timeout_seconds':1,'max_attempts':1},editions=[
            edition('rss'),dict(venue_id='venue:none',year=2023,edition_status='no_2023_edition') ])))
    def fail(*args,**kwargs): raise SourceError('example.org: HTTP 503')
    monkeypatch.setattr(SourceCache,'get',fail)
    summary=discover(config,tmp_path/'output',tmp_path/'cache')
    assert summary['incomplete_editions']==1
    assert summary['edition_statuses']=={'blocked':1,'no_2023_edition':1}
    assert summary['roster_records']==0


def test_query_bearing_roster_evidence_remains_resolvable():
    src={**SOURCE,'url':'https://example.org/2023','params':{'day':'all'}}
    row=parse_roster(b'2023<dt class="ptitle"><a href="/paper.html">Research</a></dt><dd><a>Alpha Person</a></dd>',edition('cvf'),src)[0]
    assert row['source_url']=='https://example.org/2023?day=all'


def test_official_metadata_records_roster_byline_authority_and_rejects_mismatch():
    from scientific_network.collect.acquire import official_metadata
    row=dict(title='Research',authors=['Alpha Person'],year=2023,official_url='https://example.org/paper',
        source_locator="a[href='/paper']",parser_version='official-roster-families-v2',pdf_url=None)
    paper=official_metadata(b'<div id="abstract">Abstract example.</div>',row)
    assert paper['authors_from_roster'] and paper['title_from_roster']
    assert paper['abstract']=='Abstract example.'
    with pytest.raises(ValueError,match='byline mismatch'):
        official_metadata(b'<meta name="citation_author" content="Different Person">',row)


@pytest.mark.parametrize('venue,body,locator',[
    ('miccai',b'<h1 id="author-id">Authors</h1><p>Alpha Person, Beta Person</p><h1 id="abstract-id">Abstract</h1><p>Actual abstract.</p><h1>Reviews</h1><p>Unrelated review.</p>','#abstract-id + p'),
    ('ijcai',b'<div class="article__abstract"><p class="eyebrow">Abstract</p><p>Actual abstract.</p></div>','.article__abstract p:not(.eyebrow)'),
    ('kr',b'<h2>Keywords</h2><div>Other text</div><h2>Abstract</h2><div><p>Actual abstract.</p></div>','h2[text=Abstract] + div'),
    ('rss',b'<p><b>Abstract:</b></p><p>Actual abstract.</p><p>Download</p>','b[text=Abstract:]/parent::p/following-sibling::p[1]'),
])
def test_family_abstracts_exclude_labels_reviews_and_other_sections(venue,body,locator):
    from scientific_network.collect.acquire import official_metadata
    row=dict(venue_id='venue:'+venue,title='Research',authors=[] if venue=='miccai' else ['Alpha Person'],
        year=2023,official_url='https://example.org/paper',source_locator='a[href=paper]',pdf_url=None)
    paper=official_metadata(body,row)
    assert paper['abstract']=='Actual abstract.' and paper['abstract_locator']==locator
    if venue=='miccai':
        assert paper['authors']==['Alpha Person','Beta Person']
        assert not paper['authors_from_roster']
        assert paper['author_locator'].startswith('#author-id')


def test_topic_evidence_uses_paper_text_source_not_roster(tmp_path):
    from scientific_network.contracts import GraphArtifact,Node,Edge,EvidenceRecord
    from scientific_network.graph.schema import edge_id
    from scientific_network.nlp.baseline import classify
    common=dict(kind='observed',retrieved_at='2026-11-03T00:00:00Z',source_locator='example')
    graph=GraphArtifact(graph_version='synthetic-text-source',is_synthetic=True,
        nodes=[Node(id='paper:example',label='Paper',name='Research',properties={'is_core':True,
            'abstract':'A graph neural network approach.','topic_text_evidence_id':'evidence:text',
            'year':2023,'official_url':'https://example.org/paper','track':'main',
            'unresolved_author_reason':'invented fixture with unresolved byline'}),
            Node(id='venue:sample',label='Venue',name='Sample')],
        edges=[Edge(edge_id=edge_id('PUBLISHED_IN','paper:example','venue:sample'),relation='PUBLISHED_IN',
            source_id='paper:example',target_id='venue:sample',evidence_kind='observed',
            evidence_ids=['evidence:roster'],method_version='synthetic',graph_version='synthetic-text-source',validation_status='accepted')],
        evidence=[EvidenceRecord(id='evidence:roster',source_url='https://example.org/roster',raw_sha256='a'*64,**common),
            EvidenceRecord(id='evidence:text',source_url='https://example.org/paper',raw_sha256='b'*64,**common)])
    path=tmp_path/'base.json';path.write_text(graph.model_dump_json())
    root=Path(__file__).resolve().parents[1]
    classify(path,root/'configs/topics.yaml',root/'configs/quality.yaml',tmp_path/'topics.json',tmp_path/'cache')
    result=GraphArtifact.model_validate_json((tmp_path/'topics.json').read_bytes())
    edge=next(e for e in result.edges if e.relation=='HAS_TOPIC')
    ev=next(e for e in result.evidence if e.id==edge.evidence_ids[0])
    assert ev.raw_sha256=='b'*64 and str(ev.source_url)=='https://example.org/paper'
    assert ev.excerpt=='graph neural network'


def test_acl_abstract_uses_displayed_text_not_correction_form():
    from scientific_network.collect.acquire import official_metadata
    row=dict(venue_id='venue:acl',title='Research',authors=['Alpha Person'],year=2023,
        official_url='https://example.org/paper',source_locator='a[href=paper]',pdf_url=None)
    html=b'<div class="acl-abstract"><h5>Abstract</h5><span>Displayed scientific abstract.</span></div><textarea id="paperAbstract">User edit form</textarea>'
    assert official_metadata(html,row)['abstract']=='Displayed scientific abstract.'


def test_shared_provider_work_quarantines_versions_without_silent_merge(tmp_path):
    from scientific_network.resolve.pilot import resolve
    records=[dict(paper_id=f'paper:version{i}',status='acquired',
        roster={'venue_id':'venue:icml','year':2023,'track':'main'},
        official={'title':'Example','authors':['Alpha Person'],'abstract':''},
        openalex_work={'id':'Wsame','authorships':[]}) for i in range(2)]
    path=tmp_path/'papers.json';path.write_text(json.dumps(records))
    resolve(path,tmp_path/'resolved',tmp_path/'cache',Path('configs/corpus.yaml'))
    graph=json.loads((tmp_path/'resolved/graph.json').read_text())
    assert graph['nodes']==[] and graph['edges']==[]
    review=json.loads((tmp_path/'resolved/review-queue.json').read_text())
    assert len(review)==2 and all(r['reason']=='shared_provider_work_requires_version_review' for r in review)
