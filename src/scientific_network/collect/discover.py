"""Official roster authority; unknown tracks are retained for review, never included."""

from collections import Counter
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from scientific_network.collect.storage import SourceCache, SourceError, digest, read_config, write_json, write_table

PARSER_VERSION = "official-roster-v1"


def parse_index(body: bytes, edition: dict, source: dict) -> list[dict]:
    if edition.get("adapter"):
        from scientific_network.collect.rosters import parse_roster
        return parse_roster(body, edition, source)
    soup = BeautifulSoup(body, "html.parser")
    rows = []
    venue = edition["venue_id"]
    if venue == "venue:neurips":
        entries = []
        for item in soup.select("li"):
            link = item.find("a", href=lambda value: value and re.search(r"/2023/hash/[^/]+-Abstract", value))
            if link:
                entries.append((item, link))
    elif venue == "venue:icml":
        if "202" not in soup.get_text(" ", strip=True) or "2023" not in soup.get_text(" ", strip=True):
            raise ValueError("ICML index does not identify expected volume/year")
        entries = [(item, item.find("a", href=lambda value: value and re.search(r"/v202/[^/]+\.html$", value)))
                   for item in soup.select("div.paper")]
    else:
        raise ValueError("unsupported conference edition")
    for item, link in entries:
        if link is None:
            raise ValueError("official paper entry is missing its record link")
        url = urljoin(edition["official_index"], link["href"])
        if venue == "venue:neurips":
            identifier = urlsplit(url).path.split("/")[-1].split("-Abstract")[0]
            title = link.get_text(" ", strip=True)
            author_element = item.select_one(".paper-authors") or item.find("i")
            raw_authors = author_element.get_text(" ", strip=True) if author_element else ""
            marker = item.get("data-track", "").lower()
            text = item.get_text(" ", strip=True).lower()
            if marker in {"datasets-and-benchmarks", "datasets_and_benchmarks", "datasetsandbenchmarks"} or "datasets and benchmarks track" in text:
                track = "datasets_and_benchmarks"
            elif marker == "conference" or "main conference track" in text:
                track = "main"
            else:
                track = "unknown"
            pdf = None
        else:
            identifier = urlsplit(url).path.split("/")[-1].removesuffix(".html")
            title_element = item.select_one(".title")
            if title_element is None:
                raise ValueError("official PMLR paper missing title")
            title = title_element.get_text(" ", strip=True)
            author_element = item.select_one(".authors")
            raw_authors = author_element.get_text(" ", strip=True) if author_element else ""
            track = "main"
            pdf_link = item.find("a", href=lambda value: value and value.endswith(".pdf"))
            pdf = urljoin(url, pdf_link["href"]) if pdf_link else None
        if not title or not raw_authors:
            status, reason = "review", "missing_title_or_byline"
        elif re.search(r"\b(withdrawn|retracted|editorial|preface)\b", title, re.I):
            status, reason = "excluded", "noneligible_record_requires_roster_review"
        elif track in edition["include_tracks"]:
            status, reason = "included", "official_main_track"
        elif track in edition["exclude_tracks"]:
            status, reason = "excluded", "excluded_track"
        else:
            status, reason = "review", "unknown_track"
        openreview = item.find("a", href=lambda value: value and "openreview.net/forum" in value)
        rows.append({"paper_id": f"paper:{venue.split(':')[1]}:{edition['year']}:{identifier}",
            "official_record_id": identifier, "venue_id": venue, "year": edition["year"],
            "title": title, "authors": [name.strip() for name in raw_authors.split(",") if name.strip()],
            "raw_authors": raw_authors, "official_url": url, "pdf_url": pdf,
            "openreview_url": openreview["href"] if openreview else None,
            "track": track, "status": status, "reason": reason,
            "source_url": source["url"], "source_sha256": source["sha256"],
            "retrieved_at": source["retrieved_at"],
            "source_locator": f"a[href='{link['href']}']", "parser_version": PARSER_VERSION})
    if not rows:
        raise ValueError("official index yielded no paper records; source layout must be reviewed")
    identifiers = [row["paper_id"] for row in rows]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("duplicate official record IDs; roster must be reconciled")
    return rows


def discover(config_path: Path, output: Path, cache_path: Path) -> dict:
    config = read_config(config_path)
    if config.get("workflow") == "five_year_source_closure_v10":
        from scientific_network.collect.source_closure_v10 import discover_v10
        return discover_v10(config_path, output)
    if config.get("workflow") == "five_year_source_closure_v9":
        from scientific_network.collect.source_closure_v9 import discover_v9
        return discover_v9(config_path, output)
    if config.get("workflow") == "five_year_source_closure_v8":
        from scientific_network.collect.source_closure_v8 import discover_v8
        return discover_v8(config_path, output)
    if config.get("workflow") == "five_year_source_closure_v7":
        from scientific_network.collect.source_closure_v7 import discover_v7
        return discover_v7(config_path, output)
    if config.get("workflow") == "five_year_rosters_v6":
        from scientific_network.collect.ojs_v6 import recover_v6
        return recover_v6(config_path, output, cache_path)
    if config.get("workflow") == "five_year_rosters_v5":
        from scientific_network.collect.ojs_v5 import recover_v5
        return recover_v5(config_path, output, cache_path)
    if config.get("workflow") == "five_year_rosters_v4":
        from scientific_network.collect.ojs_v4 import recover_v4
        return recover_v4(config_path, output, cache_path)
    if config.get("workflow") == "five_year_rosters_v3":
        from scientific_network.collect.ojs import recover_ojs
        return recover_ojs(config_path, output, cache_path)
    if config.get("workflow") == "five_year_rosters_v2":
        from scientific_network.collect.five_year_v2 import discover_v2
        return discover_v2(config_path, output, cache_path)
    if config.get("workflow") == "five_year_rosters_v1":
        from scientific_network.collect.five_year import discover_five_year
        return discover_five_year(config_path, output, cache_path)
    if config.get("collection_authorized") is False or "editions" not in config:
        raise ValueError("planning registry is not an authorized executable corpus config")
    if config.get("legacy_manifest"):
        from scientific_network.collect.extended import discover_extended
        return discover_extended(config_path, output, cache_path)
    rows = []
    with SourceCache(cache_path, timeout=config["retrieval"]["timeout_seconds"],
                     attempts=config["retrieval"]["max_attempts"]) as cache:
        for edition in config["editions"]:
            body, source = cache.get(edition["official_index"])
            rows.extend(parse_index(body, edition, source))
    rows.sort(key=lambda row: row["paper_id"])
    write_table(output / "corpus_manifest.parquet", rows)
    summary = {"stage": "discover", "parser_version": PARSER_VERSION,
        "config_sha256": digest(config_path.read_bytes()), "roster_records": len(rows),
        "by_venue_status": dict(Counter(f"{r['venue_id']}:{r['status']}" for r in rows)),
        "by_track": dict(Counter(r["track"] for r in rows)),
        "manifest_sha256": digest((output / "corpus_manifest.jsonl").read_bytes()),
        "review_required": sum(r["status"] == "review" for r in rows)}
    write_json(output / "summary.json", summary)
    return summary
