#!/usr/bin/env python3
"""Credential-free host/container RSS, CPU, swap and disk snapshot (run on VM)."""
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import time


def docker(*args):
    return subprocess.check_output(['sudo','-n','docker',*args], text=True)


def snapshot():
    stats=[json.loads(line) for line in docker('stats','--no-stream','--format','{{json .}}').splitlines()]
    processes={}
    for service in ('api','neo4j'):
        name='scientific-network-production-'+service+'-1'
        try:
            rows=docker('top',name,'-eo','pid,comm').splitlines()[1:]
            selected=[]
            for row in rows:
                pid,comm=row.split(None,1)
                if (service=='api' and comm=='uvicorn') or (service=='neo4j' and comm=='java'):
                    fields={}
                    for line in Path('/proc/'+pid+'/status').read_text().splitlines():
                        key,_,value=line.partition(':')
                        if key in ('VmRSS','VmHWM','Threads'): fields[key]=value.strip()
                    selected.append({'pid':int(pid),'command':comm,**fields})
            processes[service]=selected
        except (subprocess.CalledProcessError,FileNotFoundError):
            processes[service]=[]
    mem={}
    for line in Path('/proc/meminfo').read_text().splitlines():
        key,_,value=line.partition(':')
        if key in ('MemTotal','MemAvailable','SwapTotal','SwapFree'): mem[key]=value.strip()
    disk=shutil.disk_usage('/')
    return {'at':datetime.now(timezone.utc).isoformat(),'host':mem,'disk_free_bytes':disk.free,'load_average':Path('/proc/loadavg').read_text().strip(),'processes':processes,'containers':stats}


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--samples',type=int,default=1)
    p.add_argument('--interval',type=float,default=1)
    a=p.parse_args()
    for i in range(a.samples):
        print(json.dumps(snapshot()),flush=True)
        if i+1<a.samples: time.sleep(a.interval)
