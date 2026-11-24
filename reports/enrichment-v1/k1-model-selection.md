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
