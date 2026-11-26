# K1 model selection (development split, 100 papers)

AI-assessed reference labels (frozen before any model ran); lenient matching primary, strict secondary. A development comparison, not a quality claim. Two concurrent requests on one GPU; wall time covers all 100 papers.

| Model (total params) | Variant | Entity F1 lenient / strict | Relation F1 lenient / strict | Valid JSON | Wall s | GPU MiB |
|---|---|---|---|---|---|---|
| Qwen3.5-4B Q4_K_M (4.66B) | SLM only (extract-v2) | 0.663 / 0.591 | 0.318 / 0.233 | 100% | 353.8 | 4966 |
| Qwen3.5-4B Q4_K_M (4.66B) | GLiNER-Relex candidates + SLM verify-v5 + relations-v1 | 0.670 / 0.564 | 0.400 / 0.275 | 100% | 146.6 | 4966 |
| Gemma-4-E4B-it Q4_K_M (8.0B) | SLM only (extract-v2) | 0.653 / 0.493 | 0.440 / 0.269 | 100% | 256.8 | 4794 |
| Gemma-4-E4B-it Q4_K_M (8.0B) | GLiNER-Relex candidates + SLM verify-v5 + relations-v1 | 0.624 / 0.536 | 0.272 / 0.202 | 100% | 345.4 | 4794 |
| Qwen3.5-9B Q4_K_M (reference only) (9.65B) | SLM only (extract-v2) | 0.678 / 0.598 | 0.333 / 0.273 | 100% | 574.8 | 6879 |
| Qwen3.5-9B Q4_K_M (reference only) (9.65B) | GLiNER-Relex candidates + SLM verify-v5 + relations-v1 | 0.662 / 0.554 | 0.373 / 0.247 | 100% | 390.5 | 6879 |

## Encoders alone (no SLM)

| Encoder | Entity P / R / F1 | Relation F1 |
|---|---|---|
| GLiNER-Relex-large (entity 0.7, relation 0.9) | 0.480 / 0.658 / 0.555 | 0.201 |
| GLiNER2.5-base (entity 0.4, relation 0.3) | 0.378 / 0.615 / 0.468 | 0.188 |

With Qwen3.5-4B verification: GLiNER2.5 candidates entity F1 0.588; GLiNER-Relex candidates 0.670.

## Decision

- **Language model: Qwen3.5-4B Q4_K_M.** Best eligible entity F1 (0.670) and best relation F1 among encoder+SLM variants (0.400), about 2.4x faster than Gemma-4-E4B-it with less memory. Gemma's SLM-only variant has a higher relation F1 (0.440) but a lower entity F1 and is slower; with 112 reference relations that gap is noisy.
- **Qwen3.5-9B (reference only, 9.65B total) does not meet the §6.1 rule**: entity F1 -0.008 (encoder+SLM) or +0.015 (SLM only) and relation F1 -0.027 against the 4B, all far below the 5-point margin. No D042 model amendment.
- **Extractor: GLiNER-Relex-large**, picked on dev as spec §4.2 allows (encoder-only entity F1 0.556 vs 0.468 for GLiNER2.5). This replaces the stated GLiNER2.5 default and is recorded as a D042 amendment.

## Limits

- Prompts were tuned on dev with Qwen3.5-4B in the loop; Gemma and the 9B ran the final prompts unchanged, so the comparison favours the 4B.
- The dev answer-accuracy arm of the rule needs v5 and cannot run yet.
- Reference labels are conservative, so precision is understated for every system. Wilson intervals do not cover evaluator error.
- The 4B encoder+SLM run-stats file was transcribed from console output; call logs are in the ignored run directory.

## Answer-quality arm (added 2026-11-26, WORK-2026-11-26-001)

The "Limits" item above recorded the answer-accuracy arm as pending until v5 existed. It was run on
2026-11-26 under the protocol [`configs/k1-answer-v1.yaml`](../../configs/k1-answer-v1.yaml), committed
before any run. **Development figures only:** the 19 kept development questions of qa-benchmark-v1
(15 factual, 4 global). No test question was run. Pipeline: the qa-eval-v1 S4 multi-hop system
(automatic mode, prompts `rag-parse-v2`, `rag-plan-v4`, `rag-answer-v3`, `rag-global-v2`, RAG code
unchanged since the frozen qa-eval-v1 commit). Scorer: the qa-eval-v1 unified entity resolver with
integer exact match. Decoding is identical for every model: temperature 0, seed 0, thinking off,
uncached, llama.cpp, 16,384-token context, Q4_K_M. Only the model changes. Full results:
[`reports/final-exam/k1-answer/results.md`](../final-exam/k1-answer/results.md).

| Total params | Model (Q4_K_M GGUF) | Answer accuracy, 15 factual (bootstrap 95% CI) | Hop 1 / 2 / 3 | Faithfulness (19) | Planner JSON first-pass valid | Mean first event / total s | Decode tok/s | GPU over idle MiB |
|---|---|---|---|---|---|---|---|---|
| 4.66B | Qwen3.5-4B (chosen) | 0.502 [0.273, 0.735] | 0.950 / 0.284 / 0.407 | 19/19 | 18/18 | 1.05 / 9.35 | 79.4 | 3,336 |
| 8.00B | Gemma-4-E4B-it | 0.469 [0.260, 0.685] | 0.600 / 0.468 / 0.367 | 18/19 | 18/18 | 1.14 / 8.75 | 67.0 | 3,425 |
| 9.65B | Qwen3.5-9B (reference only) | 0.634 [0.420, 0.829] | 1.000 / 0.574 / 0.415 | 18/19 | 18/18 | 1.22 / 12.01 | 52.0 | 5,103 |

Hop-class values and intervals for every model are in the results file (primary run under
`PYTHONHASHSEED=0`; see the scorer note below).

**Parameter scale.** Answer accuracy is not monotonic in total size. Gemma-4-E4B-it has 8.00B total
parameters, but most are per-layer embeddings (about 4B effective), and it scores slightly below the
4.66B Qwen. Within the Qwen3.5 family the 9.65B reference scores higher than the 4.66B, at about
two-thirds of the decode speed and about 1.5x the GPU memory. With 15 factual questions all intervals
overlap.

**§6.1 outcome.** The best eligible model on this arm is still Qwen3.5-4B (Gemma −0.033; Gemma is
never within 10 points of the 4B at any hash seed). **Qwen3.5-9B (reference only) beats it by +0.132,
which meets the 10-point answer-accuracy margin** (+0.112 to +0.152 across hash seeds 0–19, met at
every seed). Under §6.1 the 9B may replace the 4B only if the team also accepts the "9B language
model" argument (9.65B total, above the 9.0B total-parameter rule) and records a D042 amendment.
**No such decision has been made; Qwen3.5-4B remains the model in use.** This is a decision for the
user and team.

**Team decision (2026-11-26, D042 amendment):** Keep **Qwen3.5-4B** (4.66B total parameters). `Qwen/Qwen3.5-9B` (9.65B total, above the strict ≤9.0B rule) stays the **parameter-scale reference** only.

**Caveats.** 15 factual development questions: a 10-point difference is within sampling noise. The
parser, planner and answer prompts were developed with Qwen3.5-4B in the loop, which favours the 4B,
so the 9B's gain is, if anything, understated. The factual score measures agreement with the graph's
edges, not truth. The qa-eval-v1 scorer depends on `PYTHONHASHSEED` (it iterates a Python `set`);
the spread is reported in the results file. The global map stage truncates JSON at its 512-token
limit for both Qwen models (4B 3/3 map calls, 9B 2/3), a product limitation shared with qa-eval-v1.
