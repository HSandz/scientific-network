"""Additive baseline inventory: historical guard exclusions,topics,citations,source anomalies."""

import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path

from scientific_network.collect.storage import read_jsonl,write_json
from scientific_network.collect.openalex_release import normalize_doi
from scientific_network.resolve.release import authorship_institutions,short_id
from scientific_network.resolve.release_identity import collect_identity_evidence
from scientific_network.quality.identity_audit import file_hash,unused

METHOD="pipeline-inventory-v5.1"


def inventory(rows,graph,queue):
    identity=collect_identity_evidence(rows)
    paper_rows={r["paper_id"]:r for r in rows}
    accepted={(e["target_id"],e["properties"]["byline_position"]):e for e in graph["edges"] if e["relation"]=="AUTHORED"}
    topics=Counter(e["source_id"] for e in graph["edges"] if e["relation"]=="HAS_TOPIC")
    targets=defaultdict(set)
    for r in rows:
        if r["match"]["status"]=="matched":
            oa=r["openalex"]
            for w in [oa]+oa.get("alternates",[]):
                targets[short_id(w["id"])].add(r["paper_id"])
    strata=defaultdict(Counter);doi_anomalies=[];expected_cites=set()
    accepted_conflicts,wrong_provider=[],[]
    for r in rows:
        s=strata[f"{r['venue_id']}:{r['year']}"]
        p=r["paper_id"]
        s["papers"]+=1;s["topic_labeled_papers"]+=topics[p]>0;s["topic_assignments"]+=topics[p]
        if r["match"]["status"]!="matched":continue
        oa=r["openalex"]
        if normalize_doi(r["doi"])!=normalize_doi(oa["doi"]):
            doi_anomalies.append({"paper_id":p,"official_doi":r["doi"],"returned_doi":oa["doi"],
                "author_positions":len(r["roster"]["authors"]),"source":{k:v for k,v in oa["source"].items() if k!="params"}})
        for ref in sorted(set(oa["referenced_works"])):
            candidates=targets.get(short_id(ref),set())
            key="citation_out_of_scope" if not candidates else "citation_ambiguous_target" if len(candidates)>1 else "citation_self" if p in candidates else "citation_accepted"
            s[key]+=1
            if key=="citation_accepted":expected_cites.add((p,next(iter(candidates))))
        for i,a in enumerate(oa["authorships"],1):
            edge=accepted.get((p,i))
            aid=short_id((a.get("author") or {}).get("id"))
            if edge:
                if aid in identity["withheld"]:accepted_conflicts.append([p,i,aid])
                if edge["source_id"]!="researcher:openalex:"+str(aid):wrong_provider.append([p,i,aid,edge["source_id"]])
                s["accepted_positions_without_source_institution"]+=not authorship_institutions(a)
    supported_triples={(e["source_id"],p,"organization:"+inst["id"])
        for (p,pos),e in accepted.items() for inst in authorship_institutions(paper_rows[p]["openalex"]["authorships"][pos-1])}
    actual_triples={(o["researcher_id"],o["paper_id"],o["organization_id"]) for o in graph["affiliation_observations"]}
    actual_cites={(e["source_id"],e["target_id"]) for e in graph["edges"] if e["relation"]=="CITES"}
    guard=[r for r in queue if r["kind"]=="paper_level_affiliation_copy"]
    guard_papers={r["paper_id"] for r in guard}
    guard_surviving={(p,pos) for p,pos in accepted if p in guard_papers}
    actual_affiliated={(o["researcher_id"],o["paper_id"]) for o in graph["affiliation_observations"]}
    missing_supported={(p,pos) for (p,pos),e in accepted.items() if authorship_institutions(paper_rows[p]["openalex"]["authorships"][pos-1]) and (e["source_id"],p) not in actual_affiliated}
    return {"method_version":METHOD,"by_venue_year":{k:dict(sorted(v.items())) for k,v in sorted(strata.items())},
        "doi_disagreements":doi_anomalies,
        "historical_affiliation_copy_guard":{"original_papers":len(guard),"original_positions":sum(x["authors"] for x in guard),
            "v4_surviving_positions_on_original_guard_papers":len(guard_surviving),
            "v4_institution_supported_positions_missing_graph_affiliations":len(missing_supported),
            "missing_supported_positions_explained_by_original_guard":len(missing_supported&guard_surviving),
            "unexplained_missing_supported_positions":len(missing_supported-guard_surviving)},
        "claim_support":{"accepted_conflicting_provider_positions":accepted_conflicts,"authorship_provider_position_disagreements":wrong_provider,
            "affiliation_triples_without_source_institution":len(actual_triples-supported_triples),
            "citation_inventory_equal_source_filtered_core_targets":actual_cites==expected_cites,
            "unsupported_citations":len(actual_cites-expected_cites),"missing_source_supported_core_citations":len(expected_cites-actual_cites)},
        "limits":"source-consistency only; no independent semantic accuracy,reference completeness,ORCID ownership,topic labels or historical affiliation gold"}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("works","graph","historical-review-queue","output"):
        p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args();unused(a.output)
    inputs={k:{"path":str(getattr(a,k)),"sha256":file_hash(getattr(a,k))} for k in ("works","graph","historical_review_queue")}
    result=inventory(read_jsonl(a.works),json.loads(a.graph.read_bytes()),read_jsonl(a.historical_review_queue))
    result["inputs"]=inputs
    write_json(a.output,result)
    print(json.dumps({k:v for k,v in result.items() if k not in {"by_venue_year","doi_disagreements"}},indent=2))


if __name__=="__main__":main()
