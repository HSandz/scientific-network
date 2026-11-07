"""Invented five-year source/sample evidence. No network or scientific score claims."""
import json
from pathlib import Path
import pytest
from scientific_network.collect.five_year_v2 import parse_v2,routes_v2

SOURCE={'url':'https://example.org/','sha256':'b'*64,'retrieved_at':'2026-11-06T00:00:00Z'}

def edition(family,year=2025,**extra):
    return dict(adapter=family,venue_id='venue:'+family,name=family,year=year,
        official_index='https://example.org/',include_tracks=['main'],
        exclude_tracks=['nonresearch','datasets_and_benchmarks'],**extra)


def test_neurips_position_and_dataset_tracks_are_excluded():
    body=b'''2025<li data-track="conference"><a href="/2025/hash/a-Abstract.html">A</a><i>Alpha</i></li>
    <li data-track="position_paper_track"><a href="/2025/hash/b-Abstract.html">B</a><i>Beta</i></li>
    <li data-track="datasets_and_benchmarks_track"><a href="/2025/hash/c-Abstract.html">C</a><i>Gamma</i><span>Datasets and Benchmarks Track</span></li>'''
    rows=parse_v2(body,edition('neurips'),SOURCE)
    assert [r['status'] for r in rows]==['included','excluded','excluded']
    assert rows[1]['track']=='position_paper_track'


def test_complete_manifest_keeps_late_optional_fields_and_old_mirror(tmp_path):
    import pyarrow.parquet as pq
    from scientific_network.collect.five_year_v2 import write_complete_manifest
    path=tmp_path/'corpus_manifest.parquet'
    path.write_bytes(b'preserve original mirror')
    rows=[{'paper_id':'first','title':'Synthetic'},
          {'paper_id':'later','title':'Synthetic KR','track_section':'Full Papers'}]
    write_complete_manifest(path,rows)
    table=path.with_name('corpus_manifest-complete.parquet')
    assert pq.read_table(table).to_pylist()==[
        {'paper_id':'first','title':'Synthetic','track_section':None},rows[1]]
    original=table.read_bytes()
    write_complete_manifest(path,rows)
    assert table.read_bytes()==original
    assert path.read_bytes()==b'preserve original mirror'
    with pytest.raises(ValueError,match='refusing'):
        write_complete_manifest(path,[dict(rows[0],title='changed'),rows[1]])


def test_ecva_accordion_year_and_pdf_link_are_required():
    body=b'''<button class="accordion">ECCV 2024 Papers</button><div class="accordion-content"><dl>
    <dt class="ptitle"><a href="papers/eccv_2024/papers/html/1.php">Example</a></dt><dd>Alpha*, Beta</dd>
    <dd><a href="papers/eccv_2024/papers/1.pdf">pdf</a><a href="papers/eccv_2024/papers/1-supp.pdf">supp</a></dd></dl></div>'''
    row=parse_v2(body,edition('ecva',2024),SOURCE)[0]
    assert row['authors']==['Alpha*','Beta'] and row['pdf_url'].endswith('/1.pdf')
    with pytest.raises(ValueError,match='disagree'):
        parse_v2(body.replace(b'ECCV 2024 Papers',b'ECCV 2022 Papers'),edition('ecva',2024),SOURCE)


def test_rss_requires_catalog_year_and_matching_roman_edition():
    conf={'adapter':'rss','venue_id':'venue:rss','name':'RSS','source_catalog':'https://example.org/'}
    cat=b'<div>Robotics: Science and Systems XIX July 2023 <a href="rss19/index.html">Content</a></div>'
    route=routes_v2(cat,conf,2023)[0]
    body=b'<h1>Robotics: Science and Systems XIX</h1><table><tr><td><a href="p001.html">Example</a><i>Alpha, Beta</i></td></tr></table>'
    assert parse_v2(body,route,SOURCE)[0]['year']==2023
    with pytest.raises(ValueError,match='corroboration'):
        parse_v2(body,{**route,'catalog_verified_year':None},SOURCE)
    with pytest.raises(ValueError,match='expected edition marker'):
        parse_v2(body.replace(b'XIX',b'XVIII'),route,SOURCE)


def test_kr_full_short_main_and_other_sections_remain_distinct():
    def p(n):return f'<div class="paperinfo"><a href="/2021/{n}/">Example {n}</a><ol><li>Alpha</li></ol></div>'
    body=('<h1>KR2021</h1><h2>Full Papers</h2>'+p(1)+'<h2>Short Papers</h2>'+p(2)+'<h2>Applications and Systems</h2>'+p(3)+'<h2>Unknown New Track</h2>'+p(4)).encode()
    rows=parse_v2(body,edition('kr',2021),SOURCE)
    assert [r['status'] for r in rows]==['included','included','excluded','review']


def sample_fixture():
    from scientific_network.collect.reconcile import leakage_triage
    rows=[dict(paper_id=f'paper:new:{i}',venue_id='venue:icml',year=2024,title=f'Invented {i}',authors=['Same Name'],status='included') for i in range(20)]
    history=[dict(paper_id='old-test',title='Frozen Example')]
    previous=[dict(paper_id='old-test',venue_id='venue:icml',leakage_group='frozen-group',split='test',is_pilot=False)]
    triage=leakage_triage(rows,history,previous)
    ledger=[dict(venue_id='venue:icml',year=2024,status='verified_eligible',routes=[{'adapter':'pmlr'}])]
    cfg={'seed':20261106,'test_groups_per_stratum':5,'diagnostic_groups_per_stratum':2,'metadata':{'max_papers':100}}
    return rows,ledger,triage,previous,cfg


def test_prospective_sample_preserves_old_test_and_records_probabilities():
    from scientific_network.collect.diagnostics import allocate_diagnostics
    args=sample_fixture();members,selected,frames=allocate_diagnostics(*args)
    assert next(r for r in members if r['paper_id']=='old-test')==args[3][0]
    assert len(selected)==2 and frames[0]['population']==20
    assert frames[0]['test_probability']==5/20
    assert all(r['selection_probability']==2/20 for r in selected)
    tests={r['paper_id'] for r in members if r['split']=='test'}
    assert len(tests)==6 and not tests & {r['paper_id'] for r in selected}
    assert allocate_diagnostics(*args)==(members,selected,frames)


def test_incomplete_editions_and_version_candidates_cannot_enter_new_sample():
    from scientific_network.collect.diagnostics import allocate_diagnostics
    rows,ledger,triage,old,cfg=sample_fixture()
    triage[0].update(action='quarantine_version_candidate',candidate_paper_ids=['paper:new:0','historical-other'])
    members,selected,frames=allocate_diagnostics(rows,ledger,triage,old,cfg)
    assert next(r for r in members if r['paper_id']=='paper:new:0')['split']=='review'
    assert frames[0]['population']==19
    with pytest.raises(ValueError,match='no independent'):
        allocate_diagnostics(rows,[{**ledger[0],'status':'needs_review'}],triage,old,cfg)


def test_insufficient_stratum_never_silently_lowers_sample_size():
    from scientific_network.collect.diagnostics import allocate_diagnostics
    rows,ledger,triage,old,cfg=sample_fixture()
    subset={r['paper_id'] for r in rows[:6]}
    with pytest.raises(ValueError,match='insufficient'):
        allocate_diagnostics(rows[:6],ledger,[r for r in triage if r['paper_id'] in subset],old,cfg)


def test_provider_shared_work_and_test_locations_are_quarantined():
    from scientific_network.collect.diagnostic_acquire import quarantine_provider_conflicts
    records=[{'paper_id':str(i),'status':'acquired','openalex_work':{'id':'W1','locations':[]}} for i in range(2)]
    output=quarantine_provider_conflicts(records,set())
    assert all(r['status']=='review' for r in output)
    assert all(r['status']=='acquired' for r in records)
    record={'paper_id':'x','status':'acquired','openalex_work':{'id':'W2','locations':[{'landing_page_url':'https://example.org/held-out/'}]}}
    assert quarantine_provider_conflicts([record],{'https://example.org/held-out'})[0]['status']=='review'


def test_non_latin_titles_and_truncated_byline_do_not_match_accidentally():
    from scientific_network.collect.diagnostic_acquire import work_match,title_key
    paper={'title':'深度学习','year':2024,'authors':['Alpha Person']}
    work={'id':'W1','title':'不同研究','publication_year':2024,'authorships':[{'author':{'display_name':'Alpha Person'}}]}
    assert title_key(paper['title'])!=title_key(work['title'])
    assert work_match([work],paper,'https://example.org')[0] is None
    work.update(title=paper['title'],is_authors_truncated=True)
    assert work_match([work],paper,'https://example.org')[0] is None


def test_quota_preflight_refuses_unknown_contract_or_insufficient_free_allowance(monkeypatch):
    from scientific_network.collect.diagnostic_acquire import quota_check
    from scientific_network.collect.storage import QuotaError
    import httpx
    monkeypatch.setattr(httpx,'get',lambda *a,**k:httpx.Response(200,json={'rate_limit':{'daily_remaining_usd':.01,'daily_budget_usd':1,'endpoint_costs_usd':{'search':.001}}}))
    with pytest.raises(QuotaError,match='exceeds'):
        quota_check('invented-test-key',max_queries=100,attempts=2)
    monkeypatch.setattr(httpx,'get',lambda *a,**k:httpx.Response(200,json={}))
    with pytest.raises(ValueError,match='unknown'):
        quota_check('invented-test-key',max_queries=2,attempts=2)


def test_acquisition_rejects_changed_frozen_selection_before_network(tmp_path,monkeypatch):
    from scientific_network.collect.diagnostic_acquire import acquire_diagnostics
    from scientific_network.collect.storage import digest
    import yaml,httpx
    config=tmp_path/'config.yaml';config.write_text(yaml.safe_dump({'metadata':{}}))
    manifest=tmp_path/'corpus.jsonl';manifest.write_text('{}\n')
    splits=tmp_path/'splits';splits.mkdir();(splits/'membership.jsonl').write_text('{}\n')
    (splits/'summary.json').write_text(json.dumps({'config_sha256':digest(config.read_bytes()),'manifest_sha256':digest(manifest.read_bytes()),'membership_sha256':'f'*64}))
    monkeypatch.setattr(httpx,'get',lambda *a,**k:pytest.fail('network before input validation'))
    with pytest.raises(ValueError,match='membership/selection hash'):
        acquire_diagnostics(manifest,splits,config,tmp_path/'out',tmp_path/'cache')
