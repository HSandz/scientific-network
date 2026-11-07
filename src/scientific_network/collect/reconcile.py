"""Conservative pre-enrichment leakage triage; never merges works or allocates splits."""
from collections import Counter, defaultdict
from pathlib import Path
import json

from scientific_network.collect.splits import title_group
from scientific_network.collect.storage import digest, read_jsonl, write_json, write_jsonl

VERSION = 'five-year-leakage-triage-v1'


def leakage_triage(rows: list[dict], previous_rows: list[dict], previous_membership: list[dict], *,
                   method_version: str = VERSION) -> list[dict]:
    previous = {r['paper_id']:r for r in previous_membership}
    history = {r['paper_id']:r for r in previous_rows}
    if len(previous) != len(previous_membership) or not previous.keys() <= history.keys():
        raise ValueError('frozen membership has duplicate IDs or is absent from historical roster')
    included = [r for r in rows if r['status']=='included']
    if len({r['paper_id'] for r in rows}) != len(rows):
        raise ValueError('duplicate official IDs in new roster')
    parent, keys = {}, {}
    def find(x):
        parent.setdefault(x,x)
        if parent[x]!=x:parent[x]=find(parent[x])
        return parent[x]
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b:parent[max(a,b)]=min(a,b)
    # Titles conservatively connect leakage candidates, NOT canonical work identities.
    # Do not use author names: two different people can share exactly the same name.
    for row in list(history.values())+included:
        pid=row['paper_id'];find(pid)
        evidence=[('title_candidate',title_group(row['title']))]
        doi=row.get('doi')
        if doi:evidence.append(('doi',doi.lower().removeprefix('https://doi.org/').strip()))
        for key in evidence:
            if key in keys:union(pid,keys[key])
            else:keys[key]=pid
    groups=defaultdict(set)
    for pid in parent:groups[find(pid)].add(pid)
    output=[]
    for row in included:
        pid=row['paper_id'];members=groups[find(pid)]
        frozen=[previous[k] for k in members if k in previous]
        roles={r['split'] for r in frozen}
        changed=pid in history and title_group(row['title'])!=title_group(history[pid]['title'])
        if 'test' in roles and roles-{'test'}:
            action='quarantine_mixed_historical_exposure'
        elif changed:
            action='quarantine_changed_official_record'
        elif pid in previous:
            action='preserve_existing_assignment'
        elif 'test' in roles:
            action='held_out_version_guard'
        elif frozen or len(members)>1:
            action='quarantine_version_candidate'
        else:
            action='pending_prospective_design'
        output.append({'paper_id':pid,'venue_id':row['venue_id'],'year':row['year'],
            'leakage_candidate_group':digest('\n'.join(sorted(members)).encode()),
            'candidate_paper_ids':sorted(members),'historical_roles':sorted(roles),
            'existing_assignment':previous.get(pid),'action':action,
            'canonical_work_id':None,'is_new_split':False,'method_version':method_version})
    return sorted(output,key=lambda r:r['paper_id'])


def reconcile_rosters(manifest: Path, previous_manifest: Path, membership: Path, output: Path) -> dict:
    summary_path=manifest.parent/'summary.json'
    discovered=json.loads(summary_path.read_text())
    if discovered.get('method_version') not in {'five-year-official-rosters-v1','five-year-official-rosters-v2'} or discovered['manifest_sha256']!=digest(manifest.read_bytes()):
        raise ValueError('five-year discovery contract/hash mismatch')
    method_version = VERSION if discovered['method_version'].endswith('-v1') else 'five-year-leakage-triage-v2'
    inputs={str(p):digest(p.read_bytes()) for p in (manifest,previous_manifest,membership,summary_path)}
    write_json(output/'inputs.json',{'method_version':method_version,'sha256':inputs})
    rows=leakage_triage(read_jsonl(manifest),read_jsonl(previous_manifest),read_jsonl(membership),method_version=method_version)
    write_jsonl(output/'leakage-triage.jsonl',rows)
    summary={'stage':'reconcile-rosters','method_version':method_version,'input_sha256':inputs,
        'included_roster_records':len(rows),'actions':dict(Counter(r['action'] for r in rows)),
        'historical_assignments_preserved':len(read_jsonl(membership)),
        'new_splits_created':0,'canonical_works_merged':0,'enrichment_authorized_by_this_output':False,
        'triage_sha256':digest((output/'leakage-triage.jsonl').read_bytes()),
        'limitations':['Exact normalized title matches guard leakage but do not establish identity.',
                      'Alternate-title versions without shared identifiers require later review.',
                      'Edition completeness and independent prospective sampling still gate enrichment.']}
    write_json(output/'summary.json',summary)
    return summary
