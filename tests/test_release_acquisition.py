"""Release OpenAlex acquisition: DOI derivation, work matching and the orchestration (offline)."""

import json
import re
from pathlib import Path

import httpx
import pytest
import yaml

from scientific_network.cli import main
from scientific_network.collect import openalex_release as release
from scientific_network.collect.storage import QuotaError, SourceError, digest

ROOT = Path(__file__).resolve().parents[1]
KEY = "test-key-not-a-real-secret"


def aaai(record="16071", series="Vol. 35 No. 1", year=2021, title="A Study of Things", authors=("Ann One", "Bo Two")):
    return {"paper_id": f"paper:aaai:{year}:{record}", "venue_id": "venue:aaai", "year": year, "track": "main",
            "status": "included", "title": title, "authors": list(authors), "official_record_id": record,
            "official_url": f"https://ojs.aaai.org/index.php/AAAI/article/view/{record}",
            "pdf_url": f"https://ojs.aaai.org/index.php/AAAI/article/view/{record}/1", "issue_series": series,
            "source_url": "https://ojs.aaai.org/index.php/AAAI/issue/view/1", "source_sha256": "a" * 64,
            "retrieved_at": "2026-11-06T00:00:00+00:00", "source_locator": "a[href]"}


def ijcai(number="7", year=2021, title="Games and Coordination", authors=("Cy Three",)):
    return {"paper_id": f"paper:ijcai:{year}:{number}", "venue_id": "venue:ijcai", "year": year, "track": "main",
            "status": "included", "title": title, "authors": list(authors), "official_record_id": number,
            "official_url": f"https://www.ijcai.org/proceedings/{year}/{number}",
            "pdf_url": f"https://www.ijcai.org/proceedings/{year}/{int(number):04d}.pdf",
            "source_url": f"https://www.ijcai.org/proceedings/{year}/", "source_sha256": "b" * 64,
            "retrieved_at": "2026-11-06T00:00:00+00:00", "source_locator": "a[href]"}


# --- DOI derivation (release plan section 7) -------------------------------------------------


def test_aaai_doi_comes_from_the_issue_series_and_the_record_id():
    assert release.derive_doi(aaai()) == "10.1609/aaai.v35i1.16071"
    assert release.derive_doi(aaai("29123", "Vol. 37 No. 12", 2023)) == "10.1609/aaai.v37i12.29123"


def test_ijcai_doi_comes_from_the_official_url():
    assert release.derive_doi(ijcai()) == "10.24963/ijcai.2021/7"
    assert release.derive_doi(ijcai("1234", 2025)) == "10.24963/ijcai.2025/1234"


@pytest.mark.parametrize("change", [
    {"issue_series": None}, {"issue_series": "Volume 35, Issue 1"}, {"issue_series": "Vol. 35 No. "},
    {"official_record_id": "abc"}, {"official_record_id": ""}, {"official_record_id": "999"},   # URL says 16071
    {"official_url": "https://ojs.aaai.org/index.php/AAAI/issue/view/385"},
    {"official_url": "https://ojs.aaai.org/index.php/AAAI/article/view/16071/15878"},
])
def test_malformed_aaai_rows_fail_instead_of_guessing(change):
    with pytest.raises(ValueError, match="cannot derive an AAAI DOI"):
        release.derive_doi({**aaai(), **change})


@pytest.mark.parametrize("change", [
    {"official_url": "https://www.ijcai.org/proceedings/2021/"}, {"official_url": "https://www.ijcai.org/proceedings/2021/x7"},
    {"official_url": "https://www.ijcai.org/proceedings/2020/7"},      # year disagrees with the row
    {"official_url": "http://www.ijcai.org/proceedings/2021/7"}, {"official_url": None},
])
def test_malformed_ijcai_rows_fail_instead_of_guessing(change):
    with pytest.raises(ValueError, match="cannot derive an IJCAI DOI"):
        release.derive_doi({**ijcai(), **change})


def test_unknown_venue_has_no_doi_rule():
    with pytest.raises(ValueError, match="no DOI rule"):
        release.derive_doi({**ijcai(), "venue_id": "venue:icml"})


# --- matching -------------------------------------------------------------------------------


def test_title_similarity_ignores_markup_case_and_punctuation_but_not_content():
    assert release.title_similarity("A Study of Things!", "a study of <i>things</i>") == 1.0
    assert 0.9 <= release.title_similarity("Learning to Plan with Graph Neural Networks", "Learning to Plan with Graph Neural Network") < 1.0
    assert release.title_similarity("Learning to Plan: A Survey", "Learning to Plan - A Survey of Methods") < 0.9
    assert release.title_similarity("Graph Neural Networks", "Distance Polymatrix Coordination Games") < 0.9
    assert release.title_similarity("", "x") == 0.0 and release.title_similarity(None, None) == 0.0


def test_abstract_is_rebuilt_from_positions_and_missing_stays_none():
    index = {"Deep": [0], "networks": [1, 6], "learn": [2], "and": [3], "plan": [4], "with": [5]}
    assert release.reconstruct_abstract(index) == "Deep networks learn and plan with networks"
    assert release.reconstruct_abstract(None) is None and release.reconstruct_abstract({}) is None


def work(row, **change):
    base = {"id": "https://openalex.org/W1", "doi": "https://doi.org/" + release.derive_doi(row), "title": row["title"],
            "publication_year": row["year"],
            "authorships": [{"author": {"id": f"https://openalex.org/A{i}", "display_name": name}, "institutions": [],
                             "raw_affiliation_strings": []} for i, name in enumerate(row["authors"])],
            "referenced_works": ["https://openalex.org/W9"], "abstract_inverted_index": {"hello": [0], "world": [1]}}
    return {**base, **change}


def test_exact_title_and_author_count_are_accepted_without_a_flag():
    row = aaai()
    result = release.evaluate_match(row, [work(row)])
    assert (result["status"], result["reasons"], result["flags"]) == ("matched", [], [])
    assert result["title_similarity"] == 1.0 and result["author_count_official"] == result["author_count_openalex"] == 2


def test_close_title_is_accepted_with_a_flag():
    row = aaai(title="Learning to Plan with Graph Neural Networks")
    result = release.evaluate_match(row, [work(row, title="Learning to Plan with Graph Neural Network")])
    assert result["status"] == "matched" and result["flags"] == ["title_similarity_below_1"]


def test_title_mismatch_goes_to_review():
    row = aaai()
    result = release.evaluate_match(row, [work(row, title="Quantum Chemistry Benchmarks")])
    assert result["status"] == "review" and result["reasons"] == ["title_mismatch"]


def test_author_count_mismatch_goes_to_review():
    row = aaai()
    short = work(row)
    short["authorships"] = short["authorships"][:1]
    result = release.evaluate_match(row, [short])
    assert result["status"] == "review" and result["reasons"] == ["author_count_mismatch"]
    assert (result["author_count_official"], result["author_count_openalex"]) == (2, 1)


def test_both_reasons_are_reported_and_a_null_title_cannot_match():
    row = aaai()
    both = work(row, title=None)
    both["authorships"] = []
    assert release.evaluate_match(row, [both])["reasons"] == ["title_mismatch", "author_count_mismatch"]


def test_no_work_is_not_found_and_two_works_for_one_doi_are_ambiguous():
    row = aaai()
    assert release.evaluate_match(row, [])["status"] == "not_found"
    ambiguous = release.evaluate_match(row, [work(row), work(row, id="https://openalex.org/W2")])
    assert ambiguous["status"] == "review" and ambiguous["reasons"] == ["duplicate_doi_works"]


# --- scope and orchestration ------------------------------------------------------------------


def make_release(tmp_path: Path, rows: list[dict], **overrides) -> Path:
    manifest = tmp_path / "roster.jsonl"
    manifest.write_text("".join(json.dumps(r) + "\n" for r in rows) + json.dumps({**aaai("1"), "status": "excluded"}) + "\n")
    config = yaml.safe_load((ROOT / "configs/release-v1.yaml").read_text())
    counts: dict = {}
    for row in rows:
        counts.setdefault(row["venue_id"], {}).setdefault(row["year"], 0)
        counts[row["venue_id"]][row["year"]] += 1
    config["scope"].update(venues=sorted(counts), years=sorted({r["year"] for r in rows}), expected_papers=len(rows),
                           expected_papers_by_venue_year=counts)
    config["roster"].update(manifest=str(manifest), sha256=digest(manifest.read_bytes()))
    config["paths"].update(cache_dir=str(tmp_path / "cache"), works=str(tmp_path / "works.jsonl"),
                           acquisition_report=str(tmp_path / "acquisition.json"))
    config.update(overrides)
    path = tmp_path / "release.yaml"
    path.write_text(yaml.safe_dump(config))
    return path


class FakeCache:
    """Serves works from memory; records whether credentials stayed out of public params."""

    def __init__(self, works: dict[str, dict], now="2999-01-01T00:00:00+00:00", fail_with=None):
        self.works, self.now, self.fail_with, self.calls = works, now, fail_with, []

    def __exit__(self, *_):
        return None

    def get(self, url, *, params=None, secret_params=None):
        self.calls.append((url, dict(params or {}), dict(secret_params or {})))
        assert secret_params == {"api_key": KEY} and "api_key" not in (params or {})
        if self.fail_with:
            raise self.fail_with
        if url.endswith("/works"):
            dois = params["filter"].removeprefix("doi:").split("|")
            results = [self.works[d] for d in dois if d in self.works]
            body = json.dumps({"meta": {"count": len(results)}, "results": results}).encode()
        else:
            doi = url.split("/works/doi:")[1]
            if doi not in self.works:
                raise SourceError("api.openalex.org: HTTP 404", 404)
            body = json.dumps(self.works[doi]).encode()
        record = {"url": url.split("?")[0], "params": dict(params or {}), "request_id": "r" + str(len(self.calls)),
                  "sha256": digest(body), "retrieved_at": self.now}
        return body, record


def mock_client(remaining=1.0, used=(0.0, 0.0005)):
    state = {"calls": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/rate-limit"
        used_now = used[min(state["calls"], len(used) - 1)]
        state["calls"] += 1
        return httpx.Response(200, json={"api_key": "xxx...yyy", "rate_limit": {
            "daily_budget_usd": 1, "daily_used_usd": used_now, "daily_remaining_usd": remaining,
            "credits_remaining": 10000, "credit_costs": {"list": 1, "singleton": 0},
            "endpoint_costs_usd": {"list": 0.0001, "singleton": 0}, "resets_at": "2026-11-08T00:00:00.000Z"}})

    return httpx.Client(transport=httpx.MockTransport(handler))


@pytest.fixture(autouse=True)
def api_key(monkeypatch):
    monkeypatch.setenv("OPENALEX_API_KEY", KEY)


def test_scope_requires_the_pinned_hash_the_expected_counts_and_unique_dois(tmp_path):
    rows = [aaai("1"), aaai("2"), ijcai("7")]
    config = yaml.safe_load(make_release(tmp_path, rows).read_text())
    assert [r["paper_id"] for r in release.load_scope(config)] == sorted(r["paper_id"] for r in rows)
    assert all(r["_doi"] for r in release.load_scope(config))
    bad = dict(config, roster={**config["roster"], "sha256": "0" * 64})
    with pytest.raises(ValueError, match="does not match the sha256"):
        release.load_scope(bad)
    dup = tmp_path / "dup"
    dup.mkdir()
    twin = {**aaai("1"), "paper_id": "paper:aaai:2021:twin"}
    with pytest.raises(ValueError, match="duplicate derived DOI"):
        release.load_scope(yaml.safe_load(make_release(dup, [aaai("1"), twin]).read_text()))
    short = dict(config, scope={**config["scope"], "expected_papers": 4})
    with pytest.raises(ValueError, match="expected 4"):
        release.load_scope(short)
    broken = tmp_path / "broken"
    broken.mkdir()
    with pytest.raises(ValueError, match="cannot derive"):
        release.load_scope(yaml.safe_load(make_release(broken, [aaai("1"), {**ijcai("7"), "official_url": "https://x.org/7"}]).read_text()))


def full_run(tmp_path, rows, works, **kwargs):
    config = make_release(tmp_path, rows)
    cache = FakeCache(works)
    result = release.acquire(config, cache=cache, client=mock_client(), **kwargs)
    return config, cache, result


def test_acquisition_matches_flags_reviews_and_reports_not_found(tmp_path):
    rows = [aaai("1"), aaai("2", title="Learning to Plan with Graph Neural Networks"), aaai("3"), aaai("4"), ijcai("7"), ijcai("8")]
    by_doi = {release.derive_doi(r): r for r in rows}
    works = {}
    for doi, row in by_doi.items():
        works[doi] = work(row)
    works[release.derive_doi(rows[1])]["title"] = "Learning to Plan with Graph Neural Network"    # flagged, accepted
    works[release.derive_doi(rows[2])]["title"] = "Something Entirely Different"                   # title review
    works[release.derive_doi(rows[3])]["authorships"] = []                                         # count review
    del works[release.derive_doi(rows[5])]                                                         # not found
    _, cache, result = full_run(tmp_path, rows, works)
    statuses = {json.loads(line)["paper_id"]: json.loads(line)["match"] for line in (tmp_path / "works.jsonl").read_text().splitlines()}
    assert {pid: m["status"] for pid, m in statuses.items()} == {
        "paper:aaai:2021:1": "matched", "paper:aaai:2021:2": "matched", "paper:aaai:2021:3": "review",
        "paper:aaai:2021:4": "review", "paper:ijcai:2021:7": "matched", "paper:ijcai:2021:8": "not_found"}
    assert statuses["paper:aaai:2021:2"]["flags"] == ["title_similarity_below_1"]
    report = json.loads((tmp_path / "acquisition.json").read_text())
    assert (report["papers"], report["matched"], report["review"], report["not_found"]) == (6, 3, 2, 1)
    assert report["matched_with_title_flag"] == 1 and report["match_rate"] == 0.5
    assert report["failure_reasons"] == {"author_count_mismatch": 1, "no_openalex_work_for_doi": 1, "title_mismatch": 1}
    assert report["by_venue_year"]["venue:aaai:2021"]["papers"] == 4 and report["by_venue_year"]["venue:ijcai:2021"]["matched"] == 1
    assert report["requests"] == {"batch_network": 1, "singleton_not_found": 1} and report["singleton_retries"] == 1
    assert report["allowance"]["used_this_run_usd"] == 0.0005 and report["allowance"]["worst_case_authorized"]["batches"] == 1
    assert report["works_sha256"] == digest((tmp_path / "works.jsonl").read_bytes())
    assert result["status"] == "written"


def test_missing_batch_dois_are_retried_once_as_singletons_and_recovered(tmp_path):
    rows = [aaai("1"), aaai("2")]
    works = {release.derive_doi(r): work(r) for r in rows}
    class BatchDropsOne(FakeCache):
        def get(self, url, **kwargs):
            body, record = super().get(url, **kwargs)
            if url.endswith("/works"):
                data = json.loads(body)
                data["results"] = data["results"][:1]
                data["meta"]["count"] = 1
                body = json.dumps(data).encode()
            return body, record
    config = make_release(tmp_path, rows)
    cache = BatchDropsOne(works)
    release.acquire(config, cache=cache, client=mock_client())
    kinds = [("batch" if u.endswith("/works") else "singleton") for u, _, _ in cache.calls]
    assert kinds == ["batch", "singleton"]
    report = json.loads((tmp_path / "acquisition.json").read_text())
    assert report["matched"] == 2 and report["not_found"] == 0


def test_mismatched_batch_work_is_rejected_after_singleton_retry(tmp_path):
    row = aaai("1")
    requested = release.derive_doi(row)
    redirected = work(row, doi="https://doi.org/10.1145/3665799")
    config = make_release(tmp_path, [row])
    cache = FakeCache({requested: redirected})

    release.acquire(config, cache=cache, client=mock_client())

    result = json.loads((tmp_path / "works.jsonl").read_text().splitlines()[0])
    assert result["match"]["status"] == "review"
    assert result["match"]["reasons"] == ["doi_disagreement"]
    assert result["match"]["doi_verification"]["state"] == "ambiguous_mismatch"
    assert ["singleton" if "/works/doi:" in url else "batch" for url, _, _ in cache.calls] == ["batch", "singleton"]


def test_works_rows_keep_evidence_source_authorships_references_and_abstract(tmp_path):
    rows = [aaai("1")]
    _, cache, _ = full_run(tmp_path, rows, {release.derive_doi(rows[0]): work(rows[0])})
    row = json.loads((tmp_path / "works.jsonl").read_text().splitlines()[0])
    assert row["doi"] == "10.1609/aaai.v35i1.1" and row["roster"]["authors"] == ["Ann One", "Bo Two"]
    assert row["roster"]["official_url"].endswith("/article/view/1") and row["roster"]["source_sha256"] == "a" * 64
    oa = row["openalex"]
    assert oa["id"] == "https://openalex.org/W1" and oa["abstract"] == "hello world"
    assert oa["referenced_works"] == ["https://openalex.org/W9"] and len(oa["authorships"]) == 2
    assert oa["source"]["locator"] == "results[0]" and len(oa["source"]["raw_sha256"]) == 64
    assert "api_key" not in json.dumps(row) and KEY not in (tmp_path / "works.jsonl").read_text()
    assert KEY not in (tmp_path / "acquisition.json").read_text() and "xxx...yyy" not in (tmp_path / "acquisition.json").read_text()


def test_requests_are_batched_at_fifty_and_the_key_never_enters_public_params(tmp_path):
    rows = [aaai(str(n)) for n in range(1, 121)]
    works = {release.derive_doi(r): work(r) for r in rows}
    _, cache, _ = full_run(tmp_path, rows, works)
    batch_calls = [params for url, params, _ in cache.calls if url.endswith("/works")]
    assert [len(p["filter"].removeprefix("doi:").split("|")) for p in batch_calls] == [50, 50, 20]
    assert all(p["per_page"] == 50 and p["select"].startswith("id,doi,title") for p in batch_calls)
    assert "authorships" in batch_calls[0]["select"] and "referenced_works" in batch_calls[0]["select"]


def test_cached_requests_are_counted_separately_from_network_requests(tmp_path):
    rows = [aaai("1")]
    config = make_release(tmp_path, rows)
    cache = FakeCache({release.derive_doi(rows[0]): work(rows[0])}, now="2000-01-01T00:00:00+00:00")
    release.acquire(config, cache=cache, client=mock_client())
    assert json.loads((tmp_path / "acquisition.json").read_text())["requests"] == {"batch_cached": 1}


def test_preflight_stops_when_the_worst_case_cost_exceeds_the_allowance(tmp_path):
    rows = [aaai(str(n)) for n in range(1, 121)]            # 3 batches x 4 attempts x $0.0001 = $0.0012
    config = make_release(tmp_path, rows)
    with pytest.raises(QuotaError, match="exceeds the remaining allowance"):
        release.acquire(config, cache=FakeCache({}), client=mock_client(remaining=0.001))
    assert not (tmp_path / "works.jsonl").exists() and not (tmp_path / "acquisition.json").exists()


def test_preflight_only_and_trial_runs_write_nothing(tmp_path):
    rows = [aaai("1"), aaai("2")]
    config = make_release(tmp_path, rows)
    only = release.acquire(config, preflight_only=True, client=mock_client())
    assert only["status"] == "preflight_only" and only["output_written"] is False
    assert only["authorization"]["worst_case_batch_cost_usd"] == 0.0004 and "api_key" not in json.dumps(only)
    trial = release.acquire(config, limit=1, cache=FakeCache({release.derive_doi(rows[0]): work(rows[0])}), client=mock_client())
    assert trial["status"] == "trial_not_written" and trial["papers"] == 1
    assert not (tmp_path / "works.jsonl").exists() and not (tmp_path / "acquisition.json").exists()


def test_existing_outputs_are_never_overwritten(tmp_path):
    rows = [aaai("1")]
    config, _, _ = full_run(tmp_path, rows, {release.derive_doi(rows[0]): work(rows[0])})
    before = (tmp_path / "works.jsonl").read_bytes()
    with pytest.raises(ValueError, match="already exist"):
        release.acquire(config, cache=FakeCache({}), client=mock_client())
    assert (tmp_path / "works.jsonl").read_bytes() == before


def test_a_failing_source_stops_the_run_without_partial_outputs(tmp_path):
    rows = [aaai("1")]
    config = make_release(tmp_path, rows)
    with pytest.raises(QuotaError):
        release.acquire(config, cache=FakeCache({}, fail_with=QuotaError("api.openalex.org: access/quota HTTP 429")), client=mock_client())
    assert not (tmp_path / "works.jsonl").exists()


def test_missing_api_key_is_reported_before_any_request(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENALEX_API_KEY")
    monkeypatch.setattr(release, "load_dotenv", lambda *a, **k: None)
    config = make_release(tmp_path, [aaai("1")])
    with pytest.raises(ValueError, match="OPENALEX_API_KEY"):
        release.acquire(config, client=mock_client())


def test_command_line_exposes_the_stage_and_reports_errors_as_json(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(release, "load_dotenv", lambda *a, **k: None)
    monkeypatch.delenv("OPENALEX_API_KEY")
    config = make_release(tmp_path, [aaai("1")])
    assert main(["release-acquire", "--config", str(config), "--preflight-only"]) == 1
    assert "OPENALEX_API_KEY" in json.loads(capsys.readouterr().err)["message"]


# --- duplicate DOIs: OpenAlex keeps an official-page record and a Crossref/arXiv record ---------


def duplicate_pair(row, *, official_landing=True, **linked_change):
    """Two records for one DOI: the crawled official-page record and the merged Crossref one."""
    official = work(row, id="https://openalex.org/W100", type="article",
                    primary_location={"landing_page_url": row["official_url"] if official_landing else None})
    official.update(linked_change)
    merged = work(row, id="https://openalex.org/W200", type="conference-paper",
                  primary_location={"landing_page_url": "https://doi.org/" + release.derive_doi(row)})
    return [merged, official]          # the merged record comes first so order cannot decide


def test_duplicate_doi_resolves_to_the_record_linked_to_the_official_page():
    row = aaai()
    result = release.evaluate_match(row, duplicate_pair(row))
    assert result["status"] == "matched" and result["chosen"] == 1
    assert "duplicate_doi_resolved_by_official_landing_page" in result["flags"]
    assert result["alternate_work_ids"] == ["https://openalex.org/W200"] and result["duplicate_author_ids_agree"] is True
    assert result["candidate_count"] == 2


def test_official_landing_page_cannot_rescue_a_duplicate_with_the_wrong_doi():
    row = aaai()
    pair = duplicate_pair(row)
    pair[1]["doi"] = "10.1145/3665799"

    result = release.evaluate_match(row, pair)

    assert result["status"] == "review"
    assert result["reasons"] == ["duplicate_doi_works"]
    assert result["chosen"] is None


@pytest.mark.parametrize("landing", ["http://www.ojs.aaai.org/index.php/AAAI/article/view/16071/",
                                     "HTTPS://OJS.AAAI.ORG/index.php/AAAI/article/view/16071"])
def test_landing_page_comparison_ignores_scheme_www_case_and_trailing_slash(landing):
    row = aaai()
    pair = duplicate_pair(row)
    pair[1]["primary_location"]["landing_page_url"] = landing
    assert release.evaluate_match(row, pair)["chosen"] == 1


def test_duplicates_with_differing_author_ids_are_flagged_not_hidden():
    row = aaai()
    pair = duplicate_pair(row)
    pair[0]["authorships"][0]["author"]["id"] = "https://openalex.org/A999"
    result = release.evaluate_match(row, pair)
    assert result["status"] == "matched" and result["duplicate_author_ids_agree"] is False


@pytest.mark.parametrize("case", ["no_landing_page_match", "both_linked", "linked_record_has_wrong_authors", "linked_record_has_wrong_title"])
def test_duplicates_without_one_clear_official_record_stay_in_review(case):
    row = aaai()
    pair = duplicate_pair(row, official_landing=case != "no_landing_page_match")
    if case == "both_linked":
        pair[0]["primary_location"]["landing_page_url"] = row["official_url"]
    elif case == "linked_record_has_wrong_authors":
        pair[1]["authorships"] = pair[1]["authorships"][:1]
        pair[0]["primary_location"]["landing_page_url"] = None
    elif case == "linked_record_has_wrong_title":
        pair[1]["title"] = "An Unrelated Chemistry Paper"
        pair[0]["primary_location"]["landing_page_url"] = None
    result = release.evaluate_match(row, pair)
    assert result["status"] == "review" and result["reasons"] == ["duplicate_doi_works"] and result["chosen"] is None
    assert result["candidate_ids"] == ["https://openalex.org/W200", "https://openalex.org/W100"]


def test_works_row_records_the_alternates_and_never_accepts_unresolved_duplicates(tmp_path):
    rows = [aaai("1"), aaai("2")]
    works = {}
    pair_one = duplicate_pair(rows[0])
    pair_two = duplicate_pair(rows[1], official_landing=False)
    class Dup(FakeCache):
        def get(self, url, **kwargs):
            body, record = super().get(url, **kwargs)
            if url.endswith("/works"):
                data = json.loads(body)
                data["results"] = pair_one + pair_two
                data["meta"]["count"] = len(data["results"])
                body = json.dumps(data).encode()
            return body, record
    config = make_release(tmp_path, rows)
    release.acquire(config, cache=Dup(works), client=mock_client())
    out = {json.loads(l)["paper_id"]: json.loads(l) for l in (tmp_path / "works.jsonl").read_text().splitlines()}
    resolved, unresolved = out["paper:aaai:2021:1"], out["paper:aaai:2021:2"]
    assert resolved["match"]["status"] == "matched" and resolved["openalex"]["id"] == "https://openalex.org/W100"
    assert resolved["openalex"]["landing_page_url"] == rows[0]["official_url"] and resolved["openalex"]["type"] == "article"
    assert [a["id"] for a in resolved["openalex"]["alternates"]] == ["https://openalex.org/W200"]
    assert unresolved["match"]["status"] == "review" and unresolved["openalex"] is None
    assert [c["id"] for c in unresolved["review_candidates"]] == ["https://openalex.org/W200", "https://openalex.org/W100"]
    report = json.loads((tmp_path / "acquisition.json").read_text())
    assert report["duplicate_doi_works"] == {"resolved_by_official_landing_page": 1,
                                             "resolved_with_differing_author_ids": 0, "left_in_review": 1}


def test_jsonl_round_trip_survives_unicode_line_separators_inside_strings(tmp_path):
    from scientific_network.collect.storage import read_jsonl, write_jsonl

    rows = [{"abstract": "line one line two\x85and more", "n": 1}, {"abstract": "plain", "n": 2}]
    path = tmp_path / "rows.jsonl"
    write_jsonl(path, rows)
    assert read_jsonl(path) == rows
