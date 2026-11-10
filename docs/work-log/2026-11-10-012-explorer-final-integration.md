# WORK-2026-11-10-012 — Explorer final integration

| Field | Value |
| --- | --- |
| Status | in_progress |
| Recorded | 2026-11-10 22:15 +07:00 (Asia/Bangkok) |
| Contributor | Codex |
| Git state | Clean main 4a432d60fe7a1a012029de86b7ce06e66b358ca2; remote HEAD matches |

## Objective

Fix deployment health, scientific filter correctness and saved views; prepare an
immutable matching runtime package and verify locally. No push, deployment,
active-artifact replacement or disruptive VM action is authorized.

## Findings and checkpoint

Read-only SSH and complete Actions run 42838707362 logs confirm activation
failed at stable_services before image delivery/update; missing receipt is a
consequence. Caddy health exec fails with procReady not received, despite public
HTTPS health passing and exact frozen inventory. Container has 96 tasks against
pids_limit 100, eight live Caddy threads and 88 orphaned zombie ssl_client
children; no init/reaper. Existing HTTPS BusyBox wget probe creates children.
API/Neo4j are healthy; active API/receipt remains b25f026, artifact azure-20261110-v1.
No VM mutation performed. Raw checks/logs: reports/runs/WORK-2026-11-10-012/.

## Verification

In progress; baseline locked environment sync passed. Tests and release plan
will be recorded before final handoff.

## Next step

Implement resource leak prevention without weakening HTTPS probe or deployment
health gate; fix paper-support filters/bookmarks and run full local verification.

## Implementation checkpoint — 2026-11-10 22:34 +07:00

Caddy Compose now enables init/reaping while retaining trusted HTTPS health and
PID limits. Isolated actual health probes reproduce 16 TLS zombies without init,
zero with init; local restart passes. Actual isolated Docker rollback restores
exact configuration after injected health failure; no graph mounts/volumes.

Accepted support-paper filtering now scopes R7/R8 overviews and bounded expansions;
distinct in-window IDs/counts are separate from unchanged full-period weights.
Unsupported dimensions return 422 and hidden projection controls clear/migrate.
Constrained expansion, complete pre-truncation comparison sets and source previews,
workspace/analytical section/control restoration, legacy bookmarks, finding-return
state and CSV provenance are implemented. Frozen artifacts remain untouched.

Latest checks: 529 repository tests pass / 1 existing skip; 32 backend tests pass
with live read-only Neo4j; 22 Chromium E2E pass; TypeScript/Vite build passes.
Compact SQLite runtime passes 28 HTTP checks plus required strict/derived checks.
Initial CORS test-harness error, stale contract expectation and newly detected
finding-return control reset are retained in raw logs; fixes rerun successfully.
Production-build visual/functional checks and final release handoff are ongoing.


## Operations checkpoint — 2026-11-10 22:38 +07:00

Built amd64 API image at application commit 75f55e2; portable configuration digest
`sha256:de96a5348902e16c6cf818d9b978fd7d08612cef3bb98635cdc92acea5347664`.
Real production-mode container with immutable SQLite artifacts and existing local
Neo4j passed all 28 smoke checks plus strict/extension assertions and restart
readiness; the no-network/missing-artifact image smoke correctly rejects readiness.
Production-build preview: 5 E2E suites pass; 32 screenshot capture checks report
zero page/console errors, alerts or horizontal overflow. Graph and chart contact
sheets inspected in both themes, including mobile. Small phone text/dense labels
remain limits, not a WCAG/performance certification.

Coordinated artifact changes with an unchanged image could leave the idempotent
CI receipt's artifact directory stale. The no-op branch now refreshes the verified
active artifact path/service identities; a fault-isolated regression covers it.
