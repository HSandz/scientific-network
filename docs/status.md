# Current project status

Updated: **2026-11-08 13:45 +07:00**. Deadline: **11 November 2026**.
Plan: [release plan](release-plan.md) under [D040](decisions.md#d040--release-reset-for-the-11-november-submission-2026-11-08).
Latest entry: [WORK-2026-11-08-032](work-log/2026-11-08-032-release-phase-6-analysis.md).

## State

- Scope, acquisition and graph v1 are complete under D040; 11 works remain in review.
- Phase 4 passed: v1 load, inventory, integrity query and idempotent replay on the
  isolated `neo4j-five-year` service.
- Phase 5 passed: classifier frozen, graph v2 validated and loaded, integrity query and
  replay passed, and the prediction-blind 50-paper topic sheet is ready.
- Current Neo4j database is graph `release-5d830ffcbdf4`: 52,415 nodes and 275,438
  relationships. The service remains healthy on localhost ports 7476/7689.
- Graph v2 summary: `reports/release-v1/graph-v2-summary.json`; load/replay receipts are
  under `reports/release-v1/neo4j-*.json`. Topic coverage is 11,575/13,617 (85.00%);
  semantic accuracy is not measured and human labels remain pending.
- P6 complete: release analysis `named-projection-analysis-v2`, six figure/table pairs,
  captions, and three bounded findings with two investigation shortlists are ready.
  All size gates pass; analysis remains `not_certified` and topic findings are provisional.
- Latest full test suite: 357 passed, 1 skipped (WORK-032).
- P7 complete: graph and four configs are hash-bound in `reports/release-v1/freeze.json`;
  edge and prediction-blind topic review sheets are prepared; report sections 2–7 are drafted.
- Edge audit is prepared, not performed. No independent labels or semantic accuracy scores
  are available; `docs/team.md` reviewer identities/contributions and course disclosure remain.

## Phase checklist

- [x] P0 Housekeeping
- [x] P1 Tooling fixes
- [x] P2 OpenAlex acquisition
- [x] P3 Graph v1: all ten relations, structural validation, summary and size gates
- [x] P4 Neo4j v1 load, inventory, integrity and idempotent replay
- [x] P5 Frozen embedding classifier; graph v2 validated, loaded and replayed; topic sheet ready
- [x] P6 Network analysis, figures and findings
- [x] P7 Graph freeze and review sheets
- [ ] Human edge/topic review returned
- [ ] P8 Scoring, full report draft and README
- [ ] P9 PDF, release and submission

## Next action

Have reviewers A and B annotate the assigned edge sheet and both reviewers label the
50 prediction-blind topic papers. Then run Phase 8 scoring and finish the report.

## Waiting on the user

- Return the completed A/B edge-review exports and two topic-label exports; no accuracy
  claim is available until these are scored.
- Fill in `docs/team.md` (real identities, roles and contributions), choose lecturer repo
  access and confirm course AI-use disclosure.
