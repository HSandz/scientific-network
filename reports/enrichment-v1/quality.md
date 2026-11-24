# Enrichment quality (AI-assessed)

Graph `enriched-c0f7d1dd4abd` (SHA-256 `011d5fe274ddbbaa...`), sample seed 20261124, 1111 frozen items, 1111 answered. AI-assessed by an agent evaluator from a different model family than the extractors; not human annotation and not independently validated gold labels. Wilson 95% intervals exclude evaluator error.

Evaluators: A: fresh Claude Opus subagent contexts (7 runs: shards 1-6 and recall); B: OpenAI Codex CLI 0.171.0 (default model of the CLI, exact model ID not exposed in its output) fresh `codex exec` runs, one per packet; C: fresh Claude Opus subagent adjudicator (24 disputed A/B items). Extractors: GLiNER-Relex-large and Qwen3.5-4B Q4_K_M. Isolation: each evaluator ran in its own directory holding only its packet and a copy of docs/final-exam/enrichment-labeling-guideline-v1.md; isolation of the filesystem was by instruction (Claude) and by working-directory sandbox (Codex), not by a hard barrier. A and C share a model family; B is a different family. The session that built the pipeline did not judge..

Each cell: estimate [Wilson 95% interval] (k correct, n decided); unclear verdicts are excluded from the primary figure and counted as incorrect in the sensitivity figure.

## Entity precision by variant (test papers; ablation)

| Variant | Type | Precision |
|---|---|---|
| default | Method | 0.950 [0.887, 0.978] (k=94, n=99); unclear 1; unclear as incorrect 0.940 [0.875, 0.972] (k=94, n=100) |
| default | Task | 0.897 [0.821, 0.943] (k=87, n=97); unclear 3; unclear as incorrect 0.870 [0.790, 0.922] (k=87, n=100) |
| default | Dataset | 0.935 [0.865, 0.970] (k=86, n=92); unclear 0; unclear as incorrect 0.935 [0.865, 0.970] (k=86, n=92) |
| default | all_types | 0.927 [0.891, 0.952] (k=267, n=288); unclear 4; unclear as incorrect 0.914 [0.877, 0.941] (k=267, n=292) |
| encoder_only | Method | 0.854 [0.770, 0.911] (k=82, n=96); unclear 4; unclear as incorrect 0.820 [0.733, 0.883] (k=82, n=100) |
| encoder_only | Task | 0.707 [0.611, 0.788] (k=70, n=99); unclear 1; unclear as incorrect 0.700 [0.604, 0.781] (k=70, n=100) |
| encoder_only | Dataset | 0.280 [0.201, 0.375] (k=28, n=100); unclear 0; unclear as incorrect 0.280 [0.201, 0.375] (k=28, n=100) |
| encoder_only | all_types | 0.610 [0.553, 0.664] (k=180, n=295); unclear 5; unclear as incorrect 0.600 [0.544, 0.654] (k=180, n=300) |
| slm_only | Method | 0.857 [0.774, 0.913] (k=84, n=98); unclear 2; unclear as incorrect 0.840 [0.756, 0.899] (k=84, n=100) |
| slm_only | Task | 0.714 [0.618, 0.794] (k=70, n=98); unclear 2; unclear as incorrect 0.700 [0.604, 0.781] (k=70, n=100) |
| slm_only | Dataset | 0.590 [0.492, 0.681] (k=59, n=100); unclear 0; unclear as incorrect 0.590 [0.492, 0.681] (k=59, n=100) |
| slm_only | all_types | 0.720 [0.666, 0.768] (k=213, n=296); unclear 4; unclear as incorrect 0.710 [0.656, 0.758] (k=213, n=300) |

Target: entity precision at least 0.85 (default variant).

## Predicate precision

| Predicate | Precision |
|---|---|
| ADDRESSES_TASK | 0.946 [0.852, 0.981] (k=52, n=55); unclear 3; unclear as incorrect 0.897 [0.792, 0.952] (k=52, n=58) |
| USES_DATASET | 0.923 [0.759, 0.979] (k=24, n=26); unclear 1; unclear as incorrect 0.889 [0.719, 0.962] (k=24, n=27) |
| USES_METHOD | 0.939 [0.865, 0.974] (k=77, n=82); unclear 12; unclear as incorrect 0.819 [0.729, 0.884] (k=77, n=94) |
| RELATED_TO | 0.625 [0.386, 0.815] (k=10, n=16); unclear 0; unclear as incorrect 0.625 [0.386, 0.815] (k=10, n=16) |
| PART_OF | 0.694 [0.531, 0.820] (k=25, n=36); unclear 14; unclear as incorrect 0.500 [0.366, 0.634] (k=25, n=50) |
| APPLIED_TO, cross_sentence (population 31), every shown paper supports | 0.935 [0.793, 0.982] (k=29, n=31); unclear 0; unclear as incorrect 0.935 [0.793, 0.982] (k=29, n=31) |
| APPLIED_TO, cross_sentence, at least half support (secondary) | 1.000 [0.890, 1.000] (k=31, n=31) |
| APPLIED_TO, same_sentence (population 1), every shown paper supports | 1.000 [0.206, 1.000] (k=1, n=1); unclear 0; unclear as incorrect 1.000 [0.206, 1.000] (k=1, n=1) |
| APPLIED_TO, same_sentence, at least half support (secondary) | 1.000 [0.206, 1.000] (k=1, n=1) |
| APPLIED_TO, population-weighted | primary 0.9375; secondary 1.0; unclear as incorrect 0.9375 |
| EVALUATED_ON, cross_sentence (population 2), every shown paper supports | 1.000 [0.342, 1.000] (k=2, n=2); unclear 0; unclear as incorrect 1.000 [0.342, 1.000] (k=2, n=2) |
| EVALUATED_ON, cross_sentence, at least half support (secondary) | 1.000 [0.342, 1.000] (k=2, n=2) |
| EVALUATED_ON, same_sentence (population 2), every shown paper supports | 1.000 [0.342, 1.000] (k=2, n=2); unclear 0; unclear as incorrect 1.000 [0.342, 1.000] (k=2, n=2) |
| EVALUATED_ON, same_sentence, at least half support (secondary) | 1.000 [0.342, 1.000] (k=2, n=2) |
| EVALUATED_ON, population-weighted | primary 1.0; secondary 1.0; unclear as incorrect 1.0 |

Target: relation precision at least 0.8.

## Linking accuracy

- link: 0.800 [0.711, 0.867] (k=80, n=100); unclear 0; unclear as incorrect 0.800 [0.711, 0.867] (k=80, n=100) (target at least 0.85)

## Recall estimate (50 test abstracts listed blind by the evaluator)

| Variant | Method | Task | Dataset | All |
|---|---|---|---|---|
| default | 0.611 [0.545, 0.674] (k=132, n=216) | 0.415 [0.314, 0.523] (k=34, n=82) | 0.861 [0.713, 0.939] (k=31, n=36) | 0.590 [0.536, 0.641] (k=197, n=334) |
| encoder_only | 0.574 [0.507, 0.638] (k=124, n=216) | 0.585 [0.477, 0.686] (k=48, n=82) | 0.917 [0.782, 0.971] (k=33, n=36) | 0.614 [0.560, 0.664] (k=205, n=334) |
| slm_only | 0.671 [0.606, 0.731] (k=145, n=216) | 0.585 [0.477, 0.686] (k=48, n=82) | 0.972 [0.858, 0.995] (k=35, n=36) | 0.683 [0.631, 0.730] (k=228, n=334) |

## Agreement

Raw A/B on the overlap: 222 items judged by both channels, observed agreement 0.8919, Cohen's kappa 0.759. Disagreements went to adjudicator C.

## Coverage and structure (whole graph)

```json
{
 "validator_errors": 0,
 "entity_nodes": 1991,
 "orphan_entity_nodes": 0,
 "duplicate_entities_same_qid_under_two_ids": 0,
 "keys_with_type_conflict": 61,
 "coverage": {
  "core_papers": 13617,
  "papers_with_method": 0.4017,
  "papers_with_task": 0.2758,
  "papers_with_dataset": 0.1182,
  "papers_with_method_task_and_dataset": 0.0214,
  "organizations": 2047,
  "organizations_with_wikidata_qid": 2044,
  "organizations_with_wikipedia_page": 1462
 }
}
```

Wilson 95% intervals describe sampling error only; they exclude evaluator error.
