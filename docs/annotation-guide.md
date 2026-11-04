# Annotation guide (pilot draft)

This guide must be tested on the pilot and frozen before held-out annotation.
Record graph/taxonomy versions, paper ID, source locator, annotator ID and decision
reason. Both teammates annotate independently before adjudication.

## Units and rules

- **Authorship/identity:** preserve official byline order. Verify identifiers and
  compatible paper evidence. Same normalized name alone is insufficient; keep
  common-name negatives and name-order/initial positives. Two distinct byline
  positions block a merge absent a documented correction.
- **Organization:** keep the printed string and approved canonical match. Review
  aliases, hierarchy, campuses and corporate research entities consistently. No
  affiliation or sector is unknown, not evidence of independence or academia.
- **Affiliation:** annotate `(researcher, paper, organization)` only with explicit
  authorship-level metadata or checked PDF/TEI markers. One author may have multiple
  affiliations. Never create the product of every author and institution on a paper.
- **Topics:** select 1–3 substantive leaf topics from `configs/topics.yaml`, or
  abstain. Copy supporting title/abstract spans and offsets. Label the contribution,
  not every related-work term. An ambiguous token alone does not establish a label.
- **References:** mark explicit in-core references and verified work targets;
  deduplicate versions and repeated mentions. Unmatched targets remain unresolved.
- **Edges:** endpoints, predicate, paper/time scope and evidence must all pass.
  Count unverifiable support as incorrect for the release audit.

Examples: graph-based recommendation can have both graph-ML and retrieval labels;
causal masking alone is not causal inference; an ensemble alone is not a multi-agent
system. Add confusing positive/negative examples for every leaf during the pilot.

## Dataset separation

The legacy NeurIPS/ICML split has 120 reserved test papers (60 per venue) and 60
development papers (30 per venue). Preserve those IDs unchanged. For the expanded
2021–2025 plan, preserve all existing expanded assignments (925 test / 470
development / 13,514 pool) and freeze future venue–year-stratified groups only
after authorization. Cross-year and cross-venue versions share leakage protection;
new versions of old tests remain held out, and exposed papers cannot become fresh
tests. Finalize annotation hours and sampling weights prospectively; 170
venue–year candidates are not a feasible sample-size promise. New training data
stays separate. No new split or annotation is created by this planning task. See [scope and staged pilot](conference-scope.md).
Rare-topic/difficult-layout diagnostics stay separate from probability-sample estimates.
The current taxonomy is a draft and needs development examples for new fields;
never use test errors to add labels or tune thresholds.

## Review process

Keep original independent annotations, agreement statistics, disagreements,
adjudicated labels, source references and decision time. Record false merges/splits,
wrong organizations, wrong affiliation alignments, topics, versions and targets.
Do not overwrite the original labels when correcting a pipeline. A revised method
requires a fresh untouched test before another independent final claim.

CSV headers in `docs/templates/` are starting contracts, not populated gold sets.
Use long-form rows for multiple labels/affiliations; define explicit negative and
abstention records before starting annotation.
