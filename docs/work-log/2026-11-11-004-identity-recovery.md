# WORK-2026-11-11-004 — Task 2B identity recovery and evaluation

| Field | Value |
| --- | --- |
| Status | in_progress |
| Recorded | 2026-11-11T17:48:28+07:00 (Asia/Bangkok; entry creation time) |
| Contributor | Codex |
| Git state | Clean main at 294e029 |

## Objective

Investigate DOI/name abstentions, freeze an identity evaluation frame, implement
supported recovery, build an isolated candidate and compare against frozen v4/v3.
Preserve sources, historical judgments, topics, application and all databases.

## Changes and findings

Baseline clean at 294e029. Verified singleton DOI gap, all seven original
source records, 170 IDs/683 positions and 23 other name-conflicted IDs with higher
ORCID conflicts. Forty bounded public requests cached; five explicit ORCID alias
certificates. Sampling frozen before recovery. Resolver/candidate extended; initial
candidate has 253 more positions than v3, no v3 losses. Data replay passes; a report
reason-ordering issue prompted a preserved intermediate and final version.
Final replay and comparison running under this work ID; no infrastructure access.

## Verification

- Baseline sync and suite: 573 passed/7 skips (report extra absent); restored
  optional report extra, no dependency/lockfile change.
- Focused final tests: 115 passed, exit0. Full final suite:603 passed/one existing
  empty-parameter skip, exit0. Source hashes and structural CLI pass.
- Two failed development checks: an ignored script named inspect.py shadowed the
  standard library (renamed); one new fixture lacked its directory (fixed).
- Initial data replay byte-identical; comparison reason-key ordering differed but
  JSON values agreed. Fixed by sorting, final new candidate/replay in progress.
- Neo4j integration not run; no import/query/service changes or DB writes.

## Decisions

Pending evidence investigation. No promotion authorized by graph counts.

## Open issues and limitations

Semantic precision/recall require independently supported references; no such
measurements claimed. No Task3 affiliation enrichment or topic work.

## Next step

Census all 170 provider IDs and seven DOI discrepancies; freeze sampling before
recovery implementation. Raw command outputs under reports/runs/WORK-2026-11-11-004/.

## Corrections

None.
