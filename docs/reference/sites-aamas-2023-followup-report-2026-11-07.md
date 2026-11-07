# Progress report — updated 7 November 2026

**Target:** international AI research network across 34 flagship series,
**2021–2025**; **11 November 2026 deadline**. D022 authorizes staged development
collection; D029–D034 record source corrections and the continuing enrichment stop.
New roster/metadata/header evidence below is separate from the historical **2023 graph**.

## AAMAS 2023 official identifier scan — latest iteration (WORK-008)

All six hash-bound official AAMAS 2023 sources were verified against
[source corrections v6](../data/manifests/five-year-source-corrections-v6.json).
The accepted page lists 237 full papers but exposes no per-entry identifier or
DOI. The official proceedings contents expose 528 PDF identifiers without DOI
links. An aggregate exact ordered-byline diagnostic finds 196 unique candidate
joins to proceedings records: 190 also match the normalized title, six have a
different title, 40 have no candidate, and one has multiple candidates. The
official author index has 471 PDF-link occurrences across 316 IDs; 154 IDs are
labeled Main Track Full Paper. These are not adjudicated record mappings, and the
full accepted-paper to proceedings-ID crosswalk remains incomplete. AAMAS 2023
therefore remains unresolved; no roster rows were added.

Roster v10 remains at **98 eligible editions / 10 verified no-edition findings /
22 unresolved roster-adapter editions / 40 access-unavailable editions**, with
**94,857 observations: 91,355 included and 3,502 excluded**. All **76,629 frozen
assignments**, including **1,095 tests**, and the v2-bound diagnostic/pregraph
inputs remain unchanged. P01 remains failed with 62 incomplete candidates; P02
remains no-go for broader enrichment. No enrichment, split, PDF, graph or database
operation occurred.

[IFAAMAS accepted-paper page](https://www.ifaamas.org/AAMAS/aamas2023/accepted_papers.html) ·
[official proceedings contents](https://www.ifaamas.org/Proceedings/aamas2023/forms/contents.htm) ·
[official author index](https://www.ifaamas.org/Proceedings/aamas2023/forms/authors.htm) ·
[source triage](../docs/five-year-source-triage.md#aamas-2023-official-identifier-scan-work-008)

## MICCAI 2022 source-route follow-up — latest iteration (D034 / WORK-007)

The directly captured official Society accepted-paper index has **573 unique
paper-detail records**; its topic-category page has 572 distinct records. The
eight Springer main-volume contents sets expose **576 chapter DOI records**,
while each volume description reports **574 revised full papers** and the refreshed
Springer index displays 576. The source records remain unreconciled.

After NFKC normalization, whitespace normalization and case-folding, 558 titles
join uniquely. Fifteen Society records and 18 publisher chapters remain outside
that exact-title join, including three correction-title chapters. These are
candidate differences only: no byline adjudication or missing-paper inference was
made. The official conference program documents did not resolve the one-record
discrepancy, so MICCAI 2022 remains unresolved and ineligible.

Roster v10 remains current: **98 eligible editions / 10 verified no-edition
findings / 22 unresolved roster-adapter editions / 40 access-unavailable
editions**, with **94,857 observations: 91,355 included and 3,502 excluded**.
The 62 incomplete candidates keep P01 failed. All 76,629 frozen assignments,
including 1,095 tests, and the v2-bound diagnostic/pregraph inputs remain intact.
No roster, split, enrichment, paper PDF, graph or database output was created.
Detailed source captures and program PDFs remain in ignored local storage; this
Report contains aggregate results and official source links only.

[MICCAI 2022 accepted-paper index](https://conferences.miccai.org/2022/papers/) ·
[Springer main proceedings, Part I](https://link.springer.com/book/10.1007/978-3-031-16431-6) ·
[Springer MICCAI index](https://link.springer.com/conference/miccai) ·
[D034 source triage](../docs/five-year-source-triage.md#d034-miccai-2022-official-source-route-follow-up)

## Previous iteration — MICCAI 2024 source reconciliation (D033 / WORK-006)

V10 reconciles all **856** Society accepted research records to **856 distinct
Springer chapters** across 12 main-proceedings volumes and 49 captured contents
pages. The 856 matches comprise 836 exact-title and 20 title-and-byline matches.
Springer’s one additional chapter is a correction notice tied to an already-listed
paper; it is excluded as nonresearch. The complete roster meets the existing D015
main-research track rule without changing the scope or policy.

| Measure | Roster v10 |
| --- | ---: |
| Eligible editions | 98 |
| Verified no-edition findings | 10 |
| Unresolved roster/adapter / access-unavailable | 22 / 40 |
| Roster observations | 94,857 |
| Included / excluded / record review | 91,355 / 3,502 / 0 |
| Guarded assignments / test assignments | 76,629 / 1,095 |

The fresh isolated discovery exited 1 as expected because 62 candidates remain
incomplete. It matched all 42 saved output hashes; all 36 inherited v9 edition
roster/summary artifacts are unchanged. No new split, enrichment request, canonical
merge, PDF download, graph write, or database operation occurred. P01 remains
incomplete; P02 is no-go for broader enrichment. The v2-bound diagnostic/pregraph
inputs remain unchanged. Semantic accuracy remains unmeasured.

Detailed captures and full rosters stay in ignored local storage. This Report
includes permitted aggregates and official source links only.

[V10 recovery report](five-year-source-recovery-v10.md) ·
[v10 edition ledger](five-year-edition-ledger-v10.csv) ·
[D033 source triage](../docs/five-year-source-triage.md#d033-miccai-2024-official-12-volume-reconciliation-v10)

## Previous iteration — MICCAI roster v9 (D032 / WORK-004)

Roster v9 adds the official MICCAI accepted-paper lists for 2021 (531), 2023
(730) and 2025 (1,027), each matching the Springer full-paper count. MICCAI 2022
remains unresolved: the official accepted-list request returned HTTP 522, and
Springer reports 574 full papers versus 576 papers in its series index. MICCAI
2024 remains unresolved because the captured Society list has 856 numbered
records versus 857 accepted full papers in Springer. Index counters remain
separate from accepted-paper counts.

The ledger now has **97 eligible editions / 10 verified no-edition findings / 23
unresolved roster/adapter editions / 40 access-unavailable editions**. It contains
**94,000 observations: 90,499 included and 3,501 excluded**. All **76,629 frozen
assignments**, including **1,095 tests**, remain guarded. No split, enrichment,
graph or database operation occurred; P01 remains incomplete and P02 remains
no-go for broader enrichment. The v2-bound diagnostic/pregraph inputs are unchanged.

The 2021 and 2023 lists contain no author bylines; 2025 provides BibTeX names.
Under D015, these roster rows alone do not support person resolution or core-paper
acceptance. Detailed source captures and per-record rosters remain in ignored local
storage; the report publishes aggregate counts and source links only.

[V9 recovery report](five-year-source-recovery-v9.md) ·
[v9 edition ledger](five-year-edition-ledger-v9.csv) ·
[D032 source triage](../docs/five-year-source-triage.md#d032-miccai-roster-closure-and-unresolved-years-v9)

The local Site Report is refreshed; the public Site remains version 14 and no
publication occurred in this iteration.

## Previous iteration — ICLR official source-route review (WORK-003)

The official OpenReview venue index lists separate ICLR Conference groups for
2021–2025, and the ICLR Proceedings FAQ directs accepted-paper access through
OpenReview. A separate electronic-proceedings index currently lists 2024–2026.
ICLR 2024's official book and fact sheet agree at **2,260** papers. The 2025 book
lists **3,703**, while the hosted draft fact sheet says **3,704** accepted; that
count remains unresolved.

Local OpenReview API access returned HTTP 403, and local proceedings retrieval
failed DNS resolution. No hash-bound ICLR roster was produced and no ICLR edition
was promoted. At that checkpoint, the measured roster was v8: **94 eligible
editions / 88,211 included records**, with 66 incomplete candidates (26 unresolved
roster/adapter editions and 40 access-unavailable editions). All frozen assignments remain
guarded. No splits, enrichment, graph or database operations occurred; P02 stays
no-go.

[Detailed ICLR source triage](../docs/five-year-source-triage.md#iclr-official-route-and-roster-access-check-work-003) ·
[V8 measured roster](five-year-source-recovery-v8.md) ·
[Work entry](../docs/work-log/2026-11-07-003-iclr-source-review.md)

The local Site Report is refreshed. The public Site remains version 14; publication
was not attempted during this iteration.

## Previous iteration — AAMAS official roster closure (D031 / WORK-002)

Roster v8 adds the official AAMAS 2021, 2022, 2024 and 2025 main-research
sections. AAMAS 2023 stays unresolved because official accepted-paper and
proceedings titles/bylines do not fully reconcile. The existing 2021–2025 scope,
track policy, schema, thresholds and frozen assignments remain unchanged. The
IFAAMAS rights notice restricts redistribution, so detailed pages and full rosters
remain local; no PDFs were downloaded.

| Measure | Roster v8 |
| --- | ---: |
| Eligible editions | 94 |
| Verified no-edition findings | 10 |
| Unresolved roster/adapter / access-unavailable | 26 / 40 |
| Roster observations | 91,712 |
| Included / excluded / record review | 88,211 / 3,501 / 0 |
| Guarded assignments / test assignments | 76,629 / 1,095 |

The source-disabled offline replay matched all **34 recorded output hashes** and
returned exit 1 because 66 candidates remain incomplete. **193 offline tests
passed** during this iteration. V8 recorded no new split, enrichment request,
canonical merge, or graph write; semantic accuracy remains unmeasured. The
2023 accepted-page/news counts are 237/219 versus 237/221; exact-title joins
matched 225 full-paper titles, with 12 title mismatches and 35 differing author
strings among matched titles. These automated joins are unresolved, not a manual
review result.

[V8 recovery report](five-year-source-recovery-v8.md) ·
[source correction](../data/manifests/five-year-source-corrections-v6.json) ·
[170-row ledger](five-year-edition-ledger-v8.csv) ·
[source triage](../docs/five-year-source-triage.md)

P01 remains incomplete across **26 unresolved roster/adapter editions and 40
access-unavailable editions**. P02 remains **no-go for broader enrichment** because canonical work
counts, the prospective P03 frame, live free-resource/storage limits and reviewer
capacity remain unmeasured. The current enrichment budget stays at zero. The
diagnostic/pregraph freeze remains bound to v2; v8 does not refresh it. The
historical graph explorer below remains 399/533.

The local Site Report is refreshed. The public Site remains version 14; publication
was not attempted during this iteration.

## Historical official route closure and COLING 2024 (D030 / WORK-001)

Roster v7 applies official conference-history evidence to all 11 route rows that
were still unverified in v6. Ten are verified no-edition findings. The official
LREC-COLING 2024 proceedings add 1,554 papers under COLING, once each, with the
LREC co-host recorded in a joint-event crosswalk; one frontmatter record is
excluded. The five-year scope, track policy, entity schema, thresholds and frozen
assignments remain unchanged.

| Measure | Roster v7 |
| --- | ---: |
| Eligible editions | 90 |
| Verified no-edition findings | 10 |
| Unsupported adapters / access-unavailable | 30 / 40 |
| Roster observations | 90,163 |
| Included / excluded / record review | 87,404 / 2,759 / 0 |
| Guarded assignments / test assignments | 76,629 / 1,095 |

The fresh offline replay matched every recorded output hash, including the
versioned ledger and COLING roster hash, and returned exit 1 because 70 edition
candidates remain incomplete. **187 offline tests passed.** The official evidence,
method/config hashes and source-response hashes are in the
[v7 recovery report](five-year-source-recovery-v7.md),
[correction record](../data/manifests/five-year-source-corrections-v5.json), and
[170-row ledger](five-year-edition-ledger-v7.csv). v7 recorded no new split,
enrichment request, canonical merge, or graph write; semantic accuracy remains
unmeasured. Its ignored local COLING capture/raw source snapshots are not a
clean-checkout reproduction bundle.

At the v7 checkpoint, P01 remained incomplete across 30 unsupported-adapter and
40 access-unavailable editions. P02 was **no-go for broader enrichment** because canonical work
counts, the prospective P03 frame, live free-resource/storage limits and actual
reviewer capacity remain unmeasured. The current enrichment budget stays at zero.
The diagnostic/pregraph freeze remains bound to v2; v7 does not refresh it. The
historical graph explorer below remains 399/533.

[Source triage](../docs/five-year-source-triage.md) ·
[Measured v7 metrics](five-year-source-recovery-v7.metrics.json) ·
[P02 feasibility checkpoint](five-year-pregraph-feasibility-v1.md)

The local Site Report snapshot is updated here. The public Site remains version 14
pending the previously blocked source-credential handoff.

## Historical ICAPS 2025 source correction (D029 / WORK-009)

Roster v6 has **89 eligible editions / 85,850 included records** from **88,608
observations**. It resolves the 48 ICAPS 2025 records previously held for track
review. All 170 venue-year candidates remain: **41 unresolved / 40 unavailable**
(81 gaps); there are no record-level review rows in v6.

The official [main technical call](https://icaps25.icaps-conference.org/calls/main_track/)
and [topic-based policy](https://icaps25.icaps-conference.org/organisation/roles_and_guidelines/)
place the theoretical, algorithmic, modelling and tools categories in the main
technical call. All 48 OJS records match publisher IDs on the [accepted-paper
page](https://icaps25.icaps-conference.org/program/accepted/). Three accepted
position papers remain excluded under the project's main archival research policy;
front matter is excluded. This corrects a track disposition under the existing
scope and does not change the corpus boundary or quality thresholds.

| Measure | Roster v6 |
| --- | ---: |
| Eligible editions | 89 |
| Unresolved / unavailable | 41 / 40 |
| Roster observations | 88,608 |
| Included / excluded / record review | 85,850 / 2,758 / 0 |
| Guarded assignments / test assignments | 76,629 / 1,095 |

The source-disabled v6 discovery replay made no network requests and returned exit 1
for the 81 remaining edition gaps. All **76,629 frozen assignments**, including
**1,095 tests**, stayed guarded. No split, paper enrichment, held-out acquisition,
merge, accepted diagnostic support or graph was produced. The old diagnostic and
pregraph freeze remain bound to v2 and false; neither was refreshed. The historical
explorer below remains 399/533.

The replay reproduced the manifest, roster rows and leakage decisions. Edition
`checked_at` values refresh on each run, so several timestamp-bearing summaries and
their dependent hashes differ byte-for-byte; after excluding those timestamps and
derived hashes, all 26 output files have no other semantic differences. The full
offline suite passed: **181 tests**. Hash comparison found **8,483 of 8,494**
task-start files unchanged; eleven existing documentation/source files were revised
for this task, and new versioned v6 artifacts were written separately.

The P02 feasibility check is a **no-go for broader enrichment** while the canonical
work population, prospective P03 frame, current free-resource limits, storage
budget, and actual reviewer capacity are unknown. No research-provider quotas,
Neo4j/GROBID health or storage allowance were checked and no new requests were
made. Independent accuracy, recall and F1 remain
unmeasured. P01 and full pregraph readiness remain incomplete.

[Source triage and official links](../docs/five-year-source-triage.md) ·
[Measured recovery report](five-year-source-recovery-v6.md) ·
[Current 170-row edition ledger](five-year-edition-ledger-v6.csv) ·
[P02 feasibility checkpoint](five-year-pregraph-feasibility-v1.md)

This dated report snapshot is prepared locally. The existing public Site remains
version 14 until this update is published through the Sites workflow.

## Historical official source recovery (D027; v5)

The preceding v5 report recorded **88 eligible editions / 85,802 included records**
and 82 edition gaps. Its source evidence, metrics and ledger remain available in
[the v5 report](five-year-source-recovery-v5.md),
[aggregate JSON](five-year-source-recovery-v5.metrics.json), and
[ledger](five-year-edition-ledger-v5.csv).

Earlier dated diagnostic stages below retain their original inputs and results.

## Preserved pregraph preparation — task 006

**No new graph has been built or imported.** The current frozen development
preparation is implemented; finishing its queue does not finish the planned
five-year network. Full scope, broader enrichment/canonical work and independent
quality prerequisites remain unmet. The historical explorer remains 399/533.

| Measure | Current development result |
| --- | ---: |
| Printed-source reviews | 19 |
| Source-accepted / withheld papers | 55 / 13 |
| Corroborated people / authorship supports | 10 / 11 |
| Reviewed affiliation triples / organizations | 12 / 9 |
| Affiliated author–paper pairs / selected positions | 9 / 346 |
| Known-frame work crosswalk records | 318 |
| Current queue rows with withheld dispositions | 339 |
| Original 345 rows: resolved / withheld | 8 / 337 |
| Uncalibrated topic candidates / papers | 17 / 16 |
| Accepted topic labels / citations | 0 / 0 |

Six further printed bylines recovered from parser errors; eight additional
paper-specific affiliation reviews. Original metadata/parser statuses preserved.
Known-frame work guards check exact DOI/provider/source IDs and reserved versions;
title matches can quarantine, never merge works. Zero detected conflicts in the
318 exposed diagnostic records does not certify global canonical completeness.

**Task 006 failed pregraph gates (v2 frame):** 91 unresolved/unavailable edition candidates,
full enrichment/work resolution, researcher/affiliation/accepted-topic coverage.
Topic calibration is unmeasured and independent component review has not run.
Abstract coverage on accepted source records is 54/55 (98.18%); that passing
availability check cannot replace the missing quality checks.

The preparation command writes support/crosswalk/candidate/disposition tables
and a content-addressed freeze receipt, with no graph artifact or DB write.
Blank two-reviewer development forms are ready locally; no annotations were
invented. They cover exposed development papers and cannot serve as release gold.
**156 offline tests passed**; source-disabled replay matches. **7,895 protected
artifacts / 369 source objects verified**; seven new public ORCID responses,
zero OpenAlex requests. Fresh end checks: GROBID healthy, Neo4j **154/211** and
**399/533**, matching the previous task. Independent accuracy/recall/F1 unmeasured.

[Pregraph readiness report](five-year-pregraph-v3.md) ·
[Measured pregraph aggregate](five-year-pregraph-v3.metrics.json) ·
[Current corroboration aggregate](five-year-corroboration-v3.metrics.json)

Earlier dated stages below retain their historical measurements.

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

This metadata tranche preceded the PDF stage below and accepted no identities or graph imports. OpenAlex used
**USD 0.067 of the daily free allowance**, with **USD 0.933 remaining** and zero prepaid
balance at the post-run check. **120 offline tests passed in that metadata iteration**; semantic accuracy,
recall and F1 remain unmeasured. Base Neo4j remains **154/211** after read-only checks;
Those were task 003 service checks; current service availability is recorded below.

[Measured collection/diagnostics report](five-year-collection-v2.md) ·
[All 170 edition statuses](five-year-edition-ledger-v2.csv) ·
[Measured summary JSON](five-year-collection-v2.json)

All historical v1 outputs and loaded/candidate graphs remain preserved. The native
explorer below still shows its dated **399/533 2023 snapshot**. It is not a five-year
graph. Internal cutoffs remain 8–10 November; preserve independent review/report
time, keep release gates unchanged and disclose actual shortfalls by 11 November.

## Selective development PDF headers — 6 November 2026

**68 PDFs cached locally; 66 headers parsed; two RSS 2025 records remain in parse review.**
All inputs are the frozen development sample; zero held-out papers were accessed.
The new sample covers 2021/2022/2024/2025, separate from the historical 2023 PDFs.

| Measure | Measured development result |
| --- | ---: |
| Selected / PDFs available | 68 / 68 |
| GROBID parsed / parse review | 66 / 2 |
| Papers with parsed affiliation blocks | 47 |
| Header titles / complete roster bylines agreeing | 62 / 48 |
| Papers passing candidate-binding checks | 45 |
| Deduplicated affiliation candidates | 255 |
| Exact author-specific institution candidates | 56 |
| Accepted new identities / affiliation triples / imports | 0 / 0 / 0 |

All affiliation outputs remain **review candidates**. Parsing success does not prove
correct bylines, printed markers or researcher identities. The MLSys PDF corroborates
the roster full byline, while its citation export uses an initial; its metadata
record remains withheld. One COLT header incorrectly includes proceedings editors
as authors, so its positional mappings are withheld. The two failed RSS PDFs have
visible text but no text extracted by `pdftotext`; OCR or another conversion method
is pending. Five printed pages were inspected as agent development evidence only.

**130 offline tests passed**, extraction replay reproduced the original summary,
**7,297 protected files remain unchanged**, and **269 source objects** were
hash-verified. No new OpenAlex requests or graph writes occurred. Neo4j was
154 nodes / 211 edges and GROBID was healthy at preflight. After extraction,
Docker became unreachable; fresh post-run service/database checks were unavailable.

[PDF/header report](five-year-headers-v1.md) ·
[Measured header summary JSON](five-year-headers-v1.metrics.json)

## Reviewed development identity and affiliation support — 6 November 2026

Five input/PDF-bound printed-source overlays recover the COLT author byline and
two RSS headers, record the MLSys full printed byline, and corroborate an IJCAI
shared block. These are agent source reviews, not successful OCR or an independent audit.
The original MLSys metadata failure and both RSS parser failures remain preserved.

| Measure | Measured development result |
| --- | ---: |
| Source-eligible papers after overlays / selected | 49 / 68 |
| Unique public ORCID responses | 84 |
| Corroborated unique researchers | 10 |
| Previously known / new researcher IDs | 1 / 9 |
| Accepted authorship support / supported papers | 11 / 9 |
| Reviewed author–paper–organization triples | 1 |
| Review queue rows, mixed claim units | 345 |
| Graph imports / held-out acquisition overlap | 0 / 0 |

Acceptance requires complete ordered source/provider bylines, stable identifiers
and the target publication in public ORCID works: six typed DOI corroborations,
five Unicode exact title/year corroborations. Affiliations additionally require
reviewed printed mappings and exact same-author institution metadata. Unsupported
and conflicting claims stay in review. This is a bounded development evidence
contract; **independent semantic accuracy, recall and F1 remain unmeasured**.

**145 offline tests passed**, identical replay plus a network-disabled replay;
**7,645 protected artifacts** unchanged and **362 source objects** hash-verified.
84 new public ORCID responses, zero new OpenAlex requests. Fresh pre/post Docker
checks: GROBID alive, original Neo4j **154/211**, extended **399/533**; no DB writes.
The historical explorer below remains **399/533**, separate from new support tables.

[Corroboration report](five-year-corroboration-v1.md) ·
[Corroboration aggregate JSON](five-year-corroboration-v1.metrics.json)

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
2023 editions remain unresolved; at v8, five-year source closure still has 26
unresolved roster/adapter and 40 access-unavailable candidates. No temporal
findings or
final ten-page report exist yet.

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

The historical checks above are separate from the new development extraction
checks reported earlier. Current publication checks are recorded
separately in the repository work log and publication receipt.

## Progress history

| Date | Work | Outcome |
| --- | --- | --- |
| 2 November 2026 | Repository initialization | Package, schema, documentation and synthetic validation |
| 3 November 2026 | Historical pilot | 100 diagnostic papers; loaded 154-node / 211-edge graph |
| 3 November 2026 | Venue expansion | 34-series registry; 17 covered 2023 editions; loaded 399 / 533 graph |
| 3 November 2026 | Visualization | Offline interactive explorer with provenance and filters |
| 4 November 2026 | Evidence review | 250 metadata / 240 parsed PDFs; 402 / 538 local candidate; two conflicts withheld |
| 6 November 2026 | Official OJS source recovery | 88 eligible editions / 85,802 included records; 82 gaps; 177 tests; no enrichment/graph |
| 6 November 2026 | Pregraph source closure and readiness freeze | 55 accepted / 13 withheld sources, 12 triples; full readiness false; 156 tests; no graph |
| 6 November 2026 | Reviewed development corroboration | 49 source-eligible papers; 10 people / 11 authorship supports / one triple; 345 review rows; no graph import; 145 tests |
| 6 November 2026 | Selective PDF/header diagnostics | 68 PDFs / 66 parsed; 255 affiliation candidates, none accepted; 130 tests; two parse-review records |
| 6 November 2026 | Corrected rosters and frozen metadata diagnostics | 79 eligible editions; 68 diagnostics / 170 tests frozen; 67 metadata / 36 strict matches; 120 tests; no new graph |
| 6 November 2026 | First five-year roster collection | 73,714 records; 67 eligible editions; all 170 candidates retained; no new graph; 108 tests |
| 6 November 2026 | Deadline-driven readiness plan | 11 November deadline; 170 unverified review rows; dated work packages and illustrative costs; execution paused |
| 7 November 2026 | ICAPS 2025 source correction and feasibility | 89 eligible editions / 85,850 included; 81 gaps; 181 tests; P02 no-go; no enrichment or graph; public Site remains v14 |
| 7 November 2026 | Official edition route closure and COLING 2024 | 90 eligible editions / 87,404 included; 70 gaps; 187 tests; no enrichment or graph; public Site remains v14 |
| 7 November 2026 | AAMAS official roster closure | 94 eligible editions / 88,211 included; four years resolved, 2023 held; 66 gaps; 193 tests; no enrichment or graph; public Site remains v14 |
| 7 November 2026 | ICLR official source-route review | Official routes identified; 2024 counts agree, 2025 counts differ; local API/DNS access blocked roster capture; no edition changes; public Site remains v14 |
| 4 November 2026 | Native Site report | Integrated graph, charts, filters, coverage and evidence in Report; no iframe or new research data |
| 4 November 2026 | Five-year planning and Site | 2021–2025 plan; one existing Site with Plan and Report tabs; no research collection |

## Next planned work

1. Resolve the 26 unresolved roster/adapter and 40 access-unavailable edition candidates
   through permitted official source/edition routes; keep AAMAS 2023 held until its
   title/byline/ID reconciliation is complete. The full 2021–2025 target remains unchanged.
2. Freeze a feasible prospective larger collection/review design before scaling,
   reconcile canonical versions and retain every old/new held-out group.
3. Obtain independent labels for topic/component quality; use the exposed development
   forms only for development calibration, with separate reviewers and adjudication.
4. Reassess failed full pregraph gates before a release graph. The current freeze
   authorizes no construction/import and must not be relabeled a complete release.

## Evidence and update policy

Current roster sources: `reports/five-year-source-recovery-v9.{md,metrics.json}`,
`reports/five-year-edition-ledger-v9.csv`, D032 and WORK-004. V8 and its original
ledger remain historical under D031 and WORK-002. V7 and its original
ledger remain historical under D030 and WORK-001. V6 and its original ledger
remain historical under D029 and WORK-009; v5 remains historical under
D027 and task 007.
Preserved pregraph sources: `reports/five-year-pregraph-v3.{md,metrics.json}`,
`reports/five-year-corroboration-v3.metrics.json`, D026 and task 006.
New development support sources: `reports/five-year-corroboration-v1.{md,metrics.json}`,
`data/manifests/five-year-source-corrections-v1.json` and task 005.
New PDF/header sources: `reports/five-year-headers-v1.{md,metrics.json}`,
`data/manifests/five-year-printed-review-v1.json` and task 004.
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
