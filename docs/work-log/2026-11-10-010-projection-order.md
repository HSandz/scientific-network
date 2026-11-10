# WORK-2026-11-10-010 — Explorer projection order and default

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-10 20:09 +07:00 (Asia/Bangkok) |
| Work performed | 10 November 2026, 20:07–20:09 +07:00 |
| Contributor | Codex |
| Related task | User-requested sidebar order/default; commit and push |
| Git state | Clean main at e1d35cc at start; origin/main matched before checkpoint |

## Objective

Order the sidebar projections as Knowledge graph, Organizations, Researchers,
Citations and open Knowledge graph by default. Verify, commit and push to origin.

## Changes and findings

- Reordered `LeftSidebar.tsx` projections as requested.
- Initial Zustand mode is `heterogeneous`, with its existing 120-node limit and
  corresponding overview title. Explicit URL modes and saved views still apply.
- Updated the existing browser flow to assert the new initial selection/order;
  researcher-specific scenarios explicitly request `?mode=researchers`.
- Updated status and work-log index. No scientific artifacts or dependencies changed.

## Verification

| Command/check | Outcome and exit code |
| --- | --- |
| `uv sync --locked --group dev --extra analysis` then `uv run pytest` | exit 0; 518 passed, 7 skipped (six require optional report extra) |
| `uv sync --locked --group dev --extra analysis --extra report` then `uv run pytest` | exit 0; 524 passed, 1 existing skip |
| `npm run build` (frontend) | exit 0; TypeScript and Vite production build passed; existing large-chunk warning |
| `EXPLORER_SCREENSHOT_DIR=<run-dir> npm run test:e2e` (frontend) | exit 0; all 5 Chromium suites passed against local live API/Neo4j and Vite |
| `uv run research-network validate --input tests/fixtures/synthetic_graph.json` | exit 0; structural-only synthetic fixture validation passed |
| `git diff --check`; `git ls-remote origin refs/heads/main` | exit 0; patch clean, remote matched starting checkpoint |

Raw browser screenshots and test output: ignored
`reports/runs/WORK-2026-11-10-010/`.

## Decisions

None; presentation-only user request.

## Open issues and limitations

Production build retains its existing bundle-size warning. Browser verification
was local; no claim of deployed frontend acceptance. No scientific graph changes.

## Next step

Commit and push this verified checkpoint to origin/main as explicitly requested;
verify remote HEAD matches the local commit. No further implementation needed.

## Corrections

None.
