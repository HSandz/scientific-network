"""Apply hash-bound official edition dispositions and a joint COLING roster."""

from collections import Counter
import json
from pathlib import Path
import shutil

from scientific_network.collect.reconcile import leakage_triage
from scientific_network.collect.rosters import parse_roster
from scientific_network.collect.five_year_v2 import write_complete_manifest
from scientific_network.collect.storage import (
    digest, read_config, read_jsonl, write_json,
    write_jsonl,
)

VERSION = "five-year-official-rosters-v7"
NO_EDITION = {
    ("venue:iccv", 2022), ("venue:iccv", 2024),
    ("venue:eccv", 2021), ("venue:eccv", 2023), ("venue:eccv", 2025),
    ("venue:naacl", 2023),
    ("venue:eacl", 2022), ("venue:eacl", 2025),
    ("venue:coling", 2021), ("venue:coling", 2023),
}
JOINT_EDITION = ("venue:coling", 2024)


def _read_verified(path: Path, expected_sha256: str, label: str) -> bytes:
    raw = path.read_bytes()
    if digest(raw) != expected_sha256:
        raise ValueError(f"{label} hash mismatch: {path}")
    return raw


def validate_edition_dispositions(items: list[dict]) -> dict[tuple[str, int], dict]:
    by_edition = {(item["venue_id"], item["year"]): item for item in items}
    if len(by_edition) != len(items) or set(by_edition) != (NO_EDITION | {JOINT_EDITION}):
        raise ValueError("source corrections must cover exactly eleven edition candidates")
    for key in NO_EDITION:
        item = by_edition[key]
        if item.get("status") != "verified_no_edition" or not item.get("evidence_source_ids"):
            raise ValueError(f"no-edition disposition lacks official evidence: {key}")
    joint = by_edition[JOINT_EDITION]
    if (joint.get("status") != "verified_eligible"
            or joint.get("primary_venue_id") != "venue:coling"
            or joint.get("joint_event_id") != "event:lrec-coling:2024"
            or not joint.get("evidence_source_ids")):
        raise ValueError("COLING 2024 joint-event disposition is incomplete")
    return by_edition


def _validate_v6(config: dict, config_path: Path) -> tuple[dict, list[dict], list[dict], list[dict], dict]:
    base = config["baseline"]
    v6_config_path = Path(base["config_path"])
    _read_verified(v6_config_path, base["config_sha256"], "v6 config")
    v6_config = read_config(v6_config_path)
    output = Path(base["output_dir"])
    summary_raw = _read_verified(output / "summary.json", base["summary_sha256"], "v6 summary")
    summary = json.loads(summary_raw)
    if summary.get("method_version") != "five-year-official-rosters-v6":
        raise ValueError("v7 requires the immutable v6 roster output")
    for name, expected in summary.get("output_sha256", {}).items():
        _read_verified(output / name, expected, "v6 output")

    for item in v6_config["baseline"].values():
        _read_verified(Path(item["path"]), item["sha256"], "v6 baseline input")
    guards = v6_config["frozen_guards"]
    for item in guards:
        _read_verified(Path(item["path"]), item["sha256"], "frozen guard")
    membership = read_jsonl(Path(v6_config["current_membership"]))
    members = {row["paper_id"]: row for row in membership}
    if len(members) != len(membership):
        raise ValueError("duplicate frozen assignments")
    for name in v6_config["membership_history"]:
        if any(members.get(row["paper_id"]) != row for row in read_jsonl(Path(name))):
            raise ValueError("historical assignment differs from current membership")
    if len(membership) != summary.get("frozen_assignments_guarded"):
        raise ValueError("v6 frozen assignment count differs from summary")

    manifest = read_jsonl(output / "corpus_manifest.jsonl")
    ledger = read_jsonl(output / "edition-ledger.jsonl")
    historical = read_jsonl(Path(v6_config["baseline"]["historical_manifest"]["path"]))
    previous = read_jsonl(Path(v6_config["baseline"]["manifest"]["path"]))
    history = {row["paper_id"]: row for row in historical}
    history.update({row["paper_id"]: row for row in previous})
    if len({row["paper_id"] for row in manifest}) != len(manifest):
        raise ValueError("duplicate IDs in v6 manifest")
    if len(ledger) != 170 or len({(r["venue_id"], r["year"]) for r in ledger}) != 170:
        raise ValueError("v6 ledger must preserve all 170 candidates")
    return summary, manifest, ledger, membership, {"history": list(history.values()), "output": output}


def _load_corrections(config: dict) -> tuple[dict, dict, dict]:
    spec = config["source_corrections"]
    raw = _read_verified(Path(spec["path"]), spec["sha256"], "source corrections")
    evidence = json.loads(raw)
    if evidence.get("version") != "five-year-source-corrections-v5" or evidence.get("decision_id") != "D030":
        raise ValueError("source correction identity mismatch")
    sources = {item["source_id"]: item for item in evidence["official_sources"]}
    if len(sources) != len(evidence["official_sources"]):
        raise ValueError("duplicate official source IDs")
    for item in sources.values():
        if item.get("snapshot_path"):
            _read_verified(Path(item["snapshot_path"]), item["sha256"], item["source_id"])
    roster_spec = evidence["joint_roster"]
    roster_raw = _read_verified(Path(roster_spec["roster_path"]), roster_spec["roster_sha256"], "COLING 2024 roster")
    rows = [json.loads(line) for line in roster_raw.decode().splitlines() if line.strip()]
    if len(rows) != 1555:
        raise ValueError("COLING 2024 joint roster must contain 1,555 source records")
    ids = [row.get("official_record_id") for row in rows]
    if len(set(ids)) != len(ids) or set(ids) != {f"2024.lrec-main.{n}" for n in range(1555)}:
        raise ValueError("COLING 2024 official IDs are incomplete or duplicated")
    if Counter(row.get("status") for row in rows) != Counter({"included": 1554, "excluded": 1}):
        raise ValueError("COLING 2024 joint roster disposition counts mismatch")
    if any(not row.get("title") or not row.get("authors") for row in rows):
        raise ValueError("COLING 2024 roster has missing title/byline evidence")
    if not all(row.get("source_sha256") == roster_spec["source_response_sha256"] for row in rows):
        raise ValueError("COLING 2024 records disagree with source response hash")
    return evidence, sources, {"rows": rows, "raw_sha256": digest(roster_raw)}


def _copy_immutable_tree(source: Path, target: Path) -> None:
    if not source.exists():
        return
    for path in sorted(source.rglob("*")):
        if path.is_file():
            destination = target / path.relative_to(source)
            destination.parent.mkdir(parents=True, exist_ok=True)
            raw = path.read_bytes()
            if destination.exists():
                if destination.read_bytes() != raw:
                    raise ValueError(f"refusing to overwrite changed inherited roster: {destination}")
            else:
                destination.write_bytes(raw)


def discover_v7(config_path: Path, output: Path) -> dict:
    config = read_config(config_path)
    if (config.get("workflow") != "five_year_source_closure_v7"
            or config.get("collection_authorized") is not True
            or config.get("stage_boundary") != "official_rosters_only_no_enrichment_or_splits"):
        raise ValueError("v7 source closure requires an authorized roster-only config")
    v6_summary, rows, ledger, membership, context = _validate_v6(config, config_path)
    evidence, sources, roster = _load_corrections(config)
    row_by_edition = {(row["venue_id"], row["year"]): row for row in ledger}
    if not (NO_EDITION | {JOINT_EDITION}) <= set(row_by_edition):
        raise ValueError("v7 corrections do not map to the ten no-edition rows and COLING 2024")
    if any(row_by_edition[key]["status"] != "unresolved" for key in NO_EDITION | {JOINT_EDITION}):
        raise ValueError("v7 can only correct currently unresolved route rows")

    # A finalized replay reuses the output only after checking every saved hash.
    if (output / "summary.json").exists():
        saved = json.loads((output / "summary.json").read_text())
        if saved.get("config_sha256") != digest(config_path.read_bytes()):
            raise ValueError("v7 output belongs to a different config")
        for name, expected in saved["output_sha256"].items():
            _read_verified(output / name, expected, "v7 checkpoint")
        return saved

    correction_by_edition = validate_edition_dispositions(evidence["edition_dispositions"])
    now = evidence["recorded_at"]
    for key in sorted(NO_EDITION):
        item = correction_by_edition[key]
        if not item.get("status") == "verified_no_edition" or not item.get("evidence_source_ids"):
            raise ValueError("no-edition disposition lacks direct official evidence")
        row = row_by_edition[key]
        row.update(status="verified_no_edition", reason="official_edition_history_confirms_no_edition",
                   checked_at=now, method_version=VERSION,
                   official_policy_sources=[sources[source_id] for source_id in item["evidence_source_ids"]])

    coling_policy = correction_by_edition[JOINT_EDITION]
    if (coling_policy.get("status") != "verified_eligible"
            or coling_policy.get("primary_venue_id") != "venue:coling"
            or coling_policy.get("joint_event_id") != "event:lrec-coling:2024"):
        raise ValueError("COLING 2024 joint-edition mapping is not explicit")
    catalog_row = row_by_edition[JOINT_EDITION]
    edition = {
        "adapter": "acl", "venue_id": "venue:coling", "year": 2024,
        "name": "COLING", "official_index": evidence["joint_roster"]["source_url"],
        "collection": "2024.lrec-main", "include_tracks": ["main"],
        "exclude_tracks": ["nonresearch", "frontmatter"],
        "required_markers": ["2024", "LREC-COLING"],
    }
    source_spec = evidence["joint_roster"]
    source = {"url": source_spec["source_url"],
              "sha256": source_spec["source_response_sha256"],
              "retrieved_at": source_spec["retrieved_at"],
              "license": "unknown_unless_source_record_supplies_license"}
    body = Path(source_spec["source_body_path"]).read_bytes()
    if digest(body) != source_spec["source_response_sha256"]:
        raise ValueError("COLING 2024 raw official volume response hash mismatch")
    parsed = parse_roster(body, edition, source)
    if (len(parsed) != 1555 or Counter(row["status"] for row in parsed)
            != Counter({"included": 1554, "excluded": 1})):
        raise ValueError("existing ACL parser did not reproduce the captured COLING roster")
    captured = roster["rows"]
    if [(r["official_record_id"], r["title"], r["authors"], r["status"]) for r in parsed] != [
            (r["official_record_id"], r["title"], r["authors"], r["status"]) for r in captured]:
        raise ValueError("COLING replay differs from the versioned browser-captured roster")
    for row in parsed:
        row.update(primary_venue_id="venue:coling", joint_event_id="event:lrec-coling:2024",
                   joint_event_title="LREC-COLING 2024",
                   joint_event_venue_ids=["venue:coling", "venue:lrec"],
                   source_venue_crosswalk=["venue:coling", "venue:lrec"],
                   parser_version=VERSION)
    rows.extend(parsed)
    rows.sort(key=lambda row: row["paper_id"])
    if len({row["paper_id"] for row in rows}) != len(rows):
        raise ValueError("v7 corpus contains duplicate paper IDs")

    catalog_row.update(status="verified_eligible", reason="complete_official_joint_main_roster_parsed",
        records=len(parsed), by_status=dict(Counter(row["status"] for row in parsed)),
        routes=[{"official_index": source_spec["source_url"], "collection": "2024.lrec-main",
                 "disposition": "joint_event_primary_series_coling", "joint_event_id": "event:lrec-coling:2024"}],
        sources=[*catalog_row.get("sources", []), source], checked_at=now,
        method_version=VERSION,
        official_policy_sources=[sources[source_id] for source_id in coling_policy["evidence_source_ids"]],
        rights="unknown_unless_source_record_supplies_license")

    edition_dir = output / "editions" / "coling" / "2024"
    write_jsonl(edition_dir / "roster.jsonl", parsed)
    write_json(edition_dir / "summary.json", {
        "venue_id": "venue:coling", "year": 2024, "status": "verified_eligible",
        "reason": "complete_official_joint_main_roster_parsed", "records": len(parsed),
        "by_status": dict(Counter(row["status"] for row in parsed)),
        "routes": catalog_row["routes"], "sources": [source],
        "official_policy_sources": catalog_row["official_policy_sources"],
        "roster_sha256": digest((edition_dir / "roster.jsonl").read_bytes()),
        "method_version": VERSION, "checked_at": now,
        "reviewer": "automated_contract_check_not_independent_scientific_review",
        "rights": "unknown_unless_source_record_supplies_license",
        "joint_event_id": "event:lrec-coling:2024", "primary_venue_id": "venue:coling",
    })
    catalog_row["roster_sha256"] = digest((edition_dir / "roster.jsonl").read_bytes())

    output.mkdir(parents=True, exist_ok=True)
    source_editions = context["output"] / "editions"
    _copy_immutable_tree(source_editions, output / "editions")
    write_complete_manifest(output / "corpus_manifest.parquet", rows)
    write_jsonl(output / "edition-ledger.jsonl", ledger)
    history = context["history"]
    triage = leakage_triage(rows, history, membership,
                            method_version="five-year-leakage-triage-v7")
    write_jsonl(output / "leakage-triage.jsonl", triage)
    files = ["corpus_manifest.jsonl", "corpus_manifest-complete.parquet",
             "edition-ledger.jsonl", "leakage-triage.jsonl"]
    files.extend(str(path.relative_to(output)) for path in sorted((output / "editions").rglob("*.json*")))
    eligible = {(row["venue_id"], row["year"]) for row in ledger
                if row["status"] == "verified_eligible"}
    summary = {
        "stage": "discover", "method_version": VERSION,
        "config_sha256": digest(config_path.read_bytes()),
        "source_corrections_sha256": digest(Path(config["source_corrections"]["path"]).read_bytes()),
        "scope": "2021-2025 official_rosters_only", "candidate_editions": len(ledger),
        "roster_records": len(rows), "records_by_status": dict(Counter(row["status"] for row in rows)),
        "edition_statuses": dict(Counter(row["status"] for row in ledger)),
        "by_year": dict(Counter(str(row["year"]) for row in rows)),
        "eligible_included_records": sum(row["status"] == "included" and
                                          (row["venue_id"], row["year"]) in eligible for row in rows),
        "incomplete_editions": sum(row["status"] not in {"verified_eligible", "verified_no_edition", "excluded_track"}
                                    for row in ledger),
        "review_required": sum(row["status"] == "review" for row in rows),
        "manifest_sha256": digest((output / "corpus_manifest.jsonl").read_bytes()),
        "edition_ledger_sha256": digest((output / "edition-ledger.jsonl").read_bytes()),
        "parent_method_version": v6_summary["method_version"],
        "parent_manifest_sha256": v6_summary["manifest_sha256"],
        "parent_edition_ledger_sha256": v6_summary["edition_ledger_sha256"],
        "frozen_assignments_guarded": len(membership),
        "protected_test_assignments": sum(row["split"] == "test" for row in membership),
        "leakage_actions": dict(Counter(row["action"] for row in triage)),
        "new_splits_created": 0, "canonical_works_merged": 0,
        "semantic_accuracy": "not_measured", "enrichment_requests": 0,
        "graph_writes": 0, "enrichment_authorized_by_this_output": False,
        "graph_construction_authorized": False,
        "output_sha256": {name: digest((output / name).read_bytes()) for name in files},
    }
    write_json(output / "summary.json", summary)
    return summary
