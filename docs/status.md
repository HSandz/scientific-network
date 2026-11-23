# Current project status

Updated: **2026-11-23T13:30:00+07:00**. Phase: **final exam**, decision
[D042](decisions.md#d042--final-exam-phase-research-trend-application-on-an-enriched-graph-2026-11-23),
due **20 December 2026, 23:59**. Specification: [docs/final-exam/](final-exam/README.md).
Latest: [WORK-2026-11-23-003](work-log/2026-11-23-003-git-checkpoint.md).
Documentation index: [docs/README.md](README.md).

## Final exam checklist (milestones in specification §8)

- [x] Requirements recorded, interpreted and traced; specification drafted (needs team review).
- [ ] M0 set-up: splits frozen, LLM client and runtime, model selection (K1).
- [ ] M1 enrichment: sources (E1), entities (E2), relations (E3), v5-enriched validated and loaded.
- [ ] M2 quality and SNA: frozen AI-assessed audit (E4); small world, ranking, communities, trends (S1–S3).
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

Team review of the specification. Then start M0: write D042 amendments for any
changed defaults, freeze `data/manifests/enrichment-splits-v1/`, and run the
model-selection experiment (specification §6.1).
