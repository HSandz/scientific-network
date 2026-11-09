# WORK-2026-11-09-007 — Review agent evaluation and local release

| Field | Value |
| --- | --- |
| Status | completed (review; findings remain open) |
| Recorded | 2026-11-09 13:25 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-09 13:25–13:31 +07:00 (Asia/Bangkok) |
| Contributor | Codex, at the user's request |
| Related task | WORK-2026-11-09-003 through WORK-006 |
| Git state | Clean main at `c80e1ee`, ahead of origin/main by five commits |

## Objective

Review the implemented agent evaluation, source/provenance records, measured
results, report and local submission package against the user-amended D040 plan.
Review only; preserve frozen/completed artifacts and implementation.

## Changes and findings

- Reviewed changes since `2305632`, the scorer/renderer and tests, frozen evaluator
  protocol/receipts, ledgers, measured report and actual local package at `c80e1ee`.
- **P1, confirmed known graph defect:** `resolve/release.py:175–184` collects only
  singular `author.orcid`, ignoring `observed_orcids`. Independently resolved all
  27 raw-source locators/hashes across the 25-row conflict inventory: the reported
  arrays and author IDs match. This violates the D040 withholding rule and affects
  accepted endpoints/derived support. See [post-audit findings](../post-audit-findings.md).
  Preserve this failed frozen graph; any correction requires a separate version
  and new audit, without reusing exposed test errors as independent evidence.
- **P2, new scorer validation gap:** `evaluation/agent_review.py:188–192` checks
  topic CSV labels only when a ledger `labels` key exists, although the frozen
  rubric requires that key. A synthetic full-wrapper reproduction first refuses a
  contradictory label, then scores successfully after removing that one ledger
  key (exit 0). Require a labels list for every topic record, including explicit
  empty/unreviewable rows, and add a missing-field regression. All current real
  topic records contain matching lists; this finding does not invalidate their scores.
- Independent rescore exactly matches both committed JSON objects. The 88% edge
  precision and failed numeric gates are correctly disclosed; embedding topic F1
  remains .4667. Human validation and evaluator independence remain unestablished.
- Actual ZIP CRC/member hashes and packaged HTML links pass; report source matches
  the package. PDF is 19 A4 pages with embedded fonts; inspected quality-table
  pages 15–16 show readable tables/disclosures without clipping or overlap.
- Only this review entry, its index and current status changed. Implementation,
  graph, judgments, configs, frozen records and package were preserved.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| Initial Git state/path checks | passed, exit 0; clean at `c80e1ee` | no unrelated edits |
| `uv sync --locked --group dev --extra analysis --extra report` | passed, exit 0 | locked local environment |
| `uv run pytest` | passed, exit 0; 419 passed, 1 existing empty-stage skip, 22.41 s | `reports/runs/WORK-2026-11-09-007/pytest.log` |
| `uv run research-network schema` | passed, exit 0 | run directory `schema.json` |
| Documented `score-agent-review`, outputs redirected to this work's run directory | exit 1 expected: numeric gates fail; both result JSONs exactly equal committed objects | `rescore.log`, `rescore-comparison.json` |
| Python hash/locator/ZIP checks | passed, exit 0: 55 unique evaluation/completion bindings match; 27 ORCID source claims verified; all 1,320 ZIP entries/CRC and five artifact hashes match | `artifact-verification.json` |
| `git diff 2305632 c80e1ee --` selected frozen configs/packets/analysis/figures | empty, exit 0; selected historical bytes preserved | inspected alongside hash bindings |
| Synthetic missing-topic-label reproduction using `test_agent_review.py` fixture and full wrapper | defect reproduced, harness exit 0; explicit mismatch refused, omitted key accepted | `topic-label-binding-reproduction.json`; no real labels changed |
| Packaged HTML resolution; `pdfinfo`, `pdffonts`, `pdftotext -layout`; `pdftoppm` pages 15–16 | passed, exit 0: 18 local links resolve; 19 A4 pages, embedded fonts, no replacement glyphs; tables visually checked | `report-verification.json`, `report-page-15.png`, `report-page-16.png` |
| `git diff --check` | passed, exit 0 | review documentation |

Run artifacts above are ignored under `reports/runs/WORK-2026-11-09-007/`.
The first exploratory hash script incorrectly compared the manifest's 1,319
payload count with all 1,320 ZIP entries; it stopped with an assertion before
writing its receipt. The corrected check includes the manifest itself and passes.
An initial two-page `pdftoppm -singlefile` call warned that only page 15 was written;
page 16 was then rendered separately and inspected.

## Decisions

None; review only.

## Open issues and limitations

The P2 missing-field guard remains unfixed in this review. Known graph quality
failures remain; software/package checks do not certify the course accuracy target.
No complete independent relabeling of all sampled claims was performed. Context
isolation/chronology are recorded declarations and hash-bound receipts, not proof
of evaluator independence. Raw-source conflict checks confirm specific evidence,
not graph-wide error prevalence. Fresh database integration, graph validation,
analysis/figure reproduction, external access and secret-value scans were not
rerun; WORK-004/006 results remain historical. Missing team/course facts and
authorized external delivery remain as documented in the checklist.

## Next step

Fix the P2 topic-ledger required-field guard in a focused code change with a
synthetic regression and unchanged real-result rescore. Treat graph correction
as a separately approved version/audit task under the frozen protocol; retain
all failed results. Supply real team/course facts before a new submission render.

## Corrections

None.
