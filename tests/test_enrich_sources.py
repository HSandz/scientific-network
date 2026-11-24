import json

import httpx

from scientific_network.enrich.sources import Fetcher, RawStore, fetch_org_wikidata, parse_org_bindings, ror_id


def binding(**fields):
    return {k: {"type": "literal", "value": v} for k, v in fields.items()}


PAYLOAD = {"results": {"bindings": [binding(
    ror="047rhhm47", item="http://www.wikidata.org/entity/Q332498", itemLabel="Brigham Young University",
    enwiki="https://en.wikipedia.org/wiki/Brigham_Young_University", countryLabel="United States", oa="I100005738",
    typeLabel="private university", parent="http://www.wikidata.org/entity/Q1", parentLabel="Parent Org", prop="P749")]}}


def make_fetcher(tmp_path, calls):
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(dict(request.url.params))
        assert "coursework" in request.headers["user-agent"] and "@" not in request.headers["user-agent"]
        return httpx.Response(200, json=PAYLOAD)
    store = RawStore(tmp_path / "raw", tmp_path / "manifest.jsonl")
    return Fetcher(store, min_interval=0, transport=httpx.MockTransport(handler), sleep=lambda s: None)


def test_ror_id_accepts_url_and_bare_id():
    assert ror_id("https://ror.org/047rhhm47") == "047rhhm47"
    assert ror_id("047rhhm47") == "047rhhm47"
    assert ror_id(None) is None and ror_id("not a ror") is None


def test_parse_bindings():
    types = {"results": {"bindings": [binding(item="http://www.wikidata.org/entity/Q332498", typeLabel="private university"),
                                      binding(item="http://www.wikidata.org/entity/Q332498", typeLabel="university")]}}
    parents = {"results": {"bindings": [binding(item="http://www.wikidata.org/entity/Q332498", parent="http://www.wikidata.org/entity/Q1",
                                                parentLabel="Parent Org", prop="P749")]}}
    row = parse_org_bindings(PAYLOAD, types, parents)[0]
    assert row["qid"] == "Q332498" and row["parents"] == [{"qid": "Q1", "label": "Parent Org", "property": "P749"}]
    assert row["types"] == ["private university", "university"]


def test_fetch_matches_by_ror_only_and_caches_immutably(tmp_path):
    calls = []
    fetcher = make_fetcher(tmp_path, calls)
    orgs = [{"id": "organization:I100005738", "ror": "https://ror.org/047rhhm47"},
            {"id": "organization:I1", "ror": None, "name": "Brigham Young University"}]
    result = fetch_org_wikidata(fetcher, orgs)
    assert list(result["matches"]) == ["organization:I100005738"]  # the nameless-ROR org is not name-matched
    assert result["orgs_with_ror"] == 1 and len(calls) == 3  # core, types, parents
    again = fetch_org_wikidata(make_fetcher(tmp_path, calls), orgs)
    assert len(calls) == 3 and again["matches"].keys() == result["matches"].keys()  # served from the immutable store
    manifest = [json.loads(line) for line in (tmp_path / "manifest.jsonl").read_text().splitlines()]
    assert len(manifest) == 3 and len(manifest[0]["sha256"]) == 64 and manifest[0]["retrieved_at"]


def test_two_qids_for_one_ror_is_a_conflict_not_a_match(tmp_path):
    payload = {"results": {"bindings": PAYLOAD["results"]["bindings"] + [binding(
        ror="047rhhm47", item="http://www.wikidata.org/entity/Q999", itemLabel="Other")]}}
    store = RawStore(tmp_path / "raw", tmp_path / "m.jsonl")
    fetcher = Fetcher(store, min_interval=0, transport=httpx.MockTransport(lambda r: httpx.Response(200, json=payload)),
                      sleep=lambda s: None)
    result = fetch_org_wikidata(fetcher, [{"id": "organization:I1", "ror": "047rhhm47"}])
    assert result["matches"] == {} and result["conflicts"][0]["qids"] == ["Q332498", "Q999"]


def test_infobox_parsing_strips_markup_and_nested_templates():
    from scientific_network.enrich.sources import parse_infobox
    text = ("{{Infobox university\n| name = Example [[University]]\n| established = {{start date|1875|1|1}}\n"
            "| type = [[Private university|Private]]<ref>x</ref>\n| website = {{URL|example.edu}}\n}}\nLead text.")
    box = parse_infobox(text)
    assert box["template"] == "infobox university"
    assert box["fields"]["name"] == "Example University"
    assert box["fields"]["type"] == "Private"
    assert box["fields"]["established"] == "1875"
    assert parse_infobox("No infobox here.") == {}


def test_wikipedia_fetch_records_revision_and_resolves_redirects(tmp_path):
    from scientific_network.enrich.sources import fetch_wikipedia
    lead = {"query": {"redirects": [{"from": "BYU", "to": "Brigham Young University"}], "pages": [
        {"pageid": 7, "title": "Brigham Young University", "extract": "BYU is a university.",
         "revisions": [{"revid": 123, "timestamp": "2026-01-01T00:00:00Z"}], "pageprops": {"wikibase_item": "Q332498"}},
        {"title": "Nope", "missing": True}]}}
    wikitext = {"query": {"pages": [{"pageid": 7, "revisions": [{"slots": {"main": {"content": "{{Infobox university|name=BYU}}"}}}]}]}}

    def handler(request):
        return httpx.Response(200, json=lead if "extracts" in request.url.params.get("prop", "") else wikitext)
    store = RawStore(tmp_path / "raw", tmp_path / "m.jsonl")
    fetcher = Fetcher(store, min_interval=0, transport=httpx.MockTransport(handler), sleep=lambda s: None)
    pages = fetch_wikipedia(fetcher, ["BYU", "Nope"])
    assert pages["BYU"]["revision_id"] == 123 and pages["BYU"]["wikibase_item"] == "Q332498"
    assert pages["Brigham Young University"]["infobox"]["fields"]["name"] == "BYU"
    assert "Nope" not in pages and len(pages["BYU"]["lead_sha256"]) == 64


def test_acquire_organization_sources_end_to_end_offline(tmp_path):
    from scientific_network.enrich.sources import acquire_organization_sources
    graph = {"nodes": [
        {"id": "organization:I100005738", "label": "Organization", "name": "Brigham Young University",
         "properties": {"ror": "https://ror.org/047rhhm47", "openalex_id": "I100005738", "sector": "academia"}},
        {"id": "organization:I2", "label": "Organization", "name": "No ROR Lab", "properties": {"openalex_id": "I2"}},
        {"id": "paper:x", "label": "Paper", "name": "p", "properties": {}}], "edges": []}
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps(graph))
    works = tmp_path / "works.jsonl"
    works.write_text(json.dumps({"openalex": {"abstract": "text"}}) + "\n" + json.dumps({"openalex": None}) + "\n")
    lead = {"query": {"pages": [{"pageid": 7, "title": "Brigham Young University", "extract": "BYU is a university.",
                                 "revisions": [{"revid": 5, "timestamp": "2026-01-01T00:00:00Z"}], "pageprops": {}}]}}
    wikitext = {"query": {"pages": [{"pageid": 7, "revisions": [{"slots": {"main": {"content": "{{Infobox university|name=BYU}}"}}}]}]}}

    def handler(request):
        params = request.url.params
        if "sparql" in str(request.url):
            return httpx.Response(200, json=PAYLOAD)
        return httpx.Response(200, json=lead if "extracts" in params.get("prop", "") else wikitext)
    report = acquire_organization_sources(graph_path, works, tmp_path / "raw", tmp_path / "raw" / "m.jsonl", tmp_path / "out",
                                          tmp_path / "sources.json", min_interval=0, transport=httpx.MockTransport(handler))
    org = report["sources"]["wikidata_organizations"]
    assert org["organizations"] == 2 and org["with_ror"] == 1 and org["matched_by_ror"] == 1
    assert org["openalex_id_agrees"] == 1 and org["openalex_id_disagrees"] == 0
    assert report["sources"]["openalex_abstracts"] == {**report["sources"]["openalex_abstracts"], "papers": 2, "with_abstract": 1, "title_only": 1}
    assert report["sources"]["wikipedia_organization_pages"]["orgs_linked"] == 1
    assert report["fetches"]["rows"] == 5


def test_truncated_json_is_retried_not_stored(tmp_path):
    responses = [httpx.Response(200, content=b'{"a": "unterminated'), httpx.Response(200, json={"a": 1})]
    store = RawStore(tmp_path / "raw", tmp_path / "m.jsonl")
    fetcher = Fetcher(store, min_interval=0, transport=httpx.MockTransport(lambda r: responses.pop(0)), sleep=lambda s: None)
    payload, row = fetcher.get("wikipedia_lead", "https://example.org/api", {"x": "1"})
    assert payload == {"a": 1} and len(row["sha256"]) == 64
    assert len((tmp_path / "m.jsonl").read_text().splitlines()) == 1


def test_abstract_counts_survive_unicode_line_separators(tmp_path):
    from scientific_network.enrich.sources import abstract_counts
    works = tmp_path / "w.jsonl"
    row = {"openalex": {"abstract": "line one line two"}}
    works.write_text(json.dumps(row, ensure_ascii=False) + "\n" + json.dumps({"openalex": None}) + "\n", encoding="utf-8")
    assert abstract_counts(works) == {"papers": 2, "with_abstract": 1, "title_only": 1}
