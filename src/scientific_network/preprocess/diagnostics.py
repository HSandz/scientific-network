"""Input-bound development PDF headers and non-adjudicating source triage."""
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

from dotenv import load_dotenv
import httpx

from scientific_network.collect.acquire import official_metadata, names_compatible
from scientific_network.collect.diagnostic_acquire import title_key
from scientific_network.collect.splits import title_group
from scientific_network.collect.storage import (
    SourceCache, SourceError, QuotaError, digest, read_config, read_jsonl,
    write_bytes, write_json,
)
from scientific_network.preprocess.extract import request_header
from scientific_network.preprocess.tei import parse_header, NS, text

VERSION = 'five-year-development-headers-v1'


def validate_selection(input_path: Path, manifest: Path, splits: Path, config: dict):
    """Reject any changed frozen input or held-out/version exposure before I/O."""
    frozen = json.loads((splits/'summary.json').read_text())
    expected = {'manifest_sha256': digest(manifest.read_bytes()),
                'config_sha256': digest(Path(config['diagnostic_config']).read_bytes())}
    for name, key in [('membership.jsonl','membership_sha256'),
                      ('diagnostics.jsonl','diagnostics_sha256'),
                      ('reserved-tests.jsonl','reserved_tests_sha256')]:
        expected[key] = digest((splits/name).read_bytes())
    if any(frozen.get(k) != v for k,v in expected.items()):
        raise ValueError('frozen diagnostic inputs changed')
    for name, value in frozen['input_sha256'].items():
        if digest(Path(name).read_bytes()) != value:
            raise ValueError('protected sampling input changed: '+name)
    selected = read_jsonl(splits/'diagnostics.jsonl')
    ids = {r['paper_id'] for r in selected}
    membership = read_jsonl(splits/'membership.jsonl')
    assigned = {r['paper_id']:r for r in membership}
    if len(assigned) != len(membership):raise ValueError('duplicate membership ID')
    records = json.loads(input_path.read_text())
    if not ids or len(ids) != len(selected) or len(ids) > config['max_papers']:
        raise ValueError('missing/duplicate/excess diagnostic selection')
    if len(records) != len(ids) or {r['paper_id'] for r in records} != ids:
        raise ValueError('extraction requires exactly the frozen diagnostic IDs')
    heldgroups = {r['leakage_group'] for r in membership if r['split']=='test'}
    roster = {r['paper_id']:r for r in read_jsonl(manifest)}
    for record in records:
        pid = record['paper_id']
        if assigned[pid]['split'] != 'development' or assigned[pid]['leakage_group'] in heldgroups:
            raise ValueError('held-out paper/group cannot enter extraction')
        if record['roster'] != roster[pid] or roster[pid]['status'] != 'included':
            raise ValueError('acquired roster differs from frozen included record')
        if title_group(roster[pid]['title']) in heldgroups:
            raise ValueError('held-out title group overlaps extraction')
    acquisition = json.loads((input_path.parent/'summary.json').read_text())
    if acquisition['papers_sha256'] != digest(input_path.read_bytes()) or any(
        acquisition.get(k) != v for k,v in expected.items() if k != 'reserved_tests_sha256'
    ):
        raise ValueError('acquisition hash/prospective sample mismatch')
    heldurls = {row[key].rstrip('/') for pid,row in roster.items()
                if pid in assigned and assigned[pid]['split']=='test'
                for key in ('official_url','pdf_url') if row.get(key)}
    return records, expected, heldurls


def ordered_byline(left: list[str], right: list[str]) -> bool:
    return bool(left) and len(left)==len(right) and all(names_compatible(a,b) for a,b in zip(left,right))


def source_triage(record: dict) -> dict:
    """Candidate author-paper-organization observations, never accepted triples."""
    row = record['roster']; headers = record.get('header_authors',[])
    names = [h['name'] for h in headers]
    roster_agrees = ordered_byline(row['authors'],names)
    detail = record.get('source_review_official') or record.get('official') or {}
    detail_agrees = ordered_byline(detail.get('authors',[]),names)
    unique = len({title_key(n) for n in names})==len(names)
    title_agrees = bool(record.get('header_title')) and title_key(record['header_title'])==title_key(row['title'])
    bindable = record['status']=='acquired' and record.get('extraction_status')=='parsed' and roster_agrees and detail_agrees and unique and title_agrees
    work = record.get('openalex_work') or {}
    authorships = work.get('authorships',[])
    provider_aligned = ordered_byline(row['authors'],[a['author']['display_name'] for a in authorships])
    observations = {}
    for pos, author in enumerate(headers,1):
        for aff in author['affiliations']:
            for printed in aff['institutions']:
                matches = {}
                if bindable and provider_aligned:
                    matches = {i['id']:i for i in authorships[pos-1].get('institutions',[])
                               if title_key(printed) and title_key(printed)==title_key(i.get('display_name',''))}
                inst = next(iter(matches.values())) if len(matches)==1 else None
                oid = 'candidate-affiliation:'+digest(json.dumps([record['paper_id'],pos,printed],ensure_ascii=False).encode())
                observation = observations.setdefault(oid,dict(observation_id=oid,paper_id=record['paper_id'],
                    byline_position=pos,header_name=author['name'],printed_institution=printed,
                    openalex_institution_id=inst['id'] if inst else None,
                    disposition='candidate_exact_authorship_match' if inst else 'needs_source_review',
                    author_binding='ordered_complete_byline' if bindable else 'unresolved',
                    pdf_sha256=record.get('pdf_source',{}).get('sha256'),
                    tei_sha256=record.get('tei_source',{}).get('sha256'),locators=[],
                    validation_status='review',identity_status='unresolved',
                    method_version=VERSION,independent_review=False))
                if aff['locator'] not in observation['locators']:observation['locators'].append(aff['locator'])
    return dict(paper_id=record['paper_id'],acquisition_status=record['status'],
        extraction_status=record.get('extraction_status'),header_title_agrees=title_agrees,
        ordered_roster_byline_agrees=roster_agrees,ordered_detail_byline_agrees=detail_agrees,
        header_names_unique=unique,ordered_provider_byline_agrees=provider_aligned,
        candidate_binding_available=bindable,
        disposition='retain_withheld' if record['status']!='acquired' else 'development_candidates_only',
        affiliation_candidates=list(observations.values()),accepted_identities=0,
        accepted_affiliation_triples=0,independent_review=False,method_version=VERSION)


def extract_diagnostics(input_path: Path, manifest: Path, splits: Path,
                        config_path: Path, output: Path, cache_path: Path) -> dict:
    load_dotenv('.env',override=False)
    config = read_config(config_path)
    if (config.get('collection_authorized') is not True or config['pdf']['consolidate_header'] != 0
        or config['review'].get('automatic_identity_acceptance') is not False
        or config['review'].get('automatic_affiliation_acceptance') is not False
        or config['review'].get('preserve_withheld_status') is not True):
        raise ValueError('development extraction requires disabled consolidation/acceptance and preserved withholding')
    records, frozen, heldurls = validate_selection(input_path,manifest,splits,config)
    signature = dict(method_version=VERSION,input_sha256=digest(input_path.read_bytes()),
        extraction_config_sha256=digest(config_path.read_bytes()),**frozen)
    write_json(output/'inputs.json',signature)
    remaining = [r for r in records if not (output/'records'/(digest(r['paper_id'].encode())+'.json')).exists()]
    url = os.environ.get('GROBID_URL','http://localhost:8070').rstrip('/')
    cfg = config['pdf']
    result=[]; stopped_hosts=set()
    with SourceCache(cache_path,attempts=cfg['max_attempts'],timeout=30,delay=cfg['delay_seconds']) as cache, httpx.Client(timeout=cfg['timeout_seconds']) as client:
        if remaining:
            try: health=client.get(url+'/api/isalive')
            except httpx.HTTPError as exc:raise SourceError('GROBID preflight: '+type(exc).__name__) from None
            if health.status_code!=200 or health.text.strip()!='true':raise SourceError('GROBID preflight failed')
        for index, original in enumerate(records,1):
            path=output/'records'/(digest(original['paper_id'].encode())+'.json')
            original_sha=digest(json.dumps(original,sort_keys=True,ensure_ascii=False).encode())
            if path.exists():
                record=json.loads(path.read_text())
                if record.get('original_record_sha256')!=original_sha:raise ValueError('extraction checkpoint input changed')
                result.append(record);continue
            record=dict(original,original_record_sha256=original_sha,extraction_method_version=VERSION)
            started=time.monotonic()
            try:
                official=record.get('official')
                if record['status']!='acquired':
                    if not config.get('include_withheld_source_review'):raise ValueError('withheld PDF review disabled')
                    body,source=cache.get(record['roster']['official_url'])
                    official=official_metadata(body,record['roster'])
                    if title_key(official['title'])!=title_key(record['roster']['title']):raise ValueError('withheld source title mismatch')
                    record.update(source_review_official=official,source_review_source=source)
                pdf_url=(official or {}).get('pdf_url')
                if not pdf_url:raise ValueError('official PDF URL missing')
                if pdf_url.rstrip('/') in heldurls:raise ValueError('PDF URL links held-out official record')
                host=urlsplit(pdf_url).netloc
                if host in stopped_hosts:raise SourceError('PDF host access stopped in this batch')
                try: pdf,pdf_source=cache.get(pdf_url)
                except QuotaError:
                    stopped_hosts.add(host);raise
                if not pdf.startswith(b'%PDF'):raise ValueError('official PDF endpoint returned non-PDF content')
                record.update(pdf_source=pdf_source,pdf_size_bytes=len(pdf))
                key=digest(f'{VERSION}|{pdf_source["sha256"]}|consolidate=0'.encode())
                meta=cache_path/'requests'/(key+'.json')
                if meta.exists():
                    tei_source=json.loads(meta.read_text());tei=(cache_path/'objects'/tei_source['sha256']).read_bytes()
                    if digest(tei)!=tei_source['sha256']:raise ValueError('TEI cache hash mismatch')
                else:
                    tei=request_header(client,url,cfg['header_endpoint'],pdf)
                    tei_source=dict(url=pdf_url,sha256=digest(tei),pdf_sha256=pdf_source['sha256'],
                        retrieved_at=datetime.now(timezone.utc).isoformat(),method_version=VERSION,consolidateHeader=0)
                    write_bytes(cache_path/'objects'/tei_source['sha256'],tei);write_json(meta,tei_source)
                root=ET.fromstring(tei)
                record.update(tei_source=tei_source,header_authors=parse_header(tei),
                    header_title=text(root.find('.//t:sourceDesc/t:biblStruct/t:analytic/t:title',NS)),extraction_status='parsed')
            except (SourceError,ValueError,ET.ParseError,httpx.HTTPError) as exc:
                record.update(extraction_status='review',extraction_reason=type(exc).__name__ if isinstance(exc,httpx.HTTPError) else str(exc),header_authors=[])
            record['extraction_seconds']=round(time.monotonic()-started,3)
            write_json(path,record);result.append(record)
            print(f'extract-diagnostics: {index}/{len(records)}: {record["extraction_status"]}',flush=True)
    reviews=[source_triage(r) for r in result]
    write_json(output/'papers.json',result);write_json(output/'source-review.json',reviews)
    candidates=[o for r in reviews for o in r['affiliation_candidates']]
    summary=dict(stage='extract-diagnostics',**signature,selected_papers=len(result),
        by_status=dict(Counter(r['extraction_status'] for r in result)),
        review_reasons=dict(Counter(r['extraction_reason'] for r in result if r['extraction_status']=='review')),
        pdfs_available=sum('pdf_source' in r for r in result),pdf_bytes=sum(r.get('pdf_size_bytes',0) for r in result),
        by_year={str(y):dict(Counter(r['extraction_status'] for r in result if r['roster']['year']==y)) for y in sorted({r['roster']['year'] for r in result})},
        papers_with_header_affiliations=sum(any(h['affiliations'] for h in r.get('header_authors',[])) for r in result),
        roster_byline_agreements=sum(r['ordered_roster_byline_agrees'] for r in reviews),
        title_agreements=sum(r['header_title_agrees'] for r in reviews),
        candidate_binding_papers=sum(r['candidate_binding_available'] for r in reviews),
        candidate_affiliation_observations=len(candidates),
        exact_authorship_institution_candidates=sum(o['disposition']=='candidate_exact_authorship_match' for o in candidates),
        withheld_records_preserved=sum(r['status']!='acquired' for r in result),held_out_papers_acquired=0,
        accepted_identities=0,accepted_affiliation_triples=0,graph_imports=0,
        external_consolidation=False,semantic_accuracy='not_measured',independent_review=False,
        papers_sha256=digest((output/'papers.json').read_bytes()),source_review_sha256=digest((output/'source-review.json').read_bytes()))
    write_json(output/'summary.json',summary)
    return summary
