# Current project status

Updated: **2026-11-11 01:08 +07:00**. Deadline: **11 November 2026**.
Plan: [D040](release-plan.md).
Latest: [WORK-2026-11-11-001](work-log/2026-11-11-001-explorer-dashboard-redesign.md).

## Release phase checklist

- [x] Tooling/source acquisition and resolution completed.
- [x] Frozen topics, corrected graph, isolated import and analysis completed.
- [x] Source-backed AI audit/scoring; failed criteria remain disclosed.
- [x] Measured report, local submission package and QA completed.
- [x] Native public Site v19 published, unchanged by Explorer work.
- [x] Azure runtime and automatic API delivery previously verified.
- [x] Explorer projections, evidence, comparisons, paths and workspace restoration.
- [x] Authorized API release/recovery and global bookmark acceptance.
- [x] Scrolling dashboard, visible figures, accessible motion and zoom-aware labels.
- [x] Local build, contracts, Chromium screenshots and regressions.
- [ ] Redesign production deployment and live acceptance (in progress).
- [ ] Personal/course facts and final course submission.

## Current verification and release boundary

Repository tests: 530 pass / one existing skip. Six pure frontend contracts pass.
Full Chromium suite: 36 pass; margin follow-up: ten dashboard/two visual pass;
final missing-quality/saved-scroll regressions: two pass.
TypeScript/Vite build passes. Main bundle reduced from540KB to293KB, with
chart/graph engines deferred; chart runtime still537KB. No backend/data changes.
[Redesign report](../reports/explorer-ui-redesign-verification-2026-11-11.md)
records methodology, screenshots, exact checks and performance limitations.

Existing API deployment, immutable artifacts and public Site remain unchanged.
[Earlier production receipt](../reports/explorer-production-verification-2026-11-10.md).

## Scientific evidence and artifacts

[Release-v4 limitations](../reports/release-v4/README.md),
[final report](../reports/final-report/report.md),
[package QA](../reports/release-v4/local-package-receipt-v3.json).
AI precision is not independent human validation. Topic coverage is not accuracy;
failed affiliation/topic-quality criteria remain visible. No graph rebuild.

## Remaining limitations

Long-session memory/load, physical devices, Firefox/Safari and formal accessibility
certification remain unverified. Deferred ECharts bundle remains large. Graph and
comparison previews are bounded; Paths/comparisons disclose full-period scope.
Real names/IDs, lecturer access and final course submission remain pending.
