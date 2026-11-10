# Azure API automatic deployment — 10 November 2026

Status: backend push/manual deployment and production acceptance passed;
documentation-only negative push pending.
Work: [WORK-2026-11-10-009](../../docs/work-log/2026-11-10-009-azure-api-cicd.md).
[Runbook](../../ops/azure/README.md).
[Workflow](https://github.com/HSandz/scientific-network/actions/workflows/deploy-azure-api.yml).

## Implementation and security

- Hosted Ubuntu amd64 builds from the exact triggering main SHA, locked dependencies,
  repository/backend tests, requirement-export equality, real image import/start smoke.
  Container smoke has no network/database/artifacts and verifies readiness stays 503.
- Immutable full-SHA image tag, portable SHA-256 configuration digest derived from
  docker-save (not Docker-store-specific inspect.Id), archive SHA-256, private
  one-day Actions artifacts. No public image or registry.
- Azure OIDC, free user-assigned managed identity, custom role assigned only on
  the existing VM: VM read, instance-view read and Run Command invocation.
  No SSH key/password/long-lived Azure secret; no deployment runner on production.
  Repository OIDC customization binds repository/environment/exact main workflow;
  production-api environment restricts branch to main without human approval.
- Run Command is root-equivalent inside this VM; trusted main workflow editors
  are production administrators. Main has no branch protection. The existing NSG
  already allows public SSH/HTTP/HTTPS; no firewall/login rule was changed.
- Global token permission contents:read; deploy adds actions:read and id-token:write.
  Production credentials never reach PR jobs. Actions use pinned supported Node24
  releases. Deployment scripts/policy on VM are operator-installed and root-owned.
- No GitHub Actions secrets created. Nonsecret production-api environment variable
  names: AZURE_API_CLIENT_ID, AZURE_API_TENANT_ID, AZURE_API_SUBSCRIPTION_ID,
  AZURE_API_VM_ID. Scientific secrets remain protected in the original VM env.
- Main-only push paths: backend/**, Dockerfile.api, requirements-api.txt,
  build-image.sh, runtime-contract.py, ci-image-smoke.sh, image-identity.py,
  pyproject.toml and uv.lock. Manual dispatch accepts trusted main only.
  Frontend/docs/data/Compose/restore/artifact-preparation paths do not trigger Azure.
- Serialized deployments, cancellation disabled, latest-main check plus VM sequence
  watermark. API-only --no-deps/--no-build/--pull never update and rollback.
  No Neo4j/Caddy recreation, graph load/dump, volume removal or data transfer.
- Root approval pins existing artifact manifest and release constants/JSON/SQLite
  readers. Contract changes need coordinated operator approval, not a CI edit.
  Scientific data and SQLite stay in the same versioned read-only mounted directory.

## Checks and real runs

| Check | Result |
| --- | --- |
| Local repository suite | 524 passed, one existing empty-parametrization skip |
| Offline backend production/unit suite | 13 passed |
| Shell transaction / path policy / hosted recovery / portable identity tests | 16 passed |
| Workflow validator | actionlint 1.7.12 passed; YAML filters checked with real configuration |
| Initial hosted checks | Previous checks failed for missing matplotlib; install locked analysis/report extras; repaired checks pass |
| Initial automatic run 42793772100 | Failed safely before activation: Docker inspect identity differs across stores |
| Initial manual run 42793793606 | Same guard failed safely before activation; original API retained |
| Corrected automatic run [42794633050](https://github.com/HSandz/scientific-network/actions/runs/42794633050) | Success; a6fc512 activated and VM/hosted public smoke passed |
| Corrected manual run [42794687317](https://github.com/HSandz/scientific-network/actions/runs/42794687317) | Success; verified idempotent no-op, existing image/API container retained |
| Real VM Docker rollback fault | Passed in isolated 64 MiB network-none Compose project; unhealthy replacement rolled back exact env and verified service; no scientific mounts/volumes |
| Offline negative tests | Frontend/docs/scientific-data/operations paths excluded; PR events absent; main/event/job gates enforced; stale recovery refused; critical rollback failure exits 70 |
| Production frontend browser | Real Pages UI renders release; actual Azure requests and browser CORS health fetch return 200 with expected graph inventory |

## Final production acceptance

- Automatic backend push: [42795556553](https://github.com/HSandz/scientific-network/actions/runs/42795556553), **success**.
- Manual dispatch: [42795640673](https://github.com/HSandz/scientific-network/actions/runs/42795640673), **success**, verified no-op.
- Existing Offline checks: [42795556832](https://github.com/HSandz/scientific-network/actions/runs/42795556832), **success**.
- Deployed commit: `b25f0267bfab7147e0491d591cf4f4a3ab083c2f`.
- Image: `scientific-network-api:sha-b25f0267bfab7147e0491d591cf4f4a3ab083c2f`.
- Portable image configuration digest: `sha256:59c983a7128d15c8572b8fdcc50727d4b6e50f817614583ccc9a9350decf6481`.
- VM image-store manifest digest: `sha256:30de654e0e36532ecd21367a8843973f91a0044c98d1c6779b3c4889d52ef998`.
- API started **2026-11-10 17:03:44.496 +07:00**; deployment verified
  **17:03:55.968 +07:00**; manual rerun retained the same API container/image.
- API container `1c92592629707aaf017492a30b20ec43a46d49646851f89e33679f0412a561ee`.
  Neo4j `3aad86b5b0d5293022eca9f902a5fef57a31c54d561c43d9c6432f7eed6841a4`
  and Caddy `040d7714d45cf278f9e22bcc20d783518d0263eac15659cc25a7e6312408dad2`
  retain their original IDs, image IDs, start times, restart counts and mounts.
- All three containers healthy, zero restarts/OOMs. API 132.3 MiB; Neo4j 992.6 MiB;
  Caddy 17.65 MiB. VM about 2 GiB RAM available, 28 KiB swap used of 4 GiB,
  18 GiB disk free (36% used). No VM image build or resource resize.
- Same artifact directory `/opt/scientific-network/artifacts/azure-20261110-v1`,
  read-only mount; manifest SHA-256
  `958be6e9493eb6b0255ad36939a96fb901dd7bd7e64cdb9634649139a105ef0f`.
  All artifact hashes pass; original graph/data, env secrets and backups retained.
- Fresh complete before/after scientific inventory comparison: **zero differences**
  across all 15 compared fields (typed-property fingerprints, IDs, labels, directions,
  counts, versions, samples, constraints and indexes). Nodes stream SHA-256
  `640d30984212dcde382ace154e19b275f9ccc0a24ac164f56a9872e3d476eea1`;
  relationships stream SHA-256
  `fd01fa8837824c5a207eb339d855e616acfad626a81b813c0256701fef2c2936`.
  Graph remains **47,875 nodes / 225,731 relationships / release-d3c788c3114a**.
- Final independent public `smoke-api.py`: **28 passed** in 9.853 seconds, including
  live/ready/verified health, summary, search, entity/edge details, neighborhoods,
  paths, provenance, aligned affiliation observations, analytics and invalid input.
- Final standalone Chromium: actual production UI graph canvas rendered; summary,
  researcher view and browser CORS health requests to Azure returned **200**;
  zero page errors. One MCP evaluation stalled; standalone Chromium retry passed.
- Current rollback snapshot: `.env.rollback-20261110T100342Z-CJCmcZ`;
  it restores the preceding a6fc512 image with the same artifacts. Retained on VM.

Documentation-only finalization push is a separate negative trigger test; its
observed run list will be recorded in the closing work entry after the push.

## Operations and limitations

Normal backend deployment is git commit/push to main. Manual redeployment uses
Actions Run workflow/main or gh workflow run deploy-azure-api.yml --ref main.
Manual rollback: on VM, cd /opt/scientific-network/ops/azure, then
sudo scripts/rollback.sh .env.rollback-<exact-snapshot-filename>.
See runbook for a separately approved graph/artifact release; CI never does one.
Disable automation with gh workflow disable deploy-azure-api.yml; Pages is untouched.

Account-wide billing/minute/storage quota is not visible to the available GitHub
credential (billing endpoints require user scope); per-run timing/artifact sizes
were inspected. Image packages are approximately 87 MB and expire after one day.
Removed only the two failed runs' CI packages (174,657,126 bytes) after recording
identity/failure evidence, reducing temporary storage. No paid quota was enabled.
Existing pre-task VM images, artifacts and backups are retained.

Frontend-only/PR negative cases use isolated workflow-policy tests, not extra live
frontend pushes/PRs; no Pages configuration or manual deployment call was changed by this task; existing
Git integration remains active.
Hosted-only public-smoke recovery is covered by offline failure tests; real Docker
health failure/rollback was tested in isolation. No deliberate live outage,
production DB fault, VM reboot or long-duration stability test was performed.
Raw outputs are ignored under reports/runs/WORK-2026-11-10-009/.
