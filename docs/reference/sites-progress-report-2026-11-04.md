# Progress report — 4 November 2026

**Target:** international AI research network across 34 flagship series,
**2021–2025**. There are 170 venue–year review candidates, not 170 confirmed editions.
**Current instruction:** planning and Site updates only; no new pipeline
implementation or research collection. All measured data below is **2023-only**.

## What exists today

| Output | Graph version | Nodes | Edges | State |
| --- | --- | ---: | ---: | --- |
| Historical two-venue Neo4j pilot | `pilot-topic-0bb7f11a404e` | 154 | 211 | Loaded historical snapshot |
| Expanded 2023 Neo4j + interactive explorer | `pilot-topic-d512d7239923` | 399 | 533 | Loaded snapshot; 17 covered editions |
| Evidence-reviewed local candidate | `pilot-topic-7e3c90189547` | 402 | 538 | Validated artifact; not imported |

The embedded explorer below shows **399 nodes / 533 edges**, not the local
candidate or the five-year target. Its layout is a display aid, not measured
centrality or communities. Stored weights describe the full snapshot; filtering
does not recalculate support. The complete explorer opens separately for printing,
filtering, evidence inspection and JSON/CSV export.

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
| 4 November 2026 | Five-year planning and Site | 2021–2025 plan; one existing Site with Plan and Report tabs; no research collection |

## Next planned work

1. Review edition/track/source policies for all 170 venue–year candidates; confirm
   deadline and annotation budget. Actual edition count remains to be verified.
2. Design cross-year leakage/version handling, yearly/cumulative support and
   citation-age controls; preserve old held-out assignments. No implementation now.
3. Re-estimate API/storage/runtime and reviewer hours before a later explicit
   implementation/collection instruction.
4. After later authorization, address identity/affiliation gaps and two source
   conflicts on development evidence, calibrate topics, then stage acquisition.
   A safe graph migration is required before replacing loaded snapshots.

## Evidence and update policy

Snapshot sources: repository `reports/evidence-review-v1.md`,
`reports/evidence-review-v1.metrics.json`, `reports/extended-v1.metrics.json`,
`docs/status.md`, `docs/work-log/2026-11-04-001-evidence-review.md` and
`docs/five-year-scope.md`. The graph explorer is the existing
`reports/extended-v1.html`; its original metrics remain separate.

**Task-driven updates:** after material project iterations, update this report
from measured versioned artifacts, validate, and publish a new version of this
same Site. Show update date, exact graph version, fresh versus historical checks,
limitations and next steps. Preserve previous Site versions and publication
receipts. This is a published snapshot; no automatic background sync, live Neo4j
connection or update schedule is configured. The final course deliverable still
requires a substantive ≥10-page report and a real GitHub repository link.
