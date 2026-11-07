# Completion plan: every prerequisite to the final graph

> **Superseded for the 11 Nov 2026 submission** by
> [D040](decisions.md#d040--release-reset-for-the-11-november-submission-2026-11-08)
> and the [release plan](release-plan.md). Its P00–P10 sequence and gates G01–G12
> no longer block release work. Kept as history.

Status: **execution tracking active under D022 and the user's proceed instruction; all stage gates remain binding**. This plan records required work and dependencies; it does not waive any gate for later enrichment, evaluation or graph construction.
Prepared **6 November 2026, Asia/Bangkok (UTC+07:00)**, after
[WORK-2026-11-06-007](work-log/2026-11-06-007-source-recovery.md).
Submission date: **11 November 2026**; exact submission time is unspecified.

This is the current task-level completion plan for work **before final graph
construction**. It expands E01–E06 and the preparation parts of E07–E09 in the
[execution plan](five-year-execution-plan.md). Existing scope, schema, acceptance
thresholds, protected samples and evidence rules remain in force. Old planning
language and historical measurements must be interpreted with their dates.
See the planning-boundary record [D028](decisions.md#d028--complete-pregraph-prerequisite-plan-documentation-only-2026-11-06).

### Execution checkpoint — D039 / WORK-022 / 8 November 2026

The connected browser captured hash-bound HTTP 200 responses for the official
CIKM 2025 accepted-paper page, proceedings page, and Full, Short, and Applied
Research calls. The accepted page has 827 unique IDs across seven categories:
436 Full Research, 185 Short Research, 93 Applied Research, 52 Resource, 37
Demo, 11 PhD Symposium, and 13 Industry Day. Full and Short are candidate
research tracks; the separate Applied call describes a track distinct from the
Research Track, with no new project-specific inclusion decision.

The proceedings page has 852 unique ACM Digital Library links. Exact normalized
title comparison matches 789 accepted records; exact title plus author-set
comparison matches 697 overall and 531 Full/Short records. The proceedings page
does not expose accepted-list IDs; 38 accepted titles and 63 publisher records
have no exact title match. No record-level candidates were adjudicated. The
research calls require an author to register and present on-site for proceedings
inclusion. Captured pages provide no metadata license or bulk-reuse authorization.
CIKM 2025 remains `access_unavailable` in v10; no roster or frozen assignment changed.
See [D039](decisions.md#d039--cikm-2025-browser-source-audit-2026-11-08),
[source corrections v12](../data/manifests/five-year-source-corrections-v12.json),
[source triage](five-year-source-triage.md#cikm-2025-browser-source-capture-work-022),
and [WORK-022](work-log/2026-11-08-022-cikm-2025-browser-source-capture.md).

P02 remains **no-go**: the user reports one reviewer, unknown hours, and no
second independent reviewer confirmed. No enrichment, split, paper PDF, graph,
or database operation occurred. The local Report was refreshed, but the existing
public Site remains at version 18. `get_site` confirmed its current public
identity and URL; the supported helper failed before checkout with
`Unable to prepare the Site.`, so no Site source audit, push, build, or publication
occurred and the local snapshot is not live.

### Execution checkpoint — D038 / WORK-021 / 8 November 2026

The connected browser recaptured the official ACM Multimedia 2024 accepted-ID
file. Its decoded 5,497-byte body has 1,149 unique numeric IDs and matches
WORK-017's body hash. The regular-paper call clarifies that there is no
long/short distinction for regular papers. The separate BNI call says accepted
BNI papers are full papers in the main proceedings, with a separate review
committee and criteria. A converted full-program view exposes only a partial
paper-ID listing and was not captured as hash-bound source bytes. The direct local
HTTP retry failed DNS. The official research-track statistic remains 1,150
acceptances; the complete roster join and metadata reuse terms remain unresolved.
ACM Multimedia 2024 stays `access_unavailable`; no roster or frozen-assignment
change was made. See [D038](decisions.md#d038--acm-multimedia-2024-browser-source-follow-up-2026-11-08),
[source triage](five-year-source-triage.md#acm-multimedia-2024-browser-source-follow-up-work-021),
and [WORK-021](work-log/2026-11-08-021-acmmm-2024-browser-source-review.md).

The user reports one reviewer with unknown hours and no second independent
reviewer confirmed. P02 remains no-go for broader enrichment. No enrichment,
split, paper PDF, graph or database operation occurred.

### Execution checkpoint — D037 / WORK-020 / 8 November 2026

The ICDM 2025 accepted-page, main CFP, separate BlueSky call and official program
were directly recaptured with HTTP 200 responses, retained headers and body hashes.
The accepted page contains 105 Regular and 70 Short entries (175 unique IDs), but
the CFP says there was no separate short-paper submission track and makes
proceedings inclusion conditional on registration and presentation. The schedule
contains 97 distinct DM IDs and does not reconcile the accepted list to the final
publisher set. A candidate IEEE Xplore contents request returned HTTP 418; no
bypass was attempted. The source pages give no metadata license or bulk-reuse
permission. ICDM 2025 remains unresolved; no v11 roster or eligibility change was
made. See [D037](decisions.md#d037--icdm-2025-accepted-list-audit-2026-11-08),
[source corrections v10](../data/manifests/five-year-source-corrections-v10.json),
[source triage](five-year-source-triage.md#icdm-2025-official-accepted-list-audit-work-020),
and [WORK-020](work-log/2026-11-07-020-icdm-2025-offline-source-audit.md).

V10 remains at **98 eligible / 10 verified no-edition / 22 unresolved / 40
access-unavailable editions**, with **94,857 observations** (91,355 included;
3,502 excluded). All **76,629 assignments**, including **1,095 tests**, remain
protected. All 42 v10 output hashes and all seven five-year split input hashes
verified in this task. P01 remains incomplete with 62 candidate gaps. P02 remains
no-go: the user reports one reviewer with no exact hours known and no second
independent reviewer confirmed. No roster, split, enrichment, PDF, graph or
database change occurred. The public Site was confirmed at v18; after local DNS
recovered, the supported helper still failed before checkout with a generic
preparation error, so no Site source audit, push, build or publication occurred.

### Execution checkpoint — D034 / 7 November 2026

The direct MICCAI 2022 source follow-up recovered hash-bound official pages after
the prior HTTP 522. The accepted-paper index has **573 unique records** and the
topic-category page has 572. The eight Springer main-volume contents sets have
**576 unique chapter records**; their descriptions say **574 revised full papers**
and the refreshed series index remains at 576. A normalized-title join has 558
unique exact pairs, with 15 accepted-index records and 18 Springer chapters outside
that exact-title join; three unmatched chapter titles are correction notices.
No byline adjudication was made for the remaining title differences. The official
program documents do not resolve the one-record count difference. MICCAI 2022
remains unresolved, with no v11 roster or eligibility change. See [D034](decisions.md#d034--miccai-2022-official-route-follow-up-2026-11-07),
[source corrections v9](../data/manifests/five-year-source-corrections-v9.json),
[source triage](five-year-source-triage.md), and [WORK-007](work-log/2026-11-07-007-miccai-2022-source-followup.md).

The current roster remains **v10: 98 eligible editions, 10 verified no-edition
findings, 22 unresolved roster/adapter editions and 40 access-unavailable
editions**; its 94,857 observations include 91,355 and exclude 3,502. The 62
incomplete candidates keep P01 failed. All 76,629 frozen assignments, including
1,095 tests, and the v2-bound diagnostic/pregraph inputs remain protected. P02
remains **no-go for broader enrichment**. No split, enrichment, paper PDF, graph,
or database operation occurred in WORK-007.

### P01 ACM Multimedia 2024 source follow-up — WORK-017 / 7 November 2026

The official conference-hosted `accepted_papers.txt` was captured locally: 1,149
unique numeric values in 5,497 bytes, with SHA-256
`00441e7cd5f52a8030d6b5d316c66bae7707021fddb2a3647c3dd1e0d2c25fc2`. The
official research-track statistics page reports 1,150 acceptances from 4,385
submissions (26.20%). The regular-papers URL remains a JavaScript shell in its
7,508-byte capture; its JS assets could not be fetched after DNS resolution
failed. The official file index exposes a full program, but its Search-rendered
view is not a local hash-bound source or a complete accepted-to-proceedings join.
The regular-paper call and separate Brave New Ideas call leave the ID file's
track coverage unclear, and bulk reuse terms remain unverified. The one-record
difference and BNI disposition are not inferred.

ACM Multimedia 2024 remains `access_unavailable` in roster v10. No v11 roster or
source correction was created. All 42 v10 outputs and five frozen-input hashes
verify; v10 remains at **98 eligible / 10 verified no-edition / 22 unresolved /
40 access-unavailable editions**, with **94,857 observations** (91,355 included;
3,502 excluded). All **76,629 assignments**, including **1,095 tests**, remain
unchanged. P01 retains 62 incomplete candidates. P02 remains no-go: one reviewer
is reported, exact hours are unknown, and a second independent reviewer is
unconfirmed. The approved Sites helper again failed before checkout because
`git.chatgpt-team.site` did not resolve; the Site remains v18, and no push,
build or publication occurred. See [D035](decisions.md#d035--acm-multimedia-2024-official-source-hold-2026-11-07),
[source triage](five-year-source-triage.md#acm-multimedia-2024-official-source-follow-up-work-017),
and [WORK-017](work-log/2026-11-07-017-p01-acmmm-2024-source-closure.md).

### P01 ICDM 2021 accepted-list follow-up — WORK-018 / 7 November 2026

The official accepted-paper page lists **197 unique IDs** (98 Regular Papers and
99 Short Papers); all 197 also occur in the official schedule. The schedule has
239 unique DM IDs. Its 42 additional IDs occur in separately named workshop
events (40) or a PhD Panel event (2), so they are not added to the accepted-list
roster. The PhD Forum call is a separate doctoral submission route, but the two
PhD Panel items were not individually linked to its proceedings. The conference
call says accepted papers appear in IEEE Computer Society proceedings. The local
IEEE Xplore proceedings request returned HTTP 418; no bypass was attempted.
University copyright terms distinguish University-owned from third-party
material, and page-level ownership or bulk metadata reuse permission was not
established. The complete proceedings join and permission boundary therefore
remain open; ICDM 2021 stays unresolved with no v11 roster. See [D036](decisions.md#d036--icdm-2021-official-source-hold-2026-11-07),
[source triage](five-year-source-triage.md#icdm-2021-official-accepted-list-follow-up-work-018),
and [WORK-018](work-log/2026-11-07-018-icdm-2021-source-closure.md).

### P01 CIKM 2025 local source recapture recheck — WORK-019 / 7 November 2026

The official Search-rendered accepted-paper and proceedings pages visibly
separate Full Research, Short Research, Applied Research, Resource, Demo, PhD
Symposium, and Industry Day categories. The full/short calls describe research
papers; separate categories still require the existing per-track policy review.
Search output is route/track evidence only and does not provide hash-bound origin
bytes or a complete accepted-to-proceedings reconciliation. A fresh scan of 55
unique hosts referenced by the scope registry and source triage resolved none;
ordinary `curl` requests to both CIKM pages failed with exit 6 before response
bytes were returned. CIKM 2025 remains unresolved in v10; no track, roster, or
source-rights disposition changed. The DNS and request outcomes are recorded in
[WORK-019](work-log/2026-11-07-019-p01-cikm-2025-source-recheck.md) and its
ignored run artifacts. Reopen when local official-host resolution and permitted
source capture are available.

V10 remains current at **98 eligible / 10 verified no-edition / 22 unresolved /
40 access-unavailable editions**, with **94,857 observations** (91,355 included;
3,502 excluded). P01 still has 62 incomplete candidates. All **76,629 frozen
assignments**, including **1,095 tests**, remain protected. P02 remains no-go:
one reviewer is reported, exact hours are unknown, and a second independent
reviewer is unconfirmed. No split, enrichment, PDF, graph or database operation
occurred. The local Report was refreshed; public Site publication status is
recorded in WORK-018.

### P01 route follow-up — WORK-008 / WORK-009 (7 November 2026)

The bounded AAMAS 2023 identifier scan reverified all six official capture hashes.
The accepted page has no per-entry ID or DOI, while 528 proceedings PDF IDs have
no accepted-page crosswalk. Exact ordered-byline comparison yields 196 unique
candidates, but 40 accepted entries have no candidate and one has multiple; none
of these candidate joins was adjudicated. AAMAS 2023 remains unresolved.

The ICLR 2024 official group identifies the `Submission` invitation, but the
documented OpenReview notes endpoint returned HTTP 403
`ChallengeRequiredError`. No challenge was attempted and no full roster was
captured. All five ICLR years remain unresolved. See [source triage](five-year-source-triage.md)
and [WORK-008](work-log/2026-11-07-008-aamas-2023-followup.md) /
[WORK-009](work-log/2026-11-07-009-iclr-official-roster-access.md).

Roster v10 remains current at **98 eligible editions, 10 verified no-edition
findings, 22 unresolved roster/adapter editions and 40 access-unavailable
editions**; 94,857 observations include 91,355 and exclude 3,502. The same 62
incomplete candidates keep P01 failed. All 76,629 frozen assignments, including
1,095 tests, and v2-bound inputs remain protected. P02 remains no-go for broader
enrichment. No eligibility, roster, split, enrichment, graph, or database change
occurred. The existing public Site is version 18; its receipt records the current
aggregate source-access limitation.

### P01 route follow-up — WORK-010 (7 November 2026)

Official ICDM accepted-paper routes were found for 2021, 2024 and 2025, alongside
2022/2023 program sources. Official ICRA materials point to PaperPlaza and
InfoVaya; IROS program material identifies separate conference, journal-transfer,
late-breaking and workshop content. These are source leads, not complete
hash-bound rosters. Direct local retrieval failed DNS resolution, and the Search
connector's robots policy prevented PaperPlaza retrieval. Rights for bulk metadata
reuse and complete proceedings crosswalks remain unverified. No bypass or gated
access attempt was made. The distinctions and route links are recorded in
[source triage](five-year-source-triage.md#icdm-icra-and-iros-official-route-review-work-010)
and [WORK-010](work-log/2026-11-07-010-ieee-edition-route-review.md).

All 15 ICDM/ICRA/IROS editions remain unresolved. Roster v10 remains at **98
eligible editions / 10 verified no-edition findings / 22 unresolved roster or
adapter editions / 40 access-unavailable editions**, with 94,857 observations
(91,355 included; 3,502 excluded). The 62 incomplete candidates keep P01 failed.
All 76,629 frozen assignments and v2-bound inputs remain unchanged; P02 remains
no-go. No roster, split, enrichment, PDF, graph or database output was created.

### P01 alternate official publisher routes — WORK-011 (7 November 2026)

The Search connector identified official accepted-paper or program routes for
selected KDD, The Web Conference, SIGIR, WSDM, RecSys, CIKM, ACM Multimedia and
SIAM SDM editions. Several sources separate main research from applied, short,
resource, industry, demonstration or Blue-Sky content; CIKM 2025 and KDD 2025
also expose multiple main/applied tracks or proceedings volumes. These are
route leads only. Direct local HTTP requests still fail DNS, and Search-service
requests for the SIAM 2025 and ACM Web Conference 2024 proceedings returned 403.
No accepted-to-proceedings reconciliation, complete hash-bound source capture or
reuse authorization was established. Roster v10, all 76,629 frozen assignments,
the **40 publisher-access candidates**, and every edition disposition are
unchanged. See [WORK-011](work-log/2026-11-07-011-acm-siam-source-route-review.md)
and the [source triage](five-year-source-triage.md#acm-and-siam-official-route-review-work-011).

### P01 CIKM proceedings route — WORK-012 (7 November 2026)

Search-service views of the official CIKM 2025 accepted-paper and conference
proceedings pages show separate Full Research, Short Research, Applied Research,
Resource, Demo and PhD Symposium categories, with proceedings records linking to
ACM Digital Library entries. This identifies an official reconciliation route
that was not captured in the prior route note. The view is not a local hash-bound
source capture and does not establish a complete accepted-to-proceedings join or
bulk-reuse rights. The Applied Research disposition remains unresolved under the
current `main_archival_research_papers` policy. No edition disposition or roster
v10 output changed; P01 still has 62 incomplete candidates.

The approved Sites-source operation also failed before checkout: the supported
helper could not resolve `git.chatgpt-team.site`. The existing public Site remains
at v18; no source audit, push or publication was completed. See [WORK-012](work-log/2026-11-07-012-pregraph-source-followup.md)
and the [source triage](five-year-source-triage.md#cikm-2025-proceedings-route-follow-up-work-012).

### P02 local resource snapshot — WORK-013 (7 November 2026)

The current workspace measured 783.40 GiB available disk, 3.96 GiB host-available
memory, and 3.65 GiB apparent size across the existing manifests/raw/interim/
processed/reports-run directories. The visible `init.scope` cgroup exposes no
memory/CPU quota, while Docker volume usage is unavailable because the Docker
socket denied access. This is a dated local-environment snapshot, not a forecast
for full-corpus acquisition, backups, graph volumes or production processing.
P02 remains **no-go** pending P01 closure, the canonical work frame, prospective
P03 design and measured bounded-batch costs. The user reports one reviewer with
no exact available hours; a second independent reviewer is unconfirmed, so the
required audit capacity is not established. See
[feasibility snapshot](../reports/five-year-pregraph-feasibility-v1.md#p02-local-workspace-snapshot--work-013-7-november-2026)
and [WORK-013](work-log/2026-11-07-013-p02-resource-snapshot.md).

### P09 named-projection analysis — WORK-015 (7 November 2026)

Implemented the offline `analyze` stage for the five configured graph projections.
It validates graph structure, preserves configured edge strength/direction, reports
components and centrality metrics, uses deterministic power-iteration PageRank and
seeded NetworkX Louvain communities on the two collaboration projections. Frozen
strict evidence filters can generate baseline-versus-filtered metrics, top-k
overlap, rank correlation and largest-component share. Non-synthetic graphs are
gated on size thresholds, a matching post-build receipt, and a frozen analysis
config/filter. Synthetic output is `synthetic_protocol_only`. The CLI smoke used
only the invented fixture; no business finding or research result was generated.
The focused suite passed 10 tests and the full suite passed 216. See the
[analysis workflow](analysis.md), [WORK-015](work-log/2026-11-07-015-offline-analysis-stage.md),
and ignored [synthetic run artifact](../reports/runs/WORK-2026-11-07-015/synthetic-analysis-v2.json).

### P09 component evaluation contracts — WORK-016 (7 November 2026)

Implemented the offline `evaluate` command with a versioned frozen-frame contract,
two reviewer label joins, reasoned adjudications, declared evidence locators,
prediction-before-review timestamps, sampling weights, component precision/
recall/F1, topic per-label/macro scores, researcher/organization pair-type errors,
reviewer agreement and eligible-core coverage. Synthetic protocol tests cover all
five component families plus a disagreement/adjudication case. Synthetic results
are `ineligible_synthetic`; real scoring requires a reserved test frame, frozen
quality config and the complete eligible release-core coverage denominator. The
current quality config is still proposed; reviewer identity/independence, blinding
and source evidence are not authenticated. P07, the final edge audit, citation-age
and coverage analysis, figures, portfolios and source-backed findings remain
incomplete. No real score, release claim, roster, split, enrichment or graph was
produced. The missing strict-filter hash helper found after WORK-015 was added and
covered. The existing public Site was confirmed at v18; its approved source update
failed before checkout when the helper could not resolve its Git host, so no push
or publication occurred. See [evaluation protocol](evaluation.md) and
[WORK-016](work-log/2026-11-07-016-p09-evaluation-contracts.md).

P01 still has 62 incomplete candidates; fresh local resolution previously failed
for all 12 checked official/Sites hosts. P02 remains no-go with one reviewer of
unknown availability and a second unconfirmed.

### Previous P09 edge-audit packet tooling — WORK-014 (7 November 2026)

Added standalone `freeze-audit-sample` and `score-edge-audit` utilities for the
future post-build edge audit. They bind the sample and review rows to the graph,
canonical full edge-frame hash, quality-config hash, post-build readiness receipt
hash and method version; sample 600 global edges and 100 per relation (or census a
smaller type); require two distinct reviewer IDs and reasoned adjudication for
disagreements; and report Wilson intervals without pooling per-type supplements
into the global estimate. A
non-synthetic graph needs a matching post-build readiness receipt and must pass
the configured size/relation gates before sample preparation. Synthetic use is
marked protocol-only. This does not implement component recall/coverage, verify
reviewer identities, perform a real audit, complete P09 or certify a release;
`analyze` and `evaluate` remain nonzero placeholders. See [evaluation protocol](evaluation.md),
[WORK-014](work-log/2026-11-07-014-p09-offline-contracts.md), and the focused
tests in `tests/test_edge_audit.py`. The focused check passed 13 tests; the latest
full offline suite passed 212. The v4 CLI sampling/scoring pass used only the
invented synthetic fixture and an invented two-review packet; it produced a
`synthetic_protocol_only` result and performed no human review.

### Previous checkpoint — D033 / 7 November 2026

P01 continues from roster v10. MICCAI 2024 is now eligible: its 856 Society
accepted research records reconcile one-to-one with 856 unique Springer chapters
across all 12 main volumes. The additional 857th publisher chapter is a correction
tied to an already-listed paper and is excluded as nonresearch. The roster has
**98 eligible editions, 10 verified no-edition findings, 22 unresolved
roster/adapter editions and 40 access-unavailable editions**. It contains
**94,857 observations: 91,355 included and 3,502 excluded**. The 62 incomplete
candidates keep P01 failed. All 76,629 frozen assignments, including 1,095 tests,
remain guarded. P02 remains **no-go for broader enrichment** while the canonical
population, prospective P03 frame, live resource/storage limits and reviewer
capacity remain unmeasured. The diagnostic/pregraph inputs remain bound to v2.
See the [v10 measured report](../reports/five-year-source-recovery-v10.md),
[v10 ledger](../reports/five-year-edition-ledger-v10.csv), [D033](decisions.md#d033--miccai-2024-full-proceedings-reconciliation-2026-11-07),
and [current status](status.md). This checkpoint does not certify a pregraph gate
or authorize work outside the existing boundaries.

### Previous checkpoint — D032 / 7 November 2026

Roster v9 closed MICCAI 2021, 2023 and 2025 and held 2022/2024 unresolved. Its
ledger had 97 eligible editions and 63 incomplete candidates. See the [v9 report](../reports/five-year-source-recovery-v9.md)
and [D032](decisions.md#d032--miccai-roster-closure-and-unresolved-edition-counts-2026-11-07).

### Historical checkpoint — D031 / 7 November 2026

P01 source recovery continues under the user's instruction to proceed. Roster v8
adds complete, permitted official AAMAS rosters for 2021, 2022, 2024 and 2025;
AAMAS 2023 stays unresolved pending exact publication-ID/byline reconciliation.
The current ledger has **94 eligible editions, 10 verified no-edition findings,
26 unresolved roster/adapter editions and 40 access-unavailable editions**. It contains
**91,712 observations: 88,211 included and 3,501 excluded**. The 66 incomplete
candidates keep P01 failed. All 76,629 frozen assignments, including 1,095 tests,
remain guarded. P02 is still **no-go for broader enrichment** while the canonical
population, prospective P03 frame, live resource/storage limits and reviewer
capacity remain unmeasured. See [the v8 measured report](../reports/five-year-source-recovery-v8.md),
[the v8 ledger](../reports/five-year-edition-ledger-v8.csv), and
[current status](status.md). This checkpoint does not certify a pregraph gate or
authorize work outside the existing boundaries.

### Previous checkpoint — D030 / 7 November 2026

P01 source recovery has started under the user's later instruction to proceed.
Roster v7 records **90 eligible editions, 10 verified no-edition findings, 30
unsupported adapters and 40 access-unavailable editions**, with 87,404 included
records from 90,163 observations. The official COLING 2024 joint proceedings are
counted once under COLING. The remaining 70 incomplete candidates keep P01 failed.
P02 remains **no-go for broader enrichment**: the canonical population,
prospective P03 frame, live resource/storage limits and reviewer capacity remain
unmeasured. See [the v7 measured report](../reports/five-year-source-recovery-v7.md)
and [current status](status.md). This checkpoint updates evidence; it does not
certify any pregraph gate or authorize work outside the documented boundaries.

Completing the plan means delivering a measured, reproducible, independently
checked set of accepted tables and a genuine readiness decision. A schedule,
closed review queue, larger roster or successful software suite cannot substitute
for the evidence. If an external prerequisite cannot be satisfied, keep the full
release blocked and state the precise shortfall; this plan cannot guarantee
access, human annotation or completion by the deadline.

## 1. Boundary and definition of done

### Work to finish before construction

- Resolve the official edition/track population and source rights/access paths.
- Reconcile versions, protect held-out work families and freeze a feasible sample
  and collection design before additional enrichment or tuning.
- Complete the intended release population's metadata, selective document parsing,
  accepted work/person/organization resolution, author-specific affiliations,
  supported topics and verified in-core references, with explicit missingness.
- Freeze methods/taxonomy, obtain independent component evaluations, measure
  coverage and prepare accepted tables with reproducible evidence and decisions.
- Prepare and test the release builder, temporal derivations, evaluation/analysis
  tools and isolated Neo4j import path using synthetic/permitted development inputs.
- Prepare report methods, provenance, reproduction instructions, audit protocols,
  resource estimates and a content-addressed final preparation bundle.

### Work that necessarily follows construction

The actual final graph artifact, R7–R10 materialization on that artifact, Neo4j
import/count reconciliation/idempotence, graph statistics and named network
analyses all require construction. The **uniform 600-edge release audit** needs
the complete frozen graph edge frame. Final findings, final report results/PDF,
release exports and a matching new Site explorer depend on those outputs.

Prepare their code, contracts and protocols in advance; do not mark their actual
results complete before the graph exists. A component test or table preflight is
not the final graph audit. Passing preparation permits consideration of the next
stage; it does not certify a course-ready release.

### Invariants

Keep **2021–2025**, **34 flagship series**, the [five entity labels and ten
predicates](graph-schema.md), Neo4j Community and all thresholds in
[quality.yaml](../configs/quality.yaml). Preserve the original/expanded 2023
artifacts, all frozen memberships, raw cache objects, reviews and diagnostic
freezes. Use new executable/output versions; never repoint an old frozen config
at a different roster or silently rewrite failed runs.

No name-only person merges, title-only work merges, current-profile historical
employment inference, paper-wide affiliation products or context-paper padding.
Preserve raw fields, stable IDs, reversible crosswalks and accepted/review/withheld
states. Agent review and human-independent evaluation must remain distinguishable.

## 2. Starting evidence and gaps

The following are the D028 baseline recorded on 6 November and checked against
task 007's reports for the original plan. They are not new collection or newly
rerun benchmarks. The current source counts are in the D031 checkpoint and exact
backlog below; the remaining evidence stays a dated planning baseline.

| Item | Evidence at plan drafting (D028) | Remaining work at that checkpoint |
| --- | --- | --- |
| Edition ledger | 170 candidates; 88 eligible, 41 unresolved, 40 unavailable, one needs review | Resolve scope and complete eligible rosters; retain all statuses |
| Roster v5 | 88,608 observations: 85,802 included, 2,758 excluded, 48 review | Deduplicate canonical works; roster counts are not people/edges |
| Frozen membership | 76,629 guarded assignments; 1,095 tests, including 925 historical + 170 new | Preserve every assignment/version and design supplements prospectively |
| Newer development diagnostics | 68 papers / 346 author positions; 55 accepted source records, 13 withheld | Correct evidence failures without forced acceptance; broaden representatively |
| Accepted diagnostic support | 10 researchers, 11 authorships, 12 affiliation triples covering nine author–paper pairs | Major identity/affiliation coverage and scale gap |
| Topic/reference staging | Zero accepted topic labels or citations in the newer tranche | Calibrated topics and explicit reference/target verification |
| Canonical works | 318 exposed diagnostic records checked in the known frame | Release-wide work/version resolution; alternate-title detection remains incomplete |
| Preparation freeze | `five-year-pregraph-v3`, still bound to roster v2; readiness false | A new release-capable preparation contract and freeze |
| Human labels | Blank development forms; independent component scores unmeasured | Real independent annotations, adjudication and untouched testing |
| Services and software | Last iteration: 177 tests; existing historical DB/explorer snapshots | Future checks at execution time; no current health or new semantic score implied |

Sources: [roster recovery](../reports/five-year-source-recovery-v5.md),
[170-row ledger](../reports/five-year-edition-ledger-v5.csv),
[preserved readiness report](../reports/five-year-pregraph-v3.md),
[current status](status.md). Historical graph researcher counts cannot be added to
newer diagnostic counts: reconcile identities and support before any union total.

### Exact source backlog

| Group | Candidates | Action to plan and verify |
| --- | ---: | --- |
| Unresolved adapter/roster editions | 22 | Twenty-one source/adapter gaps across ICLR, MICCAI (2022), ICDM, ICRA and IROS (2021–2025); ICDM 2021 has a captured accepted list and schedule comparison, but its proceedings crosswalk and metadata reuse rights remain unresolved. Plus AAMAS 2023, whose accepted-paper/proceedings reconciliation remains incomplete |
| Missing verified edition routes | 0 | The 11 route findings from the v7 checkpoint have been resolved: ten official no-edition findings and the COLING 2024 joint-edition mapping. Preserve their evidence and do not infer editions from cadence |
| Restricted publisher routes | 40 | ACM Multimedia, KDD, WWW, SIGIR, WSDM, RecSys, CIKM and SDM: each 2021–2025. Seek permitted official conference/authoritative proceedings alternatives or lawful bibliographic exports with complete track evidence; retain publisher restrictions |
| Unknown track categories | 0 | ICAPS 2025 categories were resolved in v6 under D029. Preserve the accepted-main-research and position-paper dispositions |

These groups total **62** incomplete candidates at the D033 checkpoint, not 62
necessarily existing eligible editions. The source/route and ICAPS track findings above are closed for
the current ledger; AAMAS 2023 is still unresolved. Never substitute a neighboring
year or double-count one primary proceedings work.

An inaccessible source may be operationally triaged but is still a scope-coverage
failure. Recording all 170 rows does not satisfy complete coverage. If no lawful
complete route exists, report the blocker; narrowing the release or accepting a
partial-scope claim needs a separate documented user decision. No such exception
is approved here. Secondary indexes can identify leads, not replace official
acceptance/track evidence without an explicitly justified policy decision.

## 3. Roles, execution order and task ledger

A and B are the existing proposed teammate roles in [team.md](team.md), not names,
student IDs or promised hours. The agent can engineer collectors, checks and review
packets; it cannot impersonate two independent reviewers. Record actual identities
when reviews occur. Each task gets its own work entry and versioned artifacts.

Dependency order:

```text
P00 integrity and contracts
  -> P01 official scope closure
  -> P02 feasibility and collection budget
  -> P03 preliminary work groups + prospective supplemental split freeze
  -> P04 development calibration loop (bounded collection -> source repair
         -> identity/affiliation/topic development -> independent dev review)
  -> P05 frozen methods + staged production acquisition
  -> P06 final canonical/support closure + P07 independent component evaluation
  -> P08 preflight inventories + P09 tooling/reproduction/report preparation
  -> P10 immutable preparation freeze and go/no-go
  -> STOP: final graph construction is the next, separate stage
```

P02 resource planning can begin while P01 proceeds; budgeted development collection
requires P03. P09 synthetic tooling/report methods can proceed alongside P04–P07.
Final work/version and leakage checks run again after enrichment introduces new
identifiers. These dependencies do not override D022's staged-collection boundary
or the current D029/D030 stop on broader enrichment and graph construction.

| ID | Work package | Owner / review | Dependencies | Completion evidence |
| --- | --- | --- | --- | --- |
| P00 | Integrity inventory and release contracts | Agent/A; B checks | None | Hash inventory, existing-state map, proposed version names and tests |
| P01 | Edition/track closure and complete official rosters | Agent/A; B checks policy | P00 | All 170 dispositions with evidence; every eligible roster complete and reconciled |
| P02 | Feasibility, free-resource and reviewer budgets | Agent; A/B assess actual review effort | P00; final sizing uses P01 | Executable batch limits, measured development yields, storage/request/runtime estimates and explicit stop decision |
| P03 | Work/version guards and supplemental probability design | Agent/A; B checks design | P01/P02 | Pinned frame, preserved assignments, test-before-development allocation and probabilities |
| P04 | Bounded development, source repair and calibration | Agent/A/B; independent A/B labels | P03 | Complete diagnostic dispositions, evidence-backed repairs, frozen annotation guide and calibrated method candidates |
| P05 | Frozen methods and production collection | Agent/A; B checks batch summaries | P04 development acceptance; resource gate | Intended population reconciled to acquisition/extraction states; resumable immutable evidence |
| P06 | Final canonical entities and accepted support tables | Agent/A; B checks decisions | P05; recheck P03 guards | Canonical IDs, accepted publication evidence/triples/topics/citations, rejected/review queues |
| P07 | Independent component evaluation and coverage | A/B independently; agent computes metrics | Frozen P04 methods; sealed test collection; P06 outputs | Original labels, adjudication, weighted P/R/F1/coverage and target comparisons |
| P08 | All-ten-predicate and release-size preflight | Agent/A; B verifies support rules | P06/P07 | Exact relational inventories and derivation eligibility, separately labelled preflight |
| P09 | Builder/import/analysis/evaluation tooling, reproduction and report methods | Agent; A/B reproduce/review | P00 onward; final contract P06 | Relevant tests, isolated-service specification, reproducible preparation bundle and draft methods |
| P10 | Final preparation freeze and readiness decision | Agent; A/B evidence sign-off | P01–P09 | Every required preconstruction gate passed with hashes/denominators; otherwise explicit no-go |

## 4. P00–P03: establish the population before more enrichment

### P00 — Protect state and specify release-capable interfaces

- Inventory source/config/method versions, input/output hashes, code commit plus
  uncommitted diff identity, all sample manifests, raw evidence, review decisions
  and the two historical databases. Preserve the Site project/URL/audience.
- Pin roster v5 as the current starting point; future source recovery needs a new
  version. Preserve the v2 diagnostic design and v3 preparation receipt as history.
- Specify typed JSONL/Parquet table contracts from [data-dictionary.md](data-dictionary.md),
  stable semantic keys, evidence locators, review states, deterministic ordering,
  resume rules and immutable checkpoints. Missing stages must fail nonzero.
- Trace adapter/config/split/resolution/build/query call paths before changes.
  Define exactly which historical components can be reused and which are
  diagnostic-only. Listing more venues or years does not implement those paths.

**Done:** a reviewer can identify each protected input and its consumer, and every
new output has a fresh path and a specified schema. No unversioned mutation or
silent placeholder success is part of the design.

### P01 — Close sources and reconcile every eligible roster

- Work through the 82-row backlog above. For each edition, record authoritative
  year/track evidence, complete official routes, catalog/page hashes, source dates,
  adapter version, rights/access status and a responsible review decision.
- Implement/test future adapters against changing annual formats, archive/API
  pagination, API-v1/v2 or venue-ID differences where applicable, rejected/
  withdrawn papers, main versus special tracks, duplicate DOM records, incomplete
  bylines and joint proceedings. Do not guess identifiers or scrape restricted
  sources through a bypass. Inspect source contracts before selecting a route.
- Reconcile raw observed counts to included/excluded/review counts for each page,
  issue, edition and year. A missing page/volume or unknown track withholds the
  whole affected edition from sampling; a partial successful page is not coverage.
- Keep explicit official no-edition findings and exclusion dispositions. Record
  unfetched non-main issue counts as unknown, not zero paper counts.

**Done:** all 170 candidates have evidence-backed scientific dispositions, and all
eligible editions have complete, permitted, main-research rosters. Access failures
or unresolved eligibility keep the full-scope gate failed, even after triage.

### P02 — Make the intended release executable and affordable

- Distinguish the full official population, intended release processing population,
  development diagnostics, independent component tests and final edge audit.
  Do not quietly turn a sampled diagnostic release into complete-corpus coverage.
- Estimate canonical work count after reconciliation; do not treat 85,802 roster
  observations as deduplicated works. A sampled core release would change the
  current full-enrichment objective and must be proposed explicitly, not adopted
  by choosing only easy papers or enough records to hit the size gates.
- Measure a bounded development batch's cold/warm request costs, parsing time,
  byte sizes and accepted-person/affiliation/topic yield. Existing cached GROBID
  timings are not a cold throughput benchmark; the 68-paper layout diagnostic is
  not a representative corpus-wide yield estimate.
- Budget per-source requests and retries, free OpenAlex allowance/credit weights,
  ORCID lookups, selective PDFs/OCR/reference parsing, temporary storage, raw
  cache/backup space and projected support/graph expansion. Recheck live service
  contracts/quota only when future execution is authorized; assume no paid spend.
- Estimate work as `new requests × effective latency + retry allowance`, document
  throttled concurrency, and include reviewer time for paper, affiliation, topic,
  identity-pair and reference units separately. Two independent reviews plus
  adjudication must be included. The user reports one reviewer but no exact hours;
  a second independent reviewer is unconfirmed, so usable review capacity is not
  yet established.
- Treat the **2,000 publicly corroborated core researchers** target as a separate
  feasibility test. Current 10-person evidence cannot justify an assumption that
  more API matches will meet it. Keep the ORCID/publication rule unless an explicit
  later decision authorizes a different evidence standard.
- Freeze per-batch count/time/byte/request limits and stop rules before scaling.
  If available free resources, evidence yield, source access or real review effort
  cannot satisfy the unchanged gates by the cutoffs, report no-go early. Preserve
  the verified partial result; do not spend resources on a guaranteed incomplete
  full run or invent a capacity commitment.

**Done:** a finite written budget and execution envelope cover every planned stage,
with measured assumptions, uncertainty, safe resume/stop behavior and a credible
route to the evidence/size/coverage targets. An unmeasured assumption remains open.

### P03 — Two-pass work resolution and prospective sampling

- Build preliminary cross-year/cross-venue work families from official identifiers,
  DOI/provider/source crosswalks and corroborating bibliographic/byline evidence.
  Equal titles are quarantine signals; retain alternate-title review candidates.
  Reserve known test families before development enrichment.
- Preserve all 5,046 legacy and 14,909 expanded assignments as immutable subsets
  of the current 76,629 membership, including all 1,095 tests and 68 newer
  development diagnostics. Track exposure separately from original split labels.
- Reconcile the four new version-candidate rows and any further conflicts using
  source evidence; do not merge people from author-name similarity or papers from
  titles. Shared provider-work IDs can signal a provider error, not only duplicates.
- Freeze supplemental development and untouched component-test allocation from
  eligible, previously unexposed work families. Document strata, eligible frame,
  seed, sample sizes, inclusion/conditional probabilities, tiny-stratum rules,
  nonresponse treatment, population weights and the exact annotation budget.
  Keep difficult-layout/rare-topic diagnostics outside probability estimators.
- Preserve every old test family, including newly discovered alternate versions;
  mixed test/development exposure is quarantined and disclosed. Never redraw or
  reassign an old sample to hide leakage or improve coverage.
- Specify a separate **sealed evaluation acquisition path** for reserved tests.
  Current diagnostic commands deliberately reject held-out acquisition; they
  cannot be reused by disabling that protection. Future test processing requires
  its own versioned, explicitly authorized evaluation contract, frozen methods,
  access/exposure log and evaluator isolation. No test error feeds tuning.
- Before production/evaluation, re-run version and exposure guards using identifiers
  discovered during the development loop. After production enrichment, repeat
  canonical resolution before freezing support. This avoids requiring unknowable
  provider IDs before any permissible diagnostic request.

**Done:** all original assignments remain identical; no work family crosses
training/development and independent testing; supplemental design is frozen
before acquisition/tuning; uncertainty/nonresponse and leakage are recorded.

## 5. P04–P06: finish source and semantic evidence

### P04 — Bounded development and independent development labels

- Use the prepared [development review packet manifest](../data/manifests/five-year-development-review-packet-v1.json)
  as the first calibration exercise: two separate paper/byline forms and
  author-position forms. Preserve their original blank versions; create new
  completed review artifacts instead of overwriting the originals.
- Have the two real reviewers independently inspect evidence without seeing the
  other's labels or pipeline predictions, then retain disagreements, agreement
  statistics and adjudication. These are exposed development records, not final
  independent test evidence. The agent may assemble packets/check formats.
- Extend development diagnostics under P03 to newly supported sources and years,
  ambiguous names, byline truncation, multi-affiliation, organization hierarchy,
  alternate work versions, negative/ambiguous topic phrases and missing references.
- Recover the 13 newer source-withheld papers only with new corroboration.
  Resolve title/order/count conflicts, the MLSys metadata/byline mismatch, parser
  header pollution and RSS extraction limitations through exact input-bound
  overlays or versioned OCR/alternate parsing. Preserve original failure statuses.
- Every accepted paper needs an eligible official record, title/year/byline binding
  and resolvable provenance. Keep irreparable failures as measured withheld states.
  Repeatedly processing unchanged ambiguous inputs is not evidence improvement.
- Freeze annotation units, complete positive/negative labels, abstention rules,
  confusing examples, organization granularity and candidate taxonomy before
  independent held-out testing. Label every relevant affiliation/topic/reference
  in selected gold papers so recall is measurable; checking only predictions
  cannot measure false negatives.

**Done:** source-specific development error categories are addressed, reviewers
have completed genuine development labels, and a reproducible calibration record
supports the chosen methods. Unresolved failures remain visible with denominators.

### P05 — Stage metadata/documents, then finish the intended population

- Implement release-capable orchestration under new versions, not an override of
  the 68-paper diagnostic cap. Validate roster, split and evidence hashes before
  each batch; enforce free-allowance preflight, retries, host stops and checkpoints.
- Match provider works using stable identifiers plus complete title/year/venue/
  ordered-byline corroboration. Detect truncation, shared works, erroneous
  locations and collisions with held-out families; retain raw/provider conflicts.
- Retrieve official text and only necessary permitted PDFs. Parse headers for
  affiliation evidence; parse explicit references/full text only as needed.
  Pin parser/model/OCR versions and external-consolidation behavior. Never count
  a manual overlay or OCR result as a successful original GROBID parse.
- Collect references against the whole intended canonical core, not just a tiny
  diagnostic tranche. Do not recursively acquire external context by default.
- Reconcile every intended record to a terminal included/failed/review/withheld
  state and retain missing-field reasons. Technical collection completion does
  not mean all records have accepted semantic claims or coverage gates pass.
- Re-estimate limits after development and each bounded production batch. Halt
  on quota/access/integrity violations; resume only matching inputs or create a
  new version. Do not silently change sampling probabilities midstream.

**Done:** the declared processing population is completely accounted for, raw
sources are immutable and hash-verifiable, every selected field has its own
provenance, and missingness/cost/runtime are measured by edition/source/year.

### P06a — Canonical works and researchers

- Reconcile all observed official/provider versions within the intended release
  and known held-out frame, not just the exposed 318 diagnostic records. Maintain
  source-record → canonical-work crosswalks, one primary Venue/edition, alternate
  titles/IDs, duplicate/version evidence and reversible accepted decisions.
- Quarantine conflicting shared DOI/provider identifiers; detect versions that
  would introduce a self-citation or duplicate publication. No unresolved work
  identity may support accepted release edges; keep the unresolved population in
  the ledger instead of pretending globally exhaustive identity is proved.
- Resolve each person with a stable internal ID, complete paper-specific byline
  position, consistent external-ID crosswalk and **public ORCID target-publication
  corroboration** under the current rule. Retain positive and negative evidence.
- Address conflicting ORCID/provider IDs through documented source review.
  Never merge on names/initials alone, accept an ORCID checksum as publication
  proof or multiply one accepted author across other byline positions.
- Revalidate historical accepted people/support against the new canonical work
  frame before reuse; do not add historical and newer people counts arithmetically.

**Done:** every accepted work/person has a stable, nonconflicting, auditable identity;
all accepted authorship observations map to the exact official byline and evidence.
Unresolved identities remain outside resolved-researcher totals.

### P06b — Organizations and historical affiliation triples

- Retain literal printed institutions, author order, markers/pages and document
  hashes before normalization. Require reviewed authorship-specific printed
  mapping plus the exact institution inside that same author's metadata.
- Address missing laboratories, multiple affiliations, repeated mentions,
  subsidiaries/campuses, name changes and organization hierarchy explicitly.
  Another accepted institution for the same person/paper does not validate a
  missing laboratory. Current profile affiliation is not publication-time evidence.
- Resolve canonical organization IDs and external ROR/provider crosswalks using
  approved granularity; keep unknown sectors/countries unknown. ROR similarity
  alone must not relax the current exact printed/provider alignment rule.
- Freeze `(researcher_id, canonical_paper_id, organization_id)` triples before
  aggregation. One author may have several genuine triples; repeated source
  confirmations of the same triple do not add support or coverage.

**Done:** each accepted triple has accepted authorship, exact aligned institution
and resolvable paper-specific evidence; organization mapping is reversible and
consistent. Coverage counts unique author–paper positions with at least one
accepted organization, not the number of triples.

### P06c — Topic taxonomy and supported NLP labels

- During P04, review the draft taxonomy against the full scoped fields using
  development labels. Any changed definitions/labels get a documented new
  taxonomy version; keep the old taxonomy/phrase outputs intact. P06 applies that
  frozen version rather than redesigning it after production or test exposure.
- Before P05, freeze leaf definitions, hierarchy, inclusions/exclusions, confusing
  examples, source text fields, evidence offsets and annotation instructions.
  Fully inspect every leaf→parent link before marking it curated/accepted.
- During P04, compare the phrase baseline with any chosen supported classifier
  using development evidence only. A model is optional; a pinned, tested rule
  method may qualify if it actually meets quality and coverage. Pin model/revision,
  dependency/license/runtime and per-label thresholds before P05 and held-out
  evaluation. A later change must restart the affected freeze/evaluation sequence.
- Accept only 1–3 substantive leaf labels with title/abstract evidence, or abstain.
  Ambiguous words and related-work mentions do not qualify. Scores from different
  methods are not interchangeable probabilities. The existing 17 candidates are
  not accepted labels and must not be promoted wholesale.
- Target the configured 95% topic-label precision and 80% eligible-paper coverage
  together. Do not lower confidence thresholds just to cover more papers. Report
  per-label support/abstention and unmet rare-field coverage honestly.

**Done:** the taxonomy/hierarchy is frozen and reviewed, the method/thresholds are
calibrated on development, and accepted labels carry exact text provenance.
Independent topic quality is determined by P07, not calibration scores.

### P06d — Verified citations

- Preserve explicit reference mentions with citing-paper source/page/TEI locators;
  provider `referenced_works` IDs alone remain candidates until reference and
  canonical target are verified. Record ambiguous/unmatched references separately.
- Resolve targets to accepted canonical core works in 2021–2025, preserve citing →
  cited direction and distinct-work identity, and deduplicate repeated mentions.
  Exclude same-work version self-loops; do not manufacture references to fill R4.
- Keep external/context references separate and out of factual-edge targets.
  Record citation-source snapshot date and edition/publication-date differences.

**Done:** every accepted citation has an explicit reference, verified in-core target
and correct source/target direction. Reference extraction and target-resolution
recall have measurable gold denominators; zero candidates remains an honest gap.

### P06e — Evidence closure and terminal review states

- Validate evidence URL/record, timestamp, raw hash, exact field/page/marker/text
  locator, claim class and source/method/decision versions for every accepted row.
  Use minimal permitted excerpts; do not redistribute raw PDFs/private reviews.
- Bind review decisions to specific immutable inputs; preserve both reviewers'
  original judgments where applicable. All remaining queue items need explicit
  withheld/rejected/pending-external-evidence reasons and reopening criteria.
- Recheck every reused historical claim against the final work/entity crosswalk.
  Count distinct canonical paper support and preserve conflicting evidence.
- Re-run leakage/exposure checks after the last metadata/reference match. A new
  test-version conflict quarantines support and affects reported inference; it
  does not justify rewriting the frozen split.

**Done:** no accepted claim depends on unresolved identity, unsupported mapping or
missing evidence. Review closure and scientific coverage are reported separately.

## 6. P07: independent component evaluation and coverage

Freeze method/config/taxonomy/code identities **before** processing or revealing
untouched test outcomes. Evaluation gold and predictions need separate artifacts.
Keep annotator originals, blinded independent review, adjudication, evidence
locators and the full denominator frame. Genuine unknowns must be accounted for,
not dropped to improve scores; unverifiable accepted claims fail verification.

| Component | Configured precision target | Additional required reporting |
| --- | ---: | --- |
| Researcher resolution | Pairwise ≥98% | Recall/F1; false merges/splits; common-name negatives; positive linkage opportunities; singleton/undefined cases |
| Organization resolution | ≥95% | Recall/F1, granularity/alias/hierarchy errors, unknown-sector coverage |
| Affiliation triples | ≥95% | Recall/F1, wrong-author/marker/institution errors; unique author–paper coverage |
| Topic labels | ≥95% | Micro/macro and per-label P/R/F1, label support, complete gold label sets and abstention |
| Citation targets | ≥98% | Reference extraction/target recall and F1, ambiguous/external/missing references |

These are the existing proposed component targets, not newly measured results or
newly invented component confidence-bound requirements. Report intervals/support
where appropriate; undefined or unmeasured quality cannot pass. Zero merges or
accepted predictions do not establish a meaningful precision/recall result.

Use the prospectively specified stratum probabilities/weights for population
estimates; retain venue–year/source-family, team-size and sector breakdowns.
Do not pool targeted rare-case diagnostics into unweighted corpus estimates.
Report automatic pipeline quality separately from human-corrected support quality.

Coverage gates use explicit denominators from the **frozen eligible release core**,
not only successfully parsed/acquired/source-accepted papers:

- Abstract availability **≥95%** of eligible core papers.
- Accepted affiliation resolution **≥80%** of official eligible-core author–paper
  positions; multiple organizations at one position count once. Also report the
  conditional rate among resolved researchers without substituting that denominator.
- Accepted supported topics on **≥80%** of eligible core papers; abstentions and
  unavailable text remain in the denominator.

Also report failure/withholding, work-match and resolved-person coverage against
the declared processing/official frames, by year and source. Explain differences
between official records, deduplicated works and accepted core tables. Diagnostic
54/55 abstract availability cannot stand in for population coverage.

**Done:** independently reviewed component results meet the existing targets and
population coverage gates, with frozen methods and auditable denominators. Recall
and F1 must be measured/reported; this plan invents no missing numeric recall/F1
threshold. The course's “accuracy >90%” interpretation remains proposed until
confirmed; do not substitute component precision for the final edge audit.

If a held-out failure informs a correction, preserve that test and its result,
version the method and use a fresh untouched test set for a new independent claim.
Do not retune against test errors and relabel the same test independent. The
final edge audit remains separate and is drawn only after graph construction.

## 7. P08: prove that the accepted tables can support the required graph

Use deterministic relational queries over accepted frozen tables. This is a
**preconstruction support inventory**, not a built/imported graph or final result.
Do not export production nodes/edges or run final derivations at this step.

| Predicate | Required support before construction |
| --- | --- |
| R1 AUTHORED | Accepted resolved researcher + canonical core paper + byline position/evidence |
| R2 AFFILIATED_WITH | Accepted publication-time triples aggregated by unique researcher–organization pair; retain paper/year support |
| R3 PUBLISHED_IN | Accepted canonical core paper with one primary verified Venue/edition |
| R4 CITES | Accepted explicit distinct core-work reference with verified directed target |
| R5 HAS_TOPIC | Accepted supported paper→leaf label under the frozen taxonomy/method |
| R6 SUBTOPIC_OF | Reviewed accepted leaf→parent links; hierarchy and evidence inventory valid |
| R7 COAUTHORED_WITH | Distinct resolved people on an accepted core paper; canonical pair orientation |
| R8 COLLABORATED_WITH | Distinct organizations supported by **distinct authors** on the same core paper; a sole dual-affiliated author is insufficient |
| R9 RESEARCHES_TOPIC | A researcher has that accepted leaf on **at least two distinct core works** |
| R10 CONTRIBUTES_TO_TOPIC | An organization has author-specific support for that accepted leaf on **at least three distinct core works** |

- Measure unique accepted core researchers **≥2,000** and domain entities **≥2,000**.
  Do not count unresolved mentions, evidence records, parser objects or context.
- Count unique eligible factual R1–R4 semantic tuples **≥5,000**, using the same
  identity/orientation rules the builder will enforce. Source confirmations,
  duplicate versions and reverse copies do not add semantic edges.
- Require genuine support eligibility for **all ten** predicates; this specifically
  closes the historical R9/R10 gap. Report each predicate/evidence class separately.
- Preflight every support chain for missing/withheld endpoints, temporal mismatch,
  duplicate evidence, invalid hierarchy, self-loops and ambiguous canonical IDs.
- Specify/review raw and fractional weights: R7 contributes `1/(k-1)` per eligible
  pair with all official byline authors in `k`; R8 contributes `1/q` per eligible
  organization pair. Deduplicate support by canonical paper. Preserve portfolio
  fractions and the schema's distinct-paper thresholds.
- Verify annual/cumulative support-window logic on fixtures. Recompute R7–R10 and
  weights within each window rather than filtering union weights and calling them
  annual measurements. Overlapping annual entity counts cannot be summed as the union.

**Done:** exact table inventories meet size gates and support every predicate, with
accepted evidence and no unresolved dependencies. The constructed graph must later
reconcile to this inventory; passing these queries does not pre-certify that import.

## 8. P09: tooling, reproduction and deliverables ready before graph building

### Implementation readiness for the future execution stage

- Design/implement and test the new release-capable table validator/freezer and
  builder inputs. The current `prepare-pregraph` is a **68-paper diagnostic**
  implementation with hard-coded pending full-population gates and an always-false
  construction receipt. Running it again or renaming v3 cannot certify the new
  population. Replace neither its history nor flags with manual success values.
- Prepare source/version-aware accepted table assembly, deterministic IDs,
  evidence/support partitioning and temporal derivation code. Test independently
  specified expected facts/weights; do not merely mirror implementation outputs.
- Prepare a distinct Neo4j Community service/volume and import configuration that
  preserve the historical base/expanded databases. Pin the image/schema/driver,
  localhost ports, constraints/indexes, transaction/reconciliation/resume semantics
  and rollback plan. Do not initialize or import the final graph at this stage.
- Validate import/query changes against a **disposable isolated integration
  fixture database** when available; never overwrite the existing DBs. Label those
  counts synthetic, record actual availability, and leave production readiness
  unverified if required integration tests cannot run. Optional GDS must not break
  the working base service; use a verified NetworkX fallback where appropriate.
- Implement component `evaluate` and test its contracts using synthetic or
  permitted frozen development inputs; it remains a nonzero placeholder. The
  `analyze` command now prepares five named projection metrics and a configured
  evidence-filter comparison, but it does not complete P09 or certify findings.
- Complete citation-age/coverage comparisons, sector/topic portfolios and
  source-backed business cases from [analysis.yaml](../configs/analysis.yaml).
  Actual communities, rankings and findings wait for the final graph.
- Prepare the global 600-edge uniform-without-replacement audit sampler and
  separate 100-per-type-or-census sampler, seeds, frame hashes, independent forms,
  adjudication and Wilson computation. Keep per-type supplements out of the
  unweighted global estimator. Do not draw the final sample from staging tables.

### Reproduction and report preparation

- Run `uv sync --locked --group dev`, the configured `uv run pytest` suite and
  relevant offline CLI checks during future implementation; keep `uv.lock` in sync
  if dependencies change. No full collection/model download in ordinary tests.
- Cover meaningful same-name/distinct-person cases, cross-year duplicate versions,
  provider collisions, leakage, multiple/missing affiliations, unknown tracks,
  topic abstention/ambiguous tokens, repeated supports, dual-affiliation-only
  noncollaboration and two/three-distinct-paper temporal thresholds.
- Prove offline/source-disabled replay of accepted preparation tables, exact
  input/config/method/code binding, output tamper detection, safe partial resume
  and nonzero unmet-gate behavior. Separate cache hits from cold runtime measures.
- Validate a clean environment/code checkout can regenerate permitted fixtures
  and aggregate preparation results from the pinned inputs, or document exactly
  which local-only/restricted inputs must be reacquired and why. Never claim
  network-free reproduction of missing raw sources.
- Draft the report's scope/business motivation, node/edge rationale, sources and
  collection stack, preprocessing/NLP methods, evaluation protocol, actual task
  contributions and limitations. Prepare table/figure templates and data captions.
  Correct stale planning statements in future report work; do not leave “five-year
  collection has not started” in the final report. Statistics/results stay pending.
- Prepare required names/student IDs and real contribution records without
  inventing them. Verify repository access/URL and select the code license without
  assuming it covers third-party data. Stage permissible release metadata, evidence
  instructions and archive manifests; do not commit secrets, PDFs or private labels.
- Plan the final ≥10-page substantive report and three supported business cases /
  two investigation shortlists. The Site is not a replacement for that report.
  Its future native Report must distinguish old graph, table preflight and actual
  new graph; preserve project ID/URL/audience and publish version receipts.
- Complete the outstanding Site keyboard/mobile/control QA during future authorized
  Site work. Do not transform historical static/HTTP passes into interaction passes.

**Done:** code/contracts/protocols needed for construction and evaluation are tested,
preparation tables can be rebuilt, evidence/privacy boundaries are checked and
methods/report skeletons are ready. Actual graph/import/audit/analysis results
and final report certification remain explicitly unperformed.

## 9. P10: immutable preparation bundle and go/no-go matrix

Proposed artifacts below are **specifications, not files created by this plan**.
Choose unused versioned paths during future implementation; no output may replace
`data/processed/five-year-pregraph-v3/` or another historical freeze.

| Artifact | Required contents |
| --- | --- |
| Release scope ledger and source manifests | All 170 scientific dispositions; complete eligible rosters; terms/access/evidence and excluded/unresolved counts |
| Work/version/exposure crosswalk | Official/provider/DOI IDs, primary venue/year, accepted decisions, conflicts, reserved-family links and exposure history |
| Frozen membership/design manifest | Original assignments plus prospectively frozen supplements; populations, seeds, probabilities, weights and annotation budget |
| Accepted entity/support tables | Papers, researchers, organizations, authorships, affiliation triples, paper topics, taxonomy links and directed in-core citations |
| Evidence and review history | Resolvable immutable sources/locators, method versions, accepted decisions, withheld reasons and reopening criteria |
| Independent component evaluation | Frozen predictions, original reviewer labels, adjudication, TP/FP/FN/P/R/F1, support, intervals/weights and coverage denominators |
| Preconstruction inventory | Distinct accepted researcher/entity/factual-tuple counts, all-ten support eligibility and temporal-support checks |
| Reproduction/tooling receipt | Code commit/diff, lockfile/environment, configs, source/model/taxonomy versions, checks, integration fixture status and replay hashes |
| Final preparation freeze receipt | Population ID, every input/output hash, per-gate result, unresolved blockers, recorded time and computed readiness; no production graph artifact |
| Post-build handoff specification | Planned graph version/storage, construction/import commands once implemented, audit/analysis contracts, report/Site update and rollback instructions |

| Required gate | Pass evidence | Current starting state |
| --- | --- | --- |
| G01 Scope/official rosters | All candidate dispositions scientifically resolved and every eligible edition complete | Failed: 82 edition gaps |
| G02 Integrity/work identity/leakage | Stable accepted work/entity crosswalk; old/new tests preserved; no unresolved conflict supports release claims | Partial; global closure incomplete |
| G03 Resource/design feasibility | Budgeted intended population and frozen probability/annotation design before collection/tuning | Supplemental design/budget pending |
| G04 Processing and provenance | Every intended record accounted for; accepted claims evidence-complete; failures/missingness remain in denominator | Diagnostic tranche only |
| G05 Researchers/domain entities | ≥2,000 accepted core researchers and ≥2,000 domain entities in distinct-table preflight | Failed in current diagnostics |
| G06 Factual support | ≥5,000 unique accepted factual R1–R4 tuples in preflight | Unmeasured for final population |
| G07 Ten predicate support | All ten have genuine accepted base/taxonomy/derivation eligibility | Unmet; topic/citation/threshold support incomplete |
| G08 Coverage | Abstracts ≥95%, aligned affiliations ≥80%, accepted topics ≥80%, with frozen-core denominators | Population scores not measured; diagnostic affiliations/topics fail |
| G09 Independent components | Real blinded labels and configured component precision targets, with recall/F1/support reported | Not run |
| G10 Frozen methods/taxonomy | Development-only calibration, approved taxonomy and frozen code/config/model identities | Uncalibrated draft topics |
| G11 Tooling/rebuild/integration readiness | Required checks/replay pass; isolated import/temporal algorithms verified on fixtures; no placeholder claims | Historical implementation only; release work pending |
| G12 Documentation/audit handoff | Correct methods/report drafts, contribution/evidence records, final audit protocol and complete handoff | Partial; no final graph-dependent claims |

Readiness must be computed from these measured gates. “Not run”, “unmeasured”,
“withheld”, “unavailable” and “review queue closed” are not synonyms for passed.
An accepted null/unknown optional property is allowed where the schema permits it;
a missing required gate is not. Required evidence being inaccessible remains a
blocker rather than a success exception.

**Stopping point:** freeze the bundle and publish its honest readiness status.
If all preconstruction gates pass, hand off the immutable inputs for a separately
initiated final graph stage. If any fail, output **not ready**, the failing units,
evidence, responsible action and next bounded task. Do not build the final graph
merely because the deadline or a schedule checkpoint arrives.

## 10. Deadline checkpoints and work tracking

The times below preserve the existing internal cutoffs; they are planning targets,
not promises that the workload fits. They do not grant execution authorization.

| Checkpoint (+07:00) | Planned deliverable | If incomplete |
| --- | --- | --- |
| 7 November | P00–P03 source/feasibility/design checkpoint; start only budgeted future development and report methods | Record source, resource or reviewer blockers before broad enrichment |
| 8 November, 18:00 | Stop adding source families/features; choose the feasible frozen execution envelope under unchanged scope/gates | Full-scope blockers remain failed; no silent scope reduction |
| Before 9 November, 18:00 | P04–P10 must finish early enough for the separately authorized graph stage; the existing 9 Nov 18:00 candidate/method freeze remains the outer bound | Stop expanding; do not rush a failed preparation bundle into a final graph |
| 10 November, 12:00 / 18:00 | Post-build gate record / submission-ready package under the earlier execution plan | Truthful partial delivery if final audit/report gates are unmet |
| 11 November | Final submission checks at the actual course deadline | No broad collection or redesign |

The full-corpus/resource/independent-review requirements may not fit the remaining
time. Record that at P02 with actual evidence; preserve the deadline and standards.
Do not promise complete coverage or passing accuracy from this plan alone.

For every meaningful future iteration:

- Create a new `docs/work-log/` entry early and retain its finalized outcome.
- Record scope, inputs/config/method hashes, objective, real commands/exit codes,
  reviewer/exposure evidence, accepted/withheld counts, failed gates and next action.
- Save local raw logs in `reports/runs/<work-id>/`; keep sanitized handoffs tracked.
- Refresh status/roadmap and measured report after capability/result changes;
  update the existing native Site after authorized material execution iterations.
- Do not auto-commit/push the project or publish raw evidence as part of logging.

## 11. Current next task

Continue **P01 edition/track closure** from roster v10. Resolve the 22 unresolved
roster/adapter editions and 40 access-unavailable candidates through complete,
permitted official rosters. MICCAI 2024 is closed under D033. MICCAI 2022, AAMAS 2023 and ICDM 2021/2025
remain unresolved; ACM Multimedia 2024 remains access-unavailable after D038.
WORK-020 corrected the ICDM 2025 route evidence with hash-bound accepted-page,
CFP, BlueSky and program captures; a complete final-proceedings join and metadata
reuse status remain open. WORK-021 recaptured the ACM Multimedia ID file and
clarified the regular-paper and BNI calls, but the 1,149/1,150 mismatch, full
roster join and metadata reuse terms remain unresolved. WORK-022 captured the
official CIKM 2025 accepted, proceedings, and three call pages, but the 827
accepted records do not reconcile to 852 proceedings links and metadata reuse
terms are unknown. Use source triage only as a lead list, not evidence of complete
coverage. Implement and test versioned adapters only after inspecting source
contracts, changing formats, track policies, pagination and rights. Keep
unresolved or partial editions ineligible. Refine P02's no-go assessment only
when measured inputs are available; one reviewer is reported with no exact hours
known, and a second independent reviewer is not confirmed. Preserve all historical
and newly frozen assignments. Do not begin broader metadata/PDF enrichment,
change independent test membership, or construct a graph until their respective
gates and execution authorization are satisfied.
