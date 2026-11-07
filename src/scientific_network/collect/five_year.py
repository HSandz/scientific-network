"""Versioned five-year roster collection; no enrichment, split or identity claims.

Catalog evidence chooses edition routes. Missing links never prove no edition.
Individual edition checkpoints are input-bound; failures need a new output version.
"""

from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from scientific_network.collect.rosters import parse_roster
from scientific_network.collect.storage import (
    SourceCache, SourceError, digest, read_config, read_jsonl, write_json, write_jsonl, write_table,
)

VERSION = "five-year-official-rosters-v1"
PMLR_SERIES = {"icml": "ICML", "aistats": "AISTATS", "uai": "UAI", "colt": "COLT", "corl": "CoRL"}


def edition_routes(body: bytes, conference: dict, year: int) -> list[dict]:
    """Choose only edition-specific links on an official catalog, without guessing years."""
    soup = BeautifulSoup(body, "html.parser")
    family = conference.get("adapter")
    slug = conference["venue_id"].split(":")[1]
    base = conference["source_catalog"]
    common = dict(venue_id=conference["venue_id"], name=conference["name"], year=year,
                  adapter=family, include_tracks=["main"],
                  exclude_tracks=["nonresearch", "datasets_and_benchmarks"])
    found = []
    if family == "pmlr":
        # Catalog date is the conference year (CoRL publication may be next year).
        for item in soup.select("ul.proceedings-list li"):
            text = " ".join(item.get_text(" ", strip=True).split())
            link = item.find("a", href=re.compile(r"^/?v\d+/?$"))
            if link and re.fullmatch(rf"Volume \d+ Proceedings of {PMLR_SERIES[slug]} {year}", text, re.I):
                volume = int(re.search(r"v(\d+)", link["href"])[1])
                found.append({**common, "official_index": urljoin(base, link["href"].rstrip("/") + "/"),
                              "volume": volume, "required_markers": [str(year), f"Volume {volume}"],
                              "catalog_locator": text})
    elif family == "acl":
        # Findings, industry, demos, tutorials and student tracks are deliberately absent.
        pattern = re.compile(rf"^/(?:volumes/)?({year}\.{slug}-(?:long|short|main|1))/$")
        for link in soup.find_all("a", href=pattern):
            collection = pattern.fullmatch(link["href"])[1]
            found.append({**common, "official_index": urljoin(base, link["href"]),
                          "collection": collection, "catalog_locator": link.get_text(" ", strip=True)})
    elif family in {"neurips", "mlsys"}:
        pattern = re.compile(rf"^/(?:paper_files/)?paper/{year}(?:/vol\d+-main-conference)?/?$")
        candidates = [a for a in soup.find_all("a", href=pattern)
                      if "creative" not in a.get_text(" ", strip=True).casefold()]
        specific = [a for a in candidates if "main-conference" in a["href"]]
        for link in specific or candidates:
            found.append({**common, "official_index": urljoin(base, link["href"]),
                          "catalog_locator": link.get_text(" ", strip=True)})
    elif family == "cvf":
        for link in soup.find_all("a", href=True):
            url = urljoin(base, link["href"])
            if urlsplit(url).path.rstrip("/") == f"/{slug.upper()}{year}":
                found.append({**common, "official_index": url.split("?")[0], "params": {"day": "all"},
                              "catalog_locator": link.get_text(" ", strip=True)})
    elif family in {"ijcai", "kr"}:
        for link in soup.find_all("a", href=True):
            url = urljoin(base, link["href"])
            expected = f"/proceedings/{year}" if family == "ijcai" else f"/{year}"
            if urlsplit(url).path.rstrip("/") == expected and urlsplit(url).netloc == urlsplit(base).netloc:
                found.append({**common, "official_index": url.rstrip("/") + "/",
                              "catalog_locator": link.get_text(" ", strip=True)})
    elif family == "rss":
        for link in soup.find_all("a", href=re.compile(r"rss\d+/(?:index.html)?$")):
            # The home-page edition heading contains both edition and date. Navigation
            # links alone do not establish the year mapping.
            parent = link.find_parent(["p", "td", "li", "div"])
            text = parent.get_text(" ", strip=True) if parent else ""
            if re.search(rf"\b{year}\b", text) and len(text) < 1000:
                found.append({**common, "official_index": urljoin(base, link["href"]),
                              "catalog_locator": text})
    elif family == "ecva":
        # One official page holds multiple editions; paper URL and heading must agree.
        if soup.find("a", href=re.compile(rf"papers/eccv_{year}/")):
            found.append({**common, "official_index": base,
                          "catalog_locator": f"ECCV {year} Papers; papers/eccv_{year}/"})
    unique = {r["official_index"]: r for r in found}
    routes = list(unique.values())
    if family != "acl" and len(routes) > 1:
        raise ValueError("ambiguous edition routes; explicit review required")
    if family == "acl":
        suffixes = {r["collection"].rsplit("-", 1)[-1] for r in routes}
        if suffixes & {"long", "short"} and not {"long", "short"} <= suffixes:
            raise ValueError("incomplete long/short volume route; explicit review required")
    return routes


def parse_five_year(body: bytes, edition: dict, source: dict) -> list[dict]:
    family, year = edition["adapter"], edition["year"]
    soup = BeautifulSoup(body, "html.parser")
    if str(year) not in soup.get_text(" ", strip=True):
        raise ValueError("official page does not identify expected edition year")
    if family not in {"neurips", "ecva"}:
        return parse_roster(body, edition, source)
    rows = []
    if family == "neurips":
        for item in soup.select("li"):
            link = item.find("a", href=re.compile(rf"/{year}/hash/[^/]+-Abstract"))
            if not link:
                continue
            text = item.get_text(" ", strip=True).casefold()
            marker = item.get("data-track", "").casefold()
            if marker in {"datasetsandbenchmarks", "datasets-and-benchmarks", "datasets_and_benchmarks"} or "datasets and benchmarks track" in text:
                track = "datasets_and_benchmarks"
            elif marker == "conference" or "main conference track" in text or year == 2021:
                # Official catalog explicitly separates the 2021 D&B proceedings.
                track = "main"
            else:
                track = "unknown"
            author = item.select_one(".paper-authors") or item.find("i")
            authors = [v.strip() for v in author.get_text(" ", strip=True).split(",") if v.strip()] if author else []
            rows.append(_row(link, authors, track, edition, source))
    else:
        for item in soup.select("dt.ptitle"):
            link = item.find("a", href=re.compile(rf"papers/eccv_{year}/"))
            if not link:
                continue
            heading = item.find_previous(["h2", "h3"])
            if not heading or not re.search(rf"ECCV\s+{year}", heading.get_text(" ", strip=True)):
                raise ValueError("ECVA paper URL and edition heading do not agree")
            author = item.find_next_sibling("dd")
            authors = [v.strip() for v in author.get_text(" ", strip=True).split(",") if v.strip()] if author else []
            rows.append(_row(link, authors, "main", edition, source))
    if not rows:
        raise ValueError("empty roster; reconcile official layout")
    if len({r["paper_id"] for r in rows}) != len(rows):
        raise ValueError("duplicate official records; reconcile before acceptance")
    return rows


def _row(link, authors: list[str], track: str, edition: dict, source: dict) -> dict:
    url = urljoin(edition["official_index"], link["href"])
    identifier = urlsplit(url).path.rstrip("/").rsplit("/", 1)[-1].split("-Abstract")[0]
    title = link.get_text(" ", strip=True)
    status = "included" if track == "main" else "excluded" if track in edition["exclude_tracks"] else "review"
    reason = "official_main_track" if status == "included" else "excluded_track" if status == "excluded" else "unknown_track"
    if not title or not authors:
        status, reason = "review", "missing_title_or_byline"
    return dict(paper_id=f"paper:{edition['venue_id'].split(':')[1]}:{edition['year']}:{identifier}",
                official_record_id=identifier, venue_id=edition["venue_id"], year=edition["year"],
                title=title, authors=authors, raw_authors=", ".join(authors), official_url=url,
                pdf_url=None, openreview_url=None, track=track, status=status, reason=reason,
                source_url=source["url"], source_sha256=source["sha256"],
                retrieved_at=source["retrieved_at"], source_locator=f"a[href='{link['href']}']",
                parser_version=VERSION)


def discover_five_year(config_path: Path, output: Path, cache_path: Path, *,
                      method_version: str = VERSION, roster_parser=parse_five_year,
                      route_resolver=edition_routes, manifest_table_writer=write_table) -> dict:
    config = read_config(config_path)
    if config.get("collection_authorized") is not True or config.get("stage_boundary") != "official_rosters_only_no_enrichment_or_splits":
        raise ValueError("five-year discovery requires explicit roster-only authorization")
    years, conferences = config["years"], config["conferences"]
    if years != [2021, 2022, 2023, 2024, 2025] or len(conferences) != 34 or len({c['venue_id'] for c in conferences}) != 34:
        raise ValueError("five-year config must preserve 34 unique series and all five years")
    inputs = {"config_sha256": digest(config_path.read_bytes()), "method_version": method_version}
    write_json(output / "inputs.json", inputs)

    def series_task(conference):
        slug = conference["venue_id"].split(":")[1]
        all_rows, ledger = [], []
        with SourceCache(cache_path, timeout=config['retrieval']['timeout_seconds'],
                         attempts=config['retrieval']['max_attempts']) as cache:
            catalog, catalog_source, failure = None, None, None
            for year in years:
                destination = output / "editions" / slug / str(year)
                if (destination / "summary.json").exists():
                    saved = json.loads((destination / "summary.json").read_text())
                    records = read_jsonl(destination / "roster.jsonl")
                    if saved["roster_sha256"] != digest((destination / "roster.jsonl").read_bytes()):
                        raise ValueError("checkpoint roster hash mismatch")
                    all_rows.extend(records); ledger.append(saved)
                    continue
                sources, routes, records = [], [], []
                status, reason = "unresolved", "official_catalog_has_no_verified_edition_route"
                try:
                    if catalog is None and failure is None:
                        try:
                            catalog, catalog_source = cache.get(conference["source_catalog"])
                        except SourceError as exc:
                            failure = str(exc)
                    if failure:
                        status, reason = "access_unavailable", failure
                    else:
                        sources.append(catalog_source)
                        if not conference.get("adapter"):
                            reason = "catalog_retrieved_but_main_track_adapter_not_implemented"
                        else:
                            routes = route_resolver(catalog, conference, year)
                            if routes:
                                for route in routes:
                                    body, source = cache.get(route["official_index"], params=route.get("params"))
                                    sources.append(source)
                                    records.extend(roster_parser(body, route, source))
                                if len({r["paper_id"] for r in records}) != len(records):
                                    raise ValueError("duplicate official IDs across edition volumes")
                                status = "verified_eligible" if all(r["status"] != "review" for r in records) else "needs_review"
                                reason = "official_main_roster_parsed" if status == "verified_eligible" else "roster_contains_unresolved_records"
                except (SourceError, ValueError) as exc:
                    status = "access_unavailable" if isinstance(exc, SourceError) else "needs_review"
                    reason = str(exc)
                write_table(destination / "roster.parquet", records)
                summary = {"venue_id": conference["venue_id"], "name": conference["name"], "year": year,
                    "status": status, "reason": reason, "records": len(records),
                    "by_status": dict(Counter(r["status"] for r in records)),
                    "routes": routes, "sources": sources,
                    "roster_sha256": digest((destination / "roster.jsonl").read_bytes()),
                    "checked_at": datetime.now(timezone.utc).isoformat(),
                    "reviewer": "automated_contract_check_not_independent_scientific_review",
                    "rights": "unknown_unless_source_record_supplies_license",
                    "redistribution": "raw_downloads_local_ignored_rebuild_from_sources",
                    "method_version": method_version}
                write_json(destination / "summary.json", summary)
                all_rows.extend(records); ledger.append(summary)
                print(f"discover: {slug}:{year}: {status}: {len(records)} records", flush=True)
        return all_rows, ledger

    with ThreadPoolExecutor(max_workers=config["retrieval"]["series_workers"]) as executor:
        results = list(executor.map(series_task, conferences))
    rows = sorted([r for records, _ in results for r in records], key=lambda r: r["paper_id"])
    ledger = [row for _, summaries in results for row in summaries]
    if len({r["paper_id"] for r in rows}) != len(rows):
        raise ValueError("duplicate corpus official paper ID")
    # Heterogeneous nested source/route contracts belong in lossless JSONL. Empty
    # mappings in entirely blocked ledgers have no valid Parquet struct schema.
    write_jsonl(output / "edition-ledger.jsonl", ledger)
    manifest_table_writer(output / "corpus_manifest.parquet", rows)
    eligible = { (r['venue_id'], r['year']) for r in ledger if r['status'] == 'verified_eligible' }
    summary = {"stage": "discover", **inputs, "scope": "2021-2025 official_rosters_only",
        "candidate_editions": len(ledger), "roster_records": len(rows),
        "records_by_status": dict(Counter(r['status'] for r in rows)),
        "edition_statuses": dict(Counter(r['status'] for r in ledger)),
        "by_year": dict(Counter(str(r['year']) for r in rows)),
        "eligible_included_records": sum(r['status']=='included' and (r['venue_id'],r['year']) in eligible for r in rows),
        "incomplete_editions": sum(r['status'] not in {'verified_eligible','verified_no_edition','excluded_track'} for r in ledger),
        "review_required": sum(r['status']=='review' for r in rows),
        "manifest_sha256": digest((output / 'corpus_manifest.jsonl').read_bytes()),
        "edition_ledger_sha256": digest((output / 'edition-ledger.jsonl').read_bytes()),
        "canonical_work_count": None, "resolved_researchers": None,
        "semantic_accuracy": "not_measured", "enrichment_status": "not_started_requires_leakage_reconciliation_and_frozen_design"}
    write_json(output / "summary.json", summary)
    return summary
