# Current project status

Updated: **2026-11-09 12:36 +07:00**. Deadline: **11 November 2026**.
Plan: [D040 release plan](release-plan.md). Latest entry: [WORK-2026-11-09-004](work-log/2026-11-09-004-agent-source-review.md).

## State

- The user selected agent-led audit, scoring, report and local packaging. Human annotations are optional and no longer a prerequisite.
- Active graph: `release-9d4a6fb20f63`, at `data/processed/release-graph-v3/graph.json`.
- Graph/content freeze: [release-v2/freeze-v3.json](../reports/release-v2/freeze-v3.json). All existing graph, classifier, config, sample, packet and historical receipt bytes stay unchanged.
- Active execution: [agent workflow](agent-audit-workflow.md), [protocol contract](../configs/evaluation-agent-release-v1.yaml) and [fresh-session prompt](prompts/agent-release-completion.md).
- `score-agent-review` now validates evaluator/source ledgers, freeze/receipt hashes, canonical assignments and review order; honest AI metadata is applied before output. Default isolated A/B selected; no fallback needed.
- Default A/B are isolated evaluator contexts; freeze blind topic answers before edge review. If contexts are unavailable, select the single-agent variant before judging. Do not impersonate two people.
- Full source-backed A/B reviews and adjudication are complete. AI-assessed edge precision **176/200 = 88.00%**, Wilson 95% **82.77%–91.80%**; course point/project gates **fail**. No missing reviews.
- Topic test: embedding micro F1 **.4667**, phrase **.2301**; coverage 90%/26%. Blind overlap agreement 10/10. Edge agreement 39/50. These are AI reference judgments, not independent gold.
- Fresh suite: **419 passed/1 existing skip**; schema CLI, structural/size validation, 66 frozen hashes and read-only Neo4j inventory/six integrity queries pass. Graph remains frozen; observed-ORCID array handling defect is documented for a separate future version.
- Human validation not performed; evaluator independence and verified course accuracy not established. Exact model/provider IDs unknown. Results/limitations: `reports/release-v3/`.
- No push, tag, Site publication, invitation or submission was performed or authorized by this change.

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
- [x] Adopt user-authorized agent evaluation and prepare a fresh-session prompt
- [x] Implement and test evaluator provenance/bindings and AI result metadata
- [x] Complete and score source-backed agent edge/topic reviews
- [ ] P8 Final report and README complete after scoring
- [ ] P9 PDF and submission packaging

## Next action and human input

Finish the measured report/README, then render/check the local PDF and prepare the submission bundle. Failed numeric gates remain reported; no frozen graph correction.

Only unavailable real team/private facts, demonstrated tool/access needs and separately authorized external delivery actions require human input. Continue independent work while they remain pending.
