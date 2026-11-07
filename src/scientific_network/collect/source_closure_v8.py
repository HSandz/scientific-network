"""Add hash-bound IFAAMAS rosters to the immutable five-year v7 baseline."""

from collections import Counter
import json
from pathlib import Path
import re

from bs4 import BeautifulSoup

from scientific_network.collect.aamas import parse_aamas_roster, reconcile_aamas_2023
from scientific_network.collect.five_year_v2 import write_complete_manifest
from scientific_network.collect.reconcile import leakage_triage
from scientific_network.collect.source_closure_v7 import _read_verified, _validate_v6
from scientific_network.collect.storage import digest, read_config, read_jsonl, write_json, write_jsonl

VERSION = "five-year-official-rosters-v8"
AAMAS_EDITION_CONTRACTS = {
    2021: {
        "main_section": "Main Track",
        "sections": {
            "Blue Sky Ideas Track": 12, "Main Track": 151, "Extended Abstracts": 92,
            "JAAMAS Track": 12, "Demonstration Track": 15, "Doctoral Consortium": 22,
        },
    },
    2022: {
        "main_section": "Main Track",
        "sections": {
            "Main Track": 166, "Extended Abstracts": 89, "Blue Sky Ideas Track": 9,
            "Doctoral Consortium": 20, "Demonstration Track": 11, "JAAMAS Track": 11,
        },
    },
    2024: {
        "main_section": "Full Research Papers",
        "sections": {
            "Keynote Talks": 3, "Full Research Papers": 230, "Extended Abstract": 171,
            "AAAI Track": 5, "Blue Sky Ideas Track": 10, "Doctoral Consortium": 23,
            "Demonstration Track": 10, "JAAMAS Track": 8,
        },
    },
    2025: {
        "main_section": "Research Paper Track",
        "sections": {
            "Keynote Talks": 3, "Research Paper Track": 260, "Extended Abstracts": 148,
            "Blue Sky Ideas": 12, "Doctoral Consortium": 25, "Demo Track": 22,
            "JAAMAS Track": 9,
        },
    },
}
AAMAS_2023_UNRESOLVED = ("venue:aamas", 2023)


def _copy_immutable_tree(source: Path, target: Path) -> None:
    if not source.exists():
        return
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        # AAMAS editions are replaced only from the v8 hash-bound captures.
        if relative.parts and relative.parts[0] == "aamas":
            continue
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        raw = path.read_bytes()
        if destination.exists():
            if destination.read_bytes() != raw:
                raise ValueError(f"refusing to overwrite changed inherited roster: {destination}")
        else:
            destination.write_bytes(raw)


def _load_v7(config: dict) -> tuple[dict, list[dict], list[dict], list[dict], dict]:
    base = config["baseline"]
    config_path = Path(base["config_path"])
    _read_verified(config_path, base["config_sha256"], "v7 config")
    parent_config = read_config(config_path)
    if parent_config.get("workflow") != "five_year_source_closure_v7":
        raise ValueError("v8 requires the immutable source-closure v7 config")
    output = Path(base["output_dir"])
    summary_raw = _read_verified(output / "summary.json", base["summary_sha256"], "v7 summary")
    summary = json.loads(summary_raw)
    if summary.get("method_version") != "five-year-official-rosters-v7":
        raise ValueError("v8 requires the immutable v7 roster output")
    for name, expected in summary.get("output_sha256", {}).items():
        _read_verified(output / name, expected, "v7 output")

    _, _, _, membership, context = _validate_v6(parent_config, config_path)
    rows = read_jsonl(output / "corpus_manifest.jsonl")
    ledger = read_jsonl(output / "edition-ledger.jsonl")
    if len(rows) != summary.get("roster_records") or len(ledger) != 170:
        raise ValueError("v7 manifest or edition ledger count disagrees with its summary")
    if len({row["paper_id"] for row in rows}) != len(rows):
        raise ValueError("v7 manifest contains duplicate paper IDs")
    if len(membership) != summary.get("frozen_assignments_guarded"):
        raise ValueError("v7 frozen assignment count disagrees with inherited membership")
    return summary, rows, ledger, membership, {**context, "output": output}


def _load_corrections(config: dict) -> tuple[dict, dict[str, dict], dict[tuple[str, int], dict]]:
    spec = config["source_corrections"]
    raw = _read_verified(Path(spec["path"]), spec["sha256"], "source corrections")
    evidence = json.loads(raw)
    if evidence.get("version") != "five-year-source-corrections-v6" or evidence.get("decision_id") != "D031":
        raise ValueError("AAMAS source correction identity mismatch")
    sources = {item["source_id"]: item for item in evidence.get("official_sources", [])}
    if len(sources) != len(evidence.get("official_sources", [])):
        raise ValueError("duplicate official source IDs in AAMAS correction manifest")
    if len(sources) != 14:
        raise ValueError("AAMAS correction manifest must preserve all 14 official source captures")
    for source_id, source in sources.items():
        if source.get("response_status") != 200 or "text/html" not in source.get("content_type", ""):
            raise ValueError(f"AAMAS source is not a successful HTML response: {source_id}")
        source_path = Path(source["snapshot_path"])
        if "five-year-source-cache-v8/objects" not in str(source_path):
            raise ValueError(f"AAMAS source snapshot is outside the versioned ignored cache: {source_id}")
        _read_verified(source_path, source["sha256"], source_id)

    dispositions = evidence.get("edition_dispositions", [])
    by_edition = {(row["venue_id"], row["year"]): row for row in dispositions}
    expected_keys = {("venue:aamas", year) for year in AAMAS_EDITION_CONTRACTS}
    if len(by_edition) != len(dispositions) or set(by_edition) != expected_keys:
        raise ValueError("AAMAS corrections must contain the four fully reconciled editions")
    for year, contract in AAMAS_EDITION_CONTRACTS.items():
        row = by_edition[("venue:aamas", year)]
        content_id = f"aamas{year}_contents"
        rights_id = f"aamas{year}_proceedings_index"
        if (row.get("status") != "verified_eligible" or content_id not in row.get("evidence_source_ids", [])
                or row.get("rights_source_id") != rights_id
                or row.get("main_section") != contract["main_section"]
                or row.get("expected_section_counts") != contract["sections"]
                or row.get("expected_total_records") != sum(contract["sections"].values())
                or row.get("expected_included") != contract["sections"][contract["main_section"]]):
            raise ValueError(f"AAMAS {year} correction does not match its edition-bound contract")

        rights_text = " ".join(
            Path(sources[rights_id]["snapshot_path"]).read_text(encoding="utf-8", errors="replace").casefold().split()
        )
        required_terms = ("copyright", "abstracting with credit is permitted", "specific permission")
        if any(term not in rights_text for term in required_terms):
            raise ValueError(f"AAMAS {year} copyright and reuse terms are not captured")

    unresolved = evidence.get("unresolved_findings", [])
    if len(unresolved) != 1 or (unresolved[0].get("venue_id"), unresolved[0].get("year")) != AAMAS_2023_UNRESOLVED:
        raise ValueError("AAMAS 2023 must remain an explicit unresolved finding")
    finding = unresolved[0]
    if finding.get("status") != "unresolved":
        raise ValueError("AAMAS 2023 cannot be promoted without complete roster reconciliation")
    accepted = Path(sources["aamas2023_accepted_papers"]["snapshot_path"]).read_bytes()
    contents = Path(sources["aamas2023_contents"]["snapshot_path"]).read_bytes()
    diagnostic = reconcile_aamas_2023(accepted, contents)
    for key, value in diagnostic.items():
        if finding.get(key) != value:
            raise ValueError(f"AAMAS 2023 unresolved diagnostic differs for {key}")
    news = BeautifulSoup(
        Path(sources["aamas2023_news"]["snapshot_path"]).read_bytes().decode("utf-8-sig"),
        "html.parser",
    ).get_text(" ", strip=True)
    if (finding.get("official_full_papers_announced") != diagnostic["official_full_papers_listed"]
            or finding.get("official_extended_abstracts_announced") != 221
            or finding.get("extended_abstract_announcement_minus_listed")
            != 221 - diagnostic["accepted_extended_abstracts_listed"]
            or not re.search(r"237\s+were accepted as full papers", news, re.I)
            or not re.search(r"221\s+were accepted as extended abstracts", news, re.I)):
        raise ValueError("AAMAS 2023 accepted-page/news counts are not reconciled")
    return evidence, sources, by_edition


def discover_v8(config_path: Path, output: Path) -> dict:
    config = read_config(config_path)
    if (config.get("workflow") != "five_year_source_closure_v8"
            or config.get("collection_authorized") is not True
            or config.get("stage_boundary") != "official_rosters_only_no_enrichment_or_splits"):
        raise ValueError("v8 requires an authorized official-roster-only config")

    parent_summary, rows, ledger, membership, context = _load_v7(config)
    evidence, sources, dispositions = _load_corrections(config)
    row_by_edition = {(row["venue_id"], row["year"]): row for row in ledger}
    if any(row_by_edition[key]["status"] != "unresolved" for key in set(dispositions) | {AAMAS_2023_UNRESOLVED}):
        raise ValueError("v8 can only update currently unresolved AAMAS editions")

    if (output / "summary.json").exists():
        saved = json.loads((output / "summary.json").read_text(encoding="utf-8"))
        if saved.get("config_sha256") != digest(config_path.read_bytes()):
            raise ValueError("v8 output belongs to a different config")
        for name, expected_hash in saved["output_sha256"].items():
            _read_verified(output / name, expected_hash, "v8 checkpoint")
        return saved

    now = evidence["recorded_at"]
    new_rows = []
    rights_note = evidence["rights_and_distribution"]["summary"]
    output.mkdir(parents=True, exist_ok=True)
    _copy_immutable_tree(context["output"] / "editions", output / "editions")
    for year, contract in AAMAS_EDITION_CONTRACTS.items():
        correction = dispositions[("venue:aamas", year)]
        content_spec = sources[f"aamas{year}_contents"]
        rights_spec = sources[correction["rights_source_id"]]
        edition = {
            "year": year,
            "official_index": content_spec["url"],
            "main_section": contract["main_section"],
            "expected_section_counts": contract["sections"],
            "expected_included": contract["sections"][contract["main_section"]],
        }
        source = {"url": content_spec["url"], "sha256": content_spec["sha256"],
                  "retrieved_at": content_spec["accessed_at"], "license": "IFAAMAS copyright; redistribution restricted"}
        body = Path(content_spec["snapshot_path"]).read_bytes()
        parsed = parse_aamas_roster(body, edition, source)
        if len(parsed) != correction["expected_total_records"]:
            raise ValueError(f"AAMAS {year} parsed roster count differs from the correction manifest")

        directory = output / "editions" / "aamas" / str(year)
        write_jsonl(directory / "roster.jsonl", parsed)
        row = row_by_edition[("venue:aamas", year)]
        row.update(
            status="verified_eligible",
            reason="official_research_section_roster_parsed_and_reconciled",
            records=len(parsed),
            by_status=dict(Counter(item["status"] for item in parsed)),
            routes=[{"official_index": content_spec["url"], "main_section": contract["main_section"],
                     "all_sections_reconciled": True}],
            sources=[*row.get("sources", []), source],
            official_policy_sources=[rights_spec],
            checked_at=now,
            method_version=VERSION,
            rights=rights_note,
            redistribution="local_ignored_only; public per-record metadata not authorized",
            roster_sha256=digest((directory / "roster.jsonl").read_bytes()),
        )
        write_json(directory / "summary.json", {
            "venue_id": "venue:aamas", "year": year, "status": "verified_eligible",
            "reason": row["reason"], "records": len(parsed), "by_status": row["by_status"],
            "routes": row["routes"], "sources": [source],
            "official_policy_sources": [rights_spec], "roster_sha256": row["roster_sha256"],
            "method_version": VERSION, "checked_at": now,
            "reviewer": "automated_source_contract_check_not_independent_scientific_review",
            "rights": rights_note, "redistribution": row["redistribution"],
        })
        new_rows.extend(parsed)

    unresolved_row = row_by_edition[AAMAS_2023_UNRESOLVED]
    unresolved_finding = evidence["unresolved_findings"][0]
    unresolved_row.update(
        status="unresolved",
        reason="official_full_paper_list_not_fully_reconciled_to_proceedings_records_and_bylines",
        records=0,
        routes=[{"official_index": sources["aamas2023_contents"]["url"],
                 "accepted_papers": sources["aamas2023_accepted_papers"]["url"]}],
        sources=[sources[source_id] for source_id in unresolved_finding["evidence_source_ids"]],
        source_reconciliation={key: value for key, value in unresolved_finding.items()
                               if key not in {"venue_id", "year", "status", "evidence_source_ids", "reason"}},
        checked_at=now,
        method_version=VERSION,
        rights=rights_note,
        redistribution="local_ignored_only; public per-record metadata not authorized",
    )

    rows.extend(new_rows)
    rows.sort(key=lambda row: row["paper_id"])
    if len({row["paper_id"] for row in rows}) != len(rows):
        raise ValueError("v8 corpus contains duplicate paper IDs")
    write_complete_manifest(output / "corpus_manifest.parquet", rows)
    write_jsonl(output / "edition-ledger.jsonl", ledger)
    triage = leakage_triage(rows, context["history"], membership,
                            method_version="five-year-leakage-triage-v8")
    write_jsonl(output / "leakage-triage.jsonl", triage)

    eligible = {(row["venue_id"], row["year"]) for row in ledger if row["status"] == "verified_eligible"}
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
