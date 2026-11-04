# WORK-2026-11-04-003 — Native Report in the existing Site

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-04T21:58:02+07:00 (Asia/Bangkok) |
| Finalized | 2026-11-04T22:06:58+07:00 |
| Work performed | 2026-11-04, UTC+07:00 |
| Contributor | Codex |
| Related task | [WORK-2026-11-04-002](2026-11-04-002-five-year-plan-site.md) |
| Git state | main; no project commits or remote; project files untracked |

## Objective

Replace the rejected iframe with native Report content, graph controls, charts,
coverage and evidence inspection in the existing Plan & Report Site. Preserve the
full Plan, public audience, historical artifacts and D018 collection pause.

## Changes and findings

- Opened existing Site source at `0128fd4f453d62596ac3158fbeb7d6e416a46957`
  using the Sites skill/helper. Removed iframe and `dist/report-explorer.html`.
- Integrated graph SVG, projections, conference/name filters, evidence inspector,
  entity browser, relationship/collection/topic/release charts, coverage table,
  JSON/CSV export and print controls directly into Report DOM. Shared Site palette
  and typography; namespaced `xr-` component IDs, `rp-` report prose IDs, scoped
  styles and Report-aware anchor routing preserve Plan behavior.
- Site source: `native-report.html`, `report-payload.json`,
  `dist/native-report.css`, `dist/native-report.js`, `build_site.py`,
  `dist/workspace.js` and `source-report.md`. Canonical editable sources are in
  the existing Sites source repository; checkout used:
  `/tmp/scientific-network-site-20261104`.
- Exact permitted historical payload retained: 399 nodes / 533 edges,
  `pilot-topic-d512d7239923`; SHA-256
  `fc30366f0f9e8a1748d87a030b882de076a4c438cab3881062f26fb8b50b3d8f`.
  Distinguish 402/538 unimported candidate and 2021–2025 planned target. Corrected
  native verification prose to date original task 007 graph/hash checks honestly.
- Updated [workflow](../sites-workflow.md), [visual report](../visual-report.md),
  [report prose](../../reports/site-report.md), [project plan](../project-plan.md),
  README, contributor guidance, roadmap and status. Added D020; preserved D019,
  finalized logs, original reports and earlier publication receipts/snapshots.
- Published the same public Site as **version 5**; source commit
  `cff18abcedc97a4963d44a5c98d66bd93cae557c`. Native deployment succeeded.
  [Receipt](../reference/sites-native-publication-2026-11-04.json),
  [Report snapshot](../reference/sites-progress-report-2026-11-04-native.md).

## Verification

Commands from project root unless another directory is stated. Local raw outputs
are under `reports/runs/WORK-2026-11-04-003/` (ignored).

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `PANDOC=/home/san/.cache/uv/archive-v0/WGuPJWVt0YVQCVdTXlt37/lib/python3.13/site-packages/pypandoc/files/pandoc python3 /tmp/scientific-network-site-20261104/build_site.py` | Passed, 0; 20 Plan sections, two tabs; 1,186,478 HTML bytes | Site source/build |
| `node --check /tmp/scientific-network-site-20261104/dist/native-report.js` and `node --check /tmp/scientific-network-site-20261104/dist/workspace.js` | Both passed, 0 | JavaScript syntax |
| `uv run pytest` | Passed, 0; **97 tests in 1.16s** | `pytest.log` |
| `uv run research-network schema` | Passed, 0 | `schema.log` |
| `uv run research-network validate --input tests/fixtures/synthetic_graph.json --output reports/runs/WORK-2026-11-04-003/synthetic-validation.json` | Passed, 0; synthetic structural-only result, no semantic claim | `synthetic-validation.json` |
| Static HTML/source/payload checks against previous Site HEAD and original report | Passed, 0; zero iframe/object/embed; 258 unique IDs; 20 Plan sections byte-identical; Plan source and safe payload unchanged; credential-marker scan passed | `site-static-checks.json` |
| Local browser graph/event checks | Passed; full 399/533, factual 379/369, coauthors 85/36, organizations 32/4; NeurIPS filter 78/105; empty search/reset, zoom/Fit, entity keyboard and affiliation source inspection | Browser readbacks |
| Charts/coverage/export/print-event checks | Passed; ten predicate bars; 34 series, 14 unresolved; JSON 399/533; filtered CSV 15 lines including header; beforeprint 34 rows, afterprint restored 14; four artifact downloads return 200 | Browser readbacks; actual OS print dialog/PDF export not exercised |
| Plan and navigation | Passed; all 20 sections, search 18 affiliation results, R10 schema, reversible checklist; pointer tab switching and actual ArrowRight key select Report; internal report anchors retain Report | Browser readbacks |
| Responsive browser QA | Passed at 1440/768/390px; no document overflow; mobile graph width 333px, stacked inspector; desktop and mobile screenshots inspected | `native-desktop.jpg`, `native-mobile.jpg` |
| Original artifact SHA-256 comparison | Passed, 0; **5,713** protected data/config/source/test/query/report/reference/finalized-log files unchanged | `protected-before.json`, `protected-after.json` |
| Sites helper package/push, native save/deploy | Passed, 0/succeeded; v5, commit and archive recorded | [Receipt](../reference/sites-native-publication-2026-11-04.json) |
| Live Site browser/get_site | Passed; public audience/title preserved; v5; native controls, 399 nodes, 533 edges, 20 Plan sections, zero embedded documents, no console errors | `live-browser-check.json` |

Initial screenshot/pointer calls timed out while browser visibility was hidden.
Selecting its existing tab restored visible state; subsequent pointer actions and
screenshots passed. One attempted screenshot copy exceeded shell argument length;
chunked copying saved the images. Helper packaging itself succeeded; its initial
wrapper JSON parse failed on the preceding archive-path line and was recovered
using the returned final JSON. No build/source retry or duplicate deployment.

## Decisions

[D020 — Native Report integration](../decisions.md#d020--native-report-integration-in-the-existing-site-2026-11-04).

## Open issues and limitations

No new research data, splits, pipeline changes or database imports. DB/source
services and semantic accuracy were not revalidated. All measured snapshots remain
historical 2023 evidence; the five-year edition count is unverified. Native Report
is a task-published snapshot, not automatic synchronization. Independent audit,
coverage and release gates remain unmet. No local preview job remains after
teardown. The Site source commit is published; project Git has no commit/remote.

## Next step

Continue five-year planning under D018: review edition/track/source policy and
cross-year leakage/resource design. Keep future material Report updates native
and publish through [the workflow](../sites-workflow.md). Wait for explicit later
pipeline/collection authorization.

## Corrections

None. This follow-up supersedes task 002's iframe presentation, preserving its
historical receipt, finalized work entry and source version.

## Final verification checkpoint

2026-11-04T22:07:27+07:00: relative documentation links pass; repository, Site source and dated
Report snapshot match byte-for-byte; v5 receipt succeeds; all 5,713 protected
files remain unchanged. Site checkout has clean Git status. All checks exit 0.
