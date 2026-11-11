# WORK-2026-11-11-007 — Deadline quality and presentation sprint

| Field | Value |
| --- | --- |
| Status | completed feasible scoped work; independent quality/submission facts remain pending |
| Recorded | 2026-11-11T22:16:27+07:00 (Asia/Bangkok) |
| Work performed | 11 November 2026 |
| Contributor | Codex coordinator; three fresh gpt-6-luna / high AI-review contexts |
| Git state | main at base 5140ad8; prior Task2D identity files and WORK-006 untouched and excluded |

## Objective

Implement a bounded ten-relation evidence audit, topic/metadata diagnostics,
scientifically qualified Explorer/report interpretation and local regression checks.
User sprint amendment permits proceeding without Task2C human exports.

## Changes and findings

- Frozen 80 accepted v4 edges, eight/relation with populations and probabilities;
  actual Luna outputs, protocol/run metadata, complete-review joins, per-relation
  Wilson intervals and issue ledger under `reports/final-quality-sprint/`.
- Luna challenges two researcher-topic and one organization-topic aggregates; one
  authorship unknown. Coordinator checked all four full witness sets. No aggregate
  or identity repair is justified from these AI judgments alone. No pooled accuracy.
- Eight topic diagnostic cases; label omissions/overlap and reviewer disagreement
  retained. Seven DOI cases remain ambiguous. Existing exact-DOI fix already present;
  no duplicate fix, relabeling, retraining, source recollection or graph rebuild.
- Two existing-format 26-case human packets: 20 random plus six risk diagnostics.
  No human judgments fabricated; forms render with zero completed answers.
- Topic tooltips separate raw support, labeled denominator and all-paper coverage;
  compact Task2C bridge identity-sensitivity caveat. Layout and interactions retained.
- Existing research report updated in place; coverage figure/CSV reuse frozen
  venue-year analysis, with qualified landscape and collaboration interpretation.

## Verification

| Command/check | Actual outcome |
| --- | --- |
| `uv sync --locked --group dev --extra analysis --extra report` | Exit 0, lock unchanged |
| Baseline `uv run pytest -q` | 626 passed / 7 skipped (report extra initially absent) |
| Focused sampling/acquisition tests | 49 passed, exit 0 |
| Final `uv run pytest -q` | 635 passed / 1 skipped, exit 0; includes prior unrelated working-tree edits |
| Offline sprint-audit replay | Exit 0; all 80 edge records and human selections retained |
| `research-network validate` v4 with size checks | Exit 0, zero errors, ten nonempty relations; structural only |
| Protected/source checks | 1,040 files unchanged; 341 OA hashes; 13,608 retained records including 13,606 accepted matches reconciled; 14 Crossref and five official-cache files verified |
| Frontend build / contracts | Exit 0; eight contracts pass; existing ECharts chunk warning |
| Final selected browser suites | 37 passed using local UI/public read-only API; widths, themes, hover/zoom, filters, evidence, saved workspaces |
| Blank human forms / new note | Two × 26 cards, zero prechecked, no page errors/overflow at 1440 and 390px |
| Existing report renderer/package | Exit 0; 28 A4 pages, ten images, 13 headings; coverage figure/PDF page visually checked |

Exact commands, failure counts and artifacts: `reports/final-quality-sprint/validation.md`.
Raw console/browser/render artifacts stay ignored in `reports/runs/WORK-2026-11-11-007/`.
Initial browser run hit unreachable local Neo4j (six failures, then interrupted).
First remote fallback had five runner-configuration failures; corrected API port and
normal Chromium project yielded 37/37 with no product/expectation changes.
Initial packaging rejected unindexed links, then passed after selective staging.
Two bare-system-Python probes failed imports; uv environment succeeded.
Initial packet abstract omission was repaired via pre-completion hash-bound source
supplement; replay code includes plain abstracts directly. Original sample unchanged.

## Decisions

D040 deadline-sprint amendment in `docs/decisions.md`: supplemental AI assessment,
optional human packet and local presentation/report changes; no production promotion.

## Open issues and limitations

Human validation/evaluator independence/course accuracy remain unestablished.
Only bounded semantic witnesses were read; structural validation is separate.
No production write, deployment, push, DB restart or exhaustive live URL crawl.
Local DB integration unavailable. Prior Task2D edits remain unfinished and outside
this checkpoint; an intermediate working-tree ZIP is not for final submission.
Team/course facts pending. Full identity review and affiliation rebuilding out of scope.

## Next step

Prepare the isolated checkpoint-based local draft bundle, then supply real team/course
facts and optionally independently review the small human packet. Frontend publication
requires explicit authorization. No graph/API deployment is required for these changes.

## Corrections

None.
