# Shared Plan & Report Site

Use the existing public Site, **AI Research Network — Plan & Report (2021–2025)**:
<https://ai-research-network-plan.hazy-tern-8113.chatgpt.site>.
Project ID: `appgprj_6ae7698b8b2881919d49df2426c517a2`. Keep its identity, URL,
source history and audience. Do not create a second Site or change access while
updating content. D019 records the requested consolidation; D020 requires native Report integration. The initial two-tab publication is
**version 4**, with its [historical receipt](reference/sites-publication-2026-11-04.json).
The native integration began with **version 5**;
[historical receipt](reference/sites-native-publication-2026-11-04.json).
The deadline/execution-plan update is **version 6**;
[historical receipt](reference/sites-execution-plan-publication-2026-11-06.json).
The first five-year roster collection update is **version 7**;
[historical receipt](reference/sites-collection-publication-2026-11-06.json).
The corrected roster and diagnostic metadata update is **version 10**;
[historical receipt](reference/sites-diagnostics-corrected-publication-2026-11-06.json).
Selective PDF/header development results are **version 11**;
[historical receipt](reference/sites-headers-publication-2026-11-06.json).
Reviewed development identity/affiliation support is **version 12**;
[historical receipt](reference/sites-corroboration-publication-2026-11-06.json).
Pregraph diagnostic preparation and failed full-readiness gates are **version 13**;
[historical receipt](reference/sites-pregraph-publication-2026-11-06.json).
Official OJS source recovery (88 eligible editions / 85,802 included records) is
**version 14**; [historical receipt](reference/sites-source-recovery-publication-2026-11-06.json).
Roster v10 and the MICCAI 2024 reconciliation (98 eligible editions / 91,355
included records) are **version 15**; [historical receipt](reference/sites-source-recovery-publication-2026-11-07.json),
[Plan snapshot](reference/sites-source-recovery-plan-2026-11-07.md), and
[Report snapshot](reference/sites-source-recovery-report-2026-11-07.md).
The MICCAI 2022 official-source follow-up (D034; edition unresolved and roster
v10 unchanged) is **version 16**; [current receipt](reference/sites-miccai-2022-followup-publication-2026-11-07.json)
and [Report snapshot](reference/sites-miccai-2022-followup-report-2026-11-07.md).
Local browser QA for v16 confirmed the D034 text, tabs, keyboard search, graph
projection and mobile layout. Escape still does not close the search dialog
despite its hint; the keyboard-accessible Close search button works. This UI
issue remains open.
The AAMAS 2023 official identifier scan (WORK-008; edition unresolved, roster
v10 unchanged) is **version 17**; [publication receipt](reference/sites-aamas-2023-followup-publication-2026-11-07.json)
and [Report snapshot](reference/sites-aamas-2023-followup-report-2026-11-07.md).
The ICLR API access retry (WORK-009; challenge-blocked, all five years unresolved)
is **version 18**; [publication receipt](reference/sites-iclr-access-retry-publication-2026-11-07.json)
and [Report snapshot](reference/sites-iclr-access-retry-report-2026-11-07.md).
Live browser verification confirmed the Report tab, blocker text, zero embedded
documents and no console warnings/errors.
Version 8's [receipt](reference/sites-diagnostics-publication-2026-11-06.json)
and source snapshots remain historical; [v9](reference/sites-diagnostics-final-publication-2026-11-06.json)
records replay fixes and 120 tests. V10 corrects currency rendering; counts are unchanged.

## Two views, one publication

- **Plan** (`#plan`): full specification, current 2021–2025 scope, requirements,
  pipeline design, evaluation, workload and next tasks. State that D022 authorizes staged collection; five-year roster discovery has
  started and new split/enrichment/graph stages require their prerequisite checks.
- **Report** (`#report`): dated measured progress, coverage, five-year roster progress, loaded-versus-candidate
  versions, quality gaps, history and the existing interactive graph explorer.
  The explorer retains its 399/533 2023 snapshot; report the 402/538 local candidate
  separately until a matching new explorer is authorized/generated. The graph,
  charts, filters, coverage table and evidence inspector are native Site components
  in the Report DOM, not an iframe or embedded standalone document (D020).

The Site report does not replace the final ≥10-page course report. It does not
query localhost Neo4j, read `.env` or automatically synchronize repository files.
No cloud schedule or unattended data path is configured. Updates are task-driven
publications; existing results can be published without new research collection.

## Update after material project iterations

1. Finalize measured artifacts and the work entry. Verify graph/config/source
   versions; distinguish fresh checks from dated historical results. Update
   `docs/status.md` and the mutable `reports/site-report.md`.
2. Through the **Sites skill**, call `get_site` for this project, confirm its
   audience, obtain a fresh repository write credential and open source with the
   supported helper. Keep tokens only in session memory/stdin, never files/logs.
3. Update Site `source-plan.md` when the plan changes and `source-report.md` for
   measured progress. Preserve old source commits. Copy only permitted artifacts
   such as summary JSON and the unchanged safe graph payload after checking
   hashes/disclosure. Keep the standalone HTML as an offline artifact, not a Site
   embed. In Site source, `native-report.html`, `report-payload.json` and
   `dist/native-report.{css,js}` implement the native report; `build_site.py`
   combines them with the full Plan and `source-report.md`. Namespace component
   IDs (`xr-`) and prose headings (`rp-`), scope report CSS, and route report
   anchors through `dist/workspace.js`.
   Exclude raw PDFs, full abstracts, credentials, private annotations and restricted text.
4. Rebuild static output. Check both tabs, direct hashes, keyboard/mobile behavior,
   downloads, Plan search/schema/checklist and native explorer. Assert zero
   iframe/object/embed elements in built HTML and the native Plan/Report panels,
   unique IDs and correct payload/Plan content. Hosted infrastructure may inject
   an extra frame outside those panels; record it separately rather than attributing
   it to the Report or removing platform behavior. Separate targets
   from results. Do not claim tests/services were rerun when checks are historical.
5. Use the source helper to commit/push exact Site source and package the matching
   build. Save/deploy that version through Sites with the current audience. Report
   publication failure honestly; local edits alone do not update the live Site.
6. Save a sanitized receipt under `docs/reference/`: title, URL, project/version/
   deployment IDs, source commit/hash, artifact versions and work ID. Preserve
   older receipts/snapshots. Record the verified outcome in status/work history.

Routine progress updates preserve Plan content, scope and audience. Do not replace
the full plan with a short summary. If no new measurements exist, state that; do
not extrapolate five-year counts from diagnostics. Do not add an unattended
schedule without a separate user request and supported data path.
