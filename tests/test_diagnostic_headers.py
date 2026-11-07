"""Invented source evidence; these tests do not measure scientific accuracy."""
from copy import deepcopy
import json
from pathlib import Path
import pytest

from scientific_network.collect.storage import digest, write_json, write_jsonl
from scientific_network.collect.splits import title_group
from scientific_network.preprocess.diagnostics import source_triage, validate_selection


def example():
    return dict(paper_id='paper:invented',status='acquired',extraction_status='parsed',
        roster={'title':'Synthetic title','authors':['Alpha One','Beta Two']},
        official={'authors':['Alpha One','Beta Two']},header_title='Synthetic title',
        header_authors=[{'name':'Alpha One','affiliations':[
            {'institutions':['First University','Second Institute'],'locator':'author[1]/affiliation[1]'}]},
            {'name':'Beta Two','affiliations':[{'institutions':['Third University'],'locator':'author[2]/affiliation[1]'}]}],
        openalex_work={'authorships':[
            {'author':{'display_name':'Alpha One'},'institutions':[{'id':'I1','display_name':'First University'},{'id':'I2','display_name':'Second Institute'}]},
            {'author':{'display_name':'Beta Two'},'institutions':[{'id':'I3','display_name':'Third University'}]}]},
        pdf_source={'sha256':'a'*64},tei_source={'sha256':'b'*64})


def test_multi_affiliation_candidates_remain_per_author_and_unaccepted():
    result=source_triage(example());obs=result['affiliation_candidates']
    assert [(o['byline_position'],o['openalex_institution_id']) for o in obs]==[(1,'I1'),(1,'I2'),(2,'I3')]
    assert all(o['validation_status']=='review' and o['identity_status']=='unresolved' for o in obs)
    assert result['accepted_affiliation_triples']==result['accepted_identities']==0


def test_institution_on_another_author_is_never_borrowed():
    record=example();record['header_authors'][0]['affiliations'][0]['institutions']=['Third University']
    first=source_triage(record)['affiliation_candidates'][0]
    assert first['openalex_institution_id'] is None


@pytest.mark.parametrize('failure',['duplicate_name','wrong_order','wrong_title','withheld','truncated_provider'])
def test_ambiguous_or_withheld_evidence_never_binds_institutions(failure):
    r=example()
    if failure=='duplicate_name':
        r['roster']['authors']=r['official']['authors']=['Alpha One','Alpha One']
        r['header_authors'][1]['name']='Alpha One'
    elif failure=='wrong_order':r['header_authors'].reverse()
    elif failure=='wrong_title':r['header_title']='Different paper'
    elif failure=='withheld':r['status']='failed'
    else:r['openalex_work']['authorships'].pop()
    result=source_triage(r)
    assert all(o['openalex_institution_id'] is None for o in result['affiliation_candidates'])
    if failure=='withheld':assert result['disposition']=='retain_withheld'


def test_repeated_printed_support_is_deduplicated_with_all_locators():
    r=example();aff=deepcopy(r['header_authors'][0]['affiliations'][0]);aff['locator']='author[1]/affiliation[2]'
    r['header_authors'][0]['affiliations'].append(aff)
    observations=source_triage(r)['affiliation_candidates']
    assert len(observations)==3 and len(observations[0]['locators'])==2


def selection_fixture(tmp_path):
    diagnostic=tmp_path/'config.yaml';diagnostic.write_text('synthetic: true\n')
    manifest=tmp_path/'manifest.jsonl';row=dict(paper_id='one',status='included',title='Synthetic',official_url='https://example.org/one',pdf_url=None)
    write_jsonl(manifest,[row]);splits=tmp_path/'splits';splits.mkdir()
    membership=[dict(paper_id='one',split='development',leakage_group=title_group('Synthetic'))]
    write_jsonl(splits/'membership.jsonl',membership);write_jsonl(splits/'diagnostics.jsonl',[{'paper_id':'one'}]);write_jsonl(splits/'reserved-tests.jsonl',[])
    frozen={'manifest_sha256':digest(manifest.read_bytes()),'config_sha256':digest(diagnostic.read_bytes()),'input_sha256':{}}
    for name,key in [('membership','membership_sha256'),('diagnostics','diagnostics_sha256'),('reserved-tests','reserved_tests_sha256')]:frozen[key]=digest((splits/(name+'.jsonl')).read_bytes())
    write_json(splits/'summary.json',frozen)
    acquisition=tmp_path/'acquisition';acquisition.mkdir();papers=acquisition/'papers.json';write_json(papers,[{'paper_id':'one','status':'acquired','roster':row}]);write_json(acquisition/'summary.json',{**frozen,'papers_sha256':digest(papers.read_bytes())})
    return papers,manifest,splits,{'diagnostic_config':str(diagnostic),'max_papers':1}


def test_selection_checks_all_frozen_files_before_requests(tmp_path):
    args=selection_fixture(tmp_path)
    assert len(validate_selection(*args)[0])==1
    (args[2]/'reserved-tests.jsonl').write_text('{}\n')
    with pytest.raises(ValueError,match='frozen'):validate_selection(*args)


def test_heldout_leakage_group_is_rejected_even_with_updated_file_hash(tmp_path):
    args=selection_fixture(tmp_path);splits=args[2]
    members=[json.loads(x) for x in (splits/'membership.jsonl').read_text().splitlines()]
    members.append(dict(paper_id='held-out-version',split='test',leakage_group=members[0]['leakage_group']))
    path=splits/'membership.jsonl';path.write_text(''.join(json.dumps(x)+'\n' for x in members))
    frozen=json.loads((splits/'summary.json').read_text());frozen['membership_sha256']=digest(path.read_bytes());(splits/'summary.json').write_text(json.dumps(frozen))
    with pytest.raises(ValueError,match='held-out'):validate_selection(*args)
