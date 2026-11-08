"""D040 topic test reservation must be frozen without leaking versions into development."""

import json
from pathlib import Path

import pytest

from scientific_network.nlp.topic_test import freeze_topic_test


def write_jsonl(path: Path, rows: list[dict]) -> Path:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    return path


def test_freeze_topic_test_is_deterministic_hash_bound_and_preserves_version_groups(tmp_path):
    roster = write_jsonl(tmp_path / "roster.jsonl", [
        {"paper_id": "paper:ijcai:2021:1", "venue_id": "venue:ijcai", "year": 2021, "status": "included"},
        {"paper_id": "paper:ijcai:2021:2", "venue_id": "venue:ijcai", "year": 2021, "status": "included"},
        {"paper_id": "paper:aaai:2021:1", "venue_id": "venue:aaai", "year": 2021, "status": "included"},
        {"paper_id": "paper:aaai:2021:2", "venue_id": "venue:aaai", "year": 2021, "status": "included"},
        {"paper_id": "paper:aaai:2022:3", "venue_id": "venue:aaai", "year": 2022, "status": "included"},
    ])
    membership = write_jsonl(tmp_path / "membership.jsonl", [
        {"paper_id": "paper:ijcai:2021:1", "venue_id": "venue:ijcai", "split": "test", "leakage_group": "g1"},
        {"paper_id": "paper:ijcai:2021:2", "venue_id": "venue:ijcai", "split": "test", "leakage_group": "g2"},
        {"paper_id": "paper:ijcai:2020:dev", "venue_id": "venue:ijcai", "split": "development", "leakage_group": "g-dev"},
    ])
    leakage = write_jsonl(tmp_path / "leakage.jsonl", [
        {"paper_id": "paper:ijcai:2021:1", "candidate_paper_ids": ["paper:ijcai:2021:1", "paper:ijcai:2020:v1"], "leakage_candidate_group": "g1"},
        {"paper_id": "paper:ijcai:2021:2", "candidate_paper_ids": ["paper:ijcai:2021:2"], "leakage_candidate_group": "g2"},
        {"paper_id": "paper:aaai:2021:1", "candidate_paper_ids": ["paper:aaai:2021:1", "paper:ijcai:2020:dev"], "leakage_candidate_group": "aaai-dev-overlap"},
        {"paper_id": "paper:aaai:2021:2", "candidate_paper_ids": ["paper:aaai:2021:2", "paper:aaai:2021:v2"], "leakage_candidate_group": "aaai-safe-1"},
        {"paper_id": "paper:aaai:2022:3", "candidate_paper_ids": ["paper:aaai:2022:3"], "leakage_candidate_group": "aaai-safe-2"},
    ])
    output = tmp_path / "topic-test.jsonl"

    result = freeze_topic_test(roster, membership, leakage, output, seed=20261108, ijcai_size=2, aaai_size=1, ijcai_frame_size=2)
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert result["sampled_ijcai"] == 2 and result["sampled_aaai"] == 1
    assert result["test_papers"] == 3 and result["output_sha256"]
    assert sum(row["sample_source"] == "frozen_ijcai_test_membership" for row in rows) == 2
    assert sum(row["sample_source"] == "new_aaai_roster_reservation" for row in rows) == 1
    assert "paper:aaai:2021:1" not in {row["paper_id"] for row in rows}
    chosen_aaai = next(row for row in rows if row["venue_id"] == "venue:aaai")
    expected_groups = {
        "aaai-safe-1": {"paper:aaai:2021:2", "paper:aaai:2021:v2"},
        "aaai-safe-2": {"paper:aaai:2022:3"},
    }
    assert set(chosen_aaai["heldout_paper_ids"]) == expected_groups[chosen_aaai["source_leakage_group"]]
    assert all(row["seed"] == 20261108 and row["roster_sha256"] == result["input_sha256"]["roster_sha256"] for row in rows)

    second = tmp_path / "topic-test-second.jsonl"
    freeze_topic_test(roster, membership, leakage, second, seed=20261108, ijcai_size=2, aaai_size=1, ijcai_frame_size=2)
    assert output.read_bytes() == second.read_bytes()
    with pytest.raises(ValueError, match="refusing to overwrite"):
        freeze_topic_test(roster, membership, leakage, output, seed=20261108, ijcai_size=2, aaai_size=1, ijcai_frame_size=2)


def test_freeze_topic_test_rejects_a_development_overlap_in_the_frozen_ijcai_group(tmp_path):
    roster = write_jsonl(tmp_path / "roster.jsonl", [
        {"paper_id": "paper:ijcai:2021:1", "venue_id": "venue:ijcai", "year": 2021, "status": "included"},
        {"paper_id": "paper:aaai:2021:1", "venue_id": "venue:aaai", "year": 2021, "status": "included"},
    ])
    membership = write_jsonl(tmp_path / "membership.jsonl", [
        {"paper_id": "paper:ijcai:2021:1", "venue_id": "venue:ijcai", "split": "test", "leakage_group": "g1"},
        {"paper_id": "paper:ijcai:2020:v1", "venue_id": "venue:ijcai", "split": "development", "leakage_group": "g1"},
    ])
    leakage = write_jsonl(tmp_path / "leakage.jsonl", [
        {"paper_id": "paper:ijcai:2021:1", "candidate_paper_ids": ["paper:ijcai:2021:1", "paper:ijcai:2020:v1"], "leakage_candidate_group": "g1"},
        {"paper_id": "paper:aaai:2021:1", "candidate_paper_ids": ["paper:aaai:2021:1"], "leakage_candidate_group": "a1"},
    ])
    with pytest.raises(ValueError, match="intersects development"):
        freeze_topic_test(roster, membership, leakage, tmp_path / "topic-test.jsonl", seed=1, ijcai_size=1, aaai_size=1, ijcai_frame_size=1)
