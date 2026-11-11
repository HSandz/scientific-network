# V5 quality and isolated identity candidate

[Baseline report](baseline-audit.md),[machine census](baseline-audit.json),
[ranked issues](issue-inventory.csv),[identity evidence](identity-error-analysis.md).
Original source/graph data stay ignored;restore permitted original bytes rather
than reacquiring a new API snapshot. No external collection in this work.

```bash
uv sync --locked --group dev --extra analysis --extra report
uv run python -m scientific_network.quality.identity_audit \
  --works data/interim/release-v1/works.jsonl \
  --graph data/processed/release-graph-v4/graph.json \
  --freeze reports/release-v4/content-freeze-v4.json \
  --cache-dir data/raw/openalex-release-v1 \
  --output-dir reports/runs/manual-quality-v5 \
  --detail-dir reports/runs/manual-quality-v5-details
uv run pytest
```

Use unused directories every time. JSON includes venue/year strata,input hashes
and reason categories. Record-level source diagnostics stay in ignored run storage.
Source equality and graph size do not establish semantic accuracy.

## Completed candidate and reports

The final isolated candidate is **v3** (`release-identity-v5-7e6b1a34ffa2`), with
source checkpoint `18f98d0`. Read the [implementation/comparison report](implementation-report.md),
[validation report](validation-report.md), [artifact inventory](artifact-inventory.md),
[quality denominators](candidate-v3/quality-summary.json) and
[preservation/replay receipt](candidate-v3/reproducibility-receipt.json).
Historical candidate v1/v2 reports remain preserved and have superseding notes.

To reproduce the supplementary baseline inventory:

```bash
uv run python -m scientific_network.quality.pipeline_inventory \
  --works data/interim/release-v1/works.jsonl \
  --graph data/processed/release-graph-v4/graph.json \
  --historical-review-queue data/processed/release-graph-v1/review-queue.jsonl \
  --output reports/runs/manual-pipeline-inventory-v5.json
```

To reproduce the final identity candidate, restore the exact hash-bound v4,
original works and OpenAlex cache, then use unused sibling directories:

```bash
uv run python -m scientific_network.resolve.candidate_v5 \
  --config configs/identity-candidate-v5-release-v3.yaml \
  --output-dir reports/runs/manual-identity-v5-data \
  --report-dir reports/runs/manual-identity-v5-reports
uv run research-network validate \
  --input reports/runs/manual-identity-v5-data/graph.json \
  --config configs/quality-release-v1.yaml --require-size \
  --output reports/runs/manual-identity-v5-validation.json
uv run pytest -q tests/test_mentions_v5.py tests/test_identity_audit_v5.py
uv run pytest
```

For a second replay, choose two more unused sibling directories and compare the
SHA256 values under `candidate-manifest.json` → `outputs`. Graph, decisions,
identity index, review queue and centrality score hashes must match; output paths
in comparison manifests describe their actual run locations. All commands are
offline. They neither load Neo4j nor touch the public application. The current
CLI deliberately refuses old protocol configs; historical v1/v2 need their
matching source checkpoints and unused output paths.
