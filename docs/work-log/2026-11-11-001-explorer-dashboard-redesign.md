# WORK-2026-11-11-001 — Explorer dashboard and graph readability

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-11 00:18 +07:00 (Asia/Bangkok) |
| Finalized | 2026-11-11 01:15 +07:00 |
| Contributor | Codex |
| Related task | WORK-2026-11-10-013 |
| Initial Git state | Clean main acfb3c6, matching remote |
| Implementation | 7fd73d0379e466212317dc6518990ba99268a87e |

## Objective and changes

Implemented the authorized Explorer UI redesign without changing graph semantics,
backend, artifacts or infrastructure. Seven scrolling sections replace exclusive
reports. Added API-backed quality, rank, temporal, persistence and cohort figures;
exact tables/evidence actions retained. Lazy chart/graph/dialog modules,600ms
entrance/300ms updates, live reduced motion and bounded chart instances improve
presentation. Zoom-dependent labels use inverse ratio, hysteresis, area budgets
and collision rejection. Hover/selection inspection remains available. Fixed axis
clipping, citation inventory wording, phone controls/brand margin, unavailable
quality targets and saved-section scrolling. D040 presentation amendment recorded.

## Checks and measured outcomes

- `uv run pytest`:530 passed/one existing skip (exit0).
- Relevant synthetic structural CLI validation:passed (exit0), no release rebuild.
- `npm --prefix apps/research-explorer/frontend run build`:TypeScript/Vite passed.
- `(cd apps/research-explorer/frontend && npx playwright test -c playwright.contracts.config.ts)`:six passed.
- `PLAYWRIGHT_API_PORT=8001 PLAYWRIGHT_UI_PORT=5174 npm --prefix apps/research-explorer/frontend run test:e2e`:36 passed before small follow-ups.
- Margin follow-up:ten dashboard/two visual tests passed. Final missing-quality and
  saved-section-scroll checks:two passed. No configured application lint script.
- Main minified/gzip540.11/144.40 →293.39/85.41KB; deferred ECharts537.43KB
  warning retained. Scroll profiling:maximum five active chart instances; heap/frame
  samples are limited workstation measurements, not performance certification.
- `PLAYWRIGHT_BASE_URL=https://scientific-network-explorer.pages.dev ... run test:e2e -- tests/explorer.spec.ts`:five passed against production.
- Public UI-only screenshot/check script:18 assertions passed,88 captures, no
  browser errors. Representative desktop/mobile/graph figures visually reviewed.
- `python ops/azure/scripts/smoke-api.py --base-url https://scientific-network-api.eastasia.cloudapp.azure.com/api --require-explorer-analytics`:28 passed.
- `cmp` before/after Azure API/Neo4j IDs/start/mount descriptors:equal. Public
  summary/analytics JSON equality assertions:passed. No Azure workflow triggered.

## Delivery and evidence

Authorized push of implementation to main; GitHub frontend/offline checks passed.
Pages458f1a1c-c6ca-4798-8a1c-322f783b2858 deployed matching source successfully.
Production:https://scientific-network-explorer.pages.dev . Full definitions,
files, checks, CI links and deployment receipt:
[verification report](../../reports/explorer-ui-redesign-verification-2026-11-11.md).
Raw logs/snapshots/screenshots:`reports/runs/WORK-2026-11-11-001/` (ignored).
Four reproducible pixel baselines tracked under frontend tests.

## Failures, limitations and next step

Initial stale-service/CORS failures resolved with isolated ports/same-origin proxy.
Two graph tests originally zoomed empty space; tests now center real nodes.
Missing-quality test initially intercepted the wrong summary route; corrected and
passed. Heuristic style lint reports existing UI borders/identifier monospace and
other findings, not a certified style pass; mobile inspector margin failure fixed.
Long-run memory/load, physical phones, Firefox/Safari and formal accessibility
certification remain unmeasured. ECharts chunk reduction remains a profiling task.
Scientific limitations/failed criteria remain visible. No new scientific claims.
Next:course-specific facts/submission and optional cross-browser/device profiling.
