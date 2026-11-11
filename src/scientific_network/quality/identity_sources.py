"""Bounded Task2C public source collection; immutable cache, host access stops.

An explicitly listed source is a lead, never an automatic identity reference.
No construction evidence is relabeled as independent gold by this command.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.parse import urlsplit

from scientific_network.collect.storage import SourceCache, SourceError, write_json
from scientific_network.quality.identity_audit import unused, file_hash

ALLOWED = {'www.kroening.com','clarken92.github.io','harabor.net','www.cs.uni-potsdam.de',
           'www.csc2.ncsu.edu','proceedings.biocomplexity.virginia.edu','jpdickerson.com',
           'www.sigs.tsinghua.edu.cn','ojs.aaai.org','www.ijcai.org'}


def collect(plan_path, cache_path, output):
    unused(output)
    plan = json.loads(plan_path.read_bytes())
    if not 0 < len(plan) <= 48: raise ValueError('at most 48 explicit source requests')
    if len({r['url'] for r in plan}) != len(plan): raise ValueError('duplicate request URL')
    for r in plan:
        u=urlsplit(r['url'])
        if u.scheme!='https' or u.hostname not in ALLOWED or u.query or u.username or u.password:
            raise ValueError('unscoped source URL')
    blocked=set(); ledger=[]
    with SourceCache(cache_path,timeout=18,attempts=1,delay=.2) as cache:
        for r in plan:
            host=urlsplit(r['url']).hostname
            rec={**r,'attempted_at':datetime.now(timezone.utc).isoformat(),
                 'source_role':'evaluation_lead_not_gold','upstream_independence':'not_established'}
            if host in blocked:
                ledger.append({**rec,'status':'not_requested_host_access_stop'});continue
            try:
                _,source=cache.get(r['url'])
                ledger.append({**rec,'status':'retrieved','record':source})
            except SourceError as exc:
                ledger.append({**rec,'status':'unavailable','failure':str(exc)})
                if any(c in str(exc) for c in ('401','402','403','429')): blocked.add(host)
            # Checkpoint each outcome without replacing immutable final artifacts.
            progress=cache_path/'progress.json';progress.parent.mkdir(parents=True,exist_ok=True)
            progress.write_text(json.dumps(ledger,indent=2)+'\n')
    write_json(output,{'plan_sha256':file_hash(plan_path),'sources':ledger,
                       'limitation':'source retrieval is not independent adjudication'})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('plan','cache','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();collect(a.plan,a.cache,a.output)

if __name__=='__main__':main()
