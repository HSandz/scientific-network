# Independent quality evaluation

> **For the 11 Nov 2026 submission** the audit design is in the
> [release plan](release-plan.md#24-accuracy-audit-configsquality-release-v1yaml)
> (D040). The protocol below is the original proposal; its definitions of edge
> correctness still apply.

The current planned population is 2021–2025 (D018). All measured research results
remain diagnostics; the P09 edge-audit packet tools are protocol tooling and do
not produce an independent quality result without real reviewer inputs. Future
component estimates must distinguish venue–year strata, coverage and version
leakage. [Temporal evaluation design](five-year-scope.md).

The assignment requires accuracy above 90%. The plan proposes **end-to-end edge
precision** as the primary interpretation; confirm it with the lecturer. A passing
edge has correct identities/endpoints, predicate, paper/time scope and verifiable
evidence. Computing accuracy over every possible node pair would reward trivial
nonedges and is not the proposed evaluation.

## Release audit tooling (D040, current behaviour)

`configs/quality-release-v1.yaml` sets `audit.review_design: split_with_overlap`:
200 uniform global edges, 10 per relation, and 50 global-sample edges reviewed by
both reviewers (A and B). A readiness receipt is no longer needed (`--readiness` is
verified only when supplied), and the size gates are computed and recorded as passed
or failed in the output of `freeze-audit-sample`, `score-edge-audit` and `analyze`.

```bash
research-network freeze-audit-sample --input data/processed/release-graph-v2/graph.json \
  --config configs/quality-release-v1.yaml --output reports/release-v1/audit/edge-review-sheet.csv
```

This writes the CSV form (one row per edge per assigned reviewer, with the reviewer
context columns) and `edge-review-sheet.html` next to it. Each reviewer opens the HTML
sheet (it needs no server or network), chooses A or B, records correct, incorrect or
unverifiable for each assigned edge with an error category and reason when not
correct, and exports a CSV. Concatenate the two exports and pass them to
`score-edge-audit --reviews`. A disagreement on an overlap edge needs one
adjudication row (an optional `error_category` column is read). The result reports
k/n, precision, the Wilson 95% interval, per-relation results, agreement percent and
Cohen's kappa on the overlap, error categories, and both the course (point estimate
above 90%) and project (at least 95% with a lower bound above 90%) gates. Design
rationale: [release plan section 2.4](release-plan.md#24-accuracy-audit-configsquality-release-v1yaml).
The `double_review` design below is still the default when `review_design` is absent.

## Frozen release audit

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
