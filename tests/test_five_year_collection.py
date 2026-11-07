"""Invented source snippets only; tests perform no network requests."""
import json
from pathlib import Path

import httpx
import pytest
import yaml

from scientific_network.cli import main
from scientific_network.collect.five_year import edition_routes, parse_five_year, discover_five_year
from scientific_network.collect.storage import SourceCache

SOURCE = {'url': 'https://example.org/', 'sha256': 'a'*64, 'retrieved_at': '2026-11-06T00:00:00Z'}


def conference(slug, adapter):
    return dict(venue_id=f'venue:{slug}', name=slug, adapter=adapter, source_catalog='https://example.org/')


def edition(slug='neurips', year=2021, **kwargs):
    return dict(venue_id=f'venue:{slug}', name=slug, adapter=slug, year=year,
                official_index=f'https://example.org/paper/{year}', include_tracks=['main'],
                exclude_tracks=['nonresearch','datasets_and_benchmarks'], **kwargs)


def test_pmlr_uses_exact_conference_year_not_workshop_or_publication_date():
    body=b'''<ul class="proceedings-list">
    <li><a href="v164">Volume 164</a> Proceedings of CoRL 2021</li>
    <li><a href="v184">Volume 184</a> Proceedings of ICML 2022 Workshop on Examples</li>
    <li><a href="v162">Volume 162</a> Proceedings of ICML 2022</li></ul>'''
    assert edition_routes(body,conference('corl','pmlr'),2021)[0]['volume']==164
    assert edition_routes(body,conference('corl','pmlr'),2022)==[]
    assert len(edition_routes(body,conference('icml','pmlr'),2022))==1


def test_neurips_2025_uses_main_conference_not_creative_ai():
    body=b'''<a href="/paper_files/paper/2025">Creative AI</a>
    <a href="/paper_files/paper/2025/vol38-main-conference">Main Conference</a>'''
    routes=edition_routes(body,conference('neurips','neurips'),2025)
    assert len(routes)==1 and routes[0]['official_index'].endswith('main-conference')


def test_acl_volumes_exclude_findings_and_require_complete_long_short():
    body=b'''<a href="/volumes/2025.acl-long/">Long Papers</a><a href="/volumes/2025.acl-short/">Short</a>
    <a href="/volumes/2025.findings-acl/">Findings</a><a href="/volumes/2025.acl-industry/">Industry</a>'''
    assert len(edition_routes(body,conference('acl','acl'),2025))==2
    with pytest.raises(ValueError,match='incomplete long/short'):
        edition_routes(b'<a href="/2021.acl-long/">Long</a>',conference('acl','acl'),2021)
    assert edition_routes(body,conference('acl','acl'),2021)==[]


def test_neurips_retains_unicode_same_name_authors_without_identity_merging():
    body='''2021<li><div class="paper-content"><a href="/2021/hash/abc-Abstract.html">Example</a>
    <span class="paper-authors">Nguyễn An, Alex Lee, Alex Lee</span></div></li>'''.encode()
    row=parse_five_year(body,edition(),SOURCE)[0]
    assert row['authors']==['Nguyễn An','Alex Lee','Alex Lee']
    assert row['status']=='included' and row['paper_id']=='paper:neurips:2021:abc'
    assert 'researcher_id' not in row


def test_neurips_mixed_track_and_unknown_track_do_not_enter_core():
    body=b'''2024<li data-track="conference"><a href="/2024/hash/a-Abstract.html">A</a><i>Alpha</i></li>
    <li data-track="datasetsandbenchmarks"><a href="/2024/hash/b-Abstract.html">B</a><i>Beta</i></li>
    <li><a href="/2024/hash/c-Abstract.html">C</a><i>Gamma</i></li>'''
    assert [r['status'] for r in parse_five_year(body,edition(year=2024),SOURCE)]==['included','excluded','review']
    with pytest.raises(ValueError,match='expected edition year'):
        parse_five_year(body,edition(year=2022),SOURCE)


def test_ecva_requires_heading_and_url_agreement():
    body=b'''<h3>ECCV 2024 Papers</h3><dl><dt class="ptitle"><a href="papers/eccv_2024/paper1.php">Example</a></dt><dd>Alpha, Beta</dd></dl>'''
    row=parse_five_year(body,edition(slug='ecva',year=2024),SOURCE)[0]
    assert row['authors']==['Alpha','Beta']
    with pytest.raises(ValueError,match='heading'):
        parse_five_year(body.replace(b'ECCV 2024 Papers',b'2024 Other Papers'),edition(slug='ecva',year=2024),SOURCE)


def test_resume_binds_config_and_checks_roster_hash(tmp_path,monkeypatch):
    config=yaml.safe_load(Path('configs/corpus-five-year-v1.yaml').read_text())
    config['retrieval']['series_workers']=1
    # No source routes: all candidates remain explicit unresolved rows, never no-edition.
    for c in config['conferences']:c['adapter']=None
    cp=tmp_path/'config.yaml';cp.write_text(yaml.safe_dump(config))
    calls=[]
    def get(self,url,**kwargs):
        calls.append(url);return b'<html>Public catalog</html>',SOURCE
    monkeypatch.setattr(SourceCache,'get',get)
    out=tmp_path/'out'
    result=discover_five_year(cp,out,tmp_path/'cache')
    assert result['candidate_editions']==170 and result['incomplete_editions']==170
    assert result['edition_statuses']=={'unresolved':170}
    assert discover_five_year(cp,out,tmp_path/'cache')==result
    assert len(calls)==34
    roster=next((out/'editions').rglob('roster.jsonl'));roster.write_text('{}\n')
    with pytest.raises(ValueError,match='checkpoint roster hash'):
        discover_five_year(cp,out,tmp_path/'cache')
    cp.write_text(cp.read_text()+'\n')
    with pytest.raises(ValueError,match='overwrite different artifact'):
        discover_five_year(cp,out,tmp_path/'cache')


def test_failed_second_acl_page_blocks_entire_edition(tmp_path,monkeypatch):
    config=yaml.safe_load(Path('configs/corpus-five-year-v1.yaml').read_text());config['retrieval']['series_workers']=1
    for c in config['conferences']:c['adapter']=None
    next(c for c in config['conferences'] if c['venue_id']=='venue:acl')['adapter']='acl'
    catalog=b'<a href="/2021.acl-long/">Long</a><a href="/2021.acl-short/">Short</a>'
    def get(self,url,**kwargs):
        if url.endswith('2021.acl-short/'):
            from scientific_network.collect.storage import SourceError
            raise SourceError('example.org: HTTP 503')
        if url.endswith('2021.acl-long/'):
            return b'''2021<span class="d-block"><strong><a href="/2021.acl-long.1/">Example</a></strong><a href="/people/a/">Alpha</a></span>''',SOURCE
        return catalog,SOURCE
    monkeypatch.setattr(SourceCache,'get',get)
    cp=tmp_path/'config.yaml';cp.write_text(yaml.safe_dump(config))
    result=discover_five_year(cp,tmp_path/'out',tmp_path/'cache')
    assert result['roster_records']==1 and result['eligible_included_records']==0
    ledger=json.loads((tmp_path/'out/editions/acl/2021/summary.json').read_text())
    assert ledger['status']=='access_unavailable'


def test_roster_only_config_cannot_dispatch_legacy_split(tmp_path,capsys):
    rc=main(['split','--input',str(tmp_path/'absent.jsonl'),'--corpus-config',
             'configs/corpus-five-year-v1.yaml','--output',str(tmp_path/'out')])
    assert rc==1 and not (tmp_path/'out').exists()
    assert 'discovery only' in capsys.readouterr().err


def test_leakage_triage_preserves_assignments_and_quarantines_mixed_exposure():
    from scientific_network.collect.reconcile import leakage_triage
    old=[dict(paper_id='old-test',title='Shared Work',status='included'),
         dict(paper_id='old-dev',title='Shared Work',status='included'),
         dict(paper_id='old-alone',title='Other Work',status='included')]
    membership=[dict(paper_id='old-test',split='test',is_pilot=False),
                dict(paper_id='old-dev',split='development',is_pilot=True),
                dict(paper_id='old-alone',split='pool',is_pilot=False)]
    def new(pid,title):return dict(paper_id=pid,title=title,status='included',venue_id='venue:sample',year=2025,authors=['Alex Lee'])
    rows=leakage_triage([new('new-version','Shared Work'),new('old-alone','Other Work'),new('unrelated','Unrelated Work')],old,membership)
    found={r['paper_id']:r for r in rows}
    assert found['new-version']['action']=='quarantine_mixed_historical_exposure'
    assert found['old-alone']['existing_assignment']==membership[-1]
    assert found['unrelated']['action']=='pending_prospective_design'
    assert all(r['canonical_work_id'] is None and not r['is_new_split'] for r in rows)


def test_leakage_triage_doi_versions_remain_held_out_without_name_merging():
    from scientific_network.collect.reconcile import leakage_triage
    old=[dict(paper_id='old',title='Original Title',doi='10.1234/example')]
    membership=[dict(paper_id='old',split='test',is_pilot=False)]
    row=dict(paper_id='new',title='Different Title',doi='https://doi.org/10.1234/EXAMPLE',
             status='included',venue_id='venue:sample',year=2025,authors=['Same Name'])
    output=leakage_triage([row],old,membership)
    assert output[0]['action']=='held_out_version_guard'
    assert output[0]['candidate_paper_ids']==['new','old']
    assert membership[0]['split']=='test'
