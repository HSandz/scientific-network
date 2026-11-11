"""Prospective identity sampling and scoring; no automatic reference labels.

Assignment precision uses adjudicated correctness; recall additionally requires a
reference identity even for rejected positions. Pair recall is for the declared
sampled pair frame, never implicitly population-wide. Unknown labels stay unknown.
"""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import random

from scientific_network.collect.acquire import name_tokens
from scientific_network.collect.storage import read_jsonl, write_json, write_jsonl
from scientific_network.quality.identity_audit import file_hash, unused

METHOD = 'identity-evaluation-v1'
SEED = 2026111104


def sample_frame(items, n, rng, frame):
    items = sorted(items, key=lambda x: x['unit_id'])
    chosen = rng.sample(items, min(n, len(items)))
    return [dict(x, frame=frame, population=len(items), inclusion_probability=min(n, len(items))/len(items))
            for x in sorted(chosen, key=lambda x: x['unit_id'])] if items else []


def freeze(decisions, output, inputs, n=200):
    unused(output)
    rng = random.Random(SEED)
    mentions = {d['mention_id']: d for d in decisions}
    units = [{'unit_id': d['mention_id'], 'paper_id': d['paper_id'], 'author_position': d['author_position']}
             for d in decisions]
    assignment = sample_frame(units, n, rng, 'all_official_positions')
    # Fixed diagnostic frame deliberately separated from probability assignment draw.
    groups = defaultdict(list)
    for d in decisions:
        if d['decision_reason'] == 'author_id_incompatible_name_variants': category = 'name_variants'
        elif d['was_v4_global_identity_withheld']: category = 'orcid_conflict'
        elif not d['source_author_id']: category = 'missing_provider_id'
        elif d['decision_reason'] == 'work_doi_disagreement': category = 'doi_disagreement'
        else: category = 'other'
        groups[category].append({'unit_id': d['mention_id'], 'paper_id': d['paper_id'], 'author_position': d['author_position']})
    diagnostic = [u for k in sorted(groups) if k != 'other' for u in sample_frame(groups[k], 30, rng, 'diagnostic:'+k)]
    # Probability pair frame: all pairs within the same provider OR normalized-name
    # block, union deduplicated. Includes rejected positions and competing IDs.
    blocks = defaultdict(list)
    for d in decisions:
        if d['source_author_id']: blocks['provider:'+d['source_author_id']].append(d['mention_id'])
        blocks['name:'+' '.join(name_tokens(d['official_name']))].append(d['mention_id'])
    pairs = set()
    for block in blocks.values():
        for i, a in enumerate(sorted(block)):
            for b in sorted(block)[i+1:]: pairs.add((a,b))
    pair_units = [{'unit_id': 'pair:'+sha256((a+'|'+b).encode()).hexdigest()[:24], 'left': a, 'right': b} for a,b in sorted(pairs)]
    pair_sample = sample_frame(pair_units, n, rng, 'provider_or_name_block_pairs')
    # Predictions absent from reviewer forms. Construction evidence is explicit,
    # independent sources must be added by reviewers; packets are not gold.
    selected = {u['unit_id'] for u in assignment+diagnostic}
    selected.update(u[k] for u in pair_sample for k in ('left','right'))
    packets = [{k:d[k] for k in ('mention_id','paper_id','author_position','official_name','raw_author_name','canonical_display_name','source_author_id','paper_raw_orcid','profile_orcid','supporting_evidence')}
               for mid,d in sorted(mentions.items()) if mid in selected]
    write_jsonl(output/'assignment-sample.jsonl', assignment)
    write_jsonl(output/'diagnostic-sample.jsonl', diagnostic)
    write_jsonl(output/'pair-sample.jsonl', pair_sample)
    write_jsonl(output/'evidence-packets.jsonl', packets)
    all_units = {u['unit_id']:u for u in assignment+diagnostic+pair_sample}
    assignments = []
    for uid in sorted(all_units):
        for reviewer in ('A','B'):
            assignments.append({'unit_id':uid, 'reviewer':reviewer, 'label':None, 'reference_identity':None,
                                'evidence':[], 'independence':None, 'adjudication':None})
    write_jsonl(output/'blank-reviewer-assignments.jsonl', assignments)
    manifest = {'method':METHOD,'seed':SEED,'inputs':inputs,'assignment_population':len(units),'pair_population':len(pairs),
                'assignment_n':len(assignment),'pair_n':len(pair_sample),'diagnostic_n':len(diagnostic),
                'pair_scope':'union of same-provider and exact normalized-name blocks; outside-block false splits not estimable',
                'semantic_metrics_status':'unavailable_no_independent_adjudicated_labels',
                'source_exposure':'construction metadata inspected; no independent reference labels used; historical audit labels excluded',
                'files':{p.name:file_hash(p) for p in sorted(output.iterdir())}}
    write_json(output/'freeze.json',manifest)
    return manifest


def score(sample, references, predictions, *, pair=False):
    """Score only complete independent adjudicated references; reject partial gold.

    References: unit_id, label (same/different or identity/unresolvable), evidence,
    independence='independent', adjudication='complete', reference_identity for
    assignment recall. Predictions map unit IDs to canonical IDs or pair booleans.
    """
    keys = [s['unit_id'] for s in sample]
    if len(keys) != len(set(keys)): raise ValueError('duplicate sampled unit')
    refs = {r['unit_id']:r for r in references}
    if len(refs) != len(references): raise ValueError('duplicate references')
    valid = {'same','different'} if pair else {'identity','unresolvable'}
    missing = [k for k in keys if k not in refs or refs[k].get('label') not in valid or
               refs[k].get('independence') != 'independent' or refs[k].get('adjudication') != 'complete' or not refs[k].get('evidence') or
               (not pair and refs[k].get('label')=='identity' and
                (not refs[k].get('reference_identity') or not refs[k].get('accepted_canonical_ids')))]
    if missing:
        return {'status':'unavailable_incomplete_independent_references','sample_n':len(keys),'missing_or_invalid':len(missing),
                'precision':None,'recall':None,'f1':None}
    if any(k not in predictions for k in keys): raise ValueError('missing candidate predictions')
    tp=fp=fn=0.0; accepted=0
    for s in sample:
        k=s['unit_id'];r=refs[k];p=predictions[k]
        pi=s['inclusion_probability']
        if not 0 < pi <= 1: raise ValueError('invalid inclusion probability')
        w=1/pi
        positive=bool(p)
        truth=(r['label']=='same') if pair else r['label']=='identity'
        correct=(r['label']=='same') if pair else p in r.get('accepted_canonical_ids', [])
        accepted += positive
        tp += w*bool(positive and correct)
        fp += w*bool(positive and not correct)
        fn += w*bool(truth and (not positive or not correct))
    precision=tp/(tp+fp) if tp+fp else None
    recall=tp/(tp+fn) if tp+fn else None
    f1=2*precision*recall/(precision+recall) if precision is not None and recall is not None and precision+recall else None
    return {'status':'scored','sample_n':len(keys),'accepted_n':accepted,'coverage':accepted/len(keys) if keys else None,
            'precision':precision,'recall':recall,'f1':f1,
            'estimated_false_merge_pairs' if pair else 'estimated_incorrect_assignments':fp,
            'estimated_false_split_pairs' if pair else 'estimated_missed_assignments':fn,
            'intervals':None,'interval_limitation':'use stratified survey or paired bootstrap for ratios; no unsupported Wilson interval on weighted totals'}


def paired_score(sample, references, predictions, *, pair=False, replicates=1000):
    """Same sampled units for every candidate; paired SRS bootstrap of differences.

    Ratios use inverse inclusion weights. This bootstrap is for one declared SRS
    frame, with no finite-population correction. Diagnostic frames stay separate.
    """
    results={name:score(sample,references,pred,pair=pair) for name,pred in predictions.items()}
    if any(r['status']!='scored' for r in results.values()):
        return {'status':'unavailable_no_complete_independent_references','candidates':results,
                'paired_differences':None,'confidence_intervals':None}
    if len({s['frame'] for s in sample})!=1:raise ValueError('do not pool diagnostic or distinct sampling frames')
    import numpy as np
    rng=random.Random(SEED);names=sorted(predictions);draws=defaultdict(list)
    for _ in range(replicates):
        indices=[rng.randrange(len(sample)) for _ in sample]
        # Bootstrap duplicates are intentional; provide unique replicate IDs.
        bs=[dict(sample[i],unit_id=f'replicate:{j}') for j,i in enumerate(indices)]
        lookup={r['unit_id']:r for r in references}
        br=[dict(lookup[sample[i]['unit_id']],unit_id=f'replicate:{j}') for j,i in enumerate(indices)]
        scores={n:score(bs,br,{f'replicate:{j}':predictions[n][sample[i]['unit_id']] for j,i in enumerate(indices)},pair=pair) for n in names}
        for ai,a in enumerate(names):
            for b in names[ai+1:]:
                for metric in ('precision','recall','f1'):
                    x,y=scores[a][metric],scores[b][metric]
                    if x is not None and y is not None:draws[a,b,metric].append(y-x)
    differences=[]
    for ai,a in enumerate(names):
        for b in names[ai+1:]:
            for metric in ('precision','recall','f1'):
                x,y=results[a][metric],results[b][metric];vals=draws[a,b,metric]
                differences.append({'before':a,'after':b,'metric':metric,'difference':y-x if x is not None and y is not None else None,
                    'percentile_95':list(map(float,np.quantile(vals,[.025,.975]))) if vals else None,
                    'valid_replicates':len(vals)})
    return {'status':'scored','candidates':results,'paired_differences':differences,
            'interval_method':'paired SRS percentile bootstrap; no FPC; conditional on reference correctness',
            'seed':SEED,'replicates':replicates}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--decisions',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    print(json.dumps(freeze(read_jsonl(a.decisions),a.output,{'decisions':file_hash(a.decisions)}),indent=2))

if __name__=='__main__': main()
