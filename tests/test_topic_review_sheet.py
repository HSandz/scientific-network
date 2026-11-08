"""Prediction-blind topic review sheet contract tests."""

import csv
import hashlib
import json

import pytest
import yaml

from scientific_network.evaluation.topic_review import FIELDS, prepare_topic_review_sheet


def _fixture(tmp_path, *, status="frozen"):
    works = tmp_path / "works.jsonl"
    topic_test = tmp_path / "topic-test.jsonl"
    taxonomy = tmp_path / "topics.yaml"
    works_rows = [
        {"paper_id": f"paper:{index}", "venue_id": "venue:aaai", "year": 2025,
         "roster": {"title": f"Paper {index}"}, "openalex": {"abstract": f"Abstract {index}"}}
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
