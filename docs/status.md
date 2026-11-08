# Current project status

Updated: **2026-11-09 00:52 +07:00**. Deadline: **11 November 2026**.
Plan: [D040 release plan](release-plan.md). Latest entry: [WORK-2026-11-09-001](work-log/2026-11-09-001-pre-audit-review.md).

## State

- Independent technical review of the pre-audit corrections found no blocking defect. Human review is the next action.
- Active graph: `release-9d4a6fb20f63`, at `data/processed/release-graph-v3/graph.json`.
- Active package: [release-v2/freeze-v3.json](../reports/release-v2/freeze-v3.json). Earlier graph/freeze/packet/figure versions remain preserved.
- Fresh structural/size validation passes; canonical old/new checks confirm preservation of core facts, affiliation observations, predictions, evidence, support and weights. Taxonomy matches the frozen config.
- Fresh read-only Neo4j checks on port 7689 reconcile inventory/version, all 20 taxonomy records and six zero-row integrity queries. WORK-037 records the earlier load and idempotent replay; this review did not reload.
- All six PNG/CSV pairs and captions reproduce byte-for-byte; all documented analysis differences reconcile. Full analysis was not rerun in this review.
- Active freeze references match actual and committed bytes; historical protected files match the prior review baseline. Normal A/B packets are blank and ready. Optional single-reviewer packets remain unselected; partial scoring requires opt-in.
- Fresh suite: 384 passed, one existing empty-parameterization skip. Blank topic exports are rejected. Independent semantic accuracy and topic quality remain unmeasured.
- WORK-037 verified remote main at `951b9c5`, with no tags. Remote state was not refreshed here. No push or publication occurred.

## Phase checklist

- [x] P0 Housekeeping
- [x] P1 Tooling fixes
- [x] P2 OpenAlex acquisition
- [x] P3 Graph v1 and structural validation
- [x] P4 Neo4j v1 load, inventory, integrity and replay
- [x] P5 Frozen embedding classifier, corrected graph and Neo4j replay
- [x] P6 Fresh corrected-graph analysis, figures and findings
- [x] P7 Replacement freeze and consistent review packets
- [x] Resolve pre-audit taxonomy, fallback-scoring and reviewer-export issues
- [x] Independently review the corrected pre-audit package
- [ ] Human edge/topic reviews returned and scored
- [ ] P8 Final report and README complete after scoring
- [ ] P9 PDF and submission packaging

## Next action and human input

Follow [the reviewer handoff](reviewer-handoff.md): map actual people to A/B, distribute their packets, preserve originals, return separate completed CSV exports, and jointly adjudicate edge conflicts. The normal design remains selected.

Real names, student IDs, actual contributions, course disclosure and lecturer access come from the user. No Site update, release tag, push or submission was performed.
