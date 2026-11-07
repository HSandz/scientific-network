"""Bounded development corroboration; outputs support tables, never a graph import."""
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
from urllib.parse import unquote
import xml.etree.ElementTree as ET

import httpx

from scientific_network.collect.acquire import names_compatible, name_tokens
from scientific_network.collect.diagnostic_acquire import title_key
from scientific_network.collect.storage import (
    SourceCache, SourceError, QuotaError, digest, read_config, write_json,
)
from scientific_network.preprocess.diagnostics import ordered_byline, source_triage, validate_selection

VERSION = 'five-year-public-corroboration-v1'


def record_hash(value):
    return digest(json.dumps(value, sort_keys=True, ensure_ascii=False).encode())


def doi_key(value):
    value = unquote(value or '').strip().casefold()
    value = re.sub(r'^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)', '', value)
    return value if re.fullmatch(r'10\.\d{4,9}/\S+', value) else None


def orcid_key(value):
    value = re.sub(r'^https?://orcid\.org/', '', value or '').upper()
    if not re.fullmatch(r'\d{4}-\d{4}-\d{4}-\d{3}[\dX]', value):
        return None
    total = 0
    for digit in value.replace('-', '')[:15]:
        total = (total + int(digit)) * 2
    check = (12 - total % 11) % 11
    return value if value[-1] == ('X' if check == 10 else str(check)) else None


def publication_support(body, title, year, dois):
    """Match inside one public work summary, never across groups or ID types."""
    root = ET.fromstring(body)
    if root.tag.rsplit('}', 1)[-1] != 'works':
        raise ValueError('ORCID response is not a works document')
    for work in root.findall('.//{*}work-summary'):
        locator = 'work-summary[put-code=' + work.get('put-code', 'unknown') + ']'
        typed_dois = {doi_key(node.findtext('{*}external-id-value'))
                      for node in work.findall('.//{*}external-id')
                      if (node.findtext('{*}external-id-type') or '').casefold() == 'doi'
                      and (node.findtext('{*}external-id-relationship') or '').casefold() == 'self'} - {None}
        if dois & typed_dois:
            return {'method': 'typed_public_work_doi', 'locator': locator,
                    'matched_doi': sorted(dois & typed_dois)[0]}
        titles = {title_key(''.join(n.itertext())) for n in work.findall('./{*}title/{*}title')}
        pubyear = work.findtext('./{*}publication-date/{*}year')
        if title_key(title) and title_key(title) in titles and pubyear == str(year):
            return {'method': 'unicode_exact_title_and_year', 'locator': locator}
    return None


def check_proof(proof, cache_path):
    if not proof or not proof.get('url') or not proof.get('sha256'):
        raise ValueError('missing source evidence descriptor')
    if digest((cache_path/'objects'/proof['sha256']).read_bytes()) != proof['sha256']:
        raise ValueError('source evidence hash mismatch')


def load_reviews(path, records, input_sha, cache_path):
    ledger = json.loads(path.read_text())
    if ledger.get('reviewed_input_sha256') != input_sha:
        raise ValueError('source review input hash mismatch')
    by_id = {r['paper_id']: r for r in records}
    reviews = {}
    for review in ledger['records']:
        pid = review['paper_id']
        if pid not in by_id or pid in reviews:
            raise ValueError('unknown or duplicate source review')
        record = by_id[pid]
        if review.get('record_sha256') != record_hash(record):
            raise ValueError('reviewed record hash mismatch')
        if review.get('pdf_sha256') != record.get('pdf_source', {}).get('sha256'):
            raise ValueError('reviewed PDF hash mismatch')
        check_proof(record['pdf_source'], cache_path)
        if (not review.get('decision_id') or not review.get('source_locator')
            or review.get('method') != 'printed_source_review'
            or review.get('independent_review') is not False
            or review.get('original_status_preserved') != record['status']):
            raise ValueError('invalid printed-source decision')
        authors = review['authors']
        if ([a['position'] for a in authors] != list(range(1, len(authors)+1))
            or not ordered_byline(record['roster']['authors'], [a['name'] for a in authors])
            or title_key(review['title']) != title_key(record['roster']['title'])):
            raise ValueError('printed review does not corroborate ordered roster')
        for author in authors:
            if any(not a.get('printed_institution') or not a.get('source_locator') for a in author['affiliations']):
                raise ValueError('reviewed affiliation needs institution and locator')
        reviews[pid] = review
    return reviews


def source_eligible(record, review=None):
    if not review:
        return source_triage(record)['candidate_binding_available']
    # Bibliography recovered from a reviewed page remains separate from parser/status.
    names = [a['name'] for a in review['authors']]
    return bool(names) and len({tuple(name_tokens(n)) for n in names}) == len(names)


def version_conflicts(records, historical, heldurls):
    by_work = defaultdict(set)
    for record in records + historical:
        work = record.get('openalex_work') or {}
        if work.get('id'):
            by_work[work['id']].add(record['paper_id'])
    blocked = {}
    for record in records:
        work = record.get('openalex_work') or {}
        if work.get('id') and len(by_work[work['id']]) > 1:
            blocked[record['paper_id']] = 'shared_provider_work_requires_canonical_review'
        locations = work.get('locations', []) + [work.get('primary_location') or {}]
        if any((loc.get(k) or '').rstrip('/') in heldurls for loc in locations
               for k in ('landing_page_url', 'pdf_url')):
            blocked[record['paper_id']] = 'provider_location_links_heldout_record'
    return blocked


def crosswalk_conflicts(records, historical_nodes):
    provider_orcids, orcid_providers, names = defaultdict(set), defaultdict(set), defaultdict(list)
    for record in records:
        for entry in (record.get('openalex_work') or {}).get('authorships', []):
            author = entry['author']; provider = author.get('id')
            raw_ids = [author.get('orcid'), entry.get('raw_orcid')] + (author.get('observed_orcids') or [])
            for raw in raw_ids:
                oid = orcid_key(raw)
                if provider and oid:
                    provider_orcids[provider].add(oid); orcid_providers[oid].add(provider)
                    names[oid].append(author.get('display_name', ''))
    for node in historical_nodes:
        if node['label'] != 'Researcher':
            continue
        props = node['properties']; oid = orcid_key(props.get('orcid'))
        if not oid:
            continue
        names[oid].extend(props.get('name_variants', []) + [node['name']])
        for provider in props.get('openalex_ids', []):
            provider_orcids[provider].add(oid); orcid_providers[oid].add(provider)
    bad_providers = {p for p, ids in provider_orcids.items() if len(ids) > 1}
    bad_orcids = {o for o, ids in orcid_providers.items() if len(ids) > 1}
    bad_orcids |= {o for o, ns in names.items() if any(not names_compatible(ns[0], n) for n in ns)}
    bad_orcids |= {o for p in bad_providers for o in provider_orcids[p]}
    return bad_providers, bad_orcids


def reviewed_affiliations(record, review, position, researcher, evidence):
    """Deduplicate paper-person-institution triples, retaining all printed locators."""
    triples, pending = {}, []
    authorship = record['openalex_work']['authorships'][position-1]
    for aff in review['authors'][position-1]['affiliations']:
        matches = {i['id']: i for i in authorship.get('institutions', [])
                   if re.fullmatch(r'https://openalex.org/I\d+', i.get('id') or '')
                   and title_key(aff['printed_institution']) == title_key(i.get('display_name', ''))}
        if len(matches) != 1:
            pending.append({'printed_institution': aff['printed_institution'],
                            'reason': 'printed_institution_lacks_exact_same_author_metadata'})
            continue
        inst = next(iter(matches.values()))
        key = 'affiliation:' + record_hash([record['paper_id'], researcher, inst['id']])
        triple = triples.setdefault(key, dict(id=key, paper_id=record['paper_id'],
            researcher_id=researcher, organization_id='organization:openalex:'+inst['id'].rsplit('/', 1)[-1],
            openalex_institution_id=inst['id'], organization_name=inst['display_name'],
            year=record['roster']['year'], byline_position=position, validation_status='accepted',
            acceptance_scope='development_evidence_contract', method_version=VERSION,
            source_decision_id=review['decision_id'], pdf_source=record['pdf_source'],
            evidence=evidence, printed_locators=[], independent_review=False))
        if aff['source_locator'] not in triple['printed_locators']:
            triple['printed_locators'].append(aff['source_locator'])
    return list(triples.values()), pending


def corroborate_diagnostics(input_path, manifest, splits, reviews_path, config_path, output, cache_path):
    config = read_config(config_path)
    if (config.get('collection_authorized') is not True or config.get('policy') != dict(
        source_review_may_override_identity=False, affiliations_require_printed_review=True,
        accept_name_only_merges=False, graph_import=False)):
        raise ValueError('corroboration requires conservative development-only policies')
    for field in ('original_acquisition', 'historical_acquisition', 'historical_graph'):
        if digest(Path(config[field]).read_bytes()) != config[field+'_sha256']:
            raise ValueError('protected input hash mismatch: '+field)
    originals, frozen, heldurls = validate_selection(Path(config['original_acquisition']), manifest, splits, config)
    records = json.loads(input_path.read_text())
    header_summary = json.loads((input_path.parent/'summary.json').read_text())
    input_sha = digest(input_path.read_bytes())
    if (header_summary.get('papers_sha256') != input_sha
        or header_summary.get('input_sha256') != config['original_acquisition_sha256']
        or any(header_summary.get(k) != v for k, v in frozen.items())):
        raise ValueError('header input does not match frozen acquisition')
    original_by_id = {r['paper_id']: r for r in originals}
    if len(records) != len(originals) or {r['paper_id'] for r in records} != set(original_by_id):
        raise ValueError('header membership differs from frozen selection')
    for record in records:
        original = original_by_id[record['paper_id']]
        if (record.get('original_record_sha256') != record_hash(original)
            or any(record.get(k) != v for k, v in original.items())):
            raise ValueError('original acquisition fields changed')
        for key in ('pdf_source', 'tei_source', 'official_source', 'openalex_source', 'source_review_source'):
            if record.get(key):
                check_proof(record[key], cache_path)
    reviews = load_reviews(reviews_path, records, input_sha, cache_path)
    historical = json.loads(Path(config['historical_acquisition']).read_text())
    nodes = json.loads(Path(config['historical_graph']).read_text())['nodes']
    blocked = version_conflicts(records, historical, heldurls)
    bad_providers, bad_orcids = crosswalk_conflicts(records + historical, nodes)
    plans, eligible_ids = [], set()
    for record in records:
        pid = record['paper_id']; work = record.get('openalex_work') or {}
        authorships = work.get('authorships', [])
        reason = blocked.get(pid)
        source_ok = source_eligible(record, reviews.get(pid))
        if not reason and not source_ok:
            reason = 'source_title_or_complete_ordered_byline_unresolved'
        if not reason and not work:
            reason = 'no_strict_provider_work_match'
        if not reason and (not re.fullmatch(r'https://openalex.org/W\d+', work.get('id') or '')
            or title_key(work.get('title', '')) != title_key(record['roster']['title'])
            or work.get('publication_year') != record['roster']['year']
            or not ordered_byline(record['roster']['authors'], [a['author'].get('display_name', '') for a in authorships])):
            reason = 'provider_title_year_or_complete_ordered_byline_unresolved'
        official_doi = doi_key((record.get('official') or {}).get('doi'))
        provider_doi = doi_key(work.get('doi'))
        if not reason and official_doi and provider_doi and official_doi != provider_doi:
            reason = 'official_provider_doi_conflict'
        mentions = []
        for pos, name in enumerate(record['roster']['authors'], 1):
            author = authorships[pos-1]['author'] if pos <= len(authorships) else {}
            oid = orcid_key(author.get('orcid')); provider = author.get('id')
            why = reason
            if not why and (not oid or not re.fullmatch(r'https://openalex.org/A\d+', provider or '')):
                why = 'missing_valid_stable_person_identifiers'
            if not why and (provider in bad_providers or oid in bad_orcids):
                why = 'conflicting_provider_orcid_or_name_crosswalk'
            if not why:
                eligible_ids.add(oid)
            mentions.append(dict(paper_id=pid, byline_position=pos, raw_name=name,
                openalex_author_id=provider, orcid=oid, preflight_reason=why))
        plans.append((record, source_ok, reason, mentions))
    cfg = config['orcid']
    if len(eligible_ids) > cfg['max_unique_requests']:
        raise ValueError('eligible ORCID request cap exceeded before network access')
    signature = dict(method_version=VERSION, input_sha256=input_sha,
        corroboration_config_sha256=digest(config_path.read_bytes()),
        reviews_sha256=digest(reviews_path.read_bytes()), **frozen)
    write_json(output/'inputs.json', signature)
    accepted, triples, queue, papers = [], [], [], []
    stopped = False; fetched = {}
    with httpx.Client(timeout=cfg['timeout_seconds'], follow_redirects=True,
        headers={'Accept': 'application/vnd.orcid+xml', 'User-Agent': 'ScientificNetworkCourse/0.1'}) as client, SourceCache(
            cache_path, client=client, attempts=cfg['max_attempts'], delay=cfg['delay_seconds']) as cache:
        for index, (record, source_ok, reason, mentions) in enumerate(plans, 1):
            checkpoint = output/'records'/(digest(record['paper_id'].encode())+'.json')
            if checkpoint.exists():
                result = json.loads(checkpoint.read_text())
                if result.get('signature_sha256') != record_hash(signature):
                    raise ValueError('corroboration checkpoint inputs changed')
                # A prior access stop is sticky on resume; explicit new version is required.
                stopped |= result.get('collection_stopped', False)
            else:
                result = dict(paper_id=record['paper_id'], signature_sha256=record_hash(signature),
                    original_acquisition_status=record['status'], original_extraction_status=record.get('extraction_status'),
                    source_eligible=source_ok, paper_review_reason=reason,
                    source_decision_id=reviews.get(record['paper_id'], {}).get('decision_id'),
                    accepted_authorships=[], affiliation_triples=[], review_queue=[])
                for mention in mentions:
                    why = mention.pop('preflight_reason')
                    if not why:
                        oid = mention['orcid']
                        if oid not in fetched:
                            try:
                                if stopped:
                                    raise SourceError('ORCID access stopped in this run')
                                fetched[oid] = cache.get(f'https://pub.orcid.org/v3.0/{oid}/works')
                            except QuotaError as exc:
                                stopped = True; fetched[oid] = str(exc)
                            except SourceError as exc:
                                fetched[oid] = str(exc)
                        response = fetched[oid]
                        if isinstance(response, str):
                            why = 'public_orcid_source_unavailable: '+response
                        else:
                            body, proof = response
                            dois = {doi_key((record.get('official') or {}).get('doi')), doi_key(record['openalex_work'].get('doi'))} - {None}
                            try:
                                support = publication_support(body, record['roster']['title'], record['roster']['year'], dois)
                                why = None if support else 'public_orcid_target_publication_not_corroborated'
                            except (ET.ParseError, ValueError):
                                why = 'public_orcid_malformed_works_document'
                    if why:
                        result['review_queue'].append({**mention, 'reason': why})
                        continue
                    researcher = 'researcher:orcid:'+mention['orcid']
                    evidence = dict(roster=dict(url=record['roster']['source_url'], sha256=record['roster']['source_sha256'],
                        locator=record['roster']['source_locator']+';byline_position='+str(mention['byline_position'])),
                        provider=record['openalex_source'], public_orcid={**proof, **support},
                        header=dict(pdf_source=record['pdf_source'], tei_source=record.get('tei_source'),
                            source_decision_id=reviews.get(record['paper_id'], {}).get('decision_id'),
                            locator='complete_ordered_byline;position='+str(mention['byline_position'])))
                    accepted_row = dict(mention, id='authorship:'+record_hash([researcher, record['paper_id']]),
                        researcher_id=researcher, validation_status='accepted', acceptance_scope='development_evidence_contract',
                        method_version=VERSION, evidence=evidence, independent_review=False)
                    result['accepted_authorships'].append(accepted_row)
                    review = reviews.get(record['paper_id'])
                    if review:
                        observations, pending = reviewed_affiliations(record, review, mention['byline_position'], researcher, evidence)
                        result['affiliation_triples'].extend(observations)
                        result['review_queue'].extend({**mention, **p} for p in pending)
                    else:
                        result['review_queue'].append({**mention, 'reason': 'printed_author_affiliation_review_required'})
                result['collection_stopped'] = stopped
                write_json(checkpoint, result)
            accepted.extend(result['accepted_authorships']); triples.extend(result['affiliation_triples'])
            queue.extend(result['review_queue']); papers.append(result)
            print(f'corroborate-diagnostics: {index}/{len(plans)}; accepted authorships={len(accepted)}', flush=True)
    for name, rows in [('papers', papers), ('authorship-support', accepted), ('affiliation-triples', triples), ('review-queue', queue)]:
        write_json(output/(name+'.json'), rows)
    identities = {a['researcher_id'] for a in accepted}
    historical_ids = {n['id'] for n in nodes if n['label'] == 'Researcher'}
    summary = dict(stage='corroborate-diagnostics', **signature, selected_papers=len(papers),
        source_review_overlays=len(reviews), source_eligible_papers=sum(p['source_eligible'] for p in papers),
        eligible_unique_orcids=len(eligible_ids), accepted_researchers=len(identities),
        previously_known_researchers=len(identities & historical_ids), new_researchers=len(identities - historical_ids),
        accepted_authorship_support=len(accepted), accepted_affiliation_triples=len(triples),
        papers_with_accepted_authorships=len({a['paper_id'] for a in accepted}),
        quarantined_provider_work_papers=len(blocked), review_queue_rows=len(queue),
        review_reasons=dict(Counter(q['reason'] for q in queue)),
        original_withheld_records_preserved=sum(p['original_acquisition_status'] != 'acquired' for p in papers),
        original_parser_failures_preserved=sum(p['original_extraction_status'] != 'parsed' for p in papers),
        collection_stopped=stopped, held_out_papers_acquired=0, graph_imports=0,
        semantic_accuracy='not_measured', recall='not_measured', independent_review=False,
        output_sha256={name: digest((output/(name+'.json')).read_bytes()) for name in
                       ('papers', 'authorship-support', 'affiliation-triples', 'review-queue')})
    write_json(output/'summary.json', summary)
    return summary
