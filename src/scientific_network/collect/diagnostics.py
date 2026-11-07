"""Prospective, input-bound layout/year diagnostics; existing splits are immutable."""
from collections import Counter, defaultdict
import json
from pathlib import Path
import random

from scientific_network.collect.storage import digest, read_config, read_jsonl, write_json, write_jsonl
from scientific_network.collect.splits import title_group

VERSION='five-year-diagnostics-v1'


def allocate_diagnostics(rows: list[dict], ledger: list[dict], triage: list[dict],
                         previous: list[dict], config: dict) -> tuple[list[dict],list[dict],list[dict]]:
    old={r['paper_id']:r for r in previous}
    if len(old)!=len(previous):raise ValueError('duplicate historical assignments')
    by_id={r['paper_id']:r for r in rows}
    if len(by_id)!=len(rows):raise ValueError('duplicate official roster IDs')
    checked={r['paper_id']:r for r in triage}
    if len(checked)!=len(triage) or checked.keys()!={r['paper_id'] for r in rows if r['status']=='included'}:
        raise ValueError('triage does not cover every included record exactly once')
    eligible={(e['venue_id'],e['year']):e for e in ledger if e['status']=='verified_eligible'}
    membership=[dict(r) for r in previous];strata=defaultdict(list);diagnostics=[];frames=[]
    for pid,row in sorted(by_id.items()):
        if row['status']!='included' or pid in old:continue
        review=checked[pid]
        complete=(row['venue_id'],row['year']) in eligible
        safe=review['action']=='pending_prospective_design' and len(review['candidate_paper_ids'])==1 and not review['historical_roles']
        assignment=dict(paper_id=pid,venue_id=row['venue_id'],leakage_group=title_group(row['title']),split='review',is_pilot=False)
        if complete and safe:
            edition=eligible[(row['venue_id'],row['year'])]
            family=edition['routes'][0]['adapter']
            strata[f'{family}:{row["year"]}'].append((row,assignment,review))
        else:
            if review['action']=='held_out_version_guard':assignment['split']='test'
            membership.append(assignment)
    ntest,ndev=config['test_groups_per_stratum'],config['diagnostic_groups_per_stratum']
    if type(ntest)!=int or type(ndev)!=int or min(ntest,ndev)<1:raise ValueError('positive sample counts required')
    for stratum,entries in sorted(strata.items()):
        if len(entries)<ntest+ndev:raise ValueError(f'insufficient independent new groups: {stratum}')
        # Seeded PRNG permutation of sorted IDs: equal inclusion probability within
        # each finite stratum. Hash binds each stratum to an independent PRNG seed.
        ordered=sorted(entries,key=lambda v:v[0]['paper_id'])
        random.Random(int(digest(f'{config["seed"]}|{stratum}'.encode()),16)).shuffle(ordered)
        for index,(row,assignment,review) in enumerate(ordered):
            assignment['split']='test' if index<ntest else 'development' if index<ntest+ndev else 'pool'
            membership.append(assignment)
            if ntest<=index<ntest+ndev:
                diagnostics.append({'paper_id':row['paper_id'],'venue_id':row['venue_id'],'year':row['year'],
                    'stratum':stratum,'leakage_candidate_group':review['leakage_candidate_group'],
                    'selection_probability':ndev/len(entries),'conditional_probability_after_test_reservation':ndev/(len(entries)-ntest)})
        frames.append({'stratum':stratum,'population':len(entries),'test_groups':ntest,
            'development_diagnostics':ndev,'test_probability':ntest/len(entries),
            'diagnostic_probability':ndev/len(entries),
            'pool_groups':len(entries)-ntest-ndev})
    if not diagnostics:raise ValueError('no independent eligible diagnostic strata')
    if len(diagnostics)>config['metadata']['max_papers']:raise ValueError('diagnostic batch exceeds frozen cap')
    assigned={r['paper_id']:r for r in membership}
    if len(assigned)!=len(membership) or any(assigned[k]!=v for k,v in old.items()):
        raise ValueError('historical assignments changed or duplicated')
    test_titles={r['leakage_group'] for r in membership if r['split']=='test'}
    if any(assigned[r['paper_id']]['split']!='development' or title_group(by_id[r['paper_id']]['title']) in test_titles for r in diagnostics):
        raise ValueError('held-out title/version group overlaps diagnostic selection')
    return sorted(membership,key=lambda r:r['paper_id']),sorted(diagnostics,key=lambda r:r['paper_id']),frames


def freeze_diagnostics(manifest: Path, triage_path: Path, config_path: Path, output: Path) -> dict:
    config=read_config(config_path);discovered=json.loads((manifest.parent/'summary.json').read_text())
    if discovered['manifest_sha256']!=digest(manifest.read_bytes()):raise ValueError('manifest hash changed')
    ledger_path=manifest.parent/'edition-ledger.jsonl'
    if discovered['edition_ledger_sha256']!=digest(ledger_path.read_bytes()):raise ValueError('edition ledger hash changed')
    triage_summary=json.loads((triage_path.parent/'summary.json').read_text())
    if triage_summary['triage_sha256']!=digest(triage_path.read_bytes()) or triage_summary['input_sha256'].get(str(manifest))!=digest(manifest.read_bytes()):
        raise ValueError('triage input/output hash mismatch')
    paths={'historical_manifest':Path(config['historical_manifest']),
           'historical_membership':Path(config['historical_membership']),
           'legacy_membership':Path(config['legacy_membership'])}
    for key,path in paths.items():
        if digest(path.read_bytes())!=config[key+'_sha256']:raise ValueError(f'protected {key} hash changed')
    previous=read_jsonl(paths['historical_membership']);old={r['paper_id']:r for r in previous}
    if any(old.get(r['paper_id'])!=r for r in read_jsonl(paths['legacy_membership'])):
        raise ValueError('original assignments differ from expanded historical assignments')
    inputs={str(p):digest(p.read_bytes()) for p in [manifest,ledger_path,triage_path,config_path,*paths.values()]}
    write_json(output/'inputs.json',{'method_version':VERSION,'sha256':inputs})
    members,selected,frames=allocate_diagnostics(read_jsonl(manifest),read_jsonl(ledger_path),read_jsonl(triage_path),previous,config)
    write_jsonl(output/'membership.jsonl',members);write_jsonl(output/'diagnostics.jsonl',selected);write_json(output/'strata.json',frames)
    old_ids={r['paper_id'] for r in previous}
    write_jsonl(output/'reserved-tests.jsonl',[r for r in members if r['split']=='test' and r['paper_id'] not in old_ids])
    summary={'stage':'freeze-diagnostics','method_version':VERSION,'input_sha256':inputs,
        'manifest_sha256':digest(manifest.read_bytes()),'membership_sha256':digest((output/'membership.jsonl').read_bytes()),
        'diagnostics_sha256':digest((output/'diagnostics.jsonl').read_bytes()),'config_sha256':digest(config_path.read_bytes()),
        'reserved_tests_sha256':digest((output/'reserved-tests.jsonl').read_bytes()),
        'historical_assignments_preserved':len(previous),'new_diagnostic_papers':len(selected),
        'new_test_groups':sum(r['test_groups'] for r in frames),'strata':len(frames),
        'by_split':dict(Counter(r['split'] for r in members)),'seed':config['seed'],
        'held_out_diagnostic_overlap':0,'sample_status':'frozen_unannotated_development_diagnostics',
        'inference_population':'new eligible singleton records within source-family/year strata; not full registry or release audit',
        'work_identity':'provisional_per_official_record; unresolved versions quarantined; no title-based canonical merges'}
    write_json(output/'summary.json',summary)
    return summary
