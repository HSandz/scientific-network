"""Isolated frozen-component identity candidate; never loads a database.

All path/config/input checks precede writes. Run with --help for explicit paths.
Original graph, snapshots and review decisions are read-only inputs.
"""

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import re

from scientific_network.collect.storage import read_config, read_jsonl, write_bytes, write_json, write_jsonl
from scientific_network.contracts import AffiliationObservation, Edge, GraphArtifact, Node
from scientific_network.graph.materialize import materialize
from scientific_network.graph.schema import edge_id
from scientific_network.graph.validate import graph_counts, validate_graph
from scientific_network.quality.identity_audit import file_hash, network_summary, unused
from scientific_network.quality.candidate_network import paired_rankings
from scientific_network.resolve import mentions_v5
from scientific_network.resolve.release import SECTOR, _sha, _work_evidence, authorship_institutions

METHOD = "identity-candidate-v5.3"
EXPECTED_POLICIES = {
    "work_doi_must_agree": True,
    "raw_name_required_for_recovery": True,
    "unique_raw_position_anchor_on_damaged_byline": True,
    "duplicate_provider_positions": "ambiguous",
    "profile_orcid_conflict_without_paper_raw_orcid": "ambiguous",
    "provider_id_incompatible_name_variants": "ambiguous_without_paper_identifier",
    "malformed_paper_raw_orcid": "ambiguous",
    "missing_provider_id_without_paper_raw_orcid": "unresolved",
    "names_or_coauthors_alone_merge": False,
    "paper_raw_orcid_name_expansion": "ordered_full_tokens_same_endpoints_and_canonical_agreement",
    "topic_citation_publication_taxonomy": "preserve_exact",
    "existing_affiliation_support": "preserve_exact_for_retained_positions",
    "multiple_paper_raw_orcids_with_compatible_names": "ambiguous",
    "semantic_accuracy": "unmeasured_without_independent_references",
}


def verify_sources(rows, cache):
    """Hash original bytes and compare full retained authorships,references,ID,DOI."""
    sources = defaultdict(list)
    for row in rows:
        if row["match"]["status"] == "matched":
            sources[row["openalex"]["source"]["raw_sha256"]].append(row)
    for digest, group in sorted(sources.items()):
        path = cache / "objects" / digest
        if file_hash(path) != digest:
            raise ValueError("cached source hash mismatch")
        raw = json.loads(path.read_bytes())
        for row in group:
            oa = row["openalex"]
            match = re.fullmatch(r"results\[(\d+)\](?:@page\d+)?", oa["source"]["locator"])
            work = raw["results"][int(match[1])] if match else raw
            if any(work.get(k) != oa.get(k) for k in ("id", "doi", "authorships", "referenced_works")):
                raise ValueError("source projection differs from raw: "+row["paper_id"])
    return {"matched_works": sum(map(len,sources.values())),"raw_objects_hashed": len(sources),"all_equal": True}


def _canonical_digest(items):
    return sha256(json.dumps(items,sort_keys=True,ensure_ascii=False,separators=(",", ":")).encode()).hexdigest()


def protected_content(old,new):
    """Topics/citations/venues/paper properties and all nonderived source evidence stay exact."""
    def content(g):
        return {
            "paper_venue_topic_nodes": [n.model_dump(mode="json") for n in sorted(g.nodes,key=lambda n:n.id)
                                        if n.label in {"Paper","Venue","Topic"}],
            "publication_citation_topic_taxonomy_edges": [e.model_dump(mode="json",exclude={"graph_version"})
                for e in sorted(g.edges,key=lambda e:e.edge_id) if e.relation in {"PUBLISHED_IN","CITES","HAS_TOPIC","SUBTOPIC_OF"}],
            "nonderived_evidence": [e.model_dump(mode="json") for e in sorted(g.evidence,key=lambda e:e.id) if e.kind != "derived"],
        }
    a,b=content(old),content(new)
    proof={}
    for k in a:
        left,right=_canonical_digest(a[k]),_canonical_digest(b[k])
        if left != right:
            raise ValueError("protected content changed: "+k)
        proof[k]={"before_sha256":left,"after_sha256":right,"equal":True}
    return proof


def construct_candidate(old,rows,decisions,version,quality):
    """Rebuild R1/R2/triples, then R7–R10. No classifier call or citation rematch."""
    nodes={n.id:n for n in old.nodes if n.label in {"Paper","Venue","Topic"}}
    previous={n.id:n for n in old.nodes}
    evidence={e.id:e for e in old.evidence if e.kind != "derived"}
    edges=[e.model_copy(update={"graph_version":version}) for e in old.edges
           if e.relation in {"PUBLISHED_IN","CITES","HAS_TOPIC","SUBTOPIC_OF"}]
    row_by_id={r["paper_id"]:r for r in rows}
    accepted=defaultdict(list)
    for d in decisions:
        if d["resolution_state"] == "resolved":
            if not d["canonical_researcher_id"]:
                raise ValueError("resolved mention missing canonical identity")
            accepted[d["paper_id"]].append(d)
    observations,pair_support=[],{}
    copy_guard=[]
    old_authored={(e.target_id,e.properties["byline_position"]):e.source_id for e in old.edges if e.relation=="AUTHORED"}
    old_affiliations=defaultdict(set)
    for o in old.affiliation_observations:
        old_affiliations[o.researcher_id,o.paper_id].add(o.organization_id)
    old_r2={(e.source_id,e.target_id):e for e in old.edges if e.relation=="AFFILIATED_WITH"}
    for paper, group in sorted(accepted.items()):
        if len({d["canonical_researcher_id"] for d in group}) != len(group):
            raise ValueError("candidate has repeated canonical person on one byline")
        row=row_by_id[paper]
        ev=_work_evidence(row)
        if ev.id not in evidence:
            raise ValueError("new identity must use existing source evidence")
        per_author=[]
        for d in sorted(group,key=lambda d:d["author_position"]):
            person=d["canonical_researcher_id"]
            authorship=row["openalex"]["authorships"][d["author_position"]-1]
            if person not in nodes:
                if person in previous:
                    nodes[person]=previous[person]
                else:
                    nodes[person]=Node(id=person,label="Researcher",name=d["official_name"],properties={
                        "resolution_status":"resolved","identity_method":mentions_v5.METHOD,
                        **({"openalex_id":d["source_author_id"]} if person.startswith("researcher:openalex:") else {}),
                        **({"orcid":d["paper_raw_orcid"]} if d["paper_raw_orcid"] else {})})
            edges.append(Edge(edge_id=edge_id("AUTHORED",person,paper),relation="AUTHORED",source_id=person,target_id=paper,
                              evidence_kind="observed",evidence_ids=[ev.id],method_version=mentions_v5.METHOD,
                              graph_version=version,validation_status="accepted",properties={
                                  "byline_position":d["author_position"],"roster_name":d["official_name"],
                                  "name_match":d["matching_method"],"identity_decision_id":d["decision_id"]}))
            old_person=old_authored.get((paper,d["author_position"]))
            # Preserve all prior exclusions for retained positions. Rechecking a
            # smaller post-withholding team must not reverse an old copy guard.
            per_author.append((person,authorship_institutions(authorship),old_person,old_affiliations[old_person,paper]))
        sets=[frozenset(i["id"] for i in insts) for _,insts,_,_ in per_author]
        # Frozen affiliation guard,applied to all candidate-accepted positions.
        # No affiliation inference or institution normalization changes.
        full_sets=[frozenset(i["id"] for i in authorship_institutions(a)) for a in row["openalex"]["authorships"]]
        copied=(len(sets)>=3 and len(set(sets))==1 and len(sets[0])>=2) or (
            len(full_sets)>=3 and len(set(full_sets))==1 and len(full_sets[0])>=2)
        if copied:
            copy_guard.append({"paper_id":paper,"kind":"paper_level_affiliation_copy","positions":len(group),
                               "applies_to":"new_positions_only; prior_support_and_exclusions_preserved"})
        for person,institutions,old_person,old_orgs in per_author:
            if old_person is None and copied:
                continue
            if old_person is not None:
                institutions=[i for i in institutions if "organization:"+i["id"] in old_orgs]
                if {"organization:"+i["id"] for i in institutions}!=old_orgs:
                    raise ValueError("retained affiliation no longer matches frozen raw institutions")
            for inst in institutions:
                org="organization:"+inst["id"]
                if org not in nodes:
                    nodes[org]=previous.get(org) or Node(id=org,label="Organization",name=inst["name"],properties={
                        "sector":SECTOR.get(inst["type"],"unknown"),"openalex_id":inst["id"],
                        **({"ror":inst["ror"]} if inst["ror"] else {}),
                        **({"country_code":inst["country_code"]} if inst["country_code"] else {})})
                observations.append(AffiliationObservation(id="affiliation:"+_sha(person,paper,org)[:24],
                    researcher_id=person,paper_id=paper,organization_id=org,evidence_ids=[ev.id]))
                support=pair_support.setdefault((person,org),{"evidence":set(),"papers":set(),"raw":set()})
                support["evidence"].add(ev.id);support["papers"].add(paper);support["raw"].update(inst["raw_strings"])
    for (person,org),s in sorted(pair_support.items()):
        previous_edge=old_r2.get((person,org))
        if (previous_edge is not None and set(previous_edge.evidence_ids)==s["evidence"]
                and previous_edge.properties.get("support_paper_count")==len(s["papers"])):
            edges.append(previous_edge.model_copy(update={"graph_version":version}))
            continue
        edges.append(Edge(edge_id=edge_id("AFFILIATED_WITH",person,org),relation="AFFILIATED_WITH",source_id=person,target_id=org,
                          evidence_kind="observed",evidence_ids=sorted(s["evidence"]),method_version=METHOD,
                          graph_version=version,validation_status="accepted",properties={
                              "support_paper_count":len(s["papers"]),"raw_affiliation_strings":sorted(s["raw"])[:5]}))
    # Only the identity-specific unresolved reason can change on a Paper.
    # Remove a stale all-withheld reason when individual positions recover.
    authored=set(accepted)
    paper_changes=[]
    for paper,node in list(nodes.items()):
        if node.label!="Paper":
            continue
        before=node.properties.get("unresolved_author_reason")
        after=before
        if paper not in authored and not before:
            after="identity_candidate_v5:all_mentions_abstained"
        elif paper in authored and before:
            after=None
        if before != after:
            props=dict(node.properties)
            if after is None:
                props.pop("unresolved_author_reason",None)
            else:
                props["unresolved_author_reason"]=after
            nodes[paper]=node.model_copy(update={"properties":props})
            paper_changes.append({"paper_id":paper,"before":before,"after":after})
    graph=GraphArtifact(graph_version=version,is_synthetic=old.is_synthetic,nodes=sorted(nodes.values(),key=lambda n:n.id),
                        edges=sorted(edges,key=lambda e:e.edge_id),evidence=sorted(evidence.values(),key=lambda e:e.id),
                        affiliation_observations=sorted(observations,key=lambda o:o.id))
    graph=materialize(graph,quality["derived"]["researcher_topic_min_distinct_papers"],quality["derived"]["organization_topic_min_distinct_papers"])
    return graph,copy_guard,paper_changes


def compare(old,new,decisions):
    def authored(g):
        return {(e.target_id,e.properties["byline_position"]):e.source_id for e in g.edges if e.relation=="AUTHORED"}
    a,b=authored(old),authored(new)
    gained,lost=b.keys()-a.keys(),a.keys()-b.keys()
    by_mention={(d["paper_id"],d["author_position"]):d for d in decisions}
    def observation_keys(g):
        return {(o.researcher_id,o.paper_id,o.organization_id) for o in g.affiliation_observations}
    oa,ob=observation_keys(old),observation_keys(new)
    af=lambda g:len({(o.researcher_id,o.paper_id) for o in g.affiliation_observations})
    def inventory(g):
        return {e.edge_id:e for e in g.edges}
    ea,eb=inventory(old),inventory(new)
    relation_delta={}
    for rel in sorted({str(e.relation) for e in old.edges+new.edges}):
        sa={k for k,e in ea.items() if str(e.relation)==rel};sb={k for k,e in eb.items() if str(e.relation)==rel}
        relation_delta[rel]={"before":len(sa),"after":len(sb),"gained":len(sb-sa),"lost":len(sa-sb),
                             "properties_or_evidence_changed":sum(ea[k].properties!=eb[k].properties or ea[k].evidence_ids!=eb[k].evidence_ids for k in sa&sb)}
    crosswalk=defaultdict(set)
    for d in decisions:
        if d["resolution_state"]=="resolved" and d["source_author_id"]:
            crosswalk[d["source_author_id"]].add(d["canonical_researcher_id"])
    canonical_sources=defaultdict(set)
    for source,targets in crosswalk.items():
        for target in targets:canonical_sources[target].add(source)
    old_people={n.id for n in old.nodes if n.label=="Researcher"}
    new_people={n.id for n in new.nodes if n.label=="Researcher"}
    before_orgs,after_orgs=defaultdict(set),defaultdict(set)
    for o in old.affiliation_observations:before_orgs[o.researcher_id,o.paper_id].add(o.organization_id)
    for o in new.affiliation_observations:after_orgs[o.researcher_id,o.paper_id].add(o.organization_id)
    for key in a.keys()&b.keys():
        if before_orgs[a[key],key[0]] != after_orgs[b[key],key[0]]:
            raise ValueError("identity-only candidate changed retained position affiliation support")
    strata=defaultdict(Counter)
    for key,d in by_mention.items():
        s=strata[f"{d['venue_id']}:{d['year']}"]
        s["official_positions"]+=1
        s["before_accepted"]+=key in a
        s["after_accepted"]+=key in b
        s["gained_positions"]+=key in gained
        s["lost_positions"]+=key in lost
        s["state:"+d["resolution_state"]]+=1
        s["reason:"+d["decision_reason"]]+=1
    return {"stage":"identity_candidate_comparison","baseline_graph_version":old.graph_version,"candidate_graph_version":new.graph_version,
            "before_counts":graph_counts(old),"after_counts":graph_counts(new),
            "researcher_identity_changes":{"gained":len(new_people-old_people),"lost":len(old_people-new_people)},
            "by_venue_year":{k:dict(sorted(v.items())) for k,v in sorted(strata.items())},
            "accepted_authorships":{"before":len(a),"after":len(b),"gained_positions":len(gained),"lost_positions":len(lost),
                                    "retained_positions_reassigned":sum(a[k]!=b[k] for k in a.keys()&b.keys()),
                                    "gained_by_reason":dict(Counter(by_mention[k]["decision_reason"] for k in gained)),
                                    "lost_by_reason":dict(Counter(by_mention[k]["decision_reason"] for k in lost))},
            "previously_globally_withheld_positions_recovered":sum(d["resolution_state"]=="resolved" and d["was_v4_global_identity_withheld"] for d in decisions),
            "remaining_states":dict(Counter(d["resolution_state"] for d in decisions)),
            "remaining_reasons":dict(sorted(Counter(d["decision_reason"] for d in decisions if d["resolution_state"]!="resolved").items())),
            "provider_ids_split_by_direct_evidence":sum(len(t)>1 for t in crosswalk.values()),
            "canonical_identities_with_multiple_provider_crosswalks":sum(len(t)>1 for t in canonical_sources.values()),
            "affiliated_positions":{"before":af(old),"after":af(new)},
            "retained_position_affiliation_support":{"positions_checked":len(a.keys()&b.keys()),"exact_organization_sets_preserved":True},
            "affiliation_observations":{"before":len(oa),"after":len(ob),"gained":len(ob-oa),"lost":len(oa-ob)},
            "relationship_changes":relation_delta,"network_before":network_summary(old),"network_after":network_summary(new),
            "semantic_metrics":{k:None for k in ("identity_pairwise_precision","identity_pairwise_recall","identity_pairwise_f1","authorship_precision","authorship_recall","false_merges","false_splits")},
            "semantic_evaluation":"not_measured; no independent identity gold; historical edge labels not reused"}


def build(config_path,output_dir,report_dir):
    unused(output_dir,report_dir)
    config=read_config(config_path)
    if config.get("policies")!=EXPECTED_POLICIES:
        raise ValueError("unsupported candidate policy; change method/version explicitly")
    sources={k:Path(config[k]) for k in ("works","source_graph","source_freeze","quality","analysis","baseline_audit")}
    hashes={k:file_hash(p) for k,p in sources.items()}
    hashes["config"]=file_hash(config_path)
    hashes["resolver_code"]=file_hash(Path(mentions_v5.__file__))
    hashes["candidate_code"]=file_hash(Path(__file__))
    from scientific_network.quality import candidate_network
    hashes["network_code"]=file_hash(Path(candidate_network.__file__))
    freeze=json.loads(sources["source_freeze"].read_bytes())
    if hashes["source_graph"]!=freeze["graph_sha256"] or hashes["works"]!=freeze["source_inputs"]["works"]["sha256"]:
        raise ValueError("candidate source differs from frozen v4")
    if hashes["quality"]!=freeze["source_inputs"]["quality"]["sha256"]:
        raise ValueError("candidate quality differs from frozen v4")
    if hashes["analysis"]!=freeze["config_hashes"].get(str(sources["analysis"])):
        raise ValueError("candidate analysis config differs from frozen v4")
    audit=json.loads(sources["baseline_audit"].read_bytes())
    if audit["inputs"]["graph"]["sha256"]!=hashes["source_graph"] or audit["inputs"]["works"]["sha256"]!=hashes["works"]:
        raise ValueError("baseline audit does not bind candidate inputs")
    quality=read_config(sources["quality"])
    old=GraphArtifact.model_validate_json(sources["source_graph"].read_bytes())
    if old.graph_version!=freeze["graph_version"] or old.graph_version!=audit["graph_version"]:
        raise ValueError("source graph version differs from freeze/audit")
    rows=read_jsonl(sources["works"])
    if len(rows)!=len({n.id for n in old.nodes if n.label=="Paper"}) or {r["paper_id"] for r in rows}!={n.id for n in old.nodes if n.label=="Paper"}:
        raise ValueError("source paper population mismatch")
    source_check=verify_sources(rows,Path(config["cache_dir"]))
    decisions,index=mentions_v5.resolve_mentions(rows,old)
    version="release-identity-v5-"+_canonical_digest([METHOD,mentions_v5.METHOD,hashes])[:12]
    graph,guard,paper_changes=construct_candidate(old,rows,decisions,version,quality)
    # Prove exact protected metadata after accounting for the enumerated reason-only changes.
    changes={c["paper_id"]:c for c in paper_changes}
    proof_nodes=[]
    for n in graph.nodes:
        if n.id in changes:
            props=dict(n.properties)
            if changes[n.id]["before"] is None:
                props.pop("unresolved_author_reason",None)
            else:
                props["unresolved_author_reason"]=changes[n.id]["before"]
            n=n.model_copy(update={"properties":props})
        proof_nodes.append(n)
    proof_graph=graph.model_copy(update={"nodes":proof_nodes})
    proof=protected_content(old,proof_graph)
    errors=validate_graph(graph,require_derived=True,max_topic_labels=quality["topics"]["max_labels_per_paper"],
                          researcher_min=quality["derived"]["researcher_topic_min_distinct_papers"],
                          organization_min=quality["derived"]["organization_topic_min_distinct_papers"])
    if errors:
        raise ValueError("candidate validation failed: "+"; ".join(errors[:10]))
    comparison=compare(old,graph,decisions)
    analysis=read_config(sources["analysis"])
    print("Computing paired researcher centrality diagnostics",flush=True)
    rankings,scores=paired_rankings(old,graph,sample_nodes=analysis["betweenness"]["sample_nodes"],seed=analysis["random_seed"])
    comparison.update({"method_version":METHOD,"input_hashes":hashes,"source_check":source_check,
                       "protected_content":proof,"paper_unresolved_reason_changes":paper_changes,
                       "structural_validation":"passed","affiliation_copy_guard_papers":len(guard)})
    output_dir.mkdir(parents=True)
    report_dir.mkdir(parents=True)
    write_bytes(output_dir/"graph.json",(graph.model_dump_json()+"\n").encode())
    write_jsonl(output_dir/"identity-decisions.jsonl",decisions)
    write_json(output_dir/"identity-index.json",index)
    write_json(output_dir/"centrality-scores.json",scores)
    write_jsonl(output_dir/"review-queue.jsonl",[d for d in decisions if d["review_required"]]+guard)
    comparison["artifacts"]={p.name:{"path":str(p),"sha256":file_hash(p)} for p in sorted(output_dir.iterdir())}
    write_json(report_dir/"comparison.json",comparison)
    write_json(report_dir/"network-comparison.json",rankings)
    write_json(report_dir/"candidate-manifest.json",{"method_version":METHOD,"graph_version":version,"inputs":hashes,
        "outputs":comparison["artifacts"],"comparison_sha256":file_hash(report_dir/"comparison.json"),
        "network_comparison_sha256":file_hash(report_dir/"network-comparison.json"),
        "status":"development_identity_candidate_not_independently_evaluated"})
    print(json.dumps({"graph_version":version,"authorships":comparison["accepted_authorships"],"states":comparison["remaining_states"]},indent=2))
    return comparison


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config",required=True,type=Path)
    parser.add_argument("--output-dir",required=True,type=Path)
    parser.add_argument("--report-dir",required=True,type=Path)
    args=parser.parse_args()
    build(args.config,args.output_dir,args.report_dir)


if __name__=="__main__":
    main()
