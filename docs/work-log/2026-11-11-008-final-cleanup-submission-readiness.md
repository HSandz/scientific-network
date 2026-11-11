# WORK-2026-11-11-008 — Final cleanup and submission readiness

| Field | Value |
| --- | --- |
| Status | in_progress |
| Recorded | 2026-11-11T23:24:41+07:00 (Asia/Bangkok) |
| Work performed | 11 November 2026 |
| Contributor | Codex, GPT-6.1 Sol |
| Related task | [WORK-2026-11-11-007](2026-11-11-007-final-quality-sprint.md) |
| Git state | `main` at `8219e5fbf194df3bdc67ba85d77cb86fca37b32e`; final-cleanup changes staged separately; four unrelated Task2D identity source files and WORK-006 remain excluded |

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
| Full suite, clean checkpoint, frontend build/browser regressions, final report rendering/package | pending | Run only after scoped checkpoint commit |

## Decisions

[D041](../decisions.md#d041--human-review-evidence-distinction-and-flagged-diagnostic-supplement-2026-11-11)
records the rubric distinction, additive issue-ledger subset and compatibility limits.

## Open issues and limitations

Clean-checkpoint full-suite/build/browser validation and the final package/receipt
remain in progress. Human review has not been performed. The team names, student
IDs, actual contributions, course identifier/advisor requirements, access rules,
and submission destination are not available from repository records. No push,
deployment or external submission is authorized or performed.

## Next step

Commit only the final-cleanup files, excluding Task2D; then run the clean-checkout
suite, frontend checks, report renderer and package builder, and record measured
artifact hashes in a new receipt without overwriting historical receipts.

## Corrections

None.
