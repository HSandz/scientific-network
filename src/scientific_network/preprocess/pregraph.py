"""Immutable pregraph tables and fail-closed readiness assessment; no graph code."""
from collections import Counter, defaultdict
import json
from pathlib import Path

from scientific_network.collect.diagnostic_acquire import title_key
from scientific_network.collect.storage import digest, read_config, read_jsonl, write_json
from scientific_network.collect.splits import title_group
from scientific_network.nlp.baseline import predict, METHOD as TOPIC_METHOD
from scientific_network.preprocess.diagnostics import validate_selection, ordered_byline
from scientific_network.collect.acquire import names_compatible
from scientific_network.resolve.diagnostics import (
    doi_key, orcid_key, record_hash, load_reviews, source_eligible, publication_support, check_proof,
)

VERSION = 'five-year-pregraph-readiness-v3'


def canonical_frame(rows, historical_rows, acquired, membership):
    """Identifiers connect review groups; a title alone never canonically merges works."""
    known = {r['paper_id']: r for r in historical_rows}
    known.update({r['paper_id']: r for r in rows})
    if len({r['paper_id'] for r in rows}) != len(rows):
        raise ValueError('duplicate official roster ID')
    by_id = {r['paper_id']: r for r in acquired}
    indices = defaultdict(set)
    keys = defaultdict(set)
    def add(pid, kind, value):
        if value:
            indices[kind, value].add(pid); keys[pid].add((kind, value))
    for row in historical_rows + rows:
        pid = row['paper_id']
        if row.get('status') not in (None, 'included'):
            continue
        add(pid, 'title_candidate', title_group(row['title']))
        add(pid, 'doi', doi_key(row.get('doi')))
        for k in ('official_url', 'pdf_url'):
            add(pid, 'official_url', (row.get(k) or '').rstrip('/'))
    for record in acquired:
        pid=record['paper_id']; work=record.get('openalex_work') or {}
        add(pid, 'doi', doi_key((record.get('official') or {}).get('doi')))
        add(pid, 'doi', doi_key(work.get('doi')))
        add(pid, 'provider_work', work.get('id'))
        for loc in work.get('locations', []) + [work.get('primary_location') or {}]:
            for k in ('landing_page_url', 'pdf_url'):
                value=(loc.get(k) or '').rstrip('/')
                # Link only exact known official records, never arbitrary provider URLs.
                if value and ('official_url', value) in indices:
                    add(pid, 'official_url', value)
    parent={pid:pid for pid in known}
    def find(pid):
        parent.setdefault(pid,pid)
        if parent[pid]!=pid:parent[pid]=find(parent[pid])
        return parent[pid]
    for group in indices.values():
        if len(group)>1:
            roots=sorted({find(p) for p in group})
            for root in roots[1:]:parent[root]=roots[0]
    groups=defaultdict(set)
    for pid in parent:groups[find(pid)].add(pid)
    assigned={r['paper_id']:r['split'] for r in membership}
    crosswalk=[]
    for pid, record in sorted(by_id.items()):
        others=groups[find(pid)]-{pid}
        held={p for p in groups[find(pid)] if assigned.get(p)=='test'}
        reason='heldout_version_group' if held else 'ambiguous_known_work_versions' if others else None
        crosswalk.append(dict(paper_id=pid,canonical_work_id=pid if not reason else None,
            disposition='accepted_known_frame_singleton' if not reason else 'withheld',
            reason=reason,known_group_paper_ids=sorted(groups[find(pid)]),
            identifiers=[dict(kind=k,value=v) for k,v in sorted(keys[pid])],
            merge_performed=False,global_identity_certified=False,method_version=VERSION))
    return crosswalk


def stage_topics(record, taxonomy, canonical_ok):
    """Literal candidates with provenance and explicit abstention, without graph edges."""
    official=record.get('official') or {}
    title=official.get('title') or record['roster']['title']
    abstract=official.get('abstract') or ''
    predictions, reason=predict(title+'\n'+abstract,taxonomy) if canonical_ok else ([], 'withheld_core_source_or_work')
    result=dict(paper_id=record['paper_id'],decision=reason,validation_status='review' if predictions else 'abstained',
        accepted_labels=[],candidate_labels=predictions,method_version=TOPIC_METHOD,
        calibration_status='uncalibrated',independent_review=False,
        text_sha256=digest((title+'\n'+abstract).encode()),source=record.get('official_source'),
        title_locator=official.get('title_locator'),abstract_locator=official.get('abstract_locator'))
    for prediction in predictions:
        if (title+'\n'+abstract)[prediction['start']:prediction['end']]!=prediction['excerpt']:
            raise ValueError('topic candidate has nonliteral evidence')
    return result


def close_queue(previous, authorships, affiliations):
    people={(r['paper_id'],r['byline_position']) for r in authorships}
    aligned={(r['paper_id'],r['byline_position']) for r in affiliations}
    closed=[]
    for i,row in enumerate(previous):
        key=row['paper_id'],row['byline_position']
        if row.get('printed_institution'):
            accepted=any((t['paper_id'],t['byline_position'])==key
                and title_key(t['organization_name'])==title_key(row['printed_institution']) for t in affiliations)
        elif row['reason']=='printed_author_affiliation_review_required':
            accepted=key in aligned
        else:
            accepted=key in people
        closed.append(dict(queue_id='queue:'+record_hash([i,row]),original=row,
            disposition='resolved_with_accepted_support' if accepted else 'withheld_insufficient_or_conflicting_evidence',
            reconsideration='new_version_and_new_evidence_required' if not accepted else None,
            independent_review=False,method_version=VERSION))
    return closed


def validate_authorship(row, record, review, cache):
    pos=row['byline_position']
    authors=(record.get('openalex_work') or {}).get('authorships', [])
    roster=record['roster']
    if (type(pos) is not int or not 1 <= pos <= len(roster['authors'])
        or not ordered_byline(roster['authors'], [a['author'].get('display_name','') for a in authors])
        or not source_eligible(record, review)):
        raise ValueError('accepted authorship has unresolved complete byline')
    author=authors[pos-1]['author'];oid=orcid_key(author.get('orcid'))
    expected_researcher='researcher:orcid:'+oid if oid else None
    if (not oid or row['researcher_id']!=expected_researcher or row['orcid']!=oid
        or row['openalex_author_id']!=author.get('id')
        or not names_compatible(row['raw_name'],roster['authors'][pos-1])
        or row['id']!='authorship:'+record_hash([expected_researcher,record['paper_id']])):
        raise ValueError('accepted authorship has contradictory person identifiers')
    proof=row['evidence']['public_orcid']
    if proof['url']!=f'https://pub.orcid.org/v3.0/{oid}/works':
        raise ValueError('ORCID publication evidence belongs to another person')
    check_proof(proof,cache)
    dois={doi_key((record.get('official') or {}).get('doi')),doi_key(record['openalex_work'].get('doi'))}-{None}
    match=publication_support((cache/'objects'/proof['sha256']).read_bytes(),roster['title'],roster['year'],dois)
    if not match or any(proof.get(k)!=v for k,v in match.items()):
        raise ValueError('accepted authorship lacks matching public publication evidence')


def prepare_pregraph(config_path: Path, output: Path):
    config=read_config(config_path)
    if config.get('graph_construction') is not False or config.get('heldout_acquisition') is not False:
        raise ValueError('pregraph preparation must disable graph construction and held-out acquisition')
    # All inputs are pinned; do not write even the input manifest on failed validation.
    for name, expected in config['input_sha256'].items():
        if digest(Path(name).read_bytes())!=expected:
            raise ValueError('pregraph input changed: '+name)
    paths={k:Path(v) for k,v in config['paths'].items()}
    validate_selection(paths['original_acquisition'], paths['manifest'], paths['splits'],
                       {'diagnostic_config':str(paths['diagnostic_config']), 'max_papers':68})
    records=json.loads(paths['headers'].read_text())
    reviews=load_reviews(paths['reviews'],records,digest(paths['headers'].read_bytes()),paths['cache'])
    support=json.loads(paths['corroboration'].read_text())
    accepted=[row for p in support for row in p['accepted_authorships']]
    affiliations=[row for p in support for row in p['affiliation_triples']]
    by_paper={r['paper_id']:r for r in records}
    if {r['paper_id'] for r in support}!=set(by_paper) or len(support)!=len(records):
        raise ValueError('corroboration membership differs from frozen headers')
    for r in records:
        for field in ('pdf_source','tei_source','official_source','openalex_source'):
            if r.get(field):check_proof(r[field],paths['cache'])
    for row in accepted:
        r=by_paper[row['paper_id']]
        validate_authorship(row,r,reviews.get(r['paper_id']),paths['cache'])
    # Include all old and new reserved IDs as guards, without reading their paper content.
    membership=read_jsonl(paths['splits']/'membership.jsonl')+read_jsonl(paths['historical_membership'])
    frame=canonical_frame(read_jsonl(paths['manifest']),read_jsonl(paths['historical_manifest']),
        records+json.loads(paths['historical_acquisition'].read_text()),membership)
    frame_by_id={r['paper_id']:r for r in frame}
    eligible={r['paper_id'] for r in records if source_eligible(r,reviews.get(r['paper_id']))
              and frame_by_id[r['paper_id']]['canonical_work_id']}
    blocked_support=[row for row in accepted if row['paper_id'] not in eligible]
    accepted=[row for row in accepted if row['paper_id'] in eligible]
    accepted_ids={a['id'] for a in accepted}
    quality=read_config(paths['quality'])
    affiliations=[t for t in affiliations if t['paper_id'] in eligible]
    organizations={}
    for row in affiliations:
        rid=row['researcher_id'];r=by_paper[row['paper_id']];pos=row['byline_position']
        if not any(a['paper_id']==row['paper_id'] and a['researcher_id']==rid for a in accepted):
            raise ValueError('affiliation lacks accepted paper-specific authorship')
        review=reviews.get(row['paper_id'])
        if not review or review['decision_id']!=row['source_decision_id']:
            raise ValueError('affiliation lacks its printed review')
        metadata=r['openalex_work']['authorships'][pos-1]['institutions']
        if not any(i['id']==row['openalex_institution_id'] and title_key(i['display_name'])==title_key(aff['printed_institution'])
                   for i in metadata for aff in review['authors'][pos-1]['affiliations']):
            raise ValueError('affiliation not exactly supported by same author metadata')
        oid=row['organization_id']
        organizations.setdefault(oid,dict(organization_id=oid,name=row['organization_name'],openalex_id=row['openalex_institution_id'],
            sector='unknown',method_version=VERSION,source_affiliation_ids=[]))['source_affiliation_ids'].append(row['id'])
    if len(accepted_ids)!=len(accepted) or len({t['id'] for t in affiliations})!=len(affiliations):
        raise ValueError('duplicate semantic support records')
    taxonomy=read_config(paths['taxonomy'])
    topics=[stage_topics(r,taxonomy,r['paper_id'] in eligible) for r in records]
    work_to_paper=defaultdict(set)
    for r in records:
        if r['paper_id'] in eligible and (r.get('openalex_work') or {}).get('id'):
            work_to_paper[r['openalex_work']['id']].add(r['paper_id'])
    citations={}
    for r in records:
        if r['paper_id'] not in eligible:continue
        for target in (r.get('openalex_work') or {}).get('referenced_works',[]):
            targets=work_to_paper[target]
            if len(targets)==1:
                pid=next(iter(targets))
                if pid==r['paper_id']:continue
                key=record_hash([r['paper_id'],pid])
                citations[key]=dict(support_id='citation:'+key,citing_paper_id=r['paper_id'],cited_paper_id=pid,
                    validation_status='review',source=r['openalex_source'],locator='referenced_works['+target+']',
                    reason='explicit_reference_check_required',method_version=VERSION)
    prior=json.loads(paths['previous_queue'].read_text())
    closed=close_queue(prior,accepted,affiliations)
    current_queue=[q for p in support for q in p.get('review_queue',[])]
    current_closed=close_queue(current_queue,accepted,affiliations)
    papers=[dict(paper_id=r['paper_id'],year=r['roster']['year'],venue_id=r['roster']['venue_id'],
        title=r['roster']['title'],core_disposition='accepted_development_source' if r['paper_id'] in eligible else 'withheld',
        reason=None if r['paper_id'] in eligible else frame_by_id[r['paper_id']]['reason'] or 'printed_source_byline_or_title_conflict',
        original_acquisition_status=r['status'],original_extraction_status=r['extraction_status'],
        source_decision_id=reviews.get(r['paper_id'],{}).get('decision_id'),pdf_source=r['pdf_source']) for r in records]
    editions=read_jsonl(paths['edition_ledger'])
    edition_actions=[dict(venue_id=e['venue_id'],year=e['year'],source_status=e['status'],reason=e.get('reason'),
        disposition='eligible_roster_available' if e['status']=='verified_eligible' else 'unresolved_source_dependency',
        original_ledger_sha256=digest(paths['edition_ledger'].read_bytes())) for e in editions]
    author_count=sum(len(r['roster']['authors']) for r in records)
    covered_affiliations=len({(r['paper_id'],r['byline_position']) for r in affiliations})
    unique_people=len({r['researcher_id'] for r in accepted})
    abstracts=sum(bool((r.get('official') or {}).get('abstract')) for r in records if r['paper_id'] in eligible)
    all_editions_resolved=all(e['status'] in {'verified_eligible','verified_no_edition','excluded_track'} for e in editions)
    # Full-population gates are separate from the technical frozen-diagnostic bundle.
    gates={
        'frozen_input_integrity':dict(status='passed',detail='all pinned inputs and reserved IDs verified'),
        'diagnostic_source_triage':dict(status='passed',detail='all selected papers have accepted or withheld dispositions'),
        'all_planned_editions_resolved':dict(status='passed' if all_editions_resolved else 'failed',detail='noneligible statuses remain external scope dependencies'),
        'full_enrichment_and_work_resolution':dict(status='failed',detail='only 68 new development diagnostics; historical staging separate; no full-corpus canonical certification'),
        'identity_coverage':dict(status='failed' if unique_people<quality['size']['min_resolved_core_researchers'] else 'passed',detail=f"{unique_people} unique corroborated people; release target {quality['size']['min_resolved_core_researchers']}"),
        'affiliation_coverage':dict(status='passed' if covered_affiliations/author_count>=quality['coverage_targets']['author_paper_affiliation_resolution'] else 'failed',detail=f'{covered_affiliations}/{author_count} selected byline mentions'),
        'abstract_coverage':dict(status='passed' if eligible and abstracts/len(eligible)>=quality['coverage_targets']['abstracts'] else 'failed',detail=f'{abstracts}/{len(eligible)} source-accepted development papers; selected population also reported'),
        'accepted_topic_coverage':dict(status='failed',detail=f'0/{len(eligible)} source-accepted papers; all baseline topics remain candidates'),
        'topic_calibration_and_taxonomy_approval':dict(status='unmeasured',detail='draft taxonomy and uncalibrated phrase candidates; independent labels unavailable'),
        'independent_component_quality':dict(status='not_run',detail='requires independent human annotations; reserved tests untouched'),
        'global_canonical_work_resolution':dict(status='failed',detail='known-frame version quarantine implemented; alternate-title and inaccessible-source versions remain unresolved'),
    }
    tables={'paper-dispositions':papers,'canonical-work-crosswalk':frame,
        'authorship-support':accepted,'affiliation-triples':affiliations,'organization-crosswalk':list(organizations.values()),
        'topic-candidates':topics,'citation-candidates':list(citations.values()),'previous-queue-dispositions':closed,
        'edition-dispositions':edition_actions,'current-queue-dispositions':current_closed,'quarantined-authorship-support':blocked_support}
    signature=dict(method_version=VERSION,config_sha256=digest(config_path.read_bytes()),input_sha256=config['input_sha256'])
    write_json(output/'inputs.json',signature)
    for name,rows in tables.items():write_json(output/(name+'.json'),rows)
    summary=dict(stage='prepare-pregraph',**signature,selected_papers=len(records),source_accepted_papers=len(eligible),
        source_withheld_papers=len(records)-len(eligible),accepted_researchers=unique_people,accepted_authorship_support=len(accepted),
        accepted_affiliation_triples=len(affiliations),affiliated_author_paper_pairs=covered_affiliations,selected_author_mentions=author_count,
        organizations=len(organizations),canonical_known_frame_records=len(frame),
        known_frame_quarantined=sum(r['canonical_work_id'] is None for r in frame),
        current_queue_dispositions=dict(Counter(r['disposition'] for r in current_closed)),
        source_accepted_abstracts=abstracts,
        old_queue_dispositions=dict(Counter(r['disposition'] for r in closed)),
        topic_decisions=dict(Counter(r['decision'] for r in topics)),topic_candidate_labels=sum(len(t['candidate_labels']) for t in topics),
        accepted_topic_labels=0,citation_candidates=len(citations),accepted_citations=0,
        edition_statuses=dict(Counter(e['status'] for e in editions)),gates=gates,
        diagnostic_tables_frozen=True,full_pregraph_ready=all(g['status']=='passed' for g in gates.values()),
        held_out_papers_acquired=0,graph_construction_performed=False,graph_imports=0,semantic_accuracy='not_measured',
        output_sha256={name:digest((output/(name+'.json')).read_bytes()) for name in tables})
    write_json(output/'summary.json',summary)
    # A content-addressed freeze receipt pins every table without constructing GraphArtifact.
    write_json(output/'freeze.json',dict(bundle_id='pregraph:'+record_hash(summary),summary_sha256=digest((output/'summary.json').read_bytes()),
        output_sha256=summary['output_sha256'],allowed_next_action='review_failed_gates',graph_construction_authorized=False))
    return summary
