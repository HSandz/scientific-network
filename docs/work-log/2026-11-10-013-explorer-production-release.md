# WORK-2026-11-10-013 — Explorer production release

| Field | Value |
| --- | --- |
| Status | completed |
| Started / finalized | 2026-11-10 22:55 / 23:09 +07:00 (Asia/Bangkok) |
| Contributor | Codex |
| Related task | WORK-2026-11-10-012 |
| Initial Git | Clean main 6386e3f, four local commits; remote 4a432d6 |

## Objective and authorization

User authorized commit/push and deployment verification after reviewing the local
release handoff. Execute reviewed recovery and coordinated artifact activation;
preserve the frozen graph and all database volumes. Initial in_progress and
23:04 checkpoint entries are preserved in d4dcf2a/987c693 history.

## Changes and findings

Recovered Caddy with reviewed init-enabled Compose and Caddy-only recreation;
API/Neo4j identity/start unchanged. Backed up root-only runtime selectors, approval,
Compose and scripts. Installed reviewed CI scripts; staged/verified new immutable
explorer-20261110-v2 package. Pushed d4dcf2a, verified automated API activation,
then switched artifacts transactionally and updated the approval manifest pin
only after successful checks. Contract unchanged. Second workflow verified a
no-op with accurate new artifact identity. No graph import/model/data changes.

Live review found Save controls only exposed in Graph despite correct restoration.
Added global workspace Save/Restore and changed regressions to click real controls;
frontend-only 987c693 pushed/deployed, with unchanged API code. Actual public
Graph/Table/Analytics save/reload/restore now passes. Roadmap/status updated;
[production report and exact rollback](../../reports/explorer-production-verification-2026-11-10.md),
[machine-readable identities](../../reports/explorer-production-verification-2026-11-10.json).

## Verification and evidence

- Locked environment sync passed; `uv run pytest` rerun after follow-up: 530 pass / 1 existing empty-parameter skip.
- Public API Azure push run 42849498240 and idempotent run 42850337433 passed. Offline runs 42849498206/42850930716 passed.
- `npm --prefix apps/research-explorer/frontend run build` with public API base: passed, existing chunk warnings; local `run test:e2e`: 22 passed, three actual-menu restoration tests also pass separately.
- Public `run test:e2e -- tests/explorer.spec.ts`: five pass before and after follow-up. UI-only public bookmark checks: all three workspaces pass, zero errors.
- `python ops/azure/scripts/smoke-api.py --base-url https://scientific-network-api.eastasia.cloudapp.azure.com/api --require-explorer-analytics`: 28 checks plus complete strict/derived assertions pass, repeated after restart.
- Four public collaboration year/venue windows discriminate and all support IDs/counts agree; 12 supporting node metadata records checked. Full-period metrics labeled.
- API restart ready/verification passes; Neo4j ID/mounts/original start preserved. Caddy healthy with init and no TLS helper processes over repeated intervals; all containers healthy/no OOM.
- 32 live visual captures: no unexpected browser errors/alerts/overflow; real strict-result chart and restored Table captures inspected. Offline synthetic validation and diff whitespace check pass.

Ignored logs/scripts/screenshots: reports/runs/WORK-2026-11-10-013/. Initial bookmark
harness used selectOption on a numeric input; corrected to fill and passed. Initial
receipt diagnostic assumed optional Docker Init key; corrected and passed. Neither
was hidden or counted as a successful initial check. Earlier WORK-012 results are
historical except checks explicitly rerun above.

## Limitations and next step

Rollback fault injection was isolated in WORK-012; healthy production was not
intentionally broken/rolled back. Short probe observation is not a sustained leak
benchmark. Bounded/full-period scope, unsupported preset, mobile density and
performance/accessibility limitations remain; scientific failed gates unchanged.
Next: observe normal production usage and complete personal/course delivery facts.
