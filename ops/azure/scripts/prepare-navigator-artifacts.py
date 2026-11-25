#!/usr/bin/env python3
"""Export immutable Research Trend Navigator runtime artifacts (no second DB needed, excludes chunks.json)."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
from typing import Any


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def build_navigator_bundle(root: Path, output: Path, *, allow_existing: bool = False) -> dict[str, Any]:
    """Copy precomputed analysis, RAG JSONs (never chunks.json), vectors.sqlite, and eval results into ``output``."""
    root = root.resolve()
    output = output.resolve()
    if (output.exists() or output.is_symlink()) and not allow_existing:
        raise SystemExit(f"Output directory already exists: {output}; choose a new versioned path.")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    analysis_root = root / "reports" / "final-exam" / "analysis-v2"
    analysis_files = sorted(
        p for p in analysis_root.rglob("*") if p.is_file() and not p.name.endswith(".svg")
    )
    file_groups: dict[str, list[tuple[Path, str]]] = {
        "analysis-v2": [(p, str(p.relative_to(analysis_root))) for p in analysis_files],
        "rag-v1": [
            (p, p.name)
            for p in sorted((root / "reports" / "final-exam" / "rag-v1").glob("*.json"))
            if p.name != "chunks.json"
        ],
        "enrichment-v3": [
            (root / "reports" / "enrichment-v3" / "graph-summary.json", "graph-summary.json"),
            (root / "reports" / "enrichment-v3" / "quality.json", "quality.json"),
        ],
        "enrichment-v1": [
            (root / "reports" / "enrichment-v1" / "cooccurrence.json", "cooccurrence.json"),
        ],
        "qa-eval-v1": [
            (root / "reports" / "final-exam" / "qa-eval-v1" / "results.json", "results.json"),
        ],
        "config": [
            (root / "configs" / "rag-v1.yaml", "rag-v1.yaml"),
        ],
    }

    copied: list[dict[str, Any]] = []
    for subdir, items in file_groups.items():
        dest_dir = output / subdir
        dest_dir.mkdir(parents=True, exist_ok=True)
        for src, rel_name in items:
            if src.name == "chunks.json":
                continue
            if not src.is_file():
                raise FileNotFoundError(f"Required Navigator artifact missing: {src}")
            dst = dest_dir / rel_name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            copied.append({
                "source": str(src.relative_to(root)),
                "dest": str(dst.relative_to(output)),
                "bytes": dst.stat().st_size,
                "sha256": digest(dst),
            })

    # Copy and integrity-check SQLite vectors store (exclude any raw abstract-dump files)
    vec_src = root / "data" / "processed" / "rag-v1" / "vectors.sqlite"
    if not vec_src.is_file():
        raise FileNotFoundError(f"Required vectors.sqlite missing: {vec_src}")
    vec_dst = output / "vectors.sqlite"
    shutil.copyfile(vec_src, vec_dst)
    with sqlite3.connect(f"file:{vec_dst}?mode=ro", uri=True) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        vec_rows = conn.execute("SELECT COUNT(*) FROM vectors").fetchone()[0]
    copied.append({
        "source": str(vec_src.relative_to(root)),
        "dest": "vectors.sqlite",
        "bytes": vec_dst.stat().st_size,
        "sha256": digest(vec_dst),
        "vector_rows": int(vec_rows),
    })

    # Guardrail: verify zero chunks.json anywhere in bundle
    assert not list(output.rglob("chunks.json")), "Refusing to package full-abstract chunks.json!"

    total_bytes = sum(x["bytes"] for x in copied)
    manifest = {
        "format": "navigator-runtime-v1",
        "graph_version": "enriched-cb371912e308",
        "excludes": ["chunks.json", "data/interim/release-v1/works.jsonl", "llm-cache"],
        "file_count": len(copied),
        "total_bytes": total_bytes,
        "total_mib": round(total_bytes / (1024 * 1024), 2),
        "files": copied,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--allow-existing", action="store_true")
    args = ap.parse_args()
    print(json.dumps(build_navigator_bundle(args.root, args.output, allow_existing=args.allow_existing), indent=2))
