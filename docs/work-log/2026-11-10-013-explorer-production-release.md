# WORK-2026-11-10-013 — Explorer production release

| Field | Value |
| --- | --- |
| Status | in_progress |
| Recorded | 2026-11-10 22:55 +07:00 (Asia/Bangkok) |
| Contributor | Codex |
| Related task | WORK-2026-11-10-012 |
| Git state | Clean main 6386e3f, four local commits; remote 4a432d6 |

## Objective

User authorized commit/push and deployment verification. Execute the reviewed
coordinated release, recover Caddy probe health and enable matching immutable
analytics without modifying the frozen graph or database volumes.

## Changes and findings

Initial read-only SSH confirms old API healthy, Neo4j healthy and Caddy unhealthy;
approval/receipt still pin old manifest/image. Separate new immutable package and
reviewed Caddy init recovery will precede code activation. Logs under ignored
reports/runs/WORK-2026-11-10-013/.

## Verification

New locked sync passed; new `uv run pytest`: 530 passed / 1 existing skip.
Caddy-only recreation is healthy; API/Neo4j IDs/start times unchanged. Root-only
backup: `/opt/scientific-network/ops/azure/backups/explorer-20261110-013`.
Prior frontend/backend test results are historical WORK-012 evidence.

## Next step

Back up root-owned runtime configuration, recover Caddy only, install reviewed CI
scripts, push approved source and verify live code/artifacts/browser behavior.
