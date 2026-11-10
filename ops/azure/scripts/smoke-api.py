#!/usr/bin/env python3
"""Exercise the public API contract over HTTP(S); fail on missing graph/evidence."""
import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base-url', required=True, help='https://hostname/api or VM loopback URL')
args = parser.parse_args()
base = args.base_url.rstrip('/')
checks = []


def check(path, *, payload=None, expected=200, validate=None):
    started = time.monotonic()
    headers = {'Origin': 'https://scientific-network-explorer.pages.dev'}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        headers['Content-Type'] = 'application/json'
    request = urllib.request.Request(base+path, data=data, headers=headers)
    try:
        response = urllib.request.urlopen(request, timeout=60)
    except urllib.error.HTTPError as exc:
        response = exc
    body = response.read()
    assert response.status == expected, (path, response.status, body[:300])
    if expected == 200:
        assert response.headers.get('Access-Control-Allow-Origin') == headers['Origin'], path
        result = json.loads(body)
        if validate:
            assert validate(result), (path, 'invalid payload')
    else:
        result = {}
    item={'path': path, 'status': response.status, 'seconds': round(time.monotonic()-started,3), 'bytes':len(body)}
    checks.append(item)
    print(json.dumps(item), flush=True)
    return result


check('/live')
check('/ready')
health=check('/health', validate=lambda d:d['database_verified'] and all(d['artifacts'].values()) and d['total_nodes']==47875 and d['total_edges']==225731)
check('/graph/summary', validate=lambda d:d['graph_version']=='release-d3c788c3114a')
check('/graph/schema')
check('/views')
for mode in ('researchers','organizations','citations','heterogeneous'):
    check('/views/'+mode+'?limit=40', validate=lambda d:d['displayed_node_count']>0 and d['displayed_edge_count']>0)
check('/search?q=Piotr%20Faliszewski', validate=lambda d:any(x['id']=='researcher:openalex:A5000000572' for x in d['results']))
check('/search?q=Tuomas%20Sandholm', validate=lambda d:any(x['name']=='Tüomas Sandholm' for x in d['results']))
node='researcher:openalex:A5000000572'
check('/nodes/'+node)
neighbors=check('/nodes/'+node+'/neighbors?limit=40', validate=lambda d:len(d['edges'])>0)
edge=neighbors['edges'][0]['edge_id']
check('/edges/'+edge)
check('/edges/'+edge+'/evidence', validate=lambda d:len(d['evidence_records'])>0 and d['ledger_source']=='artifact_ledger')
# Check aligned affiliation evidence, not just aggregate paper provenance.
rows=check('/table/edges?relation=AFFILIATED_WITH&page_size=5')['items']
check('/edges/'+rows[0]['edge_id']+'/evidence', validate=lambda d:len(d['affiliation_observations'])>0)
check('/nodes/organization:I183067930')
check('/nodes/paper:aaai:2021:17325')
check('/nodes/paper:aaai:2021:17325/neighbors?relations=CITES&direction=incoming&limit=20')
check('/analytics/overview', validate=lambda d:len(d['annual_counts']['rows'])==5)
check('/compare?left_id=organization:I183067930&right_id=organization:I2250653659')
check('/paths', payload={'source_id':'organization:I183067930','target_id':'organization:I2250653659','mode':'collaboration','max_hops':2}, validate=lambda d:d['found'] and d['hop_count']==1)
check('/table/nodes?label=Researcher&page=1&page_size=10', validate=lambda d:len(d['items'])==10)
check('/search?limit=100000', expected=422)
check('/paths', payload={'source_id':'a','target_id':'b','max_hops':100}, expected=422)
check('/nodes/unknown:no-such-node', expected=404)
print(json.dumps({'status':'passed','checks':len(checks),'total_seconds':round(sum(c['seconds'] for c in checks),3)}))
