# WORK-2026-11-09-018 — Research Explorer redesign and implementation

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-09 22:23 +07:00 (Asia/Bangkok) |
| Work performed | 9 November 2026 22:21–23:32 +07:00 |
| Contributor | Antigravity, at the user's request |
| Related task | WORK-2026-11-09-017, WORK-2026-11-09-016 |
| Git state | `main` (`a2f8df6`); pre-existing staged WORK-016 files and untracked WORK-017 review preserved |

## Objective

Redesign and implement the local Research Explorer web application (`apps/research-explorer/`) using `design-taste-frontend` (`references/app-screens.md`) to resolve the responsive layout, information hierarchy, dark-mode contrast/token, graph/analytics readability, and discovery workflow issues documented in `reports/research-explorer-design-review-2026-11-09.md`, while preserving the existing stack, scientific semantics, and read-only Neo4j integration (`release-d3c788c3114a`).

## Changes and findings

- **App-screen style direction (`achromatic-ledger`, seed `103171675`)**:
  - Dealt via `draw.mjs --app` (`reports/runs/WORK-2026-11-09-018/style-draw/direction.json`) and paired with a neutral charcoal dark theme (`#101010` ground, `#171717` surface, `#212121` raised, `#292929` hairline border, `#efefef` ink, `#b5b5b5` muted, `#8c8c8c` faint) and warm stone light theme (`#f5f4f1` ground, `#ffffff` surface, `#eeece7` raised, `#e2e0da` border, `#161615` ink, `#5c5b57` muted, `#71706b` faint). All body/secondary text pairs pass WCAG AA contrast (`>= 4.5:1`), `Geist` (`400, 500, 600, 700`) and `Geist Mono` (`400, 500`) are loaded in `index.html`, and `tabular-nums` is enforced on all numerical elements.
- **Recomposed application shell & responsive architecture**:
  - `TopHeader.tsx`: untruncated `AI Research Network` identity with `AAAI · IJCAI 2021–2025` scope and `release-d3c788c3114a` badge on the left; global search trigger (`/`) and `Graph / Table / Analytics` segmented switcher in the center; `Paths`, `Compare`, `96.5% AI-assessed` caveats trigger, `Export & share` menu, persisted theme toggle, and contextual `Details` toggle on the right.
  - `App.tsx`, `LeftSidebar.tsx`, `RightInspector.tsx`: `LeftSidebar` renders only in `Graph` view (giving `Table` and `Analytics` 100% width). `RightInspector` is contextual (closed when nothing is selected, opening automatically upon node/edge selection), expanding the initial 1440px graph workspace from `736px` (`51%`) to `1,168px` (`81%`). On `< 1024px` (`768px` tablet and `390px` phone), both panels become slide-over drawers with backdrops (`absolute inset-y-0`) and explicit `Return to workspace` / `Return to graph` actions, eliminating the previous `64px` and `0px` workspace collapse.
- **Graph, Table, Analytics, and Discovery workflow refinements**:
  - `SigmaGraphCanvas.tsx`: restructured into a 3-band layout (top control bar with inline projection switcher when sidebar is closed, middle 100% unobstructed WebGL canvas, bottom encoding legend and keyboard-accessible top-entity strip). Implemented per-frame synchronous bounding-box collision rejection (`createCustomSigmaRenderers`) with right-edge label flipping and live theme updates without recreating the Sigma WebGL instance.
  - `RightInspector.tsx`: leads with entity identity and synthesized primary supported fact (`buildPrimaryFactSummary`), followed by Overview (separating full-projection centrality from displayed-subgraph degree), Connections grouped by predicate, and Evidence & Provenance with progressive `<details>` disclosure for raw IDs/hashes.
  - `neo4j_repo.py`, `explorer_service.py`, `TableView.tsx`: added read-only `get_nodes_degree_counts` so `/api/table/nodes` populates `displayed_degree` with actual Neo4j incident edge counts (e.g., `58 edges` for `Warut Suksompong`), resolving the table `0` vs. inspector `58 edges` discrepancy.
  - `AnalyticsView.tsx`: separated the 4-cell Inventory Summary Strip from the Scientific Quality, Coverage & Audit Status panel (`96.50% AI-assessed`, `73.71% Affiliation FAIL`, `85.00% cov / 0.4667 F1 Topic FAIL`); fixed ECharts legend placement (`top: 0, right: 0`), straight lines (`smooth: false`), and container `ResizeObserver`.
  - `EntityPicker.tsx`, `PathFinderModal.tsx`, `CompareModal.tsx`: replaced raw ID text inputs with name-based searchable entity pickers that retain stable IDs in a secondary monospace subline.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `node .../lint.mjs --app apps/research-explorer/frontend/src` | Exit `0`: `0 FAIL, 36 WARN` (monospace warnings on legitimate technical IDs/SHAs per app-screen exceptions) | `reports/runs/WORK-2026-11-09-018/lint.log` |
| `npm --prefix apps/research-explorer/frontend run build` | Exit `0`: `tsc -b && vite build` succeeded in `5.05s` | `apps/research-explorer/frontend/dist/` |
| `node .../inspect.mjs --app http://127.0.0.1:4173 --out .../round2` | Exit `0`: `RESULT: 0 FAIL, 0 WARN` across `1440px`, `768px`, and `390px` on the production preview build | `reports/runs/WORK-2026-11-09-018/round2/report.json` |
| `node reports/runs/WORK-2026-11-09-018/capture_after.mjs` | Exit `0`: 22 after screenshots captured across `1440px`, `768px`, `390px` in dark/light themes; `consoleErrors: []`, `pageErrors: []` | `reports/runs/WORK-2026-11-09-018/after/` |
| `npx --prefix apps/research-explorer/frontend playwright test -c apps/research-explorer/frontend/playwright.config.ts` | Exit `0`: `4 passed (26.3s)` | `apps/research-explorer/frontend/tests/explorer.spec.ts` |
| `.venv/bin/pytest apps/research-explorer/backend/tests -v -o pythonpath="apps/research-explorer src"` | Exit `0`: `14 passed in 10.07s` (8 unit + 6 live `neo4j-five-year` integration tests) | `apps/research-explorer/backend/tests/` |
| `.venv/bin/pytest tests/` | Exit `0`: `507 passed, 2 skipped in 19.43s` | Repository test suite |

## Decisions

- Selected `achromatic-ledger` (`seed 103171675`) paired with neutral charcoal dark mode (`#101010` / `#171717` / `#212121`) so categorical node/edge encodings carry visual emphasis while application chrome remains quiet during extended research sessions.
- Resolved the table/inspector degree discrepancy by querying actual incident relationship counts (`get_nodes_degree_counts`) for paginated table rows and labeling the column `DB incident edges` alongside `Full-projection score`.

## Open issues and limitations

- All scientific and corpus caveats remain unchanged and prominently disclosed in the header (`96.5% AI-assessed`), Analytics quality panel, Inspector provenance section, and Caveats modal: edge precision (`193/200 = 96.50%`, Wilson 95% CI `92.95%–98.29%`) is AI-assessed (`agent-audit-v1`) without human annotation; affiliation coverage (`73.71%`) fails the `80%` gate; embedding topic inference (`85.00%` coverage, micro-F1 `0.4667`) fails the `90%` / `0.80` gates.
- Pre-existing staged files from `WORK-2026-11-09-016` and untracked review artifacts from `WORK-2026-11-09-017` were preserved in the working tree without resetting the Git index.

## Next step

Review the redesigned workspace locally (`http://127.0.0.1:5173` or production preview `http://127.0.0.1:4173`) and commit `WORK-016` through `WORK-018` when ready.

## Corrections

None.
