"""Invented official-source snippets; no real author identities or data downloads."""
from pathlib import Path

import pytest
import yaml

from scientific_network.collect.ojs import (
    archive_entries, edition_issues, load_archive, parse_ojs, recover_ojs,
)
from scientific_network.collect.storage import SourceError, digest, write_json, write_jsonl

SOURCE = dict(url="https://ojs.aaai.org/index.php/AAAI/issue/archive",
              sha256="a" * 64, retrieved_at="2026-11-06T00:00:00Z")


def archive_item(title="AAAI-25 Technical Tracks 1", series="Vol. 39 No. 1", journal="AAAI", number=1):
    return f'''<div class="obj_issue_summary"><a class="title" href="https://ojs.aaai.org/index.php/{journal}/issue/view/{number}">{title}</a><div class="series">{series}</div><div class="description"><p>Copyright 2024</p></div></div>'''


def conf(journal="AAAI"):
    return dict(venue_id="venue:" + journal.lower(), name=journal, journal=journal,
                source_catalog=f"https://ojs.aaai.org/index.php/{journal}", adapter="ojs")


def issue():
    entries, _ = archive_entries(archive_item().encode(), "AAAI", SOURCE)
    return edition_issues(entries, conf(), 2025)[0]


def article(number=1, title="Invented Research", authors="Alex Lee, Alex Lee"):
    return f'''<div class="obj_article_summary"><h3 class="title"><a href="https://ojs.aaai.org/index.php/AAAI/article/view/{number}">{title}</a></h3><div class="authors">{authors}</div><a class="obj_galley_link pdf" href="https://ojs.aaai.org/index.php/AAAI/article/view/{number}/99">PDF</a></div>'''


def page(content=None, label="AAAI Technical Track on Invented Examples"):
    return f'''<div class="page_issue"><h1>Vol. 39 No. 1: AAAI-25 Technical Tracks 1</h1><div class="obj_issue_toc"><div class="section"><h2>{label}</h2>{content or article()}</div></div></div>'''.encode()


def test_same_name_byline_positions_and_source_evidence_are_preserved():
    row = parse_ojs(page(), issue(), SOURCE)[0]
    assert row["authors"] == ["Alex Lee", "Alex Lee"]
    assert row["paper_id"] == "paper:aaai:2025:1"
    assert row["status"] == "included" and row["catalog_sha256"] == "a" * 64
    assert row["source_sha256"] == "a" * 64 and "researcher_id" not in row


def test_unknown_section_abstains_and_editorial_is_excluded():
    row = parse_ojs(page(label="New Unrecognized Track"), issue(), SOURCE)[0]
    assert row["status"] == "review"
    row = parse_ojs(page(article(title="Preface", authors="")), issue(), SOURCE)[0]
    assert row["status"] == "excluded" and row["reason"] == "excluded_editorial"
    assert parse_ojs(page(article(authors="")), issue(), SOURCE)[0]["status"] == "review"


def test_icaps_unknown_research_categories_do_not_become_main():
    edition = dict(issue(), journal="ICAPS", venue_id="venue:icaps",
                   official_index="https://ojs.aaai.org/index.php/ICAPS/issue/view/1")
    for label, status in [("Main Track", "included"), ("Industry and Applications Track", "excluded"),
                          ("Theoretical papers", "review"), ("Tools papers", "review"), ("Position papers", "excluded")]:
        body = page(label=label).replace(b"/AAAI/", b"/ICAPS/")
        assert parse_ojs(body, edition, SOURCE)[0]["status"] == status


@pytest.mark.parametrize("alteration", ["duplicate", "wrong_year", "off_host", "wrong_pdf", "orphan", "pagination"])
def test_incomplete_or_conflicting_issue_evidence_fails(alteration):
    body = page(article() + article()) if alteration == "duplicate" else page()
    if alteration == "wrong_year":
        body = body.replace(b"AAAI-25", b"AAAI-24")
    elif alteration == "off_host":
        body = body.replace(b"https://ojs.aaai.org", b"https://example.org")
    elif alteration == "wrong_pdf":
        body = body.replace(b"view/1/99", b"view/2/99")
    elif alteration == "orphan":
        body += article(2).encode()
    elif alteration == "pagination":
        body += b'<div class="cmp_pagination"><a href="?page=2">Next</a></div>'
    with pytest.raises(ValueError):
        parse_ojs(body, issue(), SOURCE)


def test_archive_year_uses_series_not_stale_copyright():
    body = archive_item("Proceedings of Invented Planning Conference", "Vol. 35 (2025)", "ICAPS")
    assert archive_entries(body.encode(), "ICAPS", SOURCE)[0][0]["year"] == 2025


def test_unknown_and_special_issues_keep_explicit_dispositions():
    body = archive_item() + archive_item("AAAI-25 Special Tracks", "Vol. 39 No. 2", number=2)
    entries, _ = archive_entries(body.encode(), "AAAI", SOURCE)
    assert [x["disposition"] for x in edition_issues(entries, conf(), 2025)] == ["collect", "excluded"]
    body = body.replace("AAAI-25 Special Tracks", "AAAI-25 Unrecognized Program")
    assert archive_entries(body.encode(), "AAAI", SOURCE)[0][1]["disposition"] == "review"


@pytest.mark.parametrize("numbers", [[1, 3], [2], [1, 1]])
def test_missing_duplicate_or_partial_issue_sequence_fails(numbers):
    body = "".join(archive_item(f"AAAI-25 Technical Tracks {n}", f"Vol. 39 No. {n}", number=i + 1)
                   for i, n in enumerate(numbers))
    entries, _ = archive_entries(body.encode(), "AAAI", SOURCE)
    with pytest.raises(ValueError, match="sequence"):
        edition_issues(entries, conf(), 2025)


def test_archive_cycle_and_page_budget_fail_without_asserting_completeness():
    homepage = b'<a href="https://ojs.aaai.org/index.php/AAAI/issue/archive">Archives</a>'
    archive = (archive_item() + '<div class="cmp_pagination"><a href="https://ojs.aaai.org/index.php/AAAI/issue/archive">Next</a></div>').encode()
    class Cache:
        def get(self, url):
            return (homepage if url == conf()["source_catalog"] else archive), dict(SOURCE, url=url)
    with pytest.raises(ValueError, match="cycle"):
        load_archive(Cache(), conf(), 2)
    with pytest.raises(ValueError, match="budget"):
        load_archive(Cache(), conf(), 1)


def recovery_fixture(tmp_path):
    config = yaml.safe_load(Path("configs/corpus-five-year-v3.yaml").read_text())
    old = tmp_path / "old"
    rows = [dict(paper_id="reserved", title="Invented Held Out Work", venue_id="venue:icml", year=2024,
                 status="included", authors=["Alex Lee"])]
    ledger = [dict(venue_id=c["venue_id"], year=y, status="unresolved", records=0)
              for c in config["conferences"] for y in config["years"]]
    write_jsonl(old / "manifest.jsonl", rows)
    write_jsonl(old / "ledger.jsonl", ledger)
    write_json(old / "summary.json", dict(method_version="five-year-official-rosters-v2",
               manifest_sha256=digest((old / "manifest.jsonl").read_bytes()),
               edition_ledger_sha256=digest((old / "ledger.jsonl").read_bytes())))
    write_jsonl(old / "membership.jsonl", [dict(paper_id="reserved", split="test", is_pilot=False)])
    files = dict(manifest=old / "manifest.jsonl", ledger=old / "ledger.jsonl", summary=old / "summary.json",
                 historical_manifest=old / "manifest.jsonl")
    config["baseline"] = {k: dict(path=str(p), sha256=digest(p.read_bytes())) for k, p in files.items()}
    member = old / "membership.jsonl"
    config["current_membership"] = str(member)
    config["membership_history"] = [str(member)]
    config["frozen_guards"] = [dict(path=str(member), sha256=digest(member.read_bytes()))]
    cp = tmp_path / "config.yaml"
    cp.write_text(yaml.safe_dump(config))
    return cp, member


def test_changed_frozen_assignments_fail_before_source_access(tmp_path, monkeypatch):
    from scientific_network.collect.storage import SourceCache
    cp, member = recovery_fixture(tmp_path)
    member.write_text("changed\n")
    monkeypatch.setattr(SourceCache, "get", lambda *a, **k: pytest.fail("source access before guards"))
    with pytest.raises(ValueError, match="protected input"):
        recover_ojs(cp, tmp_path / "out", tmp_path / "cache")


def test_source_failure_ledger_and_replay_preserve_all_candidates(tmp_path, monkeypatch):
    from scientific_network.collect.storage import SourceCache
    cp, _ = recovery_fixture(tmp_path)
    def fail(*a, **k):
        raise SourceError("invented HTTP 503")
    monkeypatch.setattr(SourceCache, "get", fail)
    output = tmp_path / "out"
    result = recover_ojs(cp, output, tmp_path / "cache")
    assert result["candidate_editions"] == 170 and result["protected_test_assignments"] == 1
    assert result["edition_statuses"] == {"unresolved": 160, "access_unavailable": 10}
    assert result["new_splits_created"] == result["canonical_works_merged"] == 0
    monkeypatch.setattr(SourceCache, "get", lambda *a, **k: pytest.fail("network on completed replay"))
    assert recover_ojs(cp, output, tmp_path / "cache") == result
    roster = output / "editions/aaai/2021/roster.jsonl"
    roster.write_text("corrupt\n")
    with pytest.raises(ValueError, match="checkpoint output"):
        recover_ojs(cp, output, tmp_path / "cache")


def test_v4_stops_at_verified_boundary_and_v3_still_withholds_old_layout():
    from scientific_network.collect.ojs_v4 import archive_entries_v4
    body = (archive_item() + archive_item("AAAI-20 Technical Tracks 1", "Vol. 34 No. 1", number=2)
            + archive_item("Issue 9: EAAI-20 / AAAI Special Programs", "Vol. 34 No. 09", number=3)).encode()
    with pytest.raises(ValueError, match="edition-year"):
        archive_entries(body, "AAAI", SOURCE)
    entries, _ = archive_entries_v4(body, "AAAI", SOURCE)
    assert [e["year"] for e in entries] == [2025, 2020]
    assert len(edition_issues(entries, conf(), 2025)) == 1


def test_second_issue_failure_withholds_whole_edition_and_guards_reserved_versions(tmp_path, monkeypatch):
    import scientific_network.collect.ojs as ojs
    from scientific_network.collect.storage import SourceCache, read_jsonl
    cp, _ = recovery_fixture(tmp_path)
    body = archive_item("AAAI-21 Technical Tracks 1", "Vol. 35 No. 1")
    body += archive_item("AAAI-21 Technical Tracks 2", "Vol. 35 No. 2", number=2)
    entries, _ = archive_entries(body.encode(), "AAAI", SOURCE)
    def loader(cache, conference, max_pages, sources):
        if conference["journal"] == "ICAPS":
            raise SourceError("invented ICAPS unavailable")
        return entries, [SOURCE]
    def get(self, url, **kwargs):
        if url.endswith("/2"):
            raise SourceError("invented second issue HTTP 503")
        data = page(article(title="Invented Held Out Work"))
        data = data.replace(b"Vol. 39 No. 1: AAAI-25", b"Vol. 35 No. 1: AAAI-21")
        return data, dict(SOURCE, url=url)
    monkeypatch.setattr(SourceCache, "get", get)
    output = tmp_path / "out"
    result = recover_ojs(cp, output, tmp_path / "cache", archive_loader=loader)
    assert result["eligible_included_records"] == 0
    assert result["leakage_actions"]["held_out_version_guard"] == 1
    first = next(r for r in read_jsonl(output / "edition-ledger.jsonl")
                 if r["venue_id"] == "venue:aaai" and r["year"] == 2021)
    assert first["status"] == "access_unavailable" and first["records"] == 1
    assert len(first["routes"]) == 2
    triage = read_jsonl(output / "leakage-triage.jsonl")
    candidate = next(r for r in triage if r["paper_id"] != "reserved")
    assert candidate["action"] == "held_out_version_guard" and candidate["canonical_work_id"] is None


@pytest.mark.parametrize("year,label", [
    (2021, "AAAI Technical Track Focus Area on Neuro-Symbolic AI"),
    (2024, "Intelligent Robots (ROB)"),
])
def test_v5_literal_main_variants_are_edition_bound_and_keep_missing_bylines_withheld(year, label):
    from scientific_network.collect.ojs_v5 import parse_v5
    volume = year - 1986
    entries, _ = archive_entries(archive_item(f"AAAI-{year % 100} Technical Tracks 1", f"Vol. {volume} No. 1").encode(), "AAAI", SOURCE)
    edition = edition_issues(entries, conf(), year)[0]
    def body(authors="Alpha, Beta"):
        return page(article(authors=authors), label).replace(
            b"Vol. 39 No. 1: AAAI-25", f"Vol. {volume} No. 1: AAAI-{year % 100}".encode())
    assert parse_ojs(body(), edition, SOURCE)[0]["status"] == "review"
    row = parse_v5(body(), edition, SOURCE)[0]
    assert row["status"] == "included" and row["track_section"] == label
    assert row["section_policy"].startswith("D027_")
    assert parse_v5(body(authors=""), edition, SOURCE)[0]["status"] == "review"
    wrong_year = dict(edition, year=2025)
    assert parse_v5(body(), wrong_year, SOURCE)[0]["status"] == "review"
