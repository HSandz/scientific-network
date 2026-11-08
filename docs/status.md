# Current project status

Updated: **2026-11-09 00:27 +07:00**. Deadline: **11 November 2026**.
Plan: [D040 release plan](release-plan.md). Latest entry: [WORK-2026-11-08-037](work-log/2026-11-08-037-pre-audit-corrections.md).

## State

- Pre-audit technical corrections are complete. Independent human review is the next action.
- Active graph: `release-9d4a6fb20f63`, at `data/processed/release-graph-v3/graph.json`.
- Active package: [release-v2/freeze-v3.json](../reports/release-v2/freeze-v3.json). It supersedes the old graph/freeze and the first corrective figure package; all remain preserved.
- Taxonomy content/provenance now matches the frozen classifier config. Core facts, affiliation observations, predictions, excerpts, scores, derived support and weights are preserved by canonical equality checks.
- Corrected graph validation passes. Isolated Neo4j load, inventory, taxonomy checks, six zero-row integrity queries and idempotent replay pass on port 7689.
- Analysis and figures were freshly computed; exact fractional sums fix unstable topic ties. Unstored community topics are masked in the final figures.
- Normal A/B review packets are ready. Single-reviewer packets are optional and not selected; incomplete scoring requires explicit opt-in. No real reviews or quality scores exist.
- Final suite: 384 passed, one existing empty-parameterization skip. Real HTML packets and synthetic browser downloads were checked; blank real packets cannot produce results.
- Remote main was verified at `951b9c5`, with no tags. This session's corrections remain local; no push or publication occurred.

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
- [ ] Human edge/topic reviews returned and scored
- [ ] P8 Final report and README complete after scoring
- [ ] P9 PDF and submission packaging

## Next action and human input

Follow [the reviewer handoff](reviewer-handoff.md): map actual people to A/B, distribute their packets, preserve originals, return separate completed CSV exports, and jointly adjudicate edge conflicts. The normal design remains selected.

Real names, student IDs, actual contributions, course disclosure and lecturer access come from the user. Semantic accuracy and topic quality remain unmeasured. No Site update, release tag, push or submission is authorized by this handoff.
