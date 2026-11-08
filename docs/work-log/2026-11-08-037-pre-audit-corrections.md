# WORK-2026-11-08-037 — Pre-audit technical corrections

| Field | Value |
| --- | --- |
| Status | completed — technical handoff; independent reviews remain pending |
| Recorded | 2026-11-08 23:57 +07:00 (Asia/Bangkok) |
| Completed | 2026-11-09 00:32 +07:00 |
| Work performed | 2026-11-08 to 2026-11-09, UTC+07:00 |
| Contributor | Codex, at the user's request |
| Related task | [WORK-036](2026-11-08-036-progress-review.md) |
| Git state | Clean main at 1a27dc0 initially; tooling checkpoint 5d92285; final package in the commit containing this entry; no push |

## Objective

Resolve technical issues before independent human audit, preserve frozen facts and
predictions, prepare consistent replacement packets, and stop before annotation,
publication or submission. D040 controls; no historical source-closure work resumed.

## Changes and findings

- Corrected the normal embedding builder and added `correct-release-taxonomy`:
  synchronize all Topic properties, hierarchy, source hashes/locators and provenance
  from the unchanged frozen classifier taxonomy. The deterministic correction uses
  existing predictions with no inference. Direct graph/config equality is checked.
- New graph: `release-9d4a6fb20f63`, SHA-256
  `c23ef82c97fcb539b4b1c279e8ff42378bdb102e80fe851acf1a42e816a727b8`,
  at `data/processed/release-graph-v3/graph.json`. The
  [summary](../../reports/release-v2/graph-summary.json) binds the old graph,
  summary/freeze and unchanged config inputs. Canonical hashes prove identical
  entity/semantic-edge identities, every non-taxonomy node/edge/evidence record,
  affiliation observation, prediction, excerpt, score, support set/count and weight.
  Every edge has the new graph version. Old graph/freeze/config/packets remain intact.
- Implemented the optional single-reviewer design and explicit partial scoring;
  complete assignment validation stays default. Separate CSV exports are parsed
  independently; malformed/blank/duplicate/foreign/mismatched rows remain fatal.
  Partial results report actual/planned n, missing assignments, overlap/relation
  coverage and nonresponse bias. Returned conflicts require adjudication; agreement
  uses actual pairs. Supplements remain separate and unverifiable remains incorrect.
- Added dedicated A/B edge packets, a blank-conflict adjudication helper, complete
  expandable evidence context and source links. Restored previously clipped text.
  A finite 64 MiB CSV-field limit supports full ledgers without truncation. New
  CSVs preserve exact bytes in Git, including source whitespace and quoted CRLFs.
- Fresh analysis exposed unordered floating accumulation. Exact rational sums
  (`d040-release-metrics-v2`) stabilize rounded fractional totals and tied topic
  rankings. The [comparison](../../reports/release-v2/analysis-comparison.json)
  records all 40 leaf differences from the historical analysis. Recomputing the
  old graph with the fixed method exactly reproduces the corrected graph metrics;
  projections, strict projections, robustness, business summaries and counts match.
  Final community plots mask unstored top-five topic cells rather than implying zero.
- Active receipt: [freeze-v3.json](../../reports/release-v2/freeze-v3.json).
  It preserves/supersedes the original freeze and earlier corrective receipts
  (first figure package, then method-binding normalization). Final figures are in
  `reports/final-report/figures-v3/`; graph/analysis/sample/packet bytes did not change
  between corrective receipt revisions. Topic master/allocation/A/B sheets are
  reused by exact-byte reference; the test, allocation, model and thresholds did not change.
- Updated README, report, evaluation instructions, roadmap and
  [reviewer handoff](../reviewer-handoff.md). Recounted author positions: 65,469
  on matched works, 65,507 over scope, including 38 on unmatched works. Remote main
  is 951b9c5 with no tags; the previous “never pushed” claim was stale.

## Verification

Commands ran from `/home/san/Code/scientific-network`. Raw logs/helpers are ignored
under `reports/runs/WORK-2026-11-08-037/`; the concise
[technical verification](../../reports/release-v2/technical-verification.json)
records observed outcomes and hashes without depending on those local logs.

| Command/check | Outcome and exit code |
| --- | --- |
| `git status --short --branch` | initial clean main at 1a27dc0, ahead 1, exit 0 |
| `uv sync --locked --group dev --extra analysis` | passed, exit 0 |
| Initial `uv run pytest` | 363 passed, one existing empty-parameterization skip, 15.45 s, exit 0 |
| `uv run research-network correct-release-taxonomy --input data/processed/release-graph-v2/graph.json --taxonomy configs/topics-release-v1.yaml --quality configs/quality-release-v1.yaml --source-summary reports/release-v1/graph-v2-summary.json --source-freeze reports/release-v1/freeze.json --output-dir data/processed/release-graph-v3 --summary reports/release-v2/graph-summary.json` | passed, exit 0, 48.18 s; max RSS 2,933,044 KiB; no swaps |
| `uv run research-network validate --input data/processed/release-graph-v3/graph.json --config configs/quality-release-v1.yaml --require-size --output reports/release-v2/validation.json` | passed, exit 0; 52,415 nodes, 275,438 edges, 36,680 resolved researchers, 124,619 factual edges, ten predicates |
| `uv run python reports/runs/WORK-2026-11-08-037/reset-release-db.py` | passed, exit 0; verified healthy neo4j-five-year/7689 mapping and old inventory, cleared only that endpoint; old disk graph preserved |
| `NEO4J_URI=bolt://localhost:7689 uv run research-network build --input data/processed/release-graph-v3/graph.json --config configs/quality-release-v1.yaml --output reports/release-v2/neo4j-load.json` | passed, exit 0; 74 transactions |
| Same `build` command with `--output reports/release-v2/neo4j-replay.json` | passed, exit 0; 74 transactions, same inventory, nodes_before equals nodes_after |
| `uv run python reports/runs/WORK-2026-11-08-037/check-neo4j.py` | passed, exit 0; all three inventory queries reconcile, all six integrity queries return zero rows, only new graph version, all 20 taxonomy definitions match config |
| `uv run research-network analyze --input data/processed/release-graph-v3/graph.json --config configs/analysis-release-v1.yaml --quality-config configs/quality-release-v1.yaml --output reports/release-v2/analysis.json` | final corrected-method run passed, exit 0, 2m31.93s; first diagnostic run preserved in run directory |
| `uv run python reports/runs/WORK-2026-11-08-037/compare-metrics.py` | passed after investigation, exit 0; exact old/new graph metric equality under fixed method |
| `uv run python -m scientific_network.analysis.figures --analysis reports/release-v2/analysis.json --output-dir reports/final-report/figures-v3` | passed, exit 0; six PNG/CSV pairs plus captions; final renderer reproduced all 13 bytes exactly in scratch |
| `uv run research-network freeze-audit-sample --input data/processed/release-graph-v3/graph.json --config configs/quality-release-v1.yaml --output reports/release-v2/audit/edge-review-sheet-v2.csv` | passed, exit 0; fresh frame/audit hashes, all decisions blank, dedicated packets generated |
| Same sampling command with `--config configs/quality-single-reviewer-release-v1.yaml --output reports/release-v2/audit-single-reviewer/edge-review-sheet-v2.csv` | passed, exit 0; optional design only, no overlap or second reviewer |
| Local Chromium via `uv run --no-project --with playwright python reports/runs/WORK-2026-11-08-037/browser-check.py` and `real-packet-browser-check.py` | passed, exit 0; synthetic single/A/B actual downloads score correctly, quoting/Unicode/multiline content survives; real packets blank, correct assigned content/links, topic blank export blocked; zero page errors |
| `uv run python reports/runs/WORK-2026-11-08-037/check-blank-packets.py`; explicit final `score-topic-review --freeze reports/release-v2/freeze-v3.json` with all other paths from handoff and blank A/B sheets | five expected exit-1 refusals; final freeze also refuses unreviewed topic row; no evaluation outputs |
| Final `uv run pytest` | **384 passed, 1 skipped**, exit 0, 14.72 s; no warnings; post-attribute CSV Git-byte regression also passes |
| `uv run python reports/runs/WORK-2026-11-08-037/check-package.py` | passed, exit 0; all active freeze references match actual/staged bytes; historical preservation and current documentation links checked |
| `git diff --cached --check`; `git ls-remote origin refs/heads/main 'refs/tags/*'` | passed; remote main 951b9c5, no tags |

Failures/partial attempts: the first new regression exposed datetime serialization
in the comparison helper (fixed with JSON-mode dumps). The first analysis-diff
helper omitted some exact-arithmetic fields from its classification; all differences
were inspected before accepting them. An initial freeze helper ran before that
comparison existed; its newly written optional receipt was preserved and superseded.
Full context exposed the CSV 128 KiB parser failure, fixed and regression-tested.
The browser MCP transport closed; local Chromium completed actual export validation.
A plotting deprecation was removed without changing figure bytes. Six historical,
unbound figure CSVs already have CRLF working-tree versus LF baseline Git bytes;
both representations remain unchanged and are recorded separately. Git's whitespace
styling is disabled for literal CSV content; no frozen source strings were cleaned.

## Decisions

[D040 amendments](../decisions.md#d040-amendments) record the correction, fallback
contracts, exact arithmetic, figure scope and final receipt choices. No corpus,
classifier, held-out membership, graph semantics or quality threshold changed.

## Open issues and limitations

No technical blocker remains. Independent edge precision and topic quality remain
unmeasured; tests, inventory and structural checks cannot establish them. The user
must map actual people to A/B, return real reviews/adjudications, and provide real
team details/contributions/disclosure. Final report scoring, PDF, lecturer access,
Site publication, push/tag and submission remain outside this completed task.
No corpus acquisition, historical audit, real model inference/retuning or human
annotation was performed. No synthetic judgments were put in real packets.

## Next step

Distribute the dedicated packets in [reviewer-handoff.md](../reviewer-handoff.md),
preserve originals, and return completed exports under the separate documented
paths. Then prepare/adjudicate conflicts and use the explicit scoring commands;
choose a fallback only deliberately. Do not proceed to publication/submission.

## Corrections

None.
