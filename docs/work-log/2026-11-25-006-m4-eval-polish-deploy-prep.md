# WORK-2026-11-25-006 — M4: M3 review fixes, QA benchmark evaluation, UI polish, and deployment prep

| Field | Value |
| --- | --- |
| Status | in_progress |
| Recorded | 2026-11-25 17:25 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-25 |
| Contributor | Agent execution session with the user |
| Related task | [WORK-2026-11-25-005](2026-11-25-005-m3-application-core.md) |
| Git state | `main` from `8e9d539`; untouched: ~15 line-ending CSVs, user's `docs/README.md`, untracked `docs/prompts/implement-final-exam-track-a.md` |

## Objective

Execute Milestone M4 of the Research Trend Navigator (`docs/final-exam/specification.md` §6.4–6.6):
1. **Phase 0**: Fix every M3 review finding on development questions and scripted demos only (never touching `split == "test"`).
2. **Phase 1**: Write and freeze `configs/qa-eval-v1.yaml` and the evaluation harness (`src/scientific_network/evaluation/qa_eval.py`) before any test question is run.
3. **Phase 2**: Run S1–S4 once on the 69 kept test questions, score factual accuracy, faithfulness, latency, AI-assessed citation validity, and AI-assessed global pairwise win rates, and write `reports/final-exam/qa-eval-v1/results.{json,md}`.
4. **Phase 3**: Polish the Navigator UI, complete tooltips/disclosures/About page benchmark results, split Playwright per-page assertions with chart verification, measure load times, and draft `docs/final-exam/demo-script-draft.md`.
5. **Phase 4**: Prepare artifact export and hosted-SLM backend config + documentation for deployment without deploying, paying, or publishing.

## Baseline before Phase 0 fixes (from M3 `reports/final-exam/rag-v1/dev-eval.json`)

- Kept development questions (`19/20`; `qa-v1-d002` dropped `empty_reference_result`):
  - Hop 1 (`n=4`): mean_score `0.8500`, faithfulness `4/4` (`1.0000`), mean_latency `5.518s`
  - Hop 2 (`n=6`): mean_score `0.6723`, faithfulness `6/6` (`1.0000`), mean_latency `7.131s`
  - Hop 3 (`n=5`): mean_score `0.6667`, faithfulness `5/5` (`1.0000`), mean_latency `7.372s`
  - Global (`n=4`): mean_score `1.0000`, faithfulness `4/4` (`1.0000`), mean_latency `19.465s`
  - Overall faithfulness under the old incomplete verifier: `19/19` (`100.0%`).
- Scripted demos (`demo-cache.json`): `demo-01` emitted `[paper:...]` placeholders and low-volume 0->1 orgs; `demo-02` stopped on step 1 (`$step1.ids` self-ref); `demo-03` failed faithfulness (`faithfulness_passed: False`); `demo-05` stopped on empty PPR lookup for `task:e8299f0a4fe25a12`.

## Changes and findings

### Phase 0 — M3 review fixes (development questions and scripted demos only; 0 test questions touched)

1. **Faithfulness verifier & prompt citations (`src/scientific_network/rag/answer.py`, `retrieval.py`, `tests/test_rag_engine.py`)**:
   - Updated `verify_answer_faithfulness` (documented rules in docstring): rejects placeholder/truncated citations (`[paper:...]`, `[...]`, ellipses/TBD/TODO inside brackets), requires every `paper:...` and entity ID in brackets or prose to exist verbatim in the trace, matches capitalized multi-word entity spans and list-item heads against trace/question entity names (including conjoined `X and Y` spans only when all parts appear in trace, plus documented generic prose allowlist), and checks numbers within `max(0.01, 0.005 * abs(a))` plus percentage equivalents.
   - Removed literal `[paper:...]` template examples from `_ANSWER_SYS` (`rag-answer-v3`), `rag-local-answer-v2`, and `rag-global-v2` (added 1 faithfulness retry in `global_search`).
   - Added unit tests covering placeholders, invented organizations, conjoined datasets (`Camelyon16 and TCGA-NSCLC` vs `FakeDataset`), valid answers within numeric tolerance, and step-aware compaction.
2. **Flagship share-growth answer & step-aware compaction (`configs/rag-v1.yaml`, `rag/tools.py`, `rag/answer.py`, `tests/test_rag_tools.py`)**:
   - Added `share_growth: {min_post_total_papers: 10, min_post_subject_papers: 2, max_rows_in_prompt: 15}` to `configs/rag-v1.yaml` and enforced it in `RAGToolset.aggregate(..., metric="share_growth")` (37 of 64 Tsinghua collaborators qualify vs 27 excluded below threshold), emitting `pre_papers`/`post_papers` (`k of n`), shares, threshold notes, and `paper_ids[:3]`.
   - Fixed `_compact_trace_for_prompt` to strip noisy internal edge metadata keys and prioritize keeping the final step intact within the 10,500-char slot budget instead of blindly slicing JSON.
3. **Trends & chart rendering (`EChartBox.tsx`, `EChartRuntime.tsx`, Navigator pages, `navigator.spec.ts`)**:
   - Added synchronous mount viewport visibility checks in `EChartRuntime` and `EChartBox`, registered `ScatterChart` (enabling the N1 log-log degree distribution chart and dynamic `C` axis on `NetworkSciencePage`), switched chart palettes to theme-aware hex colors, and added DOM telemetry (`data-chart-active`, `data-chart-rendered`, `data-chart-series-count`, `data-chart-point-count`) verified in real Chromium canvas checks (`nonZeroPixels > 100`).
4. **Header graph version & v4 Explorer compatibility (`TopHeader.tsx`, `EnrichedExplorerBar.tsx`, `App.tsx`)**:
   - Header badge shows `enriched-cb371912e308` on Navigator views and `release-d3c788c3114a` on Explorer views. Kept v4 Explorer header single-row (`<= 60px` on `390x844` mobile) and `+ Enriched v5` inline (`16px` height) so desktop Sigma canvas remains exact `1168x662`; moved secondary Navigator strip onto Navigator views with a header `Navigator` button and mobile menu entry.
5. **Progressive SSE streaming (`rag/executor.py`, `rag/answer.py`, `navigator_service.py`, `AskPage.tsx`)**:
   - Refactored `iter_execute_plan` and `stream_ask` to yield progressive events (`stage(parsing)` -> `parsed` -> `stage(planning)` -> `plan` -> per-step `step`+`subgraph` -> `synthesizing` -> `token` -> `citations` -> `done`) rendered incrementally in `AskPage.tsx`.
6. **Demo reliability (`rag/planner.py`, `rag/tools.py`, `rag/dev_eval.py`, `demo-cache.json`)**:
   - Fixed `demo-02` planner rule (`trend` tool, `rag-plan-v4`), `demo-03` co-occurrence filter, and `demo-05` task-to-topic PPR lookup (`task:e8299f0a4fe25a12` -> `Causal inference` -> `topic:causal-inference`). Re-cached all 7 scripted demos after fixes (`demo-01`..`demo-07` all succeed cleanly; `demo-04` returns `needs_disambiguation`; the 6 answer demos all pass `verify_answer_faithfulness`).
7. **Data publication & attribution compliance (`.gitignore`, `rag/index.py`, `entity-descriptions.json`, `navigator_service.py`)**:
   - Moved `reports/final-exam/rag-v1/chunks.json` (4.8 MB abstract sentences) to ignored `data/processed/rag-v1/chunks.json` and added `reports/final-exam/rag-v*/chunks.json` to `.gitignore`.
   - Patched all 4,316 records in `entity-descriptions.json` with explicit `wikipedia_url`, `wikipedia_revision_id`, `license: "CC BY-SA 4.0"`, and attribution for all 231 Wikipedia entries plus `generation_method`/`model` tags for 251 LLM and 3,834 template descriptions (`tests/test_rag_index_retrieval.py` regression test added); surfaced attribution links on `Node360Page`, `GroupsPage`, and `SubjectPage`.
8. **Layout collision & Playwright refactor (`AskPage.tsx`, `CommunitiesPage.tsx`, `navigator.spec.ts`)**:
   - Upgraded `AskPage` subgraph to collision-relaxed concentric hop rings with hover/focus labeling when crowded (>10 nodes), added collision spacing on `CommunitiesPage` super-nodes, and split `navigator.spec.ts` into 9 per-page tests with canvas render assertions.

#### Development-only evaluation before vs after Phase 0 fixes (`split == "development"`, 19 kept questions)

| Split / Metric | Before Phase 0 (M3, cached) | After Phase 0 (cached) | After Phase 0 (uncached LLM, `--no-llm-cache`) |
| --- | --- | --- | --- |
| Hop 1 (`n=4`) score / faith / tot latency | `0.8500` / `4/4` / `5.518s` | `1.0000` / `4/4` / `3.053s` | `1.0000` / `4/4` / `5.394s` (`first_event 1.465s`, `first_step 3.450s`) |
| Hop 2 (`n=6`) score / faith / tot latency | `0.6723` / `6/6` / `7.131s` | `0.5057` / `6/6` / `5.531s` | `0.5057` / `6/6` / `8.228s` (`first_event 0.649s`, `first_step 2.780s`) |
| Hop 3 (`n=5`) score / faith / tot latency | `0.6667` / `5/5` / `7.372s` | `0.8000` / `5/5` / `3.998s` | `0.6000` / `5/5` / `6.776s` (`first_event 0.843s`, `first_step 3.039s`) |
| Global (`n=4`) score / faith / tot latency | `1.0000` / `4/4` / `19.465s` | `1.0000` / `4/4` / `14.391s` | `1.0000` / `4/4` / `19.483s` (`first_event 0.930s`, `first_step 16.207s`) |
| Overall faithfulness | `19/19` *(incomplete verifier)* | `19/19` (`100.0%`, full verifier) | `19/19` (`100.0%`, full verifier) |

Uncached scripted demo streaming latencies (`--no-llm-cache`, `sn-llm` + `neo4j-enriched` on 7690):
- `demo-01`: first_event `2.025s`, first_step `4.855s`, total `15.625s`, faithful `True`
- `demo-02`: first_event `0.572s`, first_step `1.869s`, total `12.647s`, faithful `True`
- `demo-03`: first_event `0.760s`, first_step `3.651s`, total `14.459s`, faithful `True`
- `demo-04`: first_event `0.986s`, total `0.986s` (`needs_disambiguation`)
- `demo-05`: first_event `0.711s`, first_step `2.183s`, total `11.051s`, faithful `True`
- `demo-06` (`global` map-reduce): first_event `1.352s`, first_step/total `37.568s`, faithful `True`
- `demo-07` (`local` search): first_event `1.082s`, first_step `2.273s`, total `6.358s`, faithful `True`
Peak container memory under demo services (`sn-llm` + `neo4j-enriched`, `docker stats --no-stream`): `sn-llm` `7.444 GiB`, `neo4j-enriched` `657.4 MiB` (~`8.10 GiB` combined of `11.68 GiB`).

### Phase 1 — Frozen Evaluation Protocol (`configs/qa-eval-v1.yaml`, `src/scientific_network/evaluation/qa_eval.py`, `tests/test_qa_eval.py`)

Committed BEFORE running any `split == "test"` question (run-once policy):
- **Anchors**: Phase 0 commit `433903ddde134e6acd9a37b534646b601f9cac5e`; graph `enriched-cb371912e308` (`37ee8c59d8245d452e42575b7afbb13808b5f835d51c9ee838bd5581434633e3`); frozen `references-v1.jsonl` (`d2fcf2c0cba2fae7e5cfa7f6dd030971a9083604081ea4bebdb93ddf424b2c19`, 69 kept test items: hop 1 = 14, hop 2 = 22, hop 3 = 18, global = 15).
- **Model & decoding (identical across S1–S4)**: `qwen3.5-4b-q4_k_m` (`Qwen/Qwen3.5-4B` rev `e87f176479d0855a907a41277aca2f8ee7a09523`), `http://127.0.0.1:8080/v1`, `temperature=0.0`, `seed=0`, `enable_thinking=false`, dedicated fresh cache dir `data/interim/qa-eval-v1/llm-cache` so Phase 2 records uncached latency.
- **Systems**: `S1_slm_only` (`eval-s1-v1`, no retrieval), `S2_vector_rag` (`eval-s2-v1`, top-10 `abstract_chunk` cosine matches), `S3_graphrag` (`local_search` for hops 1–3 with `rag-local-answer-v2`; `global_search` for global with `rag-global-v2`), `S4_multihop` (`stream_ask(..., mode="auto")` with `rag-parse-v1`, `rag-plan-v4`, `rag-answer-v3`, `rag-global-v2`).
- **Factual scoring & faithfulness**: Unified text-to-graph-ID entity resolver applied identically to S1–S4 answer texts (`graph ID -> exact/alias normalized name -> all-MiniLM-L6-v2 cosine >= 0.80`), restricted to expected reference entity types; set-F1 (`set`, `ranked_list`) and integer exact match (`number`, `year`, `abs_tol=0`), reported with seeded percentile bootstrap 95% CIs (`seed=20261125`, `n=2000`) and 95% Wilson CIs. `verify_answer_faithfulness` applied to S2/S3/S4 (S1 `not_applicable`).
- **AI-assessed citation validity & global pairwise**: Deterministic citation pair sampling (`seed=20261125`, stratified max 25/system; full title+abstract written ONLY to ignored `reports/runs/WORK-2026-11-25-006/eval/citation-packet.jsonl`; tracked manifest without abstracts in `reports/final-exam/qa-eval-v1/citation-sample-manifest.json`); 15 global questions × 6 pairs × AB+BA = 180 blind pairwise items (`seed=20261125`).
- **Evaluator CLI smoke tests & approved adjudicator fallback**:
  - `A`: `/home/san/.local/bin/claude` (`2.1.332`, `claude-opus-5-5`, `-p --output-format json`) — passed (`"OK"`).
  - `B`: `/home/san/.local/bin/codex` (`0.172.0`, `gpt-6.2-sol` via `9router`, `exec --skip-git-repo-check`) — passed (`"OK"`).
  - `gemini` CLI (`/home/linuxbrew/.linuxbrew/bin/gemini` `0.26.0`, `-p -o json`) failed with exit 41 (unauthenticated). Per M2 precedent (`WORK-2026-11-25-003`), `C` uses a **fresh isolated `codex exec` session (`gpt-6.2-sol` via `9router`)** on A≠B disagreements — different family from A (spec §6.6), explicitly disclosed as sharing B's model family (not independent of B).

### Phase 2 — Frozen Test Benchmark Evaluation (Run ONCE on 69 kept test questions; zero tuning)

- **Pre-judging freeze (`89c120f`)**: Committed `raw-outputs.jsonl` (276 rows = 69 × 4), `factual-scores.json`, `citation-sample-manifest.json` (`75` sampled items, SHA-256 `46e563e1...`, **0 raw abstracts**), and `pairwise-manifest.json` (`180` blind AB+BA items, SHA-256 `e0921359...`) before invoking A/B/C.
- **Factual accuracy (54 factual test questions, unified entity resolver, 95% bootstrap CI)**:
  - `S1_slm_only`: `0.1242` `[0.0787, 0.1759]` (Hop 1 `0.0262`, Hop 2 `0.1929`, Hop 3 `0.1165`), mean latency `4.676s`
  - `S2_vector_rag`: `0.0547` `[0.0200, 0.0993]` (Hop 1 `0.0000`, Hop 2 `0.1250`, Hop 3 `0.0112`), mean first-event `2.065s`, mean total `7.030s`
  - `S3_graphrag`: `0.1630` `[0.0919, 0.2369]` (Hop 1 `0.2571`, Hop 2 `0.1474`, Hop 3 `0.1088`), mean first-event `3.648s`, mean total `10.595s`
  - `S4_multihop`: **`0.4273`** `[0.3132, 0.5403]` (Hop 1 `0.4190`, Hop 2 `0.2532`, Hop 3 **`0.6466`**), mean first-event **`1.652s`**, mean total `9.780s`
- **Automatic faithfulness (all 69 questions, 95% Wilson CI)**:
  - `S1_slm_only`: N/A (`0` citations emitted); `S2`: `49/69` (`0.7101` `[0.5943, 0.8038]`); `S3`: `59/69` (`0.8551` `[0.7534, 0.9193]`); `S4`: **`60/69`** (`0.8696` `[0.7703, 0.9298]`).
- **AI-assessed citation validity (25 seeded pairs/system for S2–S4; A–B Cohen's kappa `0.6199`, `15` adjudicated by C)**:
  - `S2_vector_rag`: **`23/25`** (`0.9200` `[0.7503, 0.9778]`); `S3_graphrag`: `16/25` (`0.6400` `[0.4452, 0.7975]`); `S4_multihop`: `9/25` (`0.3600` `[0.2025, 0.5548]`). *Interpretation*: S2 quotes directly from abstract chunks, whereas S4 attaches graph-level `paper_ids` returned alongside structured aggregation/neighbor counts without reading those papers' abstracts, so single-paper abstracts frequently do not mention corpus-wide aggregates.
- **AI-assessed global pairwise comparison (15 global questions × 6 pairs × AB+BA = 180 blind items; A–B kappa `0.7988`, `26` adjudicated by C, `4/90` position-inconsistent pairs)**:
  - `S2_vector_rag`: **`72/0/18`** (`0.8000`, position-consistent `35/45 = 0.7778`)
  - `S4_multihop`: `47/14/29` (`0.5222`, consistent `22/45 = 0.4889`)
  - `S3_graphrag`: `44/14/32` (`0.4889`, consistent `21/45 = 0.4667`)
  - `S1_slm_only`: `3/0/87` (`0.0333`, consistent `1/45 = 0.0222`)
- **Latency cache disclosure**: Across `483` logged test LLM calls (`llm-calls.jsonl`), `16` calls hit the `qa-eval-v1` cache because on the 15 global questions `S4_multihop` routed `7` questions to `global` (reusing S3's global map-reduce cache from the same question) and `8` questions to `multi_hop`, explaining S4's lower mean global latency (`20.778s`, first-event `2.912s`) vs S3's uncached global map-reduce (`48.275s`).

### Phase 3 — UI Polish, About Benchmark Results, Load Timing & Demo Script (§6.4–6.5)

- **Benchmark results in About Data (`backend/config.py`, `navigator_service.py`, `AboutDataPage.tsx`)**: Exposed `reports/final-exam/qa-eval-v1/results.json` via `get_about_data()` and rendered a full QA Benchmark Comparison panel (factual S1–S4 table by hop class + 95% bootstrap CIs, automatic faithfulness + AI-assessed citation validity with 95% Wilson CIs & κ=`0.6199`, AI-assessed global pairwise table & κ=`0.7988`, and all required AI-assessed / evaluator-independence / coverage disclosures).
- **Metric tooltips & `"AI-generated from graph data"` badges**: Audited and completed `MetricTooltip` definitions across `TrendsPage`, `SubjectPage`, `GroupsPage`, `CommunitiesPage`, `NetworkSciencePage`, `Node360Page`, `AskPage`, and `AboutDataPage`, and ensured non-Wikipedia generated entity/community descriptions and Ask answers display `"AI-generated from graph data"`.
- **Local dashboard load timing (`navigator.spec.ts` Test 10 -> `load-timings.json`)**: Precomputed routes rendered in `< 2000ms` (`trends: 129ms`, `groups: 1541ms`, `communities: 66ms`, `network: 65ms`).
- **Demo script draft (`docs/final-exam/demo-script-draft.md`)**: 5–7 minute walkthrough using strictly the 7 cached scripted demos (`demo-01`..`demo-07`, disjoint from test) plus live-demo cached fallback plan.

### Phase 4 — Deployment Preparation (Prepared Only; NOT Deployed / Paid / Published)

- **Hosted OpenAI-compatible SLM config & graceful cached-demo fallback (`backend/config.py`, `navigator_service.py`, `tests/test_navigator_api.py`)**:
  - Added optional env vars `EXPLORER_LLM_BASE_URL`, `EXPLORER_LLM_MODEL`, `EXPLORER_LLM_PROVIDER`, and `EXPLORER_LLM_API_KEY_ENV` (key resolved only from host environment variable, never stored or echoed in `/api/about-data`).
  - Added graceful `LLMError` fallback in `ask()` and `stream_ask_events()`: matches scripted demos from `demo-cache.json` (`fallback_reason="llm_unavailable_served_cached_demo"`) and returns structured HTTP 200 `status="llm_unavailable"` for custom uncached questions instead of HTTP 500.
- **Artifact export (`ops/azure/scripts/prepare-navigator-artifacts.py`, `tests/test_navigator_artifacts.py`)**:
  - Verified clean preview bundle into ignored `reports/runs/WORK-2026-11-25-006/navigator-artifacts-preview/`: `47` files, `52,363,711` bytes (`49.94 MiB`, including `vectors.sqlite` with `16,544` rows and all `analysis-v2/` subdirs), explicitly excluding `chunks.json`.
- **Deployment docs (`ops/azure/navigator-deployment.md`, `ops/azure/README.md`, `ops/azure/.env.example`)**:
  - Documented single-Neo4j (`enriched-cb371912e308`) VM architecture, artifact bundle mount, deployment steps, and hosted SLM cost/provider estimates (`$0` cached-demo-only vs ~`$0.10–$2.00` serverless API vs dedicated endpoint). Awaiting explicit user choice and approval before deploying.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| Start state check (`git status`, `docker ps`, `sha256sum data/processed/enriched-graph-v3/graph.json`) | passed; `enriched-cb371912e308` (`37ee8c59d8245d45...`), `sn-llm` + `neo4j-enriched` healthy | `8e9d539` |
| `uv run pytest -q` (after Phase 0 fixes) | exit 0; `764 passed, 1 skipped` (`28.30s`) | `tests/test_rag_*.py` |
| `EXPLORER_NEO4J_URI=bolt://127.0.0.1:7689 ... pytest apps/research-explorer/backend/tests -v` | exit 0; `35 passed, 0 skipped` (`16.42s`) | live Bolt 7689 + unit/navigator/prod |
| `npm --prefix apps/research-explorer/frontend run build` | exit 0; built in `3.87s` | `apps/research-explorer/frontend/dist/` |
| Contracts Playwright (`playwright.contracts.config.ts`) | exit 0; `8 passed` (`698ms`) | — |
| v4 Explorer Playwright on Bolt 7689 (`dashboard`, `explorer`, `analytics-layout`, `focus-labels`, `reproducibility`, `visual`) | `44/46` functional/layout checks passed; 2 pre-existing Nov-11 PNG baseline snapshot diffs (`focus-labels:141` `hover-neighborhood.png` degree `26` vs Nov-11 `22` at exact `1168x662`; `visual:30` `graph-overview.png` 3% diff from M3/M4 `Navigator`/`+ Enriched v5` buttons) — v4 snapshots untouched | `/tmp/playwright-test-results/` |
| Navigator Playwright on Bolt 7690 (`tests/navigator.spec.ts`) | exit 0; `9 passed` (`37.1s`), all charts pixel-verified | `reports/runs/WORK-2026-11-25-006/screenshots-phase0/` |
| `uv run python -m scientific_network.rag.dev_eval --config configs/rag-v1.yaml` (+ uncached `--no-llm-cache`) | exit 0; `19/19` kept dev faithful, `7/7` demos cached/timed | `reports/final-exam/rag-v1/{dev-eval,demo-cache}.json`, ignored `reports/runs/WORK-2026-11-25-006/uncached-dev-latency.json` |
| Phase 1 evaluator CLI smoke tests (`claude -p`, `codex exec`, `gemini -p`) | `claude` & `codex` exit 0 (`"OK"`); `gemini` exit 41 (unauthenticated) | frozen fallback in `configs/qa-eval-v1.yaml` |
| `uv run pytest -q tests/test_qa_eval.py` & `uv run pytest -q` (Phase 1 harness) | exit 0; `4 passed` (`0.51s`); `768 passed, 1 skipped` (`26.94s`) | `tests/test_qa_eval.py`, `qa_eval.py` |
| `qa_eval.py run-systems` (Phase 2 run-once on 69 kept test questions × 4 systems) | exit 0; `276` rows written | `reports/final-exam/qa-eval-v1/raw-outputs.jsonl`, `reports/runs/WORK-2026-11-25-006/eval/llm-calls.jsonl` |
| `qa_eval.py score-factual` + `prepare-judging` | exit 0; `276` scored, `75` citation pairs, `180` blind pairwise items (0 abstracts in manifest) | `reports/final-exam/qa-eval-v1/{factual-scores,citation-sample-manifest,pairwise-manifest}.json` (`89c120f`) |
| Isolated AI judging (`run_judges.py`: A `claude-opus-5-5`, B `codex exec`, C `codex exec`) + `qa_eval.py aggregate-results` | exit 0; `75` citation (`15` disputes), `180` pairwise (`26` disputes) | `reports/final-exam/qa-eval-v1/{results.json,results.md,evaluator-evidence.json}` |

## Decisions

- Resolved M3 review findings on dev/demo scope without modifying frozen v4 (`release-d3c788c3114a`) or frozen v4 PNG golden baselines.
- Approved fresh isolated `codex exec` (`gpt-6.2-sol` via `9router`) as adjudicator C after `gemini` CLI failed with exit 41, with explicit non-independence disclosure in `configs/qa-eval-v1.yaml`, work log, and `results.md`.
- Kept Phase 2 strictly run-once (`831712a` -> `89c120f` -> Phase 2b) with zero tuning after test execution.

## Open issues and limitations

- Uncached `global` mode (`demo-06` `37.6s`, S3 test global `48.3s`) exceeds the ~30s total latency guideline; uncached first-event latency (`0.57s–2.03s` demos, `1.65s` S4 factual test) meets the ~5s target.
- Adjudicator C shares B's model family (`gpt-6.2-sol`), disclosed as non-independent of B.
- Citation validity and global pairwise ratings are AI-assessed; Wilson/bootstrap intervals exclude evaluator error. S4 exhibits lower AI-assessed single-abstract citation validity (`36.0%`) than S2 (`92.0%`) despite far higher multi-hop factual accuracy (`0.4273` vs `0.0547`) because graph tool rows attach paper IDs without abstract text.

## Next step

Hand back for plan review of Phase 2 results, then execute Phase 3 (UI polish §6.4–6.5, About page updates, Playwright screenshots, demo script draft) and Phase 4 (deployment preparation).

## Corrections

None.
