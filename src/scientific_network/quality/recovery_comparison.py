"""Three-checkpoint measured comparison and honest missing-reference execution."""
import argparse
from collections import Counter
from pathlib import Path
import json

from scientific_network.analysis.analyze import _spearman, _top
from scientific_network.collect.storage import read_jsonl, write_json, write_jsonl
from scientific_network.contracts import GraphArtifact
from scientific_network.quality.identity_audit import file_hash, unused
from scientific_network.quality.identity_evaluation import paired_score
from scientific_network.resolve.candidate_v5 import compare


def summarize(comparison, side, matched, official):
    counts=comparison[side+'_counts'];accepted=counts['edges_by_relation']['AUTHORED']
    af=comparison['affiliated_positions']['before' if side=='before' else 'after']
    return {'counts':counts,'total_nodes':sum(counts['nodes_by_label'].values()),
            'total_edges':sum(counts['edges_by_relation'].values()),'accepted_authorships':accepted,
            'authorship_coverage':{'numerator':accepted,'matched_denominator':matched,'rate':accepted/matched,
                                  'official_denominator':official,'official_rate':accepted/official},
            'affiliation_coverage':{'numerator':af,'matched_denominator':matched,'rate':af/matched,
                                    'official_denominator':official,'official_rate':af/official,
                                    'accepted_denominator':accepted,'conditional_rate':af/accepted},
            'affiliation_coverage_ceiling':{'numerator':accepted,'denominator':matched,'rate':accepted/matched},
            'collaboration':comparison['network_'+side]}


def run(baseline_path, prior, revised, prior_report, revised_report, evaluation, requests, output):
    unused(output)
    prior_comparison=json.loads((prior_report/'comparison.json').read_bytes())
    revised_comparison=json.loads((revised_report/'comparison.json').read_bytes())
    decisions=read_jsonl(revised/'identity-decisions.jsonl')
    official=len(decisions)
    matched=official-sum(d['decision_reason']=='work_not_matched' for d in decisions)
    if file_hash(baseline_path)!=revised_comparison['input_hashes']['source_graph']:
        raise ValueError('baseline path differs from candidate-bound source')
    old=GraphArtifact.model_validate_json((prior/'graph.json').read_bytes())
    new=GraphArtifact.model_validate_json((revised/'graph.json').read_bytes())
    change=compare(old,new,decisions)
    write_json(output/'versus-candidate-v3.json',change)
    prior_decisions=read_jsonl(prior/'identity-decisions.jsonl');by_id={d['mention_id']:d for d in decisions}
    previous={d['mention_id']:d for d in prior_decisions}
    gains=[d for mid,d in sorted(by_id.items()) if d['resolution_state']=='resolved' and previous[mid]['resolution_state']!='resolved']
    losses=[d for mid,d in sorted(by_id.items()) if d['resolution_state']!='resolved' and previous[mid]['resolution_state']=='resolved']
    write_jsonl(output/'recovered-versus-v3.jsonl',[{k:d.get(k) for k in ('mention_id','paper_id','author_position','official_name','source_author_id','canonical_researcher_id','decision_reason','name_variation_evidence','recovery_source_work_id','supporting_evidence')} for d in gains])
    write_jsonl(output/'rejected-versus-v3.jsonl',losses)
    cp={'v4':summarize(revised_comparison,'before',matched,official), 'candidate_v3':summarize(prior_comparison,'after',matched,official),
        'revised_candidate_v4':summarize(revised_comparison,'after',matched,official)}
    before_rank=json.loads((prior_report/'network-comparison.json').read_bytes())
    after_rank=json.loads((revised_report/'network-comparison.json').read_bytes())
    same_pivots=before_rank['pivots']==after_rank['pivots']
    if not same_pivots:raise ValueError('three-way rankings need identical common pivots')
    a=json.loads((prior/'centrality-scores.json').read_bytes());b=json.loads((revised/'centrality-scores.json').read_bytes())
    if a['before']!=b['before']:raise ValueError('baseline centrality not identical')
    rankings={}
    for metric in a['after']:
        x,y=a['after'][metric],b['after'][metric]
        rankings[metric]={'v3_top20':_top(x,20),'revised_top20':_top(y,20),
            'top20_overlap':len({d['node_id'] for d in _top(x,20)}&{d['node_id'] for d in _top(y,20)}),
            'top20_denominator':20,'spearman_common_nodes':_spearman(x,y),'common_nodes':len(set(x)&set(y))}
    write_json(output/'three-way-rankings.json',{'same_256_pivots':same_pivots,'v4_versus_revised':after_rank,
        'v4_versus_v3':before_rank,'v3_versus_revised':rankings,
        'limitation':'paired descriptive approximation, not semantic quality or reproduction of frozen release ranking'})
    # Use exactly the same frozen references/units for all checkpoints. No labels
    # exist, so execute the unavailable path rather than inventing semantic scores.
    baseline=GraphArtifact.model_validate_json(baseline_path.read_bytes())
    graphs={'v4':baseline,'candidate_v3':old,'revised_candidate_v4':new}
    predictions={}
    for name,g in graphs.items():
        by_position={(e.target_id,e.properties['byline_position']):e.source_id for e in g.edges if e.relation=='AUTHORED'}
        predictions[name]={d['mention_id']:by_position.get((d['paper_id'],d['author_position'])) for d in decisions}
    eval_results={}
    for frame in ('assignment','pair','diagnostic'):
        sample=read_jsonl(evaluation/(frame+'-sample.jsonl'))
        pred=predictions
        if frame=='pair':
            pred={name:{u['unit_id']:bool(p[u['left']] and p[u['left']]==p[u['right']]) for u in sample} for name,p in predictions.items()}
        if frame=='diagnostic':
            eval_results[frame]={category:paired_score([u for u in sample if u['frame']==category],[],predictions) for category in sorted({u['frame'] for u in sample})}
        else:eval_results[frame]=paired_score(sample,[],pred,pair=frame=='pair')
    write_json(output/'semantic-evaluation.json',{'results':eval_results,'independent_labels':0,
        'semantic_accuracy':'unavailable; construction certificates are not gold',
        'evaluation_freeze_sha256':file_hash(evaluation/'freeze.json')})
    # Prespecified nested mechanism policies, same official/matched denominators.
    nested=[]
    for label,include in [('v3',set()),('v3+formatting',{'provider_id_full_letter_boundary_normalization'}),
                           ('v3+formatting+declared_aliases',{'provider_id_full_letter_boundary_normalization','provider_id_public_orcid_declared_aliases'}),
                           ('full_revised',set(d['decision_reason'] for d in gains))]:
        accepted=cp['candidate_v3']['accepted_authorships']+sum(d['decision_reason'] in include for d in gains)
        nested.append({'policy':label,'accepted':accepted,'matched_denominator':matched,'coverage':accepted/matched,'independent_precision':None})
    result={'method':'identity-task2b-comparison-v1','checkpoints':cp,'versus_v3':{
        'gained_positions':len(gains),'lost_positions':len(losses),'mechanisms':dict(Counter(d['decision_reason'] for d in gains)),
        'remaining_states':dict(Counter(d['resolution_state'] for d in decisions))},'selective_coverage':nested,
        'independent_precision_recall_f1':None,'construction_evidence_recovery_not_measured_semantic_recall':True,
        'comparison_scope':'identity-only; no corrected work sources, classifier, citation or affiliation enrichment',
        'task3_target_feasible_with_current_identities':cp['revised_candidate_v4']['affiliation_coverage_ceiling']['rate']>=.8,
        'source_evidence':{'original_matched_works':revised_comparison['source_check']['matched_works'],
                           'original_cache_objects_verified':revised_comparison['source_check']['raw_objects_hashed'],
                           'new_public_requests':sum(len(json.loads(p.read_bytes())) for p in requests),'independent_evaluation_labels':0},
        'input_graph_hashes':{'v4':file_hash(baseline_path),'candidate_v3':file_hash(prior/'graph.json'),
                             'revised_candidate_v4':file_hash(revised/'graph.json')}}
    write_json(output/'comparison-summary.json',result)
    print(json.dumps({'versus_v3':result['versus_v3'],'affiliation':cp['revised_candidate_v4']['affiliation_coverage']},indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','prior','revised','prior-report','revised-report','evaluation','output'):p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--requests',required=True,type=Path,nargs='+')
    a=p.parse_args();run(a.baseline,a.prior,a.revised,a.prior_report,a.revised_report,a.evaluation,a.requests,a.output)
if __name__=='__main__':main()
