"""Replay at most 40 explicitly listed, public Task2B evidence requests.

Restoring cached bytes is reproducible; reacquiring current API responses is not
restoration of a historical snapshot. No expansion/crawling or credentials.
"""
import argparse
from pathlib import Path
import json
from urllib.parse import urlsplit

from scientific_network.collect.storage import SourceCache, SourceError, write_json
from scientific_network.quality.identity_audit import unused


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--requests',required=True,type=Path,nargs='+')
    p.add_argument('--cache',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();unused(a.output)
    requests=[r for path in a.requests for r in json.loads(path.read_bytes())]
    if len(requests)>40:raise ValueError('bounded enrichment permits at most 40 requests')
    allowed={'api.crossref.org','pub.orcid.org','www.sigs.tsinghua.edu.cn'}
    urls=[r.get('record',{}).get('url') or r.get('url') for r in requests]
    if any(urlsplit(u).scheme!='https' or urlsplit(u).hostname not in allowed or urlsplit(u).query for u in urls):
        raise ValueError('only explicitly scoped public endpoints permitted')
    ledger=[]
    with SourceCache(a.cache,timeout=20,attempts=1) as cache:
        cache.client.headers['Accept']='application/json'
        for request,url in zip(requests,urls):
            try:
                _,rec=cache.get(url)
                ledger.append({'source':request.get('source'),'key':request['key'],'record':rec})
            except SourceError as exc:
                ledger.append({'source':request.get('source'),'key':request['key'],'url':url,'failure':str(exc)})
                # Respect access/quota failures; do not continue collecting.
                if any(code in str(exc) for code in ('401','402','403','429')):break
    write_json(a.output,ledger)
    print(json.dumps({'requests':len(ledger),'failures':sum('failure' in r for r in ledger)}))
if __name__=='__main__':main()
