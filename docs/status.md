# Current project status

Updated: **2026-11-25T19:35:00+07:00**. Phase: **final exam**, decision
[D042](decisions.md#d042--final-exam-phase-research-trend-application-on-an-enriched-graph-2026-11-23),
due **20 December 2026, 23:59**. Specification: [docs/final-exam/](final-exam/README.md).
Latest: [WORK-2026-11-25-006](work-log/2026-11-25-006-m4-eval-polish-deploy-prep.md) (M4 fixes, run-once benchmark evaluation, UI polish & deploy prep).
Documentation index: [docs/README.md](README.md).

## Final exam checklist (milestones in specification §8)

- [x] Requirements recorded, interpreted and traced; specification drafted (needs team review).
- [x] M0 set-up: splits and QA question text frozen, LLM client, K1 chose Qwen3.5-4B and GLiNER-Relex on dev ([report](../reports/enrichment-v1/k1-model-selection.md); D042 amendment).
- [x] M1 enrichment (`enriched-cb371912e308` v3 loaded on Bolt 7690): 50,144 core+enrichment nodes, 242,048 edges; E4 v3 AI-assessed ([quality](../reports/enrichment-v3/quality.md)).
- [x] M2 network analysis ([v1](../reports/final-exam/analysis/README.md), [v2 fixes](../reports/final-exam/analysis-v2/README.md)): small world holds for N1, N2, N4; PageRank & lift PPR; Leiden communities; descriptive trends & display aliases.
- [x] M3 application core ([WORK-2026-11-25-005](work-log/2026-11-25-005-m3-application-core.md)): benchmark references, 9-tool layer, GraphRAG `rag-v1`, FastAPI + 8 React Navigator pages.
- [x] M4 QA benchmark evaluation, UI polish & deployment preparation ([results](../reports/final-exam/qa-eval-v1/results.md), [deploy plan](../ops/azure/navigator-deployment.md)) — local code/docs ready; live Azure/Pages deploy awaits user approval.
- [ ] M5 arXiv report submitted by 15 December.
- [ ] M6 slides, demo script finalization, fallback video, Q&A sheet; final resubmission.

## Carried over & active disclosures

- Production v4 graph `release-d3c788c3114a` (Bolt 7689) stays frozen.
- Quality figures, citation validity, global pairwise wins, and GraphRAG summaries are AI-assessed / AI-generated; Wilson/bootstrap CIs exclude evaluator error, and adjudicator C (`codex exec`) shares B's model family (`gemini` CLI unauthenticated).
- Keep host RAM in mind: run `sn-llm` and `neo4j-five-year` (7689) separately on 11 GiB WSL.

## Open decisions for the user

1. Choose hosted SLM provider & budget (or `$0` cached-demo mode) and authorize live Azure/Cloudflare Pages deployment (`ops/azure/navigator-deployment.md`).
2. Confirm "forum icons" means communities ([requirements](final-exam/requirements.md#interpretation-notes)) and arXiv `cs.SI` endorser.

## Next step

Await user provider/budget selection and deployment approval, then proceed to M5 (arXiv report).
