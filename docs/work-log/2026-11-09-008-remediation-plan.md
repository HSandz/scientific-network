# WORK-2026-11-09-008 — Plan review remediation

| Field | Value |
| --- | --- |
| Status | completed (planning only) |
| Recorded | 2026-11-09 14:24 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-09 14:23–14:26 +07:00 (Asia/Bangkok) |
| Contributor | Codex, at the user's request |
| Related task | WORK-2026-11-09-007 |
| Git state | Clean main at `3db6943`; no unrelated edits |

## Objective

Create a concrete agent-executable plan for the review findings and release
preparation. Planning only; preserve implementation, graph, audit and package.

## Changes and findings

- Added [the remediation plan](../remediation-plan.md): immediate scorer guard,
  proposed versioned identity correction, affected database/analysis, prospective
  source-backed agent audit and replacement local package, with acceptance checks.
- The correction applies the existing conflict rule across full matched sources;
  it preserves frozen topic predictions and requires recomputing derived support.
  The existing embedding builder performs inference, so it must not be rerun just
  to retain unchanged predictions in a corrected graph.
- Preserve old failed results and actual metadata. A new audit needs a declared
  seed/protocol and exposure disclosure, not repeated sampling to obtain a pass.
  Historical topic evaluation remains historical; edge-only fresh reviewers need
  explicit tested provenance support rather than invented topic completions.
- Included 9–10 November planning targets and a stopping rule: preserve the
  verified original draft if a replacement cannot be completed and audited;
  publish no unaudited success claims. Human annotation stays optional.
- Updated status/index only; no implementation, graph, review record, config,
  scientific rule or external state changed.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| Initial Git and regular-file/symlink checks | passed, exit 0 | clean base; new paths unused |
| `uv sync --locked --group dev --extra analysis --extra report` | passed, exit 0 | locked environment |
| `uv run pytest` | passed, exit 0; 419 passed, 1 existing empty-stage skip, 22.98 s | `reports/runs/WORK-2026-11-09-008/pytest.log` |
| Plan versus D040, rubric, resolver/topic builders and materializer | inspected; proposal explicitly requires dated amendment on adoption | no frozen files edited |
| New document local-link check; `git diff --check` | passed, exit 0 | referenced local targets exist; status under 60 lines |

## Decisions

None adopted. A proposed correction track is not an amendment to frozen D040.

## Open issues and limitations

Review findings remain unfixed; the recommended correction track is a proposal,
not an executed or adopted protocol change. No new scores are claimed. Code/data
CLI, database and package checks were not rerun for this documentation-only task.
Initial guessed NLP/test paths did not exist; file discovery located the actual
`resolve/release_topics.py`, `resolve/release_taxonomy.py` and release-graph tests.

## Next step

Implement plan step 1: require topic-ledger labels, add synthetic regressions,
run the suite/offline CLI and confirm real scores unchanged in new outputs.
The proposed graph track is separate; retain the current frozen graph and audit.

## Corrections

None.
