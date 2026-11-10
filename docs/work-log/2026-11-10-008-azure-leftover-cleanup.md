# WORK-2026-11-10-008 — Azure deployment leftover cleanup

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-10 16:28 +07:00 (Asia/Bangkok) |
| Work performed | 10 November 2026 |
| Contributor | Codex |
| Related task | User-authorized cleanup following WORK-007 |
| Git state | Clean `main` at `1deff77`, synchronized with origin at start |

## Objective

Remove the specifically identified unused Azure deployment leftovers while
preserving the active graph, services, backups and known-good rollback settings.

## Changes and findings

- Removed `scientific-network-production-neo4j-data-v1`, unreferenced API images
  `azure-20261110-v1`/`v2`, `.env.rollback-20261110T074414Z` and
  `.env.rollback-20261110T074656Z`, duplicate `/opt/scientific-network/bootstrap-vm.sh`
  and empty `/opt/scientific-network/secrets/`.
- Cleanup held `.runtime.lock` and checked all container references, active v3
  settings, the v2 restore marker and duplicate script hash before deletion.
  No broad prune or forced deletion. Recovered 2,278,842,368 bytes (2.12 GiB);
  approximately 19 GiB free. Docker reports zero reclaimable images/volumes.
- Both database dumps, active env, known-good v3 env, restore marker and artifact
  manifest hashes were unchanged; cleanup preserved container IDs/images/mounts.
  Active data-v2, logs-v1 and Caddy state volumes retained. Local source and former
  Render/Aura resources were untouched.
- Inspection found Caddy unhealthy before cleanup: 96 tasks near its 100 PID
  limit, with health-check exec failures (`procReady not received`). Public API
  functionality still passed. Added `GOMAXPROCS=2` in production Compose and
  recreated only Caddy under the maintenance lock: nine tasks, healthy again.
  Existing CPU/memory/PID limits retained; API/Neo4j were not restarted.
- Updated the [runbook](../../ops/azure/README.md), status/index and an additive
  [deployment receipt follow-up](../../reports/release-v4/azure-deployment-2026-11-10.md).

## Verification

| Command/check | Outcome and exit code | Evidence |
| --- | --- | --- |
| Guarded SSH cleanup via noninteractive sudo | exit 0; all specified targets removed; protected file hashes unchanged | `cleanup.py`, `cleanup.log` |
| Compose `config --quiet`; Caddy-only `up --no-deps --no-build --wait` | exit 0; healthy, nine tasks; next scheduled health check also passed, zero failing streak | `caddy-recovery.log`, `caddy-health-final.json` |
| VM `scripts/verify.sh` | exit 0; readiness/health, expected graph counts, summary, analytics and all artifact hashes pass | `caddy-recovery.log` |
| Public `smoke-api.py --base-url https://scientific-network-api.eastasia.cloudapp.azure.com/api` before/after | exit 0 twice; 28 checks each, graph/evidence/path/analytics and safe invalid inputs | `public-smoke-before.jsonl`, `public-smoke-after.jsonl` |
| `scripts/status.sh`; `docker system df` | exit 0; three healthy services, all images/volumes active, 2.0 GiB RAM available, swap 28 KiB used | `status-after.log` |
| `uv sync --locked --group dev --extra analysis`; `uv run pytest` | exit 0; 502 passed, seven skips without optional report dependency | initial baseline |
| `uv sync --locked --group dev --extra analysis --extra report`; `uv run pytest -q` | exit 0; 508 passed, one existing skip | `pytest.log` |
| `uv run research-network schema`; `git diff --check` | exit 0 | `schema.cypher`, final diff |

Raw evidence is under ignored `reports/runs/WORK-2026-11-10-008/`.

## Decisions

None. User explicitly authorized deletion of the identified leftovers.

## Open issues and limitations

Initial direct Docker inspection lacked permission; repeated with the existing
noninteractive sudo path. No mutation occurred in that attempt. Browser suites,
full database fingerprints, reboot and long-duration stability were not rerun for
this cleanup; current API checks and artifact hashes passed. WORK-007 records the
historical full graph/browser acceptance. Periodic off-VM backup remains operational.

## Next step

Continue production observation and periodic off-VM backups; no further leftover
cleanup is required from this deployment.

## Corrections

None.
