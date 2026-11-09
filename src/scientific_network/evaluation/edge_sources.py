"""Extract complete source evidence for edge reviewers; never generate verdicts.

Raw author objects (including observed_orcids) are preserved and compared with
immutable cache records. Packs point to all supporting papers, not clipped HTML.
"""
from collections import defaultdict
from hashlib import sha256
import csv
import json
from pathlib import Path
import re


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def raw_work(oa, cache_dir):
    source = oa['source']
    path = cache_dir / 'objects' / source['raw_sha256']
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != source['raw_sha256']:
        raise ValueError(f'raw cache hash mismatch: {path}')
    doc = json.loads(raw)
    locator = source['locator']
    match = re.match(r'results\[(\d+)\]', locator)
    work = doc['results'][int(match[1])] if match else doc
    if work.get('id') != oa['id'] or work.get('authorships', []) != oa['authorships']:
        raise ValueError(f'raw work/authorship mismatch: {path}#{locator}')
    if work.get('referenced_works', []) != oa['referenced_works']:
        raise ValueError(f'raw references mismatch: {path}#{locator}')
    return path, locator, work


def prepare_sources(graph_path: Path, works_path: Path, sheet: Path, output_dir: Path,
                    cache_dir: Path = Path('data/raw/openalex-release-v1')) -> dict:
    if output_dir.exists() or output_dir.is_symlink():
        raise ValueError('source packets require an unused output directory')
    graph = json.loads(graph_path.read_bytes())
    nodes = {n['id']: n for n in graph['nodes']}
    edges = {e['edge_id']: e for e in graph['edges']}
    evidence = {e['id']: e for e in graph['evidence']}
    works = {r['paper_id']: r for r in map(json.loads, works_path.open())}
    pairpapers = defaultdict(set)
    for obs in graph['affiliation_observations']:
        pairpapers[obs['researcher_id'], obs['organization_id']].add(obs['paper_id'])
    csv.field_size_limit(100_000_000)
    with sheet.open(encoding='utf-8-sig', newline='') as f:
        assignments = list(csv.DictReader(f))
    output_dir.mkdir(parents=True)
    (output_dir / 'papers').mkdir()
    sources = {}
    packets = defaultdict(list)
    for row in assignments:
        edge = edges[row['edge_id']]
        rel = edge['relation']
        pids = {p for eid in edge['evidence_ids'] for p in evidence[eid].get('support_paper_ids', [])}
        if rel == 'AUTHORED':
            pids = {edge['target_id']}
        elif rel in {'CITES', 'HAS_TOPIC', 'PUBLISHED_IN'}:
            pids = {edge['source_id']}
        elif rel == 'AFFILIATED_WITH':
            pids = pairpapers[edge['source_id'], edge['target_id']]
        papers = []
        for pid in sorted(pids):
            if pid not in sources:
                w = works[pid]
                oa = w.get('openalex')
                raw_path, locator, raw = raw_work(oa, cache_dir) if oa else (None, None, None)
                official = w['roster']
                official_paths = list(Path('data/raw').glob('*/objects/' + official['source_sha256']))
                if not official_paths or any(digest(p) != official['source_sha256'] for p in official_paths):
                    raise ValueError(f'official roster source unavailable or hash mismatch: {pid}')
                view = {'official_raw_path': str(official_paths[0]), 'paper_id': pid, 'venue_id': w['venue_id'], 'year': w['year'], 'roster': w['roster'],
                        'match': w['match'], 'openalex': oa, 'full_raw_work': raw,
                        'raw_path': str(raw_path) if raw_path else None, 'raw_locator': locator,
                        'raw_sha256': digest(raw_path) if raw_path else None}
                dest = output_dir / 'papers' / (pid.replace(':', '_') + '.json')
                dest.write_text(json.dumps(view, ensure_ascii=False) + '\n')
                sources[pid] = {'paper_id': pid, 'path': str(dest), 'sha256': digest(dest),
                                'source_locator': str(raw_path) + '#' + str(locator) if raw_path else None,
                                'source_sha256': digest(raw_path) if raw_path else None}
            papers.append(sources[pid])
        packets[row['reviewer_id']].append({'edge': edge, 'source': nodes[edge['source_id']],
             'target': nodes[edge['target_id']], 'evidence': [evidence[i] for i in edge['evidence_ids']],
             'all_supporting_papers': papers, 'taxonomy_source': 'configs/topics-release-v1.yaml' if rel == 'SUBTOPIC_OF' else None})
    paths = []
    for reviewer, rows in packets.items():
        path = output_dir / f'{reviewer}-edge-sources.jsonl'
        path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
        paths.append({'path': str(path), 'sha256': digest(path), 'assigned_edges': len(rows)})
    receipt = {'graph_sha256': digest(graph_path), 'works_sha256': digest(works_path), 'sheet_sha256': digest(sheet),
               'source_paper_count': len(sources), 'raw_authorships_and_references_exactly_verified': True,
               'projection': 'complete original authorships including observed_orcids; full raw work; all support paper pointers',
               'verdicts_generated': False, 'packets': paths, 'papers': list(sources.values())}
    (output_dir / 'source-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt
