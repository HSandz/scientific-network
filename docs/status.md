# Current project status

Updated: **2026-11-08 12:00 +07:00**. Deadline: **11 November 2026**.
Plan: [release plan](release-plan.md) under [D040](decisions.md#d040--release-reset-for-the-11-november-submission-2026-11-08).
Latest entry: [WORK-2026-11-08-029](work-log/2026-11-08-029-release-phase-5-topic-test-freeze.md).

## State

- Scope and OpenAlex acquisition are complete under D040; 11 works remain in review.
- Phase 3 graph v1 rebuilt with method `release-openalex-graph-v1.1`; version
  `release-4c1253e05f2c`. Fresh validation passes; all ten relations and all size
  gates pass. Summary: `reports/release-v1/graph-summary.json`.
- Graph counts: 52,415 nodes; 261,755 edges; 124,619 factual R1–R4 edges;
  36,680 resolved researchers. Phrase topics remain unvalidated and under-covered.
- Phase 5 prerequisite frozen: 30 IJCAI + 20 AAAI topic-test IDs, seed `20261108`;
  development taxonomy copy created and remains unfrozen. No test content was inspected.
- Tests: 347 passed, 1 skipped (WORK-029).
- Phase 4 is not run: Docker Desktop is not integrated with this WSL 2 distro;
  `neo4j-five-year` is defined but not started and port 7689 is not listening.

## Phase checklist

- [x] P0 Housekeeping
- [x] P1 Tooling fixes
- [x] P2 OpenAlex acquisition
- [x] P3 Graph v1: all ten relations, structural validation, summary and size gates
- [ ] P4 Neo4j load, integrity and idempotent replay (**blocked by WSL Docker integration**)
- [ ] P5 Test set frozen; embedding model, graph v2 and label sheet pending
- [ ] P6 Network analysis, figures and findings
- [ ] P7 Graph freeze and review sheets
- [ ] Human edge/topic review returned
- [ ] P8 Scoring, full report draft and README
- [ ] P9 PDF, release and submission

## Next action

Continue P5 model work on development papers only while waiting for Docker integration;
then complete P4 load, integrity and replay before closing P5.

## Waiting on the user

- Enable Docker Desktop WSL integration so the isolated release DB can start.
- Fill in `docs/team.md`, choose lecturer repo access and confirm course AI-use disclosure.
- Reserve edge/topic review time for both reviewers.
