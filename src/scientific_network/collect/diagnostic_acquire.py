"""Bounded metadata-only acquisition for a frozen five-year development sample."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlsplit

from dotenv import load_dotenv
import httpx
from bs4 import BeautifulSoup

from scientific_network.collect.acquire import official_metadata, choose_work, names_compatible
from scientific_network.collect.storage import (
    SourceCache, SourceError, QuotaError, digest, read_config, read_jsonl, write_json,
)

VERSION='five-year-diagnostic-metadata-v1'


def title_key(text: str) -> str:
    return re.sub(r'\W+','',unicodedata.normalize('NFKC',text).casefold())


def quota_check(key: str, *, max_queries: int, attempts: int) -> dict:
    if not key:raise ValueError('OpenAlex key must be configured in ignored .env or process environment')
    try:
        response=httpx.get('https://api.openalex.org/rate-limit',params={'api_key':key},timeout=20)
    except httpx.RequestError as exc:
        raise SourceError('OpenAlex quota preflight: '+type(exc).__name__) from None
    if response.status_code!=200:raise QuotaError(f'OpenAlex quota preflight HTTP {response.status_code}')
    limit=response.json().get('rate_limit',{})
    remaining=limit.get('daily_remaining_usd');cost=limit.get('endpoint_costs_usd',{}).get('search')
    budget=limit.get('daily_budget_usd')
    if not all(isinstance(v,(int,float)) and v>=0 for v in (remaining,cost,budget)) or cost<=0:
        raise ValueError('unknown OpenAlex free-allowance contract; cannot authorize requests')
    required=max_queries*attempts*cost
    if required>min(remaining,budget):raise QuotaError('bounded batch exceeds remaining daily free allowance')
    return {'checked_at':datetime.now(timezone.utc).isoformat(),'daily_budget_usd':budget,
            'daily_remaining_usd':remaining,'daily_used_usd':limit.get('daily_used_usd'),
            'search_cost_usd':cost,'worst_case_batch_allowance_usd':required,
            'free_allowance_only':True,'resets_at':limit.get('resets_at')}


def extract_metadata(body: bytes, row: dict) -> dict:
    paper=official_metadata(body,row)
    # The historical helper's name-layout special cases are 2023-specific. Apply
    # visible ACL byline authority consistently across the five-year ACL family.
    if row['venue_id'] in {'venue:acl','venue:naacl','venue:emnlp','venue:eacl','venue:coling'}:
        soup=BeautifulSoup(body,'html.parser')
        bylines=[p for p in soup.select('p.lead') if p.select('a[href^="/people/"]')]
        if len(bylines)>1:raise ValueError('ambiguous ACL visible byline')
        if bylines:
            paper['authors']=[a.get_text(' ',strip=True) for a in bylines[0].select('a[href^="/people/"]')]
            paper['author_locator']='p.lead a[href^="/people/"]';paper['authors_from_roster']=False
    if not title_key(paper['title']) or title_key(paper['title'])!=title_key(row['title']):
        raise ValueError('Unicode-preserving official roster/detail title mismatch')
    if len(paper['authors'])!=len(row['authors']) or not all(names_compatible(a,b) for a,b in zip(paper['authors'],row['authors'])):
        raise ValueError('official roster/detail ordered byline mismatch')
    return paper


def work_match(candidates: list[dict], paper: dict, url: str):
    filtered=[w for w in candidates if title_key(w.get('title') or '')==title_key(paper['title'])
              and not w.get('is_authors_truncated',False)]
    return choose_work(filtered,paper,url)


def quarantine_provider_conflicts(records: list[dict], held_out_urls: set[str]) -> list[dict]:
    copies=[dict(r) for r in records];groups=defaultdict(list)
    for row in copies:
        work=row.get('openalex_work')
        if not work:continue
        groups[work['id']].append(row)
        locations={loc.get('landing_page_url','').rstrip('/') for loc in work.get('locations',[])}
        if locations & {u.rstrip('/') for u in held_out_urls}:
            row.update(status='review',review_reason='provider_location_links_held_out_official_record')
    for group in groups.values():
        if len(group)>1:
            for row in group:row.update(status='review',review_reason='shared_provider_work_requires_version_review')
    return copies


def acquire_diagnostics(manifest: Path, splits: Path, config_path: Path, output: Path, cache_path: Path) -> dict:
    load_dotenv('.env',override=False)
    config=read_config(config_path);cfg=config['metadata']
    frozen=json.loads((splits/'summary.json').read_text())
    if frozen['config_sha256']!=digest(config_path.read_bytes()) or frozen['manifest_sha256']!=digest(manifest.read_bytes()):
        raise ValueError('frozen diagnostics config/manifest mismatch')
    for name,key in [('membership.jsonl','membership_sha256'),('diagnostics.jsonl','diagnostics_sha256')]:
        if digest((splits/name).read_bytes())!=frozen[key]:raise ValueError('frozen membership/selection hash changed')
    assignment={r['paper_id']:r for r in read_jsonl(splits/'membership.jsonl')}
    selected=read_jsonl(splits/'diagnostics.jsonl');ids={r['paper_id'] for r in selected}
    if len(ids)!=len(selected) or not ids or len(ids)>min(cfg['max_papers'],cfg['max_openalex_search_queries']):
        raise ValueError('diagnostic selection missing, duplicated or exceeds cap')
    if any(assignment[pid]['split']!='development' for pid in ids):raise ValueError('held-out paper cannot enter diagnostics')
    roster={r['paper_id']:r for r in read_jsonl(manifest)}
    if not ids<=roster.keys():raise ValueError('selected diagnostics absent from roster')
    heldout={roster[pid]['official_url'] for pid,r in assignment.items() if r['split']=='test' and pid in roster}
    signature={'method_version':VERSION,'manifest_sha256':digest(manifest.read_bytes()),
        'membership_sha256':frozen['membership_sha256'],'diagnostics_sha256':frozen['diagnostics_sha256'],
        'config_sha256':digest(config_path.read_bytes())}
    write_json(output/'inputs.json',signature)
    key=os.environ.get('OPENALEX_API_KEY','')
    # Quota is checked before any official detail/API enrichment. A successful
    # replay can use its recorded preflight and local records without new requests.
    quota_path=output/'quota-before.json'
    record_paths={pid:output/'records'/(digest(pid.encode())+'.json') for pid in ids}
    if not all(p.exists() for p in record_paths.values()):
        quota=quota_check(key,max_queries=len(ids),attempts=cfg['max_attempts'])
        if not quota_path.exists():write_json(quota_path,quota)
    elif not quota_path.exists():raise ValueError('missing original quota preflight')
    records=[];closed_hosts=set()
    with SourceCache(cache_path,timeout=cfg['timeout_seconds'],attempts=cfg['max_attempts'],delay=0.3) as cache:
        for index,pid in enumerate(sorted(ids),1):
            path=record_paths[pid];row=roster[pid]
            if path.exists():
                record=json.loads(path.read_text())
                if record.get('roster')!=row:raise ValueError('checkpoint roster mismatch')
                records.append(record);continue
            host=urlsplit(row['official_url']).netloc
            if host in closed_hosts:
                record={'paper_id':pid,'roster':row,'status':'failed','reason':'official_host_access_stopped_in_this_batch'}
            else:
                stage='official'
                try:
                    body,source=cache.get(row['official_url']);paper=extract_metadata(body,row)
                    stage='openalex'
                    data,oa_source=cache.get('https://api.openalex.org/works',params={
                        'search':paper['title'].replace('*',' '),'filter':f'publication_year:{row["year"]-1}-{row["year"]+1}',
                        'per_page':5},secret_params={'api_key':key})
                    candidates=json.loads(data).get('results',[]);work,decision=work_match(candidates,paper,row['official_url'])
                    record={'paper_id':pid,'roster':row,'official':paper,'official_source':source,
                        'openalex_work':work,'openalex_source':oa_source,'match_decision':decision,
                        'candidate_ids':[w['id'] for w in candidates],'status':'acquired',
                        'acquisition_method_version':VERSION,'identity_status':'unresolved_not_graph_evidence'}
                except QuotaError as exc:
                    if stage=='openalex' or '429' in str(exc):raise
                    closed_hosts.add(host);record={'paper_id':pid,'roster':row,'status':'failed','reason':str(exc)}
                except (SourceError,ValueError) as exc:
                    record={'paper_id':pid,'roster':row,'status':'failed','reason':str(exc)}
            write_json(path,record);records.append(record)
            print(f'acquire-diagnostics: {index}/{len(ids)}: {record["status"]}',flush=True)
    accepted=quarantine_provider_conflicts(records,heldout)
    write_json(output/'papers.json',accepted)
    summary={'stage':'acquire-diagnostics',**signature,'selected_papers':len(ids),
        'by_status':dict(Counter(r['status'] for r in accepted)),
        'work_matches':sum(bool(r.get('openalex_work')) and r['status']=='acquired' for r in accepted),
        'abstracts_available':sum(bool(r.get('official',{}).get('abstract')) and r['status']=='acquired' for r in accepted),
        'by_year':dict(Counter(str(roster[pid]['year']) for pid in ids)),
        'by_venue':dict(Counter(roster[pid]['venue_id'] for pid in ids)),
        'pdfs_downloaded':0,'held_out_papers_acquired':0,'semantic_accuracy':'not_measured',
        'review_reasons':dict(Counter(r.get('review_reason','') for r in accepted if r['status']=='review')),
        'failure_reasons':dict(Counter(r.get('reason','') for r in accepted if r['status']=='failed')),
        'identity_resolution':'not_started','graph_import':'not_started',
        'papers_sha256':digest((output/'papers.json').read_bytes())}
    # Counter insertion order from the ID set can differ between processes.
    # Preserve the original summary bytes when all measured values match.
    summary_path=output/'summary.json'
    if summary_path.exists():
        saved=json.loads(summary_path.read_text())
        if saved!=summary:raise ValueError('checkpoint summary values changed')
        return saved
    write_json(summary_path,summary)
    return summary
