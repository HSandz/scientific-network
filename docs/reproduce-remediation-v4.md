# Reproduce the authorized correction and prospective audit

This is a separately versioned correction under [the dated D040 amendment](correction-amendment-2026-11-09.md). Graph v3, its failed 88% audit, old topic references and original local package are historical immutable evidence. There is no classifier tuning, model inference or source reacquisition in this correction. The new seed was committed before drawing. A failed new audit is retained, never repaired by resampling.

Use `uv sync --locked --group dev --extra analysis --extra report` and `uv run pytest`. A fresh clone/ZIP cannot rescore without permitted ignored inputs: restore original works, graph v3/v4, roster and raw caches and check SHA256 against the content and evaluator freezes. Reacquiring newer API data is not a byte-identical restoration. Never put raw caches/full graph/PDFs/models/credentials/database volumes in Git or submission artifacts.

The executed correction command was:

```bash
uv run research-network correct-release-identity \
  --works data/interim/release-v1/works.jsonl \
  --input data/processed/release-graph-v3/graph.json \
  --taxonomy configs/topics-release-v1.yaml \
  --quality configs/quality-release-v1.yaml \
  --source-summary reports/release-v2/graph-summary.json \
  --source-freeze reports/release-v2/freeze-v3.json \
  --protocol configs/evaluation-agent-release-v2.yaml \
  --output-dir data/processed/release-graph-v4 \
  --summary reports/release-v4/graph-summary.json \
  --freeze-output reports/release-v4/content-freeze-v4.json
```

Those output paths are now protected. For a reproducibility check use new unused output paths: do not overwrite the frozen outputs. The correction is deterministic for graph content; freeze timestamps describe actual executions. It uses every matched source authorship, preserves stable surviving IDs, official byline denominators, taxonomy and frozen HAS_TOPIC content, removes all observations for withheld researchers and unsupported organizations, and rebuilds R7–R10. The full machine-readable changes ledger stays ignored; its hash is in the tracked manifest binding/summary. Newly authorless papers receive a missing unresolved reason only; full paper changes are in the ledger.

```bash
uv run research-network validate --input data/processed/release-graph-v4/graph.json \
  --config configs/quality-release-v1.yaml --require-size \
  --output reports/runs/manual-v4-validation.json
uv run research-network analyze --input data/processed/release-graph-v4/graph.json \
  --config configs/analysis-release-v1.yaml --quality-config configs/quality-release-v1.yaml \
  --output reports/runs/manual-v4-analysis.json
uv run python -m scientific_network.analysis.figures \
  --analysis reports/runs/manual-v4-analysis.json \
  --output-dir reports/runs/manual-v4-figures
```

Database integration uses only `neo4j-five-year` on Bolt7689. Import refuses old-version IDs; the executed explicit reset first verified the Docker service/loopback port mapping, current graph ownership and immutable old graph hash, then deleted records only from that service. No volumes were removed. Load/replay receipts and six integrity queries are tracked under release-v4. Do not clear a database as part of an ordinary reproduction without confirming its exact service and ownership.

The new edge-only scorer validates the evaluator freeze, canonical assignments, actual run/context declarations, source hashes, CSV-ledger joins, completion exports and any separately timestamped adjudication start receipt. It creates no new topic reference labels. The historical topic metrics apply to semantically unchanged predictions and exposed historical AI references; no untouched holdout or independent validation is claimed. All results are AI-assessed, human_validation=not_performed, reviewer_independence=not_established, verified_course_accuracy=not_established. Wilson intervals omit evaluator/source/model error.

The exact new audit scoring command, exposure/source overlap and package QA are recorded with measured results in `reports/release-v4/README.md` and WORK-013/014. Choose unused result paths when rescoring; expected exit1 for failed numeric gates is distinct from an invalid-provenance refusal.

Rendering uses `uv run --extra report python -m scientific_network.reporting.release_package --report reports/final-report/report.md --output-dir <unused-ignored-directory>`. Commit report sources before rendering, verify source commit/member hashes/CRC, inspect representative pages and record actual hashes. Personal team/course facts remain pending. Nothing in these commands authorizes pushing, tagging, publication, invitations or submission.
