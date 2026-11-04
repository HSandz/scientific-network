"""Metadata-first pilot acquisition, strict work matching and resumable records."""

from collections import Counter
import json
import os
from pathlib import Path
from urllib.parse import urljoin
import re
import unicodedata

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from scientific_network.collect.storage import (SourceCache, SourceError, QuotaError, digest,
    read_config, read_jsonl, write_json, write_table)

VERSION = "pilot-acquire-v5-visible-byline-unicode"


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower())


def name_tokens(value: str) -> list[str]:
    # Retain non-Latin scripts. ASCII transliteration erased entire Chinese names.
    decomposed = unicodedata.normalize("NFKD", value).casefold()
    text = "".join(c for c in decomposed if not unicodedata.combining(c))
    return sorted(re.findall(r"[^\W_]+", text))


def names_compatible(left: str, right: str) -> bool:
    a, b = name_tokens(left), name_tokens(right)
    return bool(a and b) and a == b


def official_metadata(body: bytes, row: dict) -> dict:
    soup = BeautifulSoup(body, "html.parser")
    if row.get("parser_version", "").startswith("official-roster-families-") and row["official_url"].endswith(".pdf"):
        return dict(title=row["title"], authors=row["authors"], year=row["year"], abstract="",
            pdf_url=row["official_url"], doi=None, title_locator=row["source_locator"],
            author_locator=row["source_locator"] + ";adjacent_official_byline", abstract_locator="unavailable",
            title_from_roster=True, authors_from_roster=True)
    metas = {}
    for tag in soup.select('meta[name^="citation_"]'):
        metas.setdefault(tag["name"], []).append(tag.get("content", ""))
    title = metas.get("citation_title", [row["title"]])[0]
    if normalize(title) != normalize(row["title"]):
        raise ValueError("official index/detail title mismatch")
    authors = metas.get("citation_author", row["authors"])
    author_locator = "meta[name=citation_author]"
    authors_from_roster = "citation_author" not in metas
    citation_authors = [" ".join(reversed(n.split(", ", 1))) if ", " in n else n
                        for n in metas.get("citation_author", [])]
    byline_discrepancies = []
    if row.get("venue_id") in {"venue:acl", "venue:eacl", "venue:emnlp"}:
        # The article's visible publication byline is distinct from citation-export
        # names, which may carry expanded initials or newer profile-name variants.
        visible = soup.select("p.lead")
        bylines = [p for p in visible if p.select('a[href^="/people/"]')]
        if len(bylines) > 1:
            raise ValueError("ambiguous ACL visible article byline")
        if bylines:
            authors = [a.get_text(" ", strip=True) for a in bylines[0].select('a[href^="/people/"]')]
            author_locator, authors_from_roster = 'p.lead a[href^="/people/"]', False
            if citation_authors != authors:
                byline_discrepancies = [{"source": "citation_author", "authors": citation_authors},
                                       {"source": "visible_article_byline", "authors": authors}]
    if row.get("venue_id") == "venue:miccai" and "citation_author" not in metas:
        heading = soup.select_one("#author-id")
        paragraph = heading.find_next_sibling("p") if heading else None
        authors = [n.strip() for n in paragraph.get_text(" ", strip=True).split(",") if n.strip()] if paragraph else []
        author_locator, authors_from_roster = "#author-id + p;comma_separated_byline", False
        title_element = soup.select_one(".post-title")
        if title_element and normalize(title_element.get_text(" ", strip=True)) != normalize(row["title"]):
            raise ValueError("MICCAI title/detail mismatch")
    authors = [" ".join(reversed(name.split(", ", 1))) if ", " in name else name for name in authors]
    if not authors:
        raise ValueError("official detail has no authoritative byline")
    if row.get("parser_version", "").startswith("official-roster-families-") and row["authors"] and (
        len(authors) != len(row["authors"]) or not all(names_compatible(a, b) for a, b in zip(authors, row["authors"]))
    ):
        raise ValueError("official roster/detail byline mismatch")
    abstract = soup.select_one("#abstract, .paper-abstract, .abstract, .acl-abstract > span")
    abstract_locator = "#abstract, .paper-abstract, .abstract, .acl-abstract > span"
    if abstract is None and row.get("venue_id") == "venue:ijcai":
        abstract = soup.select_one(".article__abstract p:not(.eyebrow)")
        abstract_locator = ".article__abstract p:not(.eyebrow)"
    if abstract is None and row.get("venue_id") == "venue:kr":
        heading = soup.find("h2", string="Abstract")
        abstract = heading.find_next_sibling("div") if heading else None
        abstract_locator = "h2[text=Abstract] + div"
    if abstract is None and row.get("venue_id") == "venue:rss":
        heading = soup.find("b", string="Abstract:")
        abstract = heading.parent.find_next_sibling("p") if heading else None
        abstract_locator = "b[text=Abstract:]/parent::p/following-sibling::p[1]"
    if abstract is None and row.get("venue_id") == "venue:miccai":
        heading = soup.select_one("#abstract-id")
        abstract = heading.find_next_sibling("p") if heading else None
        abstract_locator = "#abstract-id + p"
    abstract_text = abstract.get_text(" ", strip=True) if abstract else ""
    pdf_url = metas.get("citation_pdf_url", [row.get("pdf_url")])[0]
    if not pdf_url:
        link = soup.find("a", href=lambda h: h and h.lower().endswith(".pdf") and "supp" not in h.lower())
        pdf_url = urljoin(row["official_url"], link["href"]) if link else None
    return {"title": title, "authors": authors, "abstract": abstract_text,
        "pdf_url": pdf_url, "year": row["year"],
        "title_from_roster": "citation_title" not in metas,
        "authors_from_roster": authors_from_roster,
        "title_locator": "meta[name=citation_title]" if "citation_title" in metas else row["source_locator"],
        "author_locator": row["source_locator"] + ";adjacent_official_byline" if authors_from_roster else author_locator,
        "citation_authors": citation_authors,
        "byline_discrepancies": byline_discrepancies,
        "doi": metas.get("citation_doi", [None])[0],
        "abstract_locator": abstract_locator if abstract is not None else "unavailable"}


def choose_work(candidates: list[dict], paper: dict, official_url: str) -> tuple[dict | None, str]:
    eligible = []
    for work in candidates:
        authorships = work.get("authorships", [])
        if normalize(work.get("title") or "") != normalize(paper["title"]):
            continue
        if work.get("publication_year") not in {paper.get("year", 2023) + delta for delta in (-1, 0, 1)}:
            continue
        if len(authorships) != len(paper["authors"]) or not all(
            names_compatible(name, (authorship.get("author") or {}).get("display_name", ""))
            for name, authorship in zip(paper["authors"], authorships)
        ):
            continue
        doi = (work.get("doi") or "").lower().removeprefix("https://doi.org/")
        score = 2 if paper.get("doi") and doi == paper["doi"].lower() else 0
        if any(location.get("landing_page_url") == official_url for location in work.get("locations", [])):
            score += 1
        eligible.append((score, work))
    if not eligible:
        return None, "no_exact_title_year_complete_ordered_byline_match"
    best_score = max(score for score, _ in eligible)
    best = [work for score, work in eligible if score == best_score]
    if len(best) != 1:
        return None, "ambiguous_work_candidates"
    return best[0], "exact_title_year_complete_ordered_byline" + ("_identifier_corroborated" if best_score else "_version_match")


def acquire(manifest: Path, membership: Path, output: Path, cache_path: Path, config_path: Path,
            previous: Path | None = None) -> dict:
    load_dotenv(override=False)
    splits_summary = json.loads((membership.parent / "summary.json").read_text())
    config = read_config(config_path)
    if splits_summary["corpus_config_sha256"] != digest(config_path.read_bytes()):
        raise ValueError("corpus configuration differs from the frozen split configuration")
    if splits_summary["manifest_sha256"] != digest(manifest.read_bytes()):
        raise ValueError("frozen splits do not match this manifest")
    if splits_summary["membership_sha256"] != digest(membership.read_bytes()):
        raise ValueError("frozen split membership has changed")
    assignments = read_jsonl(membership)
    test_groups = {r["leakage_group"] for r in assignments if r["split"] == "test"}
    if any(r["is_pilot"] and (r["split"] not in {"development", "pool"} or r["leakage_group"] in test_groups) for r in assignments):
        raise ValueError("held-out test paper cannot be acquired for the development pilot")
    pilot_ids = {r["paper_id"] for r in assignments if r["is_pilot"]}
    by_id = {row["paper_id"]: row for row in read_jsonl(manifest)}
    if not pilot_ids or not pilot_ids <= by_id.keys():
        raise ValueError("pilot membership missing from manifest")
    signature = {"manifest_sha256": digest(manifest.read_bytes()),
        "membership_sha256": digest(membership.read_bytes()), "method_version": VERSION}
    previous_records = {}
    if previous:
        previous_inputs = json.loads((previous.parent / "inputs.json").read_text())
        if any(previous_inputs.get(k) != signature[k] for k in ("manifest_sha256", "membership_sha256")):
            raise ValueError("previous acquisition does not match the frozen manifest/membership")
        prior = json.loads(previous.read_text())
        if len({r["paper_id"] for r in prior}) != len(prior) or {r["paper_id"] for r in prior} != pilot_ids:
            raise ValueError("previous acquisition has duplicate or missing diagnostic IDs")
        previous_records = {r["paper_id"]: r for r in prior if r.get("status") == "acquired"}
        if any(r.get("roster") != by_id[pid] for pid, r in previous_records.items()):
            raise ValueError("previous acquisition differs from the frozen roster")
        signature["previous_sha256"] = digest(previous.read_bytes())
    write_json(output / "inputs.json", signature)
    reused = {}
    if config.get("legacy_acquisition"):
        legacy_path = Path(config["legacy_acquisition"])
        if digest(legacy_path.read_bytes()) != config["legacy_acquisition_sha256"]:
            raise ValueError("legacy acquisition hash mismatch")
        reused = {r["paper_id"]: r for r in json.loads(legacy_path.read_text())}
    records = []
    key = os.environ.get("OPENALEX_API_KEY", "")
    with SourceCache(cache_path, delay=0.25, timeout=config["retrieval"]["timeout_seconds"],
                     attempts=config["retrieval"]["max_attempts"]) as cache:
        for index, paper_id in enumerate(sorted(pilot_ids), 1):
            path = output / "records" / f"{digest(paper_id.encode())}.json"
            if path.exists():
                records.append(json.loads(path.read_text()))
                continue
            row = by_id[paper_id]
            if paper_id in reused:
                record = reused[paper_id]
                if record["roster"] != row or record.get("status") != "acquired":
                    raise ValueError("legacy acquisition no longer matches official manifest")
                write_json(path, record)
                records.append(record)
                continue
            if paper_id in previous_records:
                record = previous_records[paper_id]
                write_json(path, record)
                records.append(record)
                continue
            try:
                request_stage = "official"
                body, source = cache.get(row["source_url"] if row["official_url"].endswith(".pdf") else row["official_url"])
                paper = official_metadata(body, row)
                request_stage = "openalex"
                data, oa_source = cache.get("https://api.openalex.org/works",
                    params={"search": paper["title"].replace("*", " "), "filter": f"publication_year:{row["year"] - 1}-{row["year"] + 1}", "per_page": 5},
                    secret_params={"api_key": key} if key else {})
                candidates = json.loads(data).get("results", [])
                work, decision = choose_work(candidates, paper, row["official_url"])
                record = {"paper_id": paper_id, "roster": row, "official": paper,
                    "official_source": source, "openalex_work": work,
                    "openalex_source": oa_source, "match_decision": decision,
                    "candidate_ids": [w["id"] for w in candidates], "status": "acquired",
                    "acquisition_method_version": VERSION}
                write_json(path, record)
                records.append(record)
            except QuotaError as exc:
                if request_stage != "official" or "429" in str(exc):
                    raise  # Keep successful records; resume after the API allowance clears.
                failure = {"paper_id": paper_id, "status": "failed", "reason": str(exc)}
                write_json(output / "failures" / path.name, failure)
                records.append(failure)
            except (SourceError, ValueError) as exc:
                failure = {"paper_id": paper_id, "status": "failed", "reason": str(exc)}
                write_json(output / "failures" / path.name, failure)
                records.append(failure)
            if index % 10 == 0:
                print(f"acquire: {index}/{len(pilot_ids)} pilot records", flush=True)
    write_json(output / "papers.json", records)
    matches = [r for r in records if r.get("openalex_work")]
    acquired = [r for r in records if r["status"] == "acquired"]
    summary = {"stage": "acquire", **signature, "pilot_papers": len(pilot_ids),
        "acquired": len(acquired), "failed": len(records) - len(acquired), "work_matches": len(matches),
        "abstracts_available": sum(bool(r["official"]["abstract"]) for r in acquired),
        "match_decisions": dict(Counter(r.get("match_decision", "failed") for r in records)),
        "by_venue": dict(Counter(r["roster"]["venue_id"] for r in acquired)),
        "openalex_key_used": bool(key), "held_out_papers_acquired": 0,
        "previous_acquired_reused": len(previous_records),
        "identity_status": "requires_independent_identity_and_affiliation_resolution"}
    write_json(output / "summary.json", summary)
    return summary
