"""Add reconciled MICCAI accepted-paper rosters to the immutable v8 baseline."""

from collections import Counter
import json
from pathlib import Path
import re

from bs4 import BeautifulSoup

from scientific_network.collect.five_year_v2 import write_complete_manifest
from scientific_network.collect.miccai_v1 import parse_miccai_roster
from scientific_network.collect.reconcile import leakage_triage
from scientific_network.collect.source_closure_v8 import _load_v7, _read_verified
from scientific_network.collect.storage import digest, read_config, read_jsonl, write_json, write_jsonl

VERSION = "five-year-official-rosters-v9"
MICCAI_RESOLVED = {2021, 2023, 2025}
MICCAI_HELD = {2022, 2024}
MICCAI_SOURCE_IDS = {
    "miccai2021_accepted_list", "miccai2022_proceedings_page",
    "miccai2023_accepted_list", "miccai2024_open_access_list",
    "miccai2025_open_access_list", "miccai2025_final_update",
    "miccai_open_access_index", "springer2021_main_book",
    "springer2022_main_book", "springer2023_main_book",
    "springer2024_main_book", "springer2025_main_book",
    "springer_conference_index",
}


def _copy_immutable_tree(source: Path, target: Path) -> None:
    if not source.exists():
        return
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        destination = target / path.relative_to(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        raw = path.read_bytes()
        if destination.exists():
            if destination.read_bytes() != raw:
                raise ValueError(f"refusing to overwrite changed inherited roster: {destination}")
        else:
            destination.write_bytes(raw)


def _load_v8(config: dict) -> tuple[dict, list[dict], list[dict], list[dict], dict]:
    base = config["baseline"]
    config_path = Path(base["config_path"])
    _read_verified(config_path, base["config_sha256"], "v8 config")
    parent_config = read_config(config_path)
    if parent_config.get("workflow") != "five_year_source_closure_v8":
        raise ValueError("v9 requires the immutable source-closure v8 config")
    output = Path(base["output_dir"])
    summary_raw = _read_verified(output / "summary.json", base["summary_sha256"], "v8 summary")
    summary = json.loads(summary_raw)
    if summary.get("method_version") != "five-year-official-rosters-v8":
        raise ValueError("v9 requires the immutable v8 roster output")
    for name, expected in summary.get("output_sha256", {}).items():
        _read_verified(output / name, expected, "v8 output")
    _, _, _, membership, context = _load_v7(parent_config)
    rows = read_jsonl(output / "corpus_manifest.jsonl")
    ledger = read_jsonl(output / "edition-ledger.jsonl")
    if (len(rows) != summary.get("roster_records") or len(ledger) != 170
            or len({row["paper_id"] for row in rows}) != len(rows)):
        raise ValueError("v8 manifest or edition ledger is inconsistent")
    if len(membership) != summary.get("frozen_assignments_guarded"):
        raise ValueError("v8 frozen assignment count differs from inherited membership")
    return summary, rows, ledger, membership, {**context, "output": output}


def _source_text(sources: dict[str, dict], source_id: str) -> str:
    body = Path(sources[source_id]["snapshot_path"]).read_bytes()
    return " ".join(BeautifulSoup(body, "html.parser").get_text(" ", strip=True).split())


def _open_access_ids(sources: dict[str, dict], source_id: str, year: int) -> list[str]:
    body = Path(sources[source_id]["snapshot_path"]).read_bytes()
    soup = BeautifulSoup(body, "html.parser")
    path_patterns = {
        2021: re.compile(r"(?:^|/)2021/\d{2}/\d{2}/(\d+)-(Paper\d+)\.html$"),
        2023: re.compile(r"(?:^|/)2023/papers/(\d+)-(Paper\d+)\.html$"),
        2024: re.compile(r"(?:^|/)miccai-2024/(\d+)-(Paper\d+)\.html$"),
        2025: re.compile(r"(?:^|/)miccai-2025/(\d+)-(Paper\d+)\.html$"),
    }
    pattern = path_patterns[year]
    return [f"{match.group(1)}-{match.group(2)}"
            for link in soup.find_all("a", href=True)
            if (match := pattern.search(link["href"]))]


def _load_corrections(config: dict) -> tuple[dict, dict[str, dict], dict[int, dict]]:
    spec = config["source_corrections"]
    raw = _read_verified(Path(spec["path"]), spec["sha256"], "MICCAI source corrections")
    evidence = json.loads(raw)
    if (evidence.get("version") != "five-year-source-corrections-v7"
            or evidence.get("decision_id") != "D032"):
        raise ValueError("MICCAI correction identity mismatch")
    source_list = evidence.get("official_sources", [])
    sources = {item["source_id"]: item for item in source_list}
    if len(sources) != len(source_list) or set(sources) != MICCAI_SOURCE_IDS:
        raise ValueError("MICCAI correction must contain the exact hash-bound source capture set")
    for source_id, source in sources.items():
        if source.get("response_status") != 200 or "text/html" not in source.get("content_type", ""):
            raise ValueError(f"MICCAI capture is not a successful HTML response: {source_id}")
        source_path = Path(source["snapshot_path"])
        if "reports/runs/WORK-2026-11-07-004/" not in str(source_path):
            raise ValueError(f"MICCAI capture is outside the ignored task run directory: {source_id}")
        _read_verified(source_path, source["sha256"], source_id)

    dispositions = evidence.get("edition_dispositions", [])
    by_year = {int(item["year"]): item for item in dispositions}
    if len(by_year) != len(dispositions) or set(by_year) != MICCAI_RESOLVED | MICCAI_HELD:
        raise ValueError("MICCAI corrections must disposition each 2021–2025 edition once")
    for year in MICCAI_RESOLVED:
        item = by_year[year]
        if item.get("status") != "verified_eligible" or not item.get("evidence_source_ids"):
            raise ValueError(f"MICCAI {year} lacks an eligible-roster evidence contract")
    for year in MICCAI_HELD:
        item = by_year[year]
        if item.get("status") != "unresolved" or not item.get("evidence_source_ids"):
            raise ValueError(f"MICCAI {year} must remain unresolved with source evidence")

    count_contracts = {
        2021: ("miccai2021_accepted_list", "springer2021_main_book", 531, "531 revised full papers"),
        2022: (None, "springer2022_main_book", 574, "574 revised full papers"),
        2023: ("miccai2023_accepted_list", "springer2023_main_book", 730, "730 revised full papers"),
        2024: ("miccai2024_open_access_list", "springer2024_main_book", 857,
               "MICCAI accepted 857 full papers"),
        2025: ("miccai2025_open_access_list", "springer2025_main_book", 1027,
               "total of 1027 papers included in the proceedings"),
    }
    for year, (list_source_id, book_source_id, expected, book_phrase) in count_contracts.items():
        item = by_year[year]
        if (int(item.get("springer_full_paper_count", -1)) != expected
                or book_source_id not in item["evidence_source_ids"]):
            raise ValueError(f"MICCAI {year} Springer full-paper count contract mismatch")
        if book_phrase.casefold() not in _source_text(sources, book_source_id).casefold():
            raise ValueError(f"MICCAI {year} Springer book description no longer matches the count")

        list_count = item.get("accepted_roster_count")
        if list_source_id:
            if list_source_id not in item["evidence_source_ids"]:
                raise ValueError(f"MICCAI {year} correction omits its official accepted-list source")
            observed_ids = _open_access_ids(sources, list_source_id, year)
            if len(observed_ids) != list_count or len(set(observed_ids)) != len(observed_ids):
                raise ValueError(f"MICCAI {year} official list count does not match its captured page")
        elif list_count != 0:
            raise ValueError("MICCAI 2022 has no captured complete accepted-paper list")

        if year in MICCAI_RESOLVED:
            if (item.get("status") != "verified_eligible" or list_count != expected
                    or item.get("parser_expected_records") != expected):
                raise ValueError(f"MICCAI {year} eligible roster does not reconcile to Springer")
        elif item.get("status") != "unresolved":
            raise ValueError(f"MICCAI {year} must remain unresolved")

    if "1027 accepted papers" not in _source_text(sources, "miccai2025_final_update").casefold():
        raise ValueError("MICCAI 2025 final Society count is not captured")
    access_checks = evidence.get("access_checks", [])
    failed_list = [item for item in access_checks if item.get("source_id") == "miccai2022_papers"
                   and item.get("url") == "https://conferences.miccai.org/2022/papers/"
                   and item.get("response_status") == 522 and item.get("curl_exit_code") == 22
                   and item.get("response_bytes") == 16]
    if len(failed_list) != 1 or "springer2022_main_book" not in by_year[2022]["evidence_source_ids"]:
        raise ValueError("MICCAI 2022 accepted-list route failure must be explicitly recorded")

    if (by_year[2022].get("springer_full_paper_count") != 574
            or by_year[2022].get("springer_index_paper_count") != 576
            or by_year[2024].get("accepted_roster_count") != 856
            or by_year[2024].get("springer_full_paper_count") != 857
            or by_year[2024].get("springer_index_paper_count") != 857):
        raise ValueError("MICCAI unresolved count reconciliation changed")

    # Publisher-series index counts are recorded as catalog counters, separate
    # from the accepted-paper totals stated in the year-specific book pages.
    index_text = _source_text(sources, "springer_conference_index")
    for year, count in ((2021, 535), (2022, 576), (2023, 732), (2024, 857), (2025, 1029)):
        item = by_year[year]
        if item.get("springer_index_paper_count") != count:
            raise ValueError(f"MICCAI {year} publisher-index count changed")
        if not re.search(rf"MICCAI\s+{year}.{{0,220}}?\b{count}\s+Papers\b", index_text, re.I):
            raise ValueError(f"MICCAI {year} publisher-index counter is absent from the captured catalog")
    return evidence, sources, by_year


def discover_v9(config_path: Path, output: Path) -> dict:
    config = read_config(config_path)
    if (config.get("workflow") != "five_year_source_closure_v9"
            or config.get("collection_authorized") is not True
            or config.get("stage_boundary") != "official_rosters_only_no_enrichment_or_splits"):
        raise ValueError("v9 requires an authorized official-roster-only config")
    parent_summary, rows, ledger, membership, context = _load_v8(config)
    evidence, sources, dispositions = _load_corrections(config)
    row_by_edition = {(row["venue_id"], row["year"]): row for row in ledger}
    if any(row_by_edition[("venue:miccai", year)]["status"] != "unresolved"
           for year in range(2021, 2026)):
        raise ValueError("v9 can only update unresolved MICCAI edition rows")

    if (output / "summary.json").exists():
        saved = json.loads((output / "summary.json").read_text(encoding="utf-8"))
        if saved.get("config_sha256") != digest(config_path.read_bytes()):
            raise ValueError("v9 output belongs to a different config")
        for name, expected in saved["output_sha256"].items():
            _read_verified(output / name, expected, "v9 checkpoint")
        return saved
    if output.exists() and any(output.iterdir()):
        raise ValueError("partial v9 output exists without a verified summary; refusing to overwrite it")

    existing_ids = {row["paper_id"] for row in rows}
    included_rows = []
    output.mkdir(parents=True, exist_ok=True)
    _copy_immutable_tree(context["output"] / "editions", output / "editions")
    recorded_at = evidence["recorded_at"]
    for year in sorted(MICCAI_RESOLVED):
        disposition = dispositions[year]
        list_source_id = disposition["roster_source_id"]
        source_spec = sources[list_source_id]
        source = {"url": source_spec["url"], "sha256": source_spec["sha256"],
                  "retrieved_at": source_spec["accessed_at"], "license": "local_use_only_no_public_roster"}
        edition = {"venue_id": "venue:miccai", "year": year,
                   "official_index": source_spec["url"], "format": disposition["format"],
                   "expected_records": disposition["accepted_roster_count"]}
        body = Path(source_spec["snapshot_path"]).read_bytes()
        parsed = parse_miccai_roster(body, edition, source)
        if len(parsed) != disposition["accepted_roster_count"]:
            raise ValueError(f"MICCAI {year} parsed roster count differs from its evidence contract")
        if any(row["paper_id"] in existing_ids for row in parsed):
            raise ValueError(f"MICCAI {year} paper ID collides with the inherited corpus")

        directory = output / "editions" / "miccai" / str(year)
        write_jsonl(directory / "roster.jsonl", parsed)
        roster_hash = digest((directory / "roster.jsonl").read_bytes())
        item = row_by_edition[("venue:miccai", year)]
        evidence_sources = [sources[source_id] for source_id in disposition["evidence_source_ids"]]
        item.update(
            status="verified_eligible",
            reason="accepted_roster_matches_springer_full_paper_count",
            records=len(parsed),
            by_status={"included": len(parsed)},
            routes=[{"official_index": source_spec["url"], "format": disposition["format"],
                     "accepted_roster_complete": True, "track": "main_archival_research_papers"}],
            sources=evidence_sources,
            checked_at=recorded_at,
            method_version=VERSION,
            rights=disposition["rights_summary"],
            redistribution="local_ignored_only; public per-record metadata not authorized",
            publisher_index_paper_count=disposition["springer_index_paper_count"],
            accepted_full_paper_count=disposition["springer_full_paper_count"],
            roster_sha256=roster_hash,
        )
        write_json(directory / "summary.json", {
            "venue_id": "venue:miccai", "year": year, "status": "verified_eligible",
            "reason": item["reason"], "records": len(parsed), "by_status": item["by_status"],
            "routes": item["routes"], "sources": evidence_sources,
            "roster_sha256": roster_hash, "method_version": VERSION,
            "checked_at": recorded_at,
            "reviewer": "source_contract_and_count_reconciliation_not_independent_scientific_review",
            "rights": disposition["rights_summary"],
            "redistribution": item["redistribution"],
            "publisher_index_paper_count": item["publisher_index_paper_count"],
            "accepted_full_paper_count": item["accepted_full_paper_count"],
        })
        included_rows.extend(parsed)

    for year in sorted(MICCAI_HELD):
        disposition = dispositions[year]
        item = row_by_edition[("venue:miccai", year)]
        item.update(
            status="unresolved",
            reason=disposition["reason"],
            records=0,
            routes=[{"official_index": disposition["official_index"],
                     "status": "unresolved_roster_count_or_access"}],
            sources=[sources[source_id] for source_id in disposition["evidence_source_ids"]],
            source_reconciliation={key: value for key, value in disposition.items()
                                   if key not in {"year", "status", "reason", "evidence_source_ids"}},
            checked_at=recorded_at,
            method_version=VERSION,
            rights=disposition["rights_summary"],
            redistribution="local_ignored_only; public per-record metadata not authorized",
        )

    rows.extend(included_rows)
    rows.sort(key=lambda row: row["paper_id"])
    if len({row["paper_id"] for row in rows}) != len(rows):
        raise ValueError("v9 corpus contains duplicate paper IDs")
    if len(membership) != parent_summary["frozen_assignments_guarded"]:
        raise ValueError("v9 changed frozen assignment cardinality")
    write_complete_manifest(output / "corpus_manifest.parquet", rows)
    write_jsonl(output / "edition-ledger.jsonl", ledger)
    triage = leakage_triage(rows, context["history"], membership,
                            method_version="five-year-leakage-triage-v9")
    write_jsonl(output / "leakage-triage.jsonl", triage)

    eligible = {(row["venue_id"], row["year"]) for row in ledger
                if row["status"] == "verified_eligible"}
    files = ["corpus_manifest.jsonl", "corpus_manifest-complete.parquet",
             "edition-ledger.jsonl", "leakage-triage.jsonl"]
    files.extend(str(path.relative_to(output)) for path in sorted((output / "editions").rglob("*.json*")))
    summary = {
        "stage": "discover", "method_version": VERSION,
        "config_sha256": digest(config_path.read_bytes()),
        "source_corrections_sha256": digest(Path(config["source_corrections"]["path"]).read_bytes()),
        "scope": "2021-2025 official_rosters_only",
        "candidate_editions": len(ledger), "roster_records": len(rows),
        "records_by_status": dict(Counter(row["status"] for row in rows)),
        "edition_statuses": dict(Counter(row["status"] for row in ledger)),
        "by_year": dict(Counter(str(row["year"]) for row in rows)),
        "eligible_included_records": sum(row["status"] == "included"
                                          and (row["venue_id"], row["year"]) in eligible for row in rows),
        "incomplete_editions": sum(row["status"] not in {"verified_eligible", "verified_no_edition", "excluded_track"}
                                    for row in ledger),
        "review_required": sum(row["status"] == "review" for row in rows),
        "manifest_sha256": digest((output / "corpus_manifest.jsonl").read_bytes()),
        "edition_ledger_sha256": digest((output / "edition-ledger.jsonl").read_bytes()),
        "parent_method_version": parent_summary["method_version"],
        "parent_manifest_sha256": parent_summary["manifest_sha256"],
        "parent_edition_ledger_sha256": parent_summary["edition_ledger_sha256"],
        "frozen_assignments_guarded": len(membership),
        "protected_test_assignments": sum(item["split"] == "test" for item in membership),
        "leakage_actions": dict(Counter(item["action"] for item in triage)),
        "new_splits_created": 0, "canonical_works_merged": 0,
        "semantic_accuracy": "not_measured", "enrichment_requests": 0, "graph_writes": 0,
        "pdfs_downloaded": 0, "public_per_record_roster": False,
        "enrichment_authorized_by_this_output": False,
        "graph_construction_authorized": False,
        "output_sha256": {name: digest((output / name).read_bytes()) for name in files},
    }
    write_json(output / "summary.json", summary)
    return summary
