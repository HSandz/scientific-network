# Progress report — updated 6 November 2026

**Target:** international AI research network across 34 flagship series,
**2021–2025**; **11 November 2026** deadline.
**D022:** the user authorized staged collection after the readiness-planning task.
Five-year roster evidence below is new; graph measurements remain **2023-only**.

## Five-year collection — first official roster pass

**73,714 official roster records** were collected across all five years. These are
bibliographic observations, not canonical works, researchers, graph nodes or edges.
**67 editions** passed automated complete-roster contracts, contributing **65,523
included records** eligible for later sampling. Every one of the **170 candidates**
remains in the ledger: **51 unresolved, 40 access unavailable, 12 need review**.
No missing edition was inferred from an absent catalog link or HTTP error.

| Conference year | Roster records | Included in eligible editions | Eligible editions |
| --- | ---: | ---: | ---: |
| 2021 | 10,971 | 10,750 | 14 |
| 2022 | 10,801 | 10,389 | 13 |
| 2023 | 14,368 | 13,823 | 14 |
| 2024 | 15,177 | 14,350 | 13 |
| 2025 | 22,397 | 16,211 | 13 |

Across all records: **70,973 included**, **2,556 excluded**, **185 review**.
Included records from incomplete/review-needed editions remain ineligible for
sampling. NeurIPS 2025 position papers, ECVA headings, RSS year corroboration,
KR track boundaries, and unsupported/publisher sources need further work.
These are automated contract checks, not independent semantic review.

Pre-enrichment leakage triage preserves all **14,909** historical assignments,
including the **5,046** original assignments. **13,823** collected records retain
existing assignments; **57,149** await prospective design and **one** version
candidate is quarantined. No new splits or work merges were made. Title links
are conservative guards; alternate-title versions still need identifier review.

No OpenAlex requests, new PDFs, enrichment or graph imports in this iteration.
The **108-test offline suite passed**; discovery's exit **1** explicitly reports
remaining edition gaps while retaining the successful collection. Historical
native explorer, local candidate and databases remain unchanged.

[Measured collection report](five-year-collection.md) ·
[170-row edition ledger](five-year-edition-ledger.csv) ·
[Collection summary JSON](five-year-collection.json)

Submission cutoffs remain: source/feature cutoff 8 November 18:00, candidate/method
freeze 9 November 18:00, gate assessment 10 November 12:00 and packaging 10 November
18:00 (+07:00). Independent audit feasibility is not guaranteed; keep gates unchanged
and report actual shortfalls. The earlier planning-only ledger remains a dated
snapshot; the collection ledger supplies new measured statuses.

## What exists today

| Output | Graph version | Nodes | Edges | State |
| --- | --- | ---: | ---: | --- |
| Historical two-venue Neo4j pilot | `pilot-topic-0bb7f11a404e` | 154 | 211 | Loaded historical snapshot |
| Expanded 2023 Neo4j + interactive explorer | `pilot-topic-d512d7239923` | 399 | 533 | Loaded snapshot; 17 covered editions |
| Evidence-reviewed local candidate | `pilot-topic-7e3c90189547` | 402 | 538 | Validated artifact; not imported |

The native explorer in this Report tab shows **399 nodes / 533 edges**, not the
local candidate or the five-year target. Projection and conference filters, node
search, charts, coverage, evidence inspection, printing and JSON/CSV export share
the Site interface. Its layout is a display aid, not measured centrality or
communities. Stored weights describe the full snapshot; filtering does not
recalculate support.

## Latest measured 2023 development snapshot

Evidence review completed 4 November 2026; graph/config/source versions are fixed.
No new scientific measurements were produced by this five-year planning revision.

| Measure | Recorded result |
| --- | ---: |
| Acquired diagnostic metadata | 250 selected / 250 acquired |
| Abstracts / strict OpenAlex work matches | 240 / 145 |
| Parsed PDFs | 240; ten MICCAI records lack official PDF URLs |
| Candidate papers / researchers / organizations | 248 / 85 / 32 |
| Topics / venues | 20 / 17 |
| Accepted affiliation triples | 38 |
| Factual R1–R4 edges | 372 |
| Inferred topic / taxonomy / derived edges | 110 / 16 / 40 |
| Nonempty predicates | 8 of 10 |
| Papers with baseline topic labels / abstentions | 87 / 161 |
| Candidate review queue | 723 rows; mixed claim units, not an error rate |

All five previously failed source bylines were recovered as metadata; three
papers entered the candidate. EACL 280 and one MLSys record remain withheld because
PDF author order/count contradicts HTML. Five printed affiliation observations
corroborated existing mappings; **zero affiliation triple IDs added or removed**.
No identity aliases, name-only merges or quality-threshold relaxation were used.

Historical 2023 discovery recorded 15,738 roster records (14,909 included / 829
excluded), 17 covered editions, 14 unresolved and three no-2023-edition cases.
Those statuses do not establish other years' availability. Frozen membership
remains 925 test / 470 development / 13,514 pool, preserving all 5,046 legacy
assignments; held-out samples remain unannotated.

## Coverage and release gaps

The proposed release needs at least 2,000 resolved researchers, 5,000 factual edges,
ten supported predicates and independent precision/recall/coverage. Current
candidate has 85 researchers and 372 factual edges. Author resolution is
85/1,206 (7.05%); affiliated author–paper pairs 36/1,206 (2.99%); baseline topic
coverage 87/248 (35.08%). The phrase taxonomy is a draft and uncalibrated.

**Independent semantic accuracy, recall and F1 are not measured.** Structural
checks and source hashes do not establish accuracy above 90%. Fourteen historical
2023 editions remain unresolved; five-year edition verification and collection
have not started. No temporal findings or final ten-page report exist yet.

## Verification history

These are dated outcomes from evidence-review task WORK-2026-11-04-001, not
service checks repeated while viewing this Site:

- 97 offline tests passed; structural validation and lock consistency passed.
  Size validation returned 1, correctly reporting unmet release gates.
- Candidate's 513 source objects and 20 protected artifacts were hash-checked;
  all 5,046 legacy assignments preserved; zero acquired held-out groups.
- Offline baseline triage preserved 718 rows, with 85 accepted identity and 38
  affiliation consistency checks passing; 813 distinct cached objects checked.
- Both Neo4j snapshots passed six integrity queries with unchanged content
  digests; GROBID and Neo4j HTTP endpoints returned 200 at that task's check time.
- Candidate import, independent audits, GDS and classifier calibration were not run.

This Site revision updates scope, presentation and publication only. It does not
rerun collection or database validation. Current publication checks are recorded
separately in the repository work log and publication receipt.

## Progress history

| Date | Work | Outcome |
| --- | --- | --- |
| 2 November 2026 | Repository initialization | Package, schema, documentation and synthetic validation |
| 3 November 2026 | Historical pilot | 100 diagnostic papers; loaded 154-node / 211-edge graph |
| 3 November 2026 | Venue expansion | 34-series registry; 17 covered 2023 editions; loaded 399 / 533 graph |
| 3 November 2026 | Visualization | Offline interactive explorer with provenance and filters |
| 4 November 2026 | Evidence review | 250 metadata / 240 parsed PDFs; 402 / 538 local candidate; two conflicts withheld |
| 6 November 2026 | First five-year roster collection | 73,714 records; 67 eligible editions; all 170 candidates retained; no new graph; 108 tests |
| 6 November 2026 | Deadline-driven readiness plan | 11 November deadline; 170 unverified review rows; dated work packages and illustrative costs; execution paused |
| 4 November 2026 | Native Site report | Integrated graph, charts, filters, coverage and evidence in Report; no iframe or new research data |
| 4 November 2026 | Five-year planning and Site | 2021–2025 plan; one existing Site with Plan and Report tabs; no research collection |

## Next planned work

1. Review remaining edition/track gaps in new config/output versions, without
   overwriting this pass. Keep unavailable/unsupported sources explicit.
2. Complete cross-year work/exposure reconciliation and freeze a prospective
   diagnostic design before a bounded metadata/PDF tranche.
3. Prioritize identity/author-specific affiliations and topic calibration; preserve
   independent audit time. Use isolated Neo4j storage and a matching native payload.
4. Freeze the candidate, record pass/fail/unmeasured gates and prepare the ≥10-page
   report, contributions, code link and limitations before 11 November.

## Evidence and update policy

New roster sources: `reports/five-year-collection-v1.{md,json}`,
`reports/five-year-edition-ledger-v1.csv`, versioned manifest summaries and task 002.
Historical graph sources: repository `reports/evidence-review-v1.md`,
`reports/evidence-review-v1.metrics.json`, `reports/extended-v1.metrics.json`,
`docs/status.md`, `docs/work-log/2026-11-04-001-evidence-review.md` and
`docs/five-year-scope.md`. The native graph explorer reuses the unchanged permitted payload from
`reports/extended-v1.html`; its original metrics remain separate. The original
standalone file is preserved as an offline artifact.

**Task-driven updates:** after material project iterations, update this report
from measured versioned artifacts, validate, and publish a new version of this
same Site. Show update date, exact graph version, fresh versus historical checks,
limitations and next steps. Preserve previous Site versions and publication
receipts. This is a published snapshot; no automatic background sync, live Neo4j
connection or update schedule is configured. The final course deliverable still
requires a substantive ≥10-page report and a real GitHub repository link.
