# Progress report — updated 6 November 2026

**Target:** international AI research network across 34 flagship series,
**2021–2025**; **11 November 2026 deadline**. D022/D023 authorize staged collection.
New roster/metadata evidence below is separate from the historical **2023 graph**.

## Corrected five-year rosters and frozen diagnostics

**78,321 roster records; 75,655 included** from **79 eligible editions**, up from
67 in the first pass. Every one of **170 venue–year candidates** remains visible:
**51 unresolved, 40 unavailable**. All twelve prior track/layout review cases were
resolved; this still does not establish complete scope or canonical work counts.

| Conference year | Roster records | Included | Eligible editions |
| --- | ---: | ---: | ---: |
| 2021 | 11,063 | 10,917 | 16 |
| 2022 | 12,520 | 12,151 | 16 |
| 2023 | 14,480 | 13,935 | 15 |
| 2024 | 17,698 | 16,937 | 16 |
| 2025 | 22,560 | 21,715 | 16 |

Source corrections: NeurIPS 2025 position-track exclusion, ECVA accordion/year
agreement, RSS official catalog year/edition corroboration, and KR Full/Short/Main
versus special/application tracks. Automated roster contracts are not independent
scientific accuracy. Unknown source rights/access limitations remain explicit.

Before enrichment, froze **68 new development diagnostics** and **170 new reserved
test groups** across **34 source-family/year strata**, with recorded seed, population
and probabilities. All **14,909 historical assignments**, including **5,046**
originals, stay unchanged. **Zero held-out acquisition overlap.** New diagnostics
cover 2021/2022/2024/2025; historical 2023 diagnostics remain separate. This design
checks new layouts/years; it does not replace the final independent 600-edge audit.

## Bounded metadata batch

**67/68 selected papers collected; 67 abstracts; 36 strict OpenAlex work matches.**
One MLSys 2025 paper is withheld for expanded-name versus initial byline disagreement.
No forced author alias/identity merge. Provider/version and held-out-location
conflicts are quarantined; alternate-title detection remains limited.

**No new PDFs, accepted researcher identities or graph imports.** OpenAlex used
**$0.067 of the daily free allowance**, with **$0.933 remaining** and zero prepaid
balance at the post-run check. **119 offline tests passed**; semantic accuracy,
recall and F1 remain unmeasured. Base Neo4j remains **154/211** after read-only checks;
GROBID is running and alive, ready for later selective PDF work.

[Measured collection/diagnostics report](five-year-collection.md) ·
[All 170 edition statuses](five-year-edition-ledger.csv) ·
[Measured summary JSON](five-year-collection.json)

All historical v1 outputs and loaded/candidate graphs remain preserved. The native
explorer below still shows its dated **399/533 2023 snapshot**. It is not a five-year
graph. Internal cutoffs remain 8–10 November; preserve independent review/report
time, keep release gates unchanged and disclose actual shortfalls by 11 November.

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
| 6 November 2026 | Corrected rosters and frozen metadata diagnostics | 79 eligible editions; 68 diagnostics / 170 tests frozen; 67 metadata / 36 strict matches; 119 tests; no new graph |
| 6 November 2026 | First five-year roster collection | 73,714 records; 67 eligible editions; all 170 candidates retained; no new graph; 108 tests |
| 6 November 2026 | Deadline-driven readiness plan | 11 November deadline; 170 unverified review rows; dated work packages and illustrative costs; execution paused |
| 4 November 2026 | Native Site report | Integrated graph, charts, filters, coverage and evidence in Report; no iframe or new research data |
| 4 November 2026 | Five-year planning and Site | 2021–2025 plan; one existing Site with Plan and Report tabs; no research collection |

## Next planned work

1. Selective PDF/header extraction and source-specific identity/affiliation review
   on frozen development IDs; resolve the withheld byline using explicit evidence.
2. Preserve new/old test IDs, provider/version quarantine, paper-specific triples and
   public ORCID publication corroboration. Do not accept names as identities.
3. Build accepted evidence into an isolated graph, then independently evaluate and
   analyze named projections. Keep the current native graph until a matching new
   payload is verified.
4. Prepare the ≥10-page report, contributions, code link, reproducibility and actual
   pass/fail/unmeasured gates before 11 November. No passing release claim yet.

## Evidence and update policy

New roster/diagnostic sources: `reports/five-year-collection-v2.{md,json}`,
`reports/five-year-edition-ledger-v2.csv`, frozen manifests, acquisition summary and task 003.
The v1 report/task 002 remain historical first-pass evidence.
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
