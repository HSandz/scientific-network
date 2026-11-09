# Team and contribution record

**Current D040 amendment, 9 November:** human annotation is optional. Agent review
channels A/B are evaluator runs, not the people in this table. Record agent/model
provenance in the evaluation manifest; never invent team identities or attribute
agent judgments to students. Missing names/IDs/contributions do not block audit,
scoring or local report/PDF preparation; keep those fields explicitly pending.

The role allocation and human cross-review wording below are historical/optional,
not current prerequisites. Follow [the release plan](release-plan.md) and
[agent workflow](agent-audit-workflow.md) for active execution.

Two-person baseline from the original plan. Fill in identities and actual dates
before the first annotation/review; placeholders do not assert membership.

| Role | Name | Student ID | Primary responsibility | Cross-review |
| --- | --- | --- | --- | --- |
| A | TBD | TBD | Collection, identity resolution, triples, Neo4j, derivation, rebuild | Topics, NLP evaluation, analysis |
| B | TBD | TBD | GROBID, topics, gold labels, EDA/SNA, business cases, demo/report | Identity decisions, affiliations, derivations |

Five-year scope (2021–2025) is planning-only. Re-estimate venue–year source work,
annotation/review hours and storage/runtime before agreeing delivery dates.
The former two-person/eight-week schedule is historical, not a five-year promise.
A owns source/graph evidence for report updates; B owns NLP/analysis evidence;
both check that the Site Report separates targets, historical results and new
measurements before publication. See [Site workflow](sites-workflow.md).

Actual course deadline: **11 November 2026**, confirmed by the user on 6 November.
Follow the [dated execution plan](five-year-execution-plan.md). The exact submission
time is unspecified; internal packaging target is 10 November, 18:00 +07:00.
Weekly availability/review budget remain unspecified and are not requested as
blocking inputs. Do not infer committed hours from the illustrative effort ranges.
Both independently annotate held-out papers/audit edges, adjudicate disagreements,
check limitations/references and reproduce the other's principal outputs. Neither
is the sole author and sole evaluator of an extraction rule.

A writes collection/graph/reproducibility methods; B writes NLP/analysis methods;
both own final results, conclusion and delivery. Record actual work, not assumed
credit from this role allocation.

| Date/week | Member | Issue/commit/artifact | Work performed | Reviewer | Evidence link |
| --- | --- | --- | --- | --- | --- |
| TBD | TBD | TBD | TBD | TBD | TBD |

## Actual agent execution record — 9 November 2026

This records agent work, not student credit. Human names, student IDs and actual
individual contributions remain pending; the illustrative A/B role table above
must not be treated as observed student work.

| Agent context | Recorded work | Evidence |
| --- | --- | --- |
| Codex coordinator `/root` | Freeze, integration, source/DB validation, scoring/report/package preparation | WORK-2026-11-09-003 onward |
| `/root/reviewer_a` | 30 prediction-blind topic judgments; assigned source-backed edge review | `reports/release-v3/completed/A-*` |
| `/root/reviewer_b` | 30 prediction-blind topic judgments; assigned source-backed edge review | `reports/release-v3/completed/B-*` |
| `/root/agent_scorer` | Agent provenance/scoring wrapper, synthetic regressions and renderer/package tooling | Implementation and tests in WORK-003 onward |

Exact runtime provider/model IDs are unknown; evaluator channels are not human
identities. Human validation was not performed; course AI-use/access rules are
not available in supplied records. No student contribution is invented here.

### Authorized remediation execution (9 November, separately versioned)

Coordinator `/root` integrated A–E, source verification and actual post-export
adjudication. `/root/identity_correction` implemented corrected graph/analysis and
report updates. Fresh `/root/prospective_a` and `/root/prospective_b` each reviewed
175 assigned edges, with no inherited coordinator history/shared answers. They
did not create historical topic references. Evidence/run metadata and unknown
runtime IDs are in `reports/release-v4/evaluation-freeze-v2.json` and completion
records. This adds no student credit or human validation; see WORK-010–014.
