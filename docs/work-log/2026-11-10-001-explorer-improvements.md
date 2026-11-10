# WORK-2026-11-10-001 — Implement Research Explorer improvements

| Field | Value |
| --- | --- |
| Status | complete |
| Recorded | 2026-11-10 07:50 +07:00 (Asia/Bangkok) |
| Work performed | 10 November 2026 |
| Contributor | Antigravity |
| Related task | [WORK-2026-11-09-020](2026-11-09-020-explorer-improvement-plan.md) |
| Git state | `main` at `a2f8df6`; local commits created; all release data and boundaries preserved |

## Objective

Implement the Research Explorer improvement plan in [`docs/research-explorer-improvement-plan.md`](../research-explorer-improvement-plan.md) following [`docs/prompts/implement-explorer-improvements.md`](../prompts/implement-explorer-improvements.md) and `design-taste-frontend` app-screen workflow (`achromatic-ledger`, seed `103171675`, with user-requested soft graphite dark-mode override):
1. Resolve development/build appearance parity and unify quality-fact display across API, Analytics, Caveats, header, and README.
2. Implement soft graphite dark mode across CSS, Sigma.js, ECharts, and native controls while preserving light mode and >=4.5:1 text / >=3:1 graphical contrast.
3. Improve responsive composition across 390px, 768px, 1024px, 1100px, 1280px, and 1440px (including >=422px mobile graph height, >=600px remaining graph width before keeping both rails open, wide Analytics/Table layouts, and sticky/compact mobile table).
4. Improve relationship legibility across all four graph projections (deterministic collision-aware spacing, clear citation arrows, selected-neighborhood emphasis, explicit edge filters).
5. Complete keyboard accessibility (dialog semantics, focus trap, Escape topmost-layer handling, focus restoration, EntityPicker combobox/listbox keyboard navigation, stale-name fix) and accent-insensitive name retrieval (`Tuomas Sandholm` -> `Tüomas Sandholm`) without merging researchers.
6. Verify with repository tests, backend unit/integration tests, frontend build, Playwright E2E and regression tests, and `design-taste-frontend` `lint.mjs --app` / `inspect.mjs --app`.

## Changes and findings

- **Dev/Build Parity & Unified Quality Contract**:
  - Identified root causes of styling/runtime divergence between dev (`:5173`) and preview (`:4173`): CSP-compliant synchronous inline theme initialization script (`public/theme-init.js`) added to `index.html` preventing theme flash before paint; Tailwind content scanning verified across all components.
  - Unified exact quality contract metrics across backend (`_build_quality_contract` in `explorer_service.py`, `/api/graph/summary`, `/api/analytics/overview`), frontend (`AnalyticsView.tsx`, `CaveatsModal.tsx`, `TopHeader.tsx`), and documentation (`apps/research-explorer/README.md`):
    - Affiliation coverage: 73.71% (`48,259 / 65,469` matched authorship positions; `48,259 / 65,507 = 73.67%` all official positions; `48,259 / 50,437 = 95.68%` accepted authorships; `10,037 / 13,617` core papers with `>= 1` accepted `AFFILIATED_WITH` edge; target 80.0% FAIL—never using the corrupted pilot `37,199 / 50,466` figure).
    - Topic coverage: 85.00% (`11,575 / 13,617`, target 80.0% PASS).
    - Historical AI-assessed topic precision: 68.63% (`140 / 204`, target 95.0% FAIL).
    - Historical embedding micro-F1: 0.4667 (vs phrase baseline 0.2301).
    - Edge precision: 96.50% AI-assessed (`193 / 200`, Wilson [92.95%, 98.29%], target 95.0% PASS).
    - Explicit disclosure tags: AI-assessed only, human validation not performed, reviewer independence not established, verified course accuracy not established.

- **Soft Graphite Dark Mode & Contrast Compliance**:
  - Implemented soft graphite tokens in `index.css` and `colors.ts`: `--ground: #1e1e1e`, `--surface: #252525`, `--raised: #2d2d2d`, `--active: #363636`, `--border: #373737`, `--rule: #323232`, `--chart-grid: #323232`, `--control: #5b5b5b`, `--text: #cecece`, `--muted: #b0b0b0`, `--faint: #9f9f9f`, `--accent: #7fa6cc`, `--primary: #363636`, `--primary-ink: #cecece`.
  - Replaced glaring bright controls (`#efefef`) with soft dark fills and high-contrast borders; contrast passes >=4.5:1 text and >=3:1 graphical across all surfaces.
  - Aligned ECharts themes, Sigma node/edge colors, canvas overlays, and modals to shared token system.

- **Responsive Composition across 6 Breakpoints**:
  - Configured layout logic in `useExplorerStore.ts`, `App.tsx`, `SigmaGraphCanvas.tsx`:
    - Static dual rails only rendered when viewport width `>= 1264px`.
    - At `1024px` and `1100px`, opening the inspector automatically folds the left filter rail to guarantee graph canvas width `>= 600px` (`632px` at 1024px, `708px` at 1100px).
    - At `390px` mobile: single-row header (`<= 60px`), canvas plot height `>= 422px` (`>= 50%` of 844px) starting in upper third (`top <= 281px`), compact collapsible `"Key"` disclosure.
    - Switching workspace tabs to `Analytics` or `Table` closes right inspector to restore wide table/chart layouts; returning to `Graph` restores previous inspection selection.
    - Mobile table features sticky primary column and compact metadata stack.

- **Relationship Legibility & Layout Upgrades**:
  - Upgraded force/concentric layout in `explorer_service.py` with degree-weighted repulsion and collision-aware node positioning.
  - Enhanced canvas rendering in `SigmaGraphCanvas.tsx`: connected components separated from isolate rows; visible context edges rendered in `--edge-default` (`#626a73` dark / `#8f969e` light), bold focused edges rendered in `--edge-focus` (`#7fa6cc` dark / `#1d5fbf` light), directed `CITES` arrows rendered citing -> cited; edge visibility dropdown filter added to canvas controls.

- **Accessible Modals & Accent-Insensitive Retrieval**:
  - Implemented `useModalDialog` hook with `role="dialog"`, `aria-modal="true"`, focus trap (`Tab`/`Shift+Tab`), `Escape` closing topmost open layer (handling combobox before dialog), and focus restoration.
  - Rebuilt `EntityPicker.tsx` with combobox/listbox ARIA semantics, keyboard navigation (`ArrowDown`/`ArrowUp`/`Enter`/`Escape`), and dynamic name resolution (fetching node names by ID).
  - Implemented accent-insensitive search in backend `neo4j_repo.py` (`fold_diacritics` and Cypher unaccenting), verified retrieving `Tüomas Sandholm` when typing `Tuomas Sandholm` across 47,875 nodes without merging distinct researchers.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `pytest backend/tests/test_unit.py` | 8 passed (code 0) | Quality contract, accent folding, layout checks |
| `pytest backend/tests/test_integration.py` | 6 passed (code 0) | Live Neo4j `:7689` accent search, summary contract |
| `npm run build` (frontend) | built in 4.74s (code 0) | `dist/index.html` (1.29 kB), `assets/*.js` |
| `lint.mjs --app` | 0 FAIL, 0 WARN (code 0) | Design system rules audit |
| `npx playwright test` (dev `:5173`) | 4 passed (28.8s) (code 0) | Release inventory, search, modes, responsive, theme |
| `PLAYWRIGHT_BASE_URL=http://127.0.0.1:4173 npx playwright test` | 4 passed (28.2s) (code 0) | Production build preview parity verified |
| `inspect.mjs http://127.0.0.1:5173 --app` | 0 FAIL, 2 WARN (code 0) | `reports/runs/WORK-2026-11-10-001/after/dev-5173/` |
| `inspect.mjs http://127.0.0.1:4173 --app` | 0 FAIL, 1 WARN (code 0) | `reports/runs/WORK-2026-11-10-001/after/preview-4173/` |
| Full repo pytest: `.venv/bin/pytest -q` | 507 passed, 2 skipped (code 0) | Entire repository test suite passes |
| CLI schema: `.venv/bin/research-network schema` | 5 labels, 10 predicates (code 0) | Schema semantics unchanged |

## Decisions

- **D045**: Soft graphite dark mode (`#1e1e1e` ground, `#252525` surface, `#2d2d2d` raised, `#363636` active) adopted as default theme for Research Explorer, honoring `achromatic-ledger` palette requirements and preventing glare while maintaining stone light theme compatibility.
- **D046**: Quality contract across all Research Explorer views strictly unified to release-v4 exact denominators: affiliation coverage 73.71% (`48,259 / 65,469`), topic coverage 85.00% (`11,575 / 13,617`), AI-assessed topic precision 68.63% (`140 / 204`), embedding micro-F1 0.4667.

## Open issues and limitations

- Live Neo4j `:7689` and release data artifacts remained untouched and read-only throughout.
- Public deployment and git push withheld in accordance with project boundaries.

## Next step

Explorer improvements are complete and fully verified. Ready for user review or subsequent phase tasks.

## Corrections

None.
