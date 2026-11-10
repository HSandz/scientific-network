# WORK-2026-11-10-003 — Graph operations review and improvement plan

| Field | Value |
| --- | --- |
| Status | completed (review and plan; findings open) |
| Recorded | 2026-11-10 08:20 +07:00 (Asia/Bangkok) |
| Work performed | 10 November 2026 |
| Contributor | Codex |
| Related task | WORK-2026-11-10-002, WORK-2026-11-09-020 |
| Git state | main at 41852c6; earlier review docs remain uncommitted and preserved |

## Objective

Review all four graph projections and their operations, with emphasis on the user's
missing-neighbor-name hover issue. Combine graph and earlier website findings in a
prioritized implementation plan. Planning/review only.

## Changes and findings

- Added the [graph operations review](../../reports/research-explorer-graph-operations-review-2026-11-10.md)
  and the [combined implementation plan](../research-explorer-graph-usability-plan.md).
- Confirmed that Warut's 7 visible neighbors show 1 name; the selected topic's 28
  neighbors show 1; a dense organization's 53 neighbors show 10; the small citation
  example shows both neighbor names.
- Recorded operation issues: Ego retains unrelated base nodes; expansion mixes
  predicates into a projection with stale labels/filters; parallel/reciprocal edges
  are dropped; displayed degree is stale; layout/mode changes leave selection state
  inconsistent; expansion resets camera; filter, export and share state diverge;
  Paths lacks a dedicated view/return route; request failure is silent; phone graph
  tools are unavailable.
- Preserved the softer graphite direction and prior website findings. No app files,
  graph records, frozen data, public Site or release package changed.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `uv sync --locked --group dev --extra analysis --extra report` | Passed; exit 0 | `reports/runs/WORK-2026-11-10-003/sync.log` |
| `uv run pytest` | 508 passed, 1 existing skip; exit 0 (20.72s) | `reports/runs/WORK-2026-11-10-003/pytest.log` |
| `node reports/runs/WORK-2026-11-10-003/graph-review.mjs` | Completed all four projections, pointer hover/selection, layouts, expand/Ego, switching, filters and phone; no page exceptions | `graph-review.json`, `hover-summary.json`, captures under ignored run directory |
| `node reports/runs/WORK-2026-11-10-003/supplemental-review.mjs` | Completed edge evidence, Paths, JSON export/share reload, simulated 503 and drag checks | `supplemental-review.json` |
| `node reports/runs/WORK-2026-11-10-003/final-checks.mjs` | Completed settled edge evidence/click, filtered degree, eight light screenshots | `final-checks.json`, screenshots and opened contact sheets |
| Application preservation | 49 captured app files match their baseline SHA256; no app changes | `reports/runs/WORK-2026-11-10-003/app-before.json` and `app-preservation.json` |
| Local documentation links / whitespace | 108 relative links resolve; status has 42 lines; tracked `git diff --check` passes | All new records and status/index |

WORK-002's backend tests, E2E, build and skill inspections are historical and were
not rerun here. Read-only browser runtime instrumentation used the local production
preview on :4173 and API :8000; no database writes. Initial capture harness timing
and selector errors were corrected; completed runs are summarized above. Limits:
selected representative examples rather than every entity/preset, and no physical
touch device or screen-reader certification.

## Decisions

None. Recommendations are in the linked plan; scientific graph semantics stay fixed.

## Open issues and limitations

Implementation findings remain open. Current plan is a proposal for a later
implementation task; this task made no application changes. Full accuracy audit,
all-node graph review and device-level accessibility were outside scope.

## Next step

Use the combined plan for a focused implementation pass. Begin with view/edge
integrity and the pinned, named-neighbor interaction; preserve data semantics and
verify all four projections and the listed operations.

## Corrections

Clarified WORK-002's node-size source: the active renderer computes size inline at
`SigmaGraphCanvas.tsx:316–317`; its separate `getNodeRadius` helper is unused by
this canvas. The phone collision observation remains valid. The clarification is
also recorded in the graph review, without rewriting WORK-002.
