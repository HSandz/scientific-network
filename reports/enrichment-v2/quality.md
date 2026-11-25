# Enrichment v2 quality (AI-assessed)

Graph `enriched-827be09bc987` (SHA-256 `02e5a288daf5dffe...`), built from the cached v1 inputs on top of `enriched-c0f7d1dd4abd`; audit seed 2026112502. AI-assessed by agent evaluators; not human annotation and not independently validated gold labels. Wilson 95% intervals exclude evaluator error. Development labels are from the building session and are not an audit.

Evaluators: A: claude-opus-5-5 (fresh subagent, requested 'opus'); B: codex exec, model gpt-6.2-sol via provider 9router as logged in the session file; C: claude-opus-5-5 (fresh adjudicator subagent). Isolation: by directory and instruction: each evaluator worked in its own directory holding only guideline.md and its packet; no separate containers. The building session did not judge.

Each cell: estimate [Wilson 95% interval] (k correct, n decided). Unclear verdicts are excluded from the primary figure and counted as incorrect in the sensitivity.

## Rule decisions (criteria declared before measuring; D042 amendment 2026-11-25)

| Rule | Declared criterion | Measured on development material | Decision |
|---|---|---|---|
| PART_OF v2 | kept precision >= 0.85 and >= 70% of correct edges kept | kept precision 0.778 [0.619, 0.883] (k=28, n=36); correct edges kept 0.966 | **not adopted** (v1 PART_OF unchanged) |
| MEMBER_OF | >= 15 edges on the graph and precision >= 0.85 | 85 edges; 1.000 [0.824, 1.000] (k=18, n=18) (unclear as incorrect 0.900 [0.699, 0.972] (k=18, n=20)) | **adopted**, additional predicate |
| single paper, same sentence: APPLIED_TO | same-sentence precision >= 0.80 and 0.15 above cross-sentence (dev reference labels) | same 0.452 [0.292, 0.622] (k=14, n=31); cross 0.258 [0.195, 0.334] (k=39, n=151) | **not adopted** |
| single paper, same sentence: EVALUATED_ON | >= 0.80 correct on a supplementary development sample (dev labels hold one prediction) | 0.958 [0.798, 0.993] (k=23, n=24); pool of 24 (declared 30) | **adopted** |
| linking guard (narrower page) | kept accuracy >= 0.85 and >= 65% of correct links kept | kept accuracy 0.821 [0.702, 0.900] (k=46, n=56); correct links kept 0.979 | **not adopted** (v1 links unchanged) |

Development labels come from the building session (AI-assessed development material, frozen and committed before each rule was applied); they are not an audit. The informational APPLIED_TO sample (same abstract-support rubric as EVALUATED_ON) scored 0.967 [0.833, 0.994] (k=29, n=30); it was measured after the adoption decision and was not used for it.

## Counts before and after

| Quantity | v1 | v2 |
|---|---|---|
| total_nodes | 50,211 | 50,211 |
| total_edges | 242,142 | 242,254 |
| enrichment_nodes | 2,336 | 2,336 |
| enrichment_edges | 16,411 | 16,523 |
| nodes_Method | 948 | 948 |
| nodes_Task | 673 | 673 |
| nodes_Dataset | 370 | 370 |
| nodes_Organization | 345 | 345 |
| edges_PART_OF | 1,129 | 1,129 |
| edges_MEMBER_OF | 0 | 85 |
| edges_APPLIED_TO | 32 | 32 |
| edges_EVALUATED_ON | 4 | 31 |
| edges_RELATED_TO | 16 | 16 |
| linked_entities | 261 | 261 |

## E4 v2 audit: changed axes, fresh samples

| Axis | Primary | Unclear | Unclear as incorrect | Target |
|---|---|---|---|---|
| EVALUATED_ON, single paper, same sentence (all 27; the shown paper supports the relation) | 0.963 [0.817, 0.993] (k=26, n=27) | 0 | 0.963 [0.817, 0.993] (k=26, n=27) | relation precision >= 0.80 |
| MEMBER_OF (30 of population 85; fresh, excludes v1-audited and development pairs) | 1.000 [0.883, 1.000] (k=29, n=29) | 1 | 0.967 [0.833, 0.994] (k=29, n=30) | none declared |

Raw A/B agreement on all 57 items: 0.7544, Cohen's kappa 0.1438 (kappa is low because nearly every item is correct, so chance agreement is high); 14 disagreements went to adjudicator C, by axis {'member_of': 13, 'relation': 1}. Items answered: 57 of 57.

**Caveat on MEMBER_OF.** Disagreement was almost entirely about whether "is part of an ELIXIR national node" (a Wikidata part-of statement to a consortium node) establishes membership. Channel A judged {'correct': 27, 'unclear': 3}; channel B alone judged {'correct': 18, 'unclear': 12} (B called the membership role unspecified for the node partners). Adjudicator C resolved all 14 disputed items as correct, so the headline figure follows A and C's reading. Under B's stricter reading, unclear counted as incorrect, `MEMBER_OF` would be about 18/30. Neither reading is a human annotation; the interval covers sampling error only.

## Targets (declared in specification 4.5; pass or fail, not tuned)

| Target | Figure | Result |
|---|---|---|
| relation precision >= 0.80, v2-changed axis (EVALUATED_ON single paper) | 0.963 [0.817, 0.993] (k=26, n=27) | pass |
| relation precision >= 0.80, paper edges (v1, unchanged) | ADDRESSES_TASK 0.946, USES_DATASET 0.923, USES_METHOD 0.939 | pass |
| relation precision >= 0.80, PART_OF (v1 rule remains in the graph) | 0.694 | **fail** (rule v2 not adopted) |
| relation precision >= 0.80, RELATED_TO (v1, unchanged) | 0.625 | **fail** |
| entity precision >= 0.85 (v1, unchanged) | 0.927 | pass |
| linking accuracy >= 0.85 (v1, unchanged; guard not adopted) | 0.800 | **fail** |
| MEMBER_OF | no target declared | n/a |

## Axes carried over from v1 (not re-measured; unchanged by v2)

| Axis | v1 figure |
|---|---|
| entity precision, default variant | 0.927 [0.891, 0.952] (k=267, n=288) |
| paper edge ADDRESSES_TASK | 0.946 [0.852, 0.981] (k=52, n=55) |
| paper edge USES_DATASET | 0.923 [0.759, 0.979] (k=24, n=26) |
| paper edge USES_METHOD | 0.939 [0.865, 0.974] (k=77, n=82) |
| APPLIED_TO (two or more papers), population-weighted | 0.9375 (all 32 v1 edges audited; population-weighted over the cross- and same-sentence strata) |
| RELATED_TO | 0.625 [0.386, 0.815] (k=10, n=16) |
| PART_OF (v1 packet; v1 rule is still the graph's PART_OF) | 0.694 [0.531, 0.820] (k=25, n=36); v2 packet 0.720 [0.583, 0.825] (k=36, n=50); target 0.80 not met |
| linking | 0.800 [0.711, 0.867] (k=80, n=100); target 0.85 not met |
| recall estimate, default variant | 0.590 [0.536, 0.641] (k=197, n=334) |

v1 PART_OF and linking figures apply unchanged to the v2 graph: the PART_OF v2 rule and the linking guard were not adopted. Wilson 95% intervals describe sampling error only.
