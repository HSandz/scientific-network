"""Offline technical review of frozen diagnostics; never adjudicates identities.

Decisions preserve the original queue, exact source references and stable row IDs.
This is agent triage, not independent semantic annotation or a graph override.
"""
from collections import Counter
import json
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl
import xml.etree.ElementTree as ET

from scientific_network.collect.acquire import official_metadata, normalize, names_compatible
from scientific_network.collect.storage import digest, read_config, read_jsonl, write_json
from scientific_network.contracts import GraphArtifact
from scientific_network.graph.validate import validate_graph
from scientific_network.resolve.pilot import align_header, match_institution, orcid_support

VERSION = 'frozen-diagnostic-evidence-review-v1'


def review_evidence(acquired_path: Path, headers_path: Path, graph_path: Path,
                    queue_path: Path, manifest_path: Path, membership_path: Path,
                    cache_path: Path, output: Path, config_path: Path) -> dict:
    acquired = json.loads(acquired_path.read_text())
    headers = {r['paper_id']: r for r in json.loads(headers_path.read_text())}
    manifest = {r['paper_id']: r for r in read_jsonl(manifest_path)}
    assignments = read_jsonl(membership_path)
    frozen = json.loads((membership_path.parent / 'summary.json').read_text())
    expected = {'manifest_sha256': digest(manifest_path.read_bytes()),
                'membership_sha256': digest(membership_path.read_bytes()),
                'corpus_config_sha256': digest(config_path.read_bytes())}
    if any(frozen.get(k) != v for k, v in expected.items()):
        raise ValueError('review inputs differ from frozen split hashes')
    pilot = {r['paper_id'] for r in assignments if r['is_pilot']}
    held_out_groups = {r['leakage_group'] for r in assignments if r['split'] == 'test'}
    if any(r['is_pilot'] and (r['split'] not in {'development', 'pool'} or
           r['leakage_group'] in held_out_groups) for r in assignments):
        raise ValueError('held-out paper/group cannot enter development review')
    if len({r['paper_id'] for r in acquired}) != len(acquired) or {r['paper_id'] for r in acquired} != pilot:
        raise ValueError('review requires exactly the frozen diagnostic IDs')
    graph = GraphArtifact.model_validate_json(graph_path.read_bytes())
    errors = validate_graph(graph)
    if errors:
        raise ValueError('review input graph is invalid: ' + '; '.join(errors[:3]))
    if not {n.id for n in graph.nodes if n.label == 'Paper'} <= pilot:
        raise ValueError('review graph includes non-diagnostic papers')
    config = read_config(config_path)
    if config.get('legacy_membership'):
        legacy = read_jsonl(Path(config['legacy_membership']))
        current = {r['paper_id']: r for r in assignments}
        if any(current.get(r['paper_id']) != r for r in legacy):
            raise ValueError('legacy frozen assignments changed')
    queue = json.loads(queue_path.read_text())
    if any(r['paper_id'] not in pilot for r in queue):
        raise ValueError('review queue includes non-diagnostic papers')
    paths = {'acquired': acquired_path, 'headers': headers_path, 'graph': graph_path,
             'queue': queue_path, 'manifest': manifest_path, 'membership': membership_path,
             'corpus_config': config_path}
    signature = {k: {'path': str(v), 'sha256': digest(v.read_bytes())} for k, v in paths.items()}
    write_json(output / 'inputs.json', {'method_version': VERSION, 'inputs': signature})
    checked = set()

    def raw(sha):
        body = (cache_path / 'objects' / sha).read_bytes()
        if digest(body) != sha:
            raise ValueError('review source-cache hash mismatch: ' + sha)
        checked.add(sha)
        return body

    def cached_url(url):
        parts = urlsplit(url)
        descriptor = {'url': urlunsplit((parts.scheme, parts.netloc, parts.path, '', '')),
                      'params': dict(parse_qsl(parts.query, keep_blank_values=True))}
        key = digest(json.dumps(descriptor, sort_keys=True).encode())
        path = cache_path / 'requests' / (key + '.json')
        if not path.exists():
            return None, None
        source = json.loads(path.read_text())
        return raw(source['sha256']), source

    bylines = []
    for record in acquired:
        if record['status'] == 'acquired':
            continue
        row = manifest[record['paper_id']]
        body, source = cached_url(row['official_url'])
        decision = {'decision_id': 'byline:' + digest((signature['acquired']['sha256'] + '|' + record['paper_id']).encode()),
                    'paper_id': record['paper_id'], 'original_status': record['status'],
                    'original_reason': record.get('reason'), 'original_roster_authors': row['authors'],
                    'identity_overrides': [], 'source': source,
                    'method_version': VERSION, 'reviewer': 'Codex', 'independent_review': False}
        if body is None:
            decision.update(disposition='retain_withheld', reason='official_detail_not_cached')
        else:
            try:
                meta = official_metadata(body, row)
                decision.update(disposition='source_byline_recovered',
                    reason='visible_acl_byline_agrees_with_roster' if meta['byline_discrepancies'] else 'unicode_name_tokens_preserved',
                    selected_authors=meta['authors'], selected_locator=meta['author_locator'],
                    citation_authors=meta['citation_authors'], discrepancies=meta['byline_discrepancies'])
            except ValueError as exc:
                decision.update(disposition='retain_withheld', reason=str(exc))
        bylines.append(decision)

    decisions = []
    for ordinal, row in enumerate(queue, 1):
        r = headers[row['paper_id']]
        reason = row['reason']
        refs = []
        triage = reason
        if reason == 'orcid_publication_not_corroborated':
            author = r['openalex_work']['authorships'][row['byline_position']-1]['author']
            url = f"https://pub.orcid.org/v3.0/{author['orcid'].rsplit('/', 1)[-1]}/works"
            body, source = cached_url(url)
            if source:
                refs.append(source)
            if body is None:
                triage = 'orcid_request_failure_uncached'
            else:
                try:
                    ids = {normalize(v.removeprefix('https://doi.org/')) for v in
                           [r['official'].get('doi'), r['openalex_work'].get('doi')] if v}
                    support = orcid_support(body, r['official']['title'], ids)
                    root = ET.fromstring(body)
                    triage = ('corroboration_now_present_requires_resolution_replay' if support else
                              'orcid_public_works_empty' if not root.findall('{*}group') else
                              'orcid_public_works_no_target_publication')
                except ET.ParseError:
                    triage = 'orcid_cached_response_not_parseable'
        elif reason == 'printed_institution_needs_canonical_review':
            authorship = r['openalex_work']['authorships'][row['byline_position']-1]
            institutions = authorship.get('institutions', [])
            other = [i for idx, a in enumerate(r['openalex_work']['authorships'], 1)
                     if idx != row['byline_position'] for i in a.get('institutions', [])]
            if not institutions:
                triage = 'missing_authorship_specific_institution_evidence'
            elif any(normalize(row['printed_institution']) == normalize(i['display_name']) for i in other) and not match_institution(row['printed_institution'], institutions):
                triage = 'possible_cross_author_pdf_mapping_requires_marker_review'
            else:
                triage = 'institution_alias_or_hierarchy_requires_source_review'
            refs = [r['openalex_source']]
            for key in ('pdf_source', 'tei_source'):
                if r.get(key):
                    refs.append(r[key])
        elif reason == 'pdf_author_alignment_missing_or_ambiguous':
            triage = 'official_pdf_unavailable' if not r['official'].get('pdf_url') else 'pdf_header_name_segmentation_requires_review'
            refs = [r[k] for k in ('pdf_source', 'tei_source') if r.get(k)]
        elif r.get('openalex_source'):
            refs = [r['openalex_source']]
        for source in refs:
            raw(source['sha256'])
        decisions.append({'decision_id': 'review:' + digest(f"{signature['queue']['sha256']}|{ordinal}".encode()),
            'source_queue_sha256': signature['queue']['sha256'], 'source_row': ordinal,
            'original_record': row, 'disposition': 'retain_withheld', 'triage_reason': triage,
            'source_references': refs, 'method_version': VERSION,
            'reviewer': 'Codex', 'independent_review': False, 'graph_overrides': []})

    technical = []
    by_node = {n.id: n for n in graph.nodes}
    evidence = {e.id: e for e in graph.evidence}
    authors = {(e.source_id, e.target_id): e for e in graph.edges if e.relation == 'AUTHORED'}
    for (researcher, paper), edge in authors.items():
        record = headers[paper]
        position = edge.properties['byline_position']
        name = record['official']['authors'][position-1]
        identity = by_node[researcher]
        url = f"https://pub.orcid.org/v3.0/{identity.properties['orcid']}/works"
        proofs = [evidence[eid] for eid in edge.evidence_ids]
        orcid_proofs = [p for p in proofs if str(p.source_url) == url]
        ids = {normalize(v.removeprefix('https://doi.org/')) for v in
               [record['official'].get('doi'), record['openalex_work'].get('doi')] if v}
        status = bool(orcid_proofs and names_compatible(name, identity.name))
        for proof in proofs:
            raw(proof.raw_sha256)
        if orcid_proofs:
            status = status and bool(orcid_support(raw(orcid_proofs[0].raw_sha256), record['official']['title'], ids))
        technical.append({'claim_id': edge.edge_id, 'kind': 'accepted_identity', 'paper_id': paper,
                          'check': 'stored_byline_identifier_public_work_and_hash_consistency',
                          'status': 'passed' if status else 'needs_review', 'independent_semantic_check': False})
    for obs in graph.affiliation_observations:
        record = headers[obs.paper_id]
        edge = authors[obs.researcher_id, obs.paper_id]
        pos = edge.properties['byline_position']
        header = align_header(record['official']['authors'][pos-1], record.get('header_authors', []))
        institutions = record['openalex_work']['authorships'][pos-1].get('institutions', [])
        matched = [match_institution(printed, institutions) for aff in (header or {}).get('affiliations', [])
                   for printed in aff['institutions']]
        status = any(i and 'organization:' + i['id'].rsplit('/', 1)[-1] == obs.organization_id for i in matched)
        for eid in obs.evidence_ids:
            raw(evidence[eid].raw_sha256)
        if record.get('tei_source'):
            raw(record['tei_source']['sha256'])
        technical.append({'claim_id': obs.id, 'kind': 'accepted_affiliation', 'paper_id': obs.paper_id,
                          'check': 'stored_author_specific_tei_exact_institution_and_hash_consistency',
                          'status': 'passed' if status else 'needs_review', 'independent_semantic_check': False})
    write_json(output / 'byline-decisions.json', bylines)
    write_json(output / 'queue-decisions.json', decisions)
    write_json(output / 'accepted-technical-checks.json', technical)
    summary = {'stage': 'review', 'method_version': VERSION, 'inputs': signature,
        'graph_version_reviewed': graph.graph_version,
        'diagnostic_papers': len(pilot), 'held_out_overlap': 0,
        'byline_decisions': dict(Counter(d['disposition'] for d in bylines)),
        'queue_records': len(decisions), 'original_queue_reasons': dict(Counter(r['reason'] for r in queue)),
        'triage_reasons': dict(Counter(d['triage_reason'] for d in decisions)),
        'accepted_technical_checks': dict(Counter(f"{d['kind']}:{d['status']}" for d in technical)),
        'source_objects_hash_checked': len(checked), 'graph_overrides_applied': 0,
        'semantic_accuracy': 'not_measured', 'independent_audit': 'not_performed'}
    write_json(output / 'summary.json', summary)
    return summary
