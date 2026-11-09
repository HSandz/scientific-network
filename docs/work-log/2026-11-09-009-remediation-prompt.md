# WORK-2026-11-09-009 — Fresh-session remediation prompt

| Field | Value |
| --- | --- |
| Status | completed (handoff only) |
| Recorded | 2026-11-09 15:02 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-09 15:01–15:04 +07:00 (Asia/Bangkok) |
| Contributor | Codex, at the user's request |
| Related task | WORK-2026-11-09-007 and WORK-008 |
| Git state | Clean main at `934759b`; no unrelated edits |

## Objective

Create a paste-ready fresh-session prompt to execute the remediation plan,
including the separate graph correction and prospective agent audit.

## Changes and findings

- Added [the fresh-session prompt](../prompts/implement-remediation-plan.md) for
  all five plan steps, with code/artifact anchors and concrete acceptance checks.
- Pasting it adopts the separate correction track and directs the execution agent
  to record a dated amendment without rewriting hash-bound historical files.
  Routine authorized work needs no repeated approval. External delivery stays out
  of scope; human annotation is optional and private facts remain clearly pending.
- Requires original-score preservation for the scorer fix, full-source conflict
  handling, prediction-preserving correction, new derivations/database/analysis,
  one prospectively frozen source-backed agent audit and a new checked package.
- Explicit edge-only provenance avoids attributing historical topic references to
  new reviewers. New seed/sample exposure and audit-motivated correction remain
  disclosed; no classifier tuning or repeated samples to obtain a passing score.
- Linked the prompt from plan/status and updated the work-log index. No code,
  config, graph, judgment, frozen receipt or external state changed.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| Initial Git, new-path and symlink checks | passed, exit 0 | clean base; new paths unused |
| Locked environment sync | passed, exit 0 | analysis/report extras installed |
| `uv run pytest` | passed, exit 0; 419 passed, 1 existing empty-stage skip, 21.91 s | `reports/runs/WORK-2026-11-09-009/pytest.log` |
| Prompt versus plan and current review | inspected; all five steps, amendment and preservation requirements covered | no execution claimed |
| Local documentation links, status length and `git diff --check` | passed, exit 0 | referenced local files exist; status under 60 lines |

## Decisions

None enacted. Pasting the execution prompt adopts its stated correction scope;
the execution agent records that dated amendment before changing the graph.

## Open issues and limitations

Implementation and measured results unchanged. Code/data CLI, database, audit
and package checks were not rerun for this documentation-only handoff. The next
session must verify current state and measure its own outcomes.

## Next step

Paste the new prompt into a fresh agent session and execute the plan, starting
with the scorer guard and exact original-result rescore before graph correction.

## Corrections

None.
