# Current project status

Updated: **2026-11-11T16:44+07:00**. Plan: [D040](release-plan.md), with
[user-authorized v5 candidate amendment](decisions.md).
Latest: [WORK-2026-11-11-003](work-log/2026-11-11-003-quality-v5.md).

## Phase checklist

- [x] Historical v4 graph, sources, AI evaluation and package preserved.
- [x] Existing Site/Explorer delivery remains separate from this task.
- [x] V5 Task1 baseline pipeline/source/graph audit and issue inventory.
- [x] Task2 explicit mention resolver, shared ORCID policy and state bug fix.
- [x] Conservative isolated candidate and v4 comparison, with derived recomputation.
- [x] Retained affiliation sets and protected topics/citations/metadata verified.
- [x] Two-run deterministic replay and original-file preservation checks.
- [x] Full suite:579 passed, one existing skip; structural CLI passes.
- [x] Final implementation, validation, reproduction and artifact reports.
- [ ] Independent identity references and candidate promotion decision.
- [ ] Task3 affiliation resolution, separately authorized future work.
- [ ] Personal/course facts and final course submission.

## Scientific boundary

Production remains frozen v4. Final local development candidate:
`release-identity-v5-7e6b1a34ffa2`, implementation checkpoint `18f98d0`.
[Implementation/comparison](../reports/quality-v5/implementation-report.md),
[baseline](../reports/quality-v5/baseline-audit.md),
[validation](../reports/quality-v5/validation-report.md),
[artifacts/reproduction](../reports/quality-v5/README.md).
Candidate gains15 authorships and quarantines705; coverage decreases.
Independent precision/recall/F1 and actual false merge/split counts are unmeasured.
Historical AI precision does not certify this candidate or course accuracy.
No source collection, DB writes, Explorer/production edits, push or deployment.

## Next step

Review DOI/name/crosswalk ambiguities and reserve independent references before
future tuning. Task3 can consume preserved paper triples, exclusions and explicit
unresolved mentions; no Task3–8 implementation occurred in this session.
