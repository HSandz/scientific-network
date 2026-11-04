# WORK-2026-11-04-002 — Five-year plan and unified Site

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-04 21:35 +07:00 (Asia/Bangkok) |
| Finalized | 2026-11-04 21:54 +0700 (Asia/Bangkok) |
| Work performed | 2026-11-04 |
| Contributor | Codex |
| Related task | [Evidence review](2026-11-04-001-evidence-review.md); [venue/Sites plan](2026-11-03-005-expand-conference-plan.md) |
| Git state | Project main, no commits/remote; files untracked. Separate existing Site source committed/pushed for publication; no project commit/push |

## Objective

Extend the core plan to 2021–2025, update related current files, and merge Plan
and evolving Report into the existing renamed Site. No pipeline implementation
or research collection. Preserve historical configs, source snapshots, data,
held-out assignments, graphs and measured outcomes.

## Changes and findings

- **D018:** five core years, same 34 flagship series. New planning-only
  `configs/conference-scope-2021-2025.yaml` has **170 unique venue–year review
  candidates**, all unverified for the new scope. This is not a confirmed edition
  count. Implementation/collection disabled; no executable `editions` list.
- Updated AGENTS, README, project/conference/temporal scope, roadmap, schema
  temporal notes, source policy, dictionary, evaluation, annotation, setup, team,
  historical workflow notices, visual-report guidance and final-report outline.
  Added [five-year design](../five-year-scope.md), [Site workflow](../sites-workflow.md)
  and mutable [publishable progress report](../../reports/site-report.md).
- Planned cross-year work versions/leakage protection, edition-year authority,
  annual/cumulative support recomputation, citation-age/snapshot controls and
  prospective annotation/resource estimates. Quality gates/predicates unchanged;
  do not multiply old quotas/targets by five. Historical 2023 outcomes stay separate.
- **D019:** reused Site `appgprj_6ae7698b8b2881919d49df2426c517a2`, retaining URL and
  public audience. Renamed **AI Research Network — Plan & Report (2021–2025)**.
  Retained all **20 Plan sections** and existing schema/search/checklist tools;
  added accessible Plan/Report tabs, direct hashes, downloads and measured Report.
- Report embeds the unchanged 399-node / 533-edge 2023 explorer and reports the
  402/538 local candidate separately. Its source is `source-report.md` in the Site
  repository, mirrored by `reports/site-report.md`. Update/publish task-driven
  snapshots after material iterations; no automatic sync/schedule/live DB path.
- Published **version 4**, source commit `0128fd4f453d62596ac3158fbeb7d6e416a46957`,
  deployment `appgdep_6aeb45e058088191acb295438cc5dcaf` succeeded at
  **2026-11-04 21:49:26 +07:00**. Native readback confirms renamed title, same
  public audience, same URL and latest version 4. [Receipt](../reference/sites-publication-2026-11-04.json).
  [Plan snapshot](../reference/sites-project-plan-2026-11-04.md),
  [Report snapshot](../reference/sites-progress-report-2026-11-04.md).
- No pipeline source/test/legacy config edits, new academic-source requests,
  split creation, data enrichment or graph/database calls. Site source changes
  implement the requested presentation only. No new five-year measured data.

## Verification

Commands ran from `/home/san/Code/scientific-network`, except Site helper/build
commands from `/tmp/scientific-network-site-20261104` as indicated. Raw artifacts
are under `reports/runs/WORK-2026-11-04-002/` (ignored).

| Command/check | Outcome / exit code | Evidence |
| --- | --- | --- |
| `uv run pytest -q` | 0; **97 passed** in 1.40s, offline; no collection/models | `pytest.log` |
| `uv run research-network schema` | 0; ten predicates unchanged | `schema.json` |
| Parse new planning YAML; 34 unique series × five unique years; verify status/authorization flags and absence of executable editions | 0; 170 review slots, confirmed edition count null, all pending | `planning-preservation.json` |
| `PANDOC=<existing cached executable> python3 /tmp/scientific-network-site-20261104/build_site.py` | 0; 20 Plan sections, two tabs, full Markdown downloads | `site-build-final.log`; no pipeline build changes |
| `node --check` on Site `dist/app.js` and `dist/workspace.js` | 0 each | Syntax checked after final Site source change |
| Local browser: tabs, direct Report hash, keyboard arrows, plan search/schema/checklist, six download URLs | Passed; 20 sections retained, search finds 2021, schema R8 works, checklist toggles/restores, all six endpoints 200 | `site-qa.json`; actual controls also inspected through browser |
| Local browser at 1440, 768 and 390px, both tabs | All six layouts have no horizontal overflow; no JS page errors | `site-qa.json`; mobile screenshot inspected |
| Live Site readback, tab DOM events, explorer projections | Correct title/scope/two panels; rendered 399 full, 379 factual, 85 researchers, 32 organizations | `site-live-confirmed.json`; desktop screenshot inspected |
| `uv run python reports/runs/WORK-2026-11-04-002/final-checks.py` | 0; **2,796 protected artifacts unchanged**, 22 current docs have valid local links, published-source snapshots match, old explorer byte-identical | `final-checks.json` |
| Configured secrets against 468 Git-eligible files and Site/archive payload | 0; two configured secret values checked, no leaks | `final-checks.json`; no token/key values recorded |
| Sites supported source helper open/package; save/deploy; native `get_site` readback | Commit pushed; matching archive saved as v4; publication **succeeded**; title/public audience/URL verified | [sanitized receipt](../reference/sites-publication-2026-11-04.json) |
| Research collection, new splits, DB integrity/import, semantic audit, five-year NLP/analysis | **Not run**, per explicit planning-only request | Existing measurements remain historical; no new scientific score |

The protected baseline excludes the two intentionally updated current planning
files `docs/work-log/README.md` and `reports/final-report/outline.md`; all other
old protected files are unchanged. Current documentation outside that baseline
was intentionally revised. No historical finalized entry or result was rewritten.

Failures and retries: initial preservation check included those two mutable files
and correctly failed its overbroad expectation; the explicit planning-file exclusion
fixed the checker. Initial browser QA used ambiguous SVG `title` / incorrect node
class selectors; corrected selectors verified the rendered explorer. Live
Playwright actionability waits timed out for scroll/click despite correct visible
content; live DOM event/readback and screenshots subsequently verified both tabs
and all four projections. Local pointer/keyboard tests passed. The first package
attempt stopped because the short-lived Site credential expired; renewed through
Sites and successfully packaged/pushed without persisting/exposing tokens.

## Decisions

[D018 — Five-year core scope, planning only](../decisions.md#d018--five-year-core-scope-planning-only-2026-11-04)
and [D019 — Existing Site for Plan and evolving Report](../decisions.md#d019--existing-site-for-plan-and-evolving-report-2026-11-04).
No label/predicate/quality-threshold change. New years require explicit future
implementation/collection instruction; D015 remains historical authorization.

## Open issues and limitations

Actual edition count/source access for 2021–2025 is unverified. No new five-year
config execution, collection, split or scientific analysis exists. Current data
remain partial 2023 diagnostics; candidate not imported; independent semantic
accuracy/recall/F1 remain unmeasured. Site updates are task-driven publications,
not unattended sync, and do not replace the final ten-page course report. Deadline,
review capacity, lecturer confirmations, member details/license and project Git
remote remain unresolved. No research jobs running; owned local preview stopped
at final handoff. Site source/history are remote; project files remain uncommitted.

## Next step

Review the edition matrix/track policy, cross-year leakage and reviewer/resource
budgets as planning. Acceptance: no assumed edition totals, no changes to frozen
memberships, and explicit annual/cumulative/citation-age rules. Wait for a later
implementation/collection instruction before pipeline work. After the next material
project iteration, update the same Site's Report from versioned evidence using
[the publishing workflow](../sites-workflow.md), preserving Plan and audience.

## Corrections

None. Future corrections must be dated or linked to a superseding task.

## Checkpoint — 2026-11-04 21:46 +07:00

Created planning-only 34-series/five-year registry with 170 unverified review slots;
updated current scope/evaluation/annotation/report docs and agent instructions.
Preserved historical executable configs, raw/frozen data and reports. Existing
public Site source opened from commit 532bf27a85185a1a4ad847dc872aa500f4f2ddbf at
`/tmp/scientific-network-site-20261104`; no publication yet. Full 20-section Plan
retained; added Report with measured 2023 snapshots and the existing explorer.
Local browser verified tabs, direct Report hash, keyboard switching, six mobile/
desktop layouts without horizontal overflow, plan search/schema/checklist and six
download endpoints. Initial QA used an ambiguous SVG `title` selector; corrected
to `head title` and reran successfully. 97 repository tests passed. No new research
collection, pipeline source edits, split generation or database calls performed.
