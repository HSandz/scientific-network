"""Synthetic pregraph contracts. No independent scientific scores or network access."""
from copy import deepcopy
import json
from pathlib import Path

import pytest
import yaml

from scientific_network.collect.storage import digest,write_json,write_jsonl
from scientific_network.preprocess.pregraph import (
    canonical_frame,stage_topics,close_queue,validate_authorship,prepare_pregraph,
)
from scientific_network.resolve.diagnostics import record_hash
from test_diagnostic_corroboration import run_fixture,works,OID


def roster(pid,title='Invented',**kw):
    return dict(paper_id=pid,title=title,status='included',official_url='https://example.org/'+pid,**kw)


def test_title_matches_quarantine_without_merging_same_name_or_different_people():
    rows=[roster('a',authors=['Same Name']),roster('b',authors=['Other Person'])]
    result=canonical_frame(rows,[],[{'paper_id':'a'}],[])
    assert result[0]['canonical_work_id'] is None
    assert result[0]['merge_performed'] is False
    assert result[0]['known_group_paper_ids']==['a','b']


def test_transitive_identifier_versions_cannot_leak_heldout():
    rows=[roster('a','Title A',doi='10.1234/shared'),roster('b','Title B',doi='10.1234/shared'),roster('test','Title C')]
    acquired=[{'paper_id':'a'},{'paper_id':'b','openalex_work':{'id':'W1','locations':[{'pdf_url':'https://example.org/test'}]}}]
    result=canonical_frame(rows,[],acquired,[{'paper_id':'test','split':'test'}])
    assert all(r['reason']=='heldout_version_group' for r in result)
    assert all(r['canonical_work_id'] is None for r in result)


def test_historical_title_variant_on_same_official_id_is_preserved_for_leakage():
    old=[roster('a','Original title'),roster('test','Original title')]
    new=[roster('a','Updated title')]
    result=canonical_frame(new,old,[{'paper_id':'a'}],[{'paper_id':'test','split':'test'}])
    assert result[0]['reason']=='heldout_version_group'


def test_repeat_records_do_not_create_duplicate_canonical_rows():
    r=roster('a');result=canonical_frame([r],[r],[{'paper_id':'a'},{'paper_id':'a'}],[])
    assert len(result)==1 and result[0]['canonical_work_id']=='a'


def test_queue_closure_never_uses_authorship_as_an_affiliation():
    rows=[{'paper_id':'a','byline_position':1,'reason':'printed_author_affiliation_review_required'},
          {'paper_id':'a','byline_position':1,'reason':'missing_valid_stable_person_identifiers'}]
    result=close_queue(rows,[{'paper_id':'a','byline_position':1}],[])
    assert result[0]['disposition'].startswith('withheld')
    assert result[1]['disposition']=='resolved_with_accepted_support'


def test_topics_keep_literal_candidates_separate_from_accepted_and_abstain():
    tax={'leaves':[{'id':'topic:synthetic','synonyms':['graph neural network']}],'annotation':{'max_labels':3}}
    record={'paper_id':'a','roster':{'title':'graph neural network'},'official':{'title':'graph neural network'}}
    result=stage_topics(record,tax,True)
    assert result['accepted_labels']==[] and result['validation_status']=='review'
    assert result['candidate_labels'][0]['excerpt']=='graph neural network'
    assert stage_topics(record,tax,False)['candidate_labels']==[]
    record['official']['title']='An ambiguous graph'
    assert stage_topics(record,tax,True)['decision']=='abstain_no_supported_phrase'


def test_person_and_orcid_source_must_be_the_same_author(tmp_path):
    args=run_fixture(tmp_path);r=json.loads(args[0].read_text())[0]
    cache=args[-1];body=works('Synthetic');h=digest(body);(cache/'objects'/h).write_bytes(body)
    proof={'url':f'https://pub.orcid.org/v3.0/{OID}/works','sha256':h,'method':'typed_public_work_doi','locator':'work-summary[put-code=7]','matched_doi':'10.1234/synthetic'}
    rid='researcher:orcid:'+OID
    row=dict(paper_id='one',byline_position=1,raw_name='Alpha One',openalex_author_id='https://openalex.org/A1',
        researcher_id=rid,orcid=OID,id='authorship:'+record_hash([rid,'one']),evidence={'public_orcid':proof})
    validate_authorship(row,r,None,cache)
    wrong=deepcopy(row);wrong['openalex_author_id']='https://openalex.org/A2'
    with pytest.raises(ValueError,match='person identifiers'):validate_authorship(wrong,r,None,cache)
    wrong=deepcopy(row);wrong['evidence']['public_orcid']['url']='https://pub.orcid.org/v3.0/other/works'
    with pytest.raises(ValueError,match='another person'):validate_authorship(wrong,r,None,cache)


def pregraph_fixture(tmp_path):
    args=run_fixture(tmp_path);original=yaml.safe_load(args[4].read_text())
    paper_id=json.loads(args[0].read_text())[0]['paper_id']
    support=tmp_path/'support.json';write_json(support,[{'paper_id':paper_id,'accepted_authorships':[],'affiliation_triples':[]}])
    previous=tmp_path/'queue.json';write_json(previous,[])
    editions=tmp_path/'editions.jsonl';write_jsonl(editions,[{'venue_id':'venue:synthetic','year':2021,'status':'unresolved'}])
    # Real-shaped synthetic roster fields needed by disposition tables.
    records=json.loads(args[0].read_text());records[0]['roster']['venue_id']='venue:synthetic'
    # Fixture acquisition/manifest hashes must be updated together, preserving sample contract.
    acquisition=Path(original['original_acquisition']);a=json.loads(acquisition.read_text());a[0]['roster']['venue_id']='venue:synthetic';acquisition.write_text(json.dumps(a))
    args[1].write_text(json.dumps(a[0]['roster'])+'\n');frozen=json.loads((args[2]/'summary.json').read_text());frozen['manifest_sha256']=digest(args[1].read_bytes());(args[2]/'summary.json').write_text(json.dumps(frozen))
    (acquisition.parent/'summary.json').write_text(json.dumps({**frozen,'papers_sha256':digest(acquisition.read_bytes())}))
    args[0].write_text(json.dumps(records));args[3].write_text(json.dumps({'reviewed_input_sha256':digest(args[0].read_bytes()),'records':[]}))
    taxonomy=tmp_path/'taxonomy.yaml';taxonomy.write_text(yaml.safe_dump({'leaves':[],'annotation':{'max_labels':3}}))
    historical=tmp_path/'historical.jsonl';historical.write_text('')
    members=tmp_path/'old-members.jsonl';members.write_text('')
    quality=tmp_path/'quality.yaml';quality.write_text(yaml.safe_dump({'size':{'min_resolved_core_researchers':2000},'coverage_targets':{'author_paper_affiliation_resolution':0.8,'abstracts':0.95}}))
    paths=dict(quality=str(quality),original_acquisition=str(acquisition),manifest=str(args[1]),splits=str(args[2]),diagnostic_config=original['diagnostic_config'],
        headers=str(args[0]),reviews=str(args[3]),corroboration=str(support),cache=str(args[-1]),historical_manifest=str(historical),
        historical_membership=str(members),historical_acquisition=original['historical_acquisition'],previous_queue=str(previous),
        edition_ledger=str(editions),taxonomy=str(taxonomy))
    config={'graph_construction':False,'heldout_acquisition':False,'paths':paths,'input_sha256':{
        v:digest(Path(v).read_bytes()) for k,v in paths.items() if k not in ('splits','cache')}}
    cfg=tmp_path/'pregraph.yaml';cfg.write_text(yaml.safe_dump(config))
    return cfg,tmp_path/'frozen-output'


def test_pregraph_freeze_replays_offline_without_constructing_graph(tmp_path,monkeypatch):
    cfg,output=pregraph_fixture(tmp_path)
    monkeypatch.setattr('scientific_network.collect.storage.SourceCache.get',lambda *a,**k:pytest.fail('unexpected network'))
    summary=prepare_pregraph(cfg,output)
    assert summary==prepare_pregraph(cfg,output)
    assert summary['full_pregraph_ready'] is False
    assert summary['graph_construction_performed'] is False
    assert summary['gates']['independent_component_quality']['status']=='not_run'
    assert not (output/'graph.json').exists() and not (output/'nodes.json').exists()
    assert (output/'freeze.json').exists()
    assert (output/'current-queue-dispositions.json').exists()
    assert summary['gates']['accepted_topic_coverage']['status']=='failed'


def test_changed_input_rejected_before_any_output(tmp_path):
    cfg,output=pregraph_fixture(tmp_path);c=yaml.safe_load(cfg.read_text());Path(c['paths']['headers']).write_text('[]')
    with pytest.raises(ValueError,match='input changed'):prepare_pregraph(cfg,output)
    assert not output.exists()


def test_graph_or_heldout_flags_cannot_be_enabled(tmp_path):
    cfg,output=pregraph_fixture(tmp_path);c=yaml.safe_load(cfg.read_text());c['graph_construction']=True;cfg.write_text(yaml.safe_dump(c))
    with pytest.raises(ValueError,match='disable graph'):prepare_pregraph(cfg,output)


def test_specific_missing_affiliation_cannot_borrow_another_institution():
    q=[{'paper_id':'a','byline_position':1,'reason':'printed_institution_lacks_exact_same_author_metadata','printed_institution':'Missing Lab'}]
    triples=[{'paper_id':'a','byline_position':1,'organization_name':'Accepted University'}]
    result=close_queue(q,[{'paper_id':'a','byline_position':1}],triples)
    assert result[0]['disposition'].startswith('withheld')
