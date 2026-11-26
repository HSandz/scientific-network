# WORK-2026-11-26-002 — Final non-report fixes, user decisions, push & draft data release

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-26 21:00 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-26 |
| Contributor | Agent execution session with the user |
| Related task | [WORK-2026-11-26-001](2026-11-26-001-non-report-closeout.md) |
| Git state | `main` from `d6114f5` (commits `ed9cc47`, `5fd7da7`, `2a5c131`, `46b51d4` added locally; untouched: ~15 line-ending CSVs, user's `docs/README.md`, untracked `docs/prompts/implement-final-exam-track-a.md`) |

## Objective

Record the user's four 2026-11-26 decisions, fix `"Which groups work on X"` across every subject, resolve Ask cold-start / global map truncation / raw prompt keys / mode-aware `/api/health` / deterministic entity resolution, re-cache the 7 demos, regenerate local `neo4j-five-year` (7689) v4 visual baselines, verify all suites, scan `origin/main..HEAD` for secrets and abstract leaks, push `main`, and create the draft `data-v1` GitHub release.

## Changes and findings

1. **User decisions & licences (`ed9cc47`):**
   - Recorded 2026-11-26 [D042 amendment](../decisions.md) across K1 (keep Qwen3.5-4B 4.66B; Qwen3.5-9B 9.65B remains parameter-scale reference only), tracked abstract audit evidence (keep 50 existing v1–v4 files bound by frozen receipts, forbid new commits of verbatim abstracts, exclude abstracts from data release, no history rewrite), licences (MIT for code, CC BY 4.0 for project data), and push + draft release.
   - Added dated K1 team-decision lines to `reports/final-exam/k1-answer/results.md`, `reports/enrichment-v1/k1-model-selection.md`, and `docs/final-exam/specification.md` §6.1.
   - Added dated abstract-evidence notes to `docs/source-policy.md` and `reports/final-exam/repo-hygiene-2026-11-26.md`.
   - Created `LICENSE` (MIT, `Copyright (c) 2026 Research Trend Navigator contributors`) and `LICENSE-DATA.md` (CC BY 4.0 + third-party terms); updated `ops/release/build-data-release.py` to bundle `LICENSE-DATA.md` and update `README.md`/`LICENSES.md`.
2. **"Which groups work on X" for every subject (`5fd7da7`):**
   - Added `src/scientific_network/rag/on_demand_ppr.py` (`OnDemandPPRCompute`, N4 damping 0.85, `MIN_SUBJECT_PAPERS={"Organization": 3, "Researcher": 2}`, `<5 -> >=1` fallback, in-memory cache). Verified exact match on `topic:causal-inference` against `personalized-pagerank.json` (top 3: University of Lübeck 22.1088, Yokohama National University 16.8449, University of South Australia 11.9827).
   - Updated `RAGToolset.rank` (`tools.py`): precomputed `analysis-final-exam-v2` -> cached on-demand PPR -> RCA fallback (`trends/group-interest.csv`), reporting method (`source_kind`) in trace.
   - Updated `link_entities` (`planner.py`), `iter_execute_plan` (`executor.py`), and `answer.py`: multi-kind subject preference from implied kind or most papers, `kind_choices` returned for UI, and single automatic empty-step retry with the next alternative candidate.
   - Exposed PPR method provenance and `ask-kind-choice` buttons in `navigator_service.py`, `SubjectPage.tsx`, `GroupsPage.tsx`, `AskPage.tsx`, and `types/navigator.ts`.
3. **Ask robustness, polish, determinism & 7 demos (`2a5c131`):**
   - **Startup warm-up:** `NavigatorService.warmup()` + `backend/main.py` lifespan preload JSON artifacts, SQLite vectors, embedder (`warmup` call), Neo4j check, and a 4-token LLM ping. First live question latency on fresh backend (port 8001, `7690`/`8080`): before `20.696 s` first non-status (`parsed`) event / `26.712 s` total (`cold-start-before.json`); after `13.333 s` startup warmup, first non-status event `1.487 s` / `8.799 s` total (`cold-start-after.json`).
   - **Global map truncation fix:** upgraded `rag-global-v2` -> `rag-global-v3` (`retrieval.py`: `GLOBAL_MAP_SCHEMA` `maxItems: 4`, `claim.maxLength: 240`, `paper_ids.maxItems: 3`, `key_findings[:4]`, `map_max_tokens=1024`, `map_stats` tracking). On the 4 kept dev global questions (`qa-v1-d017`..`d020`, uncached): before `6/12` map calls failed (`0.5`, all truncated), mean latency `44.581 s` (`max 53.598 s`, `global-before.json`); after `0/12` map calls failed (`0.0`), mean latency `26.735 s` (`max 30.886 s`, `global-after.json`), 12 points extracted on all 4. Added dated product-change note to `reports/final-exam/qa-eval-v1/results.md` (69 test questions untouched/not re-run).
   - **Human-readable trace labels & answer prompt (`answer.py`):** mapped raw column keys (e.g. `share_delta` -> `share change`) in `_compact_trace_for_prompt` (`_ANSWER_SYS_V4`) while preserving numerical faithfulness matching.
   - **Mode-aware `/api/health`:** `backend/config.py`, `models/schemas.py`, `neo4j_repo.py`, `explorer_service.py`, `frontend/src/types/explorer.ts` check enriched counts excluding RAG index nodes (reported in `rag_index_nodes`) on 7690 (`status: "ok"`, `database_verified: true`, `total_nodes: 50144`, `total_edges: 242048`, `rag_index_total_nodes: 16544`) vs v4 counts on 7689 (`total_nodes: 47875`, `total_edges: 225731`). Before fix on 7690: `"degraded"`, `database_verified: false`.
   - **Scorer determinism (`qa_eval.py`):** sorted iteration and stable `(len(candidates), str(c.get("id", "")), c.get("id", ""))` tie-break in `UnifiedEntityResolver.resolve` (with unit test; `qa-eval-v1` and `k1-answer` scores unchanged).
   - **Re-cached 7 scripted demos (`dev_eval --demos-only`):** `demo-01`..`demo-07` updated; 6/6 answer demos `faithful=True`, `has_raw=False`, `inline_paper=False` (`demo-04` returns `status=needs_disambiguation`, `faithful=True`); `demo-06` `0/3` map failures.
4. **Local 7689 v4 visual baselines (`46b51d4`):**
   - Stopped `sn-llm` + `neo4j-enriched`; verified `neo4j-five-year` (7689) `/api/health` (`release-d3c788c3114a`).
   - Regenerated `hover-neighborhood-chromium-linux.png`, `graph-overview-chromium-linux.png`, and `graph-close-chromium-linux.png` (previously masked when `graph-overview` failed earlier in `visual.spec.ts:33`). Causes: (1) local 7689 sampled overview has 108 nodes / 170 edges vs 110 / 166 from the 11 Nov production proxy; (2) header now includes `Navigator` and `+ Enriched v5` buttons; (3) sidebar shows 12 Nov help text (`19f82a1`). All 46 v4 Playwright specs pass.
5. **Docs & status updates:** updated `README.md`, `docs/final-exam/specification.md` §9 (plus typo fix `supports` -> `support`), `docs/status.md`, and `docs/work-log/README.md`.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| Step 2 baselines (`7690`/`8080`, `8001`) | exit 0; `/api/health` degraded; first event `20.696 s` (`26.712 s` total); global `6/12` map fail, `44.581 s` mean | `reports/runs/WORK-2026-11-26-002/{cold-start-before,global-before}.json` |
| Step 3 specialization unit tests (`pytest`) | `13 passed`, exit 0 | `tests/unit/test_rag_tools.py`, `test_rag_engine.py`, `backend/tests/test_navigator_api.py` |
| Step 3 live specialization probes (`dev`/new only) | exit 0; federated learning `method:Q50818671` `on_demand_ppr` 15 rows (`faithful=True`), clustering multi-kind `most_papers` 26 + `kind_choices` (`faithful=True`), Mamba / KG completion / ScanNet Dataset (`faithful=True`) | `reports/runs/WORK-2026-11-26-002/specialization-live.json` |
| Step 4 targeted tests (`pytest`) | `24 passed`, exit 0 | `test_rag_index_retrieval.py`, `test_rag_engine.py`, `test_qa_eval.py`, `backend/tests/test_navigator_api.py` |
| Step 4 after-fix measurements (`7690`/`8080`, `8001`) | exit 0; `/api/health` `ok`; first event `1.487 s` (`8.799 s` total); global `0/12` map fail, `26.735 s` mean; 7 demos `faithful=True` | `reports/runs/WORK-2026-11-26-002/{cold-start-after,global-after,demos-check}.json` |
| Full repo suite `uv run pytest -q` | `793 passed, 1 skipped` (`27.46s`), exit 0 | `reports/runs/WORK-2026-11-26-002/pytest-full.log` |
| Frontend build (`npm --prefix apps/research-explorer/frontend run build`) | exit 0 (`4.62s`) | `reports/runs/WORK-2026-11-26-002/frontend-build.log` |
| Navigator Playwright (`tests/navigator.spec.ts tests/contracts.spec.ts`, `7690`/`8080`, `8001`/`5175`) | `18 passed` (`36.0s`), exit 0 | `reports/runs/WORK-2026-11-26-002/playwright-navigator.log` |
| Backend suite (`EXPLORER_NEO4J_URI=bolt://127.0.0.1:7689 uv run pytest -q apps/research-explorer/backend/tests`) | `37 passed` (`47.59s`), exit 0 | `reports/runs/WORK-2026-11-26-002/v4/backend-tests.log` |
| Full v4 Playwright (all 6 specs on `7689`, `8001`/`5175`) | `46 passed` (`2.8m`), exit 0 | `reports/runs/WORK-2026-11-26-002/v4/playwright-v4.log` |
| Final secrets & abstract scan (`origin/main..HEAD`, `d6114f5..HEAD`) | exit 0; `0` secret pattern / `.env` hits (`14,859` added lines); `0` abstract-shingle hits in `d6114f5..HEAD` (`250,055` 10-word shingles; 2 prior hits in pre-existing commits `e257a8e`/`dcdfcd8`) | `git log origin/main..HEAD -p` |
| Push `main` & rebuild `data-v1` bundle (`72fc49e`) | exit 0 (`e572055..72fc49e`); 74 files, `57,521,321` B, `14,222` excerpts + `6` desc redacted, `0` shingle hits | `reports/runs/WORK-2026-11-26-002/data-release/` |
| Create GitHub draft release `data-v1` & verify | exit 0 (`isDraft: true`, `tagName: "data-v1"`, `MANIFEST.json` + `.tar.gz` uploaded) | `https://github.com/HSandz/scientific-network/releases/tag/untagged-f27c9b6883ddafe2147c` |

## Decisions

- [D042 amendment, 2026-11-26](../decisions.md#d042-amendment--k1-model-decision-tracked-abstract-evidence-licences-and-draft-data-release-2026-11-26): K1 keeps Qwen3.5-4B (9B reference only); 50 tracked v1–v4 audit/review files accepted & documented; MIT (`LICENSE`) + CC BY 4.0 (`LICENSE-DATA.md`); push `main` and create `data-v1` draft release.

## Open issues and limitations

- Hosted SLM / deployment (`ops/azure/navigator-deployment.md`), forum SVG icons on Ask, arXiv endorsement, M5 paper, and M6 slides/video/Q&A remain open outside this task.
- All quality figures (E4, K1, K3) remain AI-assessed; frozen `qa-eval-v1` and `k1-answer` tables are unchanged.

## Next step

Complete the remaining M5–M6 deliverables (hosted deployment approval, arXiv report, slides, demo video, Q&A sheet) and publish the `data-v1` draft release after team review.

## Corrections

None.
