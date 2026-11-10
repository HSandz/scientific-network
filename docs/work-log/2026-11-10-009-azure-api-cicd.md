# WORK-2026-11-10-009 — Automatic Azure API deployment

| Field | Value |
| --- | --- |
| Status | in_progress |
| Recorded | 2026-11-10 16:37 +07:00 (Asia/Bangkok) |
| Work performed | 10 November 2026 |
| Contributor | Codex |
| Related task | User-requested automatic backend deployment; WORK-007 and WORK-008 |
| Git state | Clean main at 191c0b3b294647dac7d0526dde9c687e21c89bb2; origin agrees |

## Objective

Build/test private backend images on GitHub-hosted runners, deliver securely to
existing Azure Compose, preserve scientific data, verify production and rollback.

## Changes and findings

- Initial SSH inspection: all three services healthy, 19 GiB free disk, 2 GiB
  available RAM, 4 GiB swap; no maintenance lock held. No Docker group change.
- GitHub admin access available; no secrets/variables/environments/runners/rulesets,
  main unprotected, default Actions token read-only. Billing endpoints inaccessible
  with existing token (user scope absent); quota is not verified.
- Azure CLI cached account exists but authentication expired (AADSTS700082).
  Requested local Azure login; no credentials requested in chat.
- Preferred transport: passwordless Azure OIDC and VM Run Command over the Azure
  control plane; no inbound SSH rule or production runner required.

## Verification

Baseline: 508 passed / one existing skip. After rollback tests: 512 passed / one skip.
Backend offline production/unit tests: 13 passed. Public smoke: 28 checks passed.
Actionlint 1.7.12 and locked requirement export comparison passed. Real isolated
VM Docker health failure restored exact prior env and verified recovery; no graph
mounts or volumes were used. Path-policy and transaction tests: 11 passed. Raw outputs: `reports/runs/WORK-2026-11-10-009/`.

## Decisions

[D040 backend delivery amendment](../decisions.md).

## Open issues and limitations

Azure authentication restored after user MFA. Actual VM tenant/subscription verified
using IMDS; identity/federation/custom VM-scoped role and main-only production-api
environment configured. Existing NSG public SSH/HTTP/HTTPS rules unchanged. Root-owned
activation scripts and compatibility approval installed. Production unchanged so far.
Existing Offline checks failed from missing matplotlib; install locked analysis/report
extras in both workflows. Initial push/manual runs 42793772100/42793793606 failed safely before activation:
Docker containerd inspect identity differed from the VM classic-store config ID.
Corrected packaging to hash the docker-save config directly, with offline regression
coverage. Full suite now 524 passed / one skip; rollback/path/identity tests 16 passed.
Corrected automatic run [42794633050](https://github.com/HSandz/scientific-network/actions/runs/42794633050)
passed: a6fc512 activated, public smoke passed, existing DB/proxy preserved.
Both Docker stores now derive config identity from docker-save rather than inspect.Id.
Manual [42794687317](https://github.com/HSandz/scientific-network/actions/runs/42794687317)
passed as a verified no-op, preserving the active image/container. Final push test
includes a nonfunctional backend package docstring, portable VM config fingerprinting
and current SHA-pinned Node24 actions. Hosted build and repaired Offline checks passed; Azure OIDC login/delivery succeeded.
Added transaction-bound rollback for hosted-only public smoke failures. Exact billing
quota remains inaccessible; each image artifact measured about 87 MB with one-day retention.
Multiple Codex processes exist locally; no dirty files or deployment processes
were found. Process presence alone cannot establish another session's intent.

## Next step

Push reviewed implementation on unchanged main, verify manual and automatic runs,
then finalize receipts and documentation-only negative push.

## Corrections

None.
