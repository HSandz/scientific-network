# WORK-2026-11-10-005 — Research Explorer usability and graph operations implementation

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-10 09:30 +07:00 (Asia/Bangkok) |
| Work performed | 10 November 2026 |
| Contributor | Antigravity |
| Related task | WORK-2026-11-10-004, WORK-2026-11-10-003, WORK-2026-11-10-002 |
| Git state | main at 41852c6; implementation across apps/research-explorer verified |

## Objective

Implement the complete combined Research Explorer improvement plan ([docs/research-explorer-graph-usability-plan.md](../research-explorer-graph-usability-plan.md)) across `apps/research-explorer/`. Address all graph operations findings (G01–G11) and website verification findings:
1. Authoritative effective-graph view state (canvas, counts, legend, metrics, neighbor list, exports, shared URLs agree).
2. Neighborhood reading on hover/pinning with collision-free labels, 7/7 legible neighbor names for moderate neighborhoods (Warut example), honest totals and complete searchable/selectable neighbor lists for dense nodes (Zhejiang, Representation learning).
3. Explicit Overview, Ego/neighborhood, and Path views with Back navigation, projection/filter-bounded expansion (+1 hop), reciprocal/parallel edge preservation in multi-edge graphology, and retryable error states.
4. Camera continuity, layout stability, responsive inline node sizing and spacing, and selection persistence across layouts without dimming unrelated projections.
5. Truthful filters (no fallback to all edges), projection-appropriate link strength, and complete URL round-trip serialization.
6. Responsive header hit-target clearance across 390px, 768px, 1024px, 1100px, 1280px, and 1440px; accessible combobox/listbox pickers and modal/overlay drawer focus containment; unavailable contract fallback for absent quality data; and soft graphite theme consistency.

## Changes and findings

1. **Authoritative Effective Graph State (`App.tsx`, `useExplorerStore.ts`, `types/explorer.ts`):**
   - Centralized `effectiveGraph` in `App.tsx` as the single authoritative source of truth. Scope filters, presentation filters, and degree/strength metrics are derived once and distributed synchronously to canvas, inspector, header, and export handlers.
   - Removed all silent fallbacks (e.g. strong links returning all edges). Zero matching edges renders an empty canvas with an honest reset banner.
   - Distinct edge identity preserved: all edges retain stable edge IDs (`e.edge_id`). Parallel predicates and reciprocal citation links are never collapsed or suppressed.

2. **Neighborhood Reading & Pinned Inspection (`SigmaGraphCanvas.tsx`, `RightInspector.tsx`):**
   - Enhanced Sigma custom label renderer with 4-way collision-aware candidate placement (Right, Left, Above, Below) and boundary clamping.
   - In `nodeReducer`: when `visibleNeighborCount <= 12`, labels are forced on the center AND all visible first-hop neighbors. For Warut Suksompong (`researcher:openalex:A5086022217`), all 7 visible neighbor names are rendered legibly on canvas simultaneously.
   - For dense neighborhoods (> 12 neighbors, e.g. Zhejiang University with 53 or Representation learning with 28), only the top prominent neighbors are labeled on canvas to avoid a text wall, and a dense neighborhood badge points to the complete, searchable neighbor list in the inspector.
   - Added **"On this graph ({visibleNeighborsList.length} visible neighbors)"** in `RightInspector.tsx` with a live filter, entity badges, direction indicators (`↔`, `→`, `←`), paper counts/weights, row selection, and direct "Evidence" button for each incident edge.
   - Separately labeled **"All database connections ({total_degree} total)"** with transparent scope copy disclosing that it includes stored edges beyond current filters.

3. **Explicit Graph Views & Return Route (`App.tsx`, `useExplorerStore.ts`, `SigmaGraphCanvas.tsx`, `PathFinderModal.tsx`):**
   - Added explicit view scopes: `overview`, `ego`, and `path`.
   - **Ego view:** isolates the center entity and its bounded 1-hop neighborhood, fits the view, and provides a top-left `[← Back to overview]` banner that restores prior scope, selection, positions, and camera.
   - **Path view:** emphasizes ordered traversal steps on canvas with step-level evidence, and provides `[← Back to previous view]`.
   - **Expansion:** `Expand +1 hop` bounds additions to the active projection and filters; expansion errors render a visible inline error banner with a `[Retry]` action.

4. **Multi-Edge Graphology, Camera Preservation & Layout (`SigmaGraphCanvas.tsx`):**
   - Replaced Graphology instance with `new Graph({ multi: true, type: "mixed" })` and removed `existingEdge` suppression. Reciprocal citation links (e.g. Informer CITES) and parallel predicates are retained.
   - Saved and restored camera zoom/pan states across updates to prevent unwanted camera resets during selection and expansion.
   - Added explicit `handleFitNeighborhood` alongside `handleResetCamera`.
   - Concentric layout reworked into non-overlapping multi-ring capacity based on score quartiles and circumference spacing. Viewport-aware inline node sizing adapts smoothly across desktop, tablet, and mobile.

5. **Website & Accessibility Fixes (`TopHeader.tsx`, `EntityPicker.tsx`, `LeftSidebar.tsx`, `AnalyticsView.tsx`, `TableView.tsx`, `index.css`):**
   - Header: collapsed secondary tools (`Paths`, `Compare`, `Caveats`) into a `MoreHorizontal` menu on `< 1280px`, giving primary navigation tabs (Graph, Table, Analytics) dedicated click clearance at 768px and 1024px.
   - Drawers: added `role="dialog"`, `aria-modal="true"`, accessible labels, and Escape key listeners to mobile overlay sidebars.
   - Entity Picker: added `role="combobox"`, `aria-autocomplete="list"`, `aria-expanded`, and active option tracking to search inputs.
   - Quality contract: replaced hardcoded numeric constants with truthful "Unavailable" states and derived target/pass/fail copy.
   - Mobile Analytics/Table: updated `.ledger-kpis` to a 2×2 grid on `< 480px` to bring analytical charts above the fold; table rows provide distinct button actions for graph focusing and evidence tracing.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `PYTHONPATH=apps/research-explorer:src .venv/bin/pytest apps/research-explorer/backend/tests -v` | passed; exit 0 (15 passed) | Live Neo4j bolt://127.0.0.1:7689 integration & unit tests |
| `.venv/bin/pytest tests` | passed; exit 0 (507 passed, 2 skipped) | Full repo unit test suite |
| `npm --prefix apps/research-explorer/frontend run build` | passed; exit 0 | Production TypeScript & Vite build |
| `npm --prefix apps/research-explorer/frontend run test:e2e` | passed; exit 0 (5 tests passed, 38.7s) | Playwright E2E across desktop, tablet, and mobile viewports |
| `node /home/san/.gemini/config/skills/design-taste-frontend/scripts/lint.mjs --app apps/research-explorer/frontend/src` | passed; exit 0 (0 FAIL, 41 WARN) | Design taste app lint |
| Visual inspection of generated screenshots | verified; soft graphite dark theme maintained | `explorer-warut-7-neighbors.png`, `explorer-ego-view.png`, `explorer-tablet-768.png`, `explorer-analytics-overview.png`, `explorer-mode-a-researchers.png` |

## Decisions

- **D041 (Explorer Usability Architecture):** Establish authoritative effective-graph single-slice state in `App.tsx`, multi-edge `Graph({ multi: true, type: "mixed" })` in Sigma, 4-way collision-aware label placement, explicit Ego/Path view scoping with Back navigation, and unavailable quality contract fallbacks.

## Open issues and limitations

- None. All 11 graph operations findings (G01–G11) and website review findings are resolved and verified against live Neo4j database service on port 7689.

## Next step

- Proceed with release plan phases per `docs/release-plan.md`.

## Corrections

- None.
