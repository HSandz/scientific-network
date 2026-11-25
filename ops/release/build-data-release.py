#!/usr/bin/env python3
"""Build the versioned Research Trend Navigator data release bundle (local only; never publishes).

Packs the enriched graph v3 (with abstract-sentence evidence excerpts removed), the enrichment,
quality and analysis outputs, the QA benchmark questions and references, the community reports and
entity descriptions, a MANIFEST.json with SHA-256 hashes, a README and per-source licence and
attribution notes. Follows docs/source-policy.md: no abstract text, no raw downloads, no PDFs.

The build verifies itself. When the local OpenAlex works table is available, it scans every bundled
text file for verbatim 10-word windows of corpus abstracts (windows inside the paper's own title
excluded) and fails if any are found.

Usage (from the repository root):
  uv run python ops/release/build-data-release.py \
      --out-dir reports/runs/WORK-2026-11-26-001/data-release
Publishing (GitHub release or Zenodo) is a separate, manual step that needs the user's approval.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import time
from typing import Any

RELEASE_ID = "research-trend-navigator-data-v1"
GRAPH_PATH = Path("data/processed/enriched-graph-v3/graph.json")
GRAPH_SHA256 = "37ee8c59d8245d452e42575b7afbb13808b5f835d51c9ee838bd5581434633e3"
GRAPH_VERSION = "enriched-cb371912e308"
BASE_GRAPH_VERSION = "release-d3c788c3114a"
WORKS_JSONL = Path("data/interim/release-v1/works.jsonl")

LICENCE_CLASSES: dict[str, str] = {
    "graph": "mixed: see LICENSES.md (OpenAlex/ROR/Wikidata-derived facts CC0 1.0; Wikipedia titles, URLs and revision IDs; project-derived edges: licence pending)",
    "project": "project-authored derived data: licence pending team decision (see LICENSES.md)",
    "ai_generated": "AI-generated text (labelled 'AI-generated from graph data'); project output, licence pending team decision",
    "wikipedia_mixed": "mixed: Wikipedia lead excerpts CC BY-SA 4.0 with per-record attribution; other descriptions AI-generated or template text (licence pending)",
    "source_manifest": "project-authored manifest of third-party sources (URLs, revision IDs, hashes; no source text)",
}

# (source path or directory, bundle path, licence class, description)
INCLUDES: list[tuple[str, str, str, str]] = [
    ("data/processed/enriched-graph-v3/summary.json", "graph/summary.json", "project", "Graph v3 node/edge counts by label and predicate"),
    ("reports/enrichment-v1/sources.json", "enrichment/sources-e1.json", "source_manifest", "E1 enrichment source manifest (counts, licences, selection rules)"),
    ("reports/enrichment-v1/entities.json", "enrichment/v1/entities.json", "project", "E2 entity extraction outputs (v1)"),
    ("reports/enrichment-v1/linking.json", "enrichment/v1/linking.json", "project", "E2 Wikidata/Wikipedia linking outputs (v1)"),
    ("reports/enrichment-v1/cooccurrence.json", "enrichment/v1/cooccurrence.json", "project", "Method/task/dataset co-occurrence counts"),
    ("reports/enrichment-v1/k1-model-selection.json", "enrichment/v1/k1-model-selection.json", "project", "K1 extraction-arm model comparison"),
    ("reports/enrichment-v1/k1-model-selection.md", "enrichment/v1/k1-model-selection.md", "project", "K1 model selection report (with 2026-11-26 answer-quality arm)"),
    ("reports/enrichment-v3/graph-summary.json", "enrichment/v3/graph-summary.json", "project", "Enrichment v3 graph summary"),
    ("reports/enrichment-v3/link-guard.json", "enrichment/v3/link-guard.json", "project", "Linking guard decision"),
    ("reports/enrichment-v3/applied-to-decision.json", "enrichment/v3/applied-to-decision.json", "project", "APPLIED_TO adoption decision"),
    ("reports/enrichment-v3/type-conflicts.json", "enrichment/v3/type-conflicts.json", "project", "Entity type conflicts"),
    ("reports/enrichment-v1/quality.json", "quality/enrichment-v1/quality.json", "project", "E4 quality v1 (AI-assessed)"),
    ("reports/enrichment-v1/quality.md", "quality/enrichment-v1/quality.md", "project", "E4 quality v1 report"),
    ("reports/enrichment-v2/quality.json", "quality/enrichment-v2/quality.json", "project", "E4 quality v2 (AI-assessed)"),
    ("reports/enrichment-v2/quality.md", "quality/enrichment-v2/quality.md", "project", "E4 quality v2 report"),
    ("reports/enrichment-v3/quality.json", "quality/enrichment-v3/quality.json", "project", "E4 quality v3 (AI-assessed)"),
    ("reports/enrichment-v3/quality.md", "quality/enrichment-v3/quality.md", "project", "E4 quality v3 report"),
    ("reports/final-exam/analysis-v2", "analysis/analysis-v2", "project", "S1-S3 network analysis v2 (small world, ranking, communities, trends)"),
    ("data/manifests/qa-benchmark-v1/questions.jsonl", "benchmark/questions.jsonl", "project", "QA benchmark questions (frozen)"),
    ("data/manifests/qa-benchmark-v1/references-v1.jsonl", "benchmark/references-v1.jsonl", "project", "Deterministic Cypher reference answers (frozen)"),
    ("data/manifests/qa-benchmark-v1/receipt.json", "benchmark/receipt.json", "project", "Question freeze receipt"),
    ("data/manifests/qa-benchmark-v1/references-v1-receipt.json", "benchmark/references-v1-receipt.json", "project", "Reference freeze receipt"),
    ("reports/final-exam/qa-eval-v1/results.json", "evaluation/qa-eval-v1/results.json", "project", "QA benchmark results (graph agreement; AI-assessed citation, pairwise and supplementary sections)"),
    ("reports/final-exam/qa-eval-v1/results.md", "evaluation/qa-eval-v1/results.md", "project", "QA benchmark results report"),
    ("reports/final-exam/k1-answer/results.json", "evaluation/k1-answer/results.json", "project", "K1 answer-quality arm (development figures)"),
    ("reports/final-exam/k1-answer/results.md", "evaluation/k1-answer/results.md", "project", "K1 answer-quality arm report"),
    ("reports/final-exam/rag-v1/community-reports.json", "graphrag/community-reports.json", "ai_generated", "GraphRAG community reports (AI-generated from graph data)"),
    ("reports/final-exam/rag-v1/research-communities.json", "graphrag/research-communities.json", "project", "Research-graph Leiden communities used by GraphRAG"),
    ("reports/final-exam/rag-v1/entity-descriptions.json", "graphrag/entity-descriptions.json", "wikipedia_mixed", "Entity descriptions: Wikipedia lead excerpts (CC BY-SA 4.0, attributed), AI-generated and template text"),
    ("reports/final-exam/rag-v1/index-summary.json", "graphrag/index-summary.json", "project", "GraphRAG index summary"),
    ("reports/final-exam/rag-v1/report-stats.json", "graphrag/report-stats.json", "project", "Community report statistics"),
]

EXCLUSIONS: list[tuple[str, str]] = [
    ("Evidence `excerpt` text in graph v3 (14,222 inferred_topic records)", "Abstract sentences; source policy publishes IDs, locators and hashes, not abstract text. Replaced by `excerpt_sha256`."),
    ("data/processed/rag-v1/chunks.json", "Abstract sentence chunks (abstract text)."),
    ("data/processed/rag-v1/vectors.sqlite", "Stores abstract-chunk text next to the embeddings."),
    ("6 generated entity descriptions in graphrag/entity-descriptions.json", "They copied a clause verbatim from an abstract; replaced by `description_sha256`."),
    ("data/interim/release-v1/works.jsonl and all OpenAlex responses", "Raw downloads; contain abstracts (inverted indexes); immutable local cache."),
    ("data/raw/** (including data/raw/enrichment-v1 Wikipedia/Wikidata fetches)", "Raw downloads; Wikipedia page text stays local (source policy)."),
    ("Paper PDFs and GROBID TEI", "Not redistributable; none are bundled."),
    ("LLM caches and call logs (data/interim/**/llm-cache, reports/runs/**)", "Prompts contain abstract text; run logs are local."),
    ("reports/final-exam/qa-eval-v1/raw-outputs.jsonl and judging packets", "System answers can quote abstract sentences; packets contain abstracts. Results summaries are included instead."),
    ("Audit and topic-label review sheets (reports/release-v*/audit, completed/*)", "Show abstracts or abstract excerpts to reviewers (see reports/final-exam/repo-hygiene-2026-11-26.md)."),
    ("Frozen v4 graph file (data/processed/release-graph-v4)", "The v3 graph already contains the full v4 core layer; the v4 file stays frozen and local."),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def write_public_graph(dest: Path) -> dict[str, Any]:
    actual = sha256_file(GRAPH_PATH)
    if actual != GRAPH_SHA256:
        raise SystemExit(f"graph SHA-256 mismatch: expected {GRAPH_SHA256}, got {actual}")
    g = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    if g.get("graph_version") != GRAPH_VERSION:
        raise SystemExit(f"unexpected graph_version {g.get('graph_version')}")
    redacted = 0
    for ev in g.get("evidence") or []:
        x = ev.get("excerpt")
        if isinstance(x, str) and x:
            ev["excerpt_sha256"] = hashlib.sha256(x.encode("utf-8")).hexdigest()
            ev["excerpt"] = None
            ev["excerpt_redacted"] = "abstract text not redistributed (docs/source-policy.md)"
            redacted += 1
    g["public_release"] = {
        "release_id": RELEASE_ID,
        "derived_from_graph_sha256": GRAPH_SHA256,
        "evidence_excerpts_redacted": redacted,
        "note": "Identical to graph v3 except evidence excerpts (abstract sentences) are replaced by their SHA-256.",
    }
    dest.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(dest, "wt", encoding="utf-8", compresslevel=9) as fh:
        json.dump(g, fh, ensure_ascii=False, separators=(",", ":"))
    return {"redacted_excerpts": redacted, "nodes": len(g["nodes"]), "edges": len(g["edges"])}


_TOK = re.compile(r"[a-z0-9]+")


def abstract_shingles(window: int = 10) -> set[str] | None:
    """Every aligned 10-word window of every corpus abstract, minus windows inside the paper's title."""
    if not WORKS_JSONL.exists():
        return None
    shingles: set[str] = set()
    with WORKS_JSONL.open(encoding="utf-8") as fh:
        for line in fh:
            o = json.loads(line)
            oa = o.get("openalex") or {}
            words = _TOK.findall((oa.get("abstract") or "").lower())
            title = " ".join(_TOK.findall((oa.get("title") or "").lower()))
            for i in range(0, max(0, len(words) - window + 1), window):
                w = " ".join(words[i:i + window])
                if w not in title:
                    shingles.add(w)
    return shingles


def _has_window(text: str, shingles: set[str], window: int = 10) -> bool:
    words = _TOK.findall(text.lower())
    return any(" ".join(words[i:i + window]) in shingles for i in range(len(words) - window + 1))


def sanitize_entity_descriptions(path: Path, shingles: set[str] | None) -> int:
    """Redact the few generated descriptions that copied a clause verbatim from an abstract."""
    if shingles is None:
        raise SystemExit(f"{WORKS_JSONL} is needed to check entity descriptions for abstract text")
    data = json.loads(path.read_text(encoding="utf-8"))
    n = 0
    for rec in data.get("descriptions") or []:
        desc = rec.get("description")
        if isinstance(desc, str) and _has_window(desc, shingles):
            rec["description_sha256"] = hashlib.sha256(desc.encode("utf-8")).hexdigest()
            rec["description"] = None
            rec["description_redacted"] = "generated text quoted an abstract verbatim; not redistributed (docs/source-policy.md)"
            n += 1
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return n


def abstract_scan(bundle: Path, shingles: set[str] | None, window: int = 10) -> dict[str, Any]:
    """Count verbatim abstract windows in bundled text files (titles excluded)."""
    if shingles is None:
        return {"status": "not_run", "reason": f"{WORKS_JSONL} not available"}
    hits: dict[str, int] = {}
    for path in sorted(bundle.rglob("*")):
        if not path.is_file():
            continue
        opener = gzip.open if path.suffix == ".gz" else open
        n = 0
        with opener(path, "rt", encoding="utf-8", errors="ignore") as fh:  # type: ignore[operator]
            for line in fh:
                words = _TOK.findall(line.lower())
                for i in range(len(words) - window + 1):
                    if " ".join(words[i:i + window]) in shingles:
                        n += 1
        if n:
            hits[str(path.relative_to(bundle))] = n
    return {"status": "run", "window_words": window, "abstract_shingles": len(shingles), "files_with_hits": hits}


def readme(manifest: dict[str, Any]) -> str:
    files = "\n".join(
        f"| `{f['path']}` | {f['bytes']:,} | {f['description']} |" for f in manifest["files"]
    )
    excl = "\n".join(f"- **{what}**: {why}" for what, why in EXCLUSIONS)
    return f"""# {RELEASE_ID}

Data release of the **Research Trend Navigator** (course final exam, Social Media Network Analysis for
Business): an enriched knowledge graph of AAAI and IJCAI main-track papers, 2021–2025, with network
analysis, GraphRAG community reports and a multi-hop QA benchmark.

- Graph: `{GRAPH_VERSION}` (enriched v3), built on the frozen release graph `{BASE_GRAPH_VERSION}` (v4).
- Source graph SHA-256: `{GRAPH_SHA256}`. The bundled graph differs only in redacted evidence excerpts
  (`public_release` block inside the file).
- Built {manifest['built_at']} from code commit `{manifest['code_commit']}`.
- Hashes of every file: `MANIFEST.json`.

## Contents

| File | Bytes | Description |
| --- | --- | --- |
{files}

## Excluded and why

{excl}

## Quality statement

All quality figures in this bundle (entity and relation precision, linking accuracy, citation
validity, pairwise and supplementary precision) are **AI-assessed** by isolated LLM evaluators. They
are not human annotations or verified course accuracy, and Wilson and bootstrap intervals exclude
evaluator error. The QA factual scores measure agreement with the graph's edges, not truth. Generated
text (community reports, many entity descriptions) is labelled "AI-generated from graph data".

## Licences and attribution

See `LICENSES.md`. Wikipedia excerpts are CC BY-SA 4.0, and each record carries its page URL, revision
ID and attribution. OpenAlex, ROR and Wikidata facts are CC0 1.0. The licence for project-authored data
is **pending a team decision** and is not granted by this file.

## Loading

The graph file is the project's graph JSON (`nodes`, `edges`, `evidence`, `node_enrichments`,
`affiliation_observations`). Load it with the repository's loader into an isolated Neo4j Community
database; see the repository README.
"""


LICENSES_MD = """# Licences and attribution by source

| Source | What this bundle contains from it | Licence |
| --- | --- | --- |
| OpenAlex (works, authorships, institutions, references) | IDs, titles, years, authorship and affiliation links, citation edges, DOIs; **no abstract text** | CC0 1.0 (OpenAlex data). Abstract redistribution is not assumed, so abstracts are excluded. |
| ROR | organization identifiers | CC0 1.0 |
| Wikidata | QIDs, types, parents, countries, inception, short descriptions | CC0 1.0 |
| English Wikipedia | page titles, URLs, revision IDs; lead excerpts in `graphrag/entity-descriptions.json` (records with `license: "CC BY-SA 4.0"`) | CC BY-SA 4.0. Each excerpt carries `wikipedia_url`, `wikipedia_revision_id` and an attribution line; reuse must keep the attribution and share alike. |
| AAAI and IJCAI official proceedings pages | paper roster membership, official URLs and PDF URLs (links only; no PDFs) | Licence of the pages not stated; factual bibliographic metadata and links only. |
| AI-generated text (Qwen3.5-4B, Q4_K_M, local llama.cpp) | community reports; entity descriptions marked `generation_method` LLM | Project output, labelled "AI-generated from graph data". The model is Apache-2.0; licence of this text: **pending team decision**. |
| Project-authored derived data | enrichment entities and relations, analysis outputs, benchmark questions and references, evaluation results | **Pending team decision.** No licence is granted until the team chooses one. |
"""


def build(out_dir: Path) -> dict[str, Any]:
    bundle = out_dir / RELEASE_ID
    if bundle.exists():
        shutil.rmtree(bundle)
    bundle.mkdir(parents=True)
    graph_info = write_public_graph(bundle / "graph" / "enriched-graph-v3.public.json.gz")
    files: list[dict[str, Any]] = [{
        "path": "graph/enriched-graph-v3.public.json.gz",
        "source": str(GRAPH_PATH),
        "licence": LICENCE_CLASSES["graph"],
        "description": f"Enriched graph v3 (gzip JSON), evidence excerpts redacted ({graph_info['redacted_excerpts']:,})",
    }]
    for src, dst, lic, desc in INCLUDES:
        sp = Path(src)
        if not sp.exists():
            raise SystemExit(f"missing input {src}")
        targets = [(p, Path(dst) / p.relative_to(sp)) for p in sorted(sp.rglob("*")) if p.is_file()] if sp.is_dir() else [(sp, Path(dst))]
        for s, d in targets:
            (bundle / d).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(s, bundle / d)
            files.append({"path": str(d), "source": str(s), "licence": LICENCE_CLASSES[lic], "description": desc})
    shingles = abstract_shingles()
    redacted_desc = sanitize_entity_descriptions(bundle / "graphrag" / "entity-descriptions.json", shingles)
    graph_info["redacted_entity_descriptions"] = redacted_desc
    for f in files:
        p = bundle / f["path"]
        f["bytes"] = p.stat().st_size
        f["sha256"] = sha256_file(p)
    manifest: dict[str, Any] = {
        "release_id": RELEASE_ID,
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "code_commit": git_head(),
        "graph_version": GRAPH_VERSION,
        "base_graph_version": BASE_GRAPH_VERSION,
        "source_graph_sha256": GRAPH_SHA256,
        "graph": graph_info,
        "ai_assessed_quality": True,
        "files": files,
        "excluded": [{"what": w, "why": y} for w, y in EXCLUSIONS],
    }
    (bundle / "LICENSES.md").write_text(LICENSES_MD, encoding="utf-8")
    (bundle / "README.md").write_text(readme(manifest), encoding="utf-8")
    scan = abstract_scan(bundle, shingles)
    manifest["abstract_text_scan"] = scan
    manifest["readme_sha256"] = sha256_file(bundle / "README.md")
    manifest["licenses_sha256"] = sha256_file(bundle / "LICENSES.md")
    (bundle / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if scan.get("files_with_hits"):
        raise SystemExit(f"abstract text found in bundle: {scan['files_with_hits']}")
    tar_path = out_dir / f"{RELEASE_ID}.tar.gz"
    with tarfile.open(tar_path, "w:gz", compresslevel=9) as tar:
        tar.add(bundle, arcname=RELEASE_ID)
    receipt = {
        "release_id": RELEASE_ID,
        "tarball": str(tar_path),
        "tarball_bytes": tar_path.stat().st_size,
        "tarball_sha256": sha256_file(tar_path),
        "manifest_sha256": sha256_file(bundle / "MANIFEST.json"),
        "files": len(files) + 3,
        "uncompressed_bytes": sum(p.stat().st_size for p in bundle.rglob("*") if p.is_file()),
        "graph": graph_info,
        "abstract_text_scan": {k: v for k, v in scan.items() if k != "files_with_hits"} | {"files_with_hits": len(scan.get("files_with_hits") or {})},
        "code_commit": manifest["code_commit"],
    }
    (out_dir / f"{RELEASE_ID}.receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out-dir", type=Path, required=True, help="Output directory (keep it under an ignored path).")
    args = ap.parse_args()
    print(json.dumps(build(args.out_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
