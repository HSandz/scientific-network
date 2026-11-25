# Current project status

Updated: **2026-11-25T11:00:00+07:00**. Phase: **final exam**, decision
[D042](decisions.md#d042--final-exam-phase-research-trend-application-on-an-enriched-graph-2026-11-23),
due **20 December 2026, 23:59**. Specification: [docs/final-exam/](final-exam/README.md).
Latest: [WORK-2026-11-25-001](work-log/2026-11-25-001-enrichment-review-fixes.md) (review fixes after [WORK-2026-11-24-004](work-log/2026-11-24-004-enrichment-e1-e4.md)).
Documentation index: [docs/README.md](README.md).

## Final exam checklist (milestones in specification §8)

- [x] Requirements recorded, interpreted and traced; specification drafted (needs team review).
- [x] M0 set-up: splits and QA question text frozen, LLM client, K1 chose Qwen3.5-4B and
  GLiNER-Relex on dev ([report](../reports/enrichment-v1/k1-model-selection.md); D042 amendment).
  The dev answer-accuracy arm of the model rule stays pending until v5 exists.
- [x] M1 enrichment: sources, entities (1,991 nodes), relations, v5-enriched `enriched-c0f7d1dd4abd` validated and loaded on 7690.
- [x] M2-E4 AI-assessed audit ([quality](../reports/enrichment-v1/quality.md)): entity precision 0.927 (met), extracted relations about 0.92-0.95 (met), linking 0.800 (target 0.85 missed), PART_OF 0.69 (0.72 with the statement shown, supplementary).
- [ ] M2 network analysis: small world, ranking, communities, trends (S1–S3).
- [ ] M3 application core: GraphRAG index, multi-hop engine, new Explorer pages (K2, K3).
- [ ] M4 QA benchmark, UI polish, deployment.
- [ ] M5 arXiv report submitted by 15 December.
- [ ] M6 slides, demo script, fallback video, Q&A sheet; final resubmission.

## Carried over from the v4 release

- Production graph v4 `release-d3c788c3114a` stays frozen; v5-enriched will be a
  new version in a new Neo4j service.
- Semantic accuracy, human validation and evaluator independence remain
  unestablished. The seven DOI disagreements and the affiliation/topic limits stay
  disclosed.
- Task2D identity work is an incomplete, separate
  [checkpoint](work-log/2026-11-11-006-pre-review-hardening.md).
- The GitHub repository is private, and the final exam needs public code and data
  links. Decide what can be published (source policy) before December.
- Public Explorer: <https://scientific-network-explorer.pages.dev/>. Restoring v4:
  [reproduce-remediation-v4.md](reproduce-remediation-v4.md).

## Open questions for the team

1. Confirm "forum icons" means communities ([requirements](final-exam/requirements.md#interpretation-notes)).
2. Hosted SLM provider and budget.
3. arXiv endorser for cs.SI.

## Next step

S1-S3 network analysis on the v5 graph (method-task questions use shared-paper co-occurrence, [spec §4.3 note](final-exam/specification.md); `enrich cooccurrence`), then K2/K3 (GraphRAG, multi-hop). Open: linking accuracy and thin
APPLIED_TO/EVALUATED_ON (32 and 4 edges); any rule change needs a dated decision and dev-only tuning. Keep `sn-llm` stopped while Neo4j loads (RAM).
