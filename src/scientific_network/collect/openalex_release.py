"""Release acquisition: roster papers to OpenAlex works by DOI (D040, release plan Phase 2).

Official roster papers for the release scope (AAAI and IJCAI, 2021-2025) are matched to
OpenAlex works through the DOI derived from the official URL, never by title search.
Requests go through ``SourceCache`` so every response is immutable, hashed and resumable.
A work is accepted only when its normalized title agrees (similarity at least 0.9, with a
flag below 1.0) and its authorship count equals the official byline length; everything
else goes to review with a reason. This module identifies works only; researcher and
affiliation decisions are made later from the stored authorships.
"""

from collections import Counter, defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
import hashlib
import json
import math
import os
from pathlib import Path
import re
import unicodedata
from urllib.parse import quote

from dotenv import load_dotenv
import httpx

from scientific_network.collect.storage import (
    QuotaError, SourceCache, SourceError, digest, read_config, write_json, write_jsonl,
)

METHOD_VERSION = "release-openalex-v1"
ROSTER_FIELDS = (
    "title", "authors", "official_url", "pdf_url", "official_record_id", "issue_series",
    "source_url", "source_sha256", "retrieved_at", "source_locator",
)
_AAAI_ISSUE = re.compile(r"^Vol\. (\d+) No\. (\d+)$")
_AAAI_ARTICLE = re.compile(r"^https://ojs\.aaai\.org/index\.php/AAAI/article/view/(\d+)$")
_IJCAI_URL = re.compile(r"^https://www\.ijcai\.org/proceedings/(\d{4})/(\d+)$")


# --- DOI derivation -----------------------------------------------------------------------------


def derive_doi(row: dict) -> str:
    """The DOI implied by an official roster row, or ValueError when it cannot be derived safely."""
    venue, url = row.get("venue_id"), str(row.get("official_url") or "")
    if venue == "venue:aaai":
        issue = _AAAI_ISSUE.match(str(row.get("issue_series") or "").strip())
        article = _AAAI_ARTICLE.match(url)
        record = str(row.get("official_record_id") or "")
        if not issue or not article or not record.isdigit() or article[1] != record:
            raise ValueError(f"cannot derive an AAAI DOI for {row.get('paper_id')}")
        return f"10.1609/aaai.v{issue[1]}i{issue[2]}.{record}"
    if venue == "venue:ijcai":
        match = _IJCAI_URL.match(url)
        if not match or int(match[1]) != row.get("year"):
            raise ValueError(f"cannot derive an IJCAI DOI for {row.get('paper_id')}")
        return f"10.24963/ijcai.{match[1]}/{match[2]}"
    raise ValueError(f"no DOI rule for venue {venue!r}")


def normalize_doi(value) -> str:
    text = str(value or "").strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "doi:"):
        if text.startswith(prefix):
            text = text[len(prefix):]
    return text


# --- matching -----------------------------------------------------------------------------------


def normalize_title(text) -> str:
    text = re.sub(r"<[^>]+>", " ", str(text or ""))
    return re.sub(r"[\W_]+", "", unicodedata.normalize("NFKC", text).casefold())


def title_similarity(left, right) -> float:
    a, b = normalize_title(left), normalize_title(right)
    if not a or not b:
        return 0.0
    return 1.0 if a == b else SequenceMatcher(None, a, b, autojunk=False).ratio()


def _normalize_url(value) -> str:
    text = re.sub(r"^https?://(www\.)?", "", str(value or "").strip().lower())
    return text.rstrip("/")


def _landing_page(work: dict) -> str:
    return (work.get("primary_location") or {}).get("landing_page_url") or ""


def _author_ids(work: dict) -> list[str | None]:
    return [(item.get("author") or {}).get("id") for item in work.get("authorships") or []]


def reconstruct_abstract(inverted_index) -> str | None:
    """Rebuild abstract text from OpenAlex's word-to-positions index; None when absent."""
    if not isinstance(inverted_index, dict) or not inverted_index:
        return None
    positions: dict[int, str] = {}
    for word, places in inverted_index.items():
        for place in places or []:
            positions.setdefault(int(place), word)
    return " ".join(positions[index] for index in sorted(positions)) or None


def _agrees(row: dict, work: dict, title_accept: float) -> bool:
    return (title_similarity(row["title"], work.get("title")) >= title_accept
            and len(work.get("authorships") or []) == len(row["authors"]))


def evaluate_match(row: dict, candidates: list[dict], title_accept: float = 0.9) -> dict:
    """Apply the release work-match rule to the works OpenAlex returned for one derived DOI.

    OpenAlex sometimes keeps two records for one DOI: one crawled from the official page and
    one merged from Crossref and arXiv. Among duplicates that pass the title and author-count
    checks, the single record whose landing page is the roster's official URL is chosen and the
    others are kept as alternates; anything else stays in review as ``duplicate_doi_works``.
    """
    if not candidates:
        return {"status": "not_found", "reasons": ["no_openalex_work_for_doi"], "flags": [], "chosen": None}
    chosen, flags, extra = 0, [], {}
    if len(candidates) > 1:
        agreeing = [i for i, work in enumerate(candidates) if _agrees(row, work, title_accept)]
        linked = [i for i in agreeing if _normalize_url(_landing_page(candidates[i])) == _normalize_url(row["official_url"])]
        if len(linked) != 1:
            return {"status": "review", "reasons": ["duplicate_doi_works"], "flags": [], "chosen": None,
                    "candidate_count": len(candidates),
                    "candidate_ids": [work.get("id") for work in candidates]}
        chosen = linked[0]
        flags.append("duplicate_doi_resolved_by_official_landing_page")
        others = [work for i, work in enumerate(candidates) if i != chosen]
        extra = {"alternate_work_ids": [work.get("id") for work in others],
                 "duplicate_author_ids_agree": all(_author_ids(work) == _author_ids(candidates[chosen]) for work in others)}
    work = candidates[chosen]
    similarity = title_similarity(row["title"], work.get("title"))
    official_count, openalex_count = len(row["authors"]), len(work.get("authorships") or [])
    reasons = []
    if similarity < title_accept:
        reasons.append("title_mismatch")
    elif similarity < 1.0:
        flags.append("title_similarity_below_1")
    if official_count != openalex_count:
        reasons.append("author_count_mismatch")
    return {
        "status": "review" if reasons else "matched",
        "reasons": reasons, "flags": flags, "chosen": chosen, "candidate_count": len(candidates),
        "title_similarity": round(similarity, 4),
        "author_count_official": official_count, "author_count_openalex": openalex_count, **extra,
    }


# --- scope --------------------------------------------------------------------------------------


def load_scope(config: dict, root: Path = Path(".")) -> list[dict]:
    """Roster rows in release scope with their derived DOIs; fails on any inconsistency."""
    scope, roster = config["scope"], config["roster"]
    manifest = root / roster["manifest"]
    raw = manifest.read_bytes()
    if digest(raw) != roster["sha256"]:
        raise ValueError("roster manifest does not match the sha256 pinned in the release config")
    venues, years = set(scope["venues"]), set(scope["years"])
    rows = []
    for line in raw.decode("utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("status") == scope["roster_status"] and row.get("venue_id") in venues and row.get("year") in years:
            rows.append(row)
    seen: dict[str, str] = {}
    for row in rows:
        row["_doi"] = derive_doi(row)
        if row["_doi"] in seen:
            raise ValueError(f"duplicate derived DOI {row['_doi']}: {seen[row['_doi']]} and {row['paper_id']}")
        seen[row["_doi"]] = row["paper_id"]
        if not row.get("title") or not row.get("authors"):
            raise ValueError(f"roster row {row['paper_id']} lacks a title or byline")
    ids = [row["paper_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate paper_id in release scope")
    counts = Counter((row["venue_id"], row["year"]) for row in rows)
    expected = {(venue, int(year)): n for venue, by_year in scope["expected_papers_by_venue_year"].items()
                for year, n in by_year.items()}
    if len(rows) != scope["expected_papers"] or dict(counts) != expected:
        raise ValueError(f"release scope has {len(rows)} papers, expected {scope['expected_papers']} (counts per venue-year differ)")
    return sorted(rows, key=lambda row: row["paper_id"])


# --- OpenAlex access ----------------------------------------------------------------------------


def rate_limit_preflight(client: httpx.Client, key: str, base_url: str) -> dict:
    """Read the allowance and per-endpoint costs. Only numeric fields are kept, never the key echo."""
    try:
        response = client.get(f"{base_url}/rate-limit", params={"api_key": key}, timeout=20)
    except httpx.RequestError as exc:
        raise SourceError("OpenAlex rate-limit preflight: " + type(exc).__name__) from None
    if response.status_code != 200:
        raise QuotaError(f"OpenAlex rate-limit preflight HTTP {response.status_code}")
    limit = response.json().get("rate_limit", {})
    costs = limit.get("endpoint_costs_usd", {})
    summary = {
        "daily_budget_usd": limit.get("daily_budget_usd"),
        "daily_used_usd": limit.get("daily_used_usd"),
        "daily_remaining_usd": limit.get("daily_remaining_usd"),
        "credits_remaining": limit.get("credits_remaining"),
        "list_cost_usd": costs.get("list"),
        "singleton_cost_usd": costs.get("singleton"),
        "list_cost_credits": limit.get("credit_costs", {}).get("list"),
        "resets_at": limit.get("resets_at"),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
    numeric = ("daily_remaining_usd", "list_cost_usd", "singleton_cost_usd")
    if not all(isinstance(summary[name], (int, float)) and summary[name] >= 0 for name in numeric) or summary["list_cost_usd"] <= 0:
        raise ValueError("unknown OpenAlex allowance contract; cannot authorize requests")
    return summary


def authorize(preflight: dict, batches: int, attempts: int) -> dict:
    """Stop if the worst-case cost of the batch requests exceeds what the allowance has left."""
    worst_case = batches * attempts * preflight["list_cost_usd"]
    credits = preflight.get("credits_remaining")
    credit_cost = preflight.get("list_cost_credits")
    if worst_case > preflight["daily_remaining_usd"]:
        raise QuotaError(f"worst-case batch cost ${worst_case:.4f} exceeds the remaining allowance ${preflight['daily_remaining_usd']}")
    if isinstance(credits, (int, float)) and isinstance(credit_cost, (int, float)) and batches * attempts * credit_cost > credits:
        raise QuotaError("worst-case batch credits exceed the remaining credits")
    return {"worst_case_batch_cost_usd": round(worst_case, 6), "batches": batches, "attempts_assumed": attempts}


def _results(body: bytes) -> tuple[list[dict], int]:
    data = json.loads(body)
    return list(data.get("results") or []), int((data.get("meta") or {}).get("count", 0))


class Fetcher:
    """Batch and singleton lookups through the immutable cache, tracking what hit the network."""

    def __init__(self, cache: SourceCache, base_url: str, key: str, select: list[str], run_started: str):
        self.cache, self.base_url, self.key = cache, base_url, key
        self.select, self.run_started = ",".join(select), run_started
        self.requests = Counter()

    def _get(self, kind: str, url: str, params: dict) -> tuple[bytes, dict]:
        body, record = self.cache.get(url, params=params, secret_params={"api_key": self.key})
        self.requests[kind + ("_cached" if record["retrieved_at"] < self.run_started else "_network")] += 1
        return body, record

    def batch(self, dois: list[str], per_page: int) -> list[tuple[dict, dict, str]]:
        """Works for a DOI batch as (work, source record, locator); follows pages if the count overflows."""
        found: list[tuple[dict, dict, str]] = []
        page = 1
        while True:
            params = {"filter": "doi:" + "|".join(dois), "per_page": per_page, "select": self.select}
            if page > 1:
                params["page"] = page
            body, record = self._get("batch", f"{self.base_url}/works", params)
            results, count = _results(body)
            found.extend((work, record, f"results[{index}]" + ("" if page == 1 else f"@page{page}"))
                         for index, work in enumerate(results))
            if len(found) >= count or not results:
                return found
            page += 1

    def singleton(self, doi: str) -> list[tuple[dict, dict, str]]:
        try:
            body, record = self._get("singleton", f"{self.base_url}/works/doi:{quote(doi, safe='/:')}", {"select": self.select})
        except SourceError as exc:
            if exc.status_code == 404:
                self.requests["singleton_not_found"] += 1  # a 404 is a real request and is never cached
                return []
            raise
        return [(json.loads(body), record, "$")]


# --- orchestration ------------------------------------------------------------------------------


def _source_view(record: dict, locator: str) -> dict:
    return {"request_id": record["request_id"], "url": record["url"], "params": record["params"],
            "retrieved_at": record["retrieved_at"], "raw_sha256": record["sha256"], "locator": locator}


def _works_row(row: dict, match: dict, found: list[tuple[dict, dict, str]]) -> dict:
    out = {
        "paper_id": row["paper_id"], "venue_id": row["venue_id"], "year": row["year"], "track": row["track"],
        "doi": row["_doi"], "roster": {name: row.get(name) for name in ROSTER_FIELDS}, "match": match, "openalex": None,
    }
    chosen = match.get("chosen")
    if found and chosen is not None:
        work, record, locator = found[chosen]
        out["openalex"] = {
            "id": work.get("id"), "doi": work.get("doi"), "title": work.get("title"),
            "publication_year": work.get("publication_year"), "type": work.get("type"),
            "landing_page_url": _landing_page(work) or None,
            "authorships": work.get("authorships") or [],
            "referenced_works": work.get("referenced_works") or [],
            "abstract": reconstruct_abstract(work.get("abstract_inverted_index")),
            "source": _source_view(record, locator),
        }
        if len(found) > 1:
            out["openalex"]["alternates"] = [
                {"id": other.get("id"), "type": other.get("type"), "landing_page_url": _landing_page(other) or None,
                 "author_ids": _author_ids(other), "referenced_works_count": len(other.get("referenced_works") or [])}
                for i, (other, _, _) in enumerate(found) if i != chosen]
    elif found:       # unresolved duplicates: keep a compact view for review, never as accepted evidence
        out["review_candidates"] = [
            {"id": work.get("id"), "title": work.get("title"), "type": work.get("type"),
             "landing_page_url": _landing_page(work) or None, "author_ids": _author_ids(work)}
            for work, _, _ in found]
    return out


def _tally(rows: list[dict]) -> dict:
    by_key: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        key = f"{row['venue_id']}:{row['year']}"
        by_key[key]["papers"] += 1
        by_key[key][row["match"]["status"]] += 1
        if "title_similarity_below_1" in row["match"]["flags"]:
            by_key[key]["matched_with_title_flag"] += 1
    return {key: {**counts, "match_rate": round(counts["matched"] / counts["papers"], 4)} for key, counts in sorted(by_key.items())}


def acquire(config_path: Path, *, works_path: Path | None = None, report_path: Path | None = None,
            limit: int | None = None, preflight_only: bool = False, root: Path = Path("."),
            cache: SourceCache | None = None, client: httpx.Client | None = None) -> dict:
    """Run the release acquisition. With ``limit`` or ``preflight_only`` nothing is written to disk."""
    config = read_config(config_path)
    if config.get("version") != "release-v1":
        raise ValueError("release acquisition requires configs/release-v1.yaml")
    settings, paths = config["openalex"], config["paths"]
    works_path = works_path or root / paths["works"]
    report_path = report_path or root / paths["acquisition_report"]
    if (works_path.exists() or report_path.exists()) and not (limit or preflight_only):
        raise ValueError("release acquisition outputs already exist; remove them deliberately to rebuild")
    rows = load_scope(config, root)
    if limit:
        rows = rows[:limit]
    load_dotenv(override=False)
    key = os.environ.get(settings["api_key_env"], "")
    if not key:
        raise ValueError(f"{settings['api_key_env']} must be set in the environment or the ignored .env")

    size = settings["batch_size"]
    batches = [rows[start:start + size] for start in range(0, len(rows), size)]
    own_client = client is None
    client = client or httpx.Client(timeout=30)
    run_started = datetime.now(timezone.utc).isoformat()
    try:
        preflight = rate_limit_preflight(client, key, settings["base_url"])
        attempts = 4
        authorization = authorize(preflight, len(batches), attempts)
        if preflight_only:
            return {"stage": "release-acquire", "status": "preflight_only", "papers": len(rows),
                    "preflight": preflight, "authorization": authorization, "output_written": False}
        own_cache = cache is None
        cache = cache or SourceCache(root / paths["cache_dir"], attempts=attempts)
        try:
            fetcher = Fetcher(cache, settings["base_url"], key, settings["select"], run_started)
            by_doi: dict[str, list] = defaultdict(list)
            wanted = {row["_doi"] for row in rows}
            for batch in batches:
                for work, record, locator in fetcher.batch([row["_doi"] for row in batch], size):
                    doi = normalize_doi(work.get("doi"))
                    if doi in wanted:
                        by_doi[doi].append((work, record, locator))
            retried = 0
            if settings["singleton_retry"]:
                for row in rows:
                    if row["_doi"] not in by_doi:
                        retried += 1
                        by_doi[row["_doi"]].extend(fetcher.singleton(row["_doi"]))
        finally:
            if own_cache:
                cache.__exit__()
        accept = config["matching"]["title_similarity_accept"]
        out = []
        for row in rows:
            found = by_doi.get(row["_doi"], [])
            match = evaluate_match(row, [item[0] for item in found], accept)
            out.append(_works_row(row, match, found))
        after = rate_limit_preflight(client, key, settings["base_url"])
    finally:
        if own_client:
            client.close()

    status_counts = Counter(row["match"]["status"] for row in out)
    reasons = Counter(reason for row in out for reason in row["match"]["reasons"])
    flagged = sum("title_similarity_below_1" in row["match"]["flags"] for row in out)
    resolved = [r["match"] for r in out if "duplicate_doi_resolved_by_official_landing_page" in r["match"]["flags"]]
    report = {
        "stage": "release-acquire", "method_version": METHOD_VERSION, "config_version": config["version"],
        "config_sha256": digest(config_path.read_bytes()), "roster_sha256": config["roster"]["sha256"],
        "run_started_at": run_started, "completed_at": datetime.now(timezone.utc).isoformat(),
        "papers": len(out), "matched": status_counts["matched"], "matched_with_title_flag": flagged,
        "review": status_counts["review"], "not_found": status_counts["not_found"],
        "match_rate": round(status_counts["matched"] / len(out), 4),
        "failure_reasons": dict(sorted(reasons.items())),
        "duplicate_doi_works": {
            "resolved_by_official_landing_page": len(resolved),
            "resolved_with_differing_author_ids": sum(not m["duplicate_author_ids_agree"] for m in resolved),
            "left_in_review": sum("duplicate_doi_works" in r["match"]["reasons"] for r in out)},
        "by_venue_year": _tally(out),
        "publication_year_differs_from_roster": sum(
            bool(r["openalex"]) and r["openalex"]["publication_year"] != r["year"] for r in out),
        "with_abstract": sum(bool(r["openalex"] and r["openalex"]["abstract"]) for r in out if r["match"]["status"] == "matched"),
        "requests": dict(sorted(fetcher.requests.items())), "singleton_retries": retried,
        "allowance": {"before": preflight, "worst_case_authorized": authorization, "after": after,
                      "used_this_run_usd": round((after["daily_used_usd"] or 0) - (preflight["daily_used_usd"] or 0), 6)},
        "openalex_select": settings["select"], "works_sha256": None,
    }
    if limit:
        return {**report, "status": "trial_not_written", "output_written": False}
    write_jsonl(works_path, out)
    report["works_sha256"] = hashlib.sha256(works_path.read_bytes()).hexdigest()
    write_json(report_path, report)
    return {**report, "status": "written", "output_written": True, "works": str(works_path), "report": str(report_path)}
