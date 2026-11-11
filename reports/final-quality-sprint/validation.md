# Sprint validation — actual checks, 11 November 2026

Root: `/home/san/Code/scientific-network`; run artifacts under
`reports/runs/WORK-2026-11-11-007/` (ignored). Graph/code base `5140ad8`.

| Check / command | Actual outcome |
| --- | --- |
| `uv sync --locked --group dev --extra analysis` | Exit 0. Initial sync removed optional Markdown; later sync also used `--extra report` and restored it. Lock unchanged. |
| Baseline `uv run pytest -q` | 626 passed, 7 skipped; six skips were missing optional rendering dependency. |
| `uv run pytest -q tests/test_sprint_audit.py tests/test_release_acquisition.py` | 49 passed, exit 0. Sampling, unknown handling, strict joins and pre-existing DOI guard covered. |
| Final `uv run pytest -q` with report extra | 635 passed, 1 skipped (empty historical pending-stage parameterization), exit 0. Includes pre-existing unrelated working-tree identity changes; not attributed to this sprint. |
| `uv run python -m scientific_network.quality.sprint_audit --graph data/processed/release-graph-v4/graph.json --works data/interim/release-v1/works.jsonl --output reports/runs/WORK-2026-11-11-007/replay-v1` | Exit 0; all 80 full sampled edge records equal original freeze. Human random/diagnostic IDs unchanged. New preparation includes plain abstracts directly. |
| `uv run research-network validate --input data/processed/release-graph-v4/graph.json --config configs/quality-release-v1.yaml --require-size --output reports/runs/WORK-2026-11-11-007/structural-validation.json` | Exit 0, zero errors, ten nonempty relations, size checks pass. Structural only; no DB write or semantic certification. |
| `uv run python -m scientific_network.quality.sprint_landscape --analysis reports/release-v4/analysis.json --output reports/final-quality-sprint/figures` | Exit 0; coverage 11,575/13,617 reconciles across ten venue-years. CSV and PNG input/output hashes saved. Figure visually inspected. |
| Protected/source verification | 1,040 baseline files unchanged; 341 original OpenAlex object hashes; all 13,608 retained work objects (13,606 accepted matches) reconcile ID/authorship/reference arrays to exact cache locators. Five official-cache and 14 Crossref objects hash-verified for seven DOI cases. |
| Review integrity | Exactly one Luna judgment per frozen edge; all evidence IDs resolve; actual model/run metadata and output hashes preserved. Unknown retained; no pooled accuracy. |
| `npm run build` (frontend cwd) | Exit 0. Existing deferred ECharts chunk remains >500 kB; no heavy dependency added. |
| `npx playwright test --config playwright.contracts.config.ts` | 8 passed, exit 0; distinct raw/labeled/all denominators and nonfinite coverage checked using invented counts. |
| Existing browser suites: `dashboard.spec.ts analytics-layout.spec.ts focus-labels.spec.ts reproducibility.spec.ts` | Final 37 passed, exit 0. Modified local UI with public read-only API. Four widths (1440,1024,768,390), themes, reduced motion, hover-neighborhood/zoom/selection, filters, source actions, saved Graph/Table/Analytics views and restored state. |
| Human sheets and new note | Both forms render 26 cards with zero prechecked answers; desktop/mobile note has no horizontal overflow or page errors. Local browser receipt and screenshots retained. |
| Local PDF/package | Exit 0: 28 A4 pages, ten images, 13 required headings, zero replacement glyphs. Local page 13 visually checked. |

## Failures and environment limits

The first browser run used the normal local API. Its health endpoint reported
Neo4j at `bolt://127.0.0.1:7689` unreachable. Eight tests passed, six graph-dependent
checks failed and one was interrupted; 22 were not run. It was stopped with exit
130 rather than repeatedly testing the absent DB. No service restart/migration
or production data change was attempted.

The first read-only remote-API fallback ran 37 cases: 32 passed, five failed.
Four fixtures still addressed local port 8000; one snapshot lacked the normal
`chromium` project suffix. Correcting the temporary runner's API port to 5174
(the Vite proxy) and project name, without modifying product/test expectations,
produced 37/37. Intermediate failure reports remain in the run directory; the
accidentally generated alternate snapshot was removed from the source tree.

The temporary runner is copied under the work-ID run directory. It runs the
local Vite UI at 5174, proxies `/api` to
`https://scientific-network-api.eastasia.cloudapp.azure.com`, and uses
`PLAYWRIGHT_API_PORT=5174`, Chromium `/usr/bin/google-chrome`, one worker.
This validates local frontend behavior against existing production read responses;
it does not establish local DB integration or deploy new code.

The first report-packaging attempt failed because new linked sprint files were
not yet in the tracked-file index. This is the intended packaging safeguard.
After adding only sprint files to the index, rendering was retried to a new path.
Two early bare-system-Python summary probes failed to import the src-layout
package; rerunning with `uv run python` succeeded. No data changed on failure.

No production graph replacement, new model inference, corpus collection, new
blind test, completed human review, cross-browser/device-hardware check, or
exhaustive live third-party-link crawl was performed. Official/Crossref checks
used cached bytes; graph evidence references and report local links were checked.

## Local rendering

`uv run python -m scientific_network.reporting.release_package --report
reports/final-report/report.md --output-dir
reports/runs/WORK-2026-11-11-007/report-package-v2` passed. PDF and HTML are in that
directory. The existing renderer checked headings, raster figures, local references,
text extraction and portable annotations. The coverage figure and its rendered
page were visually inspected. This intermediate draft archive includes tracked
working-tree bytes, including prior Task2D edits; it is not the final source bundle.
A clean local checkpoint snapshot is used for the isolated final draft package.

## Isolated final draft package

A detached clean checkout of **198e108** was packaged with the same renderer:

```bash
git worktree add --detach /tmp/scientific-network-sprint-198e108 198e108
uv run python -m scientific_network.reporting.release_package \
  --report /tmp/scientific-network-sprint-198e108/reports/final-report/report.md \
  --output-dir reports/runs/WORK-2026-11-11-007/checkpoint-package
```

Exit 0: 28 A4 pages, ten images, 13 headings. The clean snapshot's full Python
suite also passed **635 tests / one skip**, using the existing venv and explicit
snapshot `PYTHONPATH`; this excludes unrelated uncommitted Task2D changes.
[Receipt](package-receipt.json) binds the exact source commit, ZIP/manifest hashes
and local PDF/HTML paths. The 75 MiB local draft ZIP contains only permitted
checkpoint source bytes plus the rendered report; it is not published or submitted.
Personal/course facts still need completion. The temporary checkout was removed
after verification; exact commands are retained here and in the run logs.
