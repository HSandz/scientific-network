# Current project status

Updated: **2026-11-08 14:41 +07:00**. Deadline: **11 November 2026**.
Plan: [D040 release plan](release-plan.md). Latest entry: [WORK-2026-11-08-035](work-log/2026-11-08-035-topic-review-allocation.md).

## State

- The release covers AAAI and IJCAI main-track papers, 2021–2025, from roster v10.
- Phases 0–7 are complete. Phase 8 is the first incomplete phase; scoring requires actual human reviews.
- Frozen graph v2: `release-5d830ffcbdf4`, SHA-256 `b79e456b22488ca8f753fb0884afd5c6a89afeeeaffec07d89ce83b2c5c141fb`.
- Measured inventory: 52,415 nodes, 275,438 edges, 36,680 resolved researchers, 124,619 unique factual R1–R4 edges and 10/10 nonempty predicates. All configured size gates pass.
- Neo4j Community 5.26 service `neo4j-five-year` is healthy on ports 7476/7689. v1/v2 inventory, integrity and replay checks passed; pilot and extended databases remain preserved.
- After Docker was started, a fresh read-only v2 inventory matched 52,415 nodes and 275,438 edges; `02_integrity.cypher` returned no rows.
- Topic coverage is 11,575/13,617 (85.00%). Semantic accuracy, edge precision and topic evaluation are not measured. Release remains uncertified.
- Phase 6 analysis, six figure/table pairs and source-linked findings are committed. Phase 7 graph, config and review packet hashes are recorded in `reports/release-v1/freeze.json`.
- Topic review allocation is resolved: reviewer A and B receive 30 papers each, with 10 shared; the union covers all 50 frozen papers. Each reviewer receives 12 AAAI and 18 IJCAI papers. Reviewer packets are prediction-blind.
- Frozen CSV review sheets now use LF line endings, and allocation/freeze hashes match both the worktree bytes and staged Git blobs.
- Phase 8 report sections 1–11 are drafted; the topic scorer now supports the 30/30/10 design with equal paper weights and overlap agreement. Human scores, real team details, course AI-use disclosure and final PDF remain outstanding. The README now reports current local release results.

## Phase checklist

- [x] P0 Housekeeping
- [x] P1 Tooling fixes
- [x] P2 OpenAlex acquisition
- [x] P3 Graph v1 and structural validation
- [x] P4 Neo4j v1 load, inventory, integrity and idempotent replay
- [x] P5 Frozen embedding classifier, graph v2 and Neo4j replay
- [x] P6 Analysis, figures and findings
- [x] P7 Graph freeze and review packets
- [ ] Human edge/topic reviews returned and scored
- [ ] P8 Final report and README complete after scoring
- [ ] P9 PDF and submission packaging

## Next action

Reviewers complete the A/B edge assignments and topic CSV packets, then return the exports. Score both evaluations, finish the report, fill `docs/team.md` with real identities/contributions and course disclosure, verify a 10-page PDF, and complete Phase 9.

## Waiting on human input

- Completed edge-review export(s), including required overlap adjudications, and reviewer A/B topic-label CSVs.
- Real team names, student IDs, actual contributions and the course AI-use disclosure.
- Lecturer repository-access choice before final submission.
