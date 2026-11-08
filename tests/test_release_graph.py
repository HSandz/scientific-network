"""Release graph builder (D040 Phase 3) on invented works; never reports project results."""

import json
from pathlib import Path

import pytest
import yaml

from scientific_network.cli import main
from scientific_network.contracts import GraphArtifact, Relation
from scientific_network.resolve import release

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/release-v1.yaml"
TAXONOMY = ROOT / "configs/topics.yaml"
QUALITY = ROOT / "configs/quality-release-v1.yaml"
ABSTRACT = "We study a graph neural network for planning tasks."


def inst(ident, kind="education"):
    return {"id": f"https://openalex.org/{ident}", "display_name": f"Institute {ident}", "ror": f"https://ror.org/{ident.lower()}",
            "country_code": "US", "type": kind}


def authorship(aid, name, institutions=(), orcid=None, raw=None, strings=None):
    return {"author": {"id": f"https://openalex.org/{aid}" if aid else None, "display_name": name, "orcid": orcid},
            "raw_author_name": raw or name, "institutions": list(institutions),
            "raw_affiliation_strings": strings if strings is not None else [f"Dept, Institute {i['id']}" for i in institutions],
            "affiliations": [{"raw_affiliation_string": f"Dept, Institute {i['id']}", "institution_ids": [i["id"]]} for i in institutions]}


def row(n, names, authorships, *, refs=(), status="matched", reasons=(), abstract=ABSTRACT, venue="venue:aaai",
        year=2021, work_id=None, alternates=()):
    paper_id = f"paper:{venue.split(':')[1]}:{year}:{n}"
    base = {"paper_id": paper_id, "venue_id": venue, "year": year, "track": "main", "doi": f"10.1609/aaai.v35i1.{n}",
            "roster": {"title": f"Study number {n}", "authors": list(names), "official_url": f"https://ojs.example.org/article/view/{n}",
                       "pdf_url": f"https://ojs.example.org/article/view/{n}/1", "official_record_id": str(n),
                       "issue_series": "Vol. 35 No. 1", "source_url": "https://ojs.example.org/issue/view/1",
                       "source_sha256": "a" * 64, "retrieved_at": "2026-11-06T00:00:00+00:00", "source_locator": f"a[href='{n}']"},
            "match": {"status": status, "reasons": list(reasons), "flags": []}, "openalex": None}
    if status == "matched":
        base["openalex"] = {
            "id": f"https://openalex.org/{work_id or 'W' + str(n)}", "doi": "x", "title": f"Study number {n}",
            "publication_year": year, "authorships": authorships, "referenced_works": [f"https://openalex.org/{r}" for r in refs],
            "abstract": abstract, "alternates": [{"id": f"https://openalex.org/{a}"} for a in alternates],
            "source": {"request_id": "req" + str(n), "raw_sha256": "b" * 64, "retrieved_at": "2026-11-08T00:00:00+00:00",
                       "locator": "results[0]"}}
    return base


def build(tmp_path, rows, *, initials=False, name="graph"):
    works = tmp_path / "works.jsonl"
    works.write_text("".join(json.dumps(r) + "\n" for r in rows))
    config = yaml.safe_load(CONFIG.read_text())
    config["matching"]["initials_tolerant"] = initials
    config_path = tmp_path / "release.yaml"
    config_path.write_text(yaml.safe_dump(config))
    out = tmp_path / name
    summary = release.build_release_graph(works, config_path, TAXONOMY, QUALITY, out, tmp_path / f"{name}-summary.json")
    graph = GraphArtifact.model_validate_json((out / "graph.json").read_text())
    queue = [json.loads(l) for l in (out / "review-queue.jsonl").read_text().splitlines() if l.strip()]
    return graph, summary, queue


def edges(graph, relation):
    return [e for e in graph.edges if e.relation == relation]


def rich_rows():
    i1, i2 = inst("I1"), inst("I2")
    a1 = lambda: authorship("A1", "Ann One", [i1], orcid="https://orcid.org/0000-0001-0000-0001")
    a2 = lambda: authorship("A2", "Bo Two", [i2])
    return [
        row(1, ["Ann One", "Bo Two"], [a1(), a2()]),
        row(2, ["Ann One", "Bo Two"], [a1(), a2()], refs=["W1", "W999", "W2"]),                 # out of scope + self-loop
        row(3, ["Ann One", "Bo Two"], [a1(), a2()], refs=["W1", "W1", "W2"], venue="venue:ijcai", year=2022),
    ]


def test_all_ten_relations_are_derived_from_accepted_evidence_and_validate(tmp_path):
    graph, summary, queue = build(tmp_path, rich_rows())
    assert {e.relation for e in graph.edges} == set(Relation)
    assert graph.is_synthetic is False and graph.graph_version.startswith("release-") and len(graph.graph_version) == len("release-") + 12
    assert len(edges(graph, Relation.PUBLISHED_IN)) == 3 and len(edges(graph, Relation.AUTHORED)) == 6
    assert queue == [] and summary["review_queue"] == {}
    assert summary["size_gates"]["all_relation_types_present"] == {"status": "passed", "observed": 10, "required": 10}
    assert summary["size_gates"]["resolved_core_researchers"]["status"] == "failed"
    paper = next(n for n in graph.nodes if n.id == "paper:aaai:2021:1")
    assert paper.properties["doi"] == "10.1609/aaai.v35i1.1" and paper.properties["openalex_id"] == "W1"
    assert paper.properties["official_author_count"] == 2 and "abstract" not in paper.properties
    researcher = next(n for n in graph.nodes if n.id == "researcher:openalex:A1")
    assert researcher.properties == {"resolution_status": "resolved", "identity_method": "openalex_author_id",
                                     "openalex_id": "A1", "orcid": "0000-0001-0000-0001"}
    org = next(n for n in graph.nodes if n.id == "organization:I1")
    assert org.properties["sector"] == "academia" and org.properties["ror"] == "https://ror.org/i1" and org.properties["country_code"] == "US"
    authored = next(e for e in graph.edges if e.relation == Relation.AUTHORED and e.target_id == "paper:aaai:2021:1" and e.source_id.endswith("A2"))
    assert authored.properties == {"byline_position": 2, "roster_name": "Bo Two", "name_match": "exact"}


def test_graph_is_deterministic_and_the_output_directory_must_be_empty(tmp_path):
    first, summary, _ = build(tmp_path, rich_rows(), name="one")
    second, summary_two, _ = build(tmp_path, rich_rows(), name="two")
    assert first.graph_version == second.graph_version
    assert [e.edge_id for e in first.edges] == [e.edge_id for e in second.edges]
    works = tmp_path / "works.jsonl"
    with pytest.raises(ValueError, match="not empty"):
        release.build_release_graph(works, CONFIG, TAXONOMY, QUALITY, tmp_path / "one", tmp_path / "again.json")


def test_citations_keep_only_matched_in_scope_targets_without_self_loops_or_duplicates(tmp_path):
    graph, summary, _ = build(tmp_path, rich_rows())
    cites = {(e.source_id, e.target_id) for e in edges(graph, Relation.CITES)}
    assert cites == {("paper:aaai:2021:2", "paper:aaai:2021:1"), ("paper:ijcai:2022:3", "paper:aaai:2021:1"),
                     ("paper:ijcai:2022:3", "paper:aaai:2021:2")}
    assert summary["citations"] == {"reference_targets": 5, "reference_targets_out_of_scope": 1,
                                    "reference_targets_ambiguous": 0, "reference_targets_self": 1}


def test_a_reference_to_an_alternate_record_resolves_and_an_ambiguous_target_is_dropped(tmp_path):
    rows = [row(1, ["Ann One"], [authorship("A1", "Ann One")], work_id="W1", alternates=["W100"]),
            row(2, ["Bo Two"], [authorship("A2", "Bo Two")], refs=["W100"]),
            row(3, ["Cy Three"], [authorship("A3", "Cy Three")], refs=["W5"], work_id="W5"),
            row(4, ["Di Four"], [authorship("A4", "Di Four")], refs=["W5"], work_id="W5")]      # W5 claimed by two papers
    graph, summary, _ = build(tmp_path, rows + [row(5, ["Ed Five"], [authorship("A5", "Ed Five")], refs=["W5"])])
    cites = {(e.source_id, e.target_id) for e in edges(graph, Relation.CITES)}
    assert cites == {("paper:aaai:2021:2", "paper:aaai:2021:1")}
    assert summary["citations"]["reference_targets_ambiguous"] == 3


def test_one_incompatible_position_is_withheld_but_the_rest_of_the_paper_stays(tmp_path):
    rows = [row(1, ["Ann One", "Bo Two"], [authorship("A1", "Ann One"), authorship("A9", "Zed Different")])]
    graph, summary, queue = build(tmp_path, rows)
    assert [e.source_id for e in edges(graph, Relation.AUTHORED)] == ["researcher:openalex:A1"]
    assert [q["kind"] for q in queue] == ["author_position_withheld"] and queue[0]["position"] == 2 and queue[0]["reason"] == "name_incompatible"
    assert summary["coverage"]["author_positions_withheld"] == 1 and summary["coverage"]["author_positions_accepted"] == 1
    assert "unresolved_author_reason" not in next(n for n in graph.nodes if n.id == "paper:aaai:2021:1").properties


def test_two_incompatible_positions_withhold_the_whole_paper(tmp_path):
    rows = [row(1, ["Ann One", "Bo Two", "Cy Three"],
                [authorship("A1", "Ann One"), authorship("A8", "Wrong Person"), authorship("A9", "Other Wrong")])]
    graph, summary, queue = build(tmp_path, rows)
    assert edges(graph, Relation.AUTHORED) == []
    paper = next(n for n in graph.nodes if n.id == "paper:aaai:2021:1")
    assert paper.properties["unresolved_author_reason"] == "authorships_withheld:multiple_incompatible_positions"
    assert len(edges(graph, Relation.PUBLISHED_IN)) == 1
    assert queue[0]["kind"] == "authorships_withheld_for_paper" and len(queue[0]["positions"]) == 3
    assert queue[0]["positions"] == [
        {"position": 1, "reason": "multiple_incompatible_positions", "roster_name": "Ann One"},
        {"position": 2, "reason": "name_incompatible", "roster_name": "Bo Two"},
        {"position": 3, "reason": "name_incompatible", "roster_name": "Cy Three"},
    ]
    assert summary["coverage"]["author_positions_withheld_by_reason"] == {
        "multiple_incompatible_positions": 1, "name_incompatible": 2}


def test_the_same_author_id_twice_in_a_paper_withholds_all_its_authorships(tmp_path):
    rows = [row(1, ["Ann One", "A. One"], [authorship("A1", "Ann One"), authorship("A1", "Ann One", raw="Ann One")])]
    graph, _, queue = build(tmp_path, rows, initials=True)
    assert edges(graph, Relation.AUTHORED) == []
    assert queue[0]["reason"] == "author_id_repeated_in_paper"
    assert queue[0]["positions"] == [
        {"position": 1, "reason": "author_id_repeated_in_paper", "roster_name": "Ann One"},
        {"position": 2, "reason": "author_id_repeated_in_paper", "roster_name": "A. One"},
    ]


def test_a_missing_author_id_is_withheld_and_an_id_with_conflicting_orcids_is_withheld_everywhere(tmp_path):
    rows = [row(1, ["Ann One", "Bo Two"], [authorship("A1", "Ann One", orcid="https://orcid.org/0000-0001-0000-0001"),
                                         authorship(None, "Bo Two")]),
            row(2, ["Ann One"], [authorship("A1", "Ann One", orcid="https://orcid.org/0000-0002-0000-0002")])]
    graph, _, queue = build(tmp_path, rows)
    assert edges(graph, Relation.AUTHORED) == []
    # names fit, so none of this suggests a misaligned byline: each position is withheld on its own
    assert sorted(q["kind"] for q in queue) == ["author_id_conflicting_orcids"] + ["author_position_withheld"] * 3
    assert sorted(q["reason"] for q in queue if q["kind"] == "author_position_withheld") == [
        "author_id_conflicting_orcids", "author_id_conflicting_orcids", "no_author_id"]
    assert not any(n.id == "researcher:openalex:A1" for n in graph.nodes)


def test_names_must_match_by_tokens_and_initials_only_when_allowed(tmp_path):
    rows = [row(1, ["Ann One", "B. Two"], [authorship("A1", "One, Ann", raw="Ann One"), authorship("A2", "Bo Two", raw="Bo Two")])]
    strict, summary, queue = build(tmp_path, rows, name="strict")
    assert [e.source_id for e in edges(strict, Relation.AUTHORED)] == ["researcher:openalex:A1"]
    assert queue[0]["roster_name"] == "B. Two" and summary["name_matching"] == {"initials_tolerant": False, "exact": 1, "initials": 0}
    tolerant, summary, queue = build(tmp_path, rows, initials=True, name="tolerant")
    assert len(edges(tolerant, Relation.AUTHORED)) == 2 and queue == []
    assert summary["name_matching"] == {"initials_tolerant": True, "exact": 1, "initials": 1}
    assert sorted(e.properties["name_match"] for e in edges(tolerant, Relation.AUTHORED)) == ["exact", "initials"]


@pytest.mark.parametrize("left,right,expected", [
    ("A. Aloisio", "Alessandro Aloisio", True), ("J. Smith", "John Michael Smith", True), ("Smith J.", "John Smith", True),
    ("B. Two", "Carl Two", False), ("A. Aloisio", "Alessandro Rossi", False), ("A. B.", "Alice Brown", False),
    ("Ann One", "Ann One", True), ("", "Ann One", False),
])
def test_initials_tolerant_comparison(left, right, expected):
    assert release.names_initials_compatible(left, right) is expected


def test_each_author_keeps_only_their_own_institutions_and_unknown_institutions_create_no_node(tmp_path):
    i1, i2 = inst("I1"), inst("I2", "company")
    no_id = {"id": None, "display_name": "Unlinked Lab", "type": "company"}
    rows = [row(1, ["Ann One", "Bo Two"], [authorship("A1", "Ann One", [i1]), authorship("A2", "Bo Two", [i2, no_id])])]
    graph, summary, _ = build(tmp_path, rows)
    pairs = {(e.source_id, e.target_id) for e in edges(graph, Relation.AFFILIATED_WITH)}
    assert pairs == {("researcher:openalex:A1", "organization:I1"), ("researcher:openalex:A2", "organization:I2")}
    assert {n.id for n in graph.nodes if n.label == "Organization"} == {"organization:I1", "organization:I2"}
    assert next(n for n in graph.nodes if n.id == "organization:I2").properties["sector"] == "industry"
    assert len(graph.affiliation_observations) == 2
    collaborated = edges(graph, Relation.COLLABORATED_WITH)
    assert len(collaborated) == 1 and collaborated[0].properties["support_count"] == 1
    affiliation = edges(graph, Relation.AFFILIATED_WITH)[0]
    assert affiliation.properties["raw_affiliation_strings"] and affiliation.properties["support_paper_count"] == 1


def test_a_sole_dual_affiliated_author_creates_no_organization_collaboration(tmp_path):
    rows = [row(1, ["Ann One"], [authorship("A1", "Ann One", [inst("I1"), inst("I2")])])]
    graph, _, _ = build(tmp_path, rows)
    assert len(edges(graph, Relation.AFFILIATED_WITH)) == 2 and edges(graph, Relation.COLLABORATED_WITH) == []


def test_paper_level_copying_of_institutions_goes_to_review(tmp_path):
    both = [inst("I1"), inst("I2")]
    names = ["Ann One", "Bo Two", "Cy Three"]
    rows = [row(1, names, [authorship(f"A{i}", n, both) for i, n in enumerate(names, 1)])]
    graph, summary, queue = build(tmp_path, rows)
    assert len(edges(graph, Relation.AUTHORED)) == 3 and edges(graph, Relation.AFFILIATED_WITH) == []
    assert graph.affiliation_observations == [] and [q["kind"] for q in queue] == ["paper_level_affiliation_copy"]
    assert summary["review_queue"] == {"paper_level_affiliation_copy": 1}
    # two authors, or one shared institution, is not the copying pattern
    two = [row(1, names[:2], [authorship(f"A{i}", n, both) for i, n in enumerate(names[:2], 1)])]
    assert len(edges(build(tmp_path, two, name="two")[0], Relation.AFFILIATED_WITH)) == 4
    one = [row(1, names, [authorship(f"A{i}", n, [inst("I1")]) for i, n in enumerate(names, 1)])]
    assert len(edges(build(tmp_path, one, name="one")[0], Relation.AFFILIATED_WITH)) == 3


def test_unmatched_works_keep_their_venue_edge_and_an_unresolved_reason(tmp_path):
    rows = [row(1, ["Ann One"], [], status="review", reasons=["title_mismatch"]),
            row(2, ["Bo Two"], [], status="not_found", reasons=["no_openalex_work_for_doi"]),
            row(3, ["Cy Three"], [authorship("A3", "Cy Three")])]
    graph, summary, queue = build(tmp_path, rows)
    assert len(edges(graph, Relation.PUBLISHED_IN)) == 3 and len(edges(graph, Relation.AUTHORED)) == 1
    reasons = {n.id: n.properties.get("unresolved_author_reason") for n in graph.nodes if n.label == "Paper"}
    assert reasons == {"paper:aaai:2021:1": "work_review:title_mismatch", "paper:aaai:2021:2": "work_not_found:no_openalex_work_for_doi",
                       "paper:aaai:2021:3": None}
    assert summary["review_queue"] == {"work_not_accepted": 2} and summary["papers"] == 3
    assert all(n.properties["is_core"] is True for n in graph.nodes if n.label == "Paper")


def test_topics_use_title_and_abstract_with_literal_excerpts_and_title_only_is_flagged(tmp_path):
    rows = [row(1, ["Ann One"], [authorship("A1", "Ann One")]),
            row(2, ["Bo Two"], [authorship("A2", "Bo Two")], abstract=None),
            row(3, ["Cy Three"], [authorship("A3", "Cy Three")], abstract="Nothing here matches any phrase.")]
    graph, summary, _ = build(tmp_path, rows)
    topics = edges(graph, Relation.HAS_TOPIC)
    assert [(e.source_id, e.target_id) for e in topics] == [("paper:aaai:2021:1", "topic:graph-ml")]
    evidence = next(item for item in graph.evidence if item.id == topics[0].evidence_ids[0])
    assert evidence.excerpt == "graph neural network" and evidence.kind == "inferred_topic"
    flags = {n.id: n.properties["topic_text"] for n in graph.nodes if n.label == "Paper"}
    assert flags == {"paper:aaai:2021:1": "title_and_abstract", "paper:aaai:2021:2": "title_only", "paper:aaai:2021:3": "title_and_abstract"}
    assert summary["coverage"]["papers_topic_labeled"] == 1 and summary["coverage"]["papers_with_abstract"] == 2
    assert summary["topic_decisions"] == {"abstain_no_supported_phrase": 2, "phrase_baseline_unvalidated": 1}


def test_evidence_is_resolvable_and_shared_per_work(tmp_path):
    graph, _, _ = build(tmp_path, rich_rows())
    by_id = {item.id: item for item in graph.evidence}
    authored = edges(graph, Relation.AUTHORED)
    shared = {e.evidence_ids[0] for e in authored if e.target_id == "paper:aaai:2021:1"}
    assert len(shared) == 1
    work = by_id[shared.pop()]
    assert str(work.source_url) == "https://openalex.org/W1" and work.raw_sha256 == "b" * 64 and "req1#results[0]" in work.source_locator
    venue = edges(graph, Relation.PUBLISHED_IN)[0]
    roster = by_id[venue.evidence_ids[0]]
    assert str(roster.source_url).startswith("https://ojs.example.org/") and roster.raw_sha256 == "a" * 64


def test_command_line_builds_into_the_configured_directories(tmp_path, monkeypatch, capsys):
    works = tmp_path / "works.jsonl"
    works.write_text("".join(json.dumps(r) + "\n" for r in rich_rows()))
    config = yaml.safe_load(CONFIG.read_text())
    config["configs"]["quality"] = str(QUALITY)
    config["paths"].update(works=str(works), graph_v1_dir=str(tmp_path / "g"), graph_summary=str(tmp_path / "summary.json"))
    path = tmp_path / "release.yaml"
    path.write_text(yaml.safe_dump(config))
    assert main(["release-graph", "--config", str(path)]) == 0
    assert (tmp_path / "g/graph.json").is_file() and (tmp_path / "g/review-queue.jsonl").is_file() and (tmp_path / "summary.json").is_file()
    assert main(["validate", "--input", str(tmp_path / "g/graph.json"), "--config", str(QUALITY)]) in (0, 1)


def test_authors_without_an_openalex_id_are_withheld_singly_and_do_not_sink_the_paper(tmp_path):
    names = ["Ann One", "Bo Two", "Cy Three"]
    rows = [row(1, names, [authorship("A1", "Ann One"), authorship(None, "Bo Two"), authorship(None, "Cy Three")])]
    graph, summary, queue = build(tmp_path, rows)
    assert [e.source_id for e in edges(graph, Relation.AUTHORED)] == ["researcher:openalex:A1"]
    assert [q["reason"] for q in queue] == ["no_author_id", "no_author_id"]
    assert summary["coverage"]["author_positions_withheld_by_reason"] == {"no_author_id": 2}
    assert summary["coverage"]["papers_all_authorships_withheld"] == 0
    assert "unresolved_author_reason" not in next(n for n in graph.nodes if n.id == "paper:aaai:2021:1").properties
    # a missing ID together with a name that does not fit still counts as one incompatible name only
    mixed = [row(2, names, [authorship("A1", "Ann One"), authorship(None, "Bo Two"), authorship("A3", "Someone Else")])]
    graph, _, queue = build(tmp_path, mixed, name="mixed")
    assert len(edges(graph, Relation.AUTHORED)) == 1 and sorted(q["reason"] for q in queue) == ["name_incompatible", "no_author_id"]
