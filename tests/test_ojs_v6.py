"""Synthetic source-contract cases for the ICAPS 2025 policy correction."""

import json
from pathlib import Path

import pytest

from scientific_network.collect.ojs_v6 import load_icaps_policy, parse_v6
from scientific_network.collect.storage import digest


SOURCE = {"url": "https://ojs.aaai.org/index.php/ICAPS/issue/view/663",
          "sha256": "a" * 64, "retrieved_at": "2026-11-07T00:00:00+07:00"}
ISSUE = {
    "venue_id": "venue:icaps", "name": "ICAPS", "journal": "ICAPS", "year": 2025,
    "title": "Proceedings of the Thirty-Fifth International Conference on Automated Planning and Scheduling",
    "series": "Vol. 35 (2025)",
    "official_index": "https://ojs.aaai.org/index.php/ICAPS/issue/view/663",
    "catalog_url": "https://ojs.aaai.org/index.php/ICAPS/issue/archive",
    "catalog_sha256": "b" * 64, "include_tracks": ["main"], "exclude_tracks": ["nonresearch"],
}


def evidence():
    return json.loads(Path("data/manifests/five-year-source-corrections-v4.json").read_text())


def issue_page(policy):
    section_by_id = {}
    main_ids = sorted(policy["main_ids"], key=int)
    for index, record_id in enumerate(main_ids):
        section_by_id[record_id] = sorted(policy["main_sections"])[index % len(policy["main_sections"])]
    section_by_id.update({record_id: "Position papers" for record_id in policy["position_ids"]})
    section_by_id.update({record_id: "Frontmatter" for record_id in policy["frontmatter_ids"]})
    groups = {}
    for record_id, section in section_by_id.items():
        groups.setdefault(section, []).append(record_id)
    sections = []
    for label, record_ids in sorted(groups.items()):
        articles = "".join(
            f'<div class="obj_article_summary"><h3 class="title"><a href="https://ojs.aaai.org/index.php/ICAPS/article/view/{record_id}">Synthetic work {record_id}</a></h3><div class="authors">Author {record_id}, Collaborator {record_id}</div></div>'
            for record_id in sorted(record_ids, key=int)
        )
        sections.append(f'<div class="section"><h2>{label}</h2>{articles}</div>')
    heading = f'{ISSUE["series"]}: {ISSUE["title"]}'
    return f'<div class="page_issue"><h1>{heading}</h1><div class="obj_issue_toc">{"".join(sections)}</div></div>'.encode()


def test_v6_accepts_all_48_official_main_research_ids_and_keeps_exclusions():
    policy = {"main_ids": set(evidence()["section_policy"]["main_research_ids"]),
              "position_ids": set(evidence()["section_policy"]["position_excluded_ids"]),
              "frontmatter_ids": set(evidence()["section_policy"]["editorial_excluded_ids"]),
              "issue_ids": set(evidence()["section_policy"]["issue_record_ids"]),
              "main_sections": set(evidence()["section_policy"]["main_research_sections"])}
    rows = parse_v6(issue_page(policy), ISSUE, SOURCE, policy)
    assert len(rows) == 52
    assert sum(row["status"] == "included" for row in rows) == 48
    assert sum(row["status"] == "excluded" for row in rows) == 4
    assert not any(row["status"] == "review" for row in rows)
    assert {row["official_record_id"] for row in rows if row["status"] == "included"} == policy["main_ids"]
    assert {row["official_record_id"] for row in rows if row["status"] == "excluded"} == policy["position_ids"] | policy["frontmatter_ids"]
    assert all(row["section_policy"] == "D029_ICAPS2025_main_track_acceptance_id" for row in rows if row["status"] == "included")


def test_v6_fails_closed_on_incomplete_or_misclassified_icaps_issue():
    manifest = evidence()["section_policy"]
    policy = {"main_ids": set(manifest["main_research_ids"]),
              "position_ids": set(manifest["position_excluded_ids"]),
              "frontmatter_ids": set(manifest["editorial_excluded_ids"]),
              "issue_ids": set(manifest["issue_record_ids"]),
              "main_sections": set(manifest["main_research_sections"])}
    complete = issue_page(policy)
    with pytest.raises(ValueError, match="record set"):
        parse_v6(complete.replace(b"view/36145", b"view/99999"), ISSUE, SOURCE, policy)
    with pytest.raises(ValueError, match="unexpected section"):
        parse_v6(complete.replace(b"<h2>Tools papers</h2>", b"<h2>Unknown section</h2>"), ISSUE, SOURCE, policy)


def test_v6_requires_hash_bound_source_policy(tmp_path):
    manifest_path = Path("data/manifests/five-year-source-corrections-v4.json")
    manifest_hash = digest(manifest_path.read_bytes())
    config = tmp_path / "config.yaml"
    config.write_text(
        "edition_policy_evidence:\n  icaps_2025:\n"
        f"    path: {manifest_path}\n    sha256: \"{manifest_hash}\"\n"
    )
    assert len(load_icaps_policy(config)["main_ids"]) == 48
    config.write_text(config.read_text().replace(manifest_hash, "0" * 64))
    with pytest.raises(ValueError, match="hash mismatch"):
        load_icaps_policy(config)


def test_correction_manifest_has_consistent_official_id_sets():
    item = evidence()
    mapping = item["section_policy"]
    main = set(mapping["main_research_ids"])
    accepted = set(mapping["accepted_page_ids"])
    position = set(mapping["position_excluded_ids"])
    editorial = set(mapping["editorial_excluded_ids"])
    issue = set(mapping["issue_record_ids"])
    assert len(main) == 48
    assert accepted == main | position
    assert issue == accepted | editorial
    assert len(issue) == 52
