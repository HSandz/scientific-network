"""Report-only rendering of hash-pinned frozen v4 artifacts (no pipeline writes).

Run with --language en or --language vi; output is report/latex/figures/<language>/.
Writes only report/latex/figures; selection ledgers identify every displayed edge.
"""
from pathlib import Path
import argparse, csv, hashlib, json, textwrap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter, MaxNLocator
import networkx as nx
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
parser=argparse.ArgumentParser()
parser.add_argument('--language', choices=['en','vi'], default='en')
args=parser.parse_args()
LANG=args.language
OUT=Path(__file__).resolve().parents[1]/'figures'/LANG
OUT.mkdir(parents=True,exist_ok=True)
TRANSLATIONS={
'Distinct coauthors, k (log scale)':'Số đồng tác giả phân biệt, k (thang log)',
'Fraction with degree ≥ k (log scale)':'Tỷ lệ có bậc ≥ k (thang log)',
'Component rank (largest first)':'Thứ hạng thành phần (lớn nhất trước)',
'Researchers per component (log scale)':'Số nhà nghiên cứu mỗi thành phần\n(thang log)',
'Largest: 20,776':'Lớn nhất: 20,776',
'Fractional share among labeled papers':'Tỷ trọng phân bổ trong các bài có nhãn',
'Proceedings year':'Năm hội nghị',
'Community ID (ordered by researcher count)':'Mã cộng đồng (theo số nhà nghiên cứu)',
'Fractional topic share':'Tỷ trọng chủ đề theo phân bổ',
'Partner sector':'Khu vực của tổ chức đối tác',
'Organization sector':'Khu vực của tổ chức',
'Pair–paper supports':'Lượt hỗ trợ cặp tổ chức–bài báo',
'Distinct in-corpus citing papers':'Số bài trích dẫn phân biệt trong tập dữ liệu',
'Labeled':'Có nhãn','Unlabeled':'Chưa có nhãn',
'Share of roster papers':'Tỷ lệ trong danh mục bài báo',
'Distinct supporting core papers (all topics)':'Số bài hỗ trợ phân biệt (mọi chủ đề)',
'Academia':'Học thuật','Industry':'Doanh nghiệp','Government':'Chính phủ',
'Nonprofit':'Phi lợi nhuận','Unknown':'Chưa rõ',
'Computer vision':'Thị giác máy tính',
'Representation learning':'Học biểu diễn',
'Multimodal learning':'Học đa phương thức',
'Graph machine learning':'Học máy trên đồ thị',
'Reinforcement learning':'Học tăng cường',
'Generative modeling':'Mô hình sinh',
'Natural language processing and language models':'Xử lý ngôn ngữ tự nhiên và mô hình ngôn ngữ',
'Efficient machine learning systems':'Hệ thống học máy hiệu quả',
'Privacy robustness and security':'Quyền riêng tư, tính vững và bảo mật',
'Privacy, robustness and security':'Quyền riêng tư, tính vững và bảo mật',
'Recommender systems':'Hệ gợi ý',
'Causal inference':'Suy luận nhân quả',
'Reasoning and optimization':'Suy luận và tối ưu hóa',
'Multi-agent systems':'Hệ đa tác tử',
'Trustworthy AI':'AI đáng tin cậy',
'Knowledge representation and reasoning':'Biểu diễn tri thức và suy luận',
'Search and planning':'Tìm kiếm và lập kế hoạch',
'Robotics':'Rô-bốt',
'Speech and audio':'Tiếng nói và âm thanh',
'Publication count':'Số bài báo',
'Planning and reasoning':'Lập kế hoạch và suy luận',
'Trustworthy machine learning':'Học máy đáng tin cậy',
'Information retrieval and recommendation':'Truy hồi thông tin và gợi ý',
'Optimization and learning theory':'Tối ưu hóa và lý thuyết học',
'Probabilistic and Bayesian learning':'Học xác suất và Bayes',
'Robotics and embodied AI':'Rô-bốt và AI hiện thân',
}
def L(text):
    if LANG=='en': return text
    return TRANSLATIONS.get(text,text)

PINNED={
 'data/processed/release-graph-v4/graph.json':'6f665a946cec7473889a09e883a3ef88469de867cb1054d6a3b145239ea59c90',
 'reports/release-v4/analysis.json':'580d1a6dbc21ef2ac17b820979830f3de157fc1b04d1c89f2580731f141701c9',
 'reports/release-v4/graph-summary.json':'c6c6e78195500bfaf68cf1f758215824ea239056eefa9ae442edfb0a378b8408',
 'reports/final-report/figures-v4/community-topic-profiles.csv':'ba3b2bdbf3b41ceceabbb8a0abcb08a44ca22461fc536de2e79356c7dee0e884',
 'reports/final-report/figures-v4/component-sizes.csv':'7812d49a1246db12b9eafeac07a033925984e9f819e98860d6fa8331d543f3e2',
 'reports/final-report/figures-v4/researcher-degree-ccdf.csv':'116aa1cb00475ace3c0ef4a6ff5283b52a13e37623de90e08240af5ceff8864c',
 'reports/final-report/figures-v4/sector-mixing.csv':'0d79755312468f8c2292afee5006b2628d1669e246cca987127ab9b2e865be66',
 'reports/final-report/figures-v4/top-cited-papers.csv':'315f6040d1909a844f3692f2bc2dd76dd575861162e2aabecb147d4026b158b9',
 'reports/final-report/figures-v4/topic-trends.csv':'b51a988acc8fdb3de2fd36efffe290349fe6a7586a748711d2484e75211ea24a',
}
for p,digest in PINNED.items():
    assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==digest, f'Frozen input mismatch: {p}'
analysis=json.loads((ROOT/'reports/release-v4/analysis.json').read_bytes())
graph=json.loads((ROOT/'data/processed/release-graph-v4/graph.json').read_bytes())
assert graph['graph_version']==analysis['graph_version']=='release-d3c788c3114a'
assert not graph['is_synthetic']
nodes={n['id']:n for n in graph['nodes']}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.labelsize':10,
 'xtick.labelsize':9,'ytick.labelsize':9,'axes.spines.top':False,'axes.spines.right':False,
 'axes.edgecolor':'#8392a3','axes.labelcolor':'#28384a','text.color':'#28384a',
 'savefig.facecolor':'white','pdf.fonttype':42})
BLUE='#245783'; TEAL='#147d85'; GOLD='#bb6e31'
receipt={'graph_version':graph['graph_version'],'inputs_sha256':PINNED,'selections':{},'language':LANG,'renderer':{'matplotlib':matplotlib.__version__,'numpy':np.__version__,'networkx':nx.__version__}}

def rows(name):
    data=list(csv.DictReader((ROOT/f'reports/final-report/figures-v4/{name}.csv').open()))
    if LANG=='vi':
        assert all(x.get('topic') in TRANSLATIONS for x in data if 'topic' in x), 'Missing topic translation'
    return data

def save(fig,name):
    fig.savefig(OUT/f'{name}.pdf',bbox_inches='tight',pad_inches=.08,metadata={'CreationDate':None,'ModDate':None})
    fig.savefig(OUT/f'{name}.png',dpi=250,bbox_inches='tight',pad_inches=.08)
    plt.close(fig)

def wrap(s,n=26): return '\n'.join(textwrap.wrap(s,n,break_long_words=False))

def grid(ax):
    ax.grid(axis='y',color='#dce3e9',linewidth=.6);ax.set_axisbelow(True)

r=rows('topic-trends');mass={}
for x in r: mass[x['topic']]=mass.get(x['topic'],0)+float(x['fractional_paper_count'])
top=sorted(mass,key=lambda t:(-mass[t],t))[:8]
fig,axs=plt.subplots(4,2,figsize=(7.0,4.5),sharex=True,sharey=True,layout='constrained')
for i,(ax,t) in enumerate(zip(axs.flat,top)):
    rr=sorted([x for x in r if x['topic']==t],key=lambda x:int(x['year']))
    ax.plot([int(x['year']) for x in rr],[float(x['fractional_topic_share']) for x in rr],color=BLUE if i%2==0 else TEAL,marker='o',markersize=3,lw=1.6)
    ax.set_title(wrap(L(t),31),loc='left',fontsize=10,pad=6)
    ax.set(ylim=(0,.27),xticks=[2021,2023,2025]);ax.yaxis.set_major_formatter(PercentFormatter(1,decimals=0));grid(ax)
fig.supylabel(L('Fractional share among labeled papers'),fontsize=10)
fig.supxlabel(L('Proceedings year'),fontsize=10);save(fig,'topic-trends')

r=rows('community-topic-profiles');communities=list(dict.fromkeys(x['community_id'] for x in r))[:12]
visible=[x for x in r if x['community_id'] in communities];mass={}
for x in visible: mass[x['topic']]=mass.get(x['topic'],0)+float(x['fractional_paper_count'])
top=sorted(mass,key=lambda t:(-mass[t],t))[:10]
# Transpose the original view: horizontal, wrapped topic names replace rotated tiny labels.
m=np.full((len(top),len(communities)),np.nan)
for x in visible:
    if x['topic'] in top:m[top.index(x['topic']),communities.index(x['community_id'])]=float(x['topic_share'])
fig,ax=plt.subplots(figsize=(7.0,4.8),layout='constrained')
im=ax.imshow(m,cmap=plt.get_cmap('YlGnBu').with_extremes(bad='#e4e7eb'),aspect='auto',vmin=0)
ax.set_yticks(range(len(top)),[wrap(L(t),25) for t in top],fontsize=9)
ax.set_xticks(range(len(communities)),[c.split(':')[1] for c in communities],rotation=90,fontsize=9)
ax.set_xlabel(L('Community ID (ordered by researcher count)'))
cb=fig.colorbar(im,ax=ax,orientation='horizontal',pad=.12,shrink=.85);cb.set_label(L('Fractional topic share'));cb.ax.xaxis.set_major_formatter(PercentFormatter(1,decimals=0))
save(fig,'community-topic-profiles')

r=rows('sector-mixing');cats=list(dict.fromkeys(x['row_sector'] for x in r))
m=np.array([[next(int(x['pair_paper_support_count']) for x in r if x['row_sector']==a and x['column_sector']==b) for b in cats] for a in cats])
fig,ax=plt.subplots(figsize=(6.1,4.3),layout='constrained'); im=ax.imshow(m,cmap='Blues')
ax.set_xticks(range(len(cats)),[L(x.title()) for x in cats],rotation=25,ha='right')
ax.set_yticks(range(len(cats)),[L(x.title()) for x in cats]);ax.set(xlabel=L('Partner sector'),ylabel=L('Organization sector'))
for i in range(len(cats)):
 for j in range(len(cats)):ax.text(j,i,f'{m[i,j]:,}',ha='center',va='center',fontsize=10,color='white' if m[i,j]>m.max()*.5 else '#24354a')
fig.colorbar(im,ax=ax,shrink=.9,label=L('Pair–paper supports'));save(fig,'sector-mixing')

r=rows('top-cited-papers')[:10]
fig,ax=plt.subplots(figsize=(6.1,5.4),layout='constrained');y=np.arange(len(r))
ax.barh(y,[int(x['in_degree']) for x in r],color=GOLD,height=.58)
ax.set_yticks(y,[wrap(x['title'],39)+f" ({x['year']})" for x in r],fontsize=9)
ax.invert_yaxis();ax.set_xlabel(L('Distinct in-corpus citing papers'));ax.set_xlim(0,58)
for i,x in enumerate(r):ax.text(int(x['in_degree'])+.8,i,x['in_degree'],va='center',fontsize=10)
ax.xaxis.set_major_locator(MaxNLocator(integer=True));ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True);save(fig,'top-cited-papers')

summary=json.loads((ROOT/'reports/release-v4/graph-summary.json').read_bytes())

# All network selections use accepted edges and stable IDs, never display names.
def edges(relation):return [e for e in graph['edges'] if e['relation']==relation and e['validation_status']=='accepted']
def record(name,rule,ns,es):
 receipt['selections'][name]={'selection_rule':rule,'nodes':[{'id':n,'name':nodes[n]['name']} for n in sorted(ns)],'edge_ids':[e['edge_id'] for e in es], 'node_count':len(ns),'edge_count':len(es)}
 with (OUT/f'{name}-edges.csv').open('w') as f:
  w=csv.writer(f);w.writerow(['edge_id','source_id','target_id','support_count','fractional_weight'])
  for e in es:w.writerow([e['edge_id'],e['source_id'],e['target_id'],e['properties'].get('support_count',''),e['properties'].get('fractional_weight','')])

es=[e for e in edges('COLLABORATED_WITH') if {nodes[e['source_id']]['properties'].get('sector'),nodes[e['target_id']]['properties'].get('sector')}=={'academia','industry'}]
es=sorted(es,key=lambda e:(-e['properties']['support_count'],e['source_id'],e['target_id']))[:12]
labels=[]
for e in es:
 a,b=e['source_id'],e['target_id']
 if nodes[a]['properties']['sector']=='industry':a,b=b,a
 labels.append(wrap(nodes[a]['name'],34)+'\n'+wrap('↔ '+nodes[b]['name'],34))
fig,ax=plt.subplots(figsize=(6.1,6.6),layout='constrained');ax.barh(range(len(es)),[e['properties']['support_count'] for e in es],color=TEAL,height=.62)
ax.set_yticks(range(len(es)),labels,fontsize=9);ax.invert_yaxis();ax.set_xlabel(L('Distinct supporting core papers (all topics)'))
for i,e in enumerate(es):ax.text(e['properties']['support_count']+.5,i,str(e['properties']['support_count']),va='center',fontsize=10)
ax.margins(x=.15);ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True);save(fig,'organizations-network')
record('organizations-network','Top 12 accepted academia–industry pairs by distinct-paper support, descending; stable endpoint ID tie-break. Edge ranking, not an induced graph. All topics.',{e[k] for e in es for k in ['source_id','target_id']},es)

all_es=edges('COAUTHORED_WITH');center='researcher:openalex:A5017743551'
incident=[e for e in all_es if center in [e['source_id'],e['target_id']]]
incident=sorted(incident,key=lambda e:(-e['properties']['support_count'],-e['properties']['fractional_weight'],e['target_id'] if e['source_id']==center else e['source_id']))[:12]
ns={center}|{e[k] for e in incident for k in ['source_id','target_id']};es=[e for e in all_es if e['source_id'] in ns and e['target_id'] in ns]
G=nx.Graph();G.add_nodes_from(sorted(ns))
for e in sorted(es,key=lambda e:e['edge_id']):G.add_edge(e['source_id'],e['target_id'],weight=e['properties']['support_count'])
pos=nx.spring_layout(G,seed=17,k=1.15,iterations=400,weight='weight')
fig,ax=plt.subplots(figsize=(6.1,4.0),layout='constrained')
others=[e for e in G.edges if center not in e];focus=[e for e in G.edges if center in e]
nx.draw_networkx_edges(G,pos,edgelist=others,ax=ax,edge_color='#a3b4c2',alpha=.6,width=.8)
nx.draw_networkx_edges(G,pos,edgelist=focus,ax=ax,edge_color=BLUE,alpha=.65,width=[.7+np.sqrt(G[a][b]['weight'])*.35 for a,b in focus])
nx.draw_networkx_nodes(G,pos,ax=ax,node_color=[GOLD if n==center else TEAL for n in G],node_size=[320 if n==center else 110 for n in G],edgecolors='white',linewidths=1)
# Stable point offsets; white label backing keeps labels readable across links.
for n,(x,y) in pos.items():ax.annotate(nodes[n]['name'],(x,y),xytext=(0,10),textcoords='offset points',ha='center',va='bottom',fontsize=9,bbox={'facecolor':'white','edgecolor':'none','alpha':.86,'pad':1})
ax.margins(.2);ax.set_axis_off();save(fig,'researchers-network')
record('researchers-network','Bo An (A5017743551) plus 12 one-hop neighbors ranked by descending support_count, fractional_weight, then stable neighbor ID; all accepted coauthorship edges induced on those 13 IDs. Spring seed 17; center gold, other nodes teal.',ns,es)

# Report-only additions use the exact same frozen arrays for both languages.
fig,ax=plt.subplots(figsize=(6.5,2.65),layout='constrained')
years=range(2021,2026);bottom=np.zeros(5)
for venue,color in [('aaai',BLUE),('ijcai',TEAL)]:
    vals=[summary['coverage']['topic_labeled_by_venue_year']['venue:'+venue][str(y)]['eligible'] for y in years]
    ax.bar(list(years),vals,bottom=bottom,label=venue.upper(),color=color,width=.62)
    bottom+=vals
for year,total in zip(years,bottom):ax.text(year,total+65,f'{int(total):,}',ha='center',fontsize=10)
ax.set(xticks=list(years),ylim=(0,4600),xlabel=L('Proceedings year'),ylabel=L('Publication count'))
ax.legend(frameon=False,ncol=2,loc='upper left');grid(ax);save(fig,'publications')

fig,axs=plt.subplots(1,2,figsize=(7.0,2.9),layout='constrained')
r=[x for x in rows('researcher-degree-ccdf') if int(x['degree'])>0]
axs[0].step([int(x['degree']) for x in r],[float(x['fraction_at_least']) for x in r],where='post',color=BLUE,lw=1.7)
axs[0].set(xscale='log',yscale='log',xlabel=L('Distinct coauthors, k (log scale)'),ylabel=L('Fraction with degree ≥ k (log scale)'))
axs[0].grid(which='both',alpha=.22)
r=rows('component-sizes')
axs[1].scatter([int(x['component_rank']) for x in r],[int(x['researcher_count']) for x in r],s=6,color=TEAL)
axs[1].set(yscale='log',xlabel=L('Component rank (largest first)'),ylabel=L('Researchers per component (log scale)'))
axs[1].annotate(L('Largest: 20,776'),xy=(1,20776),xytext=(320,3500),fontsize=9,arrowprops={'arrowstyle':'-','color':TEAL})
grid(axs[1]);save(fig,'researcher-structure')
receipt['data_series_sha256']=hashlib.sha256(json.dumps({name:rows(name) for name in ['researcher-degree-ccdf','component-sizes','topic-trends','community-topic-profiles','sector-mixing','top-cited-papers']},sort_keys=True).encode()).hexdigest()

(OUT/'render-receipt.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({k:{a:v[a] for a in ['node_count','edge_count']} for k,v in receipt['selections'].items()},indent=2))
