# Current status

**Updated:** 2026-11-26 ([WORK-2026-11-26-002](work-log/2026-11-26-002-final-non-report-fixes-release.md))
**Deadlines:** Track A report submitted 11 Nov 2026 (v4 frozen). Final exam (D042) due 20 Dec 2026.

## Phase checklist

- [x] **Frozen v4 release (D040):** `release-d3c788c3114a` loaded in `neo4j-five-year` (Bolt 7689); report and Playwright checks verified (46/46 after regenerating 3 local 7689 visual baselines).
- [x] **Enrichment & K1 model selection (E1–E4):** `enriched-cb371912e308` (graph v3) in `neo4j-enriched` (Bolt 7690). Team decision (2026-11-26): keep **Qwen3.5-4B** (4.66B); Qwen3.5-9B stays parameter-scale reference only.
- [x] **Network analysis & GraphRAG (S1–S3, K2–K3):** `analysis-final-exam-v2`, `rag-v1` (228 reports), `qa-eval-v1` (69 test questions, final, unchanged), and `k1-answer` (19 dev questions) complete; all figures AI-assessed.
- [x] **Local close-out & licences (WORK-2026-11-26-002):** on-demand N4 PPR + lift + RCA fallback (`rank`), multi-kind subject linking with implied kind & empty-step retry, startup warm-up (`~20.7 s` -> `~1.5 s` first event), `rag-global-v3` (`6/12` -> `0/12` map failures), human-readable prompt labels, mode-aware `/api/health`, deterministic `UnifiedEntityResolver.resolve`, 7 re-cached demos, MIT (`LICENSE`) + CC BY 4.0 (`LICENSE-DATA.md`), tracked abstract disclosure, and all test suites green (`pytest` 793 passed / 1 skipped, backend 37/37, Navigator Playwright 18/18, v4 Playwright 46/46).
- [ ] **GitHub data release & deployment:** `main` pushed; [`data-v1` draft release](https://github.com/HSandz/scientific-network/releases/tag/untagged-f27c9b6883ddafe2147c) created (`isDraft: true`, publish pending); hosted Navigator deployment awaits approval.
- [ ] **Final deliverables (M5–M6):** arXiv report, slides, demo fallback video, Q&A sheet.

## Open items and next step

1. **Hosted SLM & deployment:** approve hosting choice (`ops/azure/navigator-deployment.md`) before M5 arXiv submission.
2. **UI polish (non-blocking):** fix forum-tag SVG icons on the Ask page.
3. **M5 & M6:** secure arXiv endorsement/submission, finalize paper/slides/video/Q&A, publish `data-v1` draft release after team review.
