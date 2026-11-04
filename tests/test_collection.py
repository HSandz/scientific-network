from pathlib import Path

import httpx
import pytest

from scientific_network.collect.discover import parse_index
from scientific_network.collect.storage import SourceCache, SourceError, QuotaError
from scientific_network.collect.splits import allocate
from scientific_network.collect.acquire import choose_work


def edition():
    return {"venue_id": "venue:neurips", "year": 2023,
        "official_index": "https://proceedings.neurips.cc/paper/2023",
        "include_tracks": ["main"], "exclude_tracks": ["datasets_and_benchmarks"]}


def source():
    return {"url": "https://example.org/index", "sha256": "a" * 64, "retrieved_at": "2026-11-03T00:00:00Z"}


def test_official_tracks_are_not_inferred_from_shared_proceedings():
    html = b'''<ul>
    <li data-track="conference"><a href="/paper_files/paper/2023/hash/aaa-Abstract-Conference.html">Main</a><span class="paper-authors">Person A, Person B</span></li>
    <li data-track="datasets_and_benchmarks"><a href="/paper_files/paper/2023/hash/bbb-Abstract-Datasets_and_Benchmarks.html">Dataset</a><span class="paper-authors">Person C</span></li>
    <li><a href="/paper_files/paper/2023/hash/ccc-Abstract-Conference.html">Unknown</a><span class="paper-authors">Person D</span></li>
    </ul>'''
    rows = parse_index(html, edition(), source())
    assert [(r["status"], r["track"]) for r in rows] == [
        ("included", "main"), ("excluded", "datasets_and_benchmarks"), ("review", "unknown")]


def test_empty_or_changed_official_index_fails_loudly():
    with pytest.raises(ValueError, match="no paper records"):
        parse_index(b"<html>temporary maintenance</html>", edition(), source())


def test_frozen_splits_are_order_independent_balanced_and_disjoint():
    rows = [{"paper_id": f"{venue}-{i}", "title": f"{venue} unique work {i}", "venue_id": venue, "status": "included"}
            for venue in ["A", "B"] for i in range(15)]
    a = allocate(rows, seed=17, test=3, development=2, pilot=8)
    assert a == allocate(list(reversed(rows)), seed=17, test=3, development=2, pilot=8)
    assert sum(r["split"] == "test" for r in a) == 6
    assert sum(r["split"] == "development" for r in a) == 4
    assert sum(r["is_pilot"] for r in a) == 8
    assert not any(r["is_pilot"] and r["split"] == "test" for r in a)


def test_duplicate_title_versions_cannot_silently_change_split_counts():
    rows = [{"paper_id": str(i), "title": f"Work {i // 2}", "venue_id": "A", "status": "included"} for i in range(20)]
    with pytest.raises(ValueError, match="duplicate versions"):
        allocate(rows, seed=4, test=2, development=2, pilot=4)


def test_cache_redacts_keys_resumes_and_detects_raw_corruption(tmp_path):
    calls = []
    def handler(request):
        calls.append(request)
        assert request.url.params["api_key"] == "private-key-do-not-log"
        return httpx.Response(200, json={"results": []})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        cache = SourceCache(tmp_path, client=client, delay=0)
        first = cache.get("https://api.openalex.org/works", params={"search": "test"}, secret_params={"api_key": "private-key-do-not-log"})
        assert cache.get("https://api.openalex.org/works", params={"search": "test"}) == first
        assert len(calls) == 1
        assert all(b"private-key-do-not-log" not in p.read_bytes() for p in tmp_path.rglob("*") if p.is_file())
        (tmp_path / "objects" / first[1]["sha256"]).write_bytes(b"corrupted")
        with pytest.raises(SourceError, match="hash mismatch"):
            cache.get("https://api.openalex.org/works", params={"search": "test"})


def test_quota_failure_stops_without_exposing_secret_or_caching_error(tmp_path):
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(429))) as client:
        cache = SourceCache(tmp_path, client=client, delay=0)
        with pytest.raises(QuotaError) as error:
            cache.get("https://api.openalex.org/works", secret_params={"api_key": "secret"})
        assert "secret" not in str(error.value)
        assert not list(tmp_path.rglob("*.json"))


def test_credentials_cannot_enter_public_cache_descriptor(tmp_path):
    with SourceCache(tmp_path) as cache:
        with pytest.raises(ValueError, match="secret_params"):
            cache.get("https://api.openalex.org/works", params={"api_key": "secret"})


def test_title_only_match_and_incomplete_or_wrong_bylines_are_rejected():
    paper = {"title": "An example work", "authors": ["Alice Smith", "Bob Jones"]}
    wrong = {"id": "W1", "title": paper["title"], "publication_year": 2023,
             "authorships": [{"author": {"display_name": "Another Person"}}]}
    assert choose_work([wrong], paper, "https://example.org/official")[0] is None


def test_duplicate_candidate_versions_are_reviewed_unless_identifier_corroborates():
    paper = {"title": "A work", "authors": ["Alice Smith"], "doi": "10.1234/test"}
    work = {"id": "W1", "title": "A work", "publication_year": 2023,
            "authorships": [{"author": {"display_name": "Alice Smith"}}]}
    other = {**work, "id": "W2"}
    assert choose_work([work, other], paper, "https://example.org/official")[0] is None
    other["doi"] = "https://doi.org/10.1234/test"
    assert choose_work([work, other], paper, "https://example.org/official")[0]["id"] == "W2"
