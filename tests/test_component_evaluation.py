import hashlib
import json
from pathlib import Path

import pytest

from scientific_network.cli import main


ROOT = Path(__file__).resolve().parents[1]
QUALITY = ROOT / "configs/quality.yaml"


def _packet(tmp_path: Path):
    units = []
    unit_values = {
        "researcher_resolution": {
            "researcher-positive": True, "researcher-negative": False,
        },
        "organization_resolution": {
            "organization-positive": True, "organization-negative": False,
        },
        "affiliation_triples": {
            "affiliation-p1-a1": ["org-a"], "affiliation-p2-a1": [],
        },
        "topic_labels": {
            "topic-p1-a": ["topic-a"], "topic-p2-a": [],
        },
        "citation_targets": {
            "reference-r1": {"is_reference": True, "core_target_id": "p2"},
            "reference-r2": {"is_reference": False, "core_target_id": None},
        },
    }
    for component, labels in unit_values.items():
        for unit_id in labels:
            metadata = {}
            if component == "researcher_resolution":
                positive = unit_id.endswith("positive")
                metadata = {
                    "left_id": f"researcher-left-{unit_id}",
                    "right_id": f"researcher-right-{unit_id}",
                    "pair_type": "positive_link_opportunity" if positive else "common_name_negative",
                }
            elif component == "organization_resolution":
                positive = unit_id.endswith("positive")
                metadata = {
                    "left_id": f"organization-left-{unit_id}",
                    "right_id": f"organization-right-{unit_id}",
                    "pair_type": "positive_link_opportunity" if positive else "common_name_negative",
                }
            elif component == "affiliation_triples":
                metadata = {"author_position_id": unit_id, "complete_label_set": True}
            elif component == "topic_labels":
                metadata = {
                    "paper_id": "p1" if "p1" in unit_id else "p2",
                    "complete_label_set": True,
                }
            elif component == "citation_targets":
                metadata = {
                    "source_paper_id": "p1",
                    "reference_id": "r1" if unit_id.endswith("r1") else "r2",
                }
            units.append({
                "unit_id": unit_id,
                "component": component,
                "stratum": {"venue_year": "FixtureConf-2025"},
                "sampling_weight": 1.0,
                **metadata,
            })
    frame = {
        "schema_version": "component-evaluation-frame-v1",
        "frame_id": "synthetic-component-frame-v1",
        "status": "frozen",
        "sample_role": "development",
        "purpose": "synthetic_protocol_only",
        "is_synthetic": True,
        "units": units,
        "label_universes": {
            "topic_labels": ["topic-a", "topic-b"],
            "organization_ids": ["org-a", "org-b"],
        },
        "coverage_frame": {
            "population_scope": "development_sample",
            "eligible_core_papers": [
                {"paper_id": "p1", "abstract_available": True, "stratum": {"venue_year": "FixtureConf-2025"}},
                {"paper_id": "p2", "abstract_available": False, "stratum": {"venue_year": "FixtureConf-2025"}},
            ],
            "author_positions": [
                {"position_id": "affiliation-p1-a1", "paper_id": "p1"},
                {"position_id": "affiliation-p2-a1", "paper_id": "p2"},
            ],
        },
    }
    frame_path = tmp_path / "frame.json"
    frame_raw = json.dumps(frame, indent=2).encode()
    frame_path.write_bytes(frame_raw)
    frame_sha = hashlib.sha256(frame_raw).hexdigest()
    config_raw = QUALITY.read_bytes()
    config_sha = hashlib.sha256(config_raw).hexdigest()
    predictions = {
        "schema_version": "component-predictions-v1",
        "frame_sha256": frame_sha,
        "quality_config_sha256": config_sha,
        "method_version": "fixture-method-v1",
        "generated_at": "2026-11-01T00:00:00+00:00",
        "labels": {
            "researcher-positive": True,
            "researcher-negative": True,
            "organization-positive": True,
            "organization-negative": False,
            "affiliation-p1-a1": ["org-a"],
            "affiliation-p2-a1": ["org-b"],
            "topic-p1-a": ["topic-a", "topic-b"],
            "topic-p2-a": [],
            "reference-r1": {"is_reference": True, "core_target_id": "p2"},
            "reference-r2": {"is_reference": False, "core_target_id": None},
        },
        "coverage": {
            "accepted_affiliation_position_ids": ["affiliation-p1-a1"],
            "topic_covered_paper_ids": ["p1"],
        },
    }
    predictions_path = tmp_path / "predictions.json"
    predictions_path.write_text(json.dumps(predictions, indent=2))
    predictions_sha = hashlib.sha256(predictions_path.read_bytes()).hexdigest()
    reviewers = []
    for reviewer_id in ("reviewer-a", "reviewer-b"):
        reviewers.append({
            "reviewer_id": reviewer_id,
            "labels": {
                unit_id: {"value": value, "evidence_locators": [f"fixture://{unit_id}"]}
                for labels in unit_values.values()
                for unit_id, value in labels.items()
            },
        })
    gold = {
        "schema_version": "component-gold-v1",
        "frame_sha256": frame_sha,
        "predictions_sha256": predictions_sha,
        "prediction_frozen_at": predictions["generated_at"],
        "first_review_started_at": "2026-11-02T00:00:00+00:00",
        "reviewers": reviewers,
        "adjudications": [],
    }
    gold_path = tmp_path / "gold.json"
    gold_path.write_text(json.dumps(gold, indent=2))
    return frame_path, predictions_path, gold_path


def test_evaluate_command_scores_synthetic_components_and_core_coverage(tmp_path):
    frame, predictions, gold = _packet(tmp_path)
    output = tmp_path / "evaluation.json"
    assert main([
        "evaluate", "--frame", str(frame), "--predictions", str(predictions),
        "--gold", str(gold), "--config", str(QUALITY), "--output", str(output),
    ]) == 0
    result = json.loads(output.read_text())
    assert result["status"] == "synthetic_protocol_only"
    assert result["release_status"] == "ineligible_synthetic"
    assert result["review"]["independence_status"] == "input_declared_unverified"
    assert result["components"]["researcher_resolution"]["sample"]["false_positive"] == 1
    assert result["components"]["researcher_resolution"]["by_pair_type"]["common_name_negative"]["sample"]["false_positive"] == 1
    assert result["components"]["affiliation_triples"]["sample"]["precision"] == 0.5
    assert result["components"]["topic_labels"]["sample"]["false_positive"] == 1
    assert result["components"]["topic_labels"]["per_label"]["topic-b"]["gold_support"] == 0
    assert result["components"]["topic_labels"]["macro_sampling_weighted"]["f1"] == 0.5
    assert result["components"]["citation_targets"]["core_target_resolution"]["sample"]["recall"] == 1.0
    assert result["components"]["organization_resolution"]["reviewer_agreement"]["exact_unit_agreement_fraction"] == 1.0
    assert result["coverage"]["abstracts"]["numerator"] == 1
    assert result["coverage"]["author_paper_affiliation_resolution"]["denominator"] == 2
    assert result["coverage"]["papers_with_supported_topics"]["rate"] == 0.5


def test_disagreement_requires_distinct_reasoned_adjudication(tmp_path):
    frame, predictions, gold_path = _packet(tmp_path)
    gold = json.loads(gold_path.read_text())
    gold["reviewers"][1]["labels"]["affiliation-p1-a1"]["value"] = []
    gold_path.write_text(json.dumps(gold))
    with pytest.raises(ValueError, match="requires a reasoned adjudication"):
        from scientific_network.evaluation.components import evaluate_components
        evaluate_components(frame, predictions, gold_path, QUALITY, tmp_path / "missing-adjudication.json")

    gold["adjudications"] = [{
        "unit_id": "affiliation-p1-a1",
        "adjudicator_id": "adjudicator-c",
        "value": ["org-a"],
        "reason": "The byline marker maps to the printed organization block.",
        "evidence_locators": ["fixture://adjudicated/affiliation-p1-a1"],
    }]
    gold_path.write_text(json.dumps(gold))
    from scientific_network.evaluation.components import evaluate_components
    result, code = evaluate_components(frame, predictions, gold_path, QUALITY, tmp_path / "adjudicated.json")
    assert code == 0
    assert result["review"]["adjudicated_unit_count"] == 1


def test_real_component_results_require_frozen_quality_and_release_core_frame(tmp_path):
    frame_path, predictions_path, gold_path = _packet(tmp_path)
    frame = json.loads(frame_path.read_text())
    frame["is_synthetic"] = False
    frame["sample_role"] = "test"
    frame["purpose"] = "held_out_component_evaluation"
    frame["coverage_frame"]["population_scope"] = "eligible_release_core"
    frame_raw = json.dumps(frame, indent=2).encode()
    frame_path.write_bytes(frame_raw)
    predictions = json.loads(predictions_path.read_text())
    predictions["frame_sha256"] = hashlib.sha256(frame_raw).hexdigest()
    predictions_path.write_text(json.dumps(predictions, indent=2))
    gold = json.loads(gold_path.read_text())
    gold["frame_sha256"] = hashlib.sha256(frame_raw).hexdigest()
    gold["predictions_sha256"] = hashlib.sha256(predictions_path.read_bytes()).hexdigest()
    gold_path.write_text(json.dumps(gold, indent=2))
    from scientific_network.evaluation.components import evaluate_components
    with pytest.raises(ValueError, match="requires a frozen quality config"):
        evaluate_components(frame_path, predictions_path, gold_path, QUALITY, tmp_path / "real.json")

