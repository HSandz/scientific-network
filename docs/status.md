# Current project status

Updated: **2026-11-26T04:20:00+07:00**. Phase: **final exam**, decision
[D042](decisions.md#d042--final-exam-phase-research-trend-application-on-an-enriched-graph-2026-11-23),
due **20 December 2026, 23:59**. Specification: [docs/final-exam/](final-exam/README.md).
Latest: [WORK-2026-11-26-001](work-log/2026-11-26-001-non-report-closeout.md) (non-report close-out).
Documentation index: [docs/README.md](README.md).

## Final exam checklist (milestones in specification §8)

- [x] Requirements recorded, interpreted and traced; specification drafted (needs team review).
- [x] M0 set-up: splits and QA text frozen, LLM client, K1 chose Qwen3.5-4B and GLiNER-Relex on dev ([report](../reports/enrichment-v1/k1-model-selection.md)).
- [x] M1 enrichment (`enriched-cb371912e308` v3 on Bolt 7690): 50,144 nodes, 242,048 edges; E4 v3 AI-assessed ([quality](../reports/enrichment-v3/quality.md)).
- [x] M2 network analysis ([v2](../reports/final-exam/analysis-v2/README.md)): small world holds for N1, N2, N4; PageRank and lift PPR; Leiden communities; trends.
- [x] M3 application core: 9-tool layer, GraphRAG `rag-v1`, FastAPI and the Navigator pages.
- [x] M4 QA benchmark ([results](../reports/final-exam/qa-eval-v1/results.md)), UI polish, deployment prepared (not deployed).
- [x] Non-report close-out (2026-11-26): K1 answer arm ([results](../reports/final-exam/k1-answer/results.md)), citation labelling, supplementary literature-supported precision, v4 Explorer cause found, hygiene scan ([report](../reports/final-exam/repo-hygiene-2026-11-26.md)), local data-release bundle, README and spec §9 ticked.
- [ ] M5 arXiv report submitted by 15 December.
- [ ] M6 slides, demo script, fallback video, Q&A sheet; final resubmission.

## Carried over and active disclosures

- Production v4 graph `release-d3c788c3114a` (Bolt 7689) stays frozen.
- Quality figures, citation validity, pairwise and supplementary precision and GraphRAG summaries are
  AI-assessed or AI-generated; intervals exclude evaluator error. Adjudicator C shares B's model
  family (the `gemini` CLI is unauthenticated).
- The qa-eval-v1 factual scorer depends on `PYTHONHASHSEED` (spread reported; ranking unchanged).
- The product's citation labelling changed after qa-eval-v1 (dated note in its results).
- Port 8080 is taken by an unrelated local `bifrost` container: run the LLM with `LLM_PORT=8081`.
- Run Navigator Playwright (7690) and v4 Playwright (7689) with separate backends; the v4 baseline
  specs now refuse a backend that is not on the verified v4 graph.

## Open decisions for the user

1. **K1:** the reference Qwen3.5-9B (9.65B) beats the 4B by +0.13 on development answer accuracy
   (meets the §6.1 margin). Adopt it as the "9B" model (D042 amendment) or keep the 4B?
2. **v4 baselines:** `graph-overview.png` and `hover-neighborhood.png` were captured against the
   production API (110/166 nodes/edges). Refresh them from local 7689 (108/170), or keep them?
3. **Abstract text in 50 public files** (audit and topic review sheets): keep and disclose, remove
   going forward, or purge history (`git filter-repo` plus force-push)?
4. **Data release:** approve `gh release create data-v1 …` (command in the work log) and choose a
   licence for project-authored data.
5. Hosted SLM provider and budget, and deployment approval (`ops/azure/navigator-deployment.md`).
6. Confirm "forum icons" means communities, and the arXiv `cs.SI` endorser.

## Next step

After the decisions above, start M5 (arXiv report, due 15 December).
