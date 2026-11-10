# Neo4j AuraDB migration report

**Work:** WORK-2026-11-10-006<br>
**Recorded:** 2026-11-10 11:16 +07:00 (Asia/Bangkok)<br>
**Status:** Partial — local backup verified; AuraDB Free rejected the import before loading it.

## Result

The authorized local `neo4j-five-year` database is healthy and unchanged. A readable, checksummed Neo4j 5.26.12 dump and sanitized source inventory are retained outside the repository. Aura authentication and target-database identity were verified, and the target was empty before and after the one upload attempt.

The official `neo4j-admin database upload` command returned HTTP 422, `ImportExceedsMaxSize`: the uncompressed dump exceeds AuraDB Free capacity; Neo4j requires **at least 3 GB disk** (minimum storage required: 2.0 GB). No second upload was attempted. The dump and local source remain available to resume after the Aura instance has adequate storage.

## Source and destination

| Inventory | Local source | AuraDB target after attempt |
| --- | ---: | ---: |
| Total nodes | 47,875 | 0 |
| Total relationships | 225,731 | 0 |
| Graph version | `release-d3c788c3114a` | none |
| Constraints | 5 | 0 |
| Indexes | 7, all online | 2 built-in token lookup indexes, online |

Aura identity was confirmed from the encrypted Bolt URI host `e86cd88a.databases.neo4j.io`; the configured instance-ID username authenticated successfully and resolved the configured database `e86cd88a`, which was online. The final read-only check still found it empty.

### Nodes by label

| Label | Local | Aura |
| --- | ---: | ---: |
| Researcher | 32,189 | 0 |
| Paper | 13,617 | 0 |
| Organization | 2,047 | 0 |
| Topic | 20 | 0 |
| Venue | 2 | 0 |

### Relationships by predicate

| Predicate | Local | Aura |
| --- | ---: | ---: |
| AUTHORED | 50,437 | 0 |
| AFFILIATED_WITH | 38,664 | 0 |
| PUBLISHED_IN | 13,617 | 0 |
| CITES | 7,308 | 0 |
| HAS_TOPIC | 14,222 | 0 |
| SUBTOPIC_OF | 16 | 0 |
| COAUTHORED_WITH | 80,482 | 0 |
| COLLABORATED_WITH | 13,031 | 0 |
| RESEARCHES_TOPIC | 5,622 | 0 |
| CONTRIBUTES_TO_TOPIC | 2,332 | 0 |

## Local database and backup

- Compose service: `neo4j-five-year`; container image and `neo4j-admin` version: `neo4j:5.26.12-community` / `5.26.12`.
- Source database: `neo4j`; resolved Docker data volume: `scientific-network_neo4j-five-year-data`, mounted at `/data`.
- Environment: Docker Engine 29.7.2 on WSL2 Ubuntu 24.04; 778 GiB was free on the WSL root filesystem at export time.
- Source database store directory: 265,011,200 bytes (253 MiB), including the schema/index files; transaction-log directory: 1,892,657,253 bytes.
- Offline export command: `neo4j-admin database dump neo4j --to-path=/backups`, run in the exact 5.26.12 image as the Neo4j user with the source service stopped and the resolved source volume mounted.
- Retained dump: `/home/san/.local/share/scientific-network/backups/neo4j-five-year-aura-migration-20261110T035914Z/neo4j.dump`.
- Dump size: 409,200,612 bytes (390.3 MiB). SHA-256: `1206b2572c4ebfb25b2c7db961daa429e0854d5daa14f307658ab178ecdce1df`.
- Neo4j archive reader (`neo4j-admin database load --info neo4j --from-path=/backups`) verified a ZSTD dump with 47 files and 2,157,668,453 uncompressed bytes. That expanded size is why Aura rejected the Free-tier import; no data was trimmed or rewritten.
- Backup directory permissions are `0700`; retained files are `0600`. It also contains `SHA256SUMS`, `backup-manifest.json`, and `source-inventory.json`. The manifest contains no credentials.

The source has five uniqueness constraints (`organization_id`, `paper_id`, `researcher_id`, `topic_id`, `venue_id`) and seven online indexes: five associated `id` range indexes and two token lookup indexes. A deterministic full-content fingerprint covered every node’s labels/properties and every relationship’s direction, type, endpoints, property values and data types. All node IDs and relationship `edge_id` values were present and unique. Pre-dump and post-restart fingerprints, inventory, constraints and index states matched exactly. Deterministic representative node samples for all five labels and relationship samples for all ten predicates are recorded in the sanitized source inventory.

The full-stream SHA-256 fingerprints were `640d30984212dcde382ace154e19b275f9ccc0a24ac164f56a9872e3d476eea1` for nodes and `fd01fa8837824c5a207eb339d855e616acfad626a81b813c0256701fef2c2936` for relationships, unchanged after the dump.

## Upload and verification

- Preflight authenticated to the Aura URI using the existing ignored `.env.auradb`, verified the configured username and database, confirmed the instance database was online, and confirmed 0 nodes / 0 relationships. Credentials were passed to the CLI through its environment; neither environment-file contents nor secret values were written to logs or this report.
- One official encrypted `neo4j-admin database upload` attempt used the retained dump and `--overwrite-destination=true` only after a second empty-target check.
- Aura accepted authentication, then returned HTTP 422 `ImportExceedsMaxSize`: “The uncompressed Neo4j dump file exceeds the disk capacity of this instance.” The response states a **3 GB minimum configured disk** is needed (minimum storage required: 2.0 GB). No retry or overwrite followed.
- Final read-only Aura inventory: target database online; 0 nodes, 0 relationships, 0 constraints, and the two built-in online token lookup indexes.
- Final local check: source service running/healthy; exact release-v4 counts, five constraints, seven online indexes, one graph version, and both full-content fingerprints unchanged.
- A scan of the run artifacts, retained backup, report and handoff files against configured database secret values found no credential matches.
- Application search, neighborhoods, edge-detail, analytics and database-version endpoints were not run against Aura because the graph import did not complete. The migration also does not include the separate local `graph.json` evidence ledger or analysis/report artifacts.

## Failures and operational notes

1. Community Edition rejected `STOP DATABASE neo4j` with `Neo.ClientError.Statement.UnsupportedAdministrationCommand`; only the authorized `neo4j-five-year` container was stopped for the offline dump and then restarted.
2. An initial read-only data-volume mount prevented `neo4j-admin database info` from acquiring `database_lock`; the source was restarted by the recovery handler. The successful offline inspection/dump used the source-compatible image and the standard read-write offline mount.
3. The dump completed successfully, but an early wrapper permission check ran while the private backup directory was owned by the container’s Neo4j UID and reported a false “missing or empty” result. The recovery handler restored ownership and restarted the source. Independent file-size, checksum, archive-reader, and post-restart full-graph checks then passed.
4. Aura rejected the only upload attempt for capacity. The target remained empty; no CSV import, graph rebuild, or dataset change was made.

## Readiness and next step

**Not ready for the Render backend.** The database is not present in Aura, application queries have not been validated there, and local evidence/analysis artifacts remain separate deployment requirements.

After the Aura instance is explicitly upgraded/configured for at least 3 GB of disk, re-authenticate, verify the intended target is still empty, and perform one upload from the retained dump. Then repeat full inventory, schema/index, graph-fingerprint/sample, and read-only application-query comparisons before preparing any backend deployment. Do not modify the source volume or recreate the graph.

## Documentation consulted

- [Neo4j Aura migration tutorial](https://neo4j.com/docs/aura/tutorials/migration/)
- [Neo4j Operations Manual: upload to Aura](https://neo4j.com/docs/operations-manual/current/database-administration/standard-databases/upload-to-aura/)
- [Neo4j Operations Manual: offline dump/load in Docker](https://neo4j.com/docs/operations-manual/current/docker/dump-load/)
- [AuraDB quotas and limits](https://neo4j.com/docs/aura/quotas-and-limits/)
