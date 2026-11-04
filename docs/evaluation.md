# Independent quality evaluation

The current planned population is 2021–2025 (D018). All measured results remain
2023 diagnostics. Future component estimates must distinguish venue–year strata,
coverage and version leakage; no new split, annotation or pipeline work is
authorized in this planning task. [Temporal evaluation design](five-year-scope.md).

The assignment requires accuracy above 90%. The plan proposes **end-to-end edge
precision** as the primary interpretation; confirm it with the lecturer. A passing
edge has correct identities/endpoints, predicate, paper/time scope and verifiable
evidence. Computing accuracy over every possible node pair would reward trivial
nonedges and is not the proposed evaluation.

## Frozen release audit

1. Freeze graph version, complete edge sampling frame, hashes and random seed.
2. Sample **600 unique edges uniformly without replacement** for the global
   estimate. A smaller diagnostic graph cannot supply the full final audit.
3. Separately sample **100 per predicate**, or inspect the entire smaller type.
   Preserve sampling flags and reuse overlapping reviews. Never pool supplemental
   per-type samples into an unweighted global estimate.
4. Both teammates inspect evidence independently, then adjudicate disagreements.
   Unverifiable edges fail. Keep review records and exact correct/total counts.
5. Require global point precision ≥95% and a **two-sided 95% Wilson lower bound
   strictly above 90%**. Publish per-type estimates/intervals and macro precision.
   A small-type census reports exact correctness, not sampling uncertainty.

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
transactional Neo4j count reconciliation, and Wilson math. Live pilot import and
replay checks are recorded separately in the work log.
Pending: independent labels/review, semantic correctness, component precision,
recall and F1, release coverage gates, source-backed findings and certification.
