# WORK-2026-11-23-002 — Final exam requirements and specification

| Field | Value |
| --- | --- |
| Status | completed (draft documents; awaiting team review) |
| Recorded | 2026-11-23 13:30 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-23 |
| Contributor | Claude Code (Claude Opus 5.5), requested by the user |
| Related task | [WORK-2026-11-23-001](2026-11-23-001-docs-reorganization.md) |
| Git state | `main` at `372f141`; uncommitted Task2D identity changes untouched |

## Objective

Record the new final-exam requirements (due 20 December 2026) and write a
detailed specification for the chosen research-trend application, organized for
the team and agents.

## Changes and findings

- Added [`docs/final-exam/`](../final-exam/README.md): the
  [requirements](../final-exam/requirements.md) (rubric, interpretation of three
  translated phrases, user constraints, traceability) and the
  [specification](../final-exam/specification.md) (enrichment E1–E4, SNA S1–S3,
  SLM/GraphRAG/multi-hop K1–K3, product pages, non-functional requirements, QA
  benchmark, deliverables, milestones, acceptance, risks).
- Recorded [D042](../decisions.md#d042--final-exam-phase-research-trend-application-on-an-enriched-graph-2026-11-23)
  with the user's decisions and the authorized enrichment-layer schema; v4 stays
  frozen. Linked the phase from `AGENTS.md`, the root and docs READMEs,
  `project-plan.md`, and replaced `status.md`.
- Facts checked in the repo for the specification: 13,606 papers with title and
  abstract (11 title-only); organizations carry ROR IDs; existing analysis has
  PageRank, betweenness and Louvain but no small-world measures, SLM or RAG; the
  Explorer stack is React/Sigma/ECharts plus FastAPI; the local GPU is an RTX 5060
  Laptop with 8 GB; the 2021–2025 paper counts are 2,240 / 1,997 / 2,217 / 3,121 /
  4,042. The existing held-out splits cover only IJCAI, so the specification
  defines new enrichment splits.
- Proposals only: no code, config, graph or report changed. Model sizes and the
  arXiv endorsement and moderation points come from general knowledge and should be
  confirmed at M0.

- Follow-up the same day, at the user's request: models were updated to current
  releases. Parameter counts, licences and release dates were read from the
  Hugging Face model API: Qwen3.5-9B 9,653,104,368; Qwen3.5-4B 4,659,865,088;
  Gemma-4-E4B-it 7,996,156,490; GLiNER2.5-base 193,581,591; GLiNER2.5-multi
  287,355,159; GLiNER-Relex-large 466,576,896. All are Apache-2.0. The user chose
  selection by experiment with strict total-parameter eligibility; recorded as a
  D042 amendment.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| Relative-link checker and anchor check over the new and edited files | passed; broken-link set unchanged from baseline (300, all pre-existing) | scratchpad scripts |
| Tests | not run; documentation only | — |

## Decisions

[D042](../decisions.md#d042--final-exam-phase-research-trend-application-on-an-enriched-graph-2026-11-23).

## Open issues and limitations

- Team confirmation needed: the "forum icons" reading, hosted SLM provider and
  budget, arXiv endorser.
- The repository is private; the exam needs public code and data links.

## Next step

Team review of the specification, then M0 (specification §8): freeze the
enrichment splits and run the model-selection experiment.

## Corrections

None.
