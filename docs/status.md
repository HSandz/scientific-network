# Current project status

Updated: **2026-11-08 (Asia/Bangkok, UTC+07:00)**.
Latest task: [WORK-2026-11-08-023 — P01 RecSys 2025 browser source audit](work-log/2026-11-08-023-recsys-2025-browser-source-audit.md) (**in progress; v10 current**).
**D022 authorizes staged collection under existing gates; D029–D039 cover ICAPS 2025, official route closure, AAMAS rosters, MICCAI 2021/2023/2025, MICCAI 2024/2022, ACM Multimedia 2024, ICDM 2021/2025, and the CIKM 2025 browser follow-up.** Deadline: 11 November 2026. [Workflow](five-year-collection.md) · [Current roster v10](../reports/five-year-source-recovery-v10.md) · [Measured revision 2](../reports/five-year-collection-v2.md).

## Current iteration — P01 RecSys 2025 browser source audit (WORK-023)

Testing whether the connected browser can capture the official RecSys 2025
accepted-contribution and proceedings routes after local DNS failures. The edition
remains `access_unavailable` in v10; no source or roster change has occurred at
this checkpoint. Preserve all v10 outputs and frozen assignments. See
[WORK-023](work-log/2026-11-08-023-recsys-2025-browser-source-audit.md).

## Previous iteration — P01 CIKM 2025 browser source capture (WORK-022)

The connected browser captured the official accepted-paper page, proceedings
page, and Full, Short, and Applied Research calls. The accepted page has 827
unique IDs across seven categories. The proceedings page has 852 ACM links;
normalized title comparison matches 789 accepted records, while exact title plus
author-set comparison matches 697 overall and 531 Full/Short records. The
incomplete crosswalk and unestablished bulk-reuse terms keep CIKM 2025
`access_unavailable`
in v10 under D039. No roster or frozen assignment changed. See [D039](decisions.md#d039--cikm-2025-browser-source-audit-2026-11-08),
[source triage](five-year-source-triage.md#cikm-2025-browser-source-capture-work-022),
and [WORK-022](work-log/2026-11-08-022-cikm-2025-browser-source-capture.md).

The existing public Site remains active at version 18 with its project ID, URL,
and audience preserved. The supported source helper failed before checkout with
`Unable to prepare the Site.` No Site source audit, push, build, or publication
occurred; the updated local Report is not live.

## Previous iteration — P01 ACM Multimedia 2024 browser source review (WORK-021)

The connected browser recaptured the official accepted-ID file: 1,149 unique
numeric IDs, with the decoded body matching WORK-017's prior 5,497-byte hash.
The official regular-paper call clarifies that paper length does not define a
separate long/short track. The BNI call says accepted papers are full papers in
the main proceedings, with a separate committee and review criteria. A converted
program view has only 63 explicit paper-ID labels and is not hash-bound origin
PDF evidence. The official research-track statistic remains 1,150 acceptances;
the full roster join and metadata reuse terms remain open. ACM Multimedia 2024
stays `access_unavailable` in v10. See [D038](decisions.md#d038--acm-multimedia-2024-browser-source-follow-up-2026-11-08),
[source triage](five-year-source-triage.md#acm-multimedia-2024-browser-source-follow-up-work-021),
and [WORK-021](work-log/2026-11-08-021-acmmm-2024-browser-source-review.md).

V10 remains at **98 eligible / 10 verified no-edition / 22 unresolved / 40
access-unavailable**, with **94,857 observations** (91,355 included; 3,502
excluded). The 76,629 assignments, including 1,095 reserved tests, are unchanged;
all 42 v10 output hashes and seven frozen split-input hashes verify. P01 retains
62 incomplete candidates. P02 remains no-go: one reviewer is reported with
unknown hours and a second independent reviewer is unconfirmed. No split,
enrichment, paper PDF, graph or database operation occurred.

The existing public Site is still active/public at v18, with its existing project
ID, URL and audience. The supported helper failed before checkout with
`Unable to prepare the Site.` No Site source was audited or pushed, and no build
or publication occurred; the refreshed local Report is not live.

## Previous iteration — P01 ICDM 2025 offline source audit (WORK-020)

Fresh direct captures of the official accepted page, main CFP, BlueSky call and
program returned HTTP 200 with response headers and matching body hashes. The
accepted page contains 105 Regular and 70 Short entries (175 unique IDs), but its
Short Papers heading conflicts with the CFP's statement that no separate short
submission track exists. The CFP conditions proceedings inclusion on registration
and presentation; the program capture does not reconcile all accepted records.
The candidate IEEE Xplore contents route returned HTTP 418, and source reuse terms
remain unclear. ICDM 2025 stays unresolved in v10; no v11 was created. See [D037](decisions.md#d037--icdm-2025-accepted-list-audit-2026-11-08),
[source triage](five-year-source-triage.md#icdm-2025-official-accepted-list-audit-work-020),
and [WORK-020](work-log/2026-11-07-020-icdm-2025-offline-source-audit.md).

V10 remains at **98 eligible / 10 verified no-edition / 22 unresolved / 40
access-unavailable editions**, with **94,857 observations** (91,355 included;
3,502 excluded). All **76,629 assignments**, including **1,095 tests**, remain
unchanged; all 42 v10 output hashes and seven split-input hashes verified. P01
retains 62 incomplete candidates. P02 remains no-go: one reviewer is reported,
exact hours are unknown, and a second independent reviewer is unconfirmed. The
existing Site was confirmed active/public at v18. After local DNS recovered, the
supported helper still failed before checkout with a generic preparation error;
no Site source audit, push, build or publication occurred. The local Report is
refreshed but unpublished.

## Previous iteration — P01 CIKM 2025 source recheck (WORK-019)

The official Search-rendered accepted-paper page and proceedings page show
separate Full, Short, Applied, Resource, Demo, PhD Symposium, and Industry Day
categories. These rendered views are route/track evidence, not hash-bound source
captures. A current local scan of 55 unique URL hosts from the scope registry and
source triage resolved none; direct requests to both CIKM pages failed with curl
exit 6 before returning bytes. CIKM 2025 remains unresolved in roster v10, with
no new roster or track decision. See [source triage](five-year-source-triage.md#cikm-2025-local-source-recapture-recheck-work-019)
and [WORK-019](work-log/2026-11-07-019-p01-cikm-2025-source-recheck.md).

V10 remains at **98 eligible / 10 verified no-edition / 22 unresolved / 40
access-unavailable editions**, with **94,857 observations** (91,355 included;
3,502 excluded). All **76,629 assignments**, including **1,095 tests**, remain
protected. P01 retains 62 incomplete candidates. P02 remains no-go: one reviewer
is reported, exact hours are unknown, and a second independent reviewer is
unconfirmed. No split, enrichment, paper PDF, graph or database operation
occurred. The existing Site remains at its last confirmed v18; this route-only
recheck did not warrant a Report publication.

## Previous iteration — P01 ICDM 2021 source closure (WORK-018)

The official accepted-paper page has 197 unique IDs (98 Regular, 99 Short), and
all 197 are also in the official schedule. The schedule has 239 unique IDs; the
42 additional IDs occur in named workshops (40) or a separate PhD Panel event
(2). The PhD Forum is a separate doctoral route, but those two panel items were
not individually linked to its proceedings. The conference call says accepted
papers appear in IEEE Computer Society proceedings. A local IEEE Xplore request
returned HTTP 418; no bypass was attempted. University copyright terms separate
University-owned from third-party material, and page-level ownership/reuse rights
remain unresolved. ICDM 2021 remains unresolved in v10; no v11 or roster change.
See [D036](decisions.md#d036--icdm-2021-official-source-hold-2026-11-07),
[source triage](five-year-source-triage.md#icdm-2021-official-accepted-list-follow-up-work-018),
and [WORK-018](work-log/2026-11-07-018-icdm-2021-source-closure.md).

V10 remains at **98 eligible / 10 verified no-edition / 22 unresolved / 40
access-unavailable editions**, with **94,857 observations** (91,355 included;
3,502 excluded). All **76,629 guarded assignments**, including **1,095 tests**,
remain intact. P01 retains 62 incomplete candidates. P02 remains **no-go**: one
reviewer is reported, exact hours are unknown, and a second independent reviewer
is unconfirmed. No split, enrichment, paper PDF, graph or database operation
occurred. The existing Site is active/public at v18 with its original project ID
and URL; its Git host still fails DNS, so this local Report refresh is not live.

## Previous iteration — P01 ACM Multimedia 2024 source closure (WORK-017)

The official conference ID file was captured and hash-verified at 1,149 unique
numeric values. The official research-track statistics page reports 1,150
acceptances. The regular-papers page is a JavaScript shell, its static assets
could not be fetched after local DNS resolution failed, and the full program is
available only through a Search-rendered view without local source bytes. The
source does not resolve the one-record difference, explain ID membership or
define the complete proceedings/track boundary. ACM Multimedia 2024 remains
`access_unavailable` in v10. No v11, roster, split, enrichment or graph state
changed. All 42 v10 output hashes and five frozen-input hashes verified; the
76,629 assignments, including 1,095 tests, remain intact.

The existing Site was confirmed active/public at v18 with its project ID and URL.
The approved helper received the short-lived credential through hidden stdin but
failed before checkout because `git.chatgpt-team.site` did not resolve. No source
audit, push, build or publication occurred; the refreshed local Report is not
live. P01 retains 62 incomplete candidates. P02 remains no-go: one reviewer is
reported, hours are unknown, and a second independent reviewer is unconfirmed.
See [D035](decisions.md#d035--acm-multimedia-2024-official-source-hold-2026-11-07),
[source triage](five-year-source-triage.md#acm-multimedia-2024-official-source-follow-up-work-017),
and [WORK-017](work-log/2026-11-07-017-p01-acmmm-2024-source-closure.md).

## Previous iteration — P09 component evaluation contracts (WORK-016)

Implemented offline `evaluate` contracts bound to a frozen frame, predictions,
quality config and two reviewer packets. It checks complete frame joins,
adjudication, declared evidence locators, sampling weights and annotation
timestamps; reports weighted/unweighted component P/R/F1, per-stratum metrics,
topic macro/per-label scores, pairwise error types, reviewer agreement and
eligible-core coverage. Synthetic outputs are protocol-only and
`ineligible_synthetic`. Real scoring requires a reserved test frame, frozen
quality config and full eligible-core coverage denominator.

The existing Site was confirmed active/public at version 18 with its existing
project ID and URL. The approved source operation failed before checkout because
the supported helper could not resolve its Git host; no Site audit, push, build or
publication occurred. The local Report snapshot is refreshed but not live.

The current quality config is still proposed, and no complete independent labels
exist. Reviewer independence, blinding and source evidence remain unverified by
software; P07 and the final edge audit remain incomplete. P01 retains 62
incomplete candidates; P02 remains no-go with one reviewer of unknown hours and
a second unconfirmed. No roster, split, enrichment or graph state changed. See
[evaluation protocol](evaluation.md) and
[WORK-016](work-log/2026-11-07-016-p09-evaluation-contracts.md).

## Previous iteration — P09 offline named-projection analysis (WORK-015)

Implemented `analyze` for the five configured collaboration, citation and
topic projections. It validates graph structure, reports deterministic weighted
metrics, betweenness and seeded collaboration communities, and can compare a
frozen strict evidence-filter view. Non-synthetic graphs require configured size
gates and a matching post-build receipt plus frozen analysis/filter settings. The
synthetic CLI smoke is marked protocol-only; no business findings, graph or release
result were produced. Citation-age/coverage analyses, figures and business
findings remain pending. See [analysis workflow](analysis.md) and
[WORK-015](work-log/2026-11-07-015-offline-analysis-stage.md).

The focused tests passed (10), and the full suite passed (216). P01 remains blocked
on local DNS for official hosts; P02 remains no-go with one reviewer of unknown
availability and a second unconfirmed. No roster, split, enrichment or database
state changed.

## Previous iteration — P09 offline edge-audit packet utilities (WORK-014)

Added standalone `freeze-audit-sample` and `score-edge-audit` tools. They bind
the sample and packet to the graph, full edge-frame hash, quality-config hash,
readiness-receipt hash and method version; keep global and per-type samples
separate; require two
distinct reviewer IDs and adjudicate disagreements. Reviewer identity and
independence are not software-verified. Non-synthetic graphs also require a
matching post-build readiness receipt and all configured size/relation gates.
The synthetic CLI exercise is marked protocol-only and supports no research
accuracy claim. `analyze` and pipeline `evaluate` remain nonzero placeholders;
component recall/coverage and final release evaluation remain incomplete.

The focused tests passed (13), and the full suite passed (212). The v4 CLI smoke
check used only the invented `synthetic-v1` fixture and 54 invented labels from two
synthetic reviewer IDs across its 27 fixture edges; no human review occurred. The
scorer returned `synthetic_protocol_only`. No final-graph sample, release metric,
graph or database operation occurred. P01 remains blocked on local official-source
DNS, and P02 remains no-go. See [WORK-014](work-log/2026-11-07-014-p09-offline-contracts.md)
and the [evaluation protocol](evaluation.md).

## Previous iteration — P02 local resource snapshot (WORK-013)

At 20:59 +07:00, the workspace mount had 783.40 GiB available and selected
manifests/raw/interim/processed/run artifacts occupied 3.65 GiB apparent size.
Host available memory was 3.96 GiB, with 3.52 GiB swap in use; the visible
`init.scope` cgroup has no memory or CPU quota. Docker storage could not be
inspected because the socket denied access. These are transient local values, not
a full-corpus or isolated-database budget, so P02 remains no-go for broader
enrichment. The user reports one reviewer and no exact hours; a second independent
reviewer is unconfirmed. The required audit capacity is not established. Exact
measurements and limits are in the [feasibility report](../reports/five-year-pregraph-feasibility-v1.md#p02-local-workspace-snapshot--work-013-7-november-2026)
and [WORK-013](work-log/2026-11-07-013-p02-resource-snapshot.md).

P01 is still blocked on hash-bound official sources. A DNS recheck failed for the
Sites Git host, CIKM 2025 and ACM Multimedia 2024. The current public Site remains
v18; no source push or deployment occurred.

## Previous iteration — pregraph source and Site follow-up (WORK-012)

The Search-rendered CIKM 2025 proceedings route shows distinct Full, Short,
Applied, Resource, Demo and PhD Symposium categories with article links to ACM
Digital Library. It remains a route lead: no local source capture, rights review
or complete reconciliation was produced. No CIKM disposition changed. V10 remains
at 98 eligible / 10 verified no-edition / 22 unresolved / 40 access-unavailable;
all 42 output hashes verify, and all 76,629 guarded assignments including 1,095
tests remain unchanged.

The user's approved Site source operation was attempted through the supported
helper. After using the documented empty-directory setup, it failed before
checkout because `git.chatgpt-team.site` did not resolve. No source audit, build,
push or deployment occurred; the existing public Site remains v18. The short-lived
credential was passed only through helper stdin and not saved. See [source triage](five-year-source-triage.md#cikm-2025-proceedings-route-follow-up-work-012)
and [WORK-012](work-log/2026-11-07-012-pregraph-source-followup.md).

## Previous iteration — ACM/SIAM official source-route review (WORK-011)

P01 still has 40 publisher-access candidates. Official accepted-list/program leads
were identified for selected years of KDD, The Web Conference, SIGIR, WSDM, RecSys,
CIKM, ACM Multimedia and SIAM SDM. Local DNS failed for nine unique conference or
publisher hosts; two proceedings-link requests through Search returned 403. These
are route leads only: no local source body or complete proceedings reconciliation
was captured, and no edition disposition changed. All 42 v10 output hashes verify;
its 170 statuses, 76,629 guarded assignments and 1,095 protected tests remain
unchanged. See [source triage](five-year-source-triage.md#acm-and-siam-official-route-review-work-011)
and [WORK-011](work-log/2026-11-07-011-acm-siam-source-route-review.md).

## Previous iteration — IEEE conference source-route review (WORK-010)

WORK-010 checked official route leads for the 15 unresolved ICDM/ICRA/IROS
venue-years, but captured no complete hash-bound roster. Direct source requests
failed DNS, and the Search connector refused PaperPlaza under its robots policy.
All 15 editions remain unresolved. The aggregate Report refresh is local only;
the supported Sites helper failed before checkout, so the Site source could not be
audited or built. No push or deployment occurred; the public Site remains at v18.
See [WORK-010](work-log/2026-11-07-010-ieee-edition-route-review.md).

## Previous iteration — ICLR official roster access retry (WORK-009)

The official OpenReview v2 endpoint was retried. Public ICLR 2024 group metadata
identified the expected submission invitation, but the read-only notes request
returned HTTP 403 ChallengeRequiredError. No challenge was attempted and no full
roster was captured. All five ICLR years remain unresolved; v10 and all frozen
assignments are unchanged. P01 remains failed and P02 no-go. See [source triage](five-year-source-triage.md#iclr-official-api-access-retry-work-009)
and [WORK-009](work-log/2026-11-07-009-iclr-official-roster-access.md).

The route blocker is published on the existing public Site as [version 18](reference/sites-iclr-access-retry-publication-2026-11-07.json)
at the unchanged public URL and audience. Cache-busted live browser verification
confirmed the blocker text, preserved Plan and zero console warnings/errors.

## Previous iteration — AAMAS 2023 official identifier scan (WORK-008)

All six hash-bound official AAMAS 2023 captures in source-corrections v6 still
match their recorded hashes. The accepted page exposes no per-entry record IDs
or DOI; the proceedings contents provide 528 PDF identifiers without DOI links.
An exploratory exact ordered-byline comparison yields 196 unique candidate links
to proceedings IDs: 190 also match the normalized title, six have title variants,
40 have no candidate, and one has multiple candidates. These are not adjudicated
matches. The official author index remains incomplete at 471 PDF-link occurrences,
316 record IDs and 154 IDs labeled Main Track Full Paper. The edition remains
unresolved, no roster rows were added, and roster v10/all frozen inputs remain
unchanged. P01 remains failed with 62 incomplete candidates and P02 remains no-go.
See [source triage](five-year-source-triage.md#aamas-2023-official-identifier-scan-work-008)
and the [work entry](work-log/2026-11-07-008-aamas-2023-followup.md).

The AAMAS summary is published on the existing public Site as [version 17](reference/sites-aamas-2023-followup-publication-2026-11-07.json),
at the unchanged project ID, URL and public audience. The publication preserves
the full Plan and historical 399/533 explorer. Live browser verification confirmed
the Report tab and new aggregate counts; it returned zero console warnings/errors.

## Previous iteration — MICCAI 2022 official source-route follow-up (WORK-007)

The official MICCAI Society index has **573 unique detail records**; its category
page has 572. Eight Springer main-volume tables contain **576 unique chapter DOI
records**, while their descriptions claim 574 revised full papers and the series
index displays 576. The normalized-title join has 558 unique pairs, leaving 15
Society records and 18 chapters unmatched, including three correction notices.
Program documents did not resolve the one-record discrepancy, so MICCAI 2022
remains unresolved and ineligible. No byline adjudication or missing-paper
inference was made. The [D034 source overlay](../data/manifests/five-year-source-corrections-v9.json)
binds 37 official captures; all 37 hashes verified locally.

Roster v10 remains unchanged at **98 eligible editions / 10 verified no-edition
findings / 22 unresolved roster/adapter editions / 40 access-unavailable
editions**, with **94,857 observations: 91,355 included and 3,502 excluded**.
The 62 incomplete candidates keep P01 failed and P02 no-go for broader
enrichment. All 76,629 frozen assignments, including 1,095 tests, and v2-bound
diagnostic/pregraph inputs remain protected. Program PDFs are ignored source
evidence; no paper PDFs, new roster, split, enrichment, graph or database output
was created. See the [work entry](work-log/2026-11-07-007-miccai-2022-source-followup.md)
and [completion plan](pregraph-completion-plan.md).

The D034 summary is published on the existing public Site as [version 16](reference/sites-miccai-2022-followup-publication-2026-11-07.json),
with the same project ID, URL and audience. It preserves the historical 399/533
explorer and 2021–2025 report snapshots. Local browser QA confirmed the new D034
content, tabs, keyboard search, graph projection and mobile layout. The existing
search dialog still does not close with Escape; its Close search button works.

## Previous iteration — MICCAI 2024 full-proceedings reconciliation (D033 / WORK-006)

V10 reconciles the MICCAI Society’s **856** accepted 2024 research records to
**856 distinct Springer chapters**: 836 exact-title and 20 title-and-byline
matches across all 12 main-proceedings volumes. Springer has one additional
chapter, a correction notice tied to an already-listed paper, which is excluded
as nonresearch. All 49 Springer contents pages are hash-bound in source-corrections
v8 under D033; no per-record roster metadata or PDFs are published.

The roster now has **98 eligible editions / 10 verified no-edition findings / 22
unresolved roster/adapter editions / 40 access-unavailable editions** and **94,857
observations: 91,355 included and 3,502 excluded**. The 62 incomplete candidates
keep P01 partial. See [D033](decisions.md#d033--miccai-2024-full-proceedings-reconciliation-2026-11-07),
[the v10 report](../reports/five-year-source-recovery-v10.md), [ledger](../reports/five-year-edition-ledger-v10.csv),
and [source triage](five-year-source-triage.md).

All **76,629 frozen assignments**, including **1,095 tests**, remain guarded; v10
created no split. A fresh isolated replay exited 1 as expected and matched all
42 saved output hashes; all 36 inherited v9 edition artifacts are unchanged.
No enrichment, PDF, graph, or database operation occurred. P02 remains no-go for
broader enrichment, and the diagnostic/pregraph inputs remain bound to v2. The
full offline suite and focused parser checks are recorded in WORK-006. The local
[Site Report](../reports/site-report.md) is refreshed; native Site version 15 is
published with matching receipt and snapshots.

## Previous iteration — MICCAI roster v9 and 2022 source hold (D032 / WORK-004)

V9 added MICCAI 2021 (531), 2023 (730) and 2025 (1,027). MICCAI 2022 remained
unresolved after HTTP 522 with Springer counts 574/576. The v9 totals were 97
eligible editions and 94,000 observations (90,499 included, 3,501 excluded), with
23 unresolved and 40 access-unavailable candidates. See the [v9 report](../reports/five-year-source-recovery-v9.md)
and [WORK-004](work-log/2026-11-07-004-miccai-source-review.md).

## Previous iteration — ICLR official source-route review (WORK-2026-11-07-003)

P01 checked official OpenReview routes for ICLR 2021–2025. The official 2024
proceedings/fact-sheet counts agree at 2,260; the 2025 book and hosted draft
fact-sheet counts differ (3,703/3,704). The local OpenReview API request returned
HTTP 403, and local proceedings retrieval failed DNS. No hash-bound ICLR roster
was produced, so all five ICLR years remain unresolved and no eligibility changed.
See the [work entry](work-log/2026-11-07-003-iclr-source-review.md).

## Previous iteration — AAMAS official roster closure v8 (WORK-2026-11-07-002)

Roster v8 adds complete official AAMAS 2021, 2022, 2024 and 2025 main-research
rosters under D031. AAMAS 2023 remains unresolved: the official sources disagree
on extended-abstract counts, 12 of 237 accepted full-paper titles do not join
exactly to proceedings titles, and 35 exact-title matches have different author
strings. These automated joins are not human adjudications; no 2023 roster rows
were added. The IFAAMAS redistribution notice is respected: full rosters and
detailed captures remain in ignored local storage; no PDFs were downloaded.

- The ledger has **94 eligible editions / 10 verified no-edition findings / 26
  unresolved roster/adapter editions / 40 access-unavailable editions**, with **91,712
  observations: 88,211 included and 3,501 excluded**. The 66 remaining candidates
  keep P01 incomplete. See the [v8 report](../reports/five-year-source-recovery-v8.md),
  [ledger](../reports/five-year-edition-ledger-v8.csv), and [D031](decisions.md#d031--aamas-official-roster-closure-and-2023-reconciliation-hold-2026-11-07).
- The source-disabled discovery replay matched all **34 recorded output hashes**
  and exited 1 as expected while scope gaps remain. The full suite passed **193
  tests** in this iteration. All **76,629 frozen assignments**, including **1,095
  tests**, remain guarded. No new splits, enrichment, canonical merges, graph
  construction/import or database operations occurred.
- P02 remains **no-go for broader enrichment**; canonical work counts, the
  prospective P03 frame, live resource/storage limits and actual reviewer capacity
  remain unmeasured. The diagnostic/pregraph inputs remain bound to v2.
- The local [Site Report](../reports/site-report.md) is refreshed. The public Site
  remains v14; publication was not attempted in this iteration.

P01 remains active. Continue on the 26 unresolved roster/adapter and 40
access-unavailable candidates using complete, permitted official rosters.
Preserve all frozen IDs;
do not begin enrichment or graph construction under the current P02/P03 gates.

## Previous iteration — pregraph completion plan (D028)

- [Complete pregraph prerequisite plan](pregraph-completion-plan.md): P00–P10,
  source backlog, dependencies/roles, resource and reviewer feasibility,
  independent evaluation, accepted support inventories and twelve readiness gates.
- Scope, schema, quality targets and frozen samples unchanged. Final graph/import,
  final uniform-edge audit and actual network findings remain later stages.
- Documentation only: no implementation, collection, service checks, tests or Site
  publication this iteration. Measured task 007 results below remain historical;
  the existing Site remains v14 and the diagnostic preparation freeze stays false.
- This was documentation only. Execution began separately under WORK-009 on
  7 November; the plan itself did not authorize execution.

## Previous iteration — P00/P01 source closure and P02 feasibility (WORK-009)

The user instructed us to proceed from [the completion plan](pregraph-completion-plan.md).
The bounded source correction and feasibility assessment are complete for this
iteration; P01 and overall pregraph readiness remain incomplete.

- **ICAPS 2025:** the official main technical call, topic policy and accepted-paper
  page confirm all 48 previously reviewed theoretical/algorithmic/modelling/tools
  records as accepted main-research papers. Three accepted position papers and one
  frontmatter record remain excluded under the existing policy. See
  [source triage](five-year-source-triage.md) and [D029](decisions.md#d029--icaps-2025-roster-correction-and-enrichment-no-go-2026-11-07).
- **Roster v6:** 89 eligible editions / **85,850 included** records from 88,608
  observations; 2,758 excluded, zero record-level review. All 170 candidates remain:
  41 unresolved / 40 unavailable, or **81 gaps**. The source-disabled discovery
  replay exits 1 as expected while those gaps remain.
- All **76,629 frozen assignments**, including **1,095 tests**, remain guarded.
  No split, enrichment, merge, held-out acquisition, graph construction/import or
  database operation occurred. The diagnostic/pregraph freeze remains bound to v2.
- `UV_CACHE_DIR=/tmp/uv-cache-work009 uv run pytest`: **181 passed**. A source-disabled
  v6 CLI replay returned expected exit 1 for 81 gaps; roster/leakage content matched
  after normalizing refreshed `checked_at` stamps and dependent hashes. **8,483/8,494**
  task-start files remain hash-identical; eleven existing source/docs files were
  intentionally revised, and versioned v6 outputs were added.
- P02 is **no-go for broader enrichment**: the canonical work population, P03 frame,
  live free-resource limits, storage budget and reviewer capacity are not measured.
  The current enrichment budget remains zero; this is not a forecast or scope change.
- [Measured v6 report](../reports/five-year-source-recovery-v6.md),
  [ledger](../reports/five-year-edition-ledger-v6.csv),
  [feasibility checkpoint](../reports/five-year-pregraph-feasibility-v1.md).
- The local [Site Report](../reports/site-report.md) is updated. The public Site
  remains v14 because automatic review rejected sending its short-lived source
  credential through the escalated terminal; publication awaits explicit approval.

## Previous iteration — official edition route closure v7 (WORK-2026-11-07-001)

Roster v7 applies the official source correction in D030. Ten of the 11 previously
unverified routes are now verified no-edition findings; the official COLING 2024
joint LREC-COLING roster is included once under COLING. The current ledger has
**90 eligible editions / 10 verified no-edition findings / 30 unsupported
adapters / 40 access-unavailable editions**. It contains **90,163 observations**:
87,404 included and 2,759 excluded. The 70 remaining gaps still fail P01.

- The v7 replay matched every recorded output hash, including the edition ledger
  and COLING roster; it exits 1 as expected because gaps remain. **187 tests
  passed.** All 76,629 assignments, including 1,095 tests, remain guarded. No new
split, enrichment, merge, accepted support, graph construction/import or database
operation occurred. Semantic accuracy remains unmeasured.
- [Measured v7 report](../reports/five-year-source-recovery-v7.md),
  [ledger](../reports/five-year-edition-ledger-v7.csv),
  [source triage](five-year-source-triage.md), and
  [D030](decisions.md#d030--official-route-closure-and-coling-joint-edition-mapping-2026-11-07).
- P02 remains **no-go for broader enrichment**. The population, prospective P03
  frame, live free-resource limits, storage budget and actual reviewer capacity
  are not measured; no broader enrichment budget is authorized.
- The local [Site Report](../reports/site-report.md) is refreshed with v7. The
  public Site remains v14. The earlier automatic approval review rejected sending
  its short-lived source credential through the terminal helper; no credential
  transmission or publication was attempted during this continuation.

At that v7 checkpoint, the next action was to continue P01 on the 30
unsupported-adapter and 40 access-unavailable candidates. WORK-002 has since
added four AAMAS rosters; 26 unresolved roster/adapter and 40 access candidates
remain. The P02 enrichment stop and all frozen assignments and v2-bound diagnostics remain in
force.

## Historical official source recovery v5 (D027)

- Roster **v5: 88 eligible editions / 85,802 included records**; 88,608 total
  including 2,758 excluded and 48 review records. All 170 candidates retained:
  **41 unresolved / 40 unavailable / one needs review** (82 gaps, down from 91).
- Recovered AAAI 2021–2025 and ICAPS 2021–2024; 10,147 additional eligible records.
  ICAPS 2025's 48 research-category records stay review; no guessed main-track
  acceptance. Eleven non-main AAAI issues excluded at catalog level, not fetched.
- Existing **78,321 roster rows** identical; all **76,629 frozen assignments**
  guarded, including **1,095 tests** (925 old + 170 new). No redraw or enrichment.
  Four included roster records quarantined as version candidates; no canonical merges.
- **177 tests passed**, three source-disabled replays identical. **8,104 prior
  artifacts unchanged**, 562 source objects verified; **92 new official HTML
  responses**, zero OpenAlex/ORCID/PDF/model requests. No DB operations or new
  service checks. Previous task's Neo4j/GROBID results remain historical.
- Current config `configs/corpus-five-year-v5.yaml`, outputs
  `data/manifests/five-year-roster-v5/`. V3/v4 outcomes preserved. The original
  diagnostic sample, corroboration v3 and failed pregraph v3 freeze remain bound
  to their old inputs; this iteration neither reruns nor supersedes that freeze.
- [Measured report](../reports/five-year-source-recovery-v5.md),
  [aggregate](../reports/five-year-source-recovery-v5.metrics.json),
  [170-row ledger](../reports/five-year-edition-ledger-v5.csv).
  Native Site **v14 published**, same public audience/URL and unchanged explorer.
  [Receipt](reference/sites-source-recovery-publication-2026-11-06.json).
  Static/hosted HTTP checks and downloads pass; browser interaction QA incomplete
  (tab click timeout; follow-up inspection did not return).
- **Next:** corroborate ICAPS 2025 tracks and remaining source families; freeze a
  budgeted supplemental sampling/review design preserving every reserved version
  before collecting new enrichment. Independent development review remains needed.
  No graph construction/import authorized by the existing freeze.

## Preserved pregraph preparation — full readiness NOT achieved (D026)

- User requested all remaining work before graph construction. **No graph built or
  imported.** The bounded diagnostic preparation is implemented/frozen; the full
  request remains partial while coverage, collection/work resolution and independent
  quality prerequisites are missing. Closing a claim as withheld does not pass a gate.
- **19 printed-source reviews; 55 source-accepted / 13 withheld development papers**.
  Six parser/byline recoveries and eight additional printed affiliation reviews;
  all original statuses preserved. **10 people / 11 authorships / 12 affiliation
  triples**, nine affiliated author–paper pairs, nine organizations.
- Known-frame crosswalk: **318** historical/new exposed diagnostics checked against
  known rosters/reserved IDs; zero detected conflicts, no canonical merges or
  global identity certification. All **339 current queue rows** have withheld
  dispositions. Original 345 rows: **8 resolved / 337 withheld**, mixed claim units.
- **17 uncalibrated topic candidates on 16 papers**, zero accepted labels; 39 no-phrase
  abstentions and 13 source-withheld papers. Zero in-tranche citation candidates.
- **156 tests passed**; identical offline/source-disabled replay. **7,895 protected
  artifacts** and **369 source objects** verified. Seven new ORCID responses,
  zero OpenAlex/PDF/model requests. GROBID/both Neo4j healthy at fresh end check;
  counts **154/211** and **399/533**, matching task 005; no writes.
- Failed full gates: **91 edition gaps**, full enrichment, researcher/affiliation/
  topic coverage, global canonical works. Topic quality unmeasured; independent
  component labels not run. Blank two-reviewer development forms prepared; no
  annotations invented and no held-out sources acquired.
- [Measured report](../reports/five-year-pregraph-v3.md),
  [aggregate](../reports/five-year-pregraph-v3.metrics.json),
  [workflow](five-year-collection.md#pregraph-staging-and-explicit-readiness-gates-d026).
  Native Site **v13 published**, same URL/public audience and historical explorer.
  [Receipt](reference/sites-pregraph-publication-2026-11-06.json). Static/HTTP checks
  pass; interactive browser evaluation did not return, so that QA is incomplete.
  V12 below is historical.

## Historical reviewed development support (D025)

- **Five** input/PDF-bound printed-source overlays; **49/68 source-eligible papers**,
  up from 45. COLT editors separated from authors; two RSS printed headers recovered
  as review overlays. Original one failed metadata / two parser failures unchanged.
- **84** public ORCID works responses; **10 corroborated researchers** (one historical,
  nine new IDs), **11 authorship supports across nine papers**, **one** reviewed
  author–paper–organization triple. **345 review rows**; mixed units, not an error rate.
- **145 offline tests passed**. Real/replay exits 1 for pending review; identical
  summaries and an additional network-disabled replay passed. **7,645 protected
  artifacts** unchanged, **362 source objects** verified; zero new OpenAlex requests.
- GROBID healthy; both Neo4j HTTP 200 and read-only pre/post counts **154/211** and
  **399/533**. No graph writes, no five-year graph materialization/import.
- Stable crosswalk conflicts, missing publication corroboration and unreviewed
  affiliations remain withheld. Independent semantic accuracy, recall and F1 remain
  unmeasured; these are bounded development evidence contracts.
- [Measured report](../reports/five-year-corroboration-v1.md),
  [aggregate JSON](../reports/five-year-corroboration-v1.metrics.json),
  [workflow command](five-year-collection.md#reviewed-development-corroboration-d025).
  Native Site **v12 published successfully**, same public audience/URL, 20 Plan
  sections and unchanged 399/533 explorer. [Receipt](reference/sites-corroboration-publication-2026-11-06.json).
  Local mobile/desktop, keyboard tabs, search, graph controls and downloads passed;
  zero console errors/embeds. V11 below is historical.

## Historical five-year PDF/header development evidence (D024)

- **68 PDFs available locally; 66 parsed / two GROBID HTTP 500 records retained**.
  RSS 2025 p046/p108 render visible text but have no first-page `pdftotext` output;
  OCR/alternate conversion is pending. No full-corpus/PDF/model collection.
- **47** papers have parsed affiliation blocks; **62** header titles and **48**
  complete ordered bylines agree with the roster. **45** papers pass all candidate
  binding checks. **255** deduplicated affiliation candidates, **56** exact
  author-specific institution matches; all remain review, not accepted triples.
- Printed review on **five papers**: MLSys full byline corroborated but original
  metadata remains withheld; COLT proceedings editors misread as authors; two RSS
  parse failures diagnosed; one IJCAI shared affiliation block corroborated.
  No author aliases, accepted identities or graph writes.
- **130 tests passed**; replay summaries identical (exit 1 for two parse failures).
  **7,297 protected artifacts unchanged**, **269 evidence objects verified**;
  zero held-out overlap and **zero new OpenAlex requests**.
- Preflight: Neo4j **154/211**, GROBID healthy. Post-run Docker became unreachable;
  service restart/check results are recorded in the work log. No post-count claim
  until a new live check succeeds. Historical graph payloads remain unchanged.
- [Measured PDF/header report](../reports/five-year-headers-v1.md),
  [aggregate JSON](../reports/five-year-headers-v1.metrics.json),
  [printed source notes](../data/manifests/five-year-printed-review-v1.json).
  Native Site **v11 published successfully**:
  [receipt](reference/sites-headers-publication-2026-11-06.json). The v10 entry below is historical.

## Previous five-year roster/metadata iteration (task 003)

- **78,321** roster records: **75,655 included / 2,666 excluded**; **79 eligible
  editions**, up from 67. All **170** candidates retained; **51 unresolved / 40
  unavailable** remain. No inferred no-edition findings or full coverage claim.
- NeurIPS 2025 position tracks, ECVA accordion/year mapping, RSS official catalog
  year corroboration and KR Full/Short/Main track policies corrected in **v2**.
  Historical v1, all raw inputs, old configs and finalized logs unchanged.
- Prospective design frozen before enrichment: **68 new development diagnostics,
  170 new reserved tests, 34 source-family/year strata**, with seed/populations/
  probabilities. All **14,909** old assignments, including **5,046** originals,
  remain identical. New reserved IDs must also be preserved in later versions.
- **67/68 metadata records acquired**, **67 abstracts**, **36 strict OpenAlex
  work matches**. One MLSys 2025 expanded-name/initial byline conflict withheld.
  No forced identity merge, PDFs, accepted researchers or five-year graph yet.
- **Zero held-out papers acquired.** Provider/test-location conflicts are quarantined.
  Preliminary version guards do not detect every alternate-title version or finish
  canonical work resolution. No independent semantic accuracy/recall/F1 measured.
- OpenAlex: **$0.067 of daily free allowance used / $0.933 remaining**, zero prepaid
  balance at check. **120 offline tests passed**. Discovery exits 1 for remaining
  scope gaps; metadata/replay exit 1 for the one withheld byline; outputs retained.
- Docker: base Neo4j healthy, **154 nodes / 211 edges** before/after read-only checks;
  existing GROBID started and `isalive=true`. No extraction or database writes.
- Native Site Report update: **v10**, existing URL/public audience, new aggregate
  downloads. Historical explorer remains **399/533**, candidate **402/538** separate.
  [Publication succeeded](reference/sites-diagnostics-corrected-publication-2026-11-06.json);
  no automatic/background sync.
- Discovery/freeze/metadata summaries replay identically. V2's new
  `corpus_manifest-complete.parquet` preserves optional KR fields; the earlier
  lossy mirror is historical. Use JSONL or the complete mirror for downstream work.

## Preserved five-year diagnostic artifacts (D023)

| Artifact | Path |
| --- | --- |
| Roster config / ledger | `configs/corpus-five-year-v2.yaml`, `data/manifests/five-year-roster-v2/` |
| Preliminary leakage triage | `data/manifests/five-year-reconciliation-v2/` |
| Frozen diagnostic design / membership | `configs/five-year-diagnostics-v1.yaml`, `data/manifests/five-year-splits-v1/` |
| Metadata / byline review | `data/interim/five-year-acquired-v1/`, `data/manifests/five-year-diagnostic-review-v1.json` |
| Corroborated development support | `data/processed/five-year-corroborated-v1/`, `configs/five-year-corroboration-v1.yaml` |
| Printed source overlays | `data/manifests/five-year-source-corrections-v1.json` |
| Measured aggregate / ledger | `reports/five-year-collection-v2.{md,json}`, `reports/five-year-edition-ledger-v2.csv` |
| Raw checks (ignored) | `reports/runs/WORK-2026-11-06-003/` |

## Latest measured candidate — historical 2023 evidence (task 001)

- All **250 diagnostic metadata records acquired**, 240 abstracts, 145 strict
  OpenAlex matches. Acquisition v4 reuses 245 successful historical records.
- After the user started containers, GROBID extraction v5 parsed **240 PDFs**;
  ten MICCAI records lack official PDF URLs. The failed-service v4 pass is preserved.
- Reviewed five byline conflicts: **three core admissions, two withheld** for
  contradictory PDF author order/count. No identity aliases or threshold relaxation.
- Candidate **`pilot-topic-7e3c90189547`**, **402 nodes / 538 edges**: 248 Paper,
  85 Researcher, 32 Organization, 20 Topic, 17 Venue. **372 factual R1–R4** edges,
  110 inferred topics, 16 taxonomy, 40 derived. Eight predicates nonempty.
- Original **718 queue rows** triaged without graph overrides. Stored technical
  checks pass for 85 identities / 38 affiliation triples, with 813 cached objects
  checked. Five printed-source observations corroborate existing mappings;
  **no affiliation triple IDs added or removed**. Candidate queue: 723 rows.
- **97 offline tests passed in task 001**; its structural validation and lock consistency
  passed. `--require-size` correctly returns 1. Final candidate's 513 source objects,
  20 protected files and all 5,046 legacy assignments verified; zero held-out overlap.
- These are agent development checks. **Independent semantic accuracy is unmeasured**;
  no precision, recall or F1 release claim. See [D017](decisions.md#d017--input-bound-development-source-review-2026-11-04).

## Historical service checks and visual output

In task 001 (4 November, 01:14 +07:00), GROBID 8070 and Neo4j HTTP 7474/7475 return 200. Both databases pass six integrity
queries and have the same content digests as task 006, checked then, not rerun during planning task 002:

| Output | Version / contents |
| --- | --- |
| Neo4j original, Browser 7474 / Bolt 7687 | `pilot-topic-0bb7f11a404e`; 154 nodes / 211 edges |
| Neo4j expanded, Browser 7475 / Bolt 7688 | `pilot-topic-d512d7239923`; 399 nodes / 533 edges |
| [Offline HTML report](../reports/extended-v1.html) | Previous expanded graph, 399 / 533; task 007 browser checks |
| Local candidate, not imported | `pilot-topic-7e3c90189547`; 402 / 538 |

No database writes in task 001 or planning task 002. The loader rejects replacement versions sharing
entity IDs; safe migration or an isolated instance is required before candidate
loading. The HTML's matching original metrics remain unchanged. Do not claim it
shows the new candidate. No collection jobs remain running.

## Historical 2023 scope and frozen samples

D015 authorized historical expanded 2023 collection. D018 expanded the target
to 2021–2025; D022 subsequently authorized staged collection. Historical scope was
**34 series / 31 in-year 2023 editions**; preserved executable config
`configs/corpus-extended-v2.yaml`. **17 covered / 14 unresolved**, plus ECCV/NAACL/
COLING without a 2023 edition. Ledger: 15,738 records, 14,909 included / 829 excluded.
This is partial conference coverage; see [the original expanded report](../reports/extended-v1.md).

Frozen membership: **925 test / 470 development / 13,514 pool**; all 5,046 legacy
assignments, including 120 test / 60 development, preserved. Diagnostics remain
250 (original 100 plus ten per 15 new venues). Held-out samples remain unannotated.
Legacy configs, data, reports and original Sites snapshots are preserved.

## Active local artifacts

| Artifact | Path |
| --- | --- |
| Roster / edition ledger | `data/manifests/extended-corpus-v3/` |
| Frozen membership | `data/manifests/extended-splits-v3/` |
| Metadata / extraction | `data/interim/extended-acquired-v4/`, `extended-headers-v5/` |
| Original queue triage | `data/processed/extended-review-v1/` |
| Reviewed source ledger | `data/manifests/reviews/source-review-v2.json` |
| Candidate base graph / queue | `data/processed/extended-resolved-v3/` |
| Candidate topic/derived graph | `data/processed/extended-graph-v2.json` and sidecars |
| Current raw checks | `reports/runs/WORK-2026-11-04-001/` (ignored) |

Earlier artifacts remain historical diagnostics; source-review-v2 supersedes the
byline-only review-v1 ledger, and resolved-v2 is a preliminary candidate.

## Next tasks and limits

Continue P01's remaining official source routes. Keep P02 no-go until reviewer
capacity is established: one reviewer is reported, exact hours are unknown, and
a second independent reviewer is unconfirmed. Address full pregraph gates before
building a release graph: a prospectively frozen feasible larger enrichment design, canonical
versions and independent topic/component labels. Current diagnostic support is
frozen under `configs/five-year-pregraph-v3.yaml`; baseline topics and ambiguous
claims remain unaccepted. Do not reprocess the same withheld claims without new
source evidence or move exposed papers into independent tests. Human review forms
are local/ignored; no review has been attributed to a teammate.

E01 still has unsupported/unavailable source families; E03 canonical work resolution
is incomplete. E04's layout/year diagnostic design is frozen, not a release audit.
E05 remaining source/header gaps, E06 full identity/topic quality, E07 isolated graph, E08 independent audit and
E09 final ≥10-page report/reproduction remain incomplete. Keep final writing time.

Internal cutoffs (+07:00): stop adding source families/features 8 November 18:00;
candidate/method freeze 9 November 18:00; record actual gates 10 November 12:00;
submission-ready package 10 November 18:00. Do not lower gates for the deadline.
Lecturer interpretation, member names/IDs, annotation hours and code license remain
unspecified; the 11 November submission date is confirmed.

Git remains main at 66e692d with prior edits preserved; no project commit/push.
Configured origin: git@github.com:HSandz/scientific-network.git. Remote/privacy/
clean-clone reproduction were not checked. No collection jobs intentionally left
running after task finalization. Task 004 Docker outage is superseded by task 005: fresh pre/post checks succeeded
for GROBID and both databases. No collection jobs remain running.
