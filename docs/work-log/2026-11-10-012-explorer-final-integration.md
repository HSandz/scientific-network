# WORK-2026-11-10-012 — Explorer final integration

| Field | Value |
| --- | --- |
| Status | completed locally; production release awaits authorization |
| Started / finalized | 2026-11-10 22:15 / 22:49 +07:00 (Asia/Bangkok) |
| Contributor | Codex |
| Initial Git | Clean main 4a432d6; remote matched; no user edits |

## Objective and boundary

Implement deployment-health, scientific-filter, workspace and exploration fixes;
prepare immutable artifacts and verify. No push, deployment, active-artifact
replacement, database change or disruptive VM action authorized/performed.
Initial in_progress checkpoint recorded before implementation; checkpoints at
22:34, 22:38 and 22:44 +07:00 are preserved in local commit history.

## Findings and changes

Full Actions 42838707362 logs/read-only SSH show Caddy health exec fails before
activation: 88 orphaned ssl_client zombies plus eight threads approach PID cap
100, while public HTTPS remains healthy. BusyBox TLS probe helpers lack a reaper.
Compose adds init without weakening probe/cap. Last healthy API was preserved.
Actual local probe reproduction: 16 zombies without init, zero with init;
restart passes. Real isolated Docker failed-health update restores exact config.

Accepted distinct core-paper support now scopes collaboration views/expansions;
in-window IDs/counts remain separate from full-period weights/metrics. Unknown or
unsupported filters reject; hidden controls migrate with disclosure. Complete
comparison totals precede bounded previews, with R8-backed organization papers.
Graph/Table/Analytics bookmarks restore layout/scope/selection and workspace
controls, including Table query/sort/page. Finding return preserves analytical
controls. Exports preserve provenance. Idempotent CI receipts refresh artifact
identity after coordinated switching. Frozen release/config/results untouched.
Material semantics and Table persistence recorded in decisions; capabilities in
roadmap; app/Azure runbooks updated. [Detailed report and approved-release procedure](../../reports/explorer-final-integration-2026-11-10.md).

## Checks and exact outcomes

- `uv sync --locked --group dev --extra analysis --extra report`: passed.
- `uv run pytest`: 530 passed, 1 existing empty-parameter skip.
- `PYTHONPATH=apps/research-explorer:src uv run pytest apps/research-explorer/backend/tests -q`: 32 passed, live read-only Neo4j included.
- `npm --prefix apps/research-explorer/frontend run build` with local API base: passed; chunk warnings remain.
- `npm --prefix apps/research-explorer/frontend run test:e2e` with base5174: 22 passed; production preview base4174 `-- tests/explorer.spec.ts`: 5 passed.
- Packaged real API container: 28 smoke checks plus strict/derived assertions, restart readiness; no-data/network image correctly fails readiness. Deployment regressions: 19 passed.
- Offline schema/synthetic validation, package output/source hashes and `git diff --check`: passed. Frozen-path diff empty; remote still 4a432d6 at final check.
- 32 production-build visual captures inspected across four projections/five sections, responsive widths, themes/reduced motion; zero unexpected browser errors/alerts/overflow.

Raw logs/screenshots: ignored `reports/runs/WORK-2026-11-10-012/` (see report).
Earlier CORS/contract/finding-state failures were fixed and rerun. Two intermittent
Table-follow-up browser failures passed diagnosis and final full rerun; cause not
proven. Failed probe diagnostics/logs remain retained, not counted as successes.

## Artifacts, limitations and next step

[Readiness JSON](../../reports/explorer-runtime-readiness-2026-11-10.json) pins new
unused runtime-explorer-v2 package hashes, graph binding and tested API image.
Code checkpoints: 75f55e2, 78485e8, a26dce5; final handoff commit adds this outcome.
Production remains Pages4a432d6/APIb25f026 with old artifacts and unrepaired Caddy
probe; live activation/recovery/rollback unverified. Bounded candidates/previews,
full-period Paths/comparisons, unsupported heterogeneous combinations, dense mobile
text and missing sustained load/accessibility certification are explicit limits.
Next: user-authorized Caddy-only recovery, approved source push and coordinated
immutable artifact switch, then independent live browser/API/health acceptance.
