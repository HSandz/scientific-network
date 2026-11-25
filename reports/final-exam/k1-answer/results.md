# K1 answer-quality arm (development figures, k1-answer-v1)

**Development figures only.** 19 kept development questions of qa-benchmark-v1 (15 factual, 4 global); no test question was run. Pipeline: the qa-eval-v1 S4 multi-hop system in automatic mode; scorer: the qa-eval-v1 unified entity resolver and integer exact match. Decoding identical for every model (temperature 0, seed 0, thinking off, uncached). Only the model changes. Graph `enriched-cb371912e308`; references SHA-256 `d2fcf2c0cba2fae7…`. The factual score measures agreement with the graph's edges, not truth.

## Answer accuracy by hop class (mean score, seeded bootstrap 95% CI)

| Model (total params) | Hop 1 (4) | Hop 2 (6) | Hop 3 (5) | Factual overall (15) | Global ok + faithful (4) |
| --- | --- | --- | --- | --- | --- |
| Qwen/Qwen3.5-4B Q4_K_M (4.66B) | 0.950 [0.850, 1.000] | 0.284 [0.016, 0.598] | 0.407 [0.040, 0.773] | 0.502 [0.273, 0.735] | 4 ok, 4/4 faithful |
| google/gemma-4-E4B-it Q4_K_M (8.00B) | 0.600 [0.200, 1.000] | 0.468 [0.152, 0.833] | 0.367 [0.040, 0.687] | 0.469 [0.260, 0.685] | 4 ok, 4/4 faithful |
| Qwen/Qwen3.5-9B Q4_K_M (9.65B), reference only | 1.000 [1.000, 1.000] | 0.574 [0.250, 0.897] | 0.415 [0.130, 0.765] | 0.634 [0.420, 0.829] | 4 ok, 4/4 faithful |

## Faithfulness, planner JSON validity, latency, memory and throughput

| Model | Faithfulness (19, Wilson 95%) | Planner JSON first-pass valid | Planner valid after retry / fallback | Parser JSON first-pass valid | Mean first event s | Mean total s (max) | GPU peak MiB (over idle) | Decode tok/s | Prompt tok/s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| qwen3.5-4b | 19/19 (1.000 [0.832, 1.000]) | 18/18 | 18/18 / 0 | 19/19 | 1.05 | 9.35 (48.2) | 5875 (3336) | 79.4 | 1051.2 |
| gemma-4-e4b | 18/19 (0.947 [0.754, 0.991]) | 18/18 | 18/18 / 0 | 19/19 | 1.14 | 8.75 (47.1) | 5530 (3425) | 67.0 | 3144.7 |
| qwen3.5-9b | 18/19 (0.947 [0.754, 0.991]) | 18/18 | 18/18 / 0 | 19/19 | 1.22 | 12.01 (57.4) | 7208 (5103) | 52.0 | 1132.0 |

## Call-level JSON validity of schema-constrained prompts

| Model | Prompt | Calls | First-pass valid | Valid after correction | Failed |
| --- | --- | --- | --- | --- | --- |
| qwen3.5-4b | `rag-global-v2-map` | 3 | 0 | 0 | 3 |
| qwen3.5-4b | `rag-parse-v2` | 19 | 19 | 0 | 0 |
| qwen3.5-4b | `rag-plan-v4` | 18 | 18 | 0 | 0 |
| gemma-4-e4b | `rag-global-v2-map` | 3 | 0 | 3 | 0 |
| gemma-4-e4b | `rag-parse-v2` | 19 | 19 | 0 | 0 |
| gemma-4-e4b | `rag-plan-v4` | 18 | 18 | 0 | 0 |
| qwen3.5-9b | `rag-global-v2-map` | 3 | 1 | 0 | 2 |
| qwen3.5-9b | `rag-parse-v2` | 19 | 19 | 0 | 0 |
| qwen3.5-9b | `rag-plan-v4` | 18 | 18 | 0 | 0 |

## §6.1 decision rule

- Development answer accuracy (factual overall): qwen3.5-4b 0.502, gemma-4-e4b 0.469, qwen3.5-9b 0.634.
- Best eligible model on this arm: `qwen3.5-4b`.
- Qwen3.5-9B (reference only, 9.65B) gain over the best eligible model: +0.132 (margin 0.10 met).
- Gemma-4-E4B-it gain over Qwen3.5-4B: -0.033 (flag-for-user margin 0.10 not met).
- Hash-seed robustness: over PYTHONHASHSEED 0–19 the 9B gain ranges +0.112 to +0.152 (margin met at every seed: yes); Gemma's best gain over the 4B is -0.013.
- **Outcome:** A margin is met; a model change needs a recorded team decision (not made by the agent).

## Scorer hash-seed sensitivity

The qa-eval-v1 unified entity resolver iterates a Python `set` when it accepts exact alias matches, so the order of resolved IDs, and the top-k slice used for ranked-list answers, depends on the process's `PYTHONHASHSEED`. The primary figures above use `PYTHONHASHSEED=0`. Re-scoring the same raw outputs under 20 hash seeds gives (factual overall, min / mean / max):

| Model | Min | Mean | Max |
| --- | --- | --- | --- |
| qwen3.5-4b | 0.489 | 0.523 | 0.556 |
| gemma-4-e4b | 0.436 | 0.478 | 0.509 |
| qwen3.5-9b | 0.601 | 0.652 | 0.681 |

Per-seed values: `hashseed-sensitivity.json`.

## Parameter scale (the rubric's "parameter scale" point)

| Total parameters | Model | Answer accuracy (15 factual) | Faithfulness (19) | Mean total s | Decode tok/s | GPU over idle MiB |
| --- | --- | --- | --- | --- | --- | --- |
| 4.66B | Qwen/Qwen3.5-4B | 0.502 | 1.000 | 9.35 | 79.4 | 3336 |
| 8.00B | google/gemma-4-E4B-it | 0.469 | 0.947 | 8.75 | 67.0 | 3425 |
| 9.65B | Qwen/Qwen3.5-9B | 0.634 | 0.947 | 12.01 | 52.0 | 5103 |

Accuracy is not monotonic in total size: Gemma-4-E4B-it counts 8.00B total parameters, but most are per-layer embeddings (about 4B effective), so its compute per token is close to the 4B's. Within the Qwen3.5 family the 9.65B reference scores higher than the 4.66B on this small development set, at about two-thirds of the decode speed and about 1.5x the GPU memory. With 15 factual questions every interval overlaps.

## Caveats

- Development figures only; 15 factual questions, so differences of 10 points are within sampling noise.
- The parser, planner and answer prompts were developed with Qwen3.5-4B in the loop; the other models run the same prompts unchanged, which favours the 4B.
- The factual score measures agreement with the graph's edges, not truth.
- Planner JSON validity counts the first `rag-plan-v4` call per question: first-pass valid means schema-valid JSON without the client's correction retry. llama.cpp enforces the JSON schema with a grammar, so validity is expected to be high for every model.
- GPU memory is total device use from `nvidia-smi`; the host display holds part of it (idle baseline shown in `results.json`).
- Global map stage: `rag-global-v2-map` caps output at 512 tokens, and the JSON of qwen3.5-4b 3/3, gemma-4-e4b 0/3, qwen3.5-9b 2/3 map calls was truncated (`finish_reason: length`) and dropped, so those global answers rest on the remaining map points or the reduce step alone. The same limit applies to the frozen qa-eval-v1 run; it is a product limitation, not a model-comparison artifact, and is left unchanged here.
- Not comparable with `reports/final-exam/rag-v1/dev-eval.json`, which used the older row-based development scorer.
