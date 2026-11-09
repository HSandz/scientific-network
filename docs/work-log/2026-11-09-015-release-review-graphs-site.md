# WORK-2026-11-09-015 — Review corrected release, report graphs and Site

| Field | Value |
| --- | --- |
| Status | in_progress |
| Recorded | 2026-11-09 18:54 +07:00 (Asia/Bangkok) |
| Work performed | 9 November 2026 +07:00 |
| Contributor | Codex, at the user's request |
| Related task | WORK-010–014 |
| Git state | Clean main at `be0ad9f` |

## Objective

Review the remediation, make graph visualizations visible in the reports and
update/publish the existing public Plan & Report Site under the user's current
instruction. Preserve scientific artifacts, Site identity/URL/audience and Plan.

## Changes and findings

Reviewed identity correction, source-bound evaluator/scorer changes and measured
report/package. Exact edge rescore matches committed JSON. Two presentation gaps
confirmed: no node-and-edge maps in the report and Site still on pilot version 18.
Added deterministic bounded views (researcher/organization/citation), public
source-pointer JSON/CSVs and three maps to the report, preserving all frozen
scientific inputs. Native Site replacement retains its full 20-chapter Plan with
D040 amendment, original public identity and audience. Escape search bug fixed.
Publication and updated package QA are in progress.

## Verification

Locked sync exit0. Baseline `uv run pytest`:504passed/1existing skip; final
suite:508passed/1existing skip,28.21s. New view tests cover induced edge semantics,
direction, deterministic order, private-text exclusion and stale/frozen/output
refusals. Network CLI generation exit0; structural validate with release quality
and --require-size exit0 (structural only). Exact rescore equality;541freeze and
32completion bindings plus1394-member prior ZIP pass. Native browser checks:
20chapters, unique IDs, zero embedded documents, all three graph counts/evidence
inspectors, filters/zoom/reset, deep hashes and mobile width pass. Initial Escape
check failed (known bug); explicit handler passes after reload. No fresh Neo4j
integration run: no import/query/graph changes. Logs under
`reports/runs/WORK-2026-11-09-015/` remain ignored.

## Decisions

The user now explicitly requests the Site update. Site-source publication is
authorized; no GitHub push, tag, invitation or course submission requested.

## Open issues and limitations

Verification and implementation in progress; no new scientific scores claimed.

## Next step

Finish review, add source-backed network views, verify report/Site and publish
one final Site update; record actual receipt or specific publication blocker.

## Corrections

None.
