"""Bilingual PDF/source checks; visual inspection is recorded separately.

Requires final local PDFs plus exact frozen graph/summary/analysis to verify
accepted selections. All output stays under report/latex/review/redesign/.
"""
from pathlib import Path
from xml.etree import ElementTree as ET
from collections import Counter
import hashlib,json,re,subprocess
BASE=Path(__file__).resolve().parents[1];ROOT=BASE.parents[1]
OUT=BASE/'review/redesign';OUT.mkdir(parents=True,exist_ok=True)
def run(*args):return subprocess.check_output([str(x) for x in args],text=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

# Numeric literals in corresponding narrative files; shared macros/tables are
# verified through their one common manifest and the rendered PDFs below.
parity={}
for rel in ['overview.tex']+['chapters/'+x for x in ['01-data.tex','02-graph.tex','03-quality.tex','04-analysis.tex','05-conclusion.tex']]:
 en,vi=[(BASE/lang/rel).read_text() for lang in ['en','vi']]
 tokens=lambda s:Counter(re.findall(r'\d+(?:[.,]\d+)*',s))
 assert tokens(en)==tokens(vi),(rel,tokens(en)-tokens(vi),tokens(vi)-tokens(en))
 parity[rel]='numeric literals identical'

manifest=json.loads((BASE/'data/fact-manifest.json').read_text())
for rel,h in manifest['inputs_sha256'].items():assert sha(ROOT/rel)==h,rel
s=json.loads((ROOT/'reports/release-v4/graph-summary.json').read_text())
assert sum(s['counts']['nodes_by_label'].values())==manifest['values']['TotalNodes']==47875
assert sum(s['counts']['edges_by_relation'].values())==manifest['values']['TotalEdges']==225731
baseline=OUT/'baseline/protected-hashes.json'
if baseline.exists():
 for rel,h in json.loads(baseline.read_text()).items():assert sha(ROOT/rel)==h,rel
# Original protected logo is independently checked against the repository.
assert (BASE/'assets/uet.png').read_bytes()==subprocess.check_output(['git','show','4b265c8:report/latex/assets/uet.png'],cwd=ROOT)
receipts={lang:json.loads((BASE/f'figures/{lang}/render-receipt.json').read_text()) for lang in ['en','vi']}
assert receipts['en']['data_series_sha256']==receipts['vi']['data_series_sha256']
assert receipts['en']['selections']==receipts['vi']['selections']
g=json.loads((ROOT/'data/processed/release-graph-v4/graph.json').read_bytes())
assert g['graph_version']==manifest['graph_version']=='release-d3c788c3114a'
assert not g['is_synthetic']
edges={e['edge_id']:e for e in g['edges']};nodes={n['id']:n for n in g['nodes']}
for receipt in receipts.values():
 for rel,h in receipt['inputs_sha256'].items():assert sha(ROOT/rel)==h,rel
 for name,sel in receipt['selections'].items():
  ns={x['id'] for x in sel['nodes']};es=[edges[x] for x in sel['edge_ids']]
  assert len(ns)==sel['node_count'] and len(es)==sel['edge_count']
  assert all(e['validation_status']=='accepted' and e['source_id'] in ns and e['target_id'] in ns for e in es)
  if name=='researchers-network':
   assert {e['edge_id'] for e in g['edges'] if e['relation']=='COAUTHORED_WITH' and e['validation_status']=='accepted' and e['source_id'] in ns and e['target_id'] in ns}==set(sel['edge_ids'])
example=json.loads((BASE/'data/construction-example.json').read_text())
assert all(nodes[n['id']]==n for n in example['nodes'])
assert all(edges[e['edge_id']]==e and e['validation_status']=='accepted' for e in example['edges'])
observations={x['id']:x for x in g['affiliation_observations']}
assert all(observations[o['id']]==o for o in example['affiliation_observations'])
assert len([e for e in example['edges'] if e['relation']=='AUTHORED'])==2
assert nodes[example['paper_id']]['properties']['official_author_count']==3

result={'status':'passed','graph_version':g['graph_version'],'numeric_source_parity':parity,'same_figure_data_and_selections':True,'construction_example_accepted_edges_verified':True,'protected_logo_unchanged':True,'editions':{}}
for lang in ['en','vi']:
 pdf=BASE/f'build/report-{lang}.pdf';log=(BASE/f'build/report-{lang}.log').read_text()
 info=run('pdfinfo',pdf);n=int(re.search(r'^Pages:\s+(\d+)',info,re.M)[1])
 boxes=run('pdfinfo','-f','1','-l',n,'-box',pdf)
 sizes=re.findall(r'Page\s+\d+ size:\s+([\d.]+) x ([\d.]+)',boxes)
 rotations=re.findall(r'Page\s+\d+ rot:\s+(\d+)',boxes)
 assert len(sizes)==len(rotations)==n
 assert all(abs(float(w)-595.276)<.1 and abs(float(h)-841.89)<.1 for w,h in sizes)
 assert all(r=='0' for r in rotations)
 assert not re.search(r'Overfull \\[hv]box|undefined references|Citation .*undefined|Reference .*undefined|Missing character|LaTeX Error',log),lang
 xml=OUT/f'{lang}-bbox.html';subprocess.run(['pdftotext','-bbox-layout',str(pdf),str(xml)],check=True)
 pages=ET.parse(xml).findall('.//{*}page');counts=[];outliers=[];wide=[]
 for i,page in enumerate(pages,1):
  words=page.findall('.//{*}word');counts.append(len(words))
  for w in words:
   x0,y0,x1,y1=[float(w.attrib[k]) for k in ['xMin','yMin','xMax','yMax']]
   if x0<0 or y0<0 or x1>595.4 or y1>842:outliers.append([i,w.text])
   if x0<65 or x1>531:wide.append([i,w.text,round(x0,2),round(x1,2)])
 assert not outliers,(lang,outliers)
 assert min(counts)>65,(lang,counts)
 txt=run('pdftotext','-layout',pdf,'-');(OUT/f'{lang}-text.txt').write_text(txt)
 assert not re.search(r'(?<![\d.])90\s*%',txt)
 for v in ['47,875','225,731','13,617','13,606','32,189','2,047','80,482','13,031','7,308','48,259','65,469','11,575','2,042','0.042193']:
  assert v in txt,(lang,v)
 assert 'release-d3c788c3114a' in txt
 assert not re.search(r'candidate-v3|release-9d4a6fb20f63|Task2[BCD]',txt)
 if lang=='vi':
  for term in ['Thu thập','đồ thị','nghiên cứu','Tài liệu tham khảo','Mục lục','ĐẠI HỌC QUỐC GIA HÀ NỘI']:
   assert term in txt,(lang,term)
  for name in ['topic-trends','community-topic-profiles','sector-mixing','publications','researcher-structure','organizations-network','top-cited-papers']:
   figtext=run('pdftotext',BASE/f'figures/vi/{name}.pdf','-')
   for leftover in ['Planning and reasoning','Trustworthy machine learning','Fractional topic share','Proceedings year','Distinct in-corpus citing papers','Partner sector','Labeled','Unlabeled']:
    assert leftover not in figtext,(name,leftover)
 aux=(BASE/f'build/report-{lang}.aux').read_text()
 keys={k for group in re.findall(r'\\citation\{([^}]+)\}',aux) for k in group.split(',')}
 bibkeys=set(re.findall(r'@\w+\{([^,]+),',(BASE/'references.bib').read_text()))
 assert keys<=bibkeys
 labels=set(re.findall(r'\\newlabel\{(fig:[^}]+)\}',aux));assert len(labels)==10,(lang,labels)
 fonts=run('pdffonts',pdf);(OUT/f'{lang}-fonts.txt').write_text(fonts)
 assert not re.search(r'\sno\s+(?:yes|no)\s+(?:yes|no)\s+\d+\s+\d+\s*$',fonts,re.M),'Unembedded PDF font'
 result['editions'][lang]={'pages':n,'portrait_A4':True,'zero_rotated_pages':True,'no_overfull_boxes':True,'no_missing_characters_or_references':True,'figure_count':len(labels),'cited_keys':sorted(keys),'page_word_counts':counts,'words_outside_page':outliers,'text_width_outliers_for_visual_inspection':wide,'sha256':sha(pdf),'bytes':pdf.stat().st_size}
assert result['editions']['en']['cited_keys']==result['editions']['vi']['cited_keys']
result['visual_inspection']='Not certified by this script; see REVIEW-BILINGUAL.md and final contact sheets.'
(OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({lang:{k:v for k,v in e.items() if k not in ['page_word_counts','cited_keys','text_width_outliers_for_visual_inspection']} for lang,e in result['editions'].items()},indent=2))
