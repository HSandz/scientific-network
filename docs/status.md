# Current project status

Updated: **2026-11-10 09:30 +07:00**. Deadline: **11 November 2026**.
Plan: [D040](release-plan.md); user adopted [full remediation](prompts/implement-remediation-plan.md).
Latest completed: [WORK-2026-11-10-005](work-log/2026-11-10-005-research-explorer-usability-implementation.md), Research Explorer usability and graph operations implementation.

## Remediation and presentation checklist

- [x] A Topic labels required; original failed scores exactly reproduced.
- [x] B Versioned observed-ORCID identity correction; frozen facts/topics preserved.
- [x] C Isolated Neo4j import/integrity/replay and corrected full analysis completed (WORK-012).
- [x] D Prospective source-backed AI edge audit complete; numeric gates pass.
- [x] E Measured report and local draft package complete; old artifacts preserved.
- [x] Presentation: three bounded network maps added; native Site v19 published with current data, six charts and PDF download.
- [x] Fresh review: exact edge rescore, structure/size, hashes/package checks; 508 tests passed / 1 existing skip.
- [x] Local interactive explorer (`apps/research-explorer/`): FastAPI + React/TypeScript/Sigma.js/ECharts workspace backed by live `neo4j-five-year` (WORK-016).
- [x] Explorer design review: [findings](../reports/research-explorer-design-review-2026-11-09.md) recorded (WORK-017).
- [x] Explorer redesign & verification: `achromatic-ledger` light/dark system, responsive shell (`1440px`/`768px`/`390px`), contextual inspector, collision-free graph labels, name-based entity pickers, and table DB edge counts; `0 FAIL, 0 WARN` browser inspection, 4 Playwright E2E, 14 backend, and 507 repo tests pass (WORK-018).
- [x] Redesign follow-up review: [findings and priorities](../reports/research-explorer-redesign-review-2026-11-09.md) recorded (WORK-019).
- [x] Improvement planning: [plan](research-explorer-improvement-plan.md) and [implementation prompt](prompts/implement-explorer-improvements.md) prepared (WORK-020).
- [x] Explorer improvements implementation: soft graphite dark mode, unified quality contract, 6-breakpoint responsive shell, accessible modal focus/Escape layers, accent-insensitive search (WORK-2026-11-10-001).
- [x] Graph operations review & prompt: [findings](../reports/research-explorer-graph-operations-review-2026-11-10.md), [plan](research-explorer-graph-usability-plan.md), [prompt](prompts/implement-explorer-graph-usability-plan.md) (WORK-003, WORK-004).
- [x] Explorer graph usability implementation: authoritative effective view state, collision-free neighbor reading and pinning (Warut 7/7 names, dense node lists), explicit Overview/Ego/Path views with Back navigation, reciprocal/parallel edge preservation in multi-edge graphology, responsive layout and header hit targets, accessible drawers/pickers, and unavailable quality fallback; 15 backend tests, 5 Playwright E2E suites, 507 repo tests, design lint 0 FAIL (WORK-2026-11-10-005).

## Current artifacts

[26-page/nine-figure package QA and paths/hashes](../reports/release-v4/local-package-receipt-v3.json),
[report source](../reports/final-report/report.md), [results/limitations](../reports/release-v4/README.md),
and [local research explorer](../apps/research-explorer/README.md).
Source checkpoint `fb2f0e7`; all 1,410 archive members and 125 historical hashes preserved.
[Public Site v19](https://ai-research-network-plan.hazy-tern-8113.chatgpt.site/#report):
[exact publication receipt](reference/sites-corrected-release-publication-2026-11-09.json) (untouched by WORK-016..022).

## Quality and preserved history

AI-assessed edge precision 193/200 = 96.5%, Wilson 92.95–98.29%; human validation not performed, reviewer independence and verified course accuracy not established. Affiliation coverage 73.71% (FAIL 80%); historical topic F1 .4667/.2301 and precision-target failures persist. Old failed 88% audit, graph versions, classifier, samples and judgments unchanged. No retuning or resampling.

## Remaining personal facts and delivery

Real names/IDs/contributions, lecturer access and course AI-use requirements remain pending. Prior WORK-014 GitHub HEAD 404 means public/lecturer access was `not_verified`. Package remains a local submission draft. No GitHub push, tag, invitation or course submission performed. Supply personal/course facts before a new delivery render. Human annotation is optional.
