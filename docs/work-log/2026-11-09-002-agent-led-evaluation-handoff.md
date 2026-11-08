# WORK-2026-11-09-002 — Agent-led evaluation and fresh-session handoff

| Field | Value |
| --- | --- |
| Status | completed — protocol and execution prompt; implementation/review next |
| Recorded | 2026-11-09 01:30 +07:00 (Asia/Bangkok) |
| Completed | 2026-11-09 01:40 +07:00 |
| Work performed | 2026-11-09 +07:00 |
| Contributor | Codex, at the user's request |
| Related task | [WORK-001](2026-11-09-001-pre-audit-review.md) |
| Git state | Clean main at `05ac5d8` before this task |

## Objective

Apply the user's decision to delegate feasible audit and release-preparation work
to agents. Update the current protocol and related guidance, preserve frozen
artifacts, and provide a self-contained prompt for a fresh execution session.

## Changes and findings

- Added the user-authorized D040 amendment: agents perform feasible evaluation,
  scoring, report and local packaging. Human annotations are optional. Only
  unavailable personal facts, demonstrated tool/access needs and external
  authorization remain human inputs; independent work continues meanwhile.
- Added [the agent workflow](../agent-audit-workflow.md), a frozen declarative
  [protocol contract](../../configs/evaluation-agent-release-v1.yaml) and a
  [self-contained fresh-session prompt](../prompts/agent-release-completion.md).
  The prompt requires execution through real source review, scoring and local PDF
  preparation, not merely tooling or packet creation.
- Updated AGENTS, release plan, evaluation guide, status, roadmap, project-plan
  banner, team guidance, README and report draft. Preserved the old human handoff
  with a clear supersession banner and left finalized logs/receipts untouched.
- Default A/B are isolated fresh agent contexts, with topic judgments frozen before
  edge predictions are exposed. A preselected single-agent variant is permitted
  when isolation is unavailable; inability to obtain a clean topic context is
  recorded as a specific not-run limitation, not fabricated blind annotation.
- Required source/evaluator ledgers, pre-review provenance bindings, actual
  model/run metadata, unchanged thresholds, failed/missing results and truthful
  AI-assessed labels. No claim of human gold labels, evaluator independence or
  verified course accuracy follows from model agreement or Wilson intervals.
- Clearly documented that existing scorers do not implement this new provenance
  contract yet. New agent configs/forms/results must use new versions; the graph,
  classifier, test/allocation and historical quality/packet/freeze bytes are unchanged.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `git status --short --branch`; existing/new path checks | passed, exit 0; clean base and unused output paths | `05ac5d8` |
| `uv sync --locked --group dev --extra analysis` | passed, exit 0; 36 packages audited | No dependency changes |
| `uv run pytest` | passed, exit 0; 384 passed, 1 existing empty-parameterization skip, 17.47 s | `reports/runs/WORK-2026-11-09-002/pytest.log` |
| `uv run research-network schema` | passed, exit 0; offline CLI emits valid JSON | Same run directory, `schema.json` |
| `uv run python reports/runs/WORK-2026-11-09-002/check-handoff.py` | passed, exit 0; protocol/inputs, graph hash, 164 relative links, protected diff paths and absent real outputs verified; status 40 lines | Same run directory, `handoff-check.json` |
| `git diff --check`; ignored-run checks | passed, exit 0 | Only protocol/config/current documentation records changed |

One documentation patch was rejected for an unmatched context; the corrected
patch applied. Non-gate searches with no matches returned expected exit 1.
No substantive validation failed. Run artifacts remain ignored.

## Decisions

[D040 user amendment](../decisions.md#d040-amendments), dated 9 November 2026.
No graph-semantic, corpus, classifier, held-out or numeric-threshold change.

## Open issues and limitations

This task implements the policy/configuration/handoff, not evaluator code or actual
judgments. No agent score, completed annotation or release package was created.
The prior technical review remains historical; graph validation, Neo4j load/replay,
analysis, figure rendering and source acquisition were not rerun here. No push,
tag, Site publication, invitation or submission occurred. Real team facts remain
unavailable and must not be invented.

## Next step

Start a fresh session with [the execution prompt](../prompts/agent-release-completion.md).
Implement/test evaluator provenance first, freeze the chosen review design before
judgments, then finish all feasible audit/scoring/report/local-package work.

## Corrections

None.
