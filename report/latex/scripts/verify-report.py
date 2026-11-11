"""Report-only mechanical checks; visual page inspection remains mandatory."""
from pathlib import Path
from xml.etree import ElementTree as ET
import hashlib, json, re, subprocess

BASE=Path(__file__).resolve().parents[1]
ROOT=BASE.parents[1]
PDF=BASE/'build/main.pdf'
OUT=BASE/'review/final'
OUT.mkdir(parents=True,exist_ok=True)
def run(*args):return subprocess.check_output([str(x) for x in args],text=True)
info=run('pdfinfo',PDF)
n=int(re.search(r'^Pages:\s+(\d+)',info,re.M)[1])
boxes=run('pdfinfo','-f','1','-l',n,'-box',PDF)
rotations=re.findall(r'Page\s+\d+ rot:\s+(\d+)',boxes)
sizes=re.findall(r'Page\s+\d+ size:\s+([\d.]+) x ([\d.]+)',boxes)
assert len(rotations)==len(sizes)==n
assert all(r=='0' for r in rotations), 'Rotated page'
assert all(abs(float(w)-595.276)<.1 and abs(float(h)-841.89)<.1 for w,h in sizes), 'Non-portrait A4 page'
xml=OUT/'bbox.html'
subprocess.run(['pdftotext','-bbox-layout',str(PDF),str(xml)],check=True)
pages=ET.parse(xml).findall('.//{*}page')
word_counts=[];outside=[];outside_text_width=[];page_labels={}
for i,page in enumerate(pages,1):
 words=page.findall('.//{*}word');word_counts.append(len(words));text=' '.join(w.text or '' for w in words)
 for term in ['Figure 3.1:','Table 3.1:','Figure 4.1:','Figure 6.2:','Figure 6.5:','Figure 6.7:','Figure 6.8:','Figure 6.10:','Full Graph Schema','Bibliography']:
  if term in text:page_labels.setdefault(term,[]).append(i)
 for w in words:
  x0,y0,x1,y1=[float(w.attrib[k]) for k in ['xMin','yMin','xMax','yMax']]
  if x0<0 or y0<0 or x1>595.4 or y1>842:outside.append([i,w.text])
  if x0<70 or x1>525.5:outside_text_width.append([i,w.text,x0,x1])
assert not outside, outside
assert min(word_counts)>65, 'Blank or very sparse page requires inspection'
log=(BASE/'build/main.log').read_text()
assert not re.search(r'undefined references|Citation .*undefined|Reference .*undefined|not found|Missing character',log), 'Unresolved source/character/reference'
overfull=[float(v) for v in re.findall(r'Overfull \\[hv]box \(([\d.]+)pt',log)]
assert not overfull,overfull
aux=(BASE/'build/main.aux').read_text();bib=(BASE/'references.bib').read_text()
keys=re.findall(r'@\w+\{([^,]+),',bib);assert len(keys)==len(set(keys)), 'Duplicate bibliography key'
cited={k for group in re.findall(r'\\citation\{([^}]+)\}',aux) for k in group.split(',')}
assert cited.issubset(keys),cited-set(keys)
original_logo=subprocess.check_output(['git','show','HEAD:report/latex/assets/uet.png'],cwd=ROOT)
assert (BASE/'assets/uet.png').read_bytes()==original_logo, 'Protected logo changed'
receipt=json.loads((BASE/'figures/render-receipt.json').read_text())
for rel,digest in receipt['inputs_sha256'].items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==digest, rel
# Verify every selected stable ID, accepted edge and endpoint directly against v4.
g=json.loads((ROOT/'data/processed/release-graph-v4/graph.json').read_bytes())
edges={e['edge_id']:e for e in g['edges']}
for name,s in receipt['selections'].items():
 ns={x['id'] for x in s['nodes']};es=[edges[x] for x in s['edge_ids']]
 assert len(ns)==s['node_count'] and len(es)==s['edge_count']
 assert all(e['validation_status']=='accepted' and e['source_id'] in ns and e['target_id'] in ns for e in es)
 if name=='researchers-network':
  expected={e['edge_id'] for e in g['edges'] if e['relation']=='COAUTHORED_WITH' and e['source_id'] in ns and e['target_id'] in ns and e['validation_status']=='accepted'}
  assert expected==set(s['edge_ids']), 'Researcher view not induced'
 if name=='citations-network':assert all(e['target_id']=='paper:aaai:2021:17325' for e in es)
result={'status':'passed','pages':n,'portrait_A4_pages':n,'rotated_pages':0,'undefined_references_or_citations':False,
 'overfull_boxes':overfull,'words_outside_page':outside,'words_outside_text_width_for_visual_check':outside_text_width,
 'minimum_page_word_count':min(word_counts),'page_word_counts':word_counts,'page_labels':page_labels,
 'cited_keys':len(cited),'protected_logo_identical_to_HEAD':True,'frozen_input_hashes_verified':True,
 'accepted_edge_selections_verified':True,'pdf_sha256':hashlib.sha256(PDF.read_bytes()).hexdigest(),
 'visual_inspection':'Recorded separately in REVIEW.md; this script does not certify visual quality.'}
(OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['page_word_counts','cited_keys']},indent=2))
