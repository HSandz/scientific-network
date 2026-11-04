# Implementation roadmap

**Current instruction (D018): 2021–2025 planning only. Pipeline implementation
and collection are paused.** Older execution sequences below are historical;
use [the five-year prerequisites](five-year-scope.md) before a later run.

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
- Explicit pending interfaces for final analysis and evaluation.
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

## Five-year planning revision — no implementation or collection (D018)

The core target now covers **2021–2025**, retaining 34 series. The 170 venue–year
candidates require edition verification; 31 is only the historical 2023 count.
Use `configs/conference-scope-2021-2025.yaml` for planning only. Preserve all current
executable configs and frozen artifacts. No five-year adapters/configs, split
generation, acquisition, NLP or graph import is implemented or authorized here.

Before later implementation: review the edition matrix/track history and source
rights; design cross-year version/leakage controls and weighted venue–year
annotation; re-estimate resources; specify yearly/cumulative support and citation
age controls; then obtain a later implementation/collection instruction. See
[temporal plan](five-year-scope.md). The existing Site now has Plan and Report
views with a [versioned publication workflow](sites-workflow.md) (D019/D020).
The Report integrates graph, charts, filters, coverage and evidence inspection
natively; the standalone HTML remains an offline snapshot.

The original eight-week schedule below is historical planning guidance and must
be re-estimated for 2021–2025; it is not a promise for all confirmed editions.

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

## Future implementation issues — execution paused by D018

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
