# Current project status

Updated: **2026-11-25T13:05:00+07:00**. Phase: **final exam**, decision
[D042](decisions.md#d042--final-exam-phase-research-trend-application-on-an-enriched-graph-2026-11-23),
due **20 December 2026, 23:59**. Specification: [docs/final-exam/](final-exam/README.md).
Latest: [WORK-2026-11-25-003](work-log/2026-11-25-003-enrichment-v3.md) (enrichment v3 after [WORK-2026-11-25-002](work-log/2026-11-25-002-enrichment-v2.md)).
Documentation index: [docs/README.md](README.md).

## Final exam checklist (milestones in specification §8)

- [x] Requirements recorded, interpreted and traced; specification drafted (needs team review).
- [x] M0 set-up: splits and QA question text frozen, LLM client, K1 chose Qwen3.5-4B and
  GLiNER-Relex on dev ([report](../reports/enrichment-v1/k1-model-selection.md); D042 amendment).
  The dev answer-accuracy arm of the model rule stays pending until v5 exists.
- [x] M1 enrichment: sources, entities (1,991 nodes), relations, v5-enriched `enriched-c0f7d1dd4abd` (v1, kept) validated and loaded on 7690.
- [x] Enrichment v2 `enriched-827be09bc987` (kept; [quality](../reports/enrichment-v2/quality.md)): `MEMBER_OF` and single-paper EVALUATED_ON adopted, the rest failed absolute criteria.
- [x] Enrichment v3 `enriched-cb371912e308` (loaded on 7690): PART_OF rule and link guard adopted post hoc, single-paper APPLIED_TO adopted. Fresh E4 v3 ([quality](../reports/enrichment-v3/quality.md)): PART_OF 0.951 (0.78 with unclear as incorrect), linking 0.895, APPLIED_TO single paper 0.983, `MEMBER_OF` 13/13 decided but half unclear. AI-assessed; adjudicator = same model as B.
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

Decide (user): how to treat `MEMBER_OF` (ambiguous, not wrong) and PART_OF's ministry-parent cases, and whether a lead-based link guard is worth an amendment. Otherwise start S1-S3 network analysis on `enriched-cb371912e308` (method-task questions use shared-paper co-occurrence and the 167 APPLIED_TO edges, [spec §4.3 notes](final-exam/specification.md)), then K2/K3. Entity precision 0.927, paper edges and APPLIED_TO/EVALUATED_ON meet targets; RELATED_TO 0.625 does not. Restore v1 or v2 on 7690: see the [v3 work log](work-log/2026-11-25-003-enrichment-v3.md). Keep `sn-llm` stopped while Neo4j loads (RAM).
