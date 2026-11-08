"""Prediction-blind topic review sheet contract tests."""

import csv
import hashlib
import json

import pytest
import yaml

from scientific_network.evaluation.topic_review import (
    FIELDS,
    assign_topic_reviewers,
    prepare_topic_review_packets,
    prepare_topic_review_sheet,
)


def _fixture(tmp_path, *, status="frozen"):
    works = tmp_path / "works.jsonl"
    topic_test = tmp_path / "topic-test.jsonl"
    taxonomy = tmp_path / "topics.yaml"
    works_rows = [
        {"paper_id": f"paper:{index}", "venue_id": "venue:aaai", "year": 2025,
         "roster": {"title": f"Paper {index}"}, "openalex": {"abstract": f"Abstract {index}"},
         "topic_predictions": ["must-not-appear"]}
        for index in range(50)
    ]
    test_rows = [{"paper_id": f"paper:{index}"} for index in range(50)]
    works.write_text("".join(json.dumps(row) + "\n" for row in works_rows), encoding="utf-8")
    topic_test.write_text("".join(json.dumps(row) + "\n" for row in test_rows), encoding="utf-8")
    leaves = [
        {"id": f"topic:{index}", "name": f"Topic {index}", "definition": f"Definition {index}"}
        for index in range(16)
    ]
    config = {
        "status": status,
        "calibration": {
            "works_sha256": hashlib.sha256(works.read_bytes()).hexdigest(),
            "topic_test_sha256": hashlib.sha256(topic_test.read_bytes()).hexdigest(),
        },
        "leaves": leaves,
    }
    taxonomy.write_text(yaml.safe_dump(config), encoding="utf-8")
    return works, topic_test, taxonomy


def test_topic_review_sheet_contains_all_source_text_and_blank_labels_without_predictions(tmp_path):
    works, topic_test, taxonomy = _fixture(tmp_path)
    output = tmp_path / "topic-label-sheet.csv"

    result = prepare_topic_review_sheet(works, topic_test, taxonomy, output)

    assert result["status"] == "ready_for_human_labels"
    assert b"\r\n" not in output.read_bytes()
    assert result["paper_count"] == 50 and result["leaf_topic_count"] == 16
    assert result["predictions_included"] is False
    with output.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == FIELDS
        rows = list(reader)
    assert len(rows) == 50
    assert rows[0]["title"] == "Paper 0" and rows[0]["abstract"] == "Abstract 0"
    assert [rows[0][f"label_{i}"] for i in range(1, 4)] == ["", "", ""]
    catalog = json.loads(rows[0]["topic_catalog"])
    assert len(catalog) == 16 and catalog[-1]["definition"] == "Definition 15"
    page = output.with_suffix(".html").read_text(encoding="utf-8")
    assert page.count('<article class="paper"') == 50
    assert "Classifier predictions are not shown" in page
    assert all(f"Definition {index}" in page for index in range(16))
    assert "topic_ids" not in page
    assert "must-not-appear" not in page


def test_topic_review_sheet_requires_frozen_hash_bound_inputs_and_never_overwrites(tmp_path):
    works, topic_test, taxonomy = _fixture(tmp_path, status="development_before_freeze")
    with pytest.raises(ValueError, match="frozen classifier"):
        prepare_topic_review_sheet(works, topic_test, taxonomy, tmp_path / "not-written.csv")
    assert not (tmp_path / "not-written.csv").exists()

    valid_dir = tmp_path / "valid"
    valid_dir.mkdir()
    works, topic_test, taxonomy = _fixture(valid_dir)
    config = yaml.safe_load(taxonomy.read_text(encoding="utf-8"))
    config["calibration"]["topic_test_sha256"] = "0" * 64
    taxonomy.write_text(yaml.safe_dump(config), encoding="utf-8")
    with pytest.raises(ValueError, match="does not bind"):
        prepare_topic_review_sheet(works, topic_test, taxonomy, tmp_path / "valid" / "bad.csv")

    existing_dir = tmp_path / "existing"
    existing_dir.mkdir()
    works, topic_test, taxonomy = _fixture(existing_dir)
    output = existing_dir / "present.csv"
    output.write_text("keep", encoding="utf-8")
    with pytest.raises(ValueError, match="overwrite"):
        prepare_topic_review_sheet(works, topic_test, taxonomy, output)
    assert output.read_text(encoding="utf-8") == "keep"


def test_topic_review_allocation_is_deterministic_and_stratified():
    papers = [
        {"paper_id": f"paper:aaai:{index}", "venue_id": "venue:aaai"}
        for index in range(20)
    ] + [
        {"paper_id": f"paper:ijcai:{index}", "venue_id": "venue:ijcai"}
        for index in range(30)
    ]

    first = assign_topic_reviewers(papers, seed=20261108)
    second = assign_topic_reviewers(list(reversed(papers)), seed=20261108)

    assert first == second
    assert len(first["reviewer_paper_ids"]["A"]) == 30
    assert len(first["reviewer_paper_ids"]["B"]) == 30
    assert len(first["overlap_paper_ids"]) == 10
    assert set(first["reviewer_paper_ids"]["A"]) | set(first["reviewer_paper_ids"]["B"]) == {
        row["paper_id"] for row in papers
    }
    assert first["venue_counts"] == {
        "A": {"venue:aaai": 12, "venue:ijcai": 18},
        "B": {"venue:aaai": 12, "venue:ijcai": 18},
    }


def test_reviewer_packets_cover_all_50_blindly_with_30_each_and_10_overlap(tmp_path):
    works, topic_test, taxonomy = _fixture(tmp_path)
    work_rows = [json.loads(line) for line in works.read_text(encoding="utf-8").splitlines()]
    for index, row in enumerate(work_rows):
        row["venue_id"] = "venue:aaai" if index < 20 else "venue:ijcai"
    works.write_text("".join(json.dumps(row) + "\n" for row in work_rows), encoding="utf-8")
    test_rows = [
        {"paper_id": f"paper:{index}", "seed": 20261108}
        for index in range(50)
    ]
    topic_test.write_text("".join(json.dumps(row) + "\n" for row in test_rows), encoding="utf-8")
    config = yaml.safe_load(taxonomy.read_text(encoding="utf-8"))
    config["calibration"]["works_sha256"] = hashlib.sha256(works.read_bytes()).hexdigest()
    config["calibration"]["topic_test_sha256"] = hashlib.sha256(topic_test.read_bytes()).hexdigest()
    taxonomy.write_text(yaml.safe_dump(config), encoding="utf-8")

    master = tmp_path / "master.csv"
    prepare_topic_review_sheet(works, topic_test, taxonomy, master)
    result = prepare_topic_review_packets(master, topic_test, taxonomy, tmp_path / "packets")

    assert result["assignments_per_reviewer"] == {"A": 30, "B": 30}
    assert result["total_assignment_rows"] == 60
    assert result["overlap_count"] == 10
    assert len(result["reviewer_paper_ids"]["A"]) == 30
    assert len(result["reviewer_paper_ids"]["B"]) == 30
    assert result["venue_counts"] == {
        "A": {"venue:aaai": 12, "venue:ijcai": 18},
        "B": {"venue:aaai": 12, "venue:ijcai": 18},
    }
    packet_ids = {}
    for reviewer in ("A", "B"):
        csv_path = tmp_path / "packets" / f"topic-label-sheet-reviewer-{reviewer}.csv"
        html_path = csv_path.with_suffix(".html")
        assert b"\r\n" not in csv_path.read_bytes()
        with csv_path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == 30
        assert {row["labeler"] for row in rows} == {reviewer}
        assert all(not row[f"label_{index}"].strip() for row in rows for index in range(1, 4))
        assert "must-not-appear" not in html_path.read_text(encoding="utf-8")
        assert f"Assigned reviewer: <strong>{reviewer}</strong>" in html_path.read_text(encoding="utf-8")
        packet_ids[reviewer] = {row["paper_id"] for row in rows}
    assert len(packet_ids["A"] | packet_ids["B"]) == 50
    assert len(packet_ids["A"] & packet_ids["B"]) == 10
    assert result["predictions_included"] is False
    assert result["reviewer_sheets"]["A"]["csv"]["sha256"]
    assert result["allocation_manifest"]["sha256"]
    with pytest.raises(ValueError, match="overwrite"):
        prepare_topic_review_packets(master, topic_test, taxonomy, tmp_path / "packets")
