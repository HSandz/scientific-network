"""Resolve the ICAPS 2025 main-track sections from official acceptance evidence."""

import json
from pathlib import Path

from scientific_network.collect.ojs import recover_ojs
from scientific_network.collect.ojs_v4 import load_archive_v4
from scientific_network.collect.ojs_v5 import parse_v5
from scientific_network.collect.storage import digest, read_config

VERSION = "five-year-official-rosters-v6"
POLICY_NAME = "icaps_2025"
EXPECTED_MAIN_SECTIONS = {
    "Theoretical papers",
    "Algorithmic papers",
    "Modelling papers",
    "Tools papers",
}
EXPECTED_POSITION_IDS = {"36140", "36141", "36142"}
EXPECTED_FRONTMATTER_IDS = {"36956"}


def load_icaps_policy(config_path: Path) -> dict:
    """Load the hash-bound official acceptance/section reconciliation."""
    config = read_config(config_path)
    spec = config.get("edition_policy_evidence", {}).get(POLICY_NAME)
    if not isinstance(spec, dict) or not spec.get("path") or not spec.get("sha256"):
        raise ValueError("ICAPS 2025 policy evidence is required for roster v6")
    evidence_path = Path(spec["path"])
    raw = evidence_path.read_bytes()
    if digest(raw) != spec["sha256"]:
        raise ValueError("ICAPS 2025 policy evidence hash mismatch")
    evidence = json.loads(raw)
    if evidence.get("decision_id") != "D029" or evidence.get("venue_id") != "venue:icaps" or evidence.get("year") != 2025:
        raise ValueError("ICAPS 2025 policy evidence identity mismatch")
    section_policy = evidence.get("section_policy", {})
    main_ids = set(section_policy.get("main_research_ids", []))
    accepted_ids = set(section_policy.get("accepted_page_ids", []))
    position_ids = set(section_policy.get("position_excluded_ids", []))
    frontmatter_ids = set(section_policy.get("editorial_excluded_ids", []))
    issue_ids = set(section_policy.get("issue_record_ids", []))
    if (len(main_ids) != 48 or len(accepted_ids) != 51 or len(issue_ids) != 52
            or section_policy.get("main_research_sections") != sorted(EXPECTED_MAIN_SECTIONS)
            or position_ids != EXPECTED_POSITION_IDS
            or frontmatter_ids != EXPECTED_FRONTMATTER_IDS
            or accepted_ids != main_ids | position_ids
            or issue_ids != accepted_ids | frontmatter_ids):
        raise ValueError("ICAPS 2025 policy evidence has inconsistent record sets")
    if not evidence.get("accepted_page_extract", {}).get("sha256"):
        raise ValueError("ICAPS 2025 acceptance evidence has no extract hash")
    return {"main_ids": main_ids, "position_ids": position_ids,
            "frontmatter_ids": frontmatter_ids, "issue_ids": issue_ids,
            "main_sections": EXPECTED_MAIN_SECTIONS}


def parse_v6(body: bytes, edition: dict, source: dict, policy: dict) -> list[dict]:
    """Apply the exact 2025 accepted-ID map; other unknown sections still abstain."""
    rows = parse_v5(body, edition, source)
    if edition.get("journal") == "ICAPS" and edition.get("year") == 2025:
        ids = {str(row.get("official_record_id", "")) for row in rows}
        if ids != policy["issue_ids"]:
            raise ValueError("ICAPS 2025 OJS issue record set differs from acceptance evidence")
        for row in rows:
            record_id = str(row["official_record_id"])
            section = row["track_section"]
            if record_id in policy["main_ids"]:
                if section not in policy["main_sections"] or row["status"] != "review":
                    raise ValueError("accepted ICAPS 2025 main record has unexpected section/status")
                row.update(track="main", status="included",
                           reason="official_main_technical_acceptance_list_match",
                           section_policy="D029_ICAPS2025_main_track_acceptance_id")
            elif record_id in policy["position_ids"]:
                if section != "Position papers" or row["status"] != "excluded":
                    raise ValueError("ICAPS 2025 position exclusion differs from source policy")
            elif record_id in policy["frontmatter_ids"]:
                if section != "Frontmatter" or row["status"] != "excluded":
                    raise ValueError("ICAPS 2025 frontmatter exclusion differs from source policy")
            else:
                raise ValueError("unmapped ICAPS 2025 issue record")
    for row in rows:
        row["parser_version"] = VERSION
    return rows


def recover_v6(config_path: Path, output: Path, cache: Path) -> dict:
    policy = load_icaps_policy(config_path)

    def roster_parser(body: bytes, edition: dict, source: dict) -> list[dict]:
        return parse_v6(body, edition, source, policy)

    return recover_ojs(config_path, output, cache, method_version=VERSION,
                       archive_loader=load_archive_v4, roster_parser=roster_parser)
