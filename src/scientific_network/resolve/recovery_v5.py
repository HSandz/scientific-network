"""Bounded evidence recovery helpers, extending the existing mention resolver.

No fuzzy matching, name-only crosswalks, profile-array ownership, or affiliation
inference. Original sources are never modified. Alternate sources must be raw
hash-verified exact-DOI work records with complete positional byline agreement.
"""
from collections import defaultdict
from pathlib import Path
import json
import re

from scientific_network.collect.openalex_release import normalize_doi, title_similarity
from scientific_network.quality.identity_audit import file_hash
from scientific_network.resolve.release import short_id

METHOD = 'paper-mention-identity-v5.3'


def boundary_equivalent(left, right):
    """Formatting only: same final surname token, same ordered full given letters.

    Does not erase middle tokens or permit initials, substitutions, permutations,
    or surname changes. Stable provider ID and aligned bylines are still required.
    """
    from scientific_network.resolve.mentions_v5 import ordered_tokens
    a,b=ordered_tokens(left),ordered_tokens(right)
    return (len(a)>=2 and len(b)>=2 and all(len(t)>1 for t in a+b)
            and a[-1]==b[-1] and ''.join(a[:-1])==''.join(b[:-1]))


def consistent_names(names, certificate=None):
    from scientific_network.resolve.mentions_v5 import positional_name
    if all(positional_name(a,b) or boundary_equivalent(a,b) for a in names for b in names):
        return 'provider_id_full_letter_boundary_normalization'
    if certificate:
        declared=certificate['declared_names']
        if all(any(positional_name(n, alias) for alias in declared) for n in names):
            return 'provider_id_public_orcid_declared_aliases'
    return None


def load_alias_certificates(path, cache, rows):
    """Verify declarations against bytes, account path and all profile observations.

    This supplies construction evidence, not independent evaluation labels.
    A name declaration cannot resolve a conflicting provider profile.
    """
    if path is None: return {}
    from scientific_network.resolve.release_identity import collect_identity_evidence, valid_orcid
    identity=collect_identity_evidence(rows)
    result={}
    for c in json.loads(Path(path).read_bytes())['certificates']:
        aid=c['provider_id'];rec=c['source'];raw=Path(cache)/'objects'/rec['sha256']
        if file_hash(raw)!=rec['sha256']:raise ValueError('alias source hash mismatch')
        data=json.loads(raw.read_bytes());name=data.get('name') or {}
        orcid=valid_orcid(c['orcid'])
        if not orcid or rec['url'] != 'https://pub.orcid.org/v3.0/'+orcid+'/person' or name.get('path')!=orcid:
            raise ValueError('alias account provenance mismatch')
        values=lambda field: (name.get(field) or {}).get('value') or ''
        declared=[' '.join(filter(None,[values('given-names'),values('family-name')]))]
        declared.extend(values('credit-name').split(';'))
        declared.extend(x['content'] for x in (data.get('other-names') or {}).get('other-name',[]))
        declared=sorted({x.strip() for x in declared if x.strip()})
        if c['declared_names']!=declared:raise ValueError('alias declaration differs from public bytes')
        if aid in identity['withheld'] or identity['orcids'].get(aid)!= {orcid}:
            raise ValueError('alias certificate conflicts with full-source ORCIDs')
        if aid in result: raise ValueError('duplicate alias certificate')
        result[aid]=c
    return result


def alternate_recoveries(rows, decisions, cache, blocked):
    """Recover absent IDs only; never override contradictory selected identifiers."""
    from scientific_network.resolve.mentions_v5 import positional_name, work_rejection
    eligible={(d['paper_id'],d['author_position']):d for d in decisions
              if d['decision_reason']=='no_provider_id_or_paper_raw_orcid'}
    result={};diagnostics=[];alternate_rows=[]
    for row in rows:
        oa=row.get('openalex') or {}
        if not oa.get('alternates') or work_rejection(row):continue
        source=oa['source'];path=Path(cache)/'objects'/source['raw_sha256']
        if file_hash(path)!=source['raw_sha256']:raise ValueError('alternate source hash mismatch')
        raw=json.loads(path.read_bytes())
        works=raw.get('results',[raw])
        alternative_ids={a['id'] for a in oa['alternates']}
        candidates=[]
        for j,w in enumerate(works):
            if w.get('id') not in alternative_ids:continue
            if normalize_doi(w.get('doi'))!=normalize_doi(row['doi']):continue
            names=row['roster']['authors'];authors=w.get('authorships') or []
            if len(names)!=len(authors) or title_similarity(row['roster']['title'],w.get('title'))<.9:continue
            if not all(positional_name(n,a.get('raw_author_name')) for n,a in zip(names,authors)):continue
            if any(positional_name(n,a.get('raw_author_name')) == 'initials' and (
                    sum(bool(positional_name(n,b.get('raw_author_name'))) for b in authors)!=1 or
                    sum(bool(positional_name(m,a.get('raw_author_name'))) for m in names)!=1)
                   for n,a in zip(names,authors)):continue
            ids=[short_id((a.get('author') or {}).get('id')) for a in authors]
            if any(a and ids.count(a)>1 for a in ids):continue
            # Selected nonmissing ID disagreements are retained as contradiction;
            # do not choose a different provider partition through duplicate works.
            disagreements=[i+1 for i,(a,b) in enumerate(zip(oa['authorships'],authors))
                           if (a.get('author') or {}).get('id') and (b.get('author') or {}).get('id')
                           and (a['author']['id']!=b['author']['id'])]
            if disagreements:
                diagnostics.append({'paper_id':row['paper_id'],'alternate_work':w['id'],'reason':'other_positions_provider_ids_disagree','positions':disagreements})
                continue
            candidates.append((j,w))
            alternate_rows.append({**row,'openalex':{**w,'source':{**source,'locator':f'results[{j}]'}}})
        for i,a in enumerate(oa['authorships'],1):
            key=(row['paper_id'],i)
            if key not in eligible:continue
            found=defaultdict(list)
            for j,w in candidates:
                b=w['authorships'][i-1];aid=short_id((b.get('author') or {}).get('id'))
                if aid and re.fullmatch(r'A\d+',aid):found[aid].append((j,w,b))
            if len(found)!=1:continue
            aid=next(iter(found))
            if aid in blocked:continue
            j,w,b=found[aid][0]
            # Never infer an ORCID ownership from an alternate profile.
            jsource={**source,'locator':f'results[{j}]'}
            if 'results' not in raw:jsource={**source,'locator':'$'}
            result[key]={'source_author_id':aid,'canonical_researcher_id':'researcher:openalex:'+aid,
                         'alternate_authorship':b,'alternate_work_id':short_id(w['id']),'source':jsource,
                         'decision_reason':'missing_id_exact_doi_alternate_work',
                         'source_record':{'paper_id':row['paper_id'],'openalex':{'id':w['id'],'source':jsource}}}
    from scientific_network.resolve.release_identity import collect_identity_evidence
    combined=collect_identity_evidence(rows+alternate_rows)
    alternate_names=defaultdict(set)
    for r in alternate_rows:
        for name,a in zip(r['roster']['authors'],r['openalex']['authorships']):
            aid=short_id((a.get('author') or {}).get('id'))
            if aid:alternate_names[aid].add(name)
    for key,c in list(result.items()):
        aid=c['source_author_id'];names=alternate_names[aid]
        if aid in combined['withheld'] or not consistent_names(names):
            diagnostics.append({'paper_id':key[0],'position':key[1],'provider_id':aid,
                                'reason':'cross_alternate_identity_conflict'})
            del result[key]
    return result,diagnostics
