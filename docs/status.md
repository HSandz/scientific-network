# Current project status

Updated: **2026-11-08 12:50 +07:00**. Deadline: **11 November 2026**.
Plan: [release plan](release-plan.md) under [D040](decisions.md#d040--release-reset-for-the-11-november-submission-2026-11-08).
Latest entry: [WORK-2026-11-08-030](work-log/2026-11-08-030-release-phase-5-embedding-development.md).

## State

- Scope and OpenAlex acquisition are complete under D040; 11 works remain in review.
- Phase 3 graph v1 is preserved. Phase 5 graph v2 `release-5d830ffcbdf4` was built
  from its frozen CPU embedding classifier and independently validates; its summary is
  `reports/release-v1/graph-v2-summary.json`.
- Graph v2: 52,415 nodes; 275,438 edges; 124,619 factual R1–R4 edges; all ten relations.
  Topic labels cover 11,575/13,617 papers (85.00%); semantic accuracy is not measured.
- A prediction-blind 50-paper topic sheet with 16 definitions is ready under
  `reports/release-v1/audit/`; human labels remain pending.
- Phase 4 remains blocked: Docker CLI is unavailable in this WSL 2 distro, and port
  7689 is not listening. No Neo4j load, integrity query or replay has run.
- Tests: 354 passed, 1 skipped (WORK-030). The CPU model build took 8m52s and peaked at
  4.02 GiB RSS.

## Phase checklist

- [x] P0 Housekeeping
- [x] P1 Tooling fixes
- [x] P2 OpenAlex acquisition
- [x] P3 Graph v1: all ten relations, structural validation, summary and size gates
- [ ] P4 Neo4j load, integrity and idempotent replay (**blocked by WSL Docker integration**)
- [ ] P5 Embedding classifier frozen; graph v2 validated; Neo4j load and replay pending
- [ ] P6 Network analysis, figures and findings
- [ ] P7 Graph freeze and review sheets
- [ ] Human edge/topic review returned
- [ ] P8 Scoring, full report draft and README
- [ ] P9 PDF, release and submission

## Next action

Enable Docker Desktop WSL integration, start only `neo4j-five-year`, then load graph v2,
run inventory/integrity queries and verify idempotent re-import. After P4, close P5 and
continue with P6.

## Waiting on the user

- Enable Docker Desktop WSL integration so the isolated release DB can start.
- Fill in `docs/team.md`, choose lecturer repo access and confirm course AI-use disclosure.
- Reserve edge/topic review time for both reviewers.
