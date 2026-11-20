"""Complete frozen-graph views; report-only layouts, no graph/analysis mutations.

Optional renderer: igraph==1.0.0 (may be installed in build/visualization-deps).
Both languages share cached coordinates; all eligible nodes/edges are included.
"""
from pathlib import Path
import argparse, hashlib, json, random, sys
from collections import Counter
import numpy as np
BASE=Path(__file__).resolve().parents[1];ROOT=BASE.parents[1]
sys.path.insert(0,str(BASE/'build/visualization-deps'))
import igraph as ig
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D

p=argparse.ArgumentParser();p.add_argument('--language',choices=['en','vi','all'],default='all');args=p.parse_args()
source=ROOT/'data/processed/release-graph-v4/graph.json'
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
assert source_hash=='6f665a946cec7473889a09e883a3ef88469de867cb1054d6a3b145239ea59c90'
graph=json.loads(source.read_bytes());assert not graph['is_synthetic']
nodes=sorted(graph['nodes'],key=lambda n:n['id'])
edges=sorted((e for e in graph['edges'] if e['validation_status']=='accepted'),key=lambda e:e['edge_id'])
assert len(nodes)==47875 and len(edges)==225731
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'pdf.fonttype':42,'text.color':'#26384a','savefig.facecolor':'white'})
colors={'Researcher':'#167d8d','Paper':'#759ecc','Organization':'#ce7135','Topic':'#944b9b','Venue':'#344457'}
translations={'Researcher':'Nhà nghiên cứu','Paper':'Bài báo','Organization':'Tổ chức','Topic':'Chủ đề','Venue':'Hội nghị'}
def digest(ids):return hashlib.sha256(('\n'.join(ids)+'\n').encode()).hexdigest()

def render(name,ns,es):
    lookup={n['id']:i for i,n in enumerate(ns)}
    pairs=np.array([(lookup[e['source_id']],lookup[e['target_id']]) for e in es],dtype=np.int32)
    G=ig.Graph(n=len(ns),edges=pairs.tolist(),directed=False)
    comps=G.connected_components();largest=max(comps,key=len);main=set(largest)
    cache=BASE/f'build/{name}-layout.npz'
    cache.parent.mkdir(parents=True,exist_ok=True)
    settings={'source_sha256':source_hash,'node_ids_sha256':digest(n['id'] for n in ns),'edge_ids_sha256':digest(e['edge_id'] for e in es),'igraph':ig.__version__,'algorithm':'Fruchterman-Reingold, grid, unweighted, 350 iterations, seed 17'}
    signature=hashlib.sha256(json.dumps(settings,sort_keys=True).encode()).hexdigest()
    if cache.exists() and str(np.load(cache)['signature'])==signature:
        xy=np.load(cache)['xy']
    else:
        print(f'Layout: {name}, {len(ns)} nodes, {len(es)} edges',flush=True)
        ig.set_random_number_generator(random.Random(17))
        rng=np.random.default_rng(17)
        xy=np.asarray(G.layout_fruchterman_reingold(niter=350,grid='grid',seed=rng.uniform(-np.sqrt(len(ns)),np.sqrt(len(ns)),(len(ns),2)).tolist()).coords)
        np.savez_compressed(cache,xy=xy,signature=signature)
    counts=Counter(n['label'] for n in ns)
    receipt={**settings,'node_count':len(ns),'edge_count':len(es),'nodes_by_type':dict(counts),'edges_by_relation':dict(Counter(e['relation'] for e in es)),'layout_sha256':hashlib.sha256(xy.tobytes()).hexdigest(),'components':len(comps),'largest_component':len(largest),'selection':'All eligible nodes and all accepted edges; no sampling or support threshold; direction suppressed for overview only.'}
    for lang in (['en','vi'] if args.language=='all' else [args.language]):
        out=BASE/f'figures/{lang}';out.mkdir(exist_ok=True,parents=True)
        if name=='full-coauthorship-network':
            fig,(ax,detail)=plt.subplots(1,2,figsize=(7.0,4.1));fig.subplots_adjust(left=.015,right=.985,top=.83,bottom=.21,wspace=.06)
        else:
            fig,ax=plt.subplots(figsize=(7.0,7.1));fig.subplots_adjust(left=.015,right=.985,top=.97,bottom=.17)
        ax.add_collection(LineCollection(xy[pairs],colors='#657a92',linewidths=.16 if name=='full-coauthorship-network' else .10,alpha=.15 if name=='full-coauthorship-network' else .065,rasterized=True,zorder=1))
        if name=='full-knowledge-graph':
            handles=[]
            for label in ['Paper','Researcher','Organization','Topic','Venue']:
                ix=[i for i,n in enumerate(ns) if n['label']==label]
                size={'Paper':.65,'Researcher':.7,'Organization':3,'Topic':23,'Venue':55}[label]
                ax.scatter(xy[ix,0],xy[ix,1],s=size,c=colors[label],alpha=.65 if label in ['Paper','Researcher'] else .95,linewidths=0,rasterized=True,zorder=2 if label in ['Paper','Researcher'] else 3)
                handles.append(Line2D([],[],marker='o',ls='',color=colors[label],markersize=6,label=f'{translations[label] if lang=="vi" else label} ({len(ix):,})'))
            fig.legend(handles=handles,loc='lower center',ncol=3,frameon=False,fontsize=9.5,bbox_to_anchor=(.5,.035))
        else:
            for inside,color,size in [(False,'#aab7c6',1.0),(True,colors['Researcher'],.85)]:
                ix=[i for i in range(len(ns)) if (i in main)==inside]
                ax.scatter(xy[ix,0],xy[ix,1],s=size,c=color,linewidths=0,alpha=.8,rasterized=True,zorder=2)
            labels=['Largest component (20,776)','Other components (11,413)'] if lang=='en' else ['Thành phần lớn nhất (20,776)','Các thành phần còn lại (11,413)']
            handles=[Line2D([],[],marker='o',ls='',color=c,markersize=6,label=t) for c,t in zip([colors['Researcher'],'#aab7c6'],labels)]
            fig.legend(handles=handles,loc='lower center',frameon=False,fontsize=9,bbox_to_anchor=(.5,.05),ncol=2)
            core_ix=sorted(main)
            core_pairs=np.array([pair for pair in pairs if int(pair[0]) in main and int(pair[1]) in main])
            detail.add_collection(LineCollection(xy[core_pairs],colors='#657a92',linewidths=.12,alpha=.12,rasterized=True,zorder=1))
            detail.scatter(xy[core_ix,0],xy[core_ix,1],s=.45,c=colors['Researcher'],linewidths=0,alpha=.72,rasterized=True,zorder=2)
            detail.autoscale();detail.margins(.04);detail.set_aspect('equal');detail.set_axis_off()
            ax.set_title('Toàn bộ mạng' if lang=='vi' else 'Complete network',fontsize=10,pad=10)
            detail.set_title('Phóng to thành phần lớn nhất' if lang=='vi' else 'Largest component enlarged',fontsize=10,pad=10)
        ax.autoscale();ax.margins(.025);ax.set_aspect('equal');ax.set_axis_off()
        heading=(f'{len(ns):,} nút · {len(es):,} cạnh' if lang=='vi' else f'{len(ns):,} nodes · {len(es):,} edges')
        fig.text(.5,.985,heading,ha='center',va='top',fontsize=11,fontweight='bold')
        fig.savefig(out/f'{name}.pdf',dpi=400,metadata={'CreationDate':None,'ModDate':None})
        fig.savefig(out/f'{name}.png',dpi=250);plt.close(fig)
        (out/f'{name}-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'figure':name,'nodes':len(ns),'edges':len(es),'components':len(comps),'largest':len(largest)}),flush=True)
render('full-knowledge-graph',nodes,edges)
render('full-coauthorship-network',[n for n in nodes if n['label']=='Researcher'],[e for e in edges if e['relation']=='COAUTHORED_WITH'])
