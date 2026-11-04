import json
from pathlib import Path

import pytest

from scientific_network.cli import main
from scientific_network.pipeline import STAGES, IMPLEMENTED_STAGES

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/synthetic_graph.json"
QUALITY = ROOT / "configs/quality.yaml"


def test_validation_report_preserves_synthetic_and_unmeasured_status(tmp_path, capsys):
    output = tmp_path / "summary.json"
    assert main(["validate", "--input", str(FIXTURE), "--config", str(QUALITY), "--output", str(output)]) == 0
    report = json.loads(output.read_text())
    assert report["validation_scope"] == "structural_only"
    assert report["release_status"] == "ineligible_synthetic"
    assert report["semantic_accuracy"] == "not_measured"
    assert not report["size_checks"]["unique_core_factual_edges"]


def test_size_gate_returns_nonzero_for_small_example(capsys):
    assert main(["validate", "--input", str(FIXTURE), "--config", str(QUALITY), "--require-size"]) == 1


@pytest.mark.parametrize("stage", sorted(set(STAGES) - IMPLEMENTED_STAGES))
def test_pending_stage_cannot_write_false_success(stage, tmp_path, capsys):
    output = tmp_path / "would-be-results.json"
    assert main([stage, "--input", "not-fetched", "--output", str(output)]) == 2
    assert not output.exists()
    assert json.loads(capsys.readouterr().err)["status"] == "not_implemented"


def test_output_cannot_overwrite_raw_input(tmp_path, capsys):
    artifact = tmp_path / "graph.json"
    original = FIXTURE.read_bytes()
    artifact.write_bytes(original)
    assert main(["validate", "--input", str(artifact), "--config", str(QUALITY), "--output", str(artifact)]) == 1
    assert artifact.read_bytes() == original


def test_malformed_graph_fails_without_traceback(tmp_path, capsys):
    artifact = tmp_path / "bad.json"
    artifact.write_text("{}")
    assert main(["validate", "--input", str(artifact), "--config", str(QUALITY)]) == 1
    assert json.loads(capsys.readouterr().err)["status"] == "error"
