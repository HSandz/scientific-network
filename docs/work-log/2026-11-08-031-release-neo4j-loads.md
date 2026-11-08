# WORK-2026-11-08-031 — Release Neo4j loads and integrity checks

| Field | Value |
| --- | --- |
| Status | completed (Phases 4 and 5 database checks passed) |
| Recorded | 2026-11-08 13:03 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-08 12:54–13:03 +07:00 |
| Contributor | Codex, at the user's request |
| Related task | [WORK-2026-11-08-030](2026-11-08-030-release-phase-5-embedding-development.md) |
| Git state | `main` at `e20bab1`; Phase 4/5 evidence ready for local checkpoint |

## Objective

With Docker available, finish Phase 4 against graph v1 and load graph v2 for Phase 5 on
the isolated `neo4j-five-year` service. Record inventory, integrity and replay results
without touching the pilot or extended databases.

## Changes and findings

- Started only `neo4j-five-year` (Neo4j 5.26.12 Community). It is healthy and remains
  running on localhost ports 7476 and 7689. Its database was empty before the first
  import. The pilot and extended services/volumes were not started or modified.
- Phase 4 graph v1 `release-4c1253e05f2c` loaded and reconciled at 52,415 nodes and
  261,755 relationships. Inventory matched the graph artifact; `02_integrity.cypher`
  returned no rows. Replay left all per-label and per-relation counts unchanged.
- Per D040, cleared records only from the isolated `neo4j-five-year` database before the
  v2 reload; verified 0 nodes/0 relationships afterward. No volume was deleted.
- Phase 5 graph v2 `release-5d830ffcbdf4` loaded with 52,415 nodes and 275,438
  relationships, matching the frozen graph summary and hash. Inventory matched; the
  integrity query returned no rows. A second v2 replay also left all counts unchanged.
  The database now contains only v2 (no v1 records).
- First v1 load emitted 86 nonfatal unknown-property and 10 unknown-relationship-type
  notifications while the newly empty database had no schema tokens yet. Import
  reconciliation passed, and replay plus both v2 imports emitted no such notifications.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `uv sync --locked --group dev --extra analysis` | passed, exit 0 | dependencies locked |
| `uv run pytest -q -p no:cacheprovider` | passed, exit 0; 354 passed, 1 skipped | existing empty-parameter skip in `tests/test_cli.py` |
| `docker compose --profile five-year up -d --wait --wait-timeout 180 neo4j-five-year` | passed, exit 0; healthy | only isolated release service started |
| Pre-load database query | passed; 0 nodes, 0 relationships | ignored run log under `reports/runs/WORK-2026-11-08-031/` |
| v1 load | passed, exit 0; 42.15 s; 72 transactions; before 0, after 52,415 nodes / 261,755 edges | [load receipt](../../reports/release-v1/neo4j-load-v1.json) |
| v1 inventory and `02_integrity.cypher` | passed; inventory equals graph summary; integrity stdout/stderr empty | ignored `v1-inventory.txt`, `v1-integrity.txt` |
| v1 replay | passed, exit 0; 30.18 s; before/after 52,415 nodes / 261,755 edges; label/relation maps identical | [replay receipt](../../reports/release-v1/neo4j-replay-v1.json) |
| Isolated DB clear before v2 | passed, exit 0; immediately verified 0 nodes/0 relationships | `MATCH (n) CALL { WITH n DETACH DELETE n } IN TRANSACTIONS OF 10000 ROWS` in the `neo4j-five-year` default database only |
| v2 load | passed, exit 0; 41.53 s; 74 transactions; before 0, after 52,415 nodes / 275,438 edges | [load receipt](../../reports/release-v1/neo4j-load-v2.json), graph SHA matches v2 summary |
| v2 inventory and `02_integrity.cypher` | passed; inventory equals summary; integrity stdout/stderr empty | ignored `v2-inventory.txt`, `v2-integrity.txt` |
| v2 replay and post-replay queries | passed, exit 0; 31.52 s; before/after 52,415 nodes / 275,438 edges; integrity still empty | [replay receipt](../../reports/release-v1/neo4j-replay-v2.json), ignored post-replay query outputs |
| Final database version query | passed | only `release-5d830ffcbdf4`: 52,415 nodes / 275,438 relationships |

The loader uses `bolt://localhost:7689`; import receipts reconcile counts against the
same graph version. No credentials were written to logs or tracked files.

## Decisions

Follow D040's load sequence: validate v1 import/replay for Phase 4, clear only the
isolated release database, then load and replay frozen v2 for Phase 5. Keep the release
container running for the next phase.

## Open issues and limitations

Phases 4 and 5 database gates are complete. Topic semantic accuracy remains unmeasured;
the blind label sheet awaits reviewers. Structural and DBMS integrity checks do not
certify semantic accuracy.

## Next step

Start Phase 6 using the frozen v2 graph: run the configured offline analysis, inspect its
coverage and projections, then implement the missing per-year, sector/country, topic,
citation and bridge analyses and produce source-supported findings.

## Corrections

None.
