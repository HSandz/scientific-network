# WORK-2026-11-11-008 — Final cleanup and submission readiness

| Field | Value |
| --- | --- |
| Status | completed scoped engineering, validation and local package; human/course details remain pending |
| Recorded | 2026-11-11T23:36:40+07:00 (Asia/Bangkok) |
| Work performed | 11 November 2026 |
| Contributor | Codex, GPT-6.1 Sol |
| Related task | [WORK-2026-11-11-007](2026-11-11-007-final-quality-sprint.md) |
| Git state | scoped implementation checkpoint `f3b00d412769c2a9eff9063b7702412cffe1e700`; final receipt/report records are being committed separately; four unrelated Task2D identity source files and WORK-006 remain excluded |

## Objective

Complete the requested final stabilization: clarify the human-review rubric, add
all issue-ledger cases to supplemental human diagnostics without changing frozen
probability samples, verify report and Explorer state, and build a clean local
submission package. Do not change the graph, deploy, push or submit externally.

## Changes and findings

- Initial inspection confirms prior packets contain 20 random plus six risk cases;
  four `issues.json` edge IDs are not explicitly guaranteed in those selections.
- The global review-sheet vocabulary has one `correct_when` field. It can express
  source-consistent support and identity limitations without changing CSV fields.
- Implemented the distinction across AUTHORED, AFFILIATED_WITH, and all four
  identity-dependent derived relations. The form retains its existing answers and
  fields; it states that `correct` is not separately coded as independent verification.
- Added all four `issues.json` IDs as a tagged diagnostic subset for both reviewers.
  The 80-edge sample and 20 random IDs are unchanged; three flagged IDs retain the
  random tag. Six existing risk diagnostics remain; each packet has 27 unique cases.
  Luna's concerns and locators are in separate post-blind pages. Both answer exports
  are blank and the diagnostic-only cases are outside probability calculations.
- Checked the report's version-separated v3/v4 audit results and AI-only accuracy
  wording; added a real team/course submission checklist without filling unknowns.
- A read-only live Pages browser check loaded the Analytics chunk and confirmed the
  topic denominator tooltip text and identity-sensitivity note. The served source
  commit is not exposed; no deployment occurred.
- Existing uncommitted Task2D identity work is preserved and excluded.
- Final package artifacts are in the ignored unique run directory. The ZIP contains
  the permitted tracked source snapshot plus rendered PDF; HTML and PDF are also
  available separately. No historical receipt or package was overwritten.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| Initial repository state | inspected; `main` at `8219e5f`; four Task2D identity source files plus WORK-006 were dirty/untracked | Git output in this session |
| `uv run pytest -q tests/test_sprint_audit.py tests/test_edge_audit_split.py` | 47 passed, exit 0 | Focused rubric, selection, compatibility, and sampling regressions |
| Human packet assertions | passed | Every issue ID present; both reviewers have same 27 unique IDs; original random draw/probability retained; diagnostics excluded; both CSVs blank |
| Frozen edge sample hash | passed; `2e5cb63ffe6c6f93c349bd730953c4c06f5cb782e020f9611b7a6446a10ea00d` | `reports/final-quality-sprint/edge-sample.json` |
| `uv run research-network validate --input data/processed/release-graph-v4/graph.json --config configs/quality-release-v1.yaml --require-size --output reports/runs/WORK-2026-11-11-008/structural-validation.json` | passed, exit 0; zero errors, 10/10 relations, structural only | Graph `release-d3c788c3114a`; semantic accuracy not measured |
| Read-only public Explorer check | passed for visible functionality; deployment source commit unknown | Public Analytics chunk includes assigned-topic count, labeled denominator, all-paper denominator, coverage, and identity-sensitivity wording |
| `git diff --check` | passed, exit 0 | Current final-cleanup diff |
| Clean checkpoint full suite | 644 passed, 1 existing skip, exit 0 | Detached clean checkout of `f3b00d4`; skipped empty historical CLI-stage parameterization |
| Frontend `npm run build` | passed, exit 0 | Existing ECharts chunk-size warning (>500 kB) remains |
| `npx playwright test --config playwright.contracts.config.ts` | 8 passed, exit 0 | Contract, denominators, analytics and graph transforms |
| Selected Playwright browser suites | 37 passed, exit 0 | Dashboard, analytics layout, focus labels and reproducibility; local Vite frontend with read-only production API, four viewport widths and light/dark checks |
| Human packet browser artifacts | passed; 27 unique cards, zero answers | Desktop/mobile and light/dark captures under `reports/runs/WORK-2026-11-11-008/`; no overflow/page errors |
| Frozen input hash checks | passed | Graph `6f665a94…a59c90`, works `2b7f3bc1…55047`, 80-edge sample `2e5cb63f…ea00d`, issue ledger `1790008f…7e66`, sampling manifest `3c368bc5…59fe90`; full values in receipt |
| Report rendering | passed | 52 local report links, ten figures, 13 headings, 28 A4 pages, zero replacement glyphs, PDF local-file annotation check passed; nine external URLs were not crawled |
| Final package ZIP integrity/scope | passed | 1,754 members; all source manifest hashes match; CRC passes; no raw/intermediate/processed data, credentials, temporary runs or Task2D files |
| PDF visual check | passed | Final checklist page inspected; remaining team/course fields are explicit blanks |
| Final handoff report and package receipt | added | [`reports/final-quality-sprint/final-cleanup-report.md`](../../reports/final-quality-sprint/final-cleanup-report.md), [`final-cleanup-package-receipt.json`](../../reports/final-quality-sprint/final-cleanup-package-receipt.json) |

## Decisions

[D041](../decisions.md#d041--human-review-evidence-distinction-and-flagged-diagnostic-supplement-2026-11-11)
records the rubric distinction, additive issue-ledger subset and compatibility limits.

## Open issues and limitations

Human review has not been performed. The team names, student IDs, actual
contributions, course identifier/advisor requirements, access rules, and
submission destination are not available from repository records. Nine report
external URLs were not availability-tested. The Pages source commit is not exposed;
the live bundle does contain the changes checked here. No push, deployment or
external submission was performed.

## Next step

The two team members should supply the real submission details listed in the
final-cleanup report and optionally return human review exports. Render a new
version only if those facts must be added. External submission or future
publication remains a separately authorized action.

## Corrections

None.
