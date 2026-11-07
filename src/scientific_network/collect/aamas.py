"""Strict IFAAMAS proceedings TOC parser for versioned roster recovery."""

from __future__ import annotations

from collections import Counter
from pathlib import PurePosixPath
import re
import unicodedata
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bs4.element import NavigableString

VERSION = "ifaamas-official-toc-v1"
PAPER_HREF = re.compile(r"^\.\./pdfs/(p\d+)\.pdf$")


def parse_aamas_roster(body: bytes, edition: dict, source: dict) -> list[dict]:
    """Parse an edition's complete official TOC without guessing section tracks.

    This is deliberately separate from the historical ``aamas`` parser in
    ``rosters.py``. Each supported edition names its exact included section and
    the complete set of observed section headings in its correction manifest.
    """
    year = edition["year"]
    try:
        decoded = body.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("IFAAMAS TOC is not valid UTF-8") from exc
    soup = BeautifulSoup(decoded, "html.parser")
    page_text = " ".join(soup.get_text(" ", strip=True).split())
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    if f"AAMAS {year}" not in title and f"AAMAS-{year}" not in title:
        raise ValueError(f"IFAAMAS page title does not identify AAMAS {year}")
    if str(year) not in page_text:
        raise ValueError(f"IFAAMAS page body does not identify AAMAS {year}")

    main_section = edition["main_section"]
    expected_sections = set(edition["expected_section_counts"])
    if main_section not in expected_sections:
        raise ValueError("main section is absent from the edition-bound section contract")

    rows = []
    for link in soup.find_all("a", href=PAPER_HREF):
        item = link.find_parent("p")
        marker = link.find_previous("a", attrs={"name": True})
        if item is None or marker is None or marker.parent is None:
            raise ValueError("IFAAMAS paper link lacks a TOC item or section marker")
        section = " ".join(marker.parent.get_text(" ", strip=True).split())
        if section not in expected_sections:
            raise ValueError(f"unrecognized IFAAMAS section for {link['href']}: {section!r}")
        paper_title = " ".join(link.get_text(" ", strip=True).split())
        byline = item.find("font", attrs={"face": "Times New Roman"})
        authors = [
            " ".join(str(child).split())
            for child in (byline.children if byline else [])
            if isinstance(child, NavigableString) and str(child).strip()
        ]
        if not paper_title or not authors:
            raise ValueError(f"IFAAMAS TOC item lacks title or complete byline: {link['href']}")

        relative_path = PurePosixPath(link["href"])
        identifier = relative_path.stem
        official_url = urljoin(edition["official_index"], link["href"])
        included = section == main_section
        rows.append({
            "paper_id": f"paper:aamas:{year}:{identifier}",
            "official_record_id": identifier,
            "venue_id": "venue:aamas",
            "year": year,
            "title": paper_title,
            "authors": authors,
            "raw_authors": ", ".join(authors),
            "official_url": official_url,
            "pdf_url": official_url,
            "openreview_url": None,
            "track": "main" if included else "nonresearch",
            "track_section": section,
            "status": "included" if included else "excluded",
            "reason": "official_main_research_section" if included else "excluded_non_main_section",
            "source_url": source["url"],
            "source_sha256": source["sha256"],
            "retrieved_at": source["retrieved_at"],
            "source_locator": f"a[href='{link['href']}']; section={section!r}",
            "parser_version": VERSION,
        })

    if not rows:
        raise ValueError("IFAAMAS TOC contains no numeric paper PDF records")
    identifiers = [row["official_record_id"] for row in rows]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("duplicate IFAAMAS paper IDs; edition is not reconciled")
    observed_sections = Counter(row["track_section"] for row in rows)
    if dict(observed_sections) != edition["expected_section_counts"]:
        raise ValueError(
            "IFAAMAS section counts differ from the hash-bound edition contract: "
            f"{dict(observed_sections)}"
        )
    if sum(row["status"] == "included" for row in rows) != edition["expected_included"]:
        raise ValueError("IFAAMAS included-paper count differs from the edition contract")
    return sorted(rows, key=lambda row: row["paper_id"])


def reconcile_aamas_2023(accepted_body: bytes, contents_body: bytes) -> dict:
    """Return a reproducible exact-title/byline diagnostic for AAMAS 2023.

    This function does not construct a roster or infer matches. It counts only
    exact normalized title joins and leaves title variants for manual review.
    """
    accepted_soup = BeautifulSoup(accepted_body.decode("utf-8-sig"), "html.parser")
    contents_soup = BeautifulSoup(contents_body.decode("utf-8-sig"), "html.parser")

    def norm(value: str) -> str:
        return " ".join(unicodedata.normalize("NFKC", value).casefold().split())

    def compact_name(value: str) -> str:
        return "".join(char for char in norm(value) if char.isalnum())

    accepted_by_section = {}
    for heading in accepted_soup.find_all("h2"):
        label = " ".join(heading.get_text(" ", strip=True).split())
        if label not in {"Main Track: Full Papers", "Main Track: Extended Abstracts"}:
            continue
        entries = []
        for sibling in heading.find_next_siblings():
            if sibling.name == "h2":
                break
            if sibling.name != "p":
                continue
            author_element = sibling.find("em")
            text = sibling.get_text("\n", strip=True).split("\n")
            title = text[0].strip() if text else ""
            authors = author_element.get_text(" ", strip=True) if author_element else ""
            if not title or not authors:
                raise ValueError("AAMAS 2023 accepted-paper entry lacks title or byline")
            entries.append((title, authors))
        accepted_by_section[label] = entries

    contents_by_title = {}
    contents_count = 0
    for link in contents_soup.find_all("a", href=PAPER_HREF):
        item = link.find_parent("p")
        byline = item.find("font", attrs={"face": "Times New Roman"}) if item else None
        authors = [
            " ".join(str(child).split())
            for child in (byline.children if byline else [])
            if isinstance(child, NavigableString) and str(child).strip()
        ]
        title = " ".join(link.get_text(" ", strip=True).split())
        if not title or not authors:
            raise ValueError("AAMAS 2023 contents item lacks title or byline")
        contents_count += 1
        contents_by_title.setdefault(norm(title), []).append(authors)

    full_papers = accepted_by_section.get("Main Track: Full Papers", [])
    extended_abstracts = accepted_by_section.get("Main Track: Extended Abstracts", [])
    if not full_papers or not extended_abstracts:
        raise ValueError("AAMAS 2023 accepted page lacks a full-paper or abstract section")

    exact_matches = 0
    title_mismatches = 0
    byline_mismatches = 0
    ambiguous_matches = 0
    for title, raw_authors in full_papers:
        candidates = contents_by_title.get(norm(title), [])
        if not candidates:
            title_mismatches += 1
            continue
        if len(candidates) != 1:
            ambiguous_matches += 1
            continue
        exact_matches += 1
        expected_authors = [
            item.strip() for item in re.split(r",\s*|\s+and\s+", raw_authors) if item.strip()
        ]
        if [compact_name(item) for item in candidates[0]] != [
            compact_name(item) for item in expected_authors
        ]:
            byline_mismatches += 1

    return {
        "official_full_papers_listed": len(full_papers),
        "accepted_extended_abstracts_listed": len(extended_abstracts),
        "contents_pdf_records_observed": contents_count,
        "exact_normalized_title_joins_to_contents": exact_matches,
        "accepted_titles_without_exact_contents_match": title_mismatches,
        "exact_byline_mismatches_among_matched_titles": byline_mismatches,
        "ambiguous_exact_title_matches": ambiguous_matches,
        "reconciliation_method": (
            "NFKC, whitespace normalization, case-fold exact title join; author sequence "
            "compared after Unicode normalization and punctuation removal"
        ),
    }
