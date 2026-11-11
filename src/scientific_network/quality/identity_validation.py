"""Task2C reproducible three-way evaluation, topology sensitivity and Task3 handoff.

Read-only with respect to candidates, frozen samples, source caches and databases.
Large ledgers stay under an explicitly chosen ignored output directory.
"""
import argparse
from collections import Counter,defaultdict
from itertools import combinations
import json
from pathlib import Path

import networkx as nx

from scientific_network.analysis.analyze import _spearman, _top
from scientific_network.collect.storage import read_jsonl,write_json,write_jsonl
from scientific_network.quality.identity_audit import file_hash,unused
from scientific_network.quality.identity_evaluation import paired_score
from scientific_network.quality.identity_review import verify_freeze


def graph_view(path):
    g=json.loads(path.read_bytes())
    authored={(e['target_id'],e['properties']['byline_position']):e['source_id'] for e in g['edges'] if e['relation']=='AUTHORED'}
    people={n['id']:n['name'] for n in g['nodes'] if n['label']=='Researcher'}
    net=nx.Graph();net.add_nodes_from(sorted(people))
    rels=defaultdict(dict)
    for e in g['edges']:
        rels[e['relation']][(e['source_id'],e['target_id'])]=e['properties']
        if e['relation']=='COAUTHORED_WITH':
            net.add_edge(e['source_id'],e['target_id'],weight=e['properties']['fractional_weight'])
    components=sorted((len(c) for c in nx.connected_components(net)),reverse=True)
    metrics={'degree':dict(net.degree()),'strength':dict(net.degree(weight='weight'))}
    return dict(version=g['graph_version'],authored=authored,people=people,relations=rels,metrics=metrics,
        observations=g['affiliation_observations'],summary=dict(researchers=len(people),authorships=len(authored),
        relationship_counts={k:len(v) for k,v in sorted(rels.items())},components=len(components),
        isolates=sum(d==0 for _,d in net.degree()),component_sizes=components,largest_component_share=components[0]/len(people)))


def run(bindings_path,evaluation,decisions_path,works_path,references_path,output):
    unused(output);bindings=json.loads(bindings_path.read_bytes());freeze_hash=verify_freeze(evaluation)
    if any(output.resolve().is_relative_to(Path(r['path']).resolve().parent) for r in bindings['graphs'].values()) or output.resolve().is_relative_to(evaluation.resolve()):
        raise ValueError('output must be outside protected candidate/sample directories')
    if freeze_hash!=bindings['freeze_sha256']:raise ValueError('wrong frozen evaluation')
    graphs={}
    for name,r in bindings['graphs'].items():
        p=Path(r['path'])
        if file_hash(p)!=r['sha256']:raise ValueError('candidate graph changed')
        graphs[name]=graph_view(p)
    ds=read_jsonl(decisions_path);works={w['paper_id']:w for w in read_jsonl(works_path)}
    refs=read_jsonl(references_path)
    if refs:
        reference_manifest=json.loads((references_path.parent/'manifest.json').read_bytes())
        if (reference_manifest['freeze_sha256']!=freeze_hash or
                reference_manifest['outputs'][references_path.name]!=file_hash(references_path)):
            raise ValueError('reference manifest does not bind this frozen study')
    predictions={name:{d['mention_id']:g['authored'].get((d['paper_id'],d['author_position'])) for d in ds} for name,g in graphs.items()}
    semantic={}
    for frame in ('assignment','pair','diagnostic'):
        sample=read_jsonl(evaluation/(frame+'-sample.jsonl'))
        pred=predictions
        if frame=='pair':
            pred={name:{u['unit_id']:bool(p[u['left']] and p[u['left']]==p[u['right']]) for u in sample} for name,p in predictions.items()}
        if frame=='diagnostic':
            semantic[frame]={cat:paired_score([s for s in sample if s['frame']==cat],refs,pred) for cat in sorted({s['frame'] for s in sample})}
        else:semantic[frame]=paired_score(sample,refs,pred,pair=frame=='pair')
    # Distinguish accepted/different IDs from endpoint abstention within false-split predictions.
    pair=read_jsonl(evaluation/'pair-sample.jsonl')
    pair_states={name:dict(Counter('same_id' if p[u['left']] and p[u['left']]==p[u['right']] else
        'both_accepted_different_ids' if p[u['left']] and p[u['right']] else 'endpoint_abstention' for u in pair)) for name,p in predictions.items()}
    write_json(output/'semantic-evaluation.json',dict(freeze_sha256=freeze_hash,reference_n=len(refs),results=semantic,
        pair_prediction_states=pair_states,limitation='No global pairwise estimand. Partial references are descriptive only. No evaluator-error coverage.'))
    # Full census coverage by mechanism; semantic method estimates require real references.
    by_reason=defaultdict(list)
    for d in ds:by_reason[d['decision_reason']].append(d)
    mechanism={}
    for reason,items in sorted(by_reason.items()):
        ids={d['mention_id'] for d in items};sample=[s for s in read_jsonl(evaluation/'assignment-sample.jsonl') if s['unit_id'] in ids]
        mechanism[reason]={'population':len(items),'frozen_assignment_sample_n':len(sample),
            'accepted':{name:sum(bool(p[mid]) for mid in ids) for name,p in predictions.items()},
            'evaluation':paired_score(sample,refs,predictions)}
    write_json(output/'mechanism-evaluation.json',mechanism)
    # Cache-based betweenness is permitted only with hash-bound exact candidate scores.
    score_inputs=[Path('data/processed/identity-candidate-v5-release-v3/centrality-scores.json'),Path('data/processed/identity-candidate-v5-release-v4-final/centrality-scores.json')]
    candidate_manifests=[Path('reports/quality-v5/candidate-v3/candidate-manifest.json'),Path('reports/quality-v5/task2b-v1/candidate-v4-final/candidate-manifest.json')]
    for manifest_path,score_path in zip(candidate_manifests,score_inputs):
        manifest=json.loads(manifest_path.read_bytes())
        if file_hash(score_path)!=manifest['outputs']['centrality-scores.json']['sha256']:
            raise ValueError('centrality cache differs from frozen candidate manifest')
    a,b=[json.loads(p.read_bytes()) for p in score_inputs]
    if a['before']!=b['before']:raise ValueError('centrality baselines disagree')
    rank_paths=[Path('reports/quality-v5/candidate-v3/network-comparison.json'),Path('reports/quality-v5/task2b-v1/candidate-v4-final/network-comparison.json')]
    for manifest_path,rank_path in zip(candidate_manifests,rank_paths):
        if file_hash(rank_path)!=json.loads(manifest_path.read_bytes())['network_comparison_sha256']:
            raise ValueError('ranking configuration differs from frozen candidate manifest')
    ranks=[json.loads(p.read_bytes()) for p in rank_paths]
    if ranks[0]['pivots']!=ranks[1]['pivots']:raise ValueError('centrality pivots disagree')
    for name,cache in [('v4',a['before']),('candidate_v3',a['after']),('task2b',b['after'])]:
        for metric in ('degree','strength'):
            actual=graphs[name]['metrics'][metric]
            if set(actual)!=set(cache[metric]) or any(abs(actual[k]-cache[metric][k])>1e-8 for k in actual):
                raise ValueError('cached rankings mismatch current graph '+name+' '+metric)
        graphs[name]['metrics']['betweenness']=cache['betweenness']
    changed_positions={key for g in graphs.values() for key in g['authored'] if len({v['authored'].get(key) for v in graphs.values()})>1}
    changed_papers={k[0] for k in changed_positions}
    changed_people={g['authored'][k] for g in graphs.values() for k in changed_positions if k in g['authored']}
    comparisons={}
    for left,right in combinations(sorted(graphs),2):
        x,y=graphs[left],graphs[right];metrics={}
        for metric in ('degree','strength','betweenness'):
            aa,bb=x['metrics'][metric],y['metrics'][metric];ta,tb=_top(aa,20),_top(bb,20)
            order_a={n:i for i,n in enumerate(sorted(aa,key=lambda n:(-aa[n],n)),1)}
            order_b={n:i for i,n in enumerate(sorted(bb,key=lambda n:(-bb[n],n)),1)}
            top_ids={r['node_id'] for r in ta+tb}
            metrics[metric]={'top20_overlap':len({r['node_id'] for r in ta}&{r['node_id'] for r in tb}),
                'spearman_common':_spearman(aa,bb),'common_n':len(aa.keys()&bb.keys()),
                'top_nodes':[dict(id=n,name=y['people'].get(n,x['people'].get(n)),before_rank=order_a.get(n),after_rank=order_b.get(n),
                    before_score=aa.get(n),after_score=bb.get(n),directly_changed_identity_support=n in changed_people) for n in sorted(top_ids,key=lambda n:order_b.get(n,10**9))]}
        rels={}
        for rel in ('COAUTHORED_WITH','COLLABORATED_WITH','RESEARCHES_TOPIC','CONTRIBUTES_TO_TOPIC'):
            # Discover actual predicate names from graph; topic aggregates below also recorded in inventory.
            ra,rb=x['relations'].get(rel,{}),y['relations'].get(rel,{})
            rels[rel]={'before':len(ra),'after':len(rb),'gained':len(rb.keys()-ra.keys()),'lost':len(ra.keys()-rb.keys()),
                'changed_support_or_weight':sum(ra[k]!=rb[k] for k in ra.keys()&rb.keys())}
        comparisons[left+'__'+right]={'metrics':metrics,'relations':rels}
    # Conservative shared-assignment network: remove every position on which a checkpoint differs.
    common=set.intersection(*(set(g['authored']) for g in graphs.values()))-changed_positions
    bypaper=defaultdict(set)
    for key in sorted(common):bypaper[key[0]].add(graphs['task2b']['authored'][key])
    net=nx.Graph();net.add_nodes_from(sorted({p for ps in bypaper.values() for p in ps}))
    for ps in bypaper.values():net.add_edges_from(combinations(sorted(ps),2))
    components=sorted((len(c) for c in nx.connected_components(net)),reverse=True)
    topology=dict(method='task2c-identity-sensitivity-v1',graphs={name:g['summary'] for name,g in graphs.items()},
        comparisons=comparisons,changed_authorship_positions=len(changed_positions),changed_papers=len(changed_papers),
        changed_researcher_ids=len(changed_people),common_assignment_scenario=dict(positions=len(common),researchers=len(net),
        coauthor_pairs=net.number_of_edges(),components=len(components),isolates=sum(d==0 for _,d in net.degree()),component_sizes=components),
        centrality=dict(method=ranks[0]['method_version'],pivots_n=len(ranks[0]['pivots']),
            limitation='Approximate betweenness with identical common pivots and inverse positive fractional-weight distances; topology stability is not semantic validity'),
        score_hashes={str(p):file_hash(p) for p in score_inputs+rank_paths})
    write_json(output/'graph-sensitivity.json',topology)
    # Task3 interfaces: retained paper-specific observations only; never assign all institutions to all authors.
    task3=output/'task3';task3.mkdir()
    observations=graphs['task2b']['observations'];orgs=defaultdict(set)
    for o in observations:orgs[o['researcher_id'],o['paper_id']].add(o['organization_id'])
    accepted=[];pending=[];reasons=Counter();blocked_aff=0
    for d in sorted(ds,key=lambda d:d['mention_id']):
        r=works[d['paper_id']]
        base={k:d.get(k) for k in ('mention_id','paper_id','author_position','official_name','resolution_state','canonical_researcher_id','decision_reason','supporting_evidence')}
        base['doi']=r['doi'];base['matched']=r['match']['status']=='matched'
        if d['resolution_state']=='resolved':
            base['organization_ids']=sorted(orgs[d['canonical_researcher_id'],d['paper_id']]);accepted.append(base)
        else:
            authors=(r.get('openalex') or {}).get('authorships') or []
            author=authors[d['author_position']-1] if d['author_position']<=len(authors) else {}
            raw={'institutions':author.get('institutions',[]),'raw_affiliation_strings':author.get('raw_affiliation_strings',[]),
                 'affiliations':author.get('affiliations',[])}
            base['unaccepted_affiliation_context']=raw
            base['identity_blocks_existing_affiliation_context']=bool(raw['institutions']) and base['matched']
            blocked_aff+=base['identity_blocks_existing_affiliation_context'];pending.append(base);reasons[d['decision_reason']]+=1
    write_jsonl(task3/'accepted-authorships.jsonl',accepted);write_jsonl(task3/'unresolved-mentions.jsonl',pending)
    write_jsonl(task3/'accepted-affiliation-observations.jsonl',observations)
    matched=sum(r['match']['status']=='matched' for d in ds for r in [works[d['paper_id']]])
    affiliated=len({(o['researcher_id'],o['paper_id']) for o in observations})
    target=(matched*80+99)//100
    write_json(task3/'handoff.json',dict(recommendation='experimental_task2b_only_not_scientifically_promoted',
        graph_version=graphs['task2b']['version'],graph_sha256=bindings['graphs']['task2b']['sha256'],
        accepted_n=len(accepted),unresolved_n=len(pending),matched_positions=matched,official_positions=len(ds),
        affiliated_positions=affiliated,accepted_without_affiliation=len(accepted)-affiliated,
        maximum_matched_affiliation_coverage=len(accepted)/matched,target_80_percent_minimum_positions=target,
        additional_identities_needed_even_with_perfect_affiliation=target-len(accepted),
        withheld_positions_with_provider_institutions=blocked_aff,withheld_reasons=dict(sorted(reasons.items())),
        warning='Provider institution context on unresolved mentions is not an accepted triple; no Cartesian copying or relaxed identity rules',
        files={p.name:file_hash(p) for p in sorted(task3.iterdir())}))
    write_json(output/'manifest.json',dict(method='identity-task2c-validation-v1',inputs={str(p):file_hash(p) for p in (bindings_path,decisions_path,works_path,references_path)},
        freeze_sha256=freeze_hash,graphs=bindings['graphs'],code_sha256=file_hash(Path(__file__)),
        transitive_code_sha256={str(p):file_hash(p) for p in (Path(__file__).with_name('identity_evaluation.py'),Path(__file__).with_name('identity_review.py'))},
        outputs={str(p.relative_to(output)):file_hash(p) for p in sorted(output.rglob('*')) if p.is_file()}))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('bindings','evaluation','decisions','works','references','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();run(a.bindings,a.evaluation,a.decisions,a.works,a.references,a.output)

if __name__=='__main__':main()
