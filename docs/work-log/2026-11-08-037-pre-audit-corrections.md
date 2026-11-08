# WORK-2026-11-08-037 — Pre-audit technical corrections

| Field | Value |
| --- | --- |
| Status | in_progress |
| Recorded | 2026-11-08T23:57+07:00 (Asia/Bangkok) |
| Work performed | Starting 2026-11-08 +07:00 |
| Contributor | Codex, at the user's request |
| Related task | [WORK-036](2026-11-08-036-progress-review.md) |
| Git state | Clean main at 1a27dc0, one commit ahead of origin/main |

## Objective

Correct taxonomy/provenance deterministically without inference or prediction changes;
implement D040 single-reviewer and explicit incomplete-audit fallbacks; verify and
freeze replacement artifacts and prepare a concrete independent-review handoff.
No human annotation, publication, push, tag or submission.

## Changes and findings

Confirmed stale taxonomy copy in embedding builder and strict two-reviewer-only scorer.
Old graph/freeze/packet/config bytes recorded before work in the ignored run directory.
Implemented deterministic correction and normal-builder taxonomy synchronization;
single-reviewer and opt-in partial scoring, separate-CSV input parsing, full
supporting review context, explicit topic freeze bindings and CSV byte protection.
Correction finished in 48.18 s, exit 0, max RSS 2,933,044 KiB, no swaps:
`release-9d4a6fb20f63`, graph SHA-256
`c23ef82c97fcb539b4b1c279e8ff42378bdb102e80fe851acf1a42e816a727b8`.
Canonical invariants preserve all non-taxonomy facts/predictions/evidence/support.
Focused first run: 1 failure (datetime serialization in the new comparison helper),
34 passes; fixed with JSON-mode model dumps; second run 35 passes. Checkpoint
full suite: 377 passed, one existing skip, 15.80 s, exit 0. Validation CLI passed.
Current analysis recomputation running; outputs under reports/release-v2.
Live remote main is 951b9c5; no tags; isolated Neo4j service is healthy.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `git status --short --branch` | clean main, ahead 1, exit 0 | base 1a27dc0 |
| `uv sync --locked --group dev --extra analysis` | passed, exit 0 | run uv-sync.log |
| `uv run pytest` | 363 passed, 1 existing empty-parameterization skip, exit 0, 15.45 s | run pytest-before.log |

## Decisions

D040 controls; implementation choices to be recorded in existing decision register.

## Open issues and limitations

Work in progress; independent semantic accuracy and topic quality remain unmeasured.

## Next step

Implement corrections, validate preserved facts, load only port 7689, and freeze new packets.

## Corrections

None.
