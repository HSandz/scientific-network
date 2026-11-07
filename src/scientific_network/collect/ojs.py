"""Conservative official OJS archive/roster recovery; no article enrichment.

AAAI technical issues and ICAPS Main Track qualify. Other named tracks are
retained as exclusions or review. Archive pagination and every selected issue
must complete before an edition is eligible. Invented snippets test this contract.
"""

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from scientific_network.collect.five_year import _row
from scientific_network.collect.five_year_v2 import write_complete_manifest
from scientific_network.collect.reconcile import leakage_triage
from scientific_network.collect.storage import (
    SourceCache, SourceError, digest, read_config, read_jsonl, write_json, write_jsonl,
)

VERSION = "five-year-official-rosters-v3"
OJS_HOST = "ojs.aaai.org"


def official_url(url: str, journal: str, kind: str) -> bool:
    parts = urlsplit(url)
    patterns = {
        "archive": rf"/index.php/{journal}/issue/archive(?:/[1-9]\d*)?/?",
        "issue": rf"/index.php/{journal}/issue/view/\d+/?",
        "article": rf"/index.php/{journal}/article/view/\d+/?",
        "pdf": rf"/index.php/{journal}/article/view/\d+/\d+/?",
    }
    return (parts.scheme == "https" and parts.netloc == OJS_HOST
            and not parts.query and not parts.fragment
            and re.fullmatch(patterns[kind], parts.path) is not None)


def archive_entries(body: bytes, journal: str, source: dict, *,
                    stop_before_year: int | None = None) -> tuple[list[dict], str | None]:
    soup = BeautifulSoup(body, "html.parser")
    entries = []
    for item in soup.select(".obj_issue_summary"):
        link, series = item.select_one("a.title"), item.select_one(".series")
        if link is None or series is None or not link.get("href"):
            raise ValueError("archive issue is missing its title, series or link")
        title, volume = link.get_text(" ", strip=True), series.get_text(" ", strip=True)
        url = urljoin(source["url"], link["href"])
        if not official_url(url, journal, "issue"):
            raise ValueError("archive issue link leaves the official journal")
        if journal == "AAAI":
            years = {2000 + int(y) for y in re.findall(r"\bAAAI-(\d{2})\b", title)}
        else:
            years = {int(y) for y in re.findall(r"\((20\d{2})\)", volume)}
            if not years:
                # Newer archive entries omit the parenthesized year. Only the
                # first descriptive paragraph may corroborate it, not arbitrary
                # copyright/footer years elsewhere on the page.
                description = item.select_one(".description p")
                years = {int(y) for y in re.findall(r"\b20\d{2}\b", description.get_text(" ", strip=True) if description else "")}
        if len(years) != 1:
            raise ValueError("archive issue lacks unambiguous edition-year evidence")
        year = years.pop()
        main = re.fullmatch(rf"AAAI-{year % 100:02d} Technical Tracks? (\d+)", title)
        if journal == "AAAI":
            if main:
                disposition, reason = "collect", "official_technical_issue"
            elif re.search(r"Special|Student|Demonstration|IAAI|EAAI", title):
                disposition, reason = "excluded", "non_main_issue_not_downloaded"
            else:
                disposition, reason = "review", "unknown_issue_track"
        else:
            disposition, reason = "collect", "inspect_per_article_section"
        entries.append(dict(year=year, title=title, series=volume, official_index=url,
                            adapter="ojs", journal=journal, disposition=disposition,
                            reason=reason, technical_number=int(main[1]) if main else None,
                            catalog_url=source["url"], catalog_sha256=source["sha256"],
                            catalog_locator=f"a.title[href='{link['href']}']"))
        if stop_before_year is not None and year < stop_before_year:
            break
    if not entries or len({e["official_index"] for e in entries}) != len(entries):
        raise ValueError("empty or duplicate archive issues")
    next_links = [urljoin(source["url"], a["href"]) for a in soup.select(".cmp_pagination a[href]")
                  if a.get_text(" ", strip=True) == "Next"]
    if len(next_links) > 1 or any(not official_url(u, journal, "archive") for u in next_links):
        raise ValueError("ambiguous or off-journal archive pagination")
    return entries, next_links[0] if next_links else None


def load_archive(cache: SourceCache, conference: dict, max_pages: int,
                 sources: list[dict] | None = None, *,
                 archive_parser=archive_entries) -> tuple[list[dict], list[dict]]:
    journal = conference["journal"]
    sources = [] if sources is None else sources
    body, source = cache.get(conference["source_catalog"])
    sources.append(source)
    soup = BeautifulSoup(body, "html.parser")
    links = {urljoin(source["url"], a["href"]) for a in soup.find_all("a", href=True)
             if official_url(urljoin(source["url"], a["href"]), journal, "archive")}
    if len(links) != 1:
        raise ValueError("catalog must explicitly identify one official archive root")
    url, visited, entries = links.pop(), set(), []
    for _ in range(max_pages):
        if url in visited:
            raise ValueError("archive pagination cycle")
        visited.add(url)
        body, source = cache.get(url)
        sources.append(source)
        page, next_url = archive_parser(body, journal, source)
        entries.extend(page)
        if len({e["official_index"] for e in entries}) != len(entries):
            raise ValueError("duplicate issue across archive pages")
        years = [e["year"] for e in entries]
        if years != sorted(years, reverse=True):
            raise ValueError("archive order cannot establish the year boundary")
        if next_url is None or min(years) < 2021:
            return entries, sources
        url = next_url
    raise ValueError("archive page budget exhausted before the 2021 boundary")


def edition_issues(entries: list[dict], conference: dict, year: int) -> list[dict]:
    selected = [dict(e, venue_id=conference["venue_id"], name=conference["name"],
                     include_tracks=["main"], exclude_tracks=["nonresearch"])
                for e in entries if e["year"] == year]
    if not selected:
        raise ValueError("official archive has no verified edition route; not proof of no edition")
    if conference["journal"] == "AAAI":
        numbers = sorted(e["technical_number"] for e in selected if e["disposition"] == "collect")
        if not numbers or numbers != list(range(1, max(numbers) + 1)):
            raise ValueError("incomplete or duplicate AAAI technical issue sequence")
        # All issue numbers, including excluded final issues, must be accounted
        # for. Publication volume is corroboration, never a guessed year mapping.
        volumes = [re.fullmatch(r"Vol\. (\d+) No\. (\d+)(?: \(\d{4}\))?", e["series"]) for e in selected]
        if any(v is None for v in volumes) or len({v[1] for v in volumes}) != 1:
            raise ValueError("ambiguous AAAI publication volume")
        issues = sorted(int(v[2]) for v in volumes)
        if issues != list(range(1, max(issues) + 1)):
            raise ValueError("incomplete AAAI archive issue sequence")
        if any(e["technical_number"] != int(v[2]) for e, v in zip(selected, volumes) if e["disposition"] == "collect"):
            raise ValueError("AAAI technical and publication issue numbers disagree")
    elif len(selected) != 1:
        raise ValueError("multiple ICAPS issues require explicit edition review")
    return selected


ICAPS_EXCLUDED = {
    "Frontmatter", "Novel Applications Track", "Special Track on Planning and Learning",
    "Special Track on Robotics", "Industry and Applications Track", "Planning and Learning Track",
    "Human-Aware Planning and Scheduling Track", "Robotics Track", "Position papers",
}


def parse_ojs(body: bytes, edition: dict, source: dict) -> list[dict]:
    soup = BeautifulSoup(body, "html.parser")
    heading = soup.select_one(".page_issue h1")
    expected = f"{edition['series']}: {edition['title']}"
    if heading is None or heading.get_text(" ", strip=True) != expected:
        raise ValueError("issue heading and archive title/series disagree")
    if soup.select(".cmp_pagination a"):
        raise ValueError("article pagination requires a new supported source route")
    rows = []
    for section in soup.select(".obj_issue_toc .section"):
        label = section.find("h2", recursive=False)
        label = label.get_text(" ", strip=True) if label else ""
        if edition["journal"] == "AAAI":
            track = "main" if label.startswith("AAAI Technical Track on ") else "unknown"
        else:
            track = "main" if label == "Main Track" else "nonresearch" if label in ICAPS_EXCLUDED else "unknown"
        for item in section.select(".obj_article_summary"):
            link, author = item.select_one("h3.title a[href]"), item.select_one(".authors")
            if link is None or not official_url(urljoin(edition["official_index"], link["href"]), edition["journal"], "article"):
                raise ValueError("article lacks an official journal record link")
            names = [n.strip() for n in author.get_text(" ", strip=True).split(",") if n.strip()] if author else []
            row = _row(link, names, track, edition, source)
            if track == "nonresearch":
                row.update(status="excluded", reason="excluded_non_main_section")
            if re.fullmatch(r"Preface|Frontmatter|Editorial|Introduction", row["title"], re.I):
                row.update(track="nonresearch", status="excluded", reason="excluded_editorial")
            pdf = item.select_one("a.obj_galley_link.pdf[href]")
            if pdf:
                pdf_url = urljoin(edition["official_index"], pdf["href"])
                if not official_url(pdf_url, edition["journal"], "pdf") or urlsplit(pdf_url).path.rsplit("/", 1)[0] != urlsplit(row["official_url"]).path.rstrip("/"):
                    raise ValueError("PDF link does not belong to this official article")
                row["pdf_url"] = pdf_url
            row.update(parser_version=VERSION, track_section=label,
                       catalog_url=edition["catalog_url"], catalog_sha256=edition["catalog_sha256"],
                       issue_title=edition["title"], issue_series=edition["series"])
            rows.append(row)
    if not rows or len(rows) != len(soup.select(".obj_article_summary")):
        raise ValueError("empty roster or article outside a classified section")
    if len({r["paper_id"] for r in rows}) != len(rows):
        raise ValueError("duplicate official article records")
    return rows


def _checked_input(spec: dict) -> Path:
    path = Path(spec["path"])
    if digest(path.read_bytes()) != spec["sha256"]:
        raise ValueError(f"protected input hash changed: {path}")
    return path


def recover_ojs(config_path: Path, output: Path, cache_path: Path, *,
                method_version: str = VERSION, archive_loader=load_archive,
                roster_parser=parse_ojs) -> dict:
    config = read_config(config_path)
    if (config.get("collection_authorized") is not True
            or config.get("stage_boundary") != "official_rosters_only_no_enrichment_or_splits"
            or config.get("years") != [2021, 2022, 2023, 2024, 2025]):
        raise ValueError("OJS recovery requires authorized five-year roster-only scope")
    base_paths = {k: _checked_input(v) for k, v in config["baseline"].items()}
    guard_paths = [_checked_input(g) for g in config["frozen_guards"]]
    base = json.loads(base_paths["summary"].read_text())
    if (base.get("method_version") != "five-year-official-rosters-v2"
            or base["manifest_sha256"] != digest(base_paths["manifest"].read_bytes())
            or base["edition_ledger_sha256"] != digest(base_paths["ledger"].read_bytes())):
        raise ValueError("baseline roster contract mismatch")
    original_rows, original_ledger = read_jsonl(base_paths["manifest"]), read_jsonl(base_paths["ledger"])
    expected = {(c["venue_id"], y) for c in config["conferences"] for y in config["years"]}
    if (len(config["conferences"]) != 34 or len(expected) != 170
            or {(r["venue_id"], r["year"]) for r in original_ledger} != expected
            or len(original_ledger) != 170):
        raise ValueError("recovery must preserve all 170 baseline candidates")
    targets = [c for c in config["conferences"] if c.get("adapter") == "ojs"]
    if {c["venue_id"] for c in targets} != {"venue:aaai", "venue:icaps"}:
        raise ValueError("bounded recovery supports AAAI and ICAPS only")
    for c in targets:
        if c["journal"] != c["venue_id"].split(":")[1].upper() or c["source_catalog"] != f"https://{OJS_HOST}/index.php/{c['journal']}":
            raise ValueError("recovery journal/source identity mismatch")
    if Path(config["current_membership"]) not in guard_paths:
        raise ValueError("current membership must be a hash-protected frozen guard")
    membership = read_jsonl(Path(config["current_membership"]))
    members = {r["paper_id"]: r for r in membership}
    if len(members) != len(membership):
        raise ValueError("duplicate frozen assignments")
    for name in config["membership_history"]:
        if Path(name) not in guard_paths:
            raise ValueError("historical membership must be hash-protected")
        if any(members.get(r["paper_id"]) != r for r in read_jsonl(Path(name))):
            raise ValueError("historical frozen assignment differs from current membership")
    inputs = {"config_sha256": digest(config_path.read_bytes()), "method_version": method_version,
              "sha256": {str(p): digest(p.read_bytes()) for p in [*base_paths.values(), *guard_paths]}}
    write_json(output / "inputs.json", inputs)
    # Completed replays never contact a source or re-date inherited observations.
    if (output / "summary.json").exists():
        saved = json.loads((output / "summary.json").read_text())
        for name, sha in saved["output_sha256"].items():
            if digest((output / name).read_bytes()) != sha:
                raise ValueError("recovery checkpoint output hash mismatch")
        return saved
    target_ids = {c["venue_id"] for c in targets}
    rows = [r for r in original_rows if r["venue_id"] not in target_ids]
    ledger = {(r["venue_id"], r["year"]): r for r in original_ledger}
    for conference in targets:
        slug = conference["venue_id"].split(":")[1]
        archive, sources, archive_error = [], [], None
        with SourceCache(cache_path, timeout=config["retrieval"]["timeout_seconds"],
                         attempts=config["retrieval"]["max_attempts"]) as cache:
            try:
                archive, sources = archive_loader(cache, conference, config["retrieval"]["max_archive_pages"], sources)
            except (SourceError, ValueError) as exc:
                archive_error = exc
            host_stopped = False
            for year in config["years"]:
                dest = output / "editions" / slug / str(year)
                if (dest / "summary.json").exists():
                    saved = json.loads((dest / "summary.json").read_text())
                    if digest((dest / "roster.jsonl").read_bytes()) != saved["roster_sha256"]:
                        raise ValueError("edition checkpoint roster hash mismatch")
                    records = read_jsonl(dest / "roster.jsonl")
                else:
                    records, routes, used = [], [], list(sources)
                    status, reason = "needs_review", "unknown_source_contract"
                    try:
                        if archive_error:
                            raise archive_error
                        if host_stopped:
                            raise SourceError("official journal collection stopped after prior access failure")
                        issues = edition_issues(archive, conference, year)
                        routes = issues
                        for issue in issues:
                            if issue["disposition"] != "collect":
                                continue
                            body, source = cache.get(issue["official_index"])
                            used.append(source)
                            records.extend(roster_parser(body, issue, source))
                        if len({r["paper_id"] for r in records}) != len(records):
                            raise ValueError("duplicate article IDs across edition issues")
                        if not records or any(i["disposition"] == "review" for i in issues) or any(r["status"] == "review" for r in records):
                            status, reason = "needs_review", "unknown_issue_or_article_track"
                        else:
                            status, reason = "verified_eligible", "complete_official_main_roster_parsed"
                    except (SourceError, ValueError) as exc:
                        status = "access_unavailable" if isinstance(exc, SourceError) else "needs_review"
                        reason = str(exc)
                        if isinstance(exc, SourceError):
                            host_stopped = True
                    records.sort(key=lambda r: r["paper_id"])
                    write_jsonl(dest / "roster.jsonl", records)
                    saved = dict(venue_id=conference["venue_id"], name=conference["name"], year=year,
                                 status=status, reason=reason, records=len(records),
                                 by_status=dict(Counter(r["status"] for r in records)),
                                 routes=routes, sources=used, archive_complete=archive_error is None,
                                 roster_sha256=digest((dest / "roster.jsonl").read_bytes()),
                                 checked_at=datetime.now(timezone.utc).isoformat(),
                                 reviewer="automated_contract_check_not_independent_scientific_review",
                                 rights="unknown_unless_source_record_supplies_license",
                                 redistribution="raw_downloads_local_ignored_rebuild_from_sources",
                                 method_version=method_version)
                    write_json(dest / "summary.json", saved)
                rows.extend(records)
                ledger[(conference["venue_id"], year)] = saved
    rows.sort(key=lambda r: r["paper_id"])
    if len({r["paper_id"] for r in rows}) != len(rows):
        raise ValueError("duplicate corpus paper IDs")
    editions = [ledger[(e["venue_id"], e["year"])] for e in original_ledger]
    write_complete_manifest(output / "corpus_manifest.parquet", rows)
    write_jsonl(output / "edition-ledger.jsonl", editions)
    # Carry every old/new reserved assignment forward as a leakage guard, with
    # roster titles as quarantine signals only. No new split or work merge.
    history = {r["paper_id"]: r for r in read_jsonl(base_paths["historical_manifest"])}
    history.update({r["paper_id"]: r for r in original_rows})
    triage = leakage_triage(
        rows, list(history.values()), membership,
        method_version="five-year-leakage-triage-" + method_version.rsplit("-", 1)[-1])
    write_jsonl(output / "leakage-triage.jsonl", triage)
    eligible = {(e["venue_id"], e["year"]) for e in editions if e["status"] == "verified_eligible"}
    files = ["corpus_manifest.jsonl", "corpus_manifest-complete.parquet", "edition-ledger.jsonl", "leakage-triage.jsonl"]
    files.extend(str(p.relative_to(output)) for p in sorted((output / "editions").rglob("*.json*")))
    summary = dict(stage="discover", method_version=method_version, config_sha256=inputs["config_sha256"],
                   scope="2021-2025 official_rosters_only", candidate_editions=len(editions),
                   roster_records=len(rows), records_by_status=dict(Counter(r["status"] for r in rows)),
                   edition_statuses=dict(Counter(e["status"] for e in editions)),
                   by_year=dict(Counter(str(r["year"]) for r in rows)),
                   eligible_included_records=sum(r["status"] == "included" and (r["venue_id"], r["year"]) in eligible for r in rows),
                   incomplete_editions=sum(e["status"] not in {"verified_eligible", "verified_no_edition", "excluded_track"} for e in editions),
                   review_required=sum(r["status"] == "review" for r in rows),
                   manifest_sha256=digest((output / "corpus_manifest.jsonl").read_bytes()),
                   edition_ledger_sha256=digest((output / "edition-ledger.jsonl").read_bytes()),
                   inherited_editions=160, recovery_target_editions=10,
                   frozen_assignments_guarded=len(membership),
                   protected_test_assignments=sum(r["split"] == "test" for r in membership),
                   leakage_actions=dict(Counter(r["action"] for r in triage)),
                   new_splits_created=0, canonical_works_merged=0,
                   semantic_accuracy="not_measured", enrichment_authorized_by_this_output=False,
                   graph_construction_authorized=False,
                   output_sha256={name: digest((output / name).read_bytes()) for name in files})
    write_json(output / "summary.json", summary)
    return summary
