# Current project status

Updated: **2026-11-08 23:47 +07:00**. Deadline: **11 November 2026**.
Plan: [D040 release plan](release-plan.md). Latest entry: [WORK-2026-11-08-036](work-log/2026-11-08-036-progress-review.md).

## State

- Release scope remains the AAAI/IJCAI 2021–2025 main-track subset of roster v10.
- Phases 0–7 have execution checkpoints. Phase 8 is partial; this review found a pre-audit taxonomy inconsistency that must be resolved first.
- Frozen graph v2: `release-5d830ffcbdf4`, SHA-256 `b79e456b22488ca8f753fb0884afd5c6a89afeeeaffec07d89ce83b2c5c141fb`.
- Fresh validation: 52,415 nodes, 275,438 edges, 36,680 resolved researchers, 124,619 factual R1–R4 edges, ten nonempty predicates; structural size gates pass.
- Fresh read-only Neo4j inventory matches v2; all six integrity queries return zero rows. `neo4j-five-year` is healthy on 7476/7689. Earlier load/replay receipts remain historical.
- Graph, works, baseline, configs, test, analysis and review-packet hashes match their recorded references and tracked Git blobs where applicable.
- **Taxonomy finding:** all v2 Topic nodes retain `taxonomy-v0.1`; generative-modeling and graph-ML definitions differ from the frozen classifier taxonomy. Four sampled topic edges show the old definitions. Preserve the freeze; a graph correction needs a new version and audit.
- **Scoring gap:** the edge scorer requires two reviewers and complete assignments; D040's one-reviewer and incomplete-audit fallbacks are not implemented.
- Analysis, six figure/table pairs and candidate findings exist. Report sections 1–11 are drafted; human edge/topic scores and the final PDF are absent. Semantic accuracy remains unmeasured.
- Report fixes remain: author-position totals need the matched-work denominator; the statement that main has not been pushed is stale. Remote main matched the review base; no release tags were found.
- Fresh environment sync and test suite pass: 363 passed, one existing empty-parameterization skip. This review changed handoff records only.

## Phase checklist

- [x] P0 Housekeeping
- [x] P1 Tooling fixes
- [x] P2 OpenAlex acquisition
- [x] P3 Graph v1 and structural validation
- [x] P4 Neo4j v1 load, inventory, integrity and replay
- [x] P5 Frozen embedding classifier, graph v2 and Neo4j replay (topic metadata correction outstanding)
- [x] P6 Analysis, figures and findings
- [x] P7 Graph freeze and review packets (review-context correction outstanding)
- [ ] Resolve pre-audit taxonomy consistency finding
- [ ] Human edge/topic reviews returned and scored
- [ ] P8 Final report and README complete after scoring
- [ ] P9 PDF and submission packaging

## Next action

Resolve the taxonomy finding under D040's new-version policy before independent review. Then collect and score completed reviewer exports, finish the report/team record, verify a ≥10-page PDF and prepare the release.

## Waiting on human input

- Completed review exports and required overlap adjudications after review context is consistent.
- Real names, student IDs, actual contributions and the course AI-use disclosure.
- Lecturer repository access and final submission/release actions.
