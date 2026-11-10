# Explorer UI redesign verification — 11 November 2026

Status: implemented, pushed and verified on production. Receipt recorded 2026-11-11 01:15 +07:00.
Work: WORK-2026-11-11-001. All times Asia/Bangkok (+07:00).

## Implementation and scope

Replaced five mutually exclusive analytics reports with seven scrolling sections:
overview, scientific quality, collaboration robustness, topic evolution, components
and communities, academia–industry, and citation/research trends. Sticky section
navigation retains v2 bookmark compatibility. Filters, graph-return actions,
researcher/paper/evidence links and exact-value tables remain available.

New visible figures include coverage/precision target bars, Wilson point/interval,
historical F1 comparison, separate network-count comparisons, bridge shortlist
rank matrix, topic endpoint changes and venue lines, organization pair support and
pair/year persistence, annual activity, cohort uncited share/CDF and citation
leaders. Existing heatmaps, component distribution, community portfolios and
degree CCDF have contained axes and clearer labels. Mobile filters wrap.
Sidebar citation inventory explicitly says “papers”.

Key files under `apps/research-explorer/frontend/src/`:

- `components/analytics/AnalyticsView.tsx`, `DashboardNavigation.tsx`,
  `DashboardPrimitives.tsx`: layout, navigation and reusable scientific cards.
- `QualityFigures.tsx`, `RankedFigures.tsx`, `TemporalFigures.tsx`: typed figures
  and accessible equivalent values/actions.
- `EChartBox.tsx`, `EChartRuntime.tsx`: lazy engine, viewport lifecycle and motion.
- `components/graph/SigmaGraphCanvas.tsx`, `lib/labelPolicy.ts`: zoom/readability.
- `App.tsx`, store/view schema, styles, sidebar and Vite/Playwright configuration:
  deferred modules, hydration, compatible views, responsive controls and isolated tests.
- `tests/dashboard.spec.ts`, `tests/visual.spec.ts`, `tests/contracts.spec.ts`:
  behavioral, numerical, geometry, motion and screenshot regression coverage.
- `.github/workflows/explorer-frontend.yml`: frontend build and offline contracts.

Documentation updated in Explorer README, status, roadmap, decisions and work log.
No backend, graph data, artifact, dependency or infrastructure changes.

## Scientific definitions and safeguards

Values are read from the current analytics API, not substituted release constants.
Quality separates affiliation coverage, inferred-topic coverage, historical topic
precision, historical F1 and AI-assessed edge precision. Failed targets remain
visible. Wilson intervals describe sample uncertainty, excluding evaluator error;
independent human validation is not established.

Topic deltas require observed first and last selected years and are percentage
points of fractional inferred-topic prevalence. Missing endpoints are omitted,
not zero-filled. Citation CDF divides cumulative bucket counts by that venue/year
cohort's paper count. Cohort context is retained. Outside-shortlist researcher
ranks are explicitly missing, never rank zero. Base/strict counts and shares use
separate units. Sector support retains canonical pairs and pair-paper units.
Co-publication does not establish contracts/employment or continuous partnership.
Connected components remain distinct from Louvain communities; bounded graph
previews are not complete communities, and identifiers may change by release.

## Chart interaction, motion and accessibility

ECharts loads when a chart approaches the viewport. Active instances are restricted
to intersecting charts plus a 200px margin and disposed outside it. Each mounted
card retains whether its entrance has played. Initial animations use 600ms cubic-out;
updates use 300ms. Reduced motion is observed live and disables animation. Resize
work is animation-frame coalesced; observers, frames and media listeners are cleaned
up. Filters update an existing visible instance. Captions, axis units, summaries,
precise tables and keyboard drilldown actions accompany the figures. Accessibility
is covered by targeted browser behavior, not a screen-reader certification.

## Graph label policy

Sigma camera ratio is inverse zoom. Bands use 0.72, 0.38 and 0.18 boundaries with
6% hysteresis. Fit view has zero routine labels; medium/close/detail budgets cap at
6/24/48 and are further limited by viewport area. Candidates must be visible;
focused neighbors and graph prominence determine priority. Four candidate label
positions reject overlap with existing label boxes, node disks and viewport edges.
There is no forced collision fallback. Existing hover overlay and inspector retain
identity when canvas text cannot fit. Sigma beforeRender handles camera changes
without React camera-frame rerenders. Selection, edge lanes, direction, neighborhood,
search, camera restore and themes retain their existing mechanisms.

## Performance evidence

Build sizes (decimal KB, same Vite toolchain):

| Chunk | Before min / gzip | After min / gzip |
| --- | ---: | ---: |
| Main | 540.11 / 144.40 | 293.39 / 85.41 |
| Analytics view | 576.22 / 191.63 | 46.39 / 14.14 |
| Deferred chart runtime | included above | 537.43 / 179.59 |
| Deferred graph renderer | included in main | 194.75 / 48.68 |

The analytics view size is not the total chart download: ECharts is deferred, not
removed. Its >500 KB warning remains visible. Dialogs/table load separately. A
built-app cold Analytics visit requested neither Sigma nor ECharts before scrolling
to charts. Existing cached analytics supports all figures without per-chart API calls.

One sequential workstation/software-WebGL profiling run, before the final small navigation/empty-state fixes, measured old production readiness
3307ms and local built preview 3081ms. Different origins and workload prevent a
causal speed claim. New dashboard's maximum active chart count was five over 20
section visits. GC heap was 4.77MB before, 11.73MB after visits, 9.30MB after leaving;
this is not long-run leak certification. Graph frame median/p95 were 33.3/50ms with
one 316.6ms maximum; old production was 16.7/50ms. This does not establish a graph
speed improvement. Label readability is the verified outcome. No Lighthouse,
physical-phone, sustained-load or cross-browser benchmark is claimed.

## Local verification

- `uv run pytest`: 530 passed, one existing skip.
- Relevant offline synthetic structural validation: passed; no release rebuild.
- TypeScript/Vite production build: passed; ECharts size warning retained.
- Pure Playwright contracts: six passed without database/browser services.
- Final expanded full Chromium suite: 36 passed (2.7m). Mobile brand-margin follow-up: build, two visual tests and ten dashboard tests passed. Unavailable quality values no longer imply target success; two final missing-data/saved-section-scroll tests passed.
- Four reviewed reduced-motion pixel baselines: analytics desktop/mobile and graph
  fit/close. Additional captures cover seven sections × four widths × two themes,
  graph projections, hover/selection and detailed temporal figures.
- A missing-quality test initially intercepted the wrong summary URL; corrected interception of `/api/graph/summary` passed. Saved section restoration while already on Analytics now scrolls correctly and has a UI regression test.
- Initial stale backend/CORS attempts failed; isolated API8001/UI5174 with same-origin
  proxy fixed the test environment without disturbing existing8000/5173 services.
- Design heuristic lint reports 81 failures/16 warnings, largely existing UI borders,
  scientific identifier monospace and a `shadow` prose match. This is not an application
  lint pass; no project lint script exists. Inspector initially flagged the phone brand margin, corrected and rechecked at390px (zero failures/two warnings). Compact secondary text/card heuristics remain. Visual review and behavioral checks are the
  acceptance evidence; no blanket design-tool certification is claimed.

Raw logs, API snapshots, screenshots and measurement JSON are ignored under
`reports/runs/WORK-2026-11-11-001/`. Reviewed pixel baselines are tracked with tests.

## Production verification

Implementation commit: `7fd73d0379e466212317dc6518990ba99268a87e`, pushed to `main`.
Cloudflare deployment `458f1a1c-c6ca-4798-8a1c-322f783b2858` succeeded at
01:13:08 +07:00, with matching Git source. Immutable URL:
https://458f1a1c.scientific-network-explorer.pages.dev . Public URL:
https://scientific-network-explorer.pages.dev .

- GitHub [frontend checks](https://github.com/HSandz/scientific-network/actions/runs/42872384443)
  and [offline checks](https://github.com/HSandz/scientific-network/actions/runs/42872384459): success.
- Five production Chromium suites: passed (45.5s), including search, evidence,
  table, paths, comparison, neighborhood, responsive inspectors and theme persistence.
- Additional public UI-only browser checks: all seven sections at1440×900,
  1024×768,768×1024 and390×844 in both themes; no document overflow. Saved
  Analytics venue/section/scroll restored after reload and navigation elsewhere.
  Live reduced motion passed. All four projections passed overview/close zoom-band
  checks in both themes, with mobile fit captures. 88 screenshots captured;
  representative desktop robustness, mobile topics and graph screenshots reviewed.
  No page or console errors. Local geometry tests supply the stronger collision
  and hovered/selected-node assertions; production tests also exercise inspectors.
- Public API smoke:28 checks passed, including complete graph-bound analytics.
  Summary and analytics JSON compare exactly equal to pre-change snapshots.
- Azure API and Neo4j IDs, start times and mount descriptors compare byte-for-byte
  equal before/after. No Azure deployment workflow ran for this frontend commit.
  Database, frozen release identities and scientific artifacts remain untouched.

A documentation-only follow-up records this receipt with identical frontend source;
no remaining application deployment step. No backend contract changes were needed.

## Remaining limitations

1. Deferred ECharts runtime still exceeds500KB; further library reduction needs
   profiling and equivalent chart capability validation.
2. Long-session memory/scroll performance, physical devices, Firefox/Safari and
   formal screen-reader/contrast certification remain unmeasured.
3. Exact tables are intentionally expandable and potentially long. Secondary labels
   use compact typography; organization names truncate in plots with full table values.
4. Data/evaluation limitations are preserved; this release makes no new scientific claims.
