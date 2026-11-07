# WORK-2026-11-06-001 — Five-year execution readiness plan

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-06T14:46:57+07:00 (Asia/Bangkok) |
| Finalized | 2026-11-06T15:00:54+07:00 |
| Work performed | 2026-11-06, UTC+07:00 |
| Contributor | Codex |
| Related task | [WORK-2026-11-04-003](2026-11-04-003-native-site-report.md) |
| Git state | main at 66e692d; clean at start; configured GitHub origin now exists; no project commit/push in this task |

## Objective

Create a five-year execution plan with edition readiness, dependencies, quality
priorities, resource/annotation estimates and acceptance checks. Update related
docs and publish Plan/Report on the same Site. The user confirmed **11 November
2026** as the deadline and asked to ignore the remaining capacity/lecturer questions.
No further answers were prerequisites. D018 remains in force: no pipeline
implementation, research discovery/collection, new splits or graph imports.

## Changes and findings

- Added [execution plan](../five-year-execution-plan.md): P01 planning plus E01–E09
  conditional work packages; dependencies, outputs/acceptance checks, stable IDs,
  cross-year leakage protection, publication-time triples, temporal support,
  isolated Neo4j storage, independent evaluation and truthful partial delivery.
- Added [planning readiness CSV](../five-year-edition-readiness.csv): all 34 series
  × 2021–2025 = 170 unique pending candidates. Catalogs are inherited leads;
  evidence/reviewer/time fields blank. Historical 2023 statuses remain separate.
  No new official edition/source was checked; no new corpus manifest was created.
- Added [planning estimates](../../reports/five-year-planning-estimates-2026-11-06.json):
  hypothetical 10k/50k/100k work scenarios, explicit request/cache/PDF/runtime
  assumptions and independent-review effort. Summarized existing metadata for
  240 historical PDFs: median 1.3002 MiB, max 34.7813 MiB, total 0.7690 GiB by record.
  Cache-dominated 0.004s median extraction timing is not a cold benchmark and is
  excluded from runtime forecasts. No PDF downloaded or parsing service run.
- Recorded 11 November deadline. Internal proposed cutoffs (+07:00): source-feature
  freeze 8 November 18:00; candidate/method freeze 9 November 18:00; gate assessment
  10 November 12:00; submission-ready package 10 November 18:00. Existing quality
  gates remain unchanged; estimates disclose that review may exceed the calendar.
- Updated README, scope/project plan, roadmap, team record, decision D021, current
  status and [Site Report prose](../../reports/site-report.md). Corrected stale
  Git handoff: main now has first commit 66e692d and configured origin
  `git@github.com:HSandz/scientific-network.git`; no remote availability/privacy or
  clean-clone check performed, and no project push/commit performed here.
- Reopened existing Site from v5 commit cff18abcedc97a4963d44a5c98d66bd93cae557c in
  `/tmp/scientific-network-site-20261106`. Kept all 20 Plan sections and native
  Report, replaced stale eight-week SVG with conditional 6–11 November schedule,
  integrated task/acceptance/resource tables in Plan and dated planning update in
  Report. Added permitted plan/CSV/estimate downloads; preserved graph payload.
- Published the same public Site as **version 6**, source commit
  `3809367c0a8e8ed351452e0ef80ffeb32697b706`. Native deployment succeeded.
  [Receipt](../reference/sites-execution-plan-publication-2026-11-06.json),
  [Plan snapshot](../reference/sites-project-plan-2026-11-06.md),
  [Report snapshot](../reference/sites-progress-report-2026-11-06.md).

## Verification

Commands from project root except Site source/build commands. Local raw outputs
are under `reports/runs/WORK-2026-11-06-001/` and ignored by Git.

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `uv run pytest` | Passed, 0; **97 tests in 1.42s** | `pytest.log` |
| Offline `research-network schema` | Schema output recorded; standalone final exit check below | `schema.log` / `schema-final.log` |
| `PANDOC=/home/san/.cache/uv/archive-v0/WGuPJWVt0YVQCVdTXlt37/lib/python3.13/site-packages/pypandoc/files/pandoc python3 /tmp/scientific-network-site-20261106/build_site.py` | Passed, 0; final build 20 sections / two tabs, 1,198,102 HTML bytes | Exact published Site source |
| `python3 -m py_compile /tmp/scientific-network-site-20261106/build_site.py /tmp/scientific-network-site-20261106/plan_figures.py` | Passed, 0 | Builder and timeline syntax |
| `uv run python /tmp/check-five-year-plan.py` | Passed, 0; 170 unique pending rows, estimate arithmetic/input hashes, local links, 262 unique IDs, 12 checklist items, zero built embeds, credential markers absent; expected Plan changes only | `planning-checks.json`; checker retained in run folder |
| Protected-file and payload checks | Passed; **5,722** original data/config/code/test/query/report/reference/finalized-log files unchanged; safe native payload byte-identical | `protected-before.json`, `planning-checks.json` |
| Native Plan browser checks | Deadline/timeline, E01–E09 acceptance table, five deadline-search results, 12 checklist items; pointer tabs and actual ArrowLeft keyboard navigation work | Browser readbacks |
| Native Report browser checks | Full 399/533; factual 379/369; researchers 85/36; organizations 32/4; all seven downloads return 200; new planning update and deadline visible; no console errors | Browser readbacks |
| Responsive/visual browser checks | Passed at 1440/768/390px; Plan/Report no document overflow; 390px timeline container 325px with scrollable 666px contents; desktop/mobile screenshot inspected | `plan-mobile.jpg`; browser desktop screenshot |
| Sites source helper, native save/deploy and get_site | Passed, helper 0/deployment succeeded; v6, title/URL/public audience preserved | Publication receipt |
| Live Site | Deadline diagram, P01/E01–E09, 20 sections, 12 checklist items and three new downloads verified; Report retains 399/533 and exact graph version, new planning update; no console errors | `live-browser-checks.json`, `live-panel-checks.json` |

The live page includes one extra frame outside both workspace panels; both native
Plan/Report panels have **zero** iframe/object/embed elements, and built HTML has
none. This frame is not a report embed. Updated the workflow to scope assertions
to built source/app panels and record outside hosted frames separately.

Failures/recoveries: the first source-helper prompt was cancelled (exit 1) before
credential input to relaunch in the selected checkout; no source effects. One
local metrics inspection assumed a nonexistent `name` key and failed; corrected
to the actual `venue_id`/`status` schema before generating artifacts. Browser cache
initially showed stale deadline text, fixed using a fresh query URL. A hidden-tab
pointer wait timed out; selecting the same browser tab restored visibility and
subsequent pointer/keyboard/visual checks passed. No build, test or publish failures.

## Decisions

[D021 — Deadline-driven readiness, planning only](../decisions.md#d021--deadline-driven-execution-readiness-planning-only-2026-11-06).
D018, D019 and D020 remain unchanged. No threshold/scope relaxation or paid spend.

## Open issues and limitations

E01–E09 execution unstarted; five-year editions remain unverified. No new scientific
results, source requests, split freezes, pipeline changes or DB writes. The loaded
399/533 snapshot and unimported 402/538 candidate remain historical 2023 evidence;
accuracy, recall and release qualification are unmeasured/unmet. Independent review
may not fit the deadline; partial results must disclose gaps. No extra capacity or
lecturer response is required to finish this planning task. Services, API quotas,
remote code access/privacy, actual disk/RAM and cold throughput were not checked.
OS print/PDF generation was not exercised. Site is a dated task-published snapshot.

## Next step

Use the dated execution plan. After a later explicit execution instruction, start
E01 edition/source verification and E02 offline contracts, reconcile cross-year
versions and freeze leakage-safe memberships before E05 enrichment. Prioritize
E06 identity/affiliation quality and reserve independent review/report time.
The 11 November deadline does not lift the D018 pause. Keep subsequent Site
updates native and dated. No automatic project commit/push required or performed.

## Corrections

None. Earlier finalized entries/receipts/snapshots remain unchanged. This entry
supersedes the old eight-week next-step guidance with the confirmed deadline.

## Final verification checkpoint

2026-11-06T15:01:26+07:00: final documentation links, matching Plan/Report snapshots, clean Site
source checkout, v6 succeeded receipt and all 5,722 protected files pass.
Standalone `uv run research-network schema` exited 0 (`schema-final.log`).
Preview stopped cleanly, exit 0. No task-owned background jobs remain.
