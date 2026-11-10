#!/usr/bin/env python3
"""Fail closed on any scientific inventory, schema or full-content difference."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', type=Path)
parser.add_argument('target', type=Path)
a = parser.parse_args()
s, t = (json.loads(p.read_bytes()) for p in (a.source, a.target))
keys = ('total_nodes', 'total_relationships', 'nodes_by_label', 'relationships_by_type', 'node_graph_versions', 'relationship_graph_versions', 'node_projects', 'relationship_projects', 'samples', 'graph_fingerprints', 'constraints', 'indexes', 'all_indexes_online')
failures = [k for k in keys if k not in s or k not in t or s[k] != t[k]]
if not s.get('connected') or not t.get('connected'):
    failures.append('connectivity')
print(json.dumps({'status': 'failed' if failures else 'passed', 'compared_fields': list(keys), 'differences': failures, 'graph_fingerprints': t.get('graph_fingerprints')}, indent=2))
raise SystemExit(bool(failures))
