# WORK-2026-11-10-006 — Neo4j AuraDB migration

| Field | Value |
| --- | --- |
| Status | partial |
| Recorded | 2026-11-10 11:18 +07:00 (Asia/Bangkok) |
| Work performed | 10 November 2026 |
| Contributor | Codex |
| Related task | User-authorized local `neo4j-five-year` to AuraDB Free migration |
| Git state | `main`; clean at start; report and handoff docs are uncommitted; no push |

## Objective

Inventory the authorized local release database, create and retain a verified offline Neo4j dump, upload it to Aura only after read-only target verification, and compare database contents/schema and application queries. Preserve the local data volume and keep all credentials out of logs and artifacts.

## Changes and findings

- Added [migration report](../../reports/release-v4/neo4j-auradb-migration.md) with exact inventory comparison, dump checksum/location, upload failure and next action.
- The authorized source is Compose service `neo4j-five-year`, image `neo4j:5.26.12-community`, database `neo4j`, and resolved data volume `scientific-network_neo4j-five-year-data` mounted at `/data`. Docker Engine is 29.7.2 in WSL2 Ubuntu 24.04.
- Source graph matches release v4: 47,875 nodes, 225,731 relationships, graph version `release-d3c788c3114a`; 5 uniqueness constraints and 7 online indexes. All node IDs and relationship `edge_id`s are present and unique.
- Retained dump: `/home/san/.local/share/scientific-network/backups/neo4j-five-year-aura-migration-20261110T035914Z/neo4j.dump` (409,200,612 bytes; SHA-256 `1206b2572c4ebfb25b2c7db961daa429e0854d5daa14f307658ab178ecdce1df`). The private directory is mode 0700; files are mode 0600. It includes a sanitized source inventory and backup manifest.
- Aura URI identity, authentication, username match and target database `e86cd88a` were confirmed read-only. Aura was online and empty before upload and remains online and empty afterward.
- WSL2 Ubuntu 24.04 / Docker Engine 29.7.2 had 778 GiB free on the WSL root filesystem. Source database store files including indexes occupied 265,011,200 bytes; transaction logs occupied 1,892,657,253 bytes.
- The one official upload attempt failed before import with HTTP 422 `ImportExceedsMaxSize`. The uncompressed archive is 2,157,668,453 bytes; Aura reported minimum storage required 2.0 GB and requested at least 3 GB disk. No retry, tier change, graph rebuild, or data trimming occurred.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `git check-ignore -v .env.auradb`; `git ls-files --error-unmatch .env.auradb` | passed; ignored and untracked | `.gitignore:2`; no credential values printed |
| Docker service/volume inspection | passed; exact healthy five-year container/image and Compose-prefixed data volume verified | `reports/runs/WORK-2026-11-10-006/` (ignored) |
| Pre-dump read-only source inventory | passed; exact v4 totals, five labels, ten predicates, graph version; 5 constraints, 7 online indexes | `source-baseline-pre.json` |
| Aura read-only preflight | passed; configured account authenticated, database online and empty | `aura-baseline-pre.json` |
| Community `STOP DATABASE neo4j` attempt | failed (exit 1) as unsupported (`Neo.ClientError.Statement.UnsupportedAdministrationCommand`); source remained usable | observed in this session; stopped only the authorized container afterward |
| Initial offline `database info` on read-only mount | failed (wrapper exit 10) because Neo4j could not write `database_lock`; recovery handler restarted service | error observed in this session; source healthy afterward |
| Offline `neo4j-admin database dump` in exact 5.26.12 image | dump completed successfully; wrapper exited 12 because its host-side file check ran while the directory was owned by container UID and falsely reported missing; recovery restored ownership and restarted source | `dump.log`; final file independently verified |
| `neo4j-admin database load --info neo4j --from-path=/backups` | passed; valid ZSTD archive, 47 files, 2,157,668,453 uncompressed bytes | `dump-info.log`; checksum and nonempty file verified |
| Post-dump source fingerprint/inventory | passed; node fingerprint `640d30984212dcde382ace154e19b275f9ccc0a24ac164f56a9872e3d476eea1` and relationship fingerprint `fd01fa8837824c5a207eb339d855e616acfad626a81b813c0256701fef2c2936`, counts, labels, predicates, graph versions, constraints and indexes unchanged; source running/healthy | `source-baseline-post.json` |
| Guarded official `neo4j-admin database upload` | failed once with exit 1 / HTTP 422 `ImportExceedsMaxSize`; minimum configured disk 3 GB; no retry | `upload.log` |
| Final Aura read-only inventory | passed; database online, still 0 nodes/relationships, 0 constraints, 2 built-in online token indexes | `aura-baseline-post.json` |
| Application endpoints against Aura | not run; import did not complete, so the target has no graph | documented in migration report |
| Credential scan of generated artifacts | passed; zero matches | Checked run artifacts, retained backup, report and handoff files against configured secret values |

## Decisions

- Preserve the source volume and retained dump. Do not retry or change Aura tier until the instance is configured with at least 3 GB disk and the empty-target guard passes again.
- No change to scientific graph semantics or application configuration. Do not treat the separate local `graph.json` evidence ledger or analysis artifacts as part of this database dump.

## Open issues and limitations

- AuraDB Free cannot accept this dump: its upload service explicitly requires at least 3 GB disk. Aura remains empty and the imported graph/schema/application queries are therefore unverified.
- Backend deployment is not ready. A future upload must be followed by full inventory, schema/index, graph-fingerprint/sample, and read-only application-query checks.

## Next step

Configure the intended Aura instance for at least 3 GB of disk (paid-tier or equivalent user-approved capacity change), then re-verify its identity and empty state before one upload from the retained dump. After import, compare the full inventory/schema/content and run the application's read-only queries against Aura before considering Render preparation.

## Corrections

- 2026-11-10 11:25 +07:00: tightened ignored `.env.auradb` from mode `0664` to `0600` without changing its contents. Rechecked `git diff --check` (pass), confirmed `.env.auradb` remains ignored and untracked, scanned 31 migration artifacts against three configured secret values (zero matches), and reverified the retained dump checksum (pass).

- 2026-11-10 16:12 +07:00: user requested committing the remaining migration documentation and shared-document hunks to clean the worktree. Records reviewed; the staged whitespace check flagged two Markdown hard breaks, normalized to explicit HTML breaks before the final passing check. Configured-credential scan and final whitespace validation passed; documentation committed locally, without a push or runtime change. No tests or migration commands rerun for this documentation-only checkpoint. The migration next-step recommendation above is historical and superseded by the verified Azure deployment in [WORK-007](2026-11-10-007-azure-production.md); no Aura upgrade is planned.
