# Current project status

Updated: **2026-11-25T16:40:00+07:00**. Phase: **final exam**, decision
[D042](decisions.md#d042--final-exam-phase-research-trend-application-on-an-enriched-graph-2026-11-23),
due **20 December 2026, 23:59**. Specification: [docs/final-exam/](final-exam/README.md).
Latest: [WORK-2026-11-25-005](work-log/2026-11-25-005-m3-application-core.md) (M3 application core built and verified).
Documentation index: [docs/README.md](README.md).

## Final exam checklist (milestones in specification §8)

- [x] Requirements recorded, interpreted and traced; specification drafted (needs team review).
- [x] M0 set-up: splits and QA question text frozen, LLM client, K1 chose Qwen3.5-4B and GLiNER-Relex on dev ([report](../reports/enrichment-v1/k1-model-selection.md); D042 amendment).
- [x] M1 enrichment (`enriched-cb371912e308` v3 loaded on Bolt 7690): 50,144 core+enrichment nodes, 242,048 edges; E4 v3 AI-assessed ([quality](../reports/enrichment-v3/quality.md)).
- [x] M2 network analysis ([v1](../reports/final-exam/analysis/README.md), [v2 fixes](../reports/final-exam/analysis-v2/README.md)): small world holds for N1, N2, N4; PageRank & lift PPR; Leiden communities; descriptive trends & display aliases.
- [x] M3 application core ([WORK-2026-11-25-005](work-log/2026-11-25-005-m3-application-core.md)): benchmark references frozen (`69/80` test, `19/20` dev kept); closed 9-tool layer; D042 GraphRAG `rag-v1` (228/233 reports, 4,316 descriptions, 12,000 chunks, SQLite + Neo4j vector indexes); multi-hop engine (`19/19` dev faithful; 7 cached demos); FastAPI + 8 new React Explorer pages (`761 passed` repo, `26` backend passed, Playwright `navigator.spec.ts` passed).
- [ ] M4 QA benchmark evaluation (score the 69 kept test questions vs 3 baselines), UI polish, deployment.
- [ ] M5 arXiv report submitted by 15 December.
- [ ] M6 slides, demo script, fallback video, Q&A sheet; final resubmission.

## Carried over from the v4 release

- Production graph v4 `release-d3c788c3114a` (Bolt 7689) stays frozen.
- Quality figures and GraphRAG summaries are AI-assessed / AI-generated; semantic accuracy and independent human validation remain unestablished.
- Task2D identity work is an incomplete, separate [checkpoint](work-log/2026-11-11-006-pre-review-hardening.md).
- Keep host RAM in mind (`sn-llm` uses `ops/llm/qwen3.5-4b-q4km-live.env` alongside `neo4j-enriched`; ~5.9 GiB + ~0.94 GiB containers).

## Open questions for the team

1. Confirm "forum icons" means communities ([requirements](final-exam/requirements.md#interpretation-notes)).
2. Hosted SLM provider and budget for public deployment.
3. arXiv endorser for cs.SI.

## Next step

Begin **M4**: run QA benchmark evaluation on the 69 kept `split == "test"` questions in `data/manifests/qa-benchmark-v1/references-v1.jsonl` (never used during M3 development) across the four comparison systems (SLM alone, vector RAG over abstracts, GraphRAG local/global, full multi-hop engine), complete UI polish, and deploy.
