"""Synthetic contract checks for official edition correction v7."""

import pytest

from scientific_network.collect.source_closure_v7 import (
    JOINT_EDITION, NO_EDITION, validate_edition_dispositions,
)


def dispositions():
    rows = [
        {"venue_id": venue, "year": year, "status": "verified_no_edition",
         "evidence_source_ids": ["official-policy"]}
        for venue, year in sorted(NO_EDITION)
    ]
    rows.append({"venue_id": JOINT_EDITION[0], "year": JOINT_EDITION[1],
                 "status": "verified_eligible", "primary_venue_id": "venue:coling",
                 "joint_event_id": "event:lrec-coling:2024",
                 "evidence_source_ids": ["official-proceedings"]})
    return rows


def test_v7_requires_all_ten_no_editions_and_one_joint_coling_roster():
    mapping = validate_edition_dispositions(dispositions())
    assert set(mapping) == NO_EDITION | {JOINT_EDITION}
    assert sum(row["status"] == "verified_no_edition" for row in mapping.values()) == 10
    assert mapping[JOINT_EDITION]["primary_venue_id"] == "venue:coling"


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "unverified", "wrong_primary", "no_evidence"])
def test_v7_rejects_incomplete_or_unsupported_edition_dispositions(mutation):
    rows = dispositions()
    if mutation == "missing":
        rows.pop()
    elif mutation == "duplicate":
        rows.append(dict(rows[0]))
    elif mutation == "unverified":
        rows[0]["status"] = "unresolved"
    elif mutation == "wrong_primary":
        rows[-1]["primary_venue_id"] = "venue:lrec"
    else:
        rows[-1]["evidence_source_ids"] = []
    with pytest.raises(ValueError):
        validate_edition_dispositions(rows)
