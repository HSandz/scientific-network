# Test Benchmark Evaluation Results (qa-eval-v1)

- **Protocol**: `qa-eval-v1` (commit `433903ddde134e6acd9a37b534646b601f9cac5e`)
- **Graph**: `enriched-cb371912e308` (`37ee8c59d8245d452e42575b7afbb13808b5f835d51c9ee838bd5581434633e3`)
- **Local LLM**: `qwen3.5-4b-q4_k_m` (`Qwen/Qwen3.5-4B` rev `e87f176479d0855a907a41277aca2f8ee7a09523`, temp `0.0`, seed `0`, `enable_thinking=False`)

> [!IMPORTANT]
> **AI-assessed quality statement**: Citation validity and global pairwise comparisons are AI-assessed by isolated LLM evaluators (not independent human annotations or verified course accuracy). Wilson and bootstrap 95% intervals reflect sampling uncertainty only and exclude evaluator error.
> **Evaluator family & independence disclosure**: Evaluator A: fresh isolated claude-opus-5-5. Evaluator B: fresh isolated codex exec (gpt-6.2-sol via 9router). Adjudicator C: separate fresh isolated codex exec session (gpt-6.2-sol via 9router, used because local gemini CLI 0.26.0 returned exit 41 unauthenticated). C differs in model family from A but shares B's model family and is therefore not independent of B.
> **Coverage & extraction caveats**: Results are measured on the 69 kept benchmark test questions (11 dropped for empty/ambiguous references) over AAAI and IJCAI 2021-2025 main-track papers; affiliation coverage (73.71%) and historical topic precision (68.63%) bound completeness, and unified text entity resolution uses normalized aliases plus all-MiniLM-L6-v2 cosine >= 0.80.

## 1. Factual Accuracy by Hop Class (Unified Entity Resolver, Mean Score & 95% Bootstrap CI)

| System | Hop 1 (14) | Hop 2 (22) | Hop 3 (18) | Overall Factual (54) | Mean Latency (Factual) |
| --- | --- | --- | --- | --- | --- |
| S1_slm_only | 0.0262 [0.0000, 0.0595] | 0.1929 [0.1111, 0.2985] | 0.1165 [0.0556, 0.1864] | 0.1242 [0.0787, 0.1759] | 4.676s |
| S2_vector_rag | 0.0000 [0.0000, 0.0000] | 0.1250 [0.0456, 0.2346] | 0.0112 [0.0000, 0.0274] | 0.0547 [0.0200, 0.0993] | 7.03s |
| S3_graphrag | 0.2571 [0.0571, 0.5000] | 0.1474 [0.0630, 0.2490] | 0.1088 [0.0403, 0.1868] | 0.1630 [0.0919, 0.2369] | 10.595s |
| S4_multihop | 0.4190 [0.1966, 0.6395] | 0.2532 [0.1168, 0.4173] | 0.6466 [0.4548, 0.8177] | 0.4273 [0.3132, 0.5403] | 9.78s |

## 2. Automatic Faithfulness & AI-Assessed Citation Validity (95% Wilson CI)

| System | Automatic Faithfulness (95% Wilson CI) | AI-Assessed Citation Validity (95% Wilson CI) |
| --- | --- | --- |
| S1_slm_only | N/A (no retrieval trace) | 0 citations emitted |
| S2_vector_rag | 49/69 (0.7101 [0.5943, 0.8038]) | 23/25 (0.9200 [0.7503, 0.9778]) |
| S3_graphrag | 59/69 (0.8551 [0.7534, 0.9193]) | 16/25 (0.6400 [0.4452, 0.7975]) |
| S4_multihop | 60/69 (0.8696 [0.7703, 0.9298]) | 9/25 (0.3600 [0.2025, 0.5548]) |

Citation A–B Cohen's kappa (AI-assessed): `0.6199` (disagreements adjudicated by C: `15`).

## 3. AI-Assessed Global Pairwise Comparison (15 Global Questions, AB+BA = 180 Blind Items)

| System | Wins / Ties / Losses (of 90) | Win Rate | Position-Consistent Wins (of 45 pairs) |
| --- | --- | --- | --- |
| S1_slm_only | 3 / 0 / 87 | 0.0333 | 1 (0.0222) |
| S2_vector_rag | 72 / 0 / 18 | 0.8000 | 35 (0.7778) |
| S3_graphrag | 44 / 14 / 32 | 0.4889 | 21 (0.4667) |
| S4_multihop | 47 / 14 / 29 | 0.5222 | 22 (0.4889) |

Global pairwise A–B Cohen's kappa (AI-assessed): `0.7988`; disagreements resolved by C: `26`; position-inconsistent pairs: `4` / `90`.

## Dated notes added after the evaluation

These notes were added later. They do not change any figure above; no system was re-run on a test
question.

### 2026-11-26 — product citation labelling changed after this evaluation (WORK-2026-11-26-001)

The figures above describe the product as evaluated (code commit `433903d`, results committed up to
`e572055`). In that version the multi-hop answer prompt `rag-answer-v3` attached paper IDs returned
with graph rows to sentences, including aggregate claims such as counts and shares. Single abstracts
rarely state such claims, which explains S4's AI-assessed citation validity of 9/25.

After the evaluation, the product changed:

- **Answer prompts.** `rag-answer-v4` and `rag-local-answer-v3`: aggregate claims point to the trace
  step that computed them, written as `[step N]`. A paper ID is written only when the sentence is
  about that specific paper.
- **Evidence labelling.** `evidence-labels-v1`, in `label_answer_evidence` in
  `src/scientific_network/rag/answer.py`. Only a paper that the trace returns as its own row (the
  `papers` tool) or as an abstract excerpt (local search) is shown as a **citation**, together with
  the sentence it supports. Every other paper is listed as **papers in this result**: the example
  papers behind a step's count or list. Inline IDs on aggregate claims are rewritten to `[step N]`.
- **Faithfulness verifier.** It now drops an unclosed parenthetical fragment from list heads, so
  `X (lift: 3.2)` checks the entity `X`.

The S4 citation-validity figure of 0.36 therefore describes the earlier labelling. It was not
re-measured under the new labelling. The automatic faithfulness figures were computed with the
earlier verifier. To reproduce this evaluation, check out commit `e572055`.
