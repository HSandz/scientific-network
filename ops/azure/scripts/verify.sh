#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
"${COMPOSE[@]}" exec -T api python - <<'PY'
import hashlib
import json
from pathlib import Path
import urllib.request
p=Path('/artifacts')
m=json.loads((p/'manifest.json').read_bytes())
assert m['format']=='explorer-runtime-v1'
assert json.loads((p/'summary.json').read_bytes())['graph_version']=='release-d3c788c3114a'
for name, expected in m['outputs'].items():
    h=hashlib.sha256()
    with (p/name).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    assert h.hexdigest()==expected['sha256'], name
for path in ('ready','health','graph/summary','analytics/overview'):
    with urllib.request.urlopen('http://127.0.0.1:8000/api/'+path, timeout=30) as r:
        d=json.load(r)
    if path=='health':
        assert d['database_verified'] and all(d['artifacts'].values()), d
        assert (d['total_nodes'],d['total_edges']) == (47875,225731)
    print(path, 'passed')
print('All artifact hashes passed')
PY

# Public HTTPS and complete graph/evidence/path/analytics contract are part of
# the transaction: a failure here rolls back just like a readiness failure.
timeout 180 python3 "$AZURE_COMPOSE_DIR/scripts/smoke-api.py" --base-url https://scientific-network-api.eastasia.cloudapp.azure.com/api
