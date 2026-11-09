# WORK-2026-11-09-011 — Versioned ORCID identity correction

| Field | Value |
| --- | --- |
| Status | in_progress |
| Recorded | 2026-11-09 15:18 +07:00 (Asia/Bangkok) |
| Work performed | 9 November 2026 |
| Contributor | Codex |
| Related task | WORK-010; full remediation B |
| Git state | main after 68191be; only task changes |

## Objective

Correct complete matched-source ORCID handling in a separately versioned graph, preserving immutable graph v3, topics and historical failed outcomes.

## Changes and findings

- [D040 amendment](../correction-amendment-2026-11-09.md) records explicit user authorization and pre-draw seed 20261109. New protocol/config paths selected before correction/sampling.
- Implementation delegated to a separate coding context; no real graph output yet.

## Verification

In progress; record code tests, correction CLI, invariants and old hash checks here.

## Decisions

Bounded amendment in decisions.md; missing ORCID allowed, malformed nonempty evidence withheld conservatively; unsupported organizations removed, all paper metadata/denominators preserved.

## Open issues and limitations

No external actions authorized. Semantic accuracy requires new prospective source audit, not structural checks alone.

## Next step

Review/tests; correct into unused v4 paths; freeze and validate before audit.

## Corrections

None.
