# WORK-2026-11-23-001 — Documentation reorganization

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-23 12:35 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-23 |
| Contributor | Claude Code (Claude Opus 5.5), requested by the user |
| Related task | [WORK-2026-11-12-001](2026-11-12-001-final-stabilization.md) |
| Git state | `main` at `74c0ebe` (one commit ahead of `origin/main`); uncommitted Task2D identity changes left untouched |

## Objective

Make `docs/` navigable after the submission: separate current reference
material from superseded plans and workflows, give the index and root README a
reader-first shape, and stop agent instructions from presenting the expired
11 November deadline plan as active. No graph, config, data or report artifact
changes. User authorized commit and push.

## Changes and findings

- **Constraint found first:** frozen receipts bind the bytes of `AGENTS.md`
  (v3 evaluation freeze), `release-plan.md`, `agent-audit-workflow.md`,
  `correction-amendment-2026-11-09.md` and `five-year-edition-readiness.csv`. The
  submitted LaTeX report cites `docs/reproduce-remediation-v4.md` as a GitHub URL,
  and `reports/final-report/report.md` links `team.md`, `post-audit-findings.md`,
  `reproduce-agent-evaluation.md` and `local-submission-checklist.md`. Those stay at
  their paths. The proposed `design/`/`guides/` subfolders were dropped because
  most current docs fall in that set. `reports/` and `configs/` were not moved:
  code, receipts and manifests use their paths.
- Moved 11 superseded docs and 3 completed-plan prompts into
  [`docs/archive/`](../archive/README.md) with `git mv`. Relative links were
  rewritten in 31 files, and in the moved files themselves. Plain-text paths
  changed only in the three archived prompts. A check confirmed every other edited
  file, including finalized work logs, differs only in link targets.
- [`project-plan.md`](../project-plan.md) now holds the course brief, business
  questions and evaluation caveat. Sites history and the D027–D034 updates moved
  verbatim to [`project-plan-history.md`](../archive/plans/project-plan-history.md).
  [`roadmap.md`](../roadmap.md) keeps current capabilities (98 of 511 lines); the
  pre-D040 iterations went to [`roadmap-history.md`](../archive/plans/roadmap-history.md).
- Rewrote [`docs/README.md`](../README.md) by reader task. Added an index to
  [`decisions.md`](../decisions.md) and [`reference/README.md`](../reference/README.md).
  Shortened the root `README.md`: results table, the AI-assessment caveat, links
  to the v4 evidence package (which already held the detailed disclosures),
  reproduction, graph model and repository layout.
- With user approval, updated `AGENTS.md` for the post-submission state (frozen
  v4, archive rule, completed agent audit). Added a dated correction to
  [`reproduce-agent-evaluation.md`](../reproduce-agent-evaluation.md): restore
  `git show 2305632:AGENTS.md` before rescoring v3. The v4 freezes do not bind it.
- The uncommitted Task2D identity files and the untracked WORK-2026-11-11-006
  entry were left out of this commit.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| Relative-link checker over all tracked Markdown, before and after | 300 broken before, 300 after; identical set (298 in captured `docs/reference/` Site snapshots, 1 ignored data manifest, 1 LaTeX build output) | scratchpad script; not committed |
| Link-only diff check on 41 rewritten/moved files | passed; only the three archived prompts have intended plain-text path changes | inline Python check |
| SHA-256 of every tracked file bound by v3/v4 freeze and receipt JSON, checked before the `AGENTS.md` edit | passed: 0 mismatches across 12 receipts | inline Python check |
| `git show 2305632:AGENTS.md \| sha256sum` | matches the v3-bound hash `fda35261…f2f` | — |
| `uv run pytest -q -x` | passed, exit 0: 650 passed, 1 skipped (working tree included the uncommitted Task2D changes) | `reports/runs/WORK-2026-11-23-001/pytest.log` (ignored) |
| Neo4j, frontend build, report rendering | not run; no code, query, graph or report source changed | — |

## Decisions

None in `decisions.md`. The layout rule (archive by `git mv` unless a receipt or
the submitted report binds the path) is recorded in `AGENTS.md` and
[`archive/README.md`](../archive/README.md).

## Open issues and limitations

- Some historical docs stay at the top level of `docs/` because of path bindings;
  the index labels them.
- After this commit, rescoring v3 needs the documented `AGENTS.md` restore step.
- `docs/release-plan.md` (byte-bound) still says "Every session starts here".
  `AGENTS.md` now overrides that ordering.
- Anchor fragments were not validated automatically. A manual search found only
  `project-plan.md#course-brief`, which still exists.

## Next step

Unchanged project next step in [status](../status.md): resolve lecturer/repository
access and official course/team facts, then authorize delivery.

## Corrections

None.
