# WORK-2026-11-10-007 — Azure production deployment

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-10 15:03 +07:00 (Asia/Bangkok) |
| Work performed | 10 November 2026 |
| Contributor | Codex |
| Related task | User-authorized Azure backend/Pages production deployment; WORK-006 dump |
| Git state | `main` at `b72100b` initially; implementation `ccdb690` pushed; final acceptance record follows; pre-existing migration edits excluded |

## Objective

Deploy the complete read-only Explorer on the existing Azure VM with Cloudflare
Pages, preserving the source graph, scientific artifacts and former resources.

## Changes and findings

- [Runbook and deployment scripts](../../ops/azure/README.md): inspected Ubuntu
  VM; safe persistent 4 GiB swap, Docker, dedicated graph volumes, bounded API/DB,
  read-only evidence SQLite, compact analytics, Caddy HTTPS, updates/rollback,
  status/logs/monitoring and guarded offline restore/backup.
- [Measured deployment receipt](../../reports/release-v4/azure-deployment-2026-11-10.md)
  records exact inventory, full-property fingerprints, all checks/failures and resources.
  [Artifact manifest](../../reports/release-v4/azure-runtime-artifacts-v1.json)
  binds source/output hashes; exhaustive ledger roundtrip and API parity passed.
- [Pages cutover receipt](../../reports/release-v4/azure-pages-cutover-receipt-v1.json):
  production build succeeded; served JS and browser requests use Azure, exact CORS/CSP.
  Existing Pages URL/project, former services and all other projects preserved.
- Production API: `https://scientific-network-api.eastasia.cloudapp.azure.com/api`.
  Local source was only queried read-only. No graph semantics/results changed.
- Fresh backup is checksum-verified outside Azure; original dump retained outside VM.
  Post-backup/restart full graph/schema equality passed. Known-good v3 settings saved.
- Durable operational rationale: [D040 Azure amendment](../decisions.md).

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `uv sync --locked --group dev --extra analysis` / initial `uv run pytest -q` | exit 0; 502 passed / 7 skipped before restoring optional report extra | initial baseline |
| `uv sync --locked --group dev --extra analysis --extra report`; final `uv run pytest -q` | exit 0; 508 passed / one existing skip | `repo-tests-acceptance.log` |
| `PYTHONPATH=apps/research-explorer:src uv run pytest apps/research-explorer/backend/tests -q` | exit 0; 19 passed, source integration plus production guards | `backend-tests-acceptance.log` |
| Offline `uv run research-network schema`; shell/Python checks; `git diff --check` | passed, exit 0 | ignored generated Cypher / final diff |
| Original dump checksums on local/VM; compatible offline fresh restore | passed; no overwrite; clean v2 restored sequentially | `restore-v2.log` |
| Fresh source/Azure inventory, schema, full typed-property fingerprints and post-restart comparator | passed, exit 0, zero differences | `database-comparison.json`, `post-restart-comparison.json` |
| Local image build/import/layout check; TypeScript/Vite Azure build; Pages production build | passed; existing chunk warning only | build logs / Pages receipt |
| `smoke-api.py --base-url https://scientific-network-api.eastasia.cloudapp.azure.com/api` | exit 0; 28 checks, complete graph/evidence functionality | `api-public-smoke-final.jsonl` |
| Production Playwright against actual Pages + Azure | exit 0; all five suites passed | `playwright-production.log`, screenshots |
| Separate browser network/console/mobile capture | exit 0; Azure only, no errors, graph rendered, no mobile overflow | `browser-network.json` |
| Offline backup, off-VM copy/checksum/admin metadata, Neo4j/API/Caddy recovery and known-good rollback | passed; zero OOM/restart loops; HTTPS and full graph recovered | backup/restart/rollback logs |
| Resource sampling, SSH, swap/fstab, public ports, strict CORS and secrets scans | passed; comfortable RAM/disk headroom; credentials mode 0600 | resource snapshots / report |

All raw paths above are under ignored `reports/runs/WORK-2026-11-10-007/`.

## Failures and decisions

First restore/start commands overlapped; stopped the new server immediately and
retained that volume unused. Restored a second fresh volume before startup and
added maintenance locks/markers. Initial empty-volume guard rejected image-created
empty skeleton directories; corrected without permitting actual data overwrite.
WSL credential helper blocked the first local image build; isolated public-image
Docker config fixed it. Startup path assumptions, missing NumPy and Caddy fallback
ordering were caught and fixed before cutover. Invalid smoke page size, unsupported
CLI flag, system-Python dependency and backup probe permissions/hostname were
corrected and rerun. Default Python HTTP user agent got Pages 403; curl/real browser
passed. No failed check was counted as passed; full details are in the receipt.

## Open issues and limitations

No blocking action or degraded feature remains. Actual VM reboot/certificate renewal
and long-duration stability were not tested. Recurring off-VM backup copying remains
an operator responsibility. Shared public rate budget is conservative. Unused first
volume and failed-image env snapshots retained; only known-good v3 is recommended.
Other agent's migration files/shared-doc hunks remain uncommitted and untouched in
content, rather than being included in this task's push.

## Next step

Observe the live deployment and perform periodic off-VM backups. Retain Render and
Aura until an observation period and explicit user authorization for cleanup.

## Corrections

None.
