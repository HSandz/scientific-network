# Explorer focus labels and analytical layout verification — 11 November 2026

Work: WORK-2026-11-11-002. Scope: frontend presentation, tests and documentation.
Initial clean main/remote HEAD: `5e4da480dbdb6aff01edfd838744c4bb6d3e5856`.
The matching production Pages deployment was `7bb4d637-2ec8-4a18-8a9a-8c2f380456de`.
No API, database, graph, frozen analytics, dependencies or infrastructure edits.
Delivery status: implementation complete; consolidated regression and delivery receipt below.
All recorded times use Asia/Bangkok (+07:00).

## Before-change reproduction

Captured all four local frontend projections against the live read-only API and
production Graph/Analytics before editing. Each graph showed a focused node name
without neighbor names at overview. Initial label boxes were empty. The selected
edge reducer also took precedence over transient node focus. Persistence-cell
identity depended on flattened array position; tooltip used numbered pairs.

At 1440×900, baseline card bounding boxes measured robustness 691/1,568px tall,
sector mixing/pair evidence 498/1,996px, and cohort/citation inventory 1,312/164px.
These differences left large empty grid regions. Baseline captures and JSON:
`reports/runs/WORK-2026-11-11-002/before*.png`, `before.json` (ignored).
Element screenshots of sections inside the scrolling dashboard can include blank
clipped regions; viewport captures and bounding boxes establish the comparison.

## Changes and scientific boundary

- `components/graph/focusLabels.ts` extracts label planning/painting from
  `SigmaGraphCanvas.tsx`. Routine labels keep inverse zoom, hysteresis and sparse
  overview. Interactive neighbors have separate viewport-aware caps, up to 12 at
  overview,16 medium,24 close,32 detail. These are maxima, not guaranteed counts.
- Focus has first priority, selected-edge endpoints second, direct neighbors next,
  then routine labels when there is no focus. Degree and stable IDs break ties.
  Hover overrides neighborhood emphasis while selected endpoints remain identifiable.
- Eight placement directions with bounded offsets reject other label rectangles,
  important node disks, hover-card reservations and canvas clipping. Displaced
  focus labels have leader lines to their own node. Dimmed background disks do not
  prevent interactive identification. Routine labels avoid all node disks.
- Planning starts in the first Sigma label callback, after normalization and camera
  matrix processing. `beforeRender` invalidates the plan; `afterRender` records only
  text that actually reached the label canvas. Hover drawing adds rings, not a
  second competing text layer. No per-node DOM or extra graph API requests.
- The summary distinguishes labeled neighbors from all neighbors in the displayed
  graph and reports `+N more`. Existing inspector connection lists remain available.
- Sigma 3 retains its internal hovered ID on stage exit. A public `enterStage`
  viewport/disk check restores transient state when returning directly to that same
  node; ghost hover rings are suppressed after exit. No private Sigma mutation.
- Robustness uses a full-width comparison with paired chart/count summaries,
  followed by a six-row preview of the top three in each stored ranking. The
  complete linked shortlist union stays in an expandable exact-data table.
- Sectors retains a matrix beside a five-entry ranked preview, one selected
  pair/topic detail panel, and a full-width persistence heatmap. Full names, distinct
  support, all-topic annual support when stored, and explicitly bounded paper
  previews replace repetitive evidence cards. All 25 pair-topic entries remain
  available. Selection outlines the corresponding canonical persistence row.
- Persistence tooltips escape full organization names and show actual year/support.
  Cells carry source/target IDs; clicks do not derive identity from `dataIndex`.
  Missing years remain null; a missing shortlist row is explicitly unavailable.
- Citation activity, CCDF and cohort figures use full-width panels. Cohort share/CDF
  and community rankings/selected portfolio use balanced inner rows. Exact tables
  and graph/evidence actions remain. Seven sections and saved section/filter IDs
  are preserved. The sticky horizontal navigation keeps its active item visible.
- Removed a redundant robustness legend that overlapped the mobile axis title.
  ECharts lazy loading, offscreen disposal,600ms entrance/300ms updates and live
  reduced-motion handling are unchanged.

The existing achromatic-ledger palette and type were retained. The design skill
was applied to hierarchy, data prominence, spacing and screenshot review; the
existing navigation shell was preserved. No scientific denominators, accepted
claims, inferred topics, scores or failed quality targets were changed. Preview
paper years are explicitly not annual totals. Co-publication is not evidence of
contracts, employment or funding.

## Verification and screenshots

Focus regressions check actual canvas `fillText`,
text/ID/name agreement, true adjacency, focus/endpoint precedence, mouse exit,
same-node re-entry, selection, themes, camera controls and rectangle geometry.
Invented 30- and 100-neighbor fixtures are stress cases, never scientific results.
Layout regressions measure widths, card gaps, sticky heading clearance, active
navigation visibility and horizontal overflow at 1440×900,1024×768,768×1024,390×844
in both themes. Real canvas clicks cover selected pair/topic and reordered/filtered
persistence cells; hostile tooltip text is escaped. Full bridge links are tested.

Reviewed captures include all projection hover/selection states, the 100-neighbor
stress case, desktop/phone Robustness/Sectors/Citations in light/dark, and refreshed
graph overview/close baselines. Twelve added Analytics snapshot images cover the
three redesigned sections at desktop/phone sizes in both themes. Overview Analytics
baselines remain unchanged. Graph baselines previously used a different bounded
runtime preview (108 nodes/170 edges); the live API already returned110/166 before
this task. Their refreshed geometry reflects that runtime preview and the label
policy, not a graph-data edit. Baseline API/summary snapshots are retained locally.

Raw outputs and reviewed comparison sheets live under
`reports/runs/WORK-2026-11-11-002/` (ignored); reproducible PNG baselines live under
`apps/research-explorer/frontend/tests/visual.spec.ts-snapshots/`.

### Commands and outcomes

- `uv sync --locked --group dev --extra analysis --extra report`: passed.
- `uv run pytest`:530 passed,one existing skip.
- `npm --prefix apps/research-explorer/frontend run build`: TypeScript and Vite passed; existing537.43KB ECharts warning remains.
- Frontend pure contracts (`playwright.contracts.config.ts`):7 passed.
- Full Chromium suite:52 passed (2.9 minutes), including the three visual cases. Initial run50 passed /2 failed because the local HTTP proxy discarded POST methods/bodies; corrected the ignored proxy, with no assertion changes.
- Focus suite6 passed; layout/interaction suite7 passed; visual suite3 passed.
- `PYTHONPATH=apps/research-explorer:src uv run pytest apps/research-explorer/backend/tests -v`:23 passed,9 skipped,one warning. Nine local Neo4j integrations unavailable.
- Offline `research-network schema` and `validate --input tests/fixtures/synthetic_graph.json --config configs/quality.yaml --output <run>/synthetic-validation.json`: passed; structural_only/ineligible_synthetic, not scientific accuracy.
- Pre-delivery production API smoke:28 passed.
- `git diff --check`: passed.

## Performance and limits

Before/after measurements (same workstation, archived pre-change frontend and live read-only API):

| Measurement | Before | After |
| --- | --- | --- |
| Hover median / p95,120 interactions | 3.8 /7.4ms | 4.4 /8.2ms |
| Placement median / p95 / max | n/a | 0.2 /0.6 /1.9ms |
| Pan/zoom frame median / p95,90 frames | 24.1 /30.1ms | 25.1 /36.8ms |
| Heap after GC,before /120 /360 interactions | 8.78 /10.52 /11.01MB | 8.74 /10.55 /11.02MB |
| Maximum active dashboard charts | 5 | 4 |
| Additional graph-focus API requests | 0 | 0 |

Both pan/zoom samples had roughly1.2s workstation outliers. These measurements
do not establish smooth60fps. Hover figures use the real110-node/166-edge bounded
preview; invented100-neighbor cases separately verify label bounds. No page errors.
Workstation Chromium software/GPU behavior,
short runs and bounded subgraphs do not establish physical-device performance or
long-session leak freedom. Existing deferred ECharts chunk remains over500KB.
Firefox/Safari, physical phones and formal screen-reader certification are untested.
The local Neo4j service was unavailable; browser checks used the existing production
HTTP API through a local read-only proxy. No database was started or modified.

## Production receipt

Pending authorized frontend push, exact-SHA Pages confirmation, public browser
smoke checks, API smoke checks and before/after read-only preservation comparisons.
