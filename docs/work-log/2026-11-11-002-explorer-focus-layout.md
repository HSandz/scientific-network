# WORK-2026-11-11-002 — Explorer focus labels and analytical layouts

| Field | Value |
| --- | --- |
| Status | in_progress — local checkpoint, production delivery next |
| Recorded | 2026-11-11 11:36 +07:00 (Asia/Bangkok) |
| Checkpoint | 2026-11-11 12:07 +07:00 |
| Contributor | Codex |
| Initial Git state | Clean main, 5e4da480dbdb |

## Objective and changes

Fix canvas neighborhood identification and unequal-height Analytics layouts;
verify responsive interactions and authorized frontend production delivery.
Independent focus budgets, bounded collision-aware canvas placement, hover/edge
precedence and Sigma same-node re-entry now identify neighbors at overview.
Section layouts, compact bridge ranks/full linked table, selected partnership
support, stable persistence cell IDs and escaped full-name tooltips replace the
long mixed-height rows. Sticky mobile navigation keeps its active section visible.
No API, database, scientific artifacts, dependencies or infrastructure edits.

## Findings and evidence

Before captures reproduce absent neighbor labels in all projections. Baseline card
heights: robustness691/1,568px; sectors498/1,996px. Source and screenshots exposed
Sigma normalization timing and stale internal hover ID; corrected using public
callbacks and viewport geometry. Reviewed canvas/desktop/phone/both-theme images;
new snapshot baselines retain exact data and disclose unlabeled neighbors.
Graph baseline refresh also reflects pre-existing bounded API preview drift,
108/170 to110/166 nodes/edges, observed before edits; no frozen graph change.

## Checks and outcomes

- Locked environment with analysis/report extras; `uv run pytest`:530 pass,one existing skip.
- Frontend TypeScript/Vite build:pass;7 pure contracts pass.
- Focus6 /layout7 /visual3 focused Chromium tests pass; full consolidated suite52 pass.
- Backend suite:23 pass,9 local-Neo4j integrations skipped,one warning.
- Offline schema/fixture structural validation pass; synthetic is ineligible for accuracy.
- Before API smoke28 pass; Azure container IDs/start/mounts and graph JSON captured.
- Initial full suite50 pass/2 fail: ignored local proxy lost POST methods/bodies.
  Corrected proxy; no application/assertion changes; consolidated rerun52 pass.
- Hover median/p95:4.4/8.2ms;placement0.2/0.6ms;zero focus API calls.
  Pan/zoom p95:36.8ms;workstation outliers preclude60fps claims.

Exact commands, screenshots, before/after performance and scientific boundaries:
[verification report](../../reports/explorer-focus-layout-verification-2026-11-11.md).
Raw artifacts: `reports/runs/WORK-2026-11-11-002/` (ignored).

## Decisions and limitations

D040 presentation amendment recorded; graph/API semantics unchanged. Browser tests
use a local read-only HTTP proxy to production because local Bolt is unavailable.
No DB was started. ECharts537KB warning remains. Physical devices,Firefox/Safari,
formal screen-reader and long-session memory certification remain untested.

## Next step

Commit/push authorized frontend checkpoint, verify exact-SHA
Pages production and public browser/API behavior, then finalize this record.
