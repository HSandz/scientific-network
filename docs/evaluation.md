# Quality evaluation

## Active agent-led protocol — 9 November amendment

The user has delegated feasible audit/scoring/report work to agents. Human
annotation is optional. Follow [agent-audit-workflow.md](agent-audit-workflow.md)
and [the frozen protocol contract](../configs/evaluation-agent-release-v1.yaml).
The next session must first implement evaluator provenance, receipt/ledger binding
and honest result metadata; those capabilities and real scores do not exist yet.

Keep the existing graph/content freeze intact. Use new agent quality/packet/result
versions under the paths declared in the contract, preserving the selected sample
recipe. Default A/B now denote isolated evaluator contexts; a documented
single-agent variant is permitted when isolated contexts are unavailable.
Freeze blind topic labels before exposing edge predictions. A considered empty
topic set and an unreviewable paper must be distinguished.

Report AI-assessed edge precision and topic agreement with AI-assigned reference
labels. Keep numeric thresholds unchanged, but qualify their outcomes as
AI-assessed; verified course accuracy is not established by these judgments.
Disclose evaluator models/runs, source reuse, evidence depth, missingness and
correlated judge errors. Wilson intervals cover sampling uncertainty conditional
on judgments, not evaluator accuracy. Do not claim human or independent gold
validation. The earlier human protocol below is retained for optional use/history;
its requirement to return human annotations no longer blocks execution.

## Preserved human protocol and implemented scoring tools

The [D040 release plan](release-plan.md) governs this release. The active package
is [release-v2/freeze-v3.json](../reports/release-v2/freeze-v3.json), for the corrected
graph at `data/processed/release-graph-v3/graph.json`. The old freeze, packets and
reports remain historical; do not send the old edge sheets to reviewers.

Use [the reviewer handoff](reviewer-handoff.md) for the exact A/B packet links,
completed-export paths, supported adjudication preparation, and complete scoring
commands with explicit graph, summary, allocation and freeze paths. Topic master,
allocation and prediction-blind A/B sheets are intentionally reused by exact-byte
reference; the replacement freeze binds them. No human reviews are completed and
independent semantic accuracy and topic quality remain unmeasured.

## Current audit contracts

`configs/quality-release-v1.yaml` selects the normal `split_with_overlap` design.
The optional `quality-single-reviewer-release-v1.yaml` uses `single_reviewer` with
no overlap and unavailable agreement. Its packets and freeze are separate and
**not selected**. `double_review` remains the historical default when no design
is specified. No readiness receipt is required under D040; an explicitly supplied
historical receipt is still verified. Size gates are measured and reported.

`score-edge-audit --reviews A.csv B.csv` parses exports separately and validates
frozen graph/config/frame, assignments, timestamps, categories and verdicts.
`prepare-edge-adjudications` copies returned conflicts into a blank joint form;
the scorer checks all final frame/assignment bindings and requires adjudication
of disagreements. Unverifiable is incorrect. Global and per-type samples stay
separate. Report both course (>90% point precision) and project (≥95% point with
Wilson lower bound >90%) thresholds.

Complete frozen assignments are required by default. `--allow-partial` explicitly
scores only completed returned rows and reports missingness, actual denominators,
overlap completion and relation coverage. Malformed/blank/duplicate/foreign rows
remain fatal. Partial results warn about nonresponse bias; they do not certify
the planned complete audit. See the handoff for fallback commands and exit codes.

Topic scoring keeps one total weight per paper and independent overlap labels.
The aliases `--embedding-graph` and `--embedding-summary` support replacement
releases; historical `--graph-v2`/`--graph-v2-summary` options remain accepted.
This test cannot be used for further classifier tuning.

## Historical and optional evaluation designs

The remaining sections preserve earlier proposals and optional component tooling.
Their historical readiness requirements, sampling sizes and source-closure gates
do not govern the D040 release. Synthetic examples are not measured project results.

## Historical pre-D040 audit proposal

1. After the graph is built, freeze its version, complete edge-frame hash and
   configured random seed. `freeze-audit-sample` refuses non-synthetic graphs
   without a matching post-build readiness receipt, hashes that receipt into the
   packet, and checks the existing size gates before writing a new review form. It
   never overwrites an existing form.
2. Select **600 unique edges uniformly without replacement** for the global
   estimate, using deterministic SHA-256 rank ordering seeded by the config. A
   smaller diagnostic graph cannot supply the full final audit. Separately select
   **100 per predicate**, or census the entire smaller type. The frozen CSV keeps
   global and per-type flags so overlapping reviews can be reused without pooling
   per-type supplements into the global estimate.
3. Each sampled edge needs one review from each of two distinct reviewer IDs.
   Reviews record endpoint, predicate, paper/time and evidence checks. Disagreements
   need one reasoned adjudication row; agreed cases must not have one. Unverifiable
   edges count as incorrect. Timestamps must include a timezone.
4. Require global point precision ≥95% and a **two-sided 95% Wilson lower bound
   strictly above 90%**. Publish per-type estimates/intervals and macro precision.
   A small-type census reports exact correctness, not sampling uncertainty.

Example commands after an authorized final graph exists:

```bash
research-network freeze-audit-sample --input data/processed/final-graph.json \
  --readiness reports/final/post-build-audit-readiness.json \
  --config configs/quality.yaml --output data/annotations/final-edge-audit-v1.csv
research-network score-edge-audit --input data/processed/final-graph.json \
  --reviews data/annotations/final-edge-audit-v1.csv \
  --readiness reports/final/post-build-audit-readiness.json \
  --config configs/quality.yaml --output reports/final/edge-audit-v1.json
```

The sample command emits one blank row per sampled edge. Duplicate each row for
both reviewers and fill their separate decisions; save disagreements and their
adjudication in the separate CSV template. When disagreements exist, also pass
the completed adjudication CSV with `--adjudications`. The scorer binds both files
to the exact graph, quality config, readiness receipt, frame, method version and
expected deterministic sample. It records reviewer IDs as
input-declared, because software cannot establish reviewer identity or
independence. A synthetic graph produces `synthetic_protocol_only` and can never
make a release claim. The current synthetic fixture demonstrates only the packet
contract; no real final sample has been drawn.

## Component-label evaluation

`research-network evaluate` scores component predictions against a frozen frame
and two input-declared reviewer packets. The frame, predictions, and gold labels
are separate artifacts. Predictions bind to the exact frame SHA-256, the gold
packet binds to both frame and prediction SHA-256, and the prediction packet also
binds the quality-config SHA-256 and method version. The
frame declares inverse-inclusion sampling weights and strata. Resolution units
are explicit researcher or organization pairs, affiliation units contain a
complete organization set for one author–paper position, topic units contain a
complete leaf-label set for one paper, and citation units identify candidates in
the frozen reference frame. Topic labels must belong to its declared frozen
taxonomy. Outputs report unweighted and sampling-weighted precision, recall and
F1, per-stratum counts, topic per-label and macro scores, pair-type error counts,
reviewer exact agreement, abstentions, and the configured precision checks.
Topic macro scores average labels with gold or predicted support; undefined
per-label metrics are shown as null and treated as zero only in the macro summary.

The gold packet requires exactly two distinct reviewer IDs and evidence
locators for every frozen unit. Agreement rows must not have adjudications;
disagreements need one reasoned adjudication from a third ID. Timestamps declare
that predictions were frozen before review began. These checks validate packet
shape and joins only: the program cannot authenticate reviewers, establish their
independence, verify evidence locators, or prove that predictions were blinded.
Those statuses remain explicitly input-declared.

Coverage is computed against the supplied core denominator: eligible papers for
abstract availability and supported-topic coverage, and unique official
author–paper positions for accepted affiliation coverage. A complete release
evaluation must supply the entire eligible release-core coverage frame; a
diagnostic sample is labeled with its narrower population scope. Citation
extraction and core-target metrics are bounded by the provided candidate
reference frame and do not prove that the frame contains every source reference.

Example invocation for a future frozen evaluation packet:

```bash
research-network evaluate \
  --frame data/annotations/component-frame-v1.json \
  --predictions data/annotations/component-predictions-v1.json \
  --gold data/annotations/component-gold-v1.json \
  --config configs/quality-component-eval-v1.yaml \
  --output reports/evaluation/component-eval-v1.json
```

Synthetic frames must say `synthetic_protocol_only` and always produce
`release_status: ineligible_synthetic`; their scores exercise formulas only.
Non-synthetic scoring additionally requires a reserved test frame, a frozen
quality config, and the complete eligible release-core coverage denominator.
The scorer binds to the frame's declared test role but does not independently
verify membership or cross-year leakage against the split manifest; that check
remains a separate P03/P07 prerequisite.
The repository's current `configs/quality.yaml` is still proposed, and no
complete independent component labels exist, so no real component evaluation
has been run. Passing this command would not pass the separate final edge audit,
verify reviewer independence, or certify a release. `score-edge-audit` remains a
separate post-build workflow.

For example, 570/600 gives 95% precision and a lower bound around 92.95%. This is
an arithmetic example, not a result. `research-network audit-precision --correct
570 --total 600` computes only that interval; it does not establish independent
sampling, annotation, semantic correctness or a passing release.

Per-type intervals are individual, not a simultaneous guarantee for ten types.
Predefine multiplicity adjustments/sample sizes if such a guarantee is required.
Targeted inspection of hubs/common names/large teams is useful error discovery,
not an estimate of graph-wide precision. Shared base evidence also means derived
edges are not independent extraction tasks.

## Recall, NLP and coverage

Fully annotate held-out papers for entities, aligned affiliations, complete leaf
topics and in-core reference targets. Report precision `TP/(TP+FP)`, recall
`TP/(TP+FN)`, F1, label support, agreement and false-merge/split categories. Separate
header extraction from author–organization linking and automated pipeline metrics
from manually corrected release quality.

Report venue–year-specific and source-family metrics across the five-year roster.
Preserve all 925 expanded test assignments and their cross-year versions. Set a
prospective feasible allocation and population weights before future enrichment.
Report yearly and cumulative windows separately; no automatic quota multiplication.
The historical NeurIPS/ICML 60/60 test sample is not representative of the expanded
population. Preserve its IDs and freeze supplemental cross-venue leakage groups
and a feasible prospective annotation allocation before collection/tuning. Equal
per-venue quotas require venue sampling weights for corpus-wide TP/FP/FN totals;
report tiny-stratum uncertainty and rare-topic diagnostics separately. See
[the scope policy](conference-scope.md). The independent 600-edge global audit
still samples uniformly from the complete frozen release edge frame; do not
substitute the legacy pilot or pool targeted supplemental inspections into it.

Publish abstract availability, work-match rate, affiliation-triple coverage,
topic paper coverage, abstention, unresolved identities and reference coverage
with denominators by venue, edition year, team size and sector. Citation
comparisons must disclose snapshot time and unequal time to accrue citations;
future metadata cannot be treated as information available in an earlier year. Initial pilot coverage is recorded in
[the pilot report](../reports/pilot-v1.md); independent semantic scores remain pending.

## Correction and robustness

Keep the frozen audit unchanged. Record issues/reviewer decisions, correct the
underlying rule, regenerate dependent relations, rerun integrity checks, version
the graph and draw a fresh blind sample for a new independent release claim.

Before final conclusions, freeze a stricter evidence filter and rebuild derivations
from the filtered base support. Compare raw/fractional weights, keyword/model
topics, resolved/name-only diagnostic identities, and core/context citations.
Record top-20 overlap, rank correlation on common nodes, component share and
case-study changes. Use three community seeds and at least two resolutions.

## What the implementation verifies

Implemented: JSON shape, deterministic IDs, endpoint/provenance references,
orientation, core invariants, derived inventory/support/weight recomputation,
transactional Neo4j count reconciliation, Wilson math, deterministic audit sample
preparation, frame/sample verification, two-review completeness and disagreement
adjudication. Live pilot import and replay checks are recorded separately in the
work log. The evaluator validates supplied review structure but cannot verify
reviewer identity or independence.

Pending: real independent labels/review, semantic correctness, component
precision/recall/F1, release coverage gates, source-backed findings and
certification. Synthetic protocol checks are not evidence of release accuracy.
