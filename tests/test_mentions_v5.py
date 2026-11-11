"""Invented identities: states and exact accepted downstream support,not benchmark scores."""

from copy import deepcopy
from hashlib import sha256
import json

import pytest
import yaml

from scientific_network.collect.storage import read_config
from scientific_network.graph.validate import validate_graph
from scientific_network.resolve import candidate_v5, mentions_v5
from scientific_network.resolve.release_identity import collect_identity_evidence
from test_release_graph import QUALITY, authorship, build, edges, inst, row

ONE,TWO="0000-0002-1825-0097","0000-0001-5109-3700"


def paper(n,names,people):
    r=row(n,names,people)
    r["openalex"]["doi"]=r["doi"]
    return r


def raw_person(aid,name,orcid=None,**kwargs):
    a=authorship(aid,name,**kwargs)
    if orcid:
        a["raw_orcid"]=orcid
    return a


def resolved(rows):
    return mentions_v5.resolve_mentions(rows)[0]


@pytest.mark.parametrize("official,raw,kind",[
    ("José García","Jose Garcia","exact"),
    ("Li Wei","Wei Li","exact"),
    ("Jean-Luc Martin","Jean Luc Martin","exact"),
    ("Zhang Wei","Wei Zhang","exact"),
    ("王伟","王伟","exact"),
    ("Ann One","A. One","initials"),
    ("J. P. Smith","John Paul Smith","initials"),
    ("Ann One","Alice One",None),
    ("Ann One","Ann Marie One",None),
    ("Wei Zhang","Way Zhang",None),
    ("Ann One","A. O.",None),
])
def test_conservative_position_names(official,raw,kind):
    assert mentions_v5.positional_name(official,raw)==kind


def test_same_person_name_forms_and_same_name_people_never_name_merge():
    rows=[paper(1,["José García","Ann One","Ann One"],[raw_person("A1","Jose Garcia"),raw_person("A2","Ann One"),raw_person("A3","Ann One")]),
          paper(2,["J. García"],[raw_person("A1","Jose Garcia")])]
    ds=resolved(rows)
    assert [d["resolution_state"] for d in ds]==["resolved"]*4
    assert [d["canonical_researcher_id"] for d in ds]==["researcher:openalex:"+a for a in ("A1","A2","A3","A1")]
    assert not any(d["paper_raw_orcid"] for d in ds)


def test_conflicting_provider_can_only_split_direct_paper_identifiers():
    a=raw_person("A1","Ann One",ONE);b=raw_person("A1","Bo Two",TWO)
    for p in (a,b):p["author"]["observed_orcids"]=[ONE,TWO]
    rows=[paper(1,["Ann One"],[a]),paper(2,["Bo Two"],[b]),paper(3,["Ann One"],[raw_person("A1","Ann One")])]
    ds,index=mentions_v5.resolve_mentions(rows)
    assert [d["resolution_state"] for d in ds]==["resolved","resolved","ambiguous"]
    assert [d["canonical_researcher_id"] for d in ds]==["researcher:orcid:"+ONE,"researcher:orcid:"+TWO,None]
    assert all(d["contradicting_evidence"] for d in ds)
    assert index["provider_withholding"]["A1"]


def test_one_person_multiple_provider_ids_require_paper_raw_crosswalk():
    rows=[paper(1,["Ann One"],[raw_person("A1","Ann One",ONE)]),
          paper(2,["A. One"],[raw_person("A2","Ann One",ONE)]),
          paper(3,["Ann One"],[raw_person("A2","Ann One")])]
    ds,index=mentions_v5.resolve_mentions(rows)
    assert {d["canonical_researcher_id"] for d in ds}=={"researcher:orcid:"+ONE}
    assert index["corroborated_provider_crosswalks"]=={"A1":"researcher:orcid:"+ONE,"A2":"researcher:orcid:"+ONE}


def test_missing_provider_id_uses_paper_raw_orcid_or_remains_unresolved():
    ds=resolved([paper(1,["Ann One","Bo Two"],[raw_person(None,"Ann One",ONE),raw_person(None,"Bo Two")])])
    assert [d["resolution_state"] for d in ds]==["resolved","unresolved"]
    assert ds[0]["canonical_researcher_id"]=="researcher:orcid:"+ONE
    assert ds[1]["canonical_researcher_id"] is None


def test_incorrect_alignment_is_not_reordered_and_unique_other_position_recovers(tmp_path):
    rows=[paper(1,["Ann One","Bo Two","Cam Three"],[raw_person("A1","Bo Two"),raw_person("A2","Ann One"),raw_person("A3","Cam Three",institutions=[inst("I1")])])]
    old,_,_=build(tmp_path,rows)
    ds=resolved(rows)
    assert [d["resolution_state"] for d in ds]==["ambiguous","ambiguous","resolved"]
    assert ds[-1]["decision_reason"]=="unique_raw_position_recovered"
    new,_,_=candidate_v5.construct_candidate(old,rows,ds,"release-test-v5",read_config(QUALITY))
    assert [(e.source_id,e.target_id) for e in edges(new,"AUTHORED")]==[("researcher:openalex:A3",rows[0]["paper_id"])]
    assert len(edges(new,"COAUTHORED_WITH"))==0
    assert len(new.affiliation_observations)==1
    assert validate_graph(new,require_derived=True)==[]


def test_repeated_provider_positions_block_both_but_keep_unique_coauthors(tmp_path):
    rows=[paper(1,["Ann One","Bo Two","Cam Three","Dan Four"],[raw_person("A1","Ann One"),raw_person("A1","Bo Two"),raw_person("A3","Cam Three"),raw_person("A4","Dan Four")])]
    old,_,_=build(tmp_path,rows)
    ds=resolved(rows)
    assert [d["resolution_state"] for d in ds]==["ambiguous","ambiguous","resolved","resolved"]
    new,_,_=candidate_v5.construct_candidate(old,rows,ds,"release-test-v5",read_config(QUALITY))
    assert {e.source_id for e in edges(new,"AUTHORED")}=={"researcher:openalex:A3","researcher:openalex:A4"}
    assert len(edges(new,"COAUTHORED_WITH"))==1
    assert edges(new,"COAUTHORED_WITH")[0].properties=={"support_count":1,"fractional_weight":1/3}


def test_conflicting_affiliations_do_not_merge_or_globally_remove_identity(tmp_path):
    rows=[paper(n,["Ann One"],[raw_person("A1","Ann One",institutions=[inst("I"+str(n))])]) for n in (1,2)]
    old,_,_=build(tmp_path,rows)
    ds=resolved(rows)
    assert all(d["resolution_state"]=="resolved" for d in ds)
    new,_,_=candidate_v5.construct_candidate(old,rows,ds,"release-test-v5",read_config(QUALITY))
    assert {(o.paper_id,o.organization_id) for o in new.affiliation_observations}=={(r["paper_id"],"organization:I"+str(n)) for n,r in enumerate(rows,1)}
    assert not edges(new,"COLLABORATED_WITH")


def test_one_ambiguous_position_does_not_prevent_verified_positions():
    bad=raw_person("A1","Ann One");bad["author"]["observed_orcids"]=[ONE,TWO]
    ds=resolved([paper(1,["Ann One","Bo Two"],[bad,raw_person("A2","Bo Two")])])
    assert [d["resolution_state"] for d in ds]==["ambiguous","resolved"]
    assert ds[0]["canonical_researcher_id"] is None
    assert ds[1]["canonical_researcher_id"]=="researcher:openalex:A2"


@pytest.mark.parametrize("change,reason",[
    ("doi","work_doi_disagreement"),("count","work_author_count_disagreement"),
    ("raw_name","raw_name_missing"),("orcid","malformed_paper_raw_orcid"),
])
def test_missing_contradictory_source_fields_abstain(change,reason):
    r=paper(1,["Ann One"],[raw_person("A1","Ann One")])
    if change=="doi":r["openalex"]["doi"]="10.123/other"
    if change=="count":r["openalex"]["authorships"].append(raw_person("A2","Bo Two"))
    if change=="raw_name":r["openalex"]["authorships"][0].pop("raw_author_name")
    if change=="orcid":r["openalex"]["authorships"][0]["raw_orcid"]="0000-0002-1825-0098"
    d=resolved([r])[0]
    assert d["resolution_state"]=="ambiguous" and d["canonical_researcher_id"] is None
    assert d["decision_reason"]==reason


def test_global_name_contradictions_remain_ambiguous_without_direct_identifier():
    ds=resolved([paper(1,["Ann One"],[raw_person("A1","Ann One")]),paper(2,["Bo Two"],[raw_person("A1","Bo Two")])])
    assert [d["decision_reason"] for d in ds]==["author_id_incompatible_name_variants"]*2
    assert all(d["resolution_state"]=="ambiguous" for d in ds)


def test_raw_orcid_middle_expansion_and_profile_conflict_are_position_scoped():
    a=raw_person("A1","Wim Van den Broeck",ONE,raw="Wim Michel Hugo Van den Broeck")
    a["author"]["orcid"]=TWO;a["author"]["observed_orcids"]=[ONE,TWO]
    ds=resolved([paper(1,["Wim Van den Broeck"],[a]),paper(2,["Wim Van den Broeck"],[raw_person("A1","Wim Van den Broeck")])])
    assert ds[0]["resolution_state"]=="resolved"
    assert ds[0]["matching_method"]=="raw_orcid_middle_expansion"
    assert ds[0]["canonical_researcher_id"]=="researcher:orcid:"+ONE
    assert ds[1]["resolution_state"]=="ambiguous"


def test_raw_orcid_conflicting_names_and_within_paper_collision_abstain():
    rows=[paper(1,["Ann One"],[raw_person("A1","Ann One",ONE)]),paper(2,["Bo Two"],[raw_person("A2","Bo Two",ONE)])]
    assert {d["decision_reason"] for d in resolved(rows)}=={"raw_orcid_incompatible_names"}
    r=paper(1,["Ann One","Ann One"],[raw_person("A1","Ann One",ONE),raw_person("A2","Ann One",ONE)])
    assert {d["decision_reason"] for d in resolved([r])}=={"raw_orcid_repeated_in_paper"}


def test_initials_ambiguity_not_resolved_from_shared_surname():
    ds=resolved([paper(1,["A. One","Bo Two"],[raw_person("A1","Ann One"),raw_person("A2","Alice One")])])
    assert ds[0]["resolution_state"]=="ambiguous"
    assert ds[0]["decision_reason"]=="initials_position_not_unique"


def test_deterministic_decisions_and_graph_preserve_input_objects(tmp_path):
    rows=[paper(1,["Ann One","Bo Two"],[raw_person("A1","Ann One"),raw_person("A2","Bo Two")])]
    old,_,_=build(tmp_path,rows)
    old_bytes=old.model_dump_json();before=deepcopy(rows)
    one=mentions_v5.resolve_mentions(rows,old)
    two=mentions_v5.resolve_mentions(deepcopy(rows),old)
    assert one==two
    q=read_config(QUALITY)
    a,_,_=candidate_v5.construct_candidate(old,rows,one[0],"release-test-v5",q)
    b,_,_=candidate_v5.construct_candidate(old,rows,two[0],"release-test-v5",q)
    assert a.model_dump_json()==b.model_dump_json()
    assert old.model_dump_json()==old_bytes and rows==before
    assert candidate_v5.protected_content(old,a)
    assert validate_graph(a,require_derived=True)==[]
    assert all(e.properties.get("identity_decision_id") in {d["decision_id"] for d in one[0]} for e in edges(a,"AUTHORED"))


@pytest.mark.parametrize("trigger",["names","duplicate"])
def test_original_builder_shadow_regression_preserves_global_lookup(tmp_path,trigger):
    if trigger=="names":
        first=paper(1,["Ann One","Bo Two"],[raw_person("A1","Wrong Person"),raw_person("A2","Other Person")])
    else:
        first=paper(1,["Ann One","Bo Two"],[raw_person("A1","Ann One"),raw_person("A1","Bo Two")])
    bad=raw_person("A3","Cam Three");bad["author"]["observed_orcids"]=[ONE,TWO]
    rows=[first,paper(2,["Cam Three"],[bad]),paper(3,["Dan Four"],[raw_person("A4","Dan Four")])]
    graph,summary,_=build(tmp_path,rows)
    assert {e.source_id for e in edges(graph,"AUTHORED")}=={"researcher:openalex:A4"}
    assert collect_identity_evidence(rows)["withheld"]=={"A3":"author_id_conflicting_orcids"}
    assert summary["coverage"]["author_positions_accepted"]==1


def test_guard_exclusions_remain_frozen_when_authors_withheld(tmp_path):
    people=[raw_person("A"+str(i),name,institutions=[inst("I1"),inst("I2")]) for i,name in enumerate(["Ann One","Bo Two","Cam Three"],1)]
    rows=[paper(1,["Ann One","Bo Two","Cam Three"],people)]
    old,_,_=build(tmp_path,rows)
    assert not old.affiliation_observations
    rows.append(paper(2,["Ann One"],[raw_person("A1","Ann One")]))
    rows[0]["openalex"]["authorships"][0]["author"]["observed_orcids"]=[ONE,TWO]
    ds=resolved(rows)
    new,_,_=candidate_v5.construct_candidate(old,rows,ds,"release-test-v5",read_config(QUALITY))
    assert not new.affiliation_observations
    assert len(edges(new,"AUTHORED"))==2


def test_full_candidate_build_is_repeatable_hash_bound_and_non_overwriting(tmp_path):
    r=paper(1,["Ann One","Bo Two"],[raw_person("A1","Ann One",institutions=[inst("I1")]),raw_person("A2","Bo Two",institutions=[inst("I2")])])
    raw=json.dumps({"results":[deepcopy(r["openalex"])]}).encode()
    digest=sha256(raw).hexdigest()
    r["openalex"]["source"]["raw_sha256"]=digest
    cache=tmp_path/"cache"; (cache/"objects").mkdir(parents=True)
    (cache/"objects"/digest).write_bytes(raw)
    old,_,_=build(tmp_path,[r])
    graph_path=tmp_path/"graph"/"graph.json"
    analysis=tmp_path/"analysis.yaml"
    analysis.write_text(yaml.safe_dump({"random_seed":17,"betweenness":{"sample_nodes":2}}))
    freeze=tmp_path/"freeze.json"
    hashes={"works":candidate_v5.file_hash(tmp_path/"works.jsonl"),"graph":candidate_v5.file_hash(graph_path),"quality":candidate_v5.file_hash(QUALITY)}
    freeze.write_text(json.dumps({"graph_sha256":hashes["graph"],"graph_version":old.graph_version,
        "source_inputs":{"works":{"sha256":hashes["works"]},"quality":{"sha256":hashes["quality"]}},
        "config_hashes":{str(analysis):candidate_v5.file_hash(analysis)}}))
    audit=tmp_path/"audit.json"
    audit.write_text(json.dumps({"graph_version":old.graph_version,"inputs":{"works":{"sha256":hashes["works"]},"graph":{"sha256":hashes["graph"]}}}))
    config=tmp_path/"candidate.yaml"
    config.write_text(yaml.safe_dump({"policies":candidate_v5.EXPECTED_POLICIES,
        "works":str(tmp_path/"works.jsonl"),"source_graph":str(graph_path),"source_freeze":str(freeze),
        "quality":str(QUALITY),"analysis":str(analysis),"baseline_audit":str(audit),"cache_dir":str(cache)}))
    originals={p:p.read_bytes() for p in (graph_path,tmp_path/"works.jsonl",freeze,audit,cache/"objects"/digest)}
    first=candidate_v5.build(config,tmp_path/"one",tmp_path/"report-one")
    second=candidate_v5.build(config,tmp_path/"two",tmp_path/"report-two")
    assert first["accepted_authorships"]["before"]==first["accepted_authorships"]["after"]==2
    assert first["remaining_states"]=={"resolved":2}
    for name in first["artifacts"]:
        assert first["artifacts"][name]["sha256"]==second["artifacts"][name]["sha256"]
    assert all(p.read_bytes()==body for p,body in originals.items())
    with pytest.raises(ValueError,match="unused"):
        candidate_v5.build(config,tmp_path/"one",tmp_path/"used-report")
    assert not (tmp_path/"used-report").exists()
    (cache/"objects"/digest).write_bytes(b"tampered")
    with pytest.raises(ValueError,match="hash mismatch"):
        candidate_v5.build(config,tmp_path/"bad",tmp_path/"bad-report")
    assert not (tmp_path/"bad").exists()


def test_profiles_cannot_override_raw_name_or_supply_uncorroborated_orcid_alias(tmp_path):
    a=raw_person("A1","Ann One",ONE)
    r=paper(1,["Ann One"],[a])
    old,_,_=build(tmp_path,[r])
    collision=raw_person("A2","Ann One",ONE)
    collision["author"]["observed_orcids"]=[ONE,TWO]
    # Existing A1 has selected ORCID but no independent raw crosswalk record
    # in these new sources;the new A2 must remain review rather than split/merge.
    old.nodes=[n.model_copy(update={"properties":{**n.properties,"orcid":ONE}}) if n.id=="researcher:openalex:A1" else n for n in old.nodes]
    ds,_=mentions_v5.resolve_mentions([paper(2,["Ann One"],[collision])],old)
    assert ds[0]["decision_reason"]=="raw_orcid_existing_identity_requires_crosswalk"
    assert ds[0]["canonical_researcher_id"] is None
    a=raw_person("A1","Ann One",ONE,raw="Bo Two")
    assert resolved([paper(3,["Ann One"],[a])])[0]["resolution_state"]=="ambiguous"


def test_raw_crosswalk_collision_exposes_canonical_duplicate_as_ambiguity():
    rows=[paper(1,["Ann One"],[raw_person("A1","Ann One",ONE)]),
          paper(2,["Ann One"],[raw_person("A2","Ann One",ONE)]),
          paper(3,["Ann One","Ann One"],[raw_person("A1","Ann One"),raw_person("A2","Ann One")])]
    ds=resolved(rows)
    assert [d["resolution_state"] for d in ds[-2:]]==["ambiguous","ambiguous"]
    assert all(d["decision_reason"]=="canonical_id_repeated_in_paper" for d in ds[-2:])


def test_materializer_preserves_retained_support_despite_full_byline_guard(tmp_path):
    names=["Ann One","Bo Two","Cam Three"]
    people=[raw_person(aid,n,institutions=[inst("I1"),inst("I2")]) for aid,n in zip(["A1","A2",None],names)]
    rows=[paper(1,names,people)]
    old,_,_=build(tmp_path,rows)
    assert len(old.affiliation_observations)==4
    ds=resolved(rows)
    new,guard,_=candidate_v5.construct_candidate(old,rows,ds,"release-test-v5",read_config(QUALITY))
    assert guard and len(new.affiliation_observations)==4
    assert {o.id for o in old.affiliation_observations}=={o.id for o in new.affiliation_observations}
    comparison=candidate_v5.compare(old,new,ds)
    assert comparison["retained_position_affiliation_support"]=={"positions_checked":2,"exact_organization_sets_preserved":True}
    broken=new.model_copy(update={"affiliation_observations":[]})
    with pytest.raises(ValueError,match="retained position affiliation"):
        candidate_v5.compare(old,broken,ds)


def test_wrong_provider_identifier_type_and_absent_work_identifier_abstain():
    ds=resolved([paper(1,["Ann One"],[raw_person("W1","Ann One")])])
    assert ds[0]["decision_reason"]=="provider_author_identifier_wrong_type"
    r=paper(1,["Ann One"],[raw_person("A1","Ann One")])
    r["openalex"]["id"]=None
    assert resolved([r])[0]["decision_reason"]=="work_identifier_missing_or_invalid"


def test_multiple_raw_orcid_accounts_with_compatible_names_do_not_prove_two_people():
    rows=[paper(1,["Ann One"],[raw_person("A1","Ann One",ONE)]),
          paper(2,["A. One"],[raw_person("A1","Ann One",TWO)])]
    ds=resolved(rows)
    assert all(d["resolution_state"]=="ambiguous" and d["canonical_researcher_id"] is None for d in ds)
    assert {d["decision_reason"] for d in ds}=={"multiple_paper_orcid_accounts_identity_uncertain"}


def downstream_cases():
    def conflicting(aid,name):
        a=raw_person(aid,name)
        a["author"]["observed_orcids"]=[ONE,TWO]
        return a
    return [
        ([paper(1,["Ann One"],[raw_person("A1","Ann One")]),paper(2,["A. One"],[raw_person("A1","Ann One")])],
         ["resolved","resolved"],1,2,0),
        ([paper(1,["Ann One","Ann One"],[raw_person("A1","Ann One"),raw_person("A2","Ann One")])],
         ["resolved","resolved"],2,2,1),
        ([paper(1,["Ann One"],[conflicting("A1","Ann One")])],
         ["ambiguous"],0,0,0),
        ([paper(1,["Ann One"],[raw_person("A1","Ann One",ONE)]),paper(2,["A. One"],[raw_person("A2","Ann One",ONE)])],
         ["resolved","resolved"],1,2,0),
        ([paper(1,["Ann One"],[raw_person("A1","Ann One")])],
         ["resolved"],1,1,0),
        ([paper(1,["Ann One","Bo Two"],[raw_person("A1","Bo Two"),raw_person("A2","Ann One")])],
         ["ambiguous","ambiguous"],0,0,0),
        ([paper(1,["Ann One","Bo Two","Cam Three","Dan Four"],[raw_person("A1","Ann One"),raw_person("A1","Bo Two"),raw_person("A3","Cam Three"),raw_person("A4","Dan Four")])],
         ["ambiguous","ambiguous","resolved","resolved"],2,2,1),
        ([paper(1,["Ann One","Bo Two","Cam Three"],[conflicting("A1","Ann One"),raw_person("A2","Bo Two"),raw_person("A3","Cam Three")])],
         ["ambiguous","resolved","resolved"],2,2,1),
    ]


@pytest.mark.parametrize("rows,states,researchers,authored,coauthored",downstream_cases(),ids=["name_forms","homonyms","conflicting_orcids","corroborated_ids","no_orcid","wrong_alignment","duplicate_positions","one_ambiguous"])
def test_resolution_state_has_exact_downstream_implications(tmp_path,rows,states,researchers,authored,coauthored):
    old,_,_=build(tmp_path,rows)
    ds,_=mentions_v5.resolve_mentions(rows,old)
    assert [d["resolution_state"] for d in ds]==states
    new,_,_=candidate_v5.construct_candidate(old,rows,ds,"release-test-v5",read_config(QUALITY))
    assert sum(n.label=="Researcher" for n in new.nodes)==researchers
    assert len(edges(new,"AUTHORED"))==authored
    assert len(edges(new,"COAUTHORED_WITH"))==coauthored
    assert not new.affiliation_observations
    assert not edges(new,"AFFILIATED_WITH")
    assert not edges(new,"COLLABORATED_WITH")
    assert validate_graph(new,require_derived=True)==[]
