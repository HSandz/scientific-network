# WORK-2026-11-07-007 — MICCAI 2022 official source-route follow-up

| Field | Value |
| --- | --- |
| Status | partial |
| Recorded | 2026-11-07T18:07:39+07:00 |
| Work performed | 2026-11-07, Asia/Bangkok (UTC+07:00) |
| Contributor | Codex |
| Related task | [WORK-2026-11-07-006](2026-11-07-006-miccai-2024-source-closure.md) |
| Git state | main at 66e692d; extensive uncommitted repository work preserved; Site source pushed separately as 1882017c0d4960c04b3493c2e0e0ab1e5e19fc9d |

## Objective

Continue P01 from roster v10 by checking whether MICCAI 2022 has another
complete, permitted official roster route that resolves the prior accepted-list
access failure and Springer counter discrepancy. Do not promote the edition
unless the full accepted main-research roster, track boundary and chapter mapping
are supported. Preserve all existing rosters and frozen assignments.

## Changes and findings

- Opened a bounded source-route follow-up using [the completion plan](../pregraph-completion-plan.md),
  [source triage](../five-year-source-triage.md), D032/D033, roster v10 and its
  immutable source-correction overlays.
- At task start, no new source capture, roster, edition disposition, split,
  enrichment or graph output had been produced.
- Direct official captures later recovered the Society accepted-paper index (573
  unique detail records), its category page (572), eight Springer main volumes
  (576 unique chapter DOI records), and two official program PDFs. The volume
  descriptions say 574 revised full papers; the refreshed series index says 576.
  A normalized-title join found 558 unique pairs, leaving 15 Society records and
  18 Springer chapters outside that join, including three correction notices. The
  program documents did not resolve the count conflict; no byline adjudication or
  missing-paper inference was made.
- The edition remains unresolved and ineligible. V10, all frozen assignments and
  v2-bound diagnostic/pregraph inputs remain unchanged. Program PDFs are local
  source evidence; no paper PDFs were downloaded or published, and no roster,
  split, enrichment or graph output was created.
- Corrected the source-triage introduction to distinguish program PDFs from paper
  PDFs, refreshed the mutable Report, and saved the published report snapshot.
- Published the D034 aggregate update as Site version 16, preserving project ID,
  public audience, URL, Plan and historical graph payload.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| Read repository handoff, plan, schema, scope/configuration, source triage, latest task entries, Site workflow and Git state | completed | README, docs/status.md, docs/work-log/README.md, docs/pregraph-completion-plan.md, docs/project-plan.md, docs/graph-schema.md, configs/corpus-five-year-v10.yaml, configs/five-year-pregraph-v3.yaml, WORK-006 and prior MICCAI/AAMAS/ICLR entries |
| Current official roster baseline | v10 remains current: 98 eligible editions, 22 unresolved roster/adapter editions, 40 access-unavailable editions; 94,857 observations, 91,355 included, 3,502 excluded | reports/five-year-source-recovery-v10.md; reports/five-year-edition-ledger-v10.csv |
| Site publication checkpoint at task start | version 15 deployed at the existing public URL; original graph payload and historical explorer retained | docs/reference/sites-source-recovery-publication-2026-11-07.json |
| MICCAI 2022 official-route reconciliation | 573 Society detail records / 572 category records; 576 Springer DOI records; 574 revised full-paper count; 558 unique exact-title pairs; unresolved | source-corrections v9 and ignored captures under reports/runs/WORK-2026-11-07-007/ |
| Source-manifest hash audit | passed; all 37 official source captures match source-corrections v9; exit 0 | reports/runs/WORK-2026-11-07-007/source-hash-audit.json; manifest SHA-256 `caf7707b759bf235309366fd40a2dc389757ecd924f3d29cc694917503cfc053` |
| `python3 build_site.py` with default environment | failed; Pandoc is absent (`FileNotFoundError`), exit 1 | Initial build attempt; no Site source or system dependency was changed by this failure |
| `PANDOC=/tmp/scientific-network-pandoc-wrapper python3 build_site.py` | passed with isolated Pandoc 3.1.3; 20 Plan sections, two tabs, 1,226,436-byte HTML; exit 0 | `/tmp`-only Pandoc package/data/runtime; reports/runs/WORK-2026-11-07-007/site-static-audit.json |
| Site static audit | passed; 269 unique IDs, no duplicates, 22/22 downloads resolve, no embedded frames, D034 content present, historical payload hash and 399/533 counts unchanged; exit 0 | reports/runs/WORK-2026-11-07-007/site-static-audit.json |
| Local Site browser QA | passed for D034 content, tabs, Ctrl+K search (18 affiliation results), result navigation, factual filter (379/369) and reset (399/533), mobile report width; zero new local console messages | reports/runs/WORK-2026-11-07-007/site-browser-qa.json; all-history console also contained warnings and one `loadMermaid` error from the previously viewed official category page |
| Supported Sites source helper | passed; pushed and packaged exact Site source at `1882017c0d4960c04b3493c2e0e0ab1e5e19fc9d`; exit 0 | Local archive SHA-256 `ed9b8d1296e5a9aaa070ec828f39dac18762df1a50ffd504f5a25848730b2a87` |
| Sites save/deploy and `get_site` verification | version 16 deployment succeeded; live Site active/public at the unchanged project ID and URL | docs/reference/sites-miccai-2022-followup-publication-2026-11-07.json |
| `uv run pytest` | not run; no Python code changed | Not applicable |

## Decisions

[D034](../decisions.md#d034--miccai-2022-official-route-follow-up-2026-11-07) preserves the unresolved disposition. D022/D015 and D032–D034 remain in force; no corpus, track, split, threshold or graph semantics changed.

## Open issues and limitations

P01 remains incomplete. MICCAI 2022, AAMAS 2023, five ICLR editions, 15 ICDM/ICRA/IROS adapter gaps, and 40 publisher-access candidates remain unresolved. The 62 incomplete candidates keep the full-scope gate failed. P02 remains no-go for broader enrichment; all frozen assignments and v2-bound diagnostic/pregraph inputs are protected. Program PDFs are captured locally; no paper PDFs were downloaded. A prior-source-page console error is recorded in the browser QA artifact and does not come from the local Site.

## Next step

Continue P01 with another complete, permitted official roster route from [the completion plan](../pregraph-completion-plan.md). Keep roster v10, every frozen assignment and v2-bound inputs unchanged until evidence supports a new version; P02 stays no-go while its feasibility gates remain unmet.

## Corrections

None.
