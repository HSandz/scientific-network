"""Task2C synthetic regression tests. No measured project accuracy labels."""
from copy import deepcopy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from scientific_network.collect.storage import write_json,write_jsonl,read_jsonl
from scientific_network.quality.identity_evaluation import score,paired_score
from scientific_network.quality.identity_review import (
    Evidence, Review, Submission, Crosswalk, Adjudication, prepare, verify_freeze,
    validate_submission, compile_references,
)
from scientific_network.quality.identity_audit import file_hash


def evidence():
    return dict(evidence_id='e1',url='https://authority.example/paper',retrieved_at='2026-11-11T12:00:00+07:00',
                sha256='a'*64,locator='byline persistent identity',excerpt='Invented source evidence',
                source_owner='Synthetic authority',provenance='author maintained',independence='independent',
                independence_rationale='Synthetic example with independent ownership')


def reference(uid='m',ids=None,label='identity'):
    return dict(unit_id=uid,label=label,reference_identity='person:1',accepted_canonical_ids=['A1'] if ids is None else ids,
                crosswalk_complete=True,evidence=[evidence()],independence='independent',adjudication='complete',reviewer_kind='human')


def sample(n=1):return [dict(unit_id='m' if i==0 else str(i),inclusion_probability=.1,frame='SRS') for i in range(n)]


def test_wrong_accepted_identity_is_fp_and_fn_and_zero_f1():
    r=score(sample(),[reference()],{'m':'wrong'})
    assert r['precision']==r['recall']==r['f1']==0
    assert r['weighted_fp']==r['weighted_fn']==10


def test_valid_person_absent_from_all_candidates_is_still_recall_denominator():
    r=score(sample(),[reference(ids=[])],{'m':None})
    assert r['status']=='scored' and r['recall']==r['f1']==0
    assert r['precision'] is None and r['weighted_fn']==10


def test_correct_abstention_and_unknown_are_distinct():
    ref=reference(label='unresolvable')
    a=score(sample(),[ref],{'m':None})
    assert a['weighted_tn']==10 and a['weighted_fn']==0 and a['recall'] is None
    ref['label']='unknown'
    b=score(sample(),[ref],{'m':None})
    assert b['valid_reference_n']==0 and b['precision'] is None


def test_partial_results_are_descriptive_and_share_same_cases():
    refs=[reference()];preds={'old':{'m':'wrong','1':None},'new':{'m':'A1','1':'X'}}
    result=paired_score(sample(2),refs,preds)
    assert result['candidates']['new']['precision'] is None
    assert result['candidates']['new']['verified_subset']['precision']==1
    assert result['paired_differences'] is None
    assert all(r['percentile_95'] is None for r in result['verified_subset_paired_differences'])


def test_weighted_assignment_ratios_and_coverage():
    s=sample(2);s[1]['inclusion_probability']=.5
    r=score(s,[reference(),reference('1')],{'m':'A1','1':'wrong'})
    assert r['precision']==r['recall']==pytest.approx(10/12)
    assert r['coverage']==1
    with pytest.raises(ValueError,match='equal inclusion'):paired_score(s,[reference(),reference('1')],{'x':{'m':'A1','1':'wrong'}},replicates=2)


def test_false_merge_and_false_split_include_abstained_pairs():
    refs=[reference(label='different'),reference('1',label='same')]
    r=score(sample(2),refs,{'m':True,'1':False},pair=True)
    assert r['false_merge_rate']==r['false_split_rate']==1
    assert r['estimand']=='within_declared_blocking_frame' and r['f1']==0
    with pytest.raises(ValueError,match='booleans'):score(sample(),refs,{'m':'A1'},pair=True)


def test_prediction_and_sampling_validation_even_without_references():
    with pytest.raises(ValueError,match='missing candidate'):score(sample(),[],{})
    s=sample();s[0]['inclusion_probability']=0
    with pytest.raises(ValueError,match='probability'):score(s,[],{'m':None})
    s=sample(2);s[1]['frame']='diagnostic'
    with pytest.raises(ValueError,match='pool'):paired_score(s,[reference(),reference('1')],{'x':{'m':None,'1':None}},replicates=2)


def test_ai_labels_never_pass_reference_gate():
    r=reference();r['reviewer_kind']='ai'
    assert score(sample(),[r],{'m':'A1'})['valid_reference_n']==0


def test_paired_bootstrap_reproducible_with_candidate_intervals():
    refs=[reference(),reference('1')];pred={'a':{'m':'wrong','1':None},'b':{'m':'A1','1':None}}
    a=paired_score(sample(2),refs,pred,replicates=30)
    assert a==paired_score(sample(2),refs,pred,replicates=30)
    assert a['candidates']['b']['intervals']['recall']['valid_replicates']==30


@pytest.fixture
def frozen(tmp_path):
    root=tmp_path/'eval';root.mkdir()
    write_jsonl(root/'assignment-sample.jsonl',sample())
    write_jsonl(root/'diagnostic-sample.jsonl',[]);write_jsonl(root/'pair-sample.jsonl',[])
    write_jsonl(root/'evidence-packets.jsonl',[dict(mention_id='m',paper_id='p',author_position=1,official_name='Ann One',
        source_author_id='SECRET_PROVIDER',profile_orcid='SECRET_ORCID',supporting_evidence=[])])
    write_json(root/'freeze.json',dict(files={p.name:file_hash(p) for p in root.iterdir()}))
    return root


def review(role='A',label='identity'):
    return dict(unit_id='m',reviewer=role,reviewer_identity='Person '+role,reviewer_kind='human',model=None,run_id=None,
        label=label,reference_identity='person:1' if label=='identity' else None,confidence='high',notes='Synthetic reasoning',
        evidence=[evidence()] if label!='unknown' else [],submitted_at='2026-11-11T12:00:00+07:00')


def submission(root,role='A',label='identity'):
    return dict(schema_version='identity-review-v2',freeze_sha256=verify_freeze(root),reviewer=role,reviews=[review(role,label)])


def decision(a,b,label='identity'):
    return dict(unit_id='m',review_a_sha256=file_hash(a),review_b_sha256=file_hash(b),adjudicator_identity='A/B consensus',
        adjudicator_kind='human',model=None,run_id=None,resolution='consensus',label=label,
        reference_identity='person:1' if label=='identity' else None,rationale='Synthetic rationale',evidence=[evidence()],
        crosswalk=dict(reference_identity='person:1',accepted_canonical_ids=[],complete=True,evidence=[evidence()],rationale='Absent from all candidates') if label=='identity' else None,
        decided_at='2026-11-11T13:00:00+07:00')


@pytest.mark.parametrize('field,value',[('sha256','x'),('url','javascript:alert(1)'),('retrieved_at','2026-11-11'),('locator',''),('unexpected','x')])
def test_strict_evidence_schema(field,value):
    e=evidence();e[field]=value
    with pytest.raises(ValidationError):Evidence.model_validate(e)


def test_review_requires_independent_evidence_and_real_ai_metadata():
    r=review();r['evidence'][0]['independence']='construction'
    with pytest.raises(ValidationError):Review.model_validate(r)
    r=review(label='unknown');r['reviewer_kind']='ai'
    with pytest.raises(ValidationError):Review.model_validate(r)
    r.update(model='test-model',run_id='synthetic-run')
    assert Review.model_validate(r).label=='unknown'


def test_reviewer_isolation_membership_and_manifest_binding(frozen):
    s=submission(frozen);s['reviews'][0]['reviewer']='B'
    with pytest.raises(ValidationError):validate_submission(s,frozen)
    s=submission(frozen);s['reviews'][0]['unit_id']='foreign'
    with pytest.raises(ValueError,match='membership'):validate_submission(s,frozen)
    s=submission(frozen);s['freeze_sha256']='f'*64
    with pytest.raises(ValueError,match='freeze'):validate_submission(s,frozen)


def test_workspace_is_blind_and_deterministic(frozen,tmp_path):
    works=tmp_path/'works.jsonl';write_jsonl(works,[dict(paper_id='p',venue_id='aaai',year=2021,doi='10.test/p',roster=dict(title='Synthetic paper',authors=['Ann One'],official_url='https://authority.example/p'))])
    a,b=tmp_path/'one',tmp_path/'two';prepare(frozen,works,a);prepare(frozen,works,b)
    assert (a/'manifest.json').read_bytes()==(b/'manifest.json').read_bytes()
    bundle=(a/'A/bundle.js').read_text()
    assert 'SECRET_PROVIDER' not in bundle and 'SECRET_ORCID' not in bundle
    assert 'predictions' not in bundle and '"reviewer": "B"' not in bundle
    with pytest.raises(ValueError,match='unused'):prepare(frozen,works,a)
    (frozen/'assignment-sample.jsonl').write_text('tampered')
    with pytest.raises(ValueError,match='frozen'):verify_freeze(frozen)


def test_compile_preserves_reviews_and_requires_both_before_adjudication(frozen,tmp_path):
    a,b=tmp_path/'a.json',tmp_path/'b.json';write_json(a,submission(frozen));write_json(b,submission(frozen,'B'))
    original=a.read_bytes(),b.read_bytes();d=tmp_path/'d.jsonl';write_jsonl(d,[decision(a,b)])
    compile_references(frozen,a,b,d,tmp_path/'out')
    ref=read_jsonl(tmp_path/'out/references.jsonl')[0]
    assert ref['accepted_canonical_ids']==[] and ref['crosswalk_complete']
    assert (a.read_bytes(),b.read_bytes())==original
    sb=submission(frozen,'B');sb['reviews']=[];b.write_text(json.dumps(sb));d.write_text(json.dumps(decision(a,b))+'\n')
    with pytest.raises(ValueError,match='both reviews'):compile_references(frozen,a,b,d,tmp_path/'bad')


def test_disagreement_not_consensus_and_unknown_stays_unknown(frozen,tmp_path):
    a,b=tmp_path/'a',tmp_path/'b';write_json(a,submission(frozen));write_json(b,submission(frozen,'B','unknown'))
    d=decision(a,b);path=tmp_path/'d';write_jsonl(path,[d])
    with pytest.raises(ValueError,match='disagreement'):compile_references(frozen,a,b,path,tmp_path/'bad')
    d.update(resolution='unresolved',label='unknown',reference_identity=None,crosswalk=None)
    path.write_text(json.dumps(d)+'\n');compile_references(frozen,a,b,path,tmp_path/'out')
    ref=read_jsonl(tmp_path/'out/references.jsonl')[0]
    assert ref['label']=='unknown' and score(sample(),[ref],{'m':'A1'})['precision'] is None


def test_one_human_cannot_impersonate_two_reviewers(frozen,tmp_path):
    a,b,d=tmp_path/'a',tmp_path/'b',tmp_path/'d'
    write_json(a,submission(frozen));s=submission(frozen,'B');s['reviews'][0]['reviewer_identity']='Person A';write_json(b,s);write_jsonl(d,[])
    with pytest.raises(ValueError,match='different actual'):compile_references(frozen,a,b,d,tmp_path/'out')


def test_independent_crosswalk_schema_rejects_duplicate_and_unevidenced_mapping():
    c=dict(reference_identity='person',accepted_canonical_ids=['A','A'],complete=True,evidence=[evidence()],rationale='test')
    with pytest.raises(ValidationError):Crosswalk.model_validate(c)
    c['accepted_canonical_ids']=[];c['evidence'][0]['independence']='shared_upstream'
    with pytest.raises(ValidationError):Crosswalk.model_validate(c)


def test_ai_adjudication_is_separate_not_human_gold(frozen,tmp_path):
    a,b,d=tmp_path/'a',tmp_path/'b',tmp_path/'d'
    write_json(a,submission(frozen));write_json(b,submission(frozen,'B'))
    row=decision(a,b);row.update(adjudicator_kind='ai',model='synthetic-model',run_id='synthetic-run')
    write_jsonl(d,[row]);compile_references(frozen,a,b,d,tmp_path/'out')
    assert read_jsonl(tmp_path/'out/references.jsonl')==[]
    assert len(read_jsonl(tmp_path/'out/ai-assessments.jsonl'))==1


def test_srs_wilson_intervals_remain_nonzero_width_at_boundaries():
    result=score(sample(),[reference()],{'m':'A1'})
    assert result['conditional_wilson_95']['precision']['wilson_lower']<1
    assert result['conditional_wilson_95']['precision']['total']==1


def test_bounded_source_collector_rejects_unscoped_or_duplicate_urls(tmp_path):
    from scientific_network.quality.identity_sources import collect
    plan=tmp_path/'plan.json';write_json(plan,[dict(url='https://unscoped.example/p')])
    with pytest.raises(ValueError,match='unscoped'):collect(plan,tmp_path/'cache',tmp_path/'out')
    plan.write_text(json.dumps([dict(url='https://www.ijcai.org/p')]*2))
    with pytest.raises(ValueError,match='duplicate'):collect(plan,tmp_path/'cache',tmp_path/'out')


def test_workspace_refuses_nested_frozen_sample_output(frozen,tmp_path):
    with pytest.raises(ValueError,match='outside frozen'):
        prepare(frozen,tmp_path/'unused-works',frozen/'new')


def test_incomplete_mixed_frames_never_pooled():
    s=sample(2);s[1]['frame']='diagnostic'
    with pytest.raises(ValueError,match='pool'):score(s,[],{'m':None,'1':None})


def test_candidate_predictions_shipped_only_to_adjudication_after_blind_roles(frozen,tmp_path):
    graph=tmp_path/'graph.json';write_json(graph,dict(nodes=[dict(id='SECRET_PERSON',name='Synthetic canonical',label='Researcher')],
        edges=[dict(relation='AUTHORED',target_id='p',source_id='SECRET_PERSON',properties=dict(byline_position=1))]))
    bindings=tmp_path/'bindings.json';write_json(bindings,dict(freeze_sha256=verify_freeze(frozen),graphs=dict(candidate=dict(path=str(graph),sha256=file_hash(graph)))))
    works=tmp_path/'works';write_jsonl(works,[dict(paper_id='p',venue_id='aaai',year=2021,doi='10.test/p',roster=dict(title='Synthetic',authors=['Ann One']))])
    prepare(frozen,works,tmp_path/'ui',candidates_path=bindings)
    assert 'SECRET_PERSON' not in (tmp_path/'ui/A/bundle.js').read_text()
    assert 'SECRET_PERSON' not in (tmp_path/'ui/B/bundle.js').read_text()
    assert 'SECRET_PERSON' in (tmp_path/'ui/adjudication/bundle.js').read_text()


def test_source_hash_tampering_is_rejected_before_packet_creation(tmp_path):
    from scientific_network.quality.identity_evidence import inventory
    cache=tmp_path/'cache';(cache/'objects').mkdir(parents=True);(cache/'objects'/('a'*64)).write_text('tampered')
    provenance=tmp_path/'provenance';write_json(provenance,dict(sources=[dict(url='https://www.ijcai.org/p',category='test',mention_ids=[],status='retrieved',record=dict(sha256='a'*64))]))
    decisions=tmp_path/'decisions';write_jsonl(decisions,[])
    with pytest.raises(ValueError,match='hash mismatch'):inventory([provenance],[cache],decisions,tmp_path/'out')


def test_browser_import_rejects_incomplete_sources_and_cross_reviewer_files():
    import shutil,subprocess
    if not shutil.which('node'):pytest.skip('Node unavailable for browser contract check')
    js=(Path(__file__).parents[1]/'src/scientific_network/quality/identity_workspace/app.js').read_text()
    helpers=js[js.index('function strictKeys('):js.index("$('import').onchange=")]
    payload=dict(schema_version='identity-review-v2',freeze_sha256='a'*64,reviewer='A',reviews=[review()])
    script='const BUNDLE={freeze_sha256:"'+('a'*64)+'",cases:[{unit_id:"m",category:"assignment"}]};\n'+helpers
    script+='\nlet s='+json.dumps(payload)+';checkSubmission(s,"A");'
    script+='\nlet failures=0;for(const change of [x=>x.reviewer="B",x=>delete x.reviews[0].evidence[0].sha256,x=>x.reviews[0].evidence[0].url="javascript:alert(1)",x=>x.reviews[0].notes=" "]){let x=structuredClone(s);change(x);try{checkSubmission(x,"A");}catch(e){failures++;}}if(failures!==4)throw Error("invalid import accepted");'
    result=subprocess.run(['node','-e',script],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
