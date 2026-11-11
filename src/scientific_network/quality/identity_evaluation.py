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

METHOD = 'identity-evaluation-v1'  # Frozen sampling contract, unchanged.
SCORING_METHOD = 'identity-evaluation-v2'
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


def _valid_reference(r, pair):
    valid = {'same', 'different'} if pair else {'identity', 'unresolvable'}
    if (r.get('label') not in valid or r.get('independence') != 'independent'
            or r.get('adjudication') != 'complete' or not r.get('evidence')
            or r.get('reviewer_kind', 'human') != 'human'):
        return False
    if not pair and r['label'] == 'identity':
        ids = r.get('accepted_canonical_ids')
        # A verified person may be absent from ALL candidates. An explicitly
        # completed, empty crosswalk must still enter the recall denominator.
        return bool(r.get('reference_identity')) and isinstance(ids, list) and (
            bool(ids) or r.get('crosswalk_complete') is True)
    return True


def _ratios(sample, refs, predictions, pair):
    tp = fp = fn = tn = 0.0
    accepted = 0
    for s in sample:
        r, p = refs[s['unit_id']], predictions[s['unit_id']]
        w = 1 / s['inclusion_probability']
        positive = bool(p)
        truth = r['label'] == ('same' if pair else 'identity')
        correct = truth if pair else truth and p in r.get('accepted_canonical_ids', [])
        accepted += positive
        tp += w * bool(positive and correct)
        fp += w * bool(positive and not correct)
        fn += w * bool(truth and (not positive or not correct))
        tn += w * bool(not positive and not truth)
    total = sum(1 / s['inclusion_probability'] for s in sample)
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    # A wrong accepted assignment counts as BOTH FP and FN. Zero true
    # positives with a positive denominator means zero F1, not missing F1.
    return {'sample_n': len(sample), 'accepted_n': accepted,
            'coverage': sum(bool(predictions[s['unit_id']]) / s['inclusion_probability'] for s in sample) / total if total else None,
            'precision': precision, 'recall': recall,
            'f1': 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
            'weighted_tp': tp, 'weighted_fp': fp, 'weighted_fn': fn, 'weighted_tn': tn,
            'false_merge_rate': fp / (tp + fp) if pair and tp + fp else None,
            'false_split_rate': fn / (tp + fn) if pair and tp + fn else None,
            'estimated_false_merge_pairs' if pair else 'estimated_incorrect_assignments': fp,
            'estimated_false_split_pairs' if pair else 'estimated_missed_assignments': fn}


def score(sample, references, predictions, *, pair=False):
    """Population ratios only with complete references; descriptive subset always.

    Inverse inclusion weights estimate frame totals, not a missing-label model.
    Pair estimands are restricted to the sampled blocking frame. Correct abstention
    requires an affirmative unresolvable reference; unknowns never become negatives.
    """
    keys = [s['unit_id'] for s in sample]
    if len(keys) != len(set(keys)):
        raise ValueError('duplicate sampled unit')
    if len({s.get('frame') for s in sample}) > 1:
        raise ValueError('do not pool diagnostic or distinct sampling frames')
    if any(not 0 < s['inclusion_probability'] <= 1 for s in sample):
        raise ValueError('invalid inclusion probability')
    if any(k not in predictions for k in keys):
        raise ValueError('missing candidate predictions')
    if pair and any(type(predictions[k]) is not bool for k in keys):
        raise ValueError('pair predictions must be booleans')
    if not pair and any(predictions[k] is not None and
                        (not isinstance(predictions[k], str) or not predictions[k]) for k in keys):
        raise ValueError('assignment predictions must be canonical ID or null')
    refs = {r['unit_id']: r for r in references}
    if len(refs) != len(references):
        raise ValueError('duplicate references')
    known = [s for s in sample if _valid_reference(refs.get(s['unit_id'], {}), pair)]
    missing = len(sample) - len(known)
    total = sum(1 / s['inclusion_probability'] for s in sample)
    coverage = sum(bool(predictions[k]) / s['inclusion_probability'] for k,s in zip(keys,sample)) / total if total else None
    base = {'scoring_method': SCORING_METHOD, 'sample_n': len(sample), 'valid_reference_n': len(known),
            'missing_or_invalid': missing, 'accepted_n': sum(bool(predictions[k]) for k in keys),
            'coverage': coverage, 'abstention_rate': 1-coverage if coverage is not None else None,
            'estimand': 'within_declared_blocking_frame' if pair else 'official_authorship_positions',
            'intervals': None,
            'interval_limitation': 'No Wilson interval on weighted totals; paired_score supplies SRS bootstrap conditional on correct references'}
    if missing or not sample:
        return {**base, 'status': 'unavailable_incomplete_independent_references',
                'precision': None, 'recall': None, 'f1': None,
                'false_merge_rate': None, 'false_split_rate': None,
                'verified_subset': {**_ratios(known, refs, predictions, pair),
                    'inference': 'descriptive_only_selection_and_missingness_bias; weights do not repair reference missingness'}}
    result = {**base, **_ratios(sample, refs, predictions, pair), 'status': 'scored'}
    if len({s['inclusion_probability'] for s in sample}) == 1:
        from scientific_network.evaluation.precision import precision_interval
        raw = _ratios([dict(s, inclusion_probability=1) for s in sample], refs, predictions, pair)
        tp, fp, fn = (int(raw[k]) for k in ('weighted_tp','weighted_fp','weighted_fn'))
        result['conditional_wilson_95'] = {
            'precision': precision_interval(tp, tp+fp) if tp+fp else None,
            'recall': precision_interval(tp, tp+fn) if tp+fn else None,
            'limitation': 'Unweighted count ratios conditional on reference truth; conservative SRS approximation without FPC, no evaluator or missingness error'}
    return result


def _partial_differences(results):
    """All candidates use the same valid-reference subset; no inferential CI."""
    names = sorted(results)
    rows = []
    for i, a in enumerate(names):
        for b in names[i+1:]:
            for metric in ('precision', 'recall', 'f1'):
                x = results[a].get('verified_subset', results[a]).get(metric)
                y = results[b].get('verified_subset', results[b]).get(metric)
                rows.append({'before': a, 'after': b, 'metric': metric,
                             'difference': y-x if x is not None and y is not None else None,
                             'inference': 'descriptive_only', 'percentile_95': None})
    return rows


def paired_score(sample, references, predictions, *, pair=False, replicates=1000):
    """Same sampled units for every candidate; paired SRS bootstrap of differences.

    Ratios use inverse inclusion weights. This bootstrap is for one declared SRS
    frame, with no finite-population correction. Diagnostic frames stay separate.
    """
    results={name:score(sample,references,pred,pair=pair) for name,pred in predictions.items()}
    if any(r['status']!='scored' for r in results.values()):
        return {'status':'unavailable_no_complete_independent_references','candidates':results,
                'paired_differences':None,'confidence_intervals':None,
                'verified_subset_paired_differences': _partial_differences(results)}
    if len({s.get('frame') for s in sample})!=1:
        raise ValueError('do not pool diagnostic or distinct sampling frames')
    if len({s['inclusion_probability'] for s in sample}) != 1:
        raise ValueError('SRS bootstrap requires equal inclusion probabilities')
    if replicates < 1:
        raise ValueError('replicates must be positive')
    import numpy as np
    rng=random.Random(SEED);names=sorted(predictions);draws=defaultdict(list); candidate_draws=defaultdict(list)
    for _ in range(replicates):
        indices=[rng.randrange(len(sample)) for _ in sample]
        # Bootstrap duplicates are intentional; provide unique replicate IDs.
        bs=[dict(sample[i],unit_id=f'replicate:{j}') for j,i in enumerate(indices)]
        lookup={r['unit_id']:r for r in references}
        br=[dict(lookup[sample[i]['unit_id']],unit_id=f'replicate:{j}') for j,i in enumerate(indices)]
        scores={n:score(bs,br,{f'replicate:{j}':predictions[n][sample[i]['unit_id']] for j,i in enumerate(indices)},pair=pair) for n in names}
        for name in names:
            for metric in ('precision', 'recall', 'f1'):
                value = scores[name][metric]
                if value is not None: candidate_draws[name, metric].append(value)
        for ai,a in enumerate(names):
            for b in names[ai+1:]:
                for metric in ('precision','recall','f1'):
                    x,y=scores[a][metric],scores[b][metric]
                    if x is not None and y is not None:draws[a,b,metric].append(y-x)
    for name in names:
        results[name]['intervals'] = {metric: {
            'percentile_95': list(map(float, np.quantile(candidate_draws[name, metric], [.025,.975]))) if candidate_draws[name, metric] else None,
            'valid_replicates': len(candidate_draws[name, metric])}
            for metric in ('precision', 'recall', 'f1')}
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
            'seed':SEED,'replicates':replicates,
            'boundary_warning':'Percentile intervals can degenerate with sparse or constant outcomes; no equality claim from zero observed differences. Use Wilson marginal intervals for boundary caution.'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--decisions',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    print(json.dumps(freeze(read_jsonl(a.decisions),a.output,{'decisions':file_hash(a.decisions)}),indent=2))

if __name__=='__main__': main()
