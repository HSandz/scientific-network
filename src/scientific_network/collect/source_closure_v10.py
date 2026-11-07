"""Reconcile MICCAI 2024 accepted papers and its Springer correction chapter."""

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scientific_network.collect.five_year_v2 import write_complete_manifest
from scientific_network.collect.miccai_v2 import (
    parse_miccai2024_society_roster,
    parse_miccai2024_springer_pages,
    reconcile_miccai2024_rosters,
)
from scientific_network.collect.reconcile import leakage_triage
from scientific_network.collect.source_closure_v9 import _read_verified, _source_text
from scientific_network.collect.storage import digest, read_config, read_jsonl, write_json, write_jsonl

VERSION = "five-year-official-rosters-v10"
SOCIETY_SOURCE_ID = "miccai2024_open_access_list"
SPRINGER_INDEX_SOURCE_ID = "springer_conference_index"
SPRINGER_PAGE_PREFIX = "springer_miccai2024_"
PARENT_VERSION = "five-year-official-rosters-v9"
PARENT_CONFIG_VERSION = "five_year_source_closure_v9"
EXPECTED_VOLUME_CHAPTERS = {
    "978-3-031-72378-0": 72,
    "978-3-031-72069-7": 71,
    "978-3-031-72384-1": 72,
    "978-3-031-72083-3": 73,
    "978-3-031-72086-4": 71,
    "978-3-031-72089-5": 70,
    "978-3-031-72104-5": 75,
    "978-3-031-72111-3": 69,
    "978-3-031-72114-4": 69,
    "978-3-031-72117-5": 70,
    "978-3-031-72120-5": 73,
    "978-3-031-72390-2": 72,
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


def _load_v9(config: dict) -> tuple[dict, list[dict], list[dict], list[dict], dict]:
    baseline = config["baseline"]
    config_path = Path(baseline["config_path"])
    _read_verified(config_path, baseline["config_sha256"], "v9 config")
    parent_config = read_config(config_path)
    if parent_config.get("workflow") != PARENT_CONFIG_VERSION:
        raise ValueError("v10 requires the immutable source-closure v9 config")
    output = Path(baseline["output_dir"])
    summary = json.loads(_read_verified(output / "summary.json", baseline["summary_sha256"], "v9 summary"))
    if summary.get("method_version") != PARENT_VERSION:
        raise ValueError("v10 requires the immutable v9 roster output")
    for name, expected in summary.get("output_sha256", {}).items():
        _read_verified(output / name, expected, "v9 output")

    # Reopen the v8 lineage for its frozen membership and historical-work context.
    from scientific_network.collect.source_closure_v9 import _load_v8

    _, _, _, membership, context = _load_v8(parent_config)
    rows = read_jsonl(output / "corpus_manifest.jsonl")
    ledger = read_jsonl(output / "edition-ledger.jsonl")
    if (len(rows) != summary.get("roster_records") or len(ledger) != 170
            or len({row["paper_id"] for row in rows}) != len(rows)):
        raise ValueError("v9 manifest or edition ledger is inconsistent")
    if len(membership) != summary.get("frozen_assignments_guarded"):
        raise ValueError("v9 frozen assignment count differs from inherited membership")
    return summary, rows, ledger, membership, {**context, "output": output}


def _load_corrections(config: dict) -> tuple[dict, dict[str, dict]]:
    spec = config["source_corrections"]
    raw = _read_verified(Path(spec["path"]), spec["sha256"], "MICCAI 2024 source corrections")
    evidence = json.loads(raw)
    if evidence.get("version") != "five-year-source-corrections-v8" or evidence.get("decision_id") != "D033":
        raise ValueError("MICCAI 2024 source-correction identity mismatch")

    inherited = evidence.get("inherited_correction", {})
    inherited_path = Path(inherited.get("path", ""))
    _read_verified(inherited_path, inherited.get("sha256", ""), "D032 source corrections")
    inherited_evidence = json.loads(inherited_path.read_text(encoding="utf-8"))
    if inherited_evidence.get("version") != "five-year-source-corrections-v7":
        raise ValueError("D033 must preserve the immutable D032 source corrections")

    source_list = evidence.get("official_sources", [])
    sources = {item["source_id"]: item for item in source_list}
    if len(sources) != len(source_list):
        raise ValueError("duplicate source IDs in MICCAI 2024 correction")
    pages = [item for item in source_list if item["source_id"].startswith(SPRINGER_PAGE_PREFIX)]
    expected_ids = {SOCIETY_SOURCE_ID, SPRINGER_INDEX_SOURCE_ID}
    if len(pages) != 49 or set(sources) != expected_ids | {item["source_id"] for item in pages}:
        raise ValueError("MICCAI 2024 correction must bind the Society/index sources and 49 TOC pages")

    for source_id, source in sources.items():
        if source.get("response_status") != 200 or "text/html" not in source.get("content_type", ""):
            raise ValueError(f"MICCAI 2024 source is not a successful HTML capture: {source_id}")
        path = Path(source["snapshot_path"])
        if source_id.startswith(SPRINGER_PAGE_PREFIX):
            if "reports/runs/WORK-2026-11-07-006/" not in str(path):
                raise ValueError(f"Springer TOC capture is outside the ignored task run directory: {source_id}")
        elif "reports/runs/WORK-2026-11-07-004/" not in str(path):
            raise ValueError(f"inherited MICCAI source path is not the recorded v9 input: {source_id}")
        _read_verified(path, source["sha256"], source_id)

    disposition = evidence.get("edition_disposition", {})
    if (disposition.get("venue_id") != "venue:miccai" or disposition.get("year") != 2024
            or disposition.get("status") != "verified_eligible"
            or disposition.get("accepted_society_records") != 856
            or disposition.get("springer_main_volume_chapter_records") != 857
            or disposition.get("excluded_correction_records") != 1):
        raise ValueError("MICCAI 2024 disposition does not match the reconciled source contract")

    expected_counts = evidence.get("springer_chapters_by_volume", {})
    if expected_counts != EXPECTED_VOLUME_CHAPTERS:
        raise ValueError("MICCAI 2024 volume counts differ from the frozen source contract")
    if evidence.get("reconciliation_metrics") != {
        "society_records": 856,
        "springer_chapters": 857,
        "unique_springer_chapters": 857,
        "exact_title_matches": 836,
        "unique_title_and_byline_matches": 20,
        "unresolved_society_records": 0,
        "publisher_only_records": 1,
        "publisher_only_corrections": 1,
        "correction_matches_a_society_original": True,
        "complete": True,
    }:
        raise ValueError("MICCAI 2024 reconciliation metrics changed")

    society_source = sources[SOCIETY_SOURCE_ID]
    body = Path(society_source["snapshot_path"]).read_bytes()
    society_rows = parse_miccai2024_society_roster(
        body,
        {"year": 2024, "expected_records": 856, "official_index": society_source["url"]},
        {"url": society_source["url"], "sha256": society_source["sha256"],
         "retrieved_at": society_source["accessed_at"]},
    )

    page_specs = sorted(pages, key=lambda item: (item["volume_eisbn"], item["toc_page"]))
    parsed_pages = [
        (item["toc_page"], Path(item["snapshot_path"]).read_bytes(), item)
        for item in page_specs
    ]
    springer_rows = parse_miccai2024_springer_pages(parsed_pages)
    chapter_counts = dict(Counter(item["eisbn"] for item in springer_rows))
    if chapter_counts != EXPECTED_VOLUME_CHAPTERS:
        raise ValueError("MICCAI 2024 Springer chapter counts do not match all 12 volumes")

    metrics = reconcile_miccai2024_rosters(society_rows, springer_rows)
    observed_metrics = {key: metrics[key] for key in evidence["reconciliation_metrics"]}
    if observed_metrics != evidence["reconciliation_metrics"] or not metrics["complete"]:
        raise ValueError("MICCAI 2024 accepted-paper roster did not fully reconcile")

    description = _source_text(sources, pages[0]["source_id"])
    if "12-volume set lncs 15001 - 15012" not in description.casefold():
        raise ValueError("Springer volume page lacks the 12-volume main-proceedings description")
    if "miccai accepted 857 full papers" not in description.casefold():
        raise ValueError("Springer volume page no longer contains the 857-paper count statement")
    index_text = _source_text(sources, SPRINGER_INDEX_SOURCE_ID)
    if not re.search(r"MICCAI\s+2024.{0,220}?\b857\s+Papers\b.{0,80}?\b12\s+Volumes\b", index_text, re.I):
        raise ValueError("Springer series index does not distinguish 857 main volume chapters from workshops")

    evidence["_society_rows"] = society_rows
    evidence["_springer_rows"] = springer_rows
    evidence["_metrics"] = metrics
    return evidence, sources


def discover_v10(config_path: Path, output: Path) -> dict:
    config = read_config(config_path)
    if (config.get("workflow") != "five_year_source_closure_v10"
            or config.get("collection_authorized") is not True
            or config.get("stage_boundary") != "official_rosters_only_no_enrichment_or_splits"):
        raise ValueError("v10 requires an authorized official-roster-only config")
    parent_summary, rows, ledger, membership, context = _load_v9(config)
    evidence, sources = _load_corrections(config)
    edition_key = ("venue:miccai", 2024)
    row_by_edition = {(item["venue_id"], item["year"]): item for item in ledger}
    if row_by_edition[edition_key]["status"] != "unresolved":
        raise ValueError("v10 can only update an unresolved MICCAI 2024 edition")

    if (output / "summary.json").exists():
        saved = json.loads((output / "summary.json").read_text(encoding="utf-8"))
        if saved.get("config_sha256") != digest(config_path.read_bytes()):
            raise ValueError("v10 output belongs to a different config")
        for name, expected in saved["output_sha256"].items():
            _read_verified(output / name, expected, "v10 checkpoint")
        return saved
    if output.exists() and any(output.iterdir()):
        raise ValueError("partial v10 output exists without a verified summary; refusing to overwrite it")

    output.mkdir(parents=True, exist_ok=True)
    _copy_immutable_tree(context["output"] / "editions", output / "editions")
    correction_at = evidence["recorded_at"]
    disposition = evidence["edition_disposition"]
    society_spec = sources[SOCIETY_SOURCE_ID]
    society_rows = evidence.pop("_society_rows")
    springer_rows = evidence.pop("_springer_rows")
    metrics = evidence.pop("_metrics")
    # Publisher volume is used to validate every crosswalk; the public-facing
    # roster contract does not add a new per-record publisher field.
    for item in society_rows:
        item.pop("publisher_volume", None)

    correction_chapter = metrics["correction"]
    correction_source = sources[correction_chapter["source_id"]]
    correction_record = {
        "paper_id": f"paper:miccai:2024:correction:{correction_chapter['doi'].replace('/', ':')}",
        "official_record_id": correction_chapter["doi"],
        "venue_id": "venue:miccai",
        "year": 2024,
        "title": correction_chapter["title"],
        "authors": correction_chapter["authors"],
        "raw_authors": ", ".join(correction_chapter["authors"]),
        "official_url": urljoin("https://link.springer.com", f"/chapter/{correction_chapter['doi']}"),
        "pdf_url": None,
        "openreview_url": None,
        "track": "nonresearch",
        "status": "excluded",
        "reason": "publisher_correction_notice_not_main_research_paper",
        "source_url": correction_source["url"],
        "source_sha256": correction_source["sha256"],
        "retrieved_at": correction_source["accessed_at"],
        "source_locator": correction_chapter["source_locator"],
        "parser_version": VERSION,
    }
    parsed_rows = [*society_rows, correction_record]
    existing_ids = {item["paper_id"] for item in rows}
    if any(item["paper_id"] in existing_ids for item in parsed_rows):
        raise ValueError("MICCAI 2024 paper ID collides with the inherited v9 roster")

    directory = output / "editions" / "miccai" / "2024"
    write_jsonl(directory / "roster.jsonl", parsed_rows)
    roster_hash = digest((directory / "roster.jsonl").read_bytes())
    disposition_sources = [society_spec, sources[SPRINGER_INDEX_SOURCE_ID], *sorted(
        (item for item in sources.values() if item["source_id"].startswith(SPRINGER_PAGE_PREFIX)),
        key=lambda item: item["source_id"],
    )]
    row = row_by_edition[edition_key]
    row.update(
        status="verified_eligible",
        reason="complete_society_research_roster_reconciles_to_12_springer_volumes",
        records=len(parsed_rows),
        by_status=dict(Counter(item["status"] for item in parsed_rows)),
        routes=[{"official_index": society_spec["url"],
                 "track": "main_archival_research_papers",
                 "accepted_society_records": 856,
                 "publisher_chapters": 857,
                 "excluded_publisher_correction_records": 1,
                 "springer_main_volumes": 12,
                 "accepted_roster_complete": True}],
        sources=disposition_sources,
        checked_at=correction_at,
        method_version=VERSION,
        source_reconciliation=disposition["count_reconciliation"],
        rights=disposition["rights_summary"],
        redistribution="local_ignored_only; public per-record metadata not authorized",
        roster_sha256=roster_hash,
    )
    write_json(directory / "summary.json", {
        "venue_id": "venue:miccai", "year": 2024, "status": "verified_eligible",
        "reason": row["reason"], "records": len(parsed_rows), "by_status": row["by_status"],
        "routes": row["routes"], "sources": disposition_sources,
        "roster_sha256": roster_hash, "method_version": VERSION,
        "checked_at": correction_at,
        "reviewer": "source-contract-and-count-reconciliation-not-independent-scientific-review",
        "rights": row["rights"], "redistribution": row["redistribution"],
        "source_reconciliation": disposition["count_reconciliation"],
    })
    rows.extend(parsed_rows)
    rows.sort(key=lambda item: item["paper_id"])
    if len({item["paper_id"] for item in rows}) != len(rows):
        raise ValueError("v10 corpus contains duplicate paper IDs")
    if len(membership) != parent_summary["frozen_assignments_guarded"]:
        raise ValueError("v10 changed frozen assignment cardinality")

    write_complete_manifest(output / "corpus_manifest.parquet", rows)
    write_jsonl(output / "edition-ledger.jsonl", ledger)
    triage = leakage_triage(rows, context["history"], membership,
                            method_version="five-year-leakage-triage-v10")
    write_jsonl(output / "leakage-triage.jsonl", triage)

    eligible = {(item["venue_id"], item["year"]) for item in ledger
                if item["status"] == "verified_eligible"}
    files = ["corpus_manifest.jsonl", "corpus_manifest-complete.parquet",
             "edition-ledger.jsonl", "leakage-triage.jsonl"]
    files.extend(str(path.relative_to(output)) for path in sorted((output / "editions").rglob("*.json*")))
    summary = {
        "stage": "discover", "method_version": VERSION,
        "config_sha256": digest(config_path.read_bytes()),
        "source_corrections_sha256": digest(Path(config["source_corrections"]["path"]).read_bytes()),
        "scope": "2021-2025 official_rosters_only",
        "candidate_editions": len(ledger), "roster_records": len(rows),
        "records_by_status": dict(Counter(item["status"] for item in rows)),
        "edition_statuses": dict(Counter(item["status"] for item in ledger)),
        "by_year": dict(Counter(str(item["year"]) for item in rows)),
        "eligible_included_records": sum(item["status"] == "included"
                                          and (item["venue_id"], item["year"]) in eligible for item in rows),
        "incomplete_editions": sum(item["status"] not in {"verified_eligible", "verified_no_edition", "excluded_track"}
                                    for item in ledger),
        "review_required": sum(item["status"] == "review" for item in rows),
        "manifest_sha256": digest((output / "corpus_manifest.jsonl").read_bytes()),
        "edition_ledger_sha256": digest((output / "edition-ledger.jsonl").read_bytes()),
        "parent_method_version": parent_summary["method_version"],
        "parent_manifest_sha256": parent_summary["manifest_sha256"],
        "parent_edition_ledger_sha256": parent_summary["edition_ledger_sha256"],
        "frozen_assignments_guarded": len(membership),
        "protected_test_assignments": sum(item["split"] == "test" for item in membership),
        "leakage_actions": dict(Counter(item["action"] for item in triage)),
        "new_splits_created": 0, "canonical_works_merged": 0,
        "semantic_accuracy": "not_measured", "enrichment_requests": 0,
        "graph_writes": 0, "pdfs_downloaded": 0, "public_per_record_roster": False,
        "miccai_2024_reconciliation": disposition["count_reconciliation"],
        "enrichment_authorized_by_this_output": False,
        "graph_construction_authorized": False,
        "output_sha256": {name: digest((output / name).read_bytes()) for name in files},
    }
    write_json(output / "summary.json", summary)
    return summary
