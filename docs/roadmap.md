# Implementation roadmap

**Current instruction (D022): staged 2021–2025 collection authorized.**
Official roster discovery v2, OJS recovery v7, and source-roster overlays v8/v9/v10,
leakage triage, frozen diagnostic sampling, bounded metadata acquisition and
selective development PDF/header source triage
are implemented. Bounded development identity/affiliation support is now staged
under D025; full five-year resolution and graph stages remain pending. See
[collection workflow](five-year-collection.md) and [current status](status.md).
Older execution sequences below remain historical.

## Current iteration — P01 ICDM 2021 source follow-up (WORK-018)

The official accepted list has 197 unique IDs (98 Regular Papers, 99 Short
Papers), all present in the official schedule. The schedule has 42 additional
IDs in separately named workshop events (40) and a PhD Panel (2). The conference
call states the accepted papers appear in IEEE Computer Society proceedings,
but a local IEEE Xplore proceedings request returned HTTP 418 and no full
crosswalk was captured. The University copyright policy does not establish who
owns or may authorize bulk reuse of this conference metadata. ICDM 2021 remains
unresolved in v10; no roster or frozen assignment changed. P01 retains 62
incomplete candidates; P02 remains no-go with one reviewer of unknown hours and
a second independent reviewer unconfirmed. The existing public Site remains v18;
its helper host still fails DNS, so this local Report refresh is unpublished.
See [D036](decisions.md#d036--icdm-2021-official-source-hold-2026-11-07),
[source triage](five-year-source-triage.md#icdm-2021-official-accepted-list-follow-up-work-018),
and [WORK-018](work-log/2026-11-07-018-icdm-2021-source-closure.md).

## Previous iteration — P01 ACM Multimedia 2024 source follow-up (WORK-017)

The official accepted-ID file has 1,149 unique numeric values; the official
research-track statistics report 1,150 acceptances. The regular-papers page capture is
a JavaScript shell, the file's track coverage and ID schema are undefined, no
complete accepted-to-proceedings join was captured, and bulk reuse terms remain
unverified. ACM Multimedia 2024 stays `access_unavailable` in v10; no new roster
or eligibility change was made. All 42 v10 hashes and five frozen-input hashes
verify, preserving 76,629 assignments including 1,095 tests. P01 still has 62
incomplete candidates. P02 remains no-go with one reviewer of unknown hours and
a second independent reviewer unconfirmed. The approved Site helper failed before
checkout on DNS, so v18 remains live and the local Report refresh is unpublished.
See [D035](decisions.md#d035--acm-multimedia-2024-official-source-hold-2026-11-07),
[source triage](five-year-source-triage.md#acm-multimedia-2024-official-source-follow-up-work-017),
and [WORK-017](work-log/2026-11-07-017-p01-acmmm-2024-source-closure.md).

## Previous iteration — P09 component evaluation contracts (WORK-016)

Implemented the offline `evaluate` command for frozen component frames, with
double-review/adjudication joins, sampling-weighted and per-stratum metrics,
topic macro/per-label scores, resolution pair-type errors, reviewer agreement,
and explicit core-frame coverage. Synthetic packets are protocol-only. Real runs
require a reserved test frame, frozen quality config and complete release-core
coverage denominator; the current config is proposed and no independent labels
are available. P07 remains incomplete and results cannot certify release quality.
The authorized Site update could not start because the supported source helper's
Git host did not resolve; the public Site remains v18. See [evaluation protocol](evaluation.md) and
[WORK-016](work-log/2026-11-07-016-p09-evaluation-contracts.md).

## Previous iteration — P09 named-projection analysis (WORK-015)

`analyze` now validates a graph artifact and reports five named projection metrics,
weighted centrality, and seeded Louvain communities for collaboration networks.
Non-synthetic graphs require configured size gates, a matching post-build receipt,
and a frozen evidence-filter config. The synthetic smoke is protocol-only. A
post-WORK-015 regression check also added a canonical strict-filter hash. Citation-
age/coverage analyses, figures, business findings and release certification
remain pending. See [analysis workflow](analysis.md) and
[WORK-015](work-log/2026-11-07-015-offline-analysis-stage.md).

## Previous iteration — P09 edge-audit packet utilities (WORK-014)

Standalone `freeze-audit-sample` and `score-edge-audit` commands now prepare and
score a deterministic, hash-bound global/per-type review packet. Synthetic use is
protocol-only; a non-synthetic sample requires a matching post-build readiness
receipt and passing size gates. This is not the full `evaluate` stage: component
recall/coverage, real independent labels, final analysis and release certification
remain pending. P01 remains incomplete and P02 remains no-go. See the [evaluation
protocol](evaluation.md) and [WORK-014](work-log/2026-11-07-014-p09-offline-contracts.md).

## Previous iteration — ICLR official source-route review (WORK-003)

- The official OpenReview venue index lists conference groups for 2021–2025.
  ICLR's official Proceedings FAQ routes accepted-paper access through OpenReview.
- The 2024 proceedings/fact-sheet counts agree at 2,260. The 2025 proceedings
  book and hosted draft fact sheet differ at 3,703 / 3,704.
- Local OpenReview API access returned HTTP 403; local proceedings access failed
  DNS. No hash-bound roster was produced; all five ICLR years remain unresolved.
  V8's 94 eligible editions and 66 incomplete candidates are unchanged. No
  sample, enrichment, graph or database work occurred.
- [Detailed source triage](five-year-source-triage.md#iclr-official-route-and-roster-access-check-work-003)
  and [work entry](work-log/2026-11-07-003-iclr-source-review.md).

## Previous checkpoint — MICCAI 2024 source reconciliation (D033 / WORK-006)

- V10 reconciles 856 Society accepted papers with 856 distinct chapters across
  all 12 Springer main volumes; 836 exact-title and 20 title/byline matches. One
  publisher correction chapter is excluded as nonresearch.
- Current ledger: **98 eligible editions / 91,355 included of 94,857 observations**;
  22 unresolved roster/adapter and 40 access-unavailable candidates remain. All
  76,629 assignments, including 1,095 tests, remain guarded. Fresh isolated replay
  matches all 42 output hashes; the full offline suite outcome is in WORK-006.
- No new split, enrichment, PDF, graph or database operation. P01 remains partial;
  P02 remains no-go for broader enrichment. The v2-bound diagnostic/pregraph
  inputs remain unchanged.
- [V10 report](../reports/five-year-source-recovery-v10.md), [ledger](../reports/five-year-edition-ledger-v10.csv),
  [source triage](five-year-source-triage.md), and [work entry](work-log/2026-11-07-006-miccai-2024-source-closure.md).

## Previous iteration — MICCAI official roster closure (D032 / WORK-004)

- V9 added official MICCAI title/record rosters for 2021 (531), 2023 (730) and
  2025 (1,027); v10 subsequently reconciled 2024. MICCAI 2022 remains unresolved:
  the local accepted-list request returned HTTP 522, and Springer reports 574 full
  papers versus an index counter of 576.
- The v9 ledger was **97 eligible editions / 90,499 included of 94,000 observations**;
  23 unresolved roster/adapter and 40 access-unavailable candidates remained.
  All 76,629 assignments, including 1,095 tests, remain guarded. **198 offline
  tests passed**, including five focused MICCAI parser tests.
- No new split, enrichment, PDF, graph or database operation. P01 remains partial;
  P02 remains no-go for broader enrichment. The v2-bound diagnostic/pregraph
  inputs remain unchanged; public Site remains v14.
- [V9 report](../reports/five-year-source-recovery-v9.md), [ledger](../reports/five-year-edition-ledger-v9.csv),
  [source triage](five-year-source-triage.md) and [work entry](work-log/2026-11-07-004-miccai-source-review.md).

## Previous iteration — AAMAS official roster closure (D031 / WORK-002)

- Roster v8 adds four eligible AAMAS editions using the official named
  main-research sections; AAMAS 2023 stays unresolved pending title/byline/ID
  reconciliation. Detailed rosters remain local under source-use restrictions.
- Current roster: **94 eligible editions / 88,211 included records** across
  91,712 observations. The remaining 66 candidates are 26 unresolved roster/adapter
  editions and 40 access-unavailable editions.
- All **76,629 frozen assignments**, including **1,095 tests**, remain guarded.
  The replay matched all 34 recorded output hashes and exits 1 while 66 candidates
  remain incomplete. **193 offline tests passed.** No split, enrichment, merge,
  graph or database operation occurred.
- P01 remains incomplete. P02 remains no-go for broader enrichment; the current
  budget remains zero pending population, design, resource, storage and reviewer
  measurements. The diagnostic/pregraph inputs remain bound to v2.
- [Measured v8 report](../reports/five-year-source-recovery-v8.md),
  [ledger](../reports/five-year-edition-ledger-v8.csv), and
  [source triage](five-year-source-triage.md).

## Historical official edition route closure (D030 / WORK-001)

- Roster v7 applies official evidence to the 11 route candidates left after v6:
  ten have verified no-edition findings and the COLING 2024 joint LREC-COLING
  roster is included once under COLING.
- Current roster: **90 eligible editions / 87,404 included records** across
  90,163 observations. The remaining 70 candidates are 30 unsupported-adapter
  editions and 40 access-unavailable editions.
- All **76,629 frozen assignments**, including **1,095 tests**, remain guarded.
  The fresh offline replay matches all recorded output hashes and exits 1 while
  those 70 candidates remain incomplete. **187 offline tests passed.** No new
  split, enrichment, canonical merge, graph or database operation occurred.
- P01 and overall pregraph readiness remain incomplete. P02 remains no-go for
  broader enrichment; the current budget is zero until population, design,
  resource, storage and reviewer prerequisites can be measured.
- [Measured v7 report](../reports/five-year-source-recovery-v7.md),
  [ledger](../reports/five-year-edition-ledger-v7.csv), and
  [source triage](five-year-source-triage.md).

## Historical pregraph completion plan and execution checkpoint (D028 / WORK-009)

The [detailed prerequisite plan](pregraph-completion-plan.md) orders P00–P10:
integrity, official scope closure, feasibility, prospective sampling, development
calibration, production evidence, canonical support, independent evaluation,
support preflight, tooling/reproduction and an immutable readiness decision.
The plan-writing iteration was documentation only. P00/P01 execution has since
started: v6 resolved the ICAPS 2025 track question, v7 closed ten no-edition
routes plus the COLING 2024 joint-event mapping, v8 added four AAMAS rosters and
v9 added three MICCAI rosters.
Source closure remains incomplete;
P02 is a no-go for broader enrichment. No new sample, enrichment, service
operation, graph construction/import, or Site publication was performed in
WORK-009. All twelve preparation gates must pass before final construction. The
final edge audit, graph analyses and final results report follow construction.

## Historical ICAPS 2025 source correction (D029)

- Official accepted-paper links and the main-call/policy evidence resolve the 48
  previously reviewed ICAPS 2025 main-research records; three position papers and
  front matter remain excluded under existing policy.
- Roster v6 at that checkpoint: **89 eligible editions / 85,850 included**; 81 edition gaps.
  All 76,629 frozen assignments, including 1,095 tests, remain guarded.
- Offline source-disabled replay returns exit 1 for remaining edition gaps; its
  roster/leakage content matches the recorded v6 output after timestamp normalization.
  **181 offline tests passed.** No enrichment, split, graph or database operation.
- P01 remains partial. P02 no-go holds until population, prospective frame, live
  resource/storage measurements and actual reviewer capacity are known.
- [Measured v6 report](../reports/five-year-source-recovery-v6.md) and
  [feasibility checkpoint](../reports/five-year-pregraph-feasibility-v1.md).

## Historical official source recovery (D027; v5)

- Implemented bounded OJS archive/issue parsing for AAAI and ICAPS, with exact
  edition/section evidence, archive completeness, partial-failure withholding and
  immutable versioned replays. V5 and v3/v4 outputs remain preserved.
- **88 eligible editions / 85,802 included records**, up from 79/75,655.
  All 170 candidates remain; 82 gaps including ICAPS 2025 track categories.
- **177 tests**, three source-disabled replays; 8,104 protected artifacts and 562
  source objects verified. No new enrichment, split, accepted identity or graph.
- E01/E02 remain partial across the full scope. Existing diagnostic/pregraph
  freezes unchanged. Next: remaining accessible routes/track corroboration and a
  budgeted supplemental design before enrichment; independent labels still needed.
- [Measured source recovery](../reports/five-year-source-recovery-v5.md).

## Pregraph evidence preparation (D026)

- Implemented `prepare-pregraph`: offline known-frame work guards, paper/organization
  staging, literal topic/citation candidates, complete old/current claim dispositions
  and immutable freeze receipts. Current version v3; no graph construction/import.
- 19 source reviews; 55 accepted/13 withheld sources; 10 people, 11 authorships,
  12 triples and nine organizations. 17 topic candidates remain unaccepted.
- 156 tests; preserved 7,895 artifacts; verified 369 sources. Original tests, source
  failures and old snapshots unchanged. Blank development reviewer packets ready.
- **Full pregraph readiness fails:** 91 edition gaps, limited collection/global work
  resolution, low identity/affiliation/topic coverage and missing independent labels.
  E01/E03/E05/E06 are not complete across the planned population. E07 has not started.
- [Measured gates and next dependencies](../reports/five-year-pregraph-v3.md).

## Historical reviewed development support (D025)

- Five input/PDF-bound printed-source overlays; 49/68 source-eligible papers.
- 84 bounded public ORCID responses; 10 corroborated people, 11 authorships across
  nine papers, one reviewed author–paper–organization triple; 345 review rows.
- 145 offline tests; identical replay and network-disabled replay; 7,645 protected
  files and 362 source objects verified. All frozen tests preserved.
- GROBID and both Neo4j services healthy before/after; counts remain 154/211 and
  399/533. No five-year graph materialization/import, no independent quality score.
- Next E06: review remaining byline/crosswalk conflicts and printed mappings;
  freeze accepted support before E07 isolated graph work. [Measured report](../reports/five-year-corroboration-v1.md).

## Historical selective PDF headers and source candidates (D024)

- E05: 68 frozen development PDFs cached, 66 parsed, two RSS 2025 failures retained
  for OCR/alternate conversion. Metadata and every old/new held-out ID preserved.
- E06 development triage: 255 affiliation candidates / 56 exact author-specific
  metadata matches; none accepted. Five printed pages inspected; MLSys full byline
  corroborated, COLT editors detected in parsed authors, source gaps retained.
- 130 offline tests; identical replay summaries; 7,297 protected files unchanged;
  269 evidence objects verified; no new OpenAlex requests or graph writes.
- Docker was healthy before collection, then became unreachable. Post-run service
  recovery/checks belong in the current work entry, not a presumed healthy state.
- Next: correct source/header gaps, canonical works and public-ORCID corroboration,
  then exact printed-marker acceptance before an isolated graph. Independent audit,
  analysis and final report remain pending. [Measured stage](../reports/five-year-headers-v1.md).

## Historical corrected rosters and frozen diagnostics (D023)

- E01/E02: 79 eligible editions; 78,321 records, 75,655 included; 91 candidates
  unresolved/unavailable. Preserve v1 outcomes and all previous configs/data.
- E03/E04: preliminary version guards and frozen 34-stratum development design;
  68 new diagnostics, 170 reserved tests; original/expanded memberships unchanged.
- E05 metadata-only tranche: 67/68 acquired, 67 abstracts, 36 strict work matches;
  one byline conflict withheld. No new PDFs, identities, graphs or accuracy result.
- 120 tests passed; Neo4j/GROBID healthy. Native Site Report v10 reflects separate
  roster/metadata progress; its graph explorer remains historical 2023 data.
- Next: selective PDFs/headers and source-specific identity/affiliation review,
  then accepted evidence and an isolated graph. Independent audit/report still pending.

## Historical first five-year roster iteration (D022)

- E01/E02: roster-only config, verified catalog routing, per-edition checkpoints,
  full 170-candidate ledger and immutable downloads implemented; **73,714 records**,
  **67 eligible editions / 65,523 included records within those editions**.
- E03: preliminary offline leakage triage; all 14,909 previous assignments retained.
  New canonical work crosswalk and prospective E04 sampling remain incomplete.
- Tests: 108 passed; discovery/replay intentionally return 1 for unresolved gaps.
- E05–E08 have not run for the five-year corpus. E09 progress reporting/Site v7 is
  updated; final course report and independent audit remain incomplete.
- Next: versioned NeurIPS 2025/ECVA/RSS/KR track-layout fixes and identifier review,
  then prospective diagnostic design before bounded metadata/PDF acquisition.
  [Measured results](../reports/five-year-collection-v1.md).

## Already available

- Git repository, contributor instructions, source-plan snapshot and documentation.
- Locked Python package, optional preview app, Compose configuration and Cypher.
- Candidate corpus/quality/topic/analysis configs, small JSON contracts, schema CLI,
  structural validator, per-paper collaboration helpers and interval utility.
- Official roster discovery, frozen splits, resumable metadata/PDF acquisition,
  GROBID TEI headers, conservative resolution, phrase topics and Neo4j loader.
- R7–R10 materialization/support checks, synthetic fixture, offline tests and CI.
- Frozen-diagnostic evidence triage, visible ACL byline/Unicode handling and
  input-bound printed-affiliation review ledgers; see [review workflow](evidence-review.md).
- Offline analysis and component-evaluation commands with synthetic protocol
  coverage and strict real-data gates; edge-audit packet utilities remain a
  separate post-build workflow.
- Standalone [HTML output explorer](visual-report.md): typed network projections,
  search, evidence inspection, conference coverage, release gaps and print/export.
  This read-only report does not implement the pending scientific analysis/audit.
- [Current handoff](status.md) and [task history](work-log/README.md), with a reusable
  template and contributor instructions for future sessions.

The [pilot workflow](pilot-workflow.md) describes current commands; measured outputs
and remaining quality gaps belong in [the pilot report](../reports/pilot-v1.md).
Implemented software does not establish independent semantic accuracy.

## Historical 2023 implementation — authorized under D015

Historical 2023 work: task 006 implemented nine official source families, additive edition-ledger
handling, protected supplemental sampling and a separate Neo4j instance. Measured:
17 covered editions, 14,909 eligible roster papers, 250 selected / 245 acquired
papers, 235 parsed PDFs and a 399-node / 533-edge graph. Fourteen editions remain
unresolved; this is a partial diagnostic run. See [the measured report](../reports/extended-v1.md).

Task 008 recovered all 250 diagnostic metadata records and parsed 240 PDFs after
services became available. Three recovered papers enter a separate 402-node /
538-edge candidate; two PDF/byline conflicts stay withheld. The original 718-row
queue was triaged, and five printed affiliation observations corroborate existing
triples. Identity coverage remains 85 researchers. Both loaded databases retain
their task 006 snapshots. See [review results](../reports/evidence-review-v1.md).

The items below preserve the historical 2023 expansion sequence, not an active
execution instruction under D018. Adapter dispatch, venue labels,
year windows and staged splits are now implemented for the documented source
families. Future missing-family work and acquisition require a later instruction.

The earlier venue revision targeted 34 flagship series / 31 planned 2023 editions.
Read [the scope policy](conference-scope.md); the existing 100-paper pilot and
5,046-paper roster remain historical two-venue results. The user authorized
expanded acquisition on 2026-11-03. See [the expanded workflow](extended-workflow.md)
and [current status](status.md) for actual coverage and run results.

1. Review the registry, track rules, no-edition cases and official source families.
2. Generalize adapter dispatch, edition IDs, venue labels, year matching and staged
   split/pilot quotas; verify with offline fixtures before enabling expanded configs.
3. Preserve old held-out IDs; design supplemental cross-venue leakage groups and
   sampling weights. Budget annotation hours: default quotas imply 1,860 test /
   930 development papers, not a commitment or new frozen sample.
4. Expand the draft taxonomy/guide on development evidence; review current pilot
   affiliation/identity errors and prospectively select additional diagnostics.
5. Stage 10 diagnostics per newly active
   venue (390 cumulative if all additions qualify), then re-estimate the schedule,
   resources and coverage before processing complete rosters.

## Historical five-year planning revision (D018; execution pause superseded by D022)

The core target now covers **2021–2025**, retaining 34 series. The 170 venue–year
candidates require edition verification; 31 is only the historical 2023 count.
Use `configs/conference-scope-2021-2025.yaml` for planning only. Preserve all current
executable configs and frozen artifacts. No five-year adapters/configs, split
generation, acquisition, NLP or graph import is implemented or authorized here.

Deadline: **11 November 2026**, user-confirmed on 6 November. Use the
[execution plan](five-year-execution-plan.md), [planning readiness ledger](five-year-edition-readiness.csv)
and [effort assumptions](../reports/five-year-planning-estimates-2026-11-06.json).
P01 documents the plan; E01–E09 are **unstarted, conditional execution packages**.
Prioritize source/track verification, offline contracts, frozen leakage/sample
groups, identity/affiliation quality and a safe isolated graph before audit/analysis.
Protect writing and validation time: proposed source-feature cutoff 8 November
18:00, candidate freeze 9 November 18:00, gate assessment 10 November 12:00 and
submission-ready package 10 November 18:00 (+07:00). Audit effort may exceed this
window; disclose unmet gates rather than lowering them. No extra capacity or
lecturer response is a planning prerequisite. D018 still requires later explicit
execution authorization. The original eight-week calendar below is historical.

The existing Site has native Plan/Report views and a
[versioned publication workflow](sites-workflow.md) (D019/D020); keep the 399/533
explorer distinct from the 402/538 candidate and future five-year evidence.

## Original first three working days

| Day | A: data and graph | B: NLP and analysis | Joint checkpoint |
| --- | --- | --- | --- |
| 1 | Implement source roster adapters and stable-ID proposal | Draft annotation examples, reserve test IDs and GROBID pilot | Agree corpus, predicates and proposed accuracy definition |
| 2 | Verify work matches, affiliation triples and review logging | Test difficult PDF headers; annotate development cases | Inspect 20 affiliations and difficult identities |
| 3 | Produce a small accepted table set and first repeatable graph import | Review outputs and measure annotation effort | Freeze pilot decisions and estimate full-run resources |

## Original eight-week baseline

| Week | A | B | Exit evidence |
| --- | --- | --- | --- |
| 1 | Source access, manifest and identity/schema | Taxonomy, parser pilot and guide | Balanced ~100-paper pilot and course-confirmation record |
| 2 | Full roster, metadata and retrieval ledger | Header extraction and development labels | Reconciled corpus; systemic extraction defects fixed |
| 3 | Canonical resolution and aligned affiliation triples | Baseline/classifier and independent gold labels | Reversible identities; uncertainty and workload quantified |
| 4 | Constraints, factual imports and provenance | Development calibration, held-out evaluation, EDA | Frozen taxonomy/model, split integrity, initial factual graph |
| 5 | Exact R7–R10 derivation and frozen audit frames | Independent audits and error analysis | All ten real types, size and structural gates |
| 6 | Named projections and quality fixes | Communities, topic/sector/citation cases | Precision/recall/coverage and supported findings |
| 7 | Clean rebuild, exports and query checks | Minimal demo, report and figures | Both people reproduce principal outputs |
| 8 | Final code/graph release | Report, presentation and demo script | Joint rubric review and disclosed limitations |

Keep the schedule adjustable to the actual deadline; do not lower quality gates
after looking at errors. The five core years are no longer optional. Remove
prediction and extra UI before
independent review. Measure pilot PDF size/runtime/API use/review minutes rather
than assuming earlier size estimates. Keep legitimate isolates and sparse citation
results; connectedness alone is not quality.

## Remaining implementation issues — follow D022 staged prerequisites

1. Independently inspect the first pilot's identities and 20 author–organization
   mappings; measure reviewer effort and parser/linker error categories.
2. Improve work/identity/institution matching on development papers using reviewed
   evidence and reversible decisions; preserve all 925 expanded test assignments,
   including the original 120. Initial source-review ledgers and technical triage
   are implemented; broader identity adjudication remains pending.
3. Annotate development topics, implement exclusion/context handling and calibrate
   a supported classifier; freeze the taxonomy/model before independent scoring.
4. Promote pilot JSON to complete canonical versioned Parquet stage tables and a
   reviewed correction history. Implement explicit graph-version migration/rebuild.
5. After adapter/split readiness and diagnostic review, scale over
   the expanded edition registry after reviewing pilot
   resource use and coverage; verify citations and all ten nonempty predicates.
6. Enforce complete release size/coverage gates, frozen global/per-type sampling,
   two-reviewer adjudication and component precision/recall/F1.
7. Implement separate SNA projections, robustness checks, three business cases and demo.
8. Produce final report PDF, real GitHub URL/release, rights and reproducibility bundle.
