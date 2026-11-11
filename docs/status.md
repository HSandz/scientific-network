# Current project status

Updated: **2026-11-11T18:18:24+07:00**. Plan: [D040](release-plan.md), with
[user-authorized Task2B amendment](decisions.md).
Latest: [WORK-2026-11-11-004](work-log/2026-11-11-004-identity-recovery.md).

## Phase checklist

- [x] Historical v4, candidate-v3, original sources and audit judgments preserved.
- [x] Task2B baseline verification and seven DOI reconciliation investigations.
- [x] Complete target-ID inventory and prioritized public source review.
- [x] Prospective identity probability/diagnostic samples, blank packets and scorer.
- [x] Bounded resolver recovery and isolated final candidate construction.
- [x] Structural/source checks, deterministic replay and three-way comparison.
- [x] Full suite:603 passed, one existing skip; focused suite:115 passed.
- [x] Reports, code/source/config hashes, preservation and local checkpoints.
- [ ] Independently adjudicated identity references and semantic P/R/F1.
- [ ] Evidence-supported promotion decision after independent evaluation.
- [ ] Task3 affiliation work, separately authorized; identity ceiling still below target.
- [ ] Personal/course facts and final submission.

## Scientific boundary

Production remains frozen v4. Task2B final development candidate:
`release-identity-v5-503aafe10a31`, implementation checkpoint `eab4dce`.
[Measured report](../reports/quality-v5/task2b-v1/implementation-report.md),
[reproduction and artifacts](../reports/quality-v5/task2b-v1/README.md),
[validation](../reports/quality-v5/task2b-v1/validation-report.md).
Coverage/source support improve over candidate-v3; semantic precision/recall do
not have independent measurements. Public ORCID declarations are construction
evidence, not independent gold. DOI ambiguities remain explicit; no source-corrected
graph is justified. Preserve both candidates; no scientific promotion yet.
No Task3/topic/Explorer work, DB writes, service changes, push or deployment.

## Next step

Obtain independent references using the frozen identity packets, adjudicate with
source-independence evidence, and score v4/v3/revision on the same units. Continue
targeted identity investigation before treating affiliation enrichment as capable
of meeting the end-to-end target. Technical Task3 inputs are available separately.
