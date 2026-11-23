# Implementation roadmap

> **Current plan:** [release-plan.md](release-plan.md) (D040, 8 Nov 2026).
> Pre-D040 iteration notes (D015–D034, P01–P09) are
> [archived](archive/plans/roadmap-history.md).

## Current capabilities — D040 remediation

**11 November final submission cleanup:** review sheets distinguish source-consistent
support from independent semantic verification, including identity uncertainty
inherited by researcher-derived relations. Human packet v2 adds issue-ledger cases
as tagged diagnostics without changing the frozen 80-edge or 20-case random sample;
post-blind pages separate AI concerns from initial judgments. See [D041](decisions.md)
and [WORK-2026-11-11-008](work-log/2026-11-11-008-final-cleanup-submission-readiness.md).

**11 November Task2C identity validation:** strict local blind A/B review and
hash-bound adjudication/crosswalk compilation, descriptive partial-reference scoring,
blocked-pair estimand safeguards, bounded source packets and three-way topology
sensitivity. Task3 ledgers are prepared; independent human references remain pending
and scientific promotion is deferred. [Deliverables and reproduction](../reports/quality-v5/task2c-v1/README.md).


**11 November Task2B identity recovery:** targeted DOI/ORCID evidence inventory,
complete 170-ID abstention classification, formatting and declared-alias recovery,
exact-DOI alternate-source recovery for missing IDs, frozen probability/diagnostic
identity evaluation packets and a paired independent-reference scorer. A final
isolated candidate gains253 positions over candidate-v3; semantic precision/recall
remain unmeasured and the affiliation ceiling remains below80%. No promotion or
Task3 work. [Measured report](../reports/quality-v5/task2b-v1/implementation-report.md).


**11 November v5 identity candidate:** reproducible source/graph quality census,
historical guard and citation inventory, explicit paper mention states, checksum
and source-aware ORCID decisions, conservative crosswalks and positional recovery,
isolated materialization, exact retained affiliation support and paired centrality
comparison. Two runs reproduce byte-identical artifacts while preserving frozen v4.
This is a development candidate with unmeasured semantic precision/recall and lower
coverage; no promotion, collection or production change. See
[implementation and limitations](../reports/quality-v5/implementation-report.md).

**11 November focus/layout follow-up:** interactive canvas neighborhood labels at
all zooms, bounded collision-aware callouts, exact remaining-neighbor disclosure,
section-specific dashboard layouts, selected partnership evidence and stable-ID
persistence interactions. Existing analytics/bookmarks remain. See
[verification](../reports/explorer-focus-layout-verification-2026-11-11.md).

**11 November Explorer presentation:** seven scrolling analytical sections, API-backed quality/temporal/ranking figures, viewport-aware charts and inverse-camera zoom labels. Exact tables, evidence actions and v2 saved views remain available. See [redesign verification](../reports/explorer-ui-redesign-verification-2026-11-11.md). No scientific graph or backend change.

**10 November Explorer final integration:** accepted support-paper windows now
scope collaboration views/expansions; unsupported filters reject explicitly.
Complete comparison totals precede bounded previews. Saved Graph/Table/Analytics
workspaces preserve controls; finding return and exports preserve provenance.
Caddy orphan reaping, runtime package/strict analytics readiness and transactional
rollback are locally verified. [Final receipt and authorized-release procedure](../reports/explorer-final-integration-2026-11-10.md).
User-authorized production activation and live acceptance are complete, including
global workspace Save/Restore. [Production receipt](../reports/explorer-production-verification-2026-11-10.md); no scientific graph rebuild.

**10 November production operations:** the Explorer has an isolated Azure Docker
runtime with read-only Neo4j, one API worker, indexed SQLite evidence, compact
analytics, Caddy HTTPS, guarded restore/backup and bounded resource limits.
See [runbook](../ops/azure/README.md) and
[deployment receipt](../reports/release-v4/azure-deployment-2026-11-10.md) for
measured acceptance and current frontend cutover state.

**9 November presentation:** `python -m scientific_network.reporting.network_views`
exports three deterministic bounded induced maps and public evidence-pointer
JSON/CSVs from exact graph/analysis/freeze bindings. Published Site v19 provides native
projection/filter/zoom controls, source inspection and the new report PDF. Full projection counts remain
separate from displayed subsets; see [WORK-015](work-log/2026-11-09-015-release-review-graphs-site.md).

**9 November remediation:** `correct-release-identity` applies global singular-plus-observed ORCID withholding from immutable works, preserves frozen predictions without inference and emits full changes/content freeze. `score-agent-edge-review` supports prospectively frozen edge-only contexts and actual post-export adjudication metadata without attributing old topic references to new reviewers. Complete raw source packets retain observed arrays and verify against cache bytes. The original combined scorer now requires explicit topic labels; historical scores reproduce unchanged.

## Earlier capabilities — D040 agent evaluation and local packaging

**9 November implementation:** `score-agent-review` validates evaluator/source
ledgers, freeze/receipt bindings, canonical assignments, review order and truthful
AI metadata around the unchanged legacy scorers. Isolated A/B contexts are
available and selected; a pre-review freeze and matching agent packets exist.
Partial unreviewable topic references retain planned overlap weighting. No
single-agent topic fallback is selected or claimed implemented. Real source-backed
A/B judgments and provenance-bound scoring are complete; failed numeric quality
gates are preserved in the release-v3 results.

Release graph construction synchronizes and checks the frozen classifier taxonomy.
`correct-release-taxonomy` preserves frozen predictions/core facts without inference.
Edge auditing supports the normal A/B design, separate optional single-reviewer
packets, explicit partial scoring, dedicated reviewer packets and blank joint
adjudication preparation. Topic scoring accepts explicit replacement graph,
summary and freeze paths while retaining historical compatibility. Fractional
descriptive metrics use exact sums; community plots mark unstored topic shares.
See [the agent workflow](agent-audit-workflow.md), the preserved optional
[human handoff](reviewer-handoff.md) and [WORK-037](work-log/2026-11-08-037-pre-audit-corrections.md).
`python -m scientific_network.reporting.release_package` renders the measured
Markdown report to A4 PDF/portable HTML, validates headings/figures/local links,
and packages permitted tracked sources with member hashes. Raw data, models,
credentials and volumes remain excluded. Human validation, evaluator independence
and verified course accuracy are not established; publication/submission remain
pending. See [reproduction instructions](reproduce-agent-evaluation.md).
