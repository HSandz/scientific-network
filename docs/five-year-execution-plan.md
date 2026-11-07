# Five-year execution plan — deadline 11 November 2026

Planning revision: **6 November 2026, Asia/Bangkok (UTC+07:00)**. The user confirmed
**11 November 2026** as the submission date; the time of day was not specified.
Target submission-ready artifacts by **10 November, 18:00 +07:00**, leaving
11 November for final checks and upload. These internal cutoffs are proposals,
not a claimed lecturer deadline time.

**Execution update — 6 November 2026 (D022):** the user subsequently explicitly
authorized collection. E01/E02 roster work and preliminary E03 leakage triage have
started; D023 now freezes 68 development diagnostics / 170 new tests and records
67 acquired metadata papers, one byline withheld. No five-year import has run.
See [collection workflow](five-year-collection.md) and [status](status.md). The conditional language below records
the original planning state; D022 supplies the later authorization.

**This planning document itself authorizes no execution.** The user's “proceed” accepted writing
this plan and updating the existing Site. D018 remains in force: no pipeline
changes, source discovery, paper acquisition/enrichment, new splits or graph
imports. All execution packages below require a later explicit instruction.
No further capacity or lecturer answers are prerequisites to completing this plan.
Keep the existing proposed accuracy definition clearly labeled until confirmed;
do not silently change the course requirement or claim a measured score.

## 1. Scope, baseline and deadline priorities

Retain the planned **2021–2025** scope, **34 flagship series**, five entity labels,
ten predicates and existing release gates. The [readiness ledger](five-year-edition-readiness.csv)
has **170 venue–year candidates**, all pending new-scope verification. They are
review slots, not 170 confirmed editions or collected rosters. Source catalog
links are inherited leads, not newly checked endpoints. See
[scope policy](conference-scope.md), [temporal rules](five-year-scope.md),
[graph schema](graph-schema.md) and [evaluation protocol](evaluation.md).

Recorded historical evidence, not new scientific results in this task:

| Artifact | Version / recorded result | Implication |
| --- | --- | --- |
| Loaded expanded graph / native Site explorer | `pilot-topic-d512d7239923`; 399 nodes / 533 edges | Preserve this snapshot; no five-year coverage claim |
| Reviewed local candidate, not imported | `pilot-topic-7e3c90189547`; 402 nodes / 538 edges; 248 papers, 85 researchers, 32 organizations | Candidate and loaded graph remain distinct |
| Candidate factual edges | 372 unique R1–R4 | Gap to 5,000 is 4,628 at this snapshot; additions may reconcile/deduplicate, so it is not an acquisition quota |
| Candidate resolved researchers | 85 | Gap to 2,000 is 1,915; collecting paper nodes alone cannot meet this gate |
| Candidate coverage | 36/1,206 affiliated author–paper pairs (2.99%); 87/248 topic-labeled papers (35.08%) | Identity, author-specific affiliations and topic calibration need deliberate work |
| Predicates / independent accuracy | Eight types nonempty; semantic accuracy unmeasured | No all-ten-type or >90% accuracy claim |

Prioritize a correct, reproducible graph and substantive course report. Expansion
must not displace independent review, evidence inspection or writing. Defer new
UI, prediction, years outside the scope, training a general NER model and optional
GDS installation. Use established tools and, when implemented and verified,
NetworkX for named projections. Do not infer communities from display layout.

The recorded candidate does **not** establish that a complete, audited five-year
release can be delivered by 11 November. Preserve the targets; if gates remain
unmet, submit the best verified partial result with explicit shortfalls. Any
narrowing of the core year/venue boundary requires a separate documented decision.

## 2. Ordered work packages and acceptance checks

Roles A/B follow [the existing team responsibilities](team.md); they are role
labels, not invented names, attendance or committed working hours. Both review
scientific evidence independently where the evaluation protocol requires it.

| ID | Work and owner | Dependencies / status | Reviewable output and acceptance check |
| --- | --- | --- | --- |
| P01 | Deadline/readiness specification; both roles | Current planning task | This document, 170-row ledger and estimate JSON; every year/series appears once; all unverified statuses explicit; historical files unchanged |
| E01 | Read-only source/edition verification; A, B reviews track policy | Later execution authorization; P01 | A versioned edition ledger records official year, complete main-track roster route, rights, evidence/time and access status for every candidate; catalog leads alone never mark an edition verified |
| E02 | Five-year config/contracts and offline fixtures; A, B reviews | Later authorization; E01 policy sufficient to define fixtures | New executable config/version and additive contracts; tests cover cross-year editions, Unicode/same-name people, duplicate work versions, multiaffiliation and missing editions; old configs/IDs unchanged; no placeholder success |
| E03 | Official roster reconciliation and leakage groups; A, B reviews | E01 verified routes; E02 | Reconciled included/excluded counts per verified edition; stable work crosswalk and quarantined ambiguous versions; every old test version stays held out; no exposure moved into a new independent test set |
| E04 | Prospective diagnostic/component sample design; B, A reviews | E03; before enrichment/tuning | Document population/strata, probabilities, seed, review cost and untouched membership; preserve old assignments; freeze new IDs only after later authorization; reserve independent tests before development |
| E05 | Staged metadata and selected PDFs; A, B checks layouts | E04 freeze; quota/rights checks | Resumable hashed input manifests, source-specific bounded retries and explicit failures; a small batch spans newly verified source layouts and all five years where accessible before scaling; no held-out development leakage |
| E06 | Identity/affiliation and topic quality tranche; A identities/triples, B topics | E05 development evidence only | Stable corroborated people, exact author–paper–organization mappings, reversible reviews, held-out-independent calibration and abstention; compare coverage/error categories against historical baseline; never relax thresholds just to increase counts |
| E07 | Candidate graph, temporal derivations and safe DB import; A, B reviews | Accepted E06 base support | New isolated Neo4j Community service/volume/config; preserve existing DBs; validate keys, provenance, core support, fractional weights, window-specific support and union counts; replay is idempotent; DB tables/counts reconcile |
| E08 | Freeze independent evaluation and named analyses; B, both audit | Frozen E07 release frame and method; component tests isolated | Uniform 600-edge global audit plus separate per-type checks/census, reviewer records, precision/intervals, recall/coverage; no tuning against audit errors; named projections and source-supported findings only |
| E09 | Report, reproducibility package and Site update; both | Methods written early; final numbers depend on E07/E08 | ≥10 substantive pages, contribution table, actual code URL, input/config/method/graph versions, figures, limitations and setup; native Site Report matches its own graph snapshot; private inputs excluded; clean-clone/offline replay checks |

E02 can begin with fixtures while E01 verifies authorized source routes, but E03
cannot invent rosters. E06 development work can proceed alongside the remaining
E05 batches; no independent test/audit errors enter development. Start E09 writing
from existing verified methods immediately after execution authorization rather
than postponing the entire report to the final day.

### Edition-readiness ledger contract

`docs/five-year-edition-readiness.csv` is a **planning review queue**, not a corpus
manifest or executable config. It intentionally leaves edition evidence, reviewer
and verification time blank. Its historical 2023 roster status is a separate
context column and never promotes a five-year row to verified.

Future states: `verified_eligible`, `verified_no_edition`, `excluded_track`,
`access_unavailable`, `unresolved`, or `pending_edition_verification`. Only an
eligible edition with explicit evidence and a complete permitted roster route may
enter acquisition. A verified edition can still have an unresolved acquisition
route; distinguish existence, eligibility, adapter support and access. Attach
reason, official evidence, snapshot time and responsible reviewer. Keep failures
visible; do not infer a missing edition from a failed request. Keep immutable
copies of this planning ledger; future executable ledgers get new versions.

### Safe versions, leakage and database isolation

Future filenames are **proposed**, not files or capabilities created here:
`configs/corpus-five-year-v1.yaml`, `data/manifests/five-year-roster-v1/`,
`five-year-splits-v1/`, `data/processed/five-year-graph-v1.json` and separate
`neo4j-five-year` service/volume. Do not copy a five-year date range into an old
config and run it: adapter dispatch, source formats, IDs and temporal support must
be implemented and tested first.

Preserve all 5,046 legacy assignments and the expanded **925 test / 470 development /
13,514 pool** membership, plus all historical diagnostics. DOI/provider/source IDs
and corroborating bibliographic evidence support work links; title similarity
alone is insufficient. Connect versions into leakage groups before enrichment.
A connected group containing an old test stays test-only; mixed exposure/test
conflicts are quarantined and reported, not silently relabeled. Already exposed
papers can never become fresh independent tests. Reserved IDs do not imply that
all papers have been annotated or that an affordable representative test exists.
A prospective probability subsample must preserve the rest as held out, disclose
selection probabilities and report the narrower inference population.

Affiliations require paper-specific triples; no current-profile employment
inference. Recompute annual/cumulative R7–R10 from accepted support within each
window, retaining raw/fractional weights and distinct works. Keep one primary
venue per canonical work; annual entity totals may overlap. Citation statistics
need snapshot time, endpoint scope and age controls. Do not aggregate 2023 weights
and label them five-year temporal results. Existing loaded DBs remain untouched;
loader version conflicts are not resolved by deleting previous data.

## 3. Calendar: 6–11 November

All times below are **Asia/Bangkok, UTC+07:00**. Post-planning rows are conditional
on later execution authorization; dates do not grant it. If authorization arrives
late, keep validation/writing time protected rather than compressing every stage.

| Date | Priority / proposed checkpoint | Deadline guardrail |
| --- | --- | --- |
| 6 Nov | Complete P01; publish execution plan, ledger, effort scenarios and deadline on the existing Site; outline report from current evidence | No pipeline or source requests in this planning task |
| 7 Nov | If authorized: E01/E02/E03, then freeze E04 before E05; write source, schema and evaluation methods; start bounded new-layout diagnostics | Do not start broad enrichment before version/leakage/sample checks |
| 8 Nov | If authorized: prioritize E06 identity/affiliation quality and topic development; compare stage diagnostics; complete only sources that pass checks | **18:00: stop adding source families/features**; record unresolved rows and decide achievable frozen candidate boundary without silently changing core scope |
| 9 Nov | If authorized: finish accepted base evidence, E07 isolated import/replay and report statistics; freeze methods/graph for evaluation; begin E08 | **18:00: candidate and method freeze**; no additional broad acquisition. These cutoffs are a latest bound, not evidence that audit hours fit |
| 10 Nov | Finish independent checks if feasible, E09 report/figures, reproduction and native Site reconciliation | **12:00: record pass/fail/unmeasured gates**; **18:00: submission-ready package**. An audit failure leaves the release unqualified; no reused test after tuning |
| 11 Nov | Final page/links/contributions/privacy checks and submission at the actual course deadline | Submit verified results and disclosed gaps; do not launch broad collection or redesign |

E08 effort may exceed this calendar even with two reviewers. Assess the explicit
hour estimates below at the 7–8 November checkpoints using actual progress,
without requesting additional user inputs. If not feasible, preserve the frozen
sample and mark incomplete/unmeasured outcomes rather than reporting a passing
release. No date is evidence that a task has run.

## 4. Resource and annotation estimates

[Machine-readable assumptions and arithmetic](../reports/five-year-planning-estimates-2026-11-06.json)
separate local historical summaries from hypothetical future scenarios. No paid
API/service spend is authorized; existing Neo4j/OpenAlex setup is sufficient to
plan the work. Current connectivity, quotas, pricing and container health were
not checked. After later authorization, verify free allowance and request-credit
weights before the first batch, honor provider limits and stop at the allowance.

### Historical local sizing evidence

The existing `extended-headers-v5/papers.json` records 240 parsed PDFs: median
**1.3002 MiB**, maximum **34.7813 MiB**, total **0.7690 GiB** (sum by record, not
unique-object cache usage). These are historical selected 2023 papers, not a
representative sample of five years. The recorded extraction median is **0.004 s**,
which is cache-dominated and unusable as a cold GROBID throughput benchmark.
A later authorized batch must measure cold/warm parsing separately. This task
summarized local metadata only; it downloaded no PDFs and ran no parsing service.

### Illustrative future scaling envelopes

Let `N` be deduplicated eligible works after actual roster verification. The values
10k/50k/100k below are sensitivity scenarios, **not a corpus-size forecast**.
Assume 2–6 metadata HTTP requests per work, 50–200 KiB cached metadata per work,
PDF selection fraction 10–30%, 2–10 MiB per selected PDF, and **assumed** serial
cold parsing of 2–20 s/PDF. The PDF/runtime ranges are budget assumptions, not
empirical quantiles, provider commitments or guaranteed upper bounds.

| Hypothetical works N | Metadata requests | Metadata cache GiB | Selected PDFs | PDF GiB | Serial cold parse hours, assumed |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 10,000 | 20,000–60,000 | 0.48–1.91 | 1,000–3,000 | 1.95–29.30 | 0.56–16.67 |
| 50,000 | 100,000–300,000 | 2.38–9.54 | 5,000–15,000 | 9.77–146.48 | 2.78–83.33 |
| 100,000 | 200,000–600,000 | 4.77–19.07 | 10,000–30,000 | 19.53–292.97 | 5.56–166.67 |

Formulas: requests `N × [2,6]`; metadata GiB `N × [50,200] / 1,048,576`;
PDF count `ceil(N × [0.1,0.3])`; PDF GiB `count × [2,10] / 1024`;
serial hours `count × [2,20] / 3600`. Multiply request counts by actual provider
credit weights; estimate wall time from effective throttled rate plus retries.
These envelopes exclude edition discovery requests, reference/profile lookups,
reviewer time, blocked access, retries beyond the assumed range and DB processing.
Cache reuse may reduce new requests; response caps/ambiguity may increase them.

Reserve approximately 3× projected input bytes as an initial working/backup
allowance, **plus separately measured database/index/derived-edge space**. Large
coauthor teams can generate quadratic pair counts; do not size graph storage by
paper bytes alone. Actual free disk/RAM and cold service throughput need later
checks. Avoid full-corpus PDF downloads by default; selection must still support
unbiased coverage estimates rather than cherry-picking easy papers.

### Independent review budget and deadline risk

| Review activity | Explicit arithmetic / illustrative reviewer effort |
| --- | --- |
| Global edge audit alone | 600 edges × 2 reviewers × 3–6 min / 60 = **60–120 person-hours** |
| Global plus per-type audit | At most 600 + 10×100 = 1,600 distinct reviews before overlap/census reductions; 600–1,600 × 2 × 3–6 min / 60 = **60–320 person-hours** |
| Adjudication | Assume 10–25% of 600–1,600 rows need 5 additional person-minutes each: **5–33.33 person-hours**; joint review can cost more |
| Illustrative component gold set | 50 papers × 2 reviewers × 20–40 min / 60 = **33.33–66.67 person-hours**; 50 is an effort example, not an approved sample size or representative release test |

The edge audit and fully annotated component papers are different tasks; overlapping
evidence does not make one replace the other. Topic/affiliation ambiguity and
multi-page reference checking may take longer. Reserved 925 test papers are not
925 completed annotations or a requirement to blindly replicate old quotas onto
170 candidates. Freeze a feasible prospective design before enrichment; disclose
unsampled strata and inference limits. Do not spend the audit budget reviewing
thousands of development queue rows and then claim those as independent tests.

## 5. Release decisions and truthful partial delivery

Keep the existing proposed gates: **≥2,000 resolved core researchers**, **≥5,000
unique accepted factual R1–R4 edges**, all ten predicates genuinely supported,
no structural defects, and documented recall/coverage. The proposed global rule
is precision ≥95% with the two-sided 95% Wilson lower bound >90%; structural
checks are not that accuracy measure. Retain configured coverage targets (95%
abstracts, 80% author–paper affiliation and 80% topic paper coverage) and disclose
all misses. Never force all ten types with synthetic or weakly evidenced edges.

At candidate freeze and final packaging, write one explicit status per gate:
`passed_with_evidence`, `failed`, `not_run` or `unmeasured`. A candidate with fewer
than 600 edges cannot supply the proposed global audit; do not pad it or replace
it with an arithmetic Wilson example. Audit errors remain frozen. If a rule is
changed after inspection, a new version and fresh blind sample are needed for a
new independent claim; if time is insufficient, report the failed/limited result.

A partial submission still needs the ≥10-page report, actual contribution record,
clear actual corpus boundary, database/reproduction instructions, separate
factual/inferred/taxonomy/derived counts and limitations. Show **planned versus
achieved** years/venues/size/accuracy. Do not rename a 2023 diagnostic as a five-year
network, imply all 34 series are covered, or quietly invoke the course's optional
1,000-node narrowing allowance. Scope changes need an explicit decision.

Minimum final package: report PDF, code link and identified source revision,
permitted data manifests/configs, graph/evidence versions, setup/rebuild commands,
DB integrity/import-replay evidence, named-projection figures, quality/gap table,
team contributions and native Site URL. The configured code origin is
`git@github.com:HSandz/scientific-network.git`; the corresponding repository URL is
<https://github.com/HSandz/scientific-network>. It is recorded from local Git;
remote availability/privacy and clean-clone reproduction remain unchecked here.
Never publish credentials, PDFs without rights, private annotations or DB volumes.

## 6. Immediate handoff

P01 is the bounded planning deliverable. Read this plan and the ledger, then issue
a later explicit implementation/collection instruction before starting E01–E09
execution. With authorization, start edition readiness and offline contracts while
writing report methods, freeze leakage/sample membership before enrichment, and
prioritize identity/affiliation quality. The 11 November deadline does not lift
D018 or make an unrun audit a passing result. Publish subsequent measured progress
on the same [Plan & Report Site](https://ai-research-network-plan.hazy-tern-8113.chatgpt.site)
using [the native publication workflow](sites-workflow.md).
