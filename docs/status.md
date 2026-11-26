# Current status

**Updated:** 2026-11-27 ([WORK-2026-11-26-003](work-log/2026-11-26-003-ui-redesign.md))
**Deadlines:** Track A report submitted 11 Nov 2026 (v4 frozen). Final exam (D042) due 20 Dec 2026.

## Phase checklist

- [x] **Frozen v4 release (D040):** `release-d3c788c3114a` in `neo4j-five-year` (Bolt 7689); unchanged.
- [x] **Enrichment & K1 model selection (E1–E4):** `enriched-cb371912e308` (graph v3) in `neo4j-enriched` (Bolt 7690). Team decision (2026-11-26): keep **Qwen3.5-4B**; Qwen3.5-9B is a parameter-scale reference only.
- [x] **Network analysis & GraphRAG (S1–S3, K2–K3):** `analysis-final-exam-v2`, `rag-v1` (228 reports), `qa-eval-v1` (69 test questions, final, unchanged), `k1-answer`; all figures AI-assessed.
- [x] **Local close-out & licences:** fallbacks, warm-up, re-cached demos, MIT + CC BY 4.0.
- [x] **Navigator UI redesign:** rebuilt on the approved mockup; summary-first answer prompts (`rag-answer-v5`, `rag-local-answer-v4`). Checks on 2026-11-27: `pytest` 796 passed / 1 skipped, backend 42/42, Navigator Playwright 11/11, v4 + contracts 54/54 (17 baselines regenerated for the new shell), build passed.
- [ ] **GitHub data release & deployment:** [`data-v1` draft](https://github.com/HSandz/scientific-network/releases/tag/untagged-f27c9b6883ddafe2147c) publish pending; hosted Navigator awaits approval.
- [ ] **Final deliverables (M5–M6):** arXiv report, slides, demo fallback video, Q&A sheet.

## Open items and next step

1. **Decide on organization attribution:** Ask's tools and the benchmark reference queries count papers through `AFFILIATED_WITH`→`AUTHORED`, not the per-paper triples (19 of 100 questions have that edge in their chain). Frozen scores unchanged; disclosed in the app and README.
2. **Hosted SLM & deployment:** approve hosting ([plan](../ops/azure/navigator-deployment.md)); first add the organization index to the artifact bundle and keep the single-page fallback for real paths.
3. **Live Ask:** 2 of 3 new questions passed the faithfulness check; the third was refused (`number 4.4 not in trace`).
4. **M5 & M6:** arXiv endorsement/submission, paper, slides, video, Q&A; publish `data-v1` after team review.

## Local run notes

Organization pages need `build_affiliation_index.py` (README quick start). Run the Navigator (7690) and v4 (7689) browser suites separately; the API allows 180 requests per minute per client.
