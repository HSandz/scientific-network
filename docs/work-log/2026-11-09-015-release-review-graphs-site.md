# WORK-2026-11-09-015 — Review corrected release, report graphs and Site

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-09 18:54 +07:00; finalized19:17 +07:00 (Asia/Bangkok) |
| Work performed | 9 November2026 +07:00 |
| Contributor | Codex, at the user's request |
| Related task | WORK-010–014 |
| Git state | Started clean main `be0ad9f`; source checkpoint `fb2f0e7`; final receipts follow |

## Objective

Review remediation, add visible graph maps to reports and update/publish the
existing public Site. Preserve frozen scientific artifacts and Site identity.

## Changes and findings

Reviewed identity correction, source-packet/scorer/evaluator changes and report.
No further blocking implementation defect found in the reviewed paths. Confirmed
two presentation gaps: only statistical charts in the report and stale pilot Site
v18. Added `release-network-views-v1`: deterministic bounded induced researcher,
organization and citation maps, public evidence JSON/CSVs and input/output hashes.
Report adds three maps alongside six statistical charts. Full-projection results
stay separate from illustrations. No new inference, graph build, judging or audit.
Native Site v19 replaces pilot Report data with corrected graph views/controls,
charts, limits and the26-page PDF. Full Plan preserved exactly except two identical
D040 amendment insertions. Fixed old Escape-search bug. Mutable Site report,
workflow/roadmap/status and dated D040 authorization updated.

## Verification

Locked sync exit0. Baseline pytest:504passed/1existing skip; final `uv run pytest`
exit0:508passed/1skip,28.21s. Four new tests cover induced/directed semantics,
determinism, public text boundary, stale analysis/freeze and output refusals.
Network CLI exit0. Structural validate with release config and --require-size
exit0; not semantic accuracy. Exact edge rescore equals committed JSON.541freeze
and32completion bindings pass; original1394-member ZIP and125historical hashes
unchanged. No new Neo4j integration run: import/query/graph unchanged.

Source checkpoint `fb2f0e797f197ebdd5691b5cec6b93afa49195ad` precedes local
render. First packaging process exited143 after partial artifacts; retained under
`package-v4-maps/`, not treated as valid. New unused `package-v4-maps-v2/` renderer
exit0:26A4pages/nine images. Independent package verifier exit0:1410ZIPmembers,
1407tracked sources,36HTMLlinks,nine tables,font/glyph/page bounds,14unchanged
historical CRLF exceptions,4configured secrets/0hits. PDF map pages13–15 inspected
at1000px; no clipping/overlap. Old packages remain byte-identical.

Site build/node syntax exit0; desktop/mobile browser verifies three exact graph
counts, node/edge evidence, search/group/support filters, zoom/reset, deep hashes,
20chapters,221unique IDs,zero embedded documents,six chart loads,14downloads.
Escape initially failed; explicit handler passes after full reload. One rerun
mistakenly navigated by hash without reloading changed JS and hit an open dialog;
full navigation resolved that stale test state. No JS errors/warnings observed.
Site output configured-secret scan:4values/0hits. Supported source helper pushed
`7fdaf1ed6cd85bda8dc1474694f90fe4e38a2f67`; native save/deploy v19 succeeded at
19:12:08 +07:00, retaining public project/URL/audience. Live DOM confirms corrected
graph/counts,20chapters,zero Report embeds,organization/evidence controls and PDF
HTTP200/2039947bytes. Hosted Plan/search automated pointer actions timed out;
DOM Plan activation works; local pointer/keyboard checks pass. Live Escape was
not established by a successful opened-dialog interaction; no such claim made.

## Artifacts and decisions

[Package receipt](../../reports/release-v4/local-package-receipt-v3.json),
[Site receipt](../reference/sites-corrected-release-publication-2026-11-09.json),
[maps/payload/CSVs](../../reports/final-report/network-views-v4-v1/).
Raw logs/render outputs remain ignored in `reports/runs/WORK-2026-11-09-015/`.
Source checkpoint and rendered PDF predate publication; their old delivery wording
is contextualized in current release README. New QA/receipts follow the package
snapshot and are intentionally outside it. User authorized Site publication only;
no GitHub push,tag,invitation or course submission. D040 records view selection
and current publication authorization. Used the Sites plugin/skill.

## Open issues and limitations

AI-only edge result193/200=96.5%,Wilson92.95–98.29%; evaluator independence,
human validation and verified course accuracy not established. Affiliation
coverage and topic precision gates still fail. No scientific thresholds changed.
Real personal/course/access facts remain pending; local course draft only.
Hosted pointer QA limitation recorded above; no confirmed app defect established.

## Next step

User can inspect the public Report/network maps and local PDF. Supply real team
and course/access facts before a new submission render; no additional tuning,
audit cycle or historical source collection is needed for this presentation work.

## Corrections

None to finalized prior records.
