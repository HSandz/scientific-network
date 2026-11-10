# WORK-2026-11-10-009 — Automatic Azure API deployment

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-10 17:12 +07:00 (Asia/Bangkok) |
| Work performed | 10 November 2026, 16:36–17:12 +07:00 |
| Contributor | Codex |
| Related task | User-requested backend CI/CD; WORK-007 and WORK-008 |
| Git state | Clean main at 191c0b3 initially, origin agreed; implementation da26a3d/a6fc512/b25f026 and acceptance c7be9f2 pushed without force |

## Objective

Automatically test/build private backend images on hosted runners, securely deploy
to the existing Azure Compose, preserve scientific data and verify recovery.

## Changes and findings

- [Workflow](../../.github/workflows/deploy-azure-api.yml): relevant main pushes and
  main-only manual dispatch; immutable image tag/config digest and checksum,
  hosted image smoke, supported SHA-pinned actions, serialized/stale-safe delivery.
- Free managed identity/OIDC restricted to this repository, main-only production-api
  environment and exact workflow; custom Run Command role assigned on this VM only.
  No GitHub Actions secrets, personal key, production runner or firewall changes.
  Four nonsecret environment variable names and privileges are in the runbook.
- Root-owned delivery/policy reuses current read-only artifacts; fingerprints block
  changed release constants/JSON/SQLite readers. API-only guarded update restores
  exact prior env on readiness/hash/DB/public-smoke failure and verifies recovery.
  Hosted-only smoke failure also invokes transaction-bound recovery.
- Repaired pre-existing Offline checks failure by installing locked analysis/report
  extras (matplotlib was missing). Backend push test changes only its package docstring
  in application code. No graph, Dockerfile/Compose, lock or Pages setting changed.
- [Measured receipt](../../reports/release-v4/azure-api-cicd-2026-11-10.md) records
  identities, graph fingerprints, timings, resources, all runs and limitations.

## Verification

| Command/check | Outcome and exit code |
| --- | --- |
| `uv sync --locked --group dev --extra analysis --extra report`; `uv run pytest -q` | exit 0; baseline 508 passed/one skip, final 524 passed/one existing skip |
| Backend offline production/unit pytest | exit 0; 13 passed |
| Shell transaction, path/ref policy, hosted recovery, saved-config identity tests | exit 0; 16 passed |
| `uv run research-network validate --input tests/fixtures/synthetic_graph.json`; requirement export/diff; shell/Python checks | exit 0 |
| `actionlint` 1.7.12; `git diff --check` | passed, exit 0 |
| Actual automatic [42795556553](https://github.com/HSandz/scientific-network/actions/runs/42795556553) / manual [42795640673](https://github.com/HSandz/scientific-network/actions/runs/42795640673) | success; b25f026 activated; manual verified same image/container as no-op |
| Repaired [Offline checks](https://github.com/HSandz/scientific-network/actions/runs/42795556832) | success |
| Documentation-only c7be9f2 push | actual run list only [successful Offline checks](https://github.com/HSandz/scientific-network/actions/runs/42796792487); zero Azure runs |
| Final installed script, isolated VM real-Docker unhealthy replacement | exit 0; failed update restored exact env and verified synthetic HTTP service; no data/volumes/network |
| Public `smoke-api.py` | exit 0; final 28/28 in 9.853s, also VM/hosted checks passed |
| Standalone production Chromium | exit 0; graph canvas, Azure summary/view/health HTTP 200, CORS works, zero page errors |
| Full before/after DB/schema comparator and infrastructure identity comparison | exit 0; all 15 fields equal, complete typed-property hashes equal; DB/proxy IDs/start times/images/mounts/restarts unchanged |
| Resource/artifact verification | all services healthy, zero OOM/restarts, ~18 GiB disk free, ~2 GiB RAM available, 28 KiB swap; original artifact path/manifest/hash/read-only mount retained |

Raw evidence: ignored `reports/runs/WORK-2026-11-10-009/`.

## Decisions

[D040 backend delivery amendment](../decisions.md); [operations runbook](../../ops/azure/README.md).

## Open issues and limitations

Azure login first expired, then actual VM tenant required MFA; user completed both
local logins. Initial push/manual 42793772100/42793793606 failed safely before
activation because Docker stores report different inspect IDs. Fixed by hashing
saved configuration on both sides; corrected push/manual runs also passed.
One MCP browser evaluation stalled; independent Chromium retry passed. No failure
was counted as successful. Exact account billing quota is inaccessible with the
available GitHub scope; repo packages measured 349,296,803 bytes with one-day
retention. Deleted only failed-run CI packages (174,657,126 bytes), not VM images/data.
Main is unprotected and Run Command is VM-root-equivalent; existing public SSH rule
was observed and unchanged. Frontend/PR negative cases were isolated policy tests,
not live pushes/PRs. Hosted-only failure recovery has offline coverage; real Docker
health rollback was isolated, without deliberately breaking production. Reboot and
long-duration stability were not tested. No blocking deployment step remains.

## Next step

Push ordinary backend changes to main; use Actions logs for verification. Check
account billing usage separately, monitor disk and preserve known-good rollback
images/artifacts. New scientific releases require explicit coordinated approval.

## Corrections

None.
