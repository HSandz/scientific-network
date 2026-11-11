# WORK-2026-11-12-001 — Final repository stabilization

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-12T01:54:51+07:00 (Asia/Bangkok) |
| Work performed | 12 November 2026 |
| Contributor | Codex, GPT-6.1 Sol |
| Related task | [WORK-2026-11-11-009](2026-11-11-009-latex-research-report.md) |
| Git state | Started on `main` at `c4daf1d`, equal to `origin/main`; stabilization committed locally; unrelated Task2D work remains uncommitted |

## Objective

Find confirmed high-impact, low-risk issues after the report checkpoint; preserve
frozen scientific artifacts and unrelated work; verify the final local state. The
LaTeX report, figures and compiled PDF were out of scope.

## Changes and findings

- Added two DOI acquisition regressions for singleton retry after a mismatched
  batch result and official-page disambiguation of a duplicate with a wrong DOI.
  The current exact-DOI/title/author-count guards already handle both paths. Seven
  historical DOI disagreements remain ambiguous; no graph data was rewritten.
- Fixed the Explorer's incompatible filter/preset interaction in local frontend
  code: venue or narrowed-year filters now select the supported paper-topic slice;
  switching away resets those scope filters. Added a focused Playwright regression.
  The live filter request was observed stuck in loading; a separate direct request
  returned the API's documented HTTP 422. No deployment was authorized or made.
- Verified four AI-flagged edge IDs across the issue ledger, reviewer packets and
  post-blind pages. Some issue/packet evidence IDs and locator fragments do not
  fully reconcile; frozen packets were preserved. No AI judgment changed a graph
  edge. The bounded `gpt-6-luna` high-effort review remains AI-assessed, not human
  ground truth.
- The 80-edge sample hash and packet conditions remain intact: 20 random IDs, six
  diagnostic IDs, four flagged IDs, 27 unique cases per reviewer, blank answers,
  concerns post-blind only and unchanged CSV schema.
- The local submission ZIP passed its recorded hash and CRC checks but is bound to
  historical source commit `f3b00d4`; no new package or PDF was generated.
- The repository is private and anonymous GitHub access returns 404. Lecturer
  source access, team/course facts and external delivery remain unresolved.
- Pre-existing Task2D changes in `identity_evaluation.py`, `identity_review.py`,
  `identity_validation.py`, `identity_integrity.py` and WORK-006 were not staged or
  changed by this task.

See the [technical stabilization report](../final-stabilization-2026-11-12.md).

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `uv sync --locked --group dev --extra analysis --extra report` | Passed, exit 0 | Locked environment audited |
| `uv run pytest -q` | 650 passed, 1 skipped, exit 0 | Existing empty CLI-stage parameter set accounts for skip |
| `research-network validate --require-size` on release v4 | Passed, zero structural errors; ten relations present | `reports/runs/WORK-2026-11-12-001/v4-structural-validation.json`; semantic accuracy not measured |
| V3/v4 graph, works, config and sample hashes | Passed against recorded freezes | V4 `6f665a94…ea59c90`; v3 `c23ef82c…16a727b8`; works `2b7f3bc1…05f55047`; sample `2e5cb63f…a10ea00d` |
| Human packet sample/schema checks | Passed | 20 random, 6 diagnostics, 4 flagged; 27 unique per member; blank decisions; initial/post-blind separation |
| `npm run build` | Passed, exit 0; ECharts chunk-size advisory | `apps/research-explorer/frontend` |
| Focused Playwright filter regression | 1 passed, exit 0 | `tests/explorer.spec.ts` |
| Playwright contract suite | 8 passed, exit 0 | `npx playwright test --config=playwright.contracts.config.ts` |
| `git diff --check` | Passed, exit 0 | Whitespace/conflict-marker check |
| Live Explorer read-only smoke | Summary/analytics/search/node/evidence requests returned 200; no console errors. Venue filter did not settle; direct API request returned 422. | Public Pages site and Azure API; local UI fix not deployed |
| Historical ZIP hash/CRC/member count | Passed, 1754 members | `reports/runs/WORK-2026-11-11-008/package-v1/`; historical source checkpoint |

No Neo4j integration validation or write was run. No 80-edge audit or 511-case
identity review was rerun. The local package is not a package of the stabilized
checkout. Repository reproduction requires restoring the ignored frozen graph,
works and original caches; reacquisition is not byte-identical restoration.

## Decisions

No new graph or release decision. D040 remains in force; the filter change is a UI
compatibility fix for the existing API contract. Frozen v3/v4, candidate graphs,
source caches and evidence packets remain preserved.

## Open issues and limitations

The seven historical DOI disagreements, flagged graph relationships, incomplete
issue-to-packet evidence reconciliation, identity/affiliation/topic uncertainty,
and private-repository lecturer-access blocker remain open. The existing package
predates this stabilization. Task2D remains unfinished and separate. Human
validation and verified course accuracy are not established.

## Next step

Resolve official lecturer/repository access requirements and actual team/course
facts. Then review the local checkpoint and authorize only the chosen external
delivery. Do not promote identity candidates or alter the frozen graph on the
basis of these AI-assessed flags.

## Corrections

None.
