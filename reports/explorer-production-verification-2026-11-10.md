# Explorer production verification — 10 November 2026

WORK-2026-11-10-013. User authorized commit/push and deployment verification after
reviewing the [local integration and coordinated release plan](explorer-final-integration-2026-11-10.md).
This receipt supersedes that report's deployment-pending statements; its scientific
limitations and frozen data bindings remain unchanged.

## Release and recovery

- Pushed the reviewed implementation plus initial release journal as
  `d4dcf2af14ef070b7f96b93d1911b78c75606f04`.
- Caddy-only recreation applies `init: true`; API/Neo4j container IDs/start times
  were unchanged by recovery. The trusted HTTPS probe and PID limit remain.
  Root-owned backup: `/opt/scientific-network/ops/azure/backups/explorer-20261110-013`.
- Installed reviewed root-owned CI scripts against the existing contract/manifest
  approval before code activation. Azure [push run 42849498240](https://github.com/HSandz/scientific-network/actions/runs/42849498240)
  and [Offline run 42849498206](https://github.com/HSandz/scientific-network/actions/runs/42849498206) passed.
- Staged the new unused immutable directory
  `/opt/scientific-network/artifacts/explorer-20261110-v2`, verified every output
  hash and graph binding, then set root ownership/read-only permissions.
- After code activation, `scripts/update.sh` switched only API to that directory.
  Approval manifest pin changed **after successful verification**; runtime contract
  remained unchanged. Azure [repeat run 42850337433](https://github.com/HSandz/scientific-network/actions/runs/42850337433)
  passed as an idempotent no-op, preserving the active image and refreshing the
  receipt's artifact path to the new directory.
- Live UI review found Save only accessible from Graph's sidebar. A frontend-only
  follow-up `987c693b631bc529eac229ccf711812718df69f2` adds global workspace
  Save/Restore. Regression tests now click those actual controls for all tabs.
  It intentionally does not deploy another API image: backend source is unchanged.

Frontend follow-up Pages deployment `d020337d-4e9a-42dc-82da-6d45ededca77`
successfully serves `987c693`. Its Offline run 42850930716 passed. Public UI-only
save → reload → restore checks passed for Graph, Table and Analytics with zero
browser errors. The five public suites passed again on this frontend. Subsequent
documentation-only commits may update Pages source metadata without changing code.

## Independently checked production behavior

- `python ops/azure/scripts/smoke-api.py --base-url https://scientific-network-api.eastasia.cloudapp.azure.com/api --require-explorer-analytics`: 28 checks pass plus graph-bound derived/strict assertions, repeated after API restart.
- Public `explorer_derived` is present, with ten citation cohorts, organization
  persistence and both complete strict projection summaries. Cross-origin browser
  access from the canonical Pages origin returned HTTP 200 with those fields.
- Live accepted-support checks discriminate 2021 AAAI from 2025 IJCAI in both
  collaboration projections. Every returned in-window support ID satisfies the
  requested paper window; distinct counts match; full-period weights are labeled.
  Three actual supporting node metadata records per window were also checked.
- Five Chromium public E2E suites passed against the deployed site: four projections,
  searches/expansion, edge evidence, Table, Analytics, Paths, Compare and responsive
  navigation. Separate live visual capture produced 32 images across four modes,
  five analytical sections, responsive widths, both themes and reduced motion:
  zero unexpected page/console errors, alerts or horizontal overflow. Desktop
  robustness screenshot was manually inspected and shows measured strict results.
- API restart recovery passed without changing its container ID. Post-restart
  mounted-artifact integrity, graph inventory and all smoke checks passed. Neo4j
  container ID, mounts and original start time match the pre-release backup.
- Caddy remains healthy with docker-init PID 1; no `ssl_client` processes remain
  after repeated probe intervals. All three containers are healthy, without OOM.

## Local regression verification for the frontend follow-up

`npm --prefix apps/research-explorer/frontend run build` passed (public API base
configured; existing bundle warnings). `uv run pytest`: 530 passed, one existing
empty-parameter skip. `npm --prefix apps/research-explorer/frontend run test:e2e`
with isolated local base: all 22 passed. The three save/reload tests also passed
separately using actual global menu controls. Offline synthetic validation and
`git diff --check` passed. No scientific graph, model or frozen results changed.

## Evidence and rollback

[Machine-readable deployment receipt](explorer-production-verification-2026-11-10.json)
pins actual image/configuration identities, artifact hashes, services and verification.
Raw ignored logs/scripts/screenshots are under `reports/runs/WORK-2026-11-10-013/`:
`azure-push.log`, `azure-idempotent.log`, `artifact-activation.log`,
`public-analytics.log`, `public-post-restart.log`, `public-e2e.log`,
`public-filters.json`, `public-visuals/`, `restart-and-preservation.json`,
`menu-e2e.log`, `public-final-e2e.log`, `public-bookmarks.json` and `bookmark-*.png`.
An initial public-bookmark harness incorrectly used selectOption on a numeric
input; it was corrected to fill and rerun successfully. An initial receipt reader
assumed Docker always returns Init; optional-field handling was corrected. Neither
diagnostic error was treated as application failure or a passing check.

For analytics-only rollback use
`sudo scripts/rollback.sh .env.rollback-20261110T160011Z-z7zXU2` from VM ops;
this retains the new API code with the old artifacts (optional charts unavailable).
For the original API/old artifacts use
`sudo scripts/rollback.sh .env.rollback-20261110T155818Z-2O1Opg`.
Restore the matching approval manifest pin from the root-only backup under the
maintenance lock and independently verify public health/identity. Keep Caddy's init
fix in both cases. No Neo4j restore or volume change. Rollback mechanics were
fault-tested in isolation in WORK-012; no intentional failure or rollback was
injected into healthy production. Pages rollback is separate.

Bounded slices/previews, full-period Paths/comparisons, unsupported narrowed
heterogeneous presets, dense labels/mobile text and absence of sustained load,
cross-browser or WCAG certification remain. Short successful probe observation
does not establish a long-duration leak benchmark. Scientific quality caveats and
historical failed gates remain explicit; this release does not improve their scores.
