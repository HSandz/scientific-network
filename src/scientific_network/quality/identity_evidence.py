"""Hash-verified evidence packets from bounded public Task2C source retrievals.

Extraction records observable locators and identifiers, never identity labels.
Full source text stays ignored; minimal public metadata excerpts are reportable.
"""
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path
import re
import subprocess
import tempfile

from bs4 import BeautifulSoup

from scientific_network.collect.storage import read_jsonl,write_json,write_jsonl
from scientific_network.quality.identity_audit import file_hash,unused


def inventory(provenances, caches, decisions_path, output):
    unused(output)
    if len(provenances)!=len(caches): raise ValueError('one cache per provenance ledger')
    ds={d['mention_id']:d for d in read_jsonl(decisions_path)}
    ledger=[];bymention=defaultdict(list)
    for provenance,cache in zip(provenances,caches):
        payload=json.loads(provenance.read_bytes())
        for r in payload['sources']:
            lead={k:r[k] for k in ('url','category','mention_ids','status')}
            lead.update(upstream_independence='unknown',identity_reference_status='pending_independent_review')
            if r['status']=='retrieved':
                rec=r['record'];path=cache/'objects'/rec['sha256']
                if file_hash(path)!=rec['sha256']:raise ValueError('source hash mismatch')
                data=path.read_bytes();pdf=data.startswith(b'%PDF')
                if pdf:
                    with tempfile.TemporaryDirectory() as temp:
                        out=Path(temp)/'page1.txt'
                        result=subprocess.run(['pdftotext','-f','1','-l','1','-layout',str(path),str(out)],capture_output=True)
                        text=out.read_text(errors='replace') if result.returncode==0 else ''
                    locator='PDF page 1 (pdftotext layout extraction; visual marker alignment still pending)'
                    links=[]
                else:
                    soup=BeautifulSoup(data,'html.parser');text=soup.get_text(' ',strip=True)
                    links=[a['href'] for a in soup.select('a[href]') if 'doi.org/' in a['href'] or 'orcid.org/' in a['href']]
                    locator='HTML publication entry; exact DOI/person link needs reviewer verification'
                ids=sorted(set(re.findall(r'\b\d{4}-\d{4}-\d{4}-\d{3}[\dX]\b',text)))
                lead.update(source=rec,cache_object=str(path),locator=locator,content_kind='pdf' if pdf else 'html',
                    text_extraction_nonempty=bool(text.strip()),printed_identifier_patterns=ids,
                    persistent_identifier_links=sorted(set(links)),
                    public_metadata_excerpt=' '.join(text[:400].split())[:240],
                    evidence_depth='printed_byline_context_only_no_automatic_person_crosswalk' if pdf else 'author_or_institution_publication_page_needs_exact_work_and_owner_check')
                # Another language/version of a construction-owner page is not new independent gold.
                if 'sigs.tsinghua.edu.cn' in r['url']:
                    lead['upstream_independence']='shared_construction_owner'
                    lead['limitation']='English owner profile was inspected in Task2B; language/endpoint change does not restore source independence'
                elif pdf:
                    lead['upstream_independence']='shared_official_publisher_family'
                    lead['limitation']='Official roster used in construction; paper PDF adds printed context but byline alone cannot prove canonical person ownership'
                else:
                    lead['limitation']='Independently retrieved owner/institution lead; possible provider upstream ingestion remains unknown'
            else:lead.update(failure=r.get('failure'),limitation='Access failure is not evidence against authorship')
            ledger.append(lead)
            for mid in r['mention_ids']:bymention[mid].append(len(ledger)-1)
    rows=[]
    for mid,indices in sorted(bymention.items()):
        d=ds[mid];available=[ledger[i] for i in indices if ledger[i]['status']=='retrieved']
        rows.append(dict(mention_id=mid,paper_id=d['paper_id'],author_position=d['author_position'],official_name=d['official_name'],
            candidate_mechanism=d['decision_reason'],source_indices=indices,retrieved_sources=len(available),
            identity_label=None,reference_identity=None,review_status='pending_actual_independent_judgments',
            remaining_requirement='Independent paper ownership AND justified candidate-person crosswalk; do not use name/provider/alias alone'))
    groups=defaultdict(list)
    for row in rows:groups[row['candidate_mechanism']].append(row)
    write_jsonl(output/'verification-ledger.jsonl',rows)
    write_jsonl(output/'source-records.jsonl',ledger)
    write_jsonl(output/'review-source-leads.jsonl',[{k:r[k] for k in ('url','status','mention_ids','upstream_independence','locator') if k in r} for r in ledger])
    write_json(output/'evidence-summary.json',dict(source_urls=len(ledger),retrieval_status=dict(Counter(r['status'] for r in ledger)),
        targeted_positions=len(rows),human_reviews=0,independent_adjudicated_references=0,
        categories={k:dict(targeted_positions=len(v),with_retrieved_source=sum(r['retrieved_sources']>0 for r in v),
            independent_person_references=0) for k,v in sorted(groups.items())},
        pdfs_with_printed_identifier_patterns=sum(bool(r.get('printed_identifier_patterns')) and r.get('content_kind')=='pdf' for r in ledger),
        method='source-inventory-not-identity-evaluation; regex identifiers are leads, not verified identifiers',
        provenance_hashes={str(p):file_hash(p) for p in provenances},decisions_sha256=file_hash(decisions_path)))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--provenances',type=Path,nargs='+',required=True);p.add_argument('--caches',type=Path,nargs='+',required=True)
    p.add_argument('--decisions',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();inventory(a.provenances,a.caches,a.decisions,a.output)

if __name__=='__main__':main()
