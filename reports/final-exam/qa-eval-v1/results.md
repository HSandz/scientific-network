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

### 2026-11-26 — Supplementary, post-hoc, AI-assessed literature-supported precision (S2 vs S4)

**Why it was added.** The factual scores in §1 measure agreement with the graph's edges, not truth.
For example, vector RAG (S2) answered "Which tasks is transformer applied to?" with plausible tasks
cited from abstracts and scored 0, because those tasks are not the graph's `APPLIED_TO` edges. This
check asks a different question of the same frozen answers. It was designed after the results were
seen (post hoc) and is reported next to the graph-agreement scores, never in place of them.

**Method** ([`configs/supplementary-precision-v1.yaml`](../../../configs/supplementary-precision-v1.yaml)).

- **No system was re-run.** Items come from the frozen `raw-outputs.jsonl` (SHA-256 `d55218eb…`):
  the listed items in S2 and S4 answers to the hop-1 and hop-2 list questions (`set`,
  `ranked_list`). The item pools held 112 (S2) and 118 (S4) items.
- **Sample.** 60 items per system, seeded (20261126) and stratified round-robin over questions.
- **Freeze.** The [manifest](supplementary-precision-manifest.json) (no abstracts) was committed
  before judging (`dcdfcd8`).
- **What evaluators saw.** Each item and its question, plus the title and abstract of the papers
  cited on the item's line. For an item with no citation on its line, they saw up to 3 of the
  system's shown papers that mention it, or else the first 3 shown papers. Abstracts appear only in
  an ignored packet. Items were blinded: interleaved, with no system names.
- **Question:** "Is this item a correct answer to the question, supported by the AAAI/IJCAI 2021–2025
  literature shown?" Verdicts: yes, no or unclear.
- **Evaluators.** A is a fresh `claude -p` (claude-opus-5-5) and B a fresh `codex exec`
  (gpt-6.2-sol via 9router), both run outside the repository. C is a separate fresh `codex exec`
  session that adjudicated the 23 A/B disagreements. C differs in
  family from A but shares B's family (the Gemini CLI still returns code 41, unauthenticated). The
  building session did not judge.
- **Agreement.** A–B Cohen's κ = 0.708.
  [Evaluator evidence](supplementary-precision-evidence.json); [per-item results](supplementary-precision.json).

| System | Literature-supported precision (yes / all, Wilson 95%) | Excluding "unclear" | Verdicts yes / no / unclear | Hop 1 | Hop 2 |
| --- | --- | --- | --- | --- | --- |
| S2_vector_rag | 26/60 = 0.433 [0.316, 0.559] | 26/48 = 0.542 [0.403, 0.674] | 26 / 22 / 12 | 10/11 = 0.909 [0.623, 0.984] | 16/49 = 0.327 [0.212, 0.466] |
| S4_multihop | 21/60 = 0.350 [0.242, 0.476] | 21/36 = 0.583 [0.422, 0.729] | 21 / 15 / 24 | 13/17 = 0.765 [0.527, 0.904] | 8/43 = 0.186 [0.097, 0.326] |

S4 by evidence rule:

- shown paper mentions the item: 17/27 = 0.630 [0.442, 0.785];
- paper cited on the item line: 4/18 = 0.222 [0.090, 0.452];
- no paper shown: 0/14 = 0.000 [0.000, 0.215].

All S2 items were cited on their line.

**Reading.** On this literature-support question the two systems overlap: S2 0.433 and S4 0.350
(all items), and 0.542 vs 0.583 excluding "unclear". Neither leads clearly, while on graph agreement
(§1) S4 leads S2 by a wide margin. The check has limits:

- It cannot support aggregate or ranking items from single abstracts, which carry no author lists
  or corpus-wide counts. Most of S4's "unclear" verdicts are researcher rankings (for example,
  "which ten researchers authored the most papers that use X").
- 14 S4 items come from steps that return no papers, so they are "no" by construction.

Both systems are wrong or unsupported on many hop-2 items. **AI-assessed:** these are not human
annotations; Wilson intervals cover sampling only, not evaluator error; C is not independent of B;
the design is post hoc.

### 2026-11-26 — Factual scorer depends on the Python hash seed (WORK-2026-11-26-001)

The unified entity resolver accepts exact alias matches while iterating a Python `set`, so the order
of resolved IDs depends on the process's `PYTHONHASHSEED`. That order matters because ranked-list
answers are scored on a top-k slice. The §1 figures came from a single scoring process with a random
hash seed, which cannot be reproduced exactly.

The frozen `raw-outputs.jsonl` was re-scored under `PYTHONHASHSEED` 0–19 in an ignored scratch
directory. No system was re-run, and the committed `factual-scores.json` is unchanged (SHA-256
`ca8735fc…`).

| System | §1 factual overall | Min over 20 seeds | Mean | Max |
| --- | --- | --- | --- | --- |
| S1_slm_only | 0.1242 | 0.1168 | 0.1211 | 0.1242 |
| S2_vector_rag | 0.0547 | 0.0361 | 0.0426 | 0.0547 |
| S3_graphrag | 0.1630 | 0.1519 | 0.1639 | 0.1815 |
| S4_multihop | 0.4273 | 0.4051 | 0.4191 | 0.4292 |

The ranking S4 > S3 > S1 > S2 holds at every seed. S4's spread is 0.405–0.429. The §1 figures sit
within each range: at its upper end for S1, S2 and S4, and near the mean for S3. Per-seed values are
in [`scorer-hashseed-sensitivity.json`](scorer-hashseed-sensitivity.json). The frozen harness was not
changed. Later evaluations should fix the seed or sort the spans.

### 2026-11-26 — Global map-stage truncation, humanized trace keys, and scorer determinism (WORK-2026-11-26-002)

After `qa-eval-v1` and `k1-answer-v1` were frozen, the following product and scorer fixes were applied.
No `qa-eval-v1` system was re-run on any test question, and all `qa-eval-v1` figures above remain unchanged.

- **Global map-stage truncation (`rag-global-v3`).** `rag-global-v2-map` previously capped output at
  512 tokens with up to 6 uncapped claims per batch, causing 41 of 66 map calls in `qa-eval-v1` and
  6 of 12 map calls (`50.0%` failure rate, 6 truncated, mean uncached latency `44.581 s`, max
  `53.598 s`) on the 4 kept development global questions (`qa-v1-d017`–`qa-v1-d020`) to truncate and
  fail. Raising map `max_tokens` to 1024 and bounding `GLOBAL_MAP_SCHEMA` to at most 4 claims of
  ≤240 characters with ≤3 `paper_ids` (and ≤4 `key_findings` per input report) reduced the
  development global map failure rate to **0 of 12 (`0.0%`, 0 truncated)** with mean uncached latency
  **`26.735 s`** (max `30.886 s`).
- **Human-readable trace labels and on-demand subject specialization.** `_compact_trace_for_prompt`
  maps internal snake_case metric keys (such as `share_delta` → `share change`) to plain English, and
  `RAGToolset.rank` computes N4 personalized PageRank lift on demand (with RCA fallback) for subjects
  outside the precomputed top 30 alongside multi-kind subject linking.
- **Scorer determinism.** `UnifiedEntityResolver.resolve` in `src/scientific_network/evaluation/qa_eval.py`
  now iterates `sorted(span_norms)` and sorts alias/catalog candidates by ID so future runs are
  independent of `PYTHONHASHSEED`. The frozen `qa-eval-v1` scores above were left untouched.

### 2026-11-26 — Summary-first answer format for the redesigned Ask screen (WORK-2026-11-26-003)

After `qa-eval-v1` was frozen, the product's answer prompts changed for the redesigned Ask screen.
No `qa-eval-v1` system was re-run on any test question, and every figure above is unchanged; the
benchmark used `rag-answer-v3` / `rag-local-answer-v2`, which stay registered for reproducibility.

- **New prompts.** `rag-answer-v5` (multi-hop) leads with one plain sentence naming the top result,
  lists only the top 3–5 items, and closes with "The full ranking of K is in the table." The full
  ranking moves to the interface's Table and Chart tabs. Shares are written as percentages (the
  faithfulness check already accepts a value × 100 rounded to one or two decimals) and internal
  identifiers are forbidden. `rag-local-answer-v4` (local search) is summary-first prose with no
  `[step N]` references, because local context has no numbered steps. The evidence rules of
  `rag-answer-v4` are kept. `rag-global-v3` is unchanged.
- **Development check only** (19 kept development questions, auto mode, Qwen3.5-4B, graph
  `enriched-cb371912e308`; `reports/runs/WORK-2026-11-26-003/dev-eval-answer-v{4,5}.json`, local and
  ignored): faithfulness pass rate **0.9474 → 0.9474** (the one failure, `qa-v1-d017`, is the same
  global answer in both runs and comes from the unchanged global prompt); development scores are
  identical by hop class (1-hop 1.00, 2-hop 0.5057, 3-hop 0.80, global 0.75; these scores read the
  step rows, not the prose). Answer shape: mean bullets per answer **5.16 → 3.00** (maximum 20 → 8),
  mean words **62.8 → 54.6**, mean first-sentence length **293.6 → 154.9** characters. Latencies in
  these two runs mix LLM-cache hits and are not compared.
- **Demos re-cached.** The 7 scripted demos were re-recorded without the LLM cache on
  `enriched-cb371912e308` with `rag-answer-v5` / `rag-local-answer-v4`; all 7 pass the faithfulness
  check (demo-04 still asks which researcher is meant). `demo-cache.json` now records
  `graph_version`, `answer_prompt_version` and `local_answer_prompt_version`. A first v5 draft that
  shared the multi-hop prompt with local search failed demo-07 (`step reference 4 not in trace`),
  which is why local search has its own prompt.
