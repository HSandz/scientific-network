"""Invented regression examples, never measured semantic accuracy."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

import pytest

from scientific_network.collect import openalex_release as matching
from scientific_network.collect.storage import read_config
from scientific_network.graph.validate import validate_graph
from scientific_network.resolve import mentions_v5, recovery_v5, candidate_v5
from scientific_network.quality.identity_evaluation import score, freeze
from test_mentions_v5 import paper, raw_person
from test_release_identity import ONE, TWO


@pytest.mark.parametrize('left,right,expected',[
    ('Shu-Tao Xia','Shutao Xia',True),('Song-Can Chen','Songcan Chen',True),
    ('Ann One','An N. One',False),('Ann One','Ann Marie One',False),
    ('Bo An','Bohui An',False),('Wei Zhang','Zhang Wei',False),
    ('José García','Jose Garcia',True),('Li Ming','Lim Ing',False),
])
def test_full_letter_boundaries_are_not_fuzzy_merging(left,right,expected):
    assert recovery_v5.boundary_equivalent(left,right)==expected


def test_formatting_recovers_provider_without_merging_distinct_provider_ids():
    rows=[paper(1,['Shu-Tao Xia'],[raw_person('A1','Shu-Tao Xia')]),
          paper(2,['Shutao Xia'],[raw_person('A1','Shutao Xia')]),
          paper(3,['Shutao Xia'],[raw_person('A2','Shutao Xia')])]
    old,_=mentions_v5.resolve_mentions(rows)
    new,index=mentions_v5.resolve_mentions(rows,recovery=True)
    assert sum(d['resolution_state']=='resolved' for d in old)==1
    assert sum(d['resolution_state']=='resolved' for d in new)==3
    assert new[0]['canonical_researcher_id']==new[1]['canonical_researcher_id']!=new[2]['canonical_researcher_id']
    assert index['name_variation_recoveries']['A1']=='provider_id_full_letter_boundary_normalization'


def test_profile_orcid_conflict_beats_formatting_recovery():
    rows=[paper(1,['Shu-Tao Xia'],[raw_person('A1','Shu-Tao Xia')]),paper(2,['Shutao Xia'],[raw_person('A1','Shutao Xia')])]
    rows[0]['openalex']['authorships'][0]['author']['observed_orcids']=[ONE,TWO]
    ds,_=mentions_v5.resolve_mentions(rows,recovery=True)
    assert all(d['resolution_state']=='ambiguous' for d in ds)


def test_public_alias_certificate_requires_raw_hash_and_account_binding(tmp_path):
    rows=[paper(1,['Ann One'],[raw_person('A1','Ann One')]),paper(2,['Ann Marie One'],[raw_person('A1','Ann Marie One')])]
    for r in rows:r['openalex']['authorships'][0]['author']['orcid']=ONE
    data={'name':{'given-names':{'value':'Ann'},'family-name':{'value':'One'},'path':ONE},
          'other-names':{'other-name':[{'content':'Ann Marie One'}]}}
    body=json.dumps(data).encode();digest=sha256(body).hexdigest();cache=tmp_path/'objects';cache.mkdir();(cache/digest).write_bytes(body)
    c={'provider_id':'A1','orcid':ONE,'declared_names':['Ann Marie One','Ann One'],
       'source':{'url':'https://pub.orcid.org/v3.0/'+ONE+'/person','sha256':digest,'retrieved_at':'2026-11-11T00:00:00+00:00'}}
    path=tmp_path/'cert.json';path.write_text(json.dumps({'certificates':[c]}))
    certs=recovery_v5.load_alias_certificates(path,tmp_path,rows)
    ds,_=mentions_v5.resolve_mentions(rows,recovery=True,alias_certificates=certs)
    assert all(d['resolution_state']=='resolved' for d in ds)
    assert all(d['additional_identity_evidence'] for d in ds)
    (cache/digest).write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='hash mismatch'):recovery_v5.load_alias_certificates(path,tmp_path,rows)


def alternate_fixture(tmp_path, *, other_id=None, wrong_doi=False, wrong_order=False, conflict=False):
    row=paper(1,['Ann One','Bo Two'],[raw_person(None,'Ann One'),raw_person('A2','Bo Two')])
    alt=deepcopy(row['openalex']);alt['id']='https://openalex.org/W99'
    alt['authorships'][0]=raw_person('A1','Ann One')
    if other_id:alt['authorships'][1]['author']['id']='https://openalex.org/'+other_id
    if wrong_doi:alt['doi']='10.123/other'
    if wrong_order:alt['authorships'].reverse()
    if conflict:alt['authorships'][0]['author']['observed_orcids']=[ONE,TWO]
    body=json.dumps({'results':[row['openalex'],alt]}).encode();digest=sha256(body).hexdigest()
    (tmp_path/'objects').mkdir();(tmp_path/'objects'/digest).write_bytes(body)
    row['openalex']['source']['raw_sha256']=digest
    row['openalex']['source']['locator']='results[0]'
    row['openalex']['alternates']=[{'id':alt['id']}]
    return row


def test_missing_id_recovers_exact_doi_cached_alternate_without_source_mutation(tmp_path):
    r=alternate_fixture(tmp_path);before=deepcopy(r)
    ds,_=mentions_v5.resolve_mentions([r],recovery=True,cache_dir=tmp_path)
    assert ds[0]['decision_reason']=='missing_id_exact_doi_alternate_work'
    assert ds[0]['canonical_researcher_id']=='researcher:openalex:A1'
    assert ds[0]['recovery_source_work_id']=='W99'
    assert ds[0]['supporting_evidence'][-1]['field']=='authorships[0]'
    assert r==before
    assert ds==mentions_v5.resolve_mentions([r],recovery=True,cache_dir=tmp_path)[0]


@pytest.mark.parametrize('kwargs',[{'other_id':'A3'},{'wrong_doi':True},{'wrong_order':True},{'conflict':True}])
def test_false_positive_alternate_recovery_is_rejected(tmp_path,kwargs):
    r=alternate_fixture(tmp_path,**kwargs)
    ds,_=mentions_v5.resolve_mentions([r],recovery=True,cache_dir=tmp_path)
    assert ds[0]['resolution_state']=='unresolved'


def test_singleton_doi_redirect_never_passes_on_title_alone():
    from test_release_acquisition import aaai,work
    row=aaai();w=work(row,doi='10.123/journal')
    m=matching.evaluate_match(row,[w])
    assert m['status']=='review' and 'doi_disagreement' in m['reasons']
    assert m['doi_verification']['state']=='ambiguous_mismatch'
    assert matching.verify_work_doi('10.123/a',{'doi':None})['state']=='unresolved_source'
    for state in ('incorrect_match','verified_equivalent_version'):
        decision={'official_doi':'10.123/a','returned_doi':'10.123/b','decision':state,'evidence':[{'url':'https://publisher.example/record','sha256':'a'*64}]}
        assert matching.verify_work_doi('10.123/a',{'doi':'10.123/b'},decision)['state']==state
    assert matching.verify_work_doi('10.123/a',{'doi':'10.123/b'},{'decision':'verified_equivalent_version'})['state']=='ambiguous_mismatch'


def test_independent_scorer_rejects_ai_and_incomplete_references():
    sample=[{'unit_id':'m1','inclusion_probability':.5}]
    assert score(sample,[],{'m1':'A1'})['precision'] is None
    assert score(sample,[{'unit_id':'m1','label':'correct','evidence':['provider'],'independence':'AI','adjudication':'complete'}],{'m1':'A1'})['precision'] is None
    with pytest.raises(ValueError,match='duplicate'):score(sample*2,[],{})


def test_scorer_uses_same_blind_references_for_changed_assignments_and_abstentions():
    from scientific_network.quality.identity_evaluation import paired_score
    sample=[{'unit_id':str(i),'inclusion_probability':.1,'frame':'SRS'} for i in range(3)]
    refs=[{'unit_id':str(i),'label':'identity','reference_identity':'person:'+str(i),
           'accepted_canonical_ids':['A'+str(i)],'evidence':['https://authority.example/person/'+str(i)],
           'independence':'independent','adjudication':'complete'} for i in range(3)]
    old={'0':'A0','1':'wrong','2':None};new={'0':'A0','1':'A1','2':None}
    a=score(sample,refs,old);b=score(sample,refs,new)
    assert a['precision']==.5 and b['precision']==1
    assert a['recall']==1/3 and b['recall']==2/3
    paired=paired_score(sample,refs,{'v4':old,'new':new},replicates=50)
    assert paired['status']=='scored' and len(paired['paired_differences'])==3
    assert paired==paired_score(sample,refs,{'v4':old,'new':new},replicates=50)


def test_pair_scorer_counts_merges_and_splits():
    sample=[{'unit_id':str(i),'inclusion_probability':.5} for i in range(3)]
    refs=[{'unit_id':str(i),'label':label,'evidence':['https://authority.example/evidence'],
           'independence':'independent','adjudication':'complete'} for i,label in enumerate(['same','different','same'])]
    result=score(sample,refs,{'0':True,'1':True,'2':False},pair=True)
    assert result['precision']==result['recall']==.5
    assert result['estimated_false_merge_pairs']==result['estimated_false_split_pairs']==2


def test_true_incompatible_names_stay_ambiguous_with_recovery_enabled():
    rows=[paper(1,['Bo An'],[raw_person('A1','Bo An')]),paper(2,['Bohui An'],[raw_person('A1','Bohui An')])]
    ds,_=mentions_v5.resolve_mentions(rows,recovery=True)
    assert all(d['decision_reason']=='author_id_incompatible_name_variants' for d in ds)


def test_public_alias_cannot_override_conflicting_external_identifier(tmp_path):
    from scientific_network.collect.storage import write_json
    rows=[paper(1,['Ann One'],[raw_person('A1','Ann One')])]
    rows[0]['openalex']['authorships'][0]['author']['orcid']=ONE
    rows[0]['openalex']['authorships'][0]['author']['observed_orcids']=[ONE,TWO]
    data={'name':{'given-names':{'value':'Ann'},'family-name':{'value':'One'},'path':ONE}}
    body=json.dumps(data).encode();h=sha256(body).hexdigest();(tmp_path/'objects').mkdir();(tmp_path/'objects'/h).write_bytes(body)
    c={'provider_id':'A1','orcid':ONE,'declared_names':['Ann One'],
       'source':{'url':'https://pub.orcid.org/v3.0/'+ONE+'/person','sha256':h,'retrieved_at':'2026-11-11T00:00:00+00:00'}}
    path=tmp_path/'cert.json';write_json(path,{'certificates':[c]})
    with pytest.raises(ValueError,match='conflicts'):recovery_v5.load_alias_certificates(path,tmp_path,rows)


def test_probability_sampling_replay_and_overwrite_guard(tmp_path):
    rows=[paper(i,['Ann One'],[raw_person('A1','Ann One')]) for i in range(1,6)]
    ds,_=mentions_v5.resolve_mentions(rows)
    first=freeze(ds,tmp_path/'first',{'decisions':'test'},n=3)
    second=freeze(list(reversed(ds)),tmp_path/'second',{'decisions':'test'},n=3)
    assert first==second
    assert first['assignment_population']==5 and first['pair_population']==10
    with pytest.raises(ValueError,match='unused'):freeze(ds,tmp_path/'first',{})


def test_alternate_evidence_does_not_overwrite_same_batch_primary_evidence(tmp_path):
    from test_release_graph import build,QUALITY
    r=alternate_fixture(tmp_path);ds,_=mentions_v5.resolve_mentions([r],recovery=True,cache_dir=tmp_path)
    (tmp_path/'graph-build').mkdir()
    old,_,_=build(tmp_path/'graph-build',[r])
    new,_,_=candidate_v5.construct_candidate(old,[r],ds,'release-new',read_config(QUALITY))
    old_ids={e.id:e.model_dump() for e in old.evidence if e.kind!='derived'}
    new_ids={e.id:e.model_dump() for e in new.evidence}
    assert all(new_ids[k]==v for k,v in old_ids.items())
    recovered=next(e for e in new.edges if e.relation=='AUTHORED' and e.source_id=='researcher:openalex:A1')
    assert len(recovered.evidence_ids)==2
    assert validate_graph(new,require_derived=True)==[]
