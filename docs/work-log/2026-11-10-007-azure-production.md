# WORK-2026-11-10-007 — Azure production deployment

| Field | Value |
| --- | --- |
| Status | in_progress |
| Recorded | 2026-11-10 14:30 +07:00 (Asia/Bangkok) |
| Work performed | 10 November 2026 |
| Contributor | Codex |
| Related task | User-authorized Azure backend deployment; WORK-2026-11-10-006 dump |
| Git state | `main` at `b72100b`; migration report/log and status/index edits present at start and preserved |

## Objective

Deploy the complete read-only Explorer backend and unchanged release database on
the existing Azure VM, retaining Cloudflare Pages and all former services.

## Changes and findings

- SSH alias works; Ubuntu 24.04.5 LTS, x86-64, 2 vCPUs, 3.8 GiB RAM,
  30 GB OS SSD (ext4 root; 27 GiB available), no resource disk or existing swap.
- Docker absent; only SSH listens publicly. Password SSH disabled; sudo works.
  Azure-agent swap disabled and cloud-init complete. Existing data/services preserved.
- Resource plan: 4 GiB OS-disk swap, swappiness 10; Neo4j heap 512–768 MiB,
  page cache 512 MiB, container ceiling 2 GiB; API ceiling 768 MiB, one worker;
  retain at least 8 GiB disk headroom. Build API/artifacts locally.
- Dump SHA-256 matches user-supplied value. Local database receives read-only
  verification queries only; no stop/restart, import, or configuration changes.
- Cloudflare connector authenticated; account has zero zones. Stable HTTPS hostname
  is pending user input; continue independent VM/database/API work.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `uv sync --locked --group dev --extra analysis`; `uv run pytest -q` | 502 passed / 7 skipped, exit 0; six skips because optional report extra absent; restored report extra afterward | initial baseline |
| SSH OS, disks, memory, ports, users, cloud-init, waagent, SSH/firewall inspection | passed, exit 0; no temporary disk, existing swap or application containers | inventory above |
| `sha256sum` existing dump | passed, exit 0 | original backup outside VM |
| Cloudflare accounts/zones read | authenticated, zero zones | connector read |

## Decisions

Use dedicated production volumes and disk-backed evidence; preserve graph semantics.

## Open issues and limitations

Checkpoint 2026-11-10 14:48 +07:00: swap/Docker and clean v2 dump restore
complete; exhaustive inventory, schema, samples and full typed-property node/edge
fingerprints equal the fresh local source. Source-only read queries performed.
142,928 evidence objects and 56,273 affiliation observations preserved by exhaustive
SQLite roundtrip; exact API analytics/metrics/community/ranking parity passed.
First startup was issued before loader returned; stopped immediately, volume v1
retained unused, then restored fresh v2 sequentially. Locks/markers added.
Initial API image path assumptions failed startup; corrected layout/import check.
Functionality smoke exposed missing NumPy (NetworkX layout) and Caddy route-order
404; include required NumPy, bound BLAS threads, add image layout check and use
exclusive Caddy handlers. Final v3 image is building/transferring. No cutover yet.
HTTPS certificate obtained for user-supplied Azure DNS hostname; no NSG change needed.
Repo tests 508 pass / 1 existing skip; backend tests 17 pass. No push yet.

## Next step

Configure safe swap and Docker; prepare compact artifacts and guarded deployment.

## Corrections

None.
