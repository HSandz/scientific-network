"""Unit test for ops/azure/scripts/prepare-navigator-artifacts.py bundle export."""

import importlib.util
import json
from pathlib import Path
import sqlite3

import numpy as np


def _load_exporter():
    spec = importlib.util.spec_from_file_location(
        "prepare_navigator_artifacts",
        Path("ops/azure/scripts/prepare-navigator-artifacts.py").resolve(),
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_prepare_navigator_bundle_excludes_chunks_and_hashes_all(tmp_path: Path):
    mod = _load_exporter()
    root = tmp_path / "repo"
    (root / "reports/final-exam/analysis-v2/smallworld").mkdir(parents=True)
    (root / "reports/final-exam/rag-v1").mkdir(parents=True)
    (root / "reports/enrichment-v3").mkdir(parents=True)
    (root / "reports/enrichment-v1").mkdir(parents=True)
    (root / "reports/final-exam/qa-eval-v1").mkdir(parents=True)
    (root / "configs").mkdir(parents=True)
    (root / "data/processed/rag-v1").mkdir(parents=True)

    (root / "reports/final-exam/analysis-v2/smallworld/smallworld.json").write_text('{"ok": true}\n', encoding="utf-8")
    (root / "reports/final-exam/rag-v1/demo-cache.json").write_text('{"demos": []}\n', encoding="utf-8")
    # Place chunks.json inside rag-v1 and assert exporter excludes it cleanly
    (root / "reports/final-exam/rag-v1/chunks.json").write_text('{"secret": "abstract"}\n', encoding="utf-8")
    (root / "reports/enrichment-v3/graph-summary.json").write_text('{"graph_version": "enriched-cb371912e308"}\n', encoding="utf-8")
    (root / "reports/enrichment-v3/quality.json").write_text('{"e4_v3": {}}\n', encoding="utf-8")
    (root / "reports/enrichment-v1/cooccurrence.json").write_text('{}\n', encoding="utf-8")
    (root / "reports/final-exam/qa-eval-v1/results.json").write_text('{"protocol_version": "qa-eval-v1"}\n', encoding="utf-8")
    (root / "configs/rag-v1.yaml").write_text("version: rag-v1\n", encoding="utf-8")

    vec_db = root / "data/processed/rag-v1/vectors.sqlite"
    with sqlite3.connect(vec_db) as conn:
        conn.execute("CREATE TABLE vectors (kind TEXT, id TEXT, text TEXT, metadata_json TEXT, dim INTEGER, embedding BLOB)")
        conn.execute("INSERT INTO vectors VALUES ('entity_description', 'x', 'hello', '{}', 4, ?)", (np.ones(4, dtype=np.float32).tobytes(),))
        conn.commit()

    out = tmp_path / "bundle"
    manifest = mod.build_navigator_bundle(root, out)
    assert manifest["format"] == "navigator-runtime-v1"
    assert not list(out.rglob("chunks.json"))
    assert (out / "vectors.sqlite").is_file()
    assert (out / "manifest.json").is_file()
    assert (out / "analysis-v2/smallworld/smallworld.json").is_file()
    assert json.loads((out / "qa-eval-v1/results.json").read_text())["protocol_version"] == "qa-eval-v1"
