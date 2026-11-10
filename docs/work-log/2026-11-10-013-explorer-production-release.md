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

## Checkpoint — 2026-11-10 23:04 +07:00

Pushed d4dcf2a; Offline run 42849498206 and Azure run 42849498240 passed.
Pages canonical deployment 341f6925-f26b-4ac6-be1b-2b153e4afa70 serves that source.
Coordinated immutable artifact activation passed all checks; rollback snapshot
`.env.rollback-20261110T160011Z-z7zXU2`. Manifest approval changed only after
activation, contract unchanged. Workflow 42850337433 passed as an idempotent
no-op and records actual explorer-20261110-v2 directory. Public API: 28 smoke
checks plus complete derived/strict assertions pass. Five public browser suites
and 32 visual captures passed; narrowed public windows discriminate correctly.

Live UI review found Save only exposed in Graph sidebar despite correct restoration.
Added Save/Restore to global workspace tools for all tabs; regressions now click
actual Save/Restore controls. Build, 530 repo tests/1 skip and all 22 local browser
tests pass after this follow-up. Frontend-only push follows; API code unchanged.
