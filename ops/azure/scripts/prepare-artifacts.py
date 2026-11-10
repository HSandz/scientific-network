#!/usr/bin/env python3
"""Build versioned runtime artifacts locally; never rebuild scientific results."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def build(root: Path, output: Path):
    if output.exists() or output.is_symlink():
        raise SystemExit('Output already exists; use a new versioned directory.')
    output.mkdir(parents=True)
    inputs = {
        'graph': root / 'data/processed/release-graph-v4/graph.json',
        'analysis': root / 'reports/release-v4/analysis.json',
        'summary.json': root / 'reports/release-v4/graph-summary.json',
        'network-views.json': root / 'reports/final-report/network-views-v4-v1/network-views.json',
        'audit.json': root / 'reports/release-v4/audit-results-agent-v2.json',
        'quality.yaml': root / 'configs/quality-agent-release-v2.yaml',
        'topic-eval.json': root / 'reports/release-v3/topic-eval-agent.json',
        'topic-reuse.json': root / 'reports/release-v4/historical-topic-reuse-v2.json',
    }
    manifest = {'format': 'explorer-runtime-v1', 'sources': {k: {'path': str(p.relative_to(root)), 'sha256': digest(p)} for k, p in inputs.items()}}
    graph = json.loads(inputs['graph'].read_bytes())
    # Preserve each entire evidence/observation object; index only its lookup keys.
    with sqlite3.connect(output / 'ledger.sqlite') as conn:
        conn.executescript('''
            CREATE TABLE evidence (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
            CREATE TABLE affiliations (seq INTEGER PRIMARY KEY, researcher_id TEXT NOT NULL,
                organization_id TEXT NOT NULL, paper_id TEXT NOT NULL, payload TEXT NOT NULL);
            CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        ''')
        conn.executemany('INSERT INTO evidence VALUES (?,?)', ((e['id'], json.dumps(e, ensure_ascii=False, separators=(',', ':'))) for e in graph['evidence']))
        conn.executemany('INSERT INTO affiliations VALUES (?,?,?,?,?)', ((i, a['researcher_id'], a['organization_id'], a['paper_id'], json.dumps(a, ensure_ascii=False, separators=(',', ':'))) for i, a in enumerate(graph['affiliation_observations'])))
        conn.executescript('''
            CREATE INDEX affiliation_researcher ON affiliations(researcher_id);
            CREATE INDEX affiliation_org ON affiliations(organization_id);
            CREATE INDEX affiliation_paper ON affiliations(paper_id);
            CREATE INDEX affiliation_pair ON affiliations(researcher_id, organization_id);
        ''')
        manifest['ledger_counts'] = {'evidence': len(graph['evidence']), 'affiliations': len(graph['affiliation_observations'])}
        conn.execute('INSERT INTO metadata VALUES (?,?)', ('graph_sha256', manifest['sources']['graph']['sha256']))
        conn.commit()
        # Exhaustive roundtrip check, in original observation order.
        for e in graph['evidence']:
            assert json.loads(conn.execute('SELECT payload FROM evidence WHERE id=?', (e['id'],)).fetchone()[0]) == e
        for original, row in zip(graph['affiliation_observations'], conn.execute('SELECT payload FROM affiliations ORDER BY seq'), strict=True):
            assert json.loads(row[0]) == original
        assert conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    del graph
    analysis = json.loads(inputs['analysis'].read_bytes())
    # The API uses base projections and robustness comparisons. Strict projection
    # centrality maps and partitions are omitted; retain compact measured summaries.
    analysis['strict_projections'] = {
        name: {key: p.get(key) for key in ('node_count', 'edge_count', 'isolate_count',
               'weak_or_undirected_component_sizes', 'top_betweenness')}
        for name, p in analysis.get('strict_projections', {}).items()
        if name in ('researcher_collaboration', 'organization_collaboration')
    }
    # Only the first frozen Louvain partition is used by the existing Explorer.
    for projection in analysis.get('projections', {}).values():
        projection['communities'] = projection.get('communities', [])[:1]
    derived_path = root / 'reports/explorer-analysis-release-v1/derived.json'
    if derived_path.is_file():
        derived = json.loads(derived_path.read_bytes())
        if derived['graph_sha256'] != manifest['sources']['graph']['sha256']:
            raise ValueError('Explorer extension belongs to another graph')
        analysis['explorer_derived'] = derived
        manifest['sources']['explorer_derived'] = {'path': str(derived_path.relative_to(root)), 'sha256': digest(derived_path)}
    (output / 'analysis.json').write_text(json.dumps(analysis, ensure_ascii=False, separators=(',', ':')))
    for name, path in inputs.items():
        if name not in ('graph', 'analysis'):
            shutil.copyfile(path, output / name)
    manifest['outputs'] = {p.name: {'sha256': digest(p), 'bytes': p.stat().st_size} for p in sorted(output.iterdir())}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build(args.root.resolve(), args.output.resolve())
