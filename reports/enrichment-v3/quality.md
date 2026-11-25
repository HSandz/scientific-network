# Enrichment v3 quality (AI-assessed)

Graph `enriched-cb371912e308` (SHA-256 `37ee8c59d8245d45...`); audit seed 2026112504. AI-assessed by agent evaluators; not human annotation and not independently validated gold labels. Wilson 95% intervals exclude evaluator error.

## Post-hoc adoption

A reviewer judged the v2 absolute criteria badly chosen. The PART_OF and link rules are adopted on a relative criterion decided after the v2 development results were seen, and the APPLIED_TO criterion was re-declared on the E4 scale after its first result. The development checks are not evidence for v3; accuracy rests only on the fresh E4 v3 audit below.

Evaluators: A: claude-opus-5-5 (three fresh subagents, one per shard); B: codex exec, model gpt-6.2-sol via provider 9router as logged (three fresh sessions); C: codex exec, model gpt-6.2-sol via provider 9router as logged (one fresh session separate from B's); the APPLIED_TO development labeler was a fresh claude-opus-5-5 subagent. Isolation: by directory and instruction: each evaluator worked in its own directory holding only guideline.md and its packet; no separate containers. The building session did not judge. A and B judged every one of the 212 items; C judged the 29 disagreements.

Each cell: estimate [Wilson 95% interval] (k correct / n decided). Unclear verdicts are excluded from the primary figure and counted as incorrect in the sensitivity.

## E4 v3 audit: fresh items only

| Axis | Fresh items (requested; pool) | Primary | Unclear | Unclear as incorrect | Target | Result |
|---|---|---|---|---|---|---|
| PART_OF v3 kept edges | 50 (50; pool 710 of 783) | 0.951 [0.839, 0.987] (39/41) | 9 | 0.780 [0.648, 0.873] (39/50) | 0.80 | pass (primary); **fail** (unclear as incorrect) |
| MEMBER_OF | 26 (30; pool 26 of 85) | 1.000 [0.772, 1.000] (13/13) | 13 | 0.500 [0.321, 0.679] (13/26) | none declared | n/a |
| linking v3 | 76 (100; pool 76 of 231) | 0.895 [0.806, 0.946] (68/76) | 0 | 0.895 [0.806, 0.946] (68/76) | 0.85 | pass (primary); pass (unclear as incorrect) |
| APPLIED_TO single paper, same sentence (shown paper supports the relation) | 60 (100; pool 60 of 136) | 0.983 [0.911, 0.997] (59/60) | 0 | 0.983 [0.911, 0.997] (59/60) | 0.80 | pass (primary); pass (unclear as incorrect) |

Pass or fail compares the point estimate with the declared target; read it with the interval. Fewer fresh items existed than were requested on every axis except PART_OF, so the intervals are wide.

**PART_OF** passes on the decided items but 9 of 50 are unclear (five have a ministry as the Wikidata parent of a university or institute; A called most of the nine incorrect, B and C unclear), so counting unclear as incorrect gives 0.78, below 0.80. **MEMBER_OF**: 13 of 26 items are unclear in the final reading (C marked every ELIXIR national-node dispute unclear), so 1.000 on the 13 decided items is not a reliable summary; no `MEMBER_OF` item was judged incorrect by any channel, and the sensitivity is 0.50.

### Agreement per axis (A and B judged every item; C adjudicated the disputes)

| Axis | Observed agreement / Cohen's kappa / disputes sent to C | A verdicts | B verdicts | C verdicts |
|---|---|---|---|---|
| PART_OF | 0.700 / 0.200 / 15 | {'incorrect': 9, 'correct': 38, 'unclear': 3} | {'unclear': 8, 'correct': 40, 'incorrect': 2} | {'unclear': 9, 'correct': 4, 'incorrect': 2} |
| MEMBER_OF | 0.577 / 0.154 / 11 | {'correct': 24, 'unclear': 2} | {'correct': 13, 'unclear': 13} | {'unclear': 11} |
| linking | 0.974 / 0.861 / 2 | {'correct': 69, 'incorrect': 7} | {'correct': 67, 'incorrect': 9} | {'correct': 1, 'incorrect': 1} |
| APPLIED_TO single paper | 0.983 / 0.000 / 1 | {'correct': 60} | {'correct': 59, 'incorrect': 1} | {'incorrect': 1} |

### Single-channel readings (how much the final figure depends on the adjudicator)

| Axis | A alone: correct / incorrect / unclear | B alone: correct / incorrect / unclear | Final (A/B, C decides disputes) |
|---|---|---|---|
| PART_OF | 38 / 9 / 3 | 40 / 2 / 8 | 0.951 [0.839, 0.987] (39/41), 9 unclear |
| MEMBER_OF | 24 / 0 / 2 | 13 / 0 / 13 | 1.000 [0.772, 1.000] (13/13), 13 unclear |
| linking | 69 / 7 / 0 | 67 / 9 / 0 | 0.895 [0.806, 0.946] (68/76), 0 unclear |
| APPLIED_TO single paper | 60 / 0 / 0 | 59 / 1 / 0 | 0.983 [0.911, 0.997] (59/60), 0 unclear |

Kappa is uninformative where one rater has no variation (APPLIED_TO single paper: A judged all 60 correct). Pooled: agreement 0.8632, kappa 0.4121, 29 disputes. Items answered: 212 of 212.
**Adjudicator caveat.** C is a different family from A, as declared, but it is the same model as B (`gpt-6.2-sol` via `9router`, separate session), so C and B are not independent of each other. On MEMBER_OF and PART_OF, C followed B's more cautious reading and marked many items unclear; the single-channel table shows the figures A alone and B alone would give. No other non-Claude model was tried.

## MEMBER_OF in the v2 audit under four readings

The 14 v2 disputes (13 `MEMBER_OF` items) were sent to the same non-Claude adjudicator with the same packet. The original v2 figure is unchanged in `reports/enrichment-v2/quality.md`; here it is the first row. Of the 13 disputed `MEMBER_OF` items the new adjudicator ruled {'correct': 3, 'incorrect': 0, 'unclear': 10}.

| Reading | Primary | Unclear | Unclear as incorrect |
|---|---|---|---|
| A + C (Claude), the original v2 figure | 1.000 [0.883, 1.000] (29/29) | 1 | 0.967 [0.833, 0.994] (29/30) |
| A + C (non-Claude) | 1.000 [0.832, 1.000] (19/19) | 11 | 0.633 [0.455, 0.781] (19/30) |
| B alone | 1.000 [0.824, 1.000] (18/18) | 12 | 0.600 [0.423, 0.754] (18/30) |
| A alone (informational) | 1.000 [0.875, 1.000] (27/27) | 3 | 0.900 [0.744, 0.965] (27/30) |

## Counts v1 / v2 / v3

| Quantity | v1 | v2 | v3 |
|---|---|---|---|
| total_nodes | 50,211 | 50,211 | 50,144 |
| total_edges | 242,142 | 242,254 | 242,048 |
| enrichment_nodes | 2,336 | 2,336 | 2,269 |
| nodes_Method | 948 | 948 | 954 |
| nodes_Task | 673 | 673 | 679 |
| nodes_Dataset | 370 | 370 | 371 |
| nodes_Organization | 345 | 345 | 265 |
| edges_PART_OF | 1,129 | 1,129 | 783 |
| edges_MEMBER_OF | 0 | 85 | 85 |
| edges_APPLIED_TO | 32 | 32 | 167 |
| edges_EVALUATED_ON | 4 | 31 | 31 |
| edges_RELATED_TO | 16 | 16 | 16 |
| edges_USES_METHOD | 7,907 | 7,907 | 7,911 |
| edges_ADDRESSES_TASK | 4,591 | 4,591 | 4,591 |
| edges_USES_DATASET | 2,732 | 2,732 | 2,733 |
| linked_entities | 261 | 261 | 231 |

PART_OF edges dropped by the v3 rule, by reason: {'end_dated': 26, 'excluded_class': 157, 'implausible_type_order': 6, 'not_organization': 61, 'reversed_direction': 11}. The 85 consortium and association pairs are `MEMBER_OF` only (no `PART_OF`).
Links: the guard removed 43 of 287 raw links (final linked entities 261 to 231); unlinking a QID undoes some merges, so entity node counts moved (see the table).

## All axes: v1, v2 and v3 side by side

| Axis | v1 | v2 | v3 | Target |
|---|---|---|---|---|
| entity precision, default | 0.927 [0.891, 0.952] (267/288) | carried over (unchanged) | carried over from v1 (unchanged) | 0.85 |
| paper edge ADDRESSES_TASK | 0.946 [0.852, 0.981] (52/55) | carried over | carried over | 0.80 |
| paper edge USES_DATASET | 0.923 [0.759, 0.979] (24/26) | carried over | carried over | 0.80 |
| paper edge USES_METHOD | 0.939 [0.865, 0.974] (77/82) | carried over | carried over | 0.80 |
| linking | 0.800 [0.711, 0.867] (80/100) | carried over (guard not adopted in v2: same as v1) | **fresh:** 0.895 [0.806, 0.946] (68/76) on 76 items | 0.85 |
| PART_OF | 0.694 [0.531, 0.820] (25/36) (unclear as incorrect 0.50); with the statement shown 0.720 [0.583, 0.825] (36/50) | carried over (v1 rule) | **fresh:** 0.951 [0.839, 0.987] (39/41) on 50 items (unclear as incorrect 0.78) | 0.80 |
| MEMBER_OF | n/a | 1.000 [0.883, 1.000] (29/29) (original reading; see the readings above) | **fresh:** 1.000 [0.772, 1.000] (13/13) on 26 items | none declared |
| APPLIED_TO two or more papers | 0.9375 (32 edges audited) | carried over | carried over from v1 (the v3 graph has a different edge set; not re-audited) | 0.80 |
| APPLIED_TO single paper, same sentence | n/a | not adopted | **fresh:** 0.983 [0.911, 0.997] (59/60) on 60 items | 0.80 |
| EVALUATED_ON (two or more papers) | 1.0 (4 edges) | carried over | carried over | 0.80 |
| EVALUATED_ON single paper | n/a | 0.963 [0.817, 0.993] (26/27) (all 27 audited) | carried over from v2 (not re-audited) | 0.80 |
| RELATED_TO | 0.625 [0.386, 0.815] (10/16) | carried over | carried over | 0.80 |
| recall estimate, default | 0.590 [0.536, 0.641] (197/334) | carried over | carried over | none declared |

Wilson 95% intervals describe sampling error only; they exclude evaluator error. Development checks (v2 and the v3 APPLIED_TO sample) are not part of this table.
