"""Synthetic contract tests; none of these examples measures semantic accuracy."""
from copy import deepcopy
import json
from pathlib import Path

import pytest
import yaml

from scientific_network.collect.storage import digest, write_json
from scientific_network.resolve.diagnostics import (
    publication_support, orcid_key, crosswalk_conflicts, version_conflicts,
    reviewed_affiliations, load_reviews, record_hash, corroborate_diagnostics,
)
from test_diagnostic_headers import example, selection_fixture

OID = '0000-0002-1825-0097'


def works(title='Synthetic title', year='2021', identifier='10.1234/synthetic', kind='doi', relationship='self'):
    return f'''<works xmlns="urn:synthetic"><group><work-summary put-code="7">
    <title><title>{title}</title></title><publication-date><year>{year}</year></publication-date>
    <external-ids><external-id><external-id-type>{kind}</external-id-type>
    <external-id-value>{identifier}</external-id-value><external-id-relationship>{relationship}</external-id-relationship>
    </external-id></external-ids></work-summary></group></works>'''.encode()


def test_unicode_publication_titles_do_not_collapse_to_empty():
    assert publication_support(works('研究网络'), '研究网络', 2021, set())['method'] == 'unicode_exact_title_and_year'
    assert publication_support(works('研究网络'), '不同论文', 2021, set()) is None
    assert publication_support(works('研究网络', year='2020'), '研究网络', 2021, set()) is None


@pytest.mark.parametrize('kind,relationship', [('isbn','self'), ('doi','part-of'), ('doi','version-of')])
def test_identifier_types_and_relationships_are_not_borrowed(kind, relationship):
    assert publication_support(works(kind=kind, relationship=relationship), 'Another title', 2021, {'10.1234/synthetic'}) is None


def test_typed_doi_and_malformed_xml():
    assert publication_support(works(identifier='HTTPS://DOI.ORG/10.1234/SYNTHETIC'), 'Another', 2020, {'10.1234/synthetic'})['method'] == 'typed_public_work_doi'
    with pytest.raises(Exception): publication_support(b'<broken', 'T', 2021, set())
    with pytest.raises(ValueError): publication_support(b'<html/>', 'T', 2021, set())
    assert orcid_key(OID) == OID
    assert orcid_key(OID[:-1]+'8') is None


def test_work_match_cannot_join_fields_across_summaries():
    body = b'<works><group><work-summary><title><title>T</title></title></work-summary><work-summary><publication-date><year>2021</year></publication-date></work-summary></group></works>'
    assert publication_support(body, 'T', 2021, set()) is None


def person_record(provider='https://openalex.org/A1', oid=OID, name='Alpha One'):
    return {'paper_id':'p', 'openalex_work':{'id':'https://openalex.org/W1', 'authorships':[
        {'author':{'id':provider, 'orcid':oid, 'display_name':name}}]}}


def test_conflicting_crosswalks_and_historical_names_withhold():
    a=person_record();b=person_record(oid='0000-0001-5109-3700')
    assert 'https://openalex.org/A1' in crosswalk_conflicts([a,b],[])[0]
    assert OID in crosswalk_conflicts([a,person_record(name='Different Person')],[])[1]
    node={'label':'Researcher','name':'Other Person','properties':{'orcid':OID,'openalex_ids':['https://openalex.org/A1']}}
    assert OID in crosswalk_conflicts([a],[node])[1]
    # Same normalized names alone do not create a crosswalk.
    assert crosswalk_conflicts([person_record(provider=None,oid=None)],[]) == (set(),set())


def test_shared_work_and_heldout_location_are_quarantined():
    a=person_record();b=deepcopy(a);b['paper_id']='historical-version'
    assert version_conflicts([a],[b],set())['p'].startswith('shared_provider')
    a['openalex_work']['locations']=[{'pdf_url':'https://example.org/test.pdf'}]
    assert version_conflicts([a],[],{'https://example.org/test.pdf'})['p'].startswith('provider_location')


def test_reviewed_multi_affiliations_are_positional_and_deduplicated():
    r=example();r['roster']['year']=2021
    for i,entry in enumerate(r['openalex_work']['authorships']):
        for j,inst in enumerate(entry['institutions']): inst['id']='https://openalex.org/I'+str(i*10+j+1)
    affs=[{'printed_institution':n,'source_locator':loc} for n,loc in [
        ('First University','block1'),('Second Institute','block2'),('First University','block3'),('Third University','wrong-author')]]
    review={'decision_id':'d','authors':[{'affiliations':affs},{'affiliations':[]}]}
    triples,pending=reviewed_affiliations(r,review,1,'researcher:synthetic',{})
    assert len(triples)==2 and len(pending)==1
    assert triples[0]['printed_locators']==['block1','block3']


def run_fixture(tmp_path):
    acquired,manifest,splits,config=selection_fixture(tmp_path)
    original=json.loads(acquired.read_text())[0]
    original['roster'].update(authors=['Alpha One'],year=2021,source_url='https://example.org/roster',source_sha256='x',source_locator='article')
    original['official']={'title':'Synthetic','authors':['Alpha One'],'doi':'10.1234/synthetic'}
    original['openalex_work']={'id':'https://openalex.org/W1','title':'Synthetic','publication_year':2021,
        'doi':'https://doi.org/10.1234/synthetic','authorships':[{'author':{'id':'https://openalex.org/A1','display_name':'Alpha One','orcid':OID},'institutions':[]}]}
    cache=tmp_path/'cache';(cache/'objects').mkdir(parents=True)
    proof={'url':'https://example.org/evidence','sha256':digest(b'synthetic evidence')}
    (cache/'objects'/proof['sha256']).write_bytes(b'synthetic evidence')
    original['official_source']=original['openalex_source']=proof
    # Rewrite only this synthetic fixture's linked hashes.
    acquired.write_text(json.dumps([original]));manifest.write_text(json.dumps(original['roster'])+'\n')
    frozen=json.loads((splits/'summary.json').read_text());frozen['manifest_sha256']=digest(manifest.read_bytes())
    (splits/'summary.json').write_text(json.dumps(frozen));(acquired.parent/'summary.json').write_text(json.dumps({**frozen,'papers_sha256':digest(acquired.read_bytes())}))
    header=dict(original,original_record_sha256=record_hash(original),pdf_source=proof,tei_source=proof,
        extraction_status='parsed',header_title='Synthetic',header_authors=[{'name':'Alpha One','affiliations':[]}])
    inp=tmp_path/'headers'/'papers.json';write_json(inp,[header]);write_json(inp.parent/'summary.json',{
        **{k:v for k,v in frozen.items() if k!='input_sha256'},'input_sha256':digest(acquired.read_bytes()),'papers_sha256':digest(inp.read_bytes())})
    reviews=tmp_path/'reviews.json';write_json(reviews,{'reviewed_input_sha256':digest(inp.read_bytes()),'records':[]})
    hist=tmp_path/'hist.json';write_json(hist,[]);graph=tmp_path/'graph.json';write_json(graph,{'nodes':[]})
    config.update(collection_authorized=True,original_acquisition=str(acquired),original_acquisition_sha256=digest(acquired.read_bytes()),
        historical_acquisition=str(hist),historical_acquisition_sha256=digest(hist.read_bytes()),historical_graph=str(graph),historical_graph_sha256=digest(graph.read_bytes()),
        orcid=dict(max_unique_requests=1,timeout_seconds=1,max_attempts=1,delay_seconds=0),
        policy=dict(source_review_may_override_identity=False,affiliations_require_printed_review=True,accept_name_only_merges=False,graph_import=False))
    cfg=tmp_path/'corroborate.yaml';cfg.write_text(yaml.safe_dump(config))
    return inp,manifest,splits,reviews,cfg,tmp_path/'out',cache


def test_end_to_end_cache_checkpoint_replay_and_frozen_tampering(tmp_path,monkeypatch):
    args=run_fixture(tmp_path);calls=[]
    def fake_get(self,url,**kwargs):
        calls.append(url)
        return works('Synthetic'),{'url':url,'sha256':digest(works('Synthetic'))}
    monkeypatch.setattr('scientific_network.resolve.diagnostics.SourceCache.get',fake_get)
    first=corroborate_diagnostics(*args)
    assert first['accepted_researchers']==first['accepted_authorship_support']==1
    assert first['accepted_affiliation_triples']==0 and first['graph_imports']==0
    assert first==corroborate_diagnostics(*args) and len(calls)==1
    (args[2]/'reserved-tests.jsonl').write_text('{}\n')
    with pytest.raises(ValueError,match='frozen'):corroborate_diagnostics(*args)
    assert len(calls)==1


def test_review_binding_rejects_modified_pdf_and_record(tmp_path):
    args=run_fixture(tmp_path);records=json.loads(args[0].read_text());r=records[0]
    review=dict(paper_id=r['paper_id'],record_sha256='wrong',pdf_sha256=r['pdf_source']['sha256'])
    path=tmp_path/'review2.json';path.write_text(json.dumps({'reviewed_input_sha256':digest(args[0].read_bytes()),'records':[review]}))
    with pytest.raises(ValueError,match='record hash'):load_reviews(path,records,digest(args[0].read_bytes()),args[-1])
    review['record_sha256']=record_hash(r);review['pdf_sha256']='wrong';path.write_text(json.dumps({'reviewed_input_sha256':digest(args[0].read_bytes()),'records':[review]}))
    with pytest.raises(ValueError,match='PDF hash'):load_reviews(path,records,digest(args[0].read_bytes()),args[-1])


@pytest.mark.parametrize('mode', ['no_public_work', 'malformed', 'quota'])
def test_unavailable_public_support_is_queued_and_replay_is_offline(tmp_path,monkeypatch,mode):
    from scientific_network.collect.storage import QuotaError
    args=run_fixture(tmp_path);calls=[]
    def fake_get(self,url,**kwargs):
        calls.append(url)
        if mode=='quota':raise QuotaError('pub.orcid.org: access/quota HTTP 429; collection stopped')
        return (b'<broken' if mode=='malformed' else b'<works/>'),{'url':url,'sha256':'synthetic'}
    monkeypatch.setattr('scientific_network.resolve.diagnostics.SourceCache.get',fake_get)
    summary=corroborate_diagnostics(*args)
    assert summary['accepted_researchers']==summary['accepted_authorship_support']==0
    assert summary['collection_stopped']==(mode=='quota')
    assert summary==corroborate_diagnostics(*args) and len(calls)==1


def test_original_fields_cannot_be_replaced_by_new_header_record(tmp_path,monkeypatch):
    args=run_fixture(tmp_path);records=json.loads(args[0].read_text());records[0]['official']['authors']=['Different Person']
    args[0].write_text(json.dumps(records))
    summary_path=args[0].parent/'summary.json';summary=json.loads(summary_path.read_text());summary['papers_sha256']=digest(args[0].read_bytes());summary_path.write_text(json.dumps(summary))
    monkeypatch.setattr('scientific_network.resolve.diagnostics.SourceCache.get',lambda *a,**k:pytest.fail('network before input checks'))
    with pytest.raises(ValueError,match='original acquisition'):corroborate_diagnostics(*args)
