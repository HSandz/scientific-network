"""Versioned parsers for official MICCAI accepted-paper listings."""

from __future__ import annotations

from hashlib import sha256
from pathlib import PurePosixPath
import re
import unicodedata
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

VERSION = "miccai-official-rosters-v1"


def _field(entry: str, name: str) -> str:
    match = re.search(rf"(?im)^\s*{re.escape(name)}\s*=\s*", entry)
    if not match:
        raise ValueError(f"MICCAI BibTeX entry is missing {name}")
    pos = match.end()
    if pos >= len(entry):
        raise ValueError(f"MICCAI BibTeX {name} value is empty")
    if entry[pos] == "{":
        start = pos + 1
        depth = 1
        escaped = False
        for index in range(start, len(entry)):
            char = entry[index]
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    value = entry[start:index]
                    break
        else:
            raise ValueError(f"MICCAI BibTeX {name} value has unbalanced braces")
    elif entry[pos] == '"':
        start = pos + 1
        end = entry.find('"', start)
        if end < 0:
            raise ValueError(f"MICCAI BibTeX {name} value has no closing quote")
        value = entry[start:end]
    else:
        end = entry.find(",", pos)
        value = entry[pos:end if end >= 0 else len(entry)].strip()
    return " ".join(value.split())


def _strip_outer_braces(value: str) -> str:
    value = value.strip()
    while value.startswith("{") and value.endswith("}"):
        depth = 0
        closes_at_end = False
        for index, char in enumerate(value):
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    closes_at_end = index == len(value) - 1
                    break
        if not closes_at_end:
            break
        value = value[1:-1].strip()
    return value


def _normalize_title(value: str) -> str:
    value = unicodedata.normalize("NFKC", _strip_outer_braces(value))
    value = value.replace("\u00a0", " ")
    return " ".join(value.split()).casefold()


def _bibtex_record(block: str) -> dict:
    if not re.match(r"\s*@InProceedings\s*\{", block, re.I):
        raise ValueError("MICCAI list contains a non-proceedings BibTeX block")
    title = _strip_outer_braces(_field(block, "title"))
    author_value = _strip_outer_braces(_field(block, "author"))
    authors = [" ".join(item.split()) for item in re.split(r"\s+AND\s+", author_value, flags=re.I)
               if item.strip()]
    year = _field(block, "year")
    booktitle = _strip_outer_braces(_field(block, "booktitle"))
    volume = _strip_outer_braces(_field(block, "volume"))
    if not title or not authors:
        raise ValueError("MICCAI BibTeX paper is missing title or authors")
    return {"title": title, "authors": authors, "year": year,
            "booktitle": booktitle, "volume": volume,
            "raw_authors": author_value}


def _record(edition: dict, source: dict, identifier: str, title: str,
            authors: list[str], locator: str, official_url: str) -> dict:
    venue_id, year = edition["venue_id"], int(edition["year"])
    return {
        "paper_id": f"paper:miccai:{year}:{identifier}",
        "official_record_id": identifier,
        "venue_id": venue_id,
        "year": year,
        "title": title,
        "authors": authors,
        "raw_authors": ", ".join(authors),
        "official_url": official_url,
        "pdf_url": None,
        "openreview_url": None,
        "track": "main",
        "status": "included",
        "reason": "official_accepted_main_conference_roster",
        "source_url": source["url"],
        "source_sha256": source["sha256"],
        "retrieved_at": source["retrieved_at"],
        "source_locator": locator,
        "parser_version": VERSION,
    }


def parse_miccai_roster(body: bytes, edition: dict, source: dict) -> list[dict]:
    """Parse a full accepted-paper list; reject gaps, duplicates, or scope drift."""
    year = int(edition["year"])
    expected = int(edition["expected_records"])
    fmt = edition["format"]
    if year not in {2021, 2023, 2025} or expected < 1:
        raise ValueError("unsupported MICCAI edition contract")
    if sha256(body).hexdigest() != source["sha256"]:
        raise ValueError("MICCAI input does not match its captured source hash")
    soup = BeautifulSoup(body, "html.parser")
    rows = []

    if fmt == "accepted_list":
        if year == 2021:
            pattern = re.compile(rf"(?:^|/)2021/09/01/(\d{{3}})-(Paper\d+)\.html$")
        elif year == 2023:
            pattern = re.compile(r"^/2023/papers/(\d+)-(Paper\d+)\.html$")
        else:
            raise ValueError("MICCAI accepted_list format is only defined for 2021 and 2023")
        observed = []
        for link in soup.find_all("a", href=pattern):
            match = pattern.search(link["href"])
            ordinal = int(match.group(1))
            article_id = match.group(2)
            title = link.get_text(" ", strip=True)
            if not title:
                raise ValueError("MICCAI accepted-paper entry has an empty title")
            identifier = PurePosixPath(urlsplit(link["href"]).path).stem
            official_url = urljoin(edition["official_index"], link["href"])
            locator = f"a[href='{link['href']}']"
            observed.append((ordinal, article_id, title, identifier, official_url, locator))
        if len(observed) != expected:
            raise ValueError(f"MICCAI {year} list count {len(observed)} != expected {expected}")
        ordinals = [item[0] for item in observed]
        if sorted(ordinals) != list(range(1, expected + 1)):
            raise ValueError(f"MICCAI {year} list sequence has gaps or duplicate positions")
        if len({item[1] for item in observed}) != expected:
            raise ValueError(f"MICCAI {year} list repeats a submission record ID")
        rows = [_record(edition, source, identifier, title, [], locator, official_url)
                for _, _, title, identifier, official_url, locator in sorted(observed)]

    elif fmt == "bibtex_list" and year == 2025:
        pattern = re.compile(r"^/miccai-2025/(\d+)-(Paper\d+)\.html$")
        observed = []
        for link in soup.find_all("a", href=pattern):
            node = link.find_parent("div", class_="posts-list-item")
            bib_strings = [str(item) for item in node.find_all(string=lambda value: value and "@InProceedings" in value)] if node else []
            if len(bib_strings) != 1:
                raise ValueError("MICCAI 2025 paper entry must contain exactly one BibTeX record")
            record = _bibtex_record(bib_strings[0])
            if record["year"] != str(year):
                raise ValueError("MICCAI BibTeX year disagrees with the accepted-list edition")
            if f"MICCAI {year}" not in record["booktitle"]:
                raise ValueError("MICCAI BibTeX booktitle does not identify the main conference")
            volume_match = re.fullmatch(r"LNCS\s+(\d+)", record["volume"])
            if not volume_match or not 15960 <= int(volume_match.group(1)) <= 15975:
                raise ValueError("MICCAI BibTeX volume is outside the 2025 main-conference set")
            normalized_entry = _normalize_title(node.get_text(" ", strip=True))
            if normalized_entry.count(_normalize_title(record["title"])) < 2:
                raise ValueError("MICCAI BibTeX title does not match its accepted-paper entry")
            match = pattern.fullmatch(urlsplit(link["href"]).path)
            identifier = f"{match.group(1)}-{match.group(2)}"
            official_url = urljoin(edition["official_index"], link["href"])
            record["official_url"] = official_url
            record["source_locator"] = f"a[href='{link['href']}']"
            observed.append((identifier, record))
        if len(observed) != expected:
            raise ValueError(f"MICCAI 2025 list count {len(observed)} != expected {expected}")
        ids = [identifier for identifier, _ in observed]
        ordinals = [int(identifier.split("-", 1)[0]) for identifier in ids]
        if sorted(ordinals) != list(range(1, expected + 1)) or len(set(ids)) != expected:
            raise ValueError("MICCAI 2025 list has gaps, duplicate positions, or repeated records")
        rows = [_record(edition, source, identifier, record["title"], record["authors"],
                        record["source_locator"], record["official_url"])
                for identifier, record in sorted(observed)]
    else:
        raise ValueError(f"unsupported MICCAI source format for {year}: {fmt}")

    if len({row["paper_id"] for row in rows}) != len(rows):
        raise ValueError("MICCAI roster contains duplicate paper IDs")
    return rows
