# WORK-2026-11-09-012 — Corrected database and analysis

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-09T15:21:08+07:00 (Asia/Bangkok) |
| Work performed | 9 November 2026 |
| Contributor | Codex coordinator and isolated computation context |
| Related task | WORK-011; remediation C |
| Git state | main at 8761991 |

## Objective

Load frozen graph v4 in the isolated release DB, reconcile inventory/integrity/replay; recompute all projections, sensitivity, figures and descriptive findings.

## Changes and findings

[Measured findings](../../reports/release-v4/findings.md) and [comparison](../../reports/release-v4/analysis-comparison.json) show 3,533 academia–industry pair-paper supports (previous4,181); top bridge Bo An; largest researcher component20,776/32,189. Organization portfolios change despite canonically identical citation/paper-topic projections. Two investigation shortlists are regenerated and qualified.

Only neo4j-five-year on7689 is authorized. Verified container identity/published ports and Neo4j5.26.12 Community before reset. Old graph remains recoverable from hash-verified immutable graph v3/receipts. Computation uses existing frozen analysis/quality configs. Long-running commands/logs under `reports/runs/WORK-2026-11-09-012/` (database.py, database-reset.log, neo4j-load.log, analysis.log).

## Verification

| Check | Outcome |
| --- | --- |
| Explicit isolated reset, loader and replay with NEO4J_URI=bolt://localhost:7689 | passed, exit0; 47,875 nodes/225,731 relationships; all per-label/relation maps identical |
| Inventory/version check + all six `queries/02_integrity.cypher` statements | passed, exit0; zero violation rows; only corrected version |
| `validate --require-size` | passed, exit0; structural/derived and size gates pass |
| `analyze` with frozen analysis/quality configs | passed, exit0; all five projections + strict sensitivity freshly recomputed; SHA256 580d1a6dbc21ef2ac17b820979830f3de157fc1b04d1c89f2580731f141701c9 |
| figures module | passed, exit0; six PNG/CSV pairs and versioned captions |
| Eight descriptive source-case checks | passed; original cached authorships/official roster hashes; recorded in analysis-comparison/source run artifact |

Initial validate attempt used nonexistent --require-derived (exit2); corrected command succeeds. Replay comparison initially read top-level instead of nested database receipt fields (KeyError); corrected comparison passes. These were command/check errors, not database failures. Recorded wall clock jumped during interruption; do not infer execution duration from timestamps.

## Decisions

Follow authorized version reset/import procedure only in isolated service. No volume pruning or pilot/extended DB change.

## Open issues and limitations

Structural/DB/analysis checks do not establish semantic accuracy. AI audit follows one prospective freeze.

## Next step

WORK-013: draw one full-frame prospective edge sample using precommitted seed20261109, freeze source/evaluator bindings, authorize isolated reviewers.

## Corrections

None.
