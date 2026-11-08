# Current project status

Updated: **2026-11-08 13:03 +07:00**. Deadline: **11 November 2026**.
Plan: [release plan](release-plan.md) under [D040](decisions.md#d040--release-reset-for-the-11-november-submission-2026-11-08).
Latest entry: [WORK-2026-11-08-031](work-log/2026-11-08-031-release-neo4j-loads.md).

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
- Tests: 354 passed, 1 skipped (WORK-031).

## Phase checklist

- [x] P0 Housekeeping
- [x] P1 Tooling fixes
- [x] P2 OpenAlex acquisition
- [x] P3 Graph v1: all ten relations, structural validation, summary and size gates
- [x] P4 Neo4j v1 load, inventory, integrity and idempotent replay
- [x] P5 Frozen embedding classifier; graph v2 validated, loaded and replayed; topic sheet ready
- [ ] P6 Network analysis, figures and findings
- [ ] P7 Graph freeze and review sheets
- [ ] Human edge/topic review returned
- [ ] P8 Scoring, full report draft and README
- [ ] P9 PDF, release and submission

## Next action

Continue P6 from graph v2: run configured analysis, identify missing metrics, and produce
the planned figures and evidence-backed business findings.

## Waiting on the user

- Complete the topic and edge review sheets with the reviewers; do not report accuracy
  until those labels are returned and scored.
- Fill in `docs/team.md`, choose lecturer repo access and confirm course AI-use disclosure.
