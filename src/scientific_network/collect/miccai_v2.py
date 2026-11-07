"""MICCAI 2024 Society-list parsing and Springer chapter reconciliation."""

from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
import re
import unicodedata
from urllib.parse import parse_qs, urljoin, urlsplit

from bs4 import BeautifulSoup

from scientific_network.collect.miccai_v1 import _bibtex_record

VERSION = "miccai-2024-society-roster-v1"
PAPER_LINK = re.compile(r"^/miccai-2024/(\d+)-(Paper\d+)\.html$")
SPRINGER_CHAPTER = re.compile(r"/chapter/10\.1007/978-3-031-\d+-\d+_\d+$")
VOLUME_EISBNS = {
    "I": "978-3-031-72378-0", "II": "978-3-031-72069-7",
    "III": "978-3-031-72384-1", "IV": "978-3-031-72083-3",
    "V": "978-3-031-72086-4", "VI": "978-3-031-72089-5",
    "VII": "978-3-031-72104-5", "VIII": "978-3-031-72111-3",
    "IX": "978-3-031-72114-4", "X": "978-3-031-72117-5",
    "XI": "978-3-031-72120-5", "XII": "978-3-031-72390-2",
}
VOLUME_LNCS = {
    "I": 15001, "II": 15002, "III": 15003, "IV": 15004,
    "V": 15005, "VI": 15006, "VII": 15007, "VIII": 15008,
    "IX": 15009, "X": 15010, "XI": 15011, "XII": 15012,
}


def _norm(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).replace("\u00a0", " ")
    return " ".join(value.split()).casefold()


def _person_parts(value: str) -> tuple[str, str]:
    folded = "".join(
        char for char in unicodedata.normalize("NFKD", _norm(value))
        if not unicodedata.combining(char)
    )
    parts = re.findall(r"[a-z0-9]+", folded)
    return (parts[0], parts[-1]) if parts else ("", "")


def _given_first_name(value: str) -> str:
    if "," not in value:
        return " ".join(value.split())
    family, given = value.split(",", 1)
    return " ".join(f"{given.strip()} {family.strip()}".split())


def parse_miccai2024_society_roster(body: bytes, edition: dict, source: dict) -> list[dict]:
    """Parse the complete official 2024 Society list with its full BibTeX bylines."""
    year = int(edition["year"])
    expected = int(edition["expected_records"])
    if year != 2024 or expected < 1:
        raise ValueError("MICCAI Society-list parser is defined only for edition 2024")
    if sha256(body).hexdigest() != source["sha256"]:
        raise ValueError("MICCAI 2024 Society input does not match its captured hash")

    soup = BeautifulSoup(body, "html.parser")
    records = []
    submission_ids = []
    for card in soup.select("div.posts-list-item"):
        links = [link for link in card.find_all("a", href=True)
                 if PAPER_LINK.fullmatch(link["href"])]
        bibtex = [str(node) for node in card.find_all(
            string=lambda value: value and "@InProceedings" in value
        )]
        if not links and not bibtex:
            continue
        if len(links) != 1 or len(bibtex) != 1:
            raise ValueError("MICCAI 2024 Society item must have one paper link and one BibTeX entry")

        match = PAPER_LINK.fullmatch(links[0]["href"])
        record_id = f"{match.group(1)}-{match.group(2)}"
        submission_ids.append(match.group(2))
        item = _bibtex_record(bibtex[0])
        if item["year"] != "2024" or "MICCAI 2024" not in item["booktitle"]:
            raise ValueError("MICCAI 2024 Society BibTeX entry has the wrong edition")
        volume = re.fullmatch(r"LNCS\s+(\d+)", item["volume"])
        if not volume or not 15001 <= int(volume.group(1)) <= 15012:
            raise ValueError("MICCAI 2024 Society entry is outside main-proceedings volumes")
        records.append({
            "paper_id": f"paper:miccai:2024:{record_id}",
            "official_record_id": record_id,
            "venue_id": "venue:miccai",
            "year": 2024,
            "publisher_volume": int(volume.group(1)),
            "title": item["title"],
            "authors": item["authors"],
            "raw_authors": item["raw_authors"],
            "official_url": urljoin(edition["official_index"], links[0]["href"]),
            "pdf_url": None,
            "openreview_url": None,
            "track": "main",
            "status": "included",
            "reason": "official_society_accepted_main_research_roster",
            "source_url": source["url"],
            "source_sha256": source["sha256"],
            "retrieved_at": source["retrieved_at"],
            "source_locator": f"div.posts-list-item > a[href='{links[0]['href']}']",
            "parser_version": VERSION,
        })

    if len(records) != expected:
        raise ValueError(f"MICCAI 2024 Society roster has {len(records)} records, expected {expected}")
    ids = [item["official_record_id"] for item in records]
    ordinals = sorted(int(item.split("-", 1)[0]) for item in ids)
    if len(set(ids)) != expected or ordinals != list(range(1, expected + 1)):
        raise ValueError("MICCAI 2024 Society roster has duplicate IDs or ordinal gaps")
    if len(set(submission_ids)) != expected:
        raise ValueError("MICCAI 2024 Society roster repeats a submission ID")
    paper_ids = [item["paper_id"] for item in records]
    if len(set(paper_ids)) != expected:
        raise ValueError("MICCAI 2024 Society roster has duplicate stable paper IDs")
    return sorted(records, key=lambda item: item["paper_id"])


def parse_miccai2024_springer_pages(pages: list[tuple[int, bytes, dict]]) -> list[dict]:
    """Parse all chapter cards from captured, edition-bound Springer TOC pages."""
    rows = []
    observed_pages: dict[str, set[int]] = defaultdict(set)
    for page_number, body, source in pages:
        if sha256(body).hexdigest() != source["sha256"]:
            raise ValueError("MICCAI 2024 Springer page hash mismatch")
        soup = BeautifulSoup(body, "html.parser")
        page_title = soup.title.get_text(" ", strip=True) if soup.title else ""
        title_match = re.search(r"Proceedings, Part ([IVX]+)", page_title)
        if "MICCAI 2024" not in page_title or not title_match:
            raise ValueError("Springer page title does not identify a MICCAI 2024 main volume")
        volume_roman = title_match.group(1)
        volume_match = re.search(r"978-3-031-\d+-\d+", source["url"])
        if not volume_match:
            raise ValueError("Springer source URL lacks an eISBN")
        eisbn = volume_match.group(0)
        if VOLUME_EISBNS.get(volume_roman) != eisbn:
            raise ValueError("Springer volume title and eISBN do not agree")
        query_page = parse_qs(urlsplit(source["url"]).query).get("page", ["1"])[0]
        if query_page != str(page_number):
            raise ValueError("Springer TOC page number disagrees with its source URL")
        observed_pages[eisbn].add(int(page_number))

        for link in soup.find_all("a", href=SPRINGER_CHAPTER):
            card = link.find_parent("div", class_="app-card-open")
            if card is None:
                raise ValueError("Springer chapter link lacks its publisher card")
            title = " ".join(link.get_text(" ", strip=True).split())
            authors = [
                " ".join(author.split())
                for item in card.select("ul.app-author-list li")
                for author in item.get_text(" ", strip=True).split(",")
                if author.strip()
            ]
            if not title or not authors or any(not item for item in authors):
                raise ValueError("Springer chapter card is missing a title or byline")
            doi = link["href"].split("/chapter/", 1)[1]
            if not doi.startswith(f"10.1007/{eisbn}_"):
                raise ValueError("Springer chapter DOI does not belong to its source volume")
            rows.append({
                "doi": doi,
                "title": title,
                "authors": authors,
                "eisbn": eisbn,
                "volume_roman": volume_roman,
                "publisher_volume": VOLUME_LNCS[volume_roman],
                "source_id": source["source_id"],
                "source_sha256": source["sha256"],
                "source_locator": f"a[href='{link['href']}']",
            })

    expected_pages = {
        eisbn: list(range(1, 6 if roman == "I" else 5))
        for roman, eisbn in VOLUME_EISBNS.items()
    }
    if (set(observed_pages) != set(VOLUME_EISBNS.values())
            or any(sorted(observed_pages[eisbn]) != expected_pages[eisbn]
                   for eisbn in expected_pages)):
        raise ValueError("Springer MICCAI 2024 capture must include every page for 12 volumes")
    dois = [item["doi"] for item in rows]
    if len(dois) != len(set(dois)):
        raise ValueError("Springer MICCAI 2024 capture repeats chapter DOIs")
    return sorted(rows, key=lambda item: item["doi"])


def _springer_name_keys(authors: list[str]) -> list[tuple[str, str]]:
    """Return normalized first/last name keys, omitting a displayed et-al marker."""
    values = list(authors)
    if values and _norm(values[-1]).rstrip(".") in {"et al", "and others"}:
        values.pop()
    result = []
    for value in values:
        result.append(_person_parts(value))
    return result


def reconcile_miccai2024_rosters(society: list[dict], springer: list[dict]) -> dict:
    """Reconcile accepted Society papers to publisher chapters and classify extras."""
    by_title: dict[str, list[dict]] = defaultdict(list)
    for item in springer:
        by_title[_norm(item["title"])].append(item)

    used_dois: set[str] = set()
    exact = 0
    unresolved = []
    for item in society:
        candidates = by_title[_norm(item["title"])]
        if (len(candidates) == 1 and candidates[0]["doi"] not in used_dois
                and candidates[0]["publisher_volume"] == item["publisher_volume"]):
            used_dois.add(candidates[0]["doi"])
            exact += 1
        else:
            unresolved.append(item)

    fuzzy = 0
    for item in unresolved:
        society_authors = [_person_parts(_given_first_name(name)) for name in item["authors"]]
        candidates = []
        for publisher in springer:
            if publisher["doi"] in used_dois:
                continue
            if publisher["publisher_volume"] != item["publisher_volume"]:
                continue
            publisher_names = _springer_name_keys(publisher["authors"])
            compare_count = min(3, len(society_authors), len(publisher_names))
            if compare_count == 0:
                continue
            if any(society_authors[index] != publisher_names[index]
                   for index in range(compare_count)):
                continue
            ratio = _title_similarity(item["title"], publisher["title"])
            if ratio >= 0.85:
                candidates.append((ratio, publisher))
        candidates.sort(key=lambda pair: pair[0], reverse=True)
        if len(candidates) != 1:
            return {
                "society_records": len(society), "springer_chapters": len(springer),
                "exact_title_matches": exact, "unique_title_and_byline_matches": fuzzy,
                "unresolved_society_records": len(unresolved) - fuzzy,
                "publisher_only_records": len(springer) - len(used_dois),
                "complete": False,
            }
        used_dois.add(candidates[0][1]["doi"])
        fuzzy += 1

    publisher_only = [item for item in springer if item["doi"] not in used_dois]
    correction = [item for item in publisher_only
                  if _norm(item["title"]).startswith("correction to:")]
    correction_original_matches = False
    if len(correction) == 1:
        original_title = re.sub(r"(?i)^correction\s+to:\s*", "", correction[0]["title"]).strip()
        matched_originals = [item for item in society if _norm(item["title"]) == _norm(original_title)]
        original_dois = [publisher["doi"] for item in matched_originals
                         for publisher in by_title[_norm(item["title"])]
                         if publisher["doi"] in used_dois
                         and publisher["publisher_volume"] == correction[0]["publisher_volume"]]
        correction_original_matches = len(matched_originals) == 1 and len(original_dois) == 1
    return {
        "society_records": len(society),
        "springer_chapters": len(springer),
        "unique_springer_chapters": len({item["doi"] for item in springer}),
        "exact_title_matches": exact,
        "unique_title_and_byline_matches": fuzzy,
        "unresolved_society_records": len(unresolved) - fuzzy,
        "publisher_only_records": len(publisher_only),
        "publisher_only_corrections": len(correction),
        "correction_matches_a_society_original": correction_original_matches,
        "complete": (
            len(unresolved) == fuzzy and len(publisher_only) == 1 and len(correction) == 1
            and correction_original_matches
        ),
        "correction": correction[0] if len(correction) == 1 else None,
    }


def _title_similarity(left: str, right: str) -> float:
    from difflib import SequenceMatcher

    return SequenceMatcher(None, _norm(left), _norm(right)).ratio()
