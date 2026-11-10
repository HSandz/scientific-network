#!/usr/bin/env python3
"""Run a bounded representative workload and record RSS before/after each phase on VM."""
import json
from pathlib import Path
import subprocess
import time
import urllib.request

base='http://127.0.0.1:8000/api'
node='researcher:openalex:A5000000572'
for phase,path in [('idle','/ready'),('global_search','/search?q=Tuomas%20Sandholm'),('neighborhood','/nodes/'+node+'/neighbors?limit=150'),('analytics','/analytics/overview')]:
    before=time.monotonic()
    for _ in range(3):
        with urllib.request.urlopen(base+path,timeout=45) as response:
            data=json.load(response)
    elapsed=time.monotonic()-before
    snapshot=json.loads(subprocess.check_output(['python3',str(Path(__file__).with_name('resource-snapshot.py'))],text=True))
    print(json.dumps({'phase':phase,'requests':3,'seconds':round(elapsed,3),'snapshot':snapshot}),flush=True)
