# Reproduce the agent evaluation and local report

This procedure scores recorded source-backed AI judgments. It does not create new
judgments, establish independent gold labels or certify course accuracy. The
immutable content receipt remains `reports/release-v2/freeze-v3.json`; the separate
evaluator receipt is `reports/release-v3/evaluation-freeze-v1.json`.

## Environment and inputs

```bash
uv sync --locked --group dev --extra analysis --extra report
uv run pytest
uv run research-network schema
```

The test suite uses invented fixtures only and does not download models or collect
the corpus. The optional `report` extra installs the Markdown renderer. Rendering
also requires `google-chrome`, Poppler's `pdfinfo`, `pdftotext`, `pdfimages`,
`mutool` and DejaVu Sans fonts on the host. All commands run from the repository root.

Full graph JSON, the roster, immutable raw caches and work records are local
ignored inputs. A fresh clone or submission ZIP does not contain them. Restore the
original permitted inputs and verify their hashes against the content/evaluator
freezes before scoring. New acquisition can consume API allowance and returns a
newer source snapshot; it is not automatically a byte-identical reconstruction.
Do not rebuild the graph, rerun the frozen classifier, resample or tune from these
labels. Existing release-plan/work-log commands describe the original build.

Completed per-channel CSVs and source ledgers are preserved under
`reports/release-v3/completed/`. Combined ledgers concatenate the original A/B
records without changing their decisions. `completion-receipt-v1.json` binds all
exports/ledgers and records that both topic exports were frozen before edge
review began. A/B contexts did not share answers. Precise runtime model/provider
IDs and sampling settings are unknown, explicitly recorded in the evaluator
freeze; separate contexts do not establish independence.

## Score the recorded exports

Choose unused output paths. Refusing existing outputs protects frozen results.
The command validates graph/config/assignment/source hashes, evaluator identities,
CSV-to-ledger joins and review order before scoring both classifiers and the edge
sample. Sample supplements are never pooled into the global precision estimate.

```bash
uv run research-network score-agent-review \
  --evaluation-freeze reports/release-v3/evaluation-freeze-v1.json \
  --completion-receipt reports/release-v3/completion-receipt-v1.json \
  --protocol configs/evaluation-agent-release-v1.yaml \
  --topic-ledger reports/release-v3/completed/topic-ledger.jsonl \
  --edge-ledger reports/release-v3/completed/edge-ledger.jsonl \
  --graph data/processed/release-graph-v3/graph.json \
  --quality configs/quality-agent-release-v1.yaml \
  --graph-v1 data/processed/release-graph-v1/graph.json \
  --topic-test data/manifests/release-v1/topic-test.jsonl \
  --taxonomy configs/topics-release-v1.yaml \
  --allocation reports/release-v1/audit/topic-review-allocation.json \
  --master-sheet reports/release-v1/audit/topic-label-sheet.csv \
  --topic-reviewer-a reports/release-v3/completed/A-topics.csv \
  --topic-reviewer-b reports/release-v3/completed/B-topics.csv \
  --graph-freeze reports/release-v2/freeze-v3.json \
  --graph-summary reports/release-v2/graph-summary.json \
  --edge-reviews reports/release-v3/completed/A-edges.csv reports/release-v3/completed/B-edges.csv \
  --adjudications reports/release-v3/completed/adjudications.csv \
  --adjudication-ledger reports/release-v3/completed/adjudication-ledger.jsonl \
  --edge-output reports/runs/manual-agent-edge-results.json \
  --topic-output reports/runs/manual-agent-topic-results.json
```

The adjudication arguments apply only when disagreements exist. Read the recorded
completion receipt and actual result package for the selected inputs. Failed
numeric thresholds produce a nonzero exit code while retaining measured JSON
results; they are reported rather than corrected by retuning. Missing inputs or
invalid provenance are refusal errors and must not be treated as quality results.
Do not add `--allow-partial` to a complete audit. For explicit partial review, the
scorer preserves planned denominators and separates unreviewable topic references
from considered empty label sets.

Every result is `evaluation_kind=ai_agent_review`,
`human_validation=not_performed`, `reviewer_independence=not_established`, and
`verified_course_accuracy=not_established`. Wilson intervals exclude evaluator
error and shared source/model bias. See the evaluation limitations beside results.

## Render and package locally

After all report changes and local checkpoint commits, choose a new ignored
output directory:

```bash
uv run --extra report python -m scientific_network.reporting.release_package \
  --report reports/final-report/report.md \
  --output-dir reports/runs/manual-submission-package-v1
```

The command renders A4 HTML/PDF, embeds checked figures/fonts, verifies at least
ten pages, section headings, extracted text and raster figures, and creates a ZIP
and member-hash manifest. It checks report references against permitted tracked
files. Local repository references remain clickable in packaged HTML; the shared
PDF renders them as plain text to avoid recipient-specific filesystem links.
External DOI/GitHub URL presence is checked; external URL availability is not
asserted by this renderer. Inspect representative rendered pages and glyph
coverage separately and record the results.

The ZIP uses permitted tracked working-tree bytes plus the explicit rendered PDF
and HTML. The manifest records the actual source commit and every member hash;
commit the source checkpoint before rendering for an exact source snapshot. Raw
caches, full graph JSON, `.env` credentials, models and database volumes are
excluded; PDFs, ZIPs and run artifacts remain ignored. The package is a local
draft until real team facts and course access/disclosure requirements are supplied.
Push, release tag, Site publication, invitation and submission require separate
explicit authorization and are not performed by these commands.
