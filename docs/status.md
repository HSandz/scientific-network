# Current project status

Updated: **2026-11-08 11:51 +07:00**. Deadline: **11 November 2026**.
Plan: [release plan](release-plan.md) under [D040](decisions.md#d040--release-reset-for-the-11-november-submission-2026-11-08).
Latest entry: [WORK-2026-11-08-028](work-log/2026-11-08-028-release-phase-3-verification.md).

## State

- Scope and OpenAlex acquisition are complete under D040; 11 works remain in review.
- Phase 3 graph v1 rebuilt with method `release-openalex-graph-v1.1`; version
  `release-4c1253e05f2c`. Fresh validation passes; all ten relations and all size
  gates pass. Summary: `reports/release-v1/graph-summary.json`.
- Graph counts: 52,415 nodes; 261,755 edges; 124,619 factual R1–R4 edges;
  36,680 resolved researchers. Topic labels remain an unvalidated phrase baseline.
- Tests: 345 passed, 1 skipped (WORK-028).
- Phase 4 is not run: Docker Desktop is not integrated with this WSL 2 distro;
  `neo4j-five-year` is defined but not started and port 7689 is not listening.

## Phase checklist

- [x] P0 Housekeeping
- [x] P1 Tooling fixes
- [x] P2 OpenAlex acquisition
- [x] P3 Graph v1: all ten relations, structural validation, summary and size gates
- [ ] P4 Neo4j load, integrity and idempotent replay (**blocked by WSL Docker integration**)
- [ ] P5 Embedding topics, frozen test set, graph v2 and label sheet
- [ ] P6 Network analysis, figures and findings
- [ ] P7 Graph freeze and review sheets
- [ ] Human edge/topic review returned
- [ ] P8 Scoring, full report draft and README
- [ ] P9 PDF, release and submission

## Next action

Enable Docker Desktop WSL integration, start only `neo4j-five-year`, then complete the
Phase 4 load, integrity and replay checks.

## Waiting on the user

- Enable Docker Desktop WSL integration so the isolated release DB can start.
- Fill in `docs/team.md`, choose lecturer repo access and confirm course AI-use disclosure.
- Reserve edge/topic review time for both reviewers.
