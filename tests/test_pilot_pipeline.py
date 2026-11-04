import pytest
import httpx
import xml.etree.ElementTree as ET
import json

from scientific_network.preprocess.tei import parse_header
from scientific_network.resolve.pilot import align_header, match_institution, orcid_support
from scientific_network.graph.materialize import materialize
from scientific_network.nlp.baseline import predict
from scientific_network.collect.storage import read_config
from scientific_network.graph.validate import validate_graph
from pathlib import Path


def test_grobid_explicitly_negotiates_tei_instead_of_default_bibtex():
    from scientific_network.preprocess.extract import request_header

    tei = b'<TEI xmlns="http://www.tei-c.org/ns/1.0"/>'

    def handler(request):
        assert request.headers["Accept"] == "application/xml"
        assert b'consolidateHeader' in request.content
        return httpx.Response(200, content=tei)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        assert request_header(client, "http://localhost:8070", "processHeaderDocument", b"%PDF") == tei


@pytest.mark.parametrize("body,error", [(b"@article{example}", ET.ParseError), (b"<html/>", ValueError)])
def test_grobid_successful_non_tei_response_is_rejected(body, error):
    from scientific_network.preprocess.extract import request_header

    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, content=body))) as client:
        with pytest.raises(error):
            request_header(client, "http://localhost:8070", "processHeaderDocument", b"%PDF")


def test_import_report_collision_is_rejected_before_database_access(tmp_path, monkeypatch):
    from scientific_network.graph.load import build, GraphDatabase

    def unexpected_connection(*args, **kwargs):
        raise AssertionError("database must not be accessed before checking report path")

    monkeypatch.setattr(GraphDatabase, "driver", unexpected_connection)
    graph_path = tmp_path / "graph.json"
    graph_path.write_text("protected input")
    config_path = tmp_path / "quality.yaml"
    config_path.write_text("protected config")
    report_path = tmp_path / "report.json"
    report_path.write_text("previous report")
    for output in (graph_path, config_path, report_path):
        with pytest.raises(ValueError, match="choose a new report path"):
            build(graph_path, output, config_path)
    assert graph_path.read_text() == "protected input"
    assert config_path.read_text() == "protected config"
    assert report_path.read_text() == "previous report"


def test_tei_affiliations_stay_with_printed_author_instead_of_cross_product():
    body = b'''<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader><fileDesc><sourceDesc><biblStruct><analytic>
    <author><persName><forename>Alice</forename><surname>Smith</surname></persName><affiliation><orgName type="institution">University X</orgName></affiliation><affiliation><orgName type="institution">Lab Y</orgName></affiliation></author>
    <author><persName><forename>Bob</forename><surname>Jones</surname></persName></author>
    </analytic></biblStruct></sourceDesc></fileDesc></teiHeader></TEI>'''
    authors = parse_header(body)
    assert len(authors[0]["affiliations"]) == 2
    assert authors[1]["affiliations"] == []
    assert align_header("Alice Smith", authors)["name"] == "Alice Smith"
    assert align_header("Someone Else", authors) is None


def test_ambiguous_institution_name_does_not_choose_arbitrary_provider_id():
    institutions = [{"id": "I1", "display_name": "University X"}, {"id": "I2", "display_name": "University X"}]
    assert match_institution("University X", institutions) is None


def test_orcid_identifier_alone_is_not_public_publication_corroboration():
    body = b'<works xmlns="urn:test"><group><work-summary><title><title>Different publication</title></title></work-summary></group></works>'
    assert orcid_support(body, "Requested publication", set()) is None
    assert orcid_support(body, "Different publication", set()) == "public_work_title"


def test_same_name_people_stay_distinct_and_corroborated_crosswalks_accumulate(tmp_path, monkeypatch):
    from scientific_network.resolve import pilot

    source = {"url": "https://example.org/source", "sha256": "a" * 64,
              "retrieved_at": "2026-11-03T00:00:00Z"}
    records = []
    for number, (name, provider, orcid) in enumerate([
        ("Alex Lee", "A1", "0000-0000-0000-0001"),
        ("Alex Lee", "A2", "0000-0000-0000-0002"),
        ("Lee Alex", "A3", "0000-0000-0000-0001"),
    ], 1):
        records.append({"status": "acquired", "paper_id": f"paper:p{number}",
            "roster": {"year": 2023, "track": "main", "venue_id": "venue:icml",
                       "official_url": f"https://example.org/p{number}",
                       "source_url": source["url"], "source_sha256": source["sha256"],
                       "retrieved_at": source["retrieved_at"], "source_locator": f"a[href=p{number}]"},
            "official": {"title": f"Synthetic work {number}", "abstract": "", "authors": [name]},
            "official_source": source, "openalex_source": source,
            "openalex_work": {"id": f"W{number}", "authorships": [{"author": {
                "id": provider, "orcid": f"https://orcid.org/{orcid}"}}]}})

    class FakeCache:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get(self, url):
            titles = "".join(f"<group><work-summary><title><title>Synthetic work {i}</title></title></work-summary></group>" for i in range(1, 4))
            return f"<works>{titles}</works>".encode(), {**source, "url": url}

    monkeypatch.setattr(pilot, "SourceCache", FakeCache)
    records[0]["roster"]["venue_id"] = "venue:aistats"
    input_path = tmp_path / "papers.json"
    input_path.write_text(json.dumps(records))
    config_path = Path(__file__).resolve().parents[1] / "configs/corpus-extended-v2.yaml"
    pilot.resolve(input_path, tmp_path / "resolved", tmp_path / "cache", config_path)
    result = json.loads((tmp_path / "resolved/graph.json").read_text())
    assert next(n for n in result["nodes"] if n["id"] == "venue:aistats")["name"] == "AISTATS"
    people = [n for n in result["nodes"] if n["label"] == "Researcher"]
    assert len(people) == 2
    first = next(n for n in people if n["properties"]["orcid"].endswith("0001"))
    assert first["properties"]["openalex_ids"] == ["A1", "A3"]
    assert first["properties"]["name_variants"] == ["Alex Lee", "Lee Alex"]
    assert sum(e["relation"] == "AUTHORED" for e in result["edges"]) == 3


def test_derived_support_counts_and_weights_recompute_idempotently(graph):
    first = materialize(graph)
    second = materialize(first)
    assert first.model_dump() == second.model_dump()
    organization = next(e for e in first.edges if e.relation == "CONTRIBUTES_TO_TOPIC")
    assert organization.properties["support_count"] == 3


def test_fractional_coauthor_weight_uses_full_byline_despite_unresolved_authors(graph):
    paper = next(n for n in graph.nodes if n.id == "paper:p1")
    paper.properties["official_author_count"] = 4
    result = materialize(graph)
    pair = next(e for e in result.edges if e.relation == "COAUTHORED_WITH" and e.target_id == "researcher:b")
    assert pair.properties["fractional_weight"] == pytest.approx(1 / 3)


def test_unsupported_or_tampered_derivation_is_rejected(graph):
    result = materialize(graph)
    pair = next(e for e in result.edges if e.relation == "COAUTHORED_WITH")
    pair.properties["fractional_weight"] = 99.0
    assert any("fractional weight mismatch" in error for error in validate_graph(result))
    pair.properties["fractional_weight"] = 1.0
    pair.properties["support_count"] = 10
    assert any("distinct-paper count mismatch" in error for error in validate_graph(result))


def test_generic_ambiguous_words_abstain_and_real_phrase_retains_literal_span():
    taxonomy = read_config(Path(__file__).resolve().parents[1] / "configs/topics.yaml")
    assert predict("A graph of causal attention and an agent", taxonomy)[0] == []
    text = "We propose a GRAPH NEURAL NETWORK for node prediction."
    labels, _ = predict(text, taxonomy)
    assert labels[0]["topic_id"] == "topic:graph-ml"
    assert text[labels[0]["start"]:labels[0]["end"]] == labels[0]["excerpt"]


def test_too_many_topic_candidates_abstain_instead_of_arbitrary_truncation():
    taxonomy = read_config(Path(__file__).resolve().parents[1] / "configs/topics.yaml")
    labels, reason = predict("A language model for computer vision with reinforcement learning and graph neural network", taxonomy)
    assert labels == []
    assert reason == "abstain_too_many_candidate_labels"
