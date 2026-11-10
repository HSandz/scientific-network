# WORK-2026-11-09-017 — Research Explorer design review

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-09 21:57 +07:00 (Asia/Bangkok) |
| Work performed | 9 November 2026 21:46–21:57 +07:00 |
| Contributor | Codex |
| Related task | WORK-2026-11-09-016 |
| Git state | main at a2f8df6; pre-existing staged application, dependency and documentation changes preserved |

## Objective

Review the local Research Explorer using design-taste-frontend app-screen rules.
Recommendations only; no application implementation, scientific changes or publication.

## Changes and findings

- Wrote the [screenshot-based critique](../../reports/research-explorer-design-review-2026-11-09.md), with a subjective design score of 4.9/10.
- Fixed 320px/384px sidebars leave 736px at desktop, 64px at tablet and 0px at phone width. Analytics inherits graph rails and cramped KPI columns.
- Found 3.8:1 secondary text, 21 text blocks below 11px, pale graph hover backgrounds behind near-white text, and graph/chart label collisions.
- Proposed shell/responsive changes, shared dark typography/rendering tokens, and graph/analytics readability improvements. Preserve all scientific limitations and evidence access.
- Port 5173 serves the frontend; port 8000 is the API (root returns 404).

## Verification

All raw evidence is ignored under `reports/runs/WORK-2026-11-09-017/`.

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `uv sync --locked --group dev --extra analysis`; `uv run pytest` | exit 0 each; 502 passed, 7 skipped; sync removed optional Markdown, causing six report skips | `uv-sync.log`, `pytest.log` |
| `uv sync --locked --group dev --extra analysis --extra report`; `uv run pytest` | restored existing report extra; exit 0 each; 508 passed, 1 existing skip | `uv-sync-restore-report-extra.log`, `pytest-with-report-extra.log` |
| `node /home/san/.agents/skills/design-taste-frontend/scripts/inspect.mjs --app http://127.0.0.1:5173 --out reports/runs/WORK-2026-11-09-017/before` | exit 1; 4 FAIL / 3 WARN categories across 1440, 768, 390px; all six images opened | `inspect.log`, `before/report.json` |
| `node /home/san/.agents/skills/design-taste-frontend/scripts/lint.mjs --app apps/research-explorer/frontend/src` | exit 1; 13 FAIL / 131 WARN occurrences; app exceptions discussed in report | `lint.log` |
| `node reports/runs/WORK-2026-11-09-017/browser-review.mjs` | exit 0; 13 screenshots and width measurements; no uncaught page errors | `browser-review.log`, `browser-measurements.json` |
| `node reports/runs/WORK-2026-11-09-017/modal-review.mjs` (two runs) | exit 0 each; first skipped two incorrect test IDs; corrected rerun captured both; all images opened | `modal-review.log`, `modal-review-second.log` |
| Production build, full accessibility audit and new E2E suite | not run; review of existing development server only | Report limitations |

## Decisions

None adopted; recommendations remain proposals. No release checkpoint or commit.

## Open issues and limitations

Scientific accuracy and every disclosure were not independently audited. The table's
zero incident-edge display versus the selected inspector's nonzero counts needs a
separate functional trace. An initial documentation patch failed its README context
match without changing files; corrected using the actual index content.

## Next step

If implementation is authorized, begin with `apps/research-explorer/frontend/src/App.tsx`
and the layout panels; verify usable primary workspaces at 1440, 768 and 390px.

## Corrections

None.
