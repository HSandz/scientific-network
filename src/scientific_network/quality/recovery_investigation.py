"""Reproducible cached Task2B evidence inventory; never silently labels identities."""
import argparse
from collections import Counter, defaultdict
from pathlib import Path
import json

from scientific_network.collect.storage import read_jsonl, write_json
from scientific_network.collect.openalex_release import normalize_doi
from scientific_network.quality.identity_audit import file_hash, unused
from scientific_network.resolve.mentions_v5 import ordered_tokens
from scientific_network.resolve.recovery_v5 import consistent_names
from scientific_network.resolve.release import short_id


def investigate(works, decisions, requests, cache, output):
    unused(output)
    rows=read_jsonl(works);ds=read_jsonl(decisions);req=json.loads(requests.read_bytes())
    by_paper={r['paper_id']:r for r in rows};group=defaultdict(list)
    for d in ds:
        if d['decision_reason']=='author_id_incompatible_name_variants':group[d['source_author_id']].append(d)
    # Public declarations are construction certificates, explicitly not gold.
    certificates=[];public={}
    for request in req:
        if request['source']!='orcid' or 'record' not in request:continue
        rec=request['record'];p=cache/'objects'/rec['sha256']
        if file_hash(p)!=rec['sha256']:raise ValueError('external hash mismatch')
        data=json.loads(p.read_bytes());n=data.get('name') or {};v=lambda k:(n.get(k) or {}).get('value') or ''
        names=[' '.join(filter(None,[v('given-names'),v('family-name')]))]+v('credit-name').split(';')
        names += [a['content'] for a in (data.get('other-names') or {}).get('other-name',[])]
        names=sorted({s.strip() for s in names if s.strip()})
        c={'provider_id':request['key'],'orcid':rec['url'].split('/')[-2],'declared_names':names,'source':rec,
           'claim':'public_owner_declared_name_variants','independent_gold':False,
           'limitation':'provider may ingest this ORCID account; ownership and every paper not independently verified'}
        public[request['key']]=c
        variants={d['official_name'] for d in group.get(request['key'],[])}
        if variants and consistent_names(variants,c)=='provider_id_public_orcid_declared_aliases':certificates.append(c)
    ledger=[];priority=sorted(group,key=lambda aid:(-len(group[aid]),aid))
    for rank,aid in enumerate(priority,1):
        mentions=group[aid];names=sorted({d['official_name'] for d in mentions});mechanism=consistent_names(names,public.get(aid))
        tokens=[ordered_tokens(n) for n in names]
        if mechanism=='provider_id_full_letter_boundary_normalization':category='given_name_token_boundaries'
        elif mechanism:category='public_declared_aliases'
        elif len({t[-1] for t in tokens if t})==1 and len({t[0] for t in tokens if t})==1:category='middle_name_or_initial_variation_unverified'
        else:category='different_full_names_or_spelling_unverified'
        observations=[];orgs=set();coauthors=set()
        for d in mentions:
            r=by_paper[d['paper_id']];a=r['openalex']['authorships'][d['author_position']-1]
            orgs.update(short_id(i.get('id')) for i in a.get('institutions',[]) if i.get('id'))
            coauthors.update(short_id((b.get('author') or {}).get('id')) for b in r['openalex']['authorships'] if (b.get('author') or {}).get('id'))
            observations.append({k:d[k] for k in ('mention_id','paper_id','author_position','official_name','raw_author_name','canonical_display_name','paper_raw_orcid','profile_orcid','profile_observed_orcids','supporting_evidence')})
        ledger.append({'provider_id':aid,'priority_rank':rank,'affected_positions':len(mentions),'official_names':names,
                       'classification':category,'classification_scope':'observed_string_pattern_or_public_declaration_not_proven_cause',
                       'recoverability':mechanism or 'insufficient_evidence_abstain',
                       'organization_ids':sorted(orgs),'distinct_coauthor_ids':len(coauthors-{aid}),
                       'public_declaration':public.get(aid),'positions':observations,
                       'uncertainty':None if mechanism else 'no corroborated alias/crosswalk; provider error and true conflation not distinguished',
                       'context_role':'affiliations/coauthors prioritize review only; never identity acceptance'})
    doi=[]
    for r in rows:
        oa=r.get('openalex') or {}
        if r['match']['status']!='matched' or normalize_doi(r['doi'])==normalize_doi(oa.get('doi')):continue
        records=[]
        for request in req:
            if request['source']=='crossref' and request['key']==r['paper_id'] and 'record' in request:
                rec=request['record'];path=cache/'objects'/rec['sha256']
                if file_hash(path)!=rec['sha256']:raise ValueError('Crossref source hash mismatch')
                m=json.loads(path.read_bytes())['message']
                records.append({'DOI':m['DOI'],'type':m.get('type'),'title':m.get('title'),
                                'container_title':m.get('container-title'),'published':m.get('published'),
                                'authors':[{'name':' '.join(filter(None,[a.get('given'),a.get('family')])),'orcid':a.get('ORCID')} for a in m.get('author',[])],
                                'relation':m.get('relation'),'source':rec})
        official_paths=list(Path('data/raw').glob('*/objects/'+r['roster']['source_sha256']))
        if not official_paths or any(file_hash(p)!=r['roster']['source_sha256'] for p in official_paths):
            raise ValueError('official cached source absent or corrupted')
        doi.append({'paper_id':r['paper_id'],'official_doi':normalize_doi(r['doi']),'returned_doi':normalize_doi(oa['doi']),
                    'official_metadata':r['roster'],'returned_work':{'id':oa['id'],'title':oa['title'],'year':oa['publication_year'],
                    'byline':[a.get('raw_author_name') for a in oa['authorships']],'source':oa['source'],'alternates':oa.get('alternates',[])},
                    'official_source_hash_verified':True,'official_cached_paths':[str(p) for p in official_paths],
                    'crossref_records':records,'decision':'ambiguous_mismatch',
                    'cause':'likely_proceedings_journal_version_linking; provider canonical DOI differs',
                    'evidence_strength':'two registered DOI records, matching titles/bylines, different publication dates; no explicit relation deposited',
                    'identity_action':'withhold all positions; do not transfer journal ORCIDs or historical affiliations',
                    'potential_authorship_positions':len(r['roster']['authors']),
                    'source_correction':None,'remaining_uncertainty':'explicit version equivalence and provenance of authorship/affiliations not established'})
    write_json(output/'alias-certificates.json',{'method':'public-orcid-declared-aliases-v1','certificates':sorted(certificates,key=lambda c:c['provider_id'])})
    write_json(output/'provider-ledger.json',ledger)
    write_json(output/'doi-ledger.json',doi)
    write_json(output/'investigation-summary.json',{'inputs':{str(p):file_hash(p) for p in (works,decisions,requests)},
        'provider_ids':len(ledger),'affected_positions':sum(x['affected_positions'] for x in ledger),
        'classification_ids':dict(Counter(x['classification'] for x in ledger)),
        'classification_positions':{k:sum(x['affected_positions'] for x in ledger if x['classification']==k) for k in sorted({x['classification'] for x in ledger})},
        'doi_cases':len(doi),'doi_positions':sum(x['potential_authorship_positions'] for x in doi),
        'alias_certificates':len(certificates),'semantic_accuracy':'not_measured'})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ('works','decisions','requests','cache','output'):p.add_argument('--'+arg,required=True,type=Path)
    p.add_argument('--context-only',action='store_true',help='Write paper-specific context for the frozen 683-position frame')
    a=p.parse_args()
    if a.context_only:
        unused(a.output)
        rows={r['paper_id']:r for r in read_jsonl(a.works)}
        context=[]
        for d in read_jsonl(a.decisions):
            if d['decision_reason']!='author_id_incompatible_name_variants':continue
            r=rows[d['paper_id']];author=r['openalex']['authorships'][d['author_position']-1]
            context.append({'provider_id':d['source_author_id'],'mention_id':d['mention_id'],
                'paper_id':r['paper_id'],'position':d['author_position'],'doi':r['doi'],
                'year':r['year'],'venue_id':r['venue_id'],'title':r['roster']['title'],
                'raw_affiliation_strings':author.get('raw_affiliation_strings'),
                'affiliations':author.get('affiliations'),'institutions':author.get('institutions'),
                'coauthors':[{'position':i,'official_name':name,'provider_id':short_id((b.get('author') or {}).get('id'))}
                    for i,(name,b) in enumerate(zip(r['roster']['authors'],r['openalex']['authorships']),1) if i!=d['author_position']],
                'source':r['openalex']['source'],'evidence_role':'historical paper context; never sufficient alone for identity recovery'})
        write_json(a.output,context)
    else:
        investigate(a.works,a.decisions,a.requests,a.cache,a.output)
if __name__=='__main__':main()
