# Work log and session handoff

Read [current status](../status.md) first, then the latest relevant entries below.
The journal records completed and incomplete work for both teammates and future
agent sessions. It complements [the roadmap](../roadmap.md) and
[decision register](../decisions.md).

## Work history

Newest recorded entry first. Status describes the bounded task, not overall
project completion. Dates use Asia/Bangkok (UTC+07:00).

| ID | Task | Status | Outcome |
| --- | --- | --- | --- |
| [WORK-2026-11-04-003](2026-11-04-003-native-site-report.md) | Native Report integration in existing Site | completed | Published v5; graph, charts, filters, coverage and evidence in Site DOM; no iframe; 20 Plan sections preserved; 97 tests; 5,713 artifacts unchanged |
| [WORK-2026-11-04-002](2026-11-04-002-five-year-plan-site.md) | Five-year planning and unified Plan/Report Site | completed | 2021–2025 plan; 170 unverified venue–year candidates; existing Site renamed/published v4 with Plan/Report; 97 tests; data/configs preserved |
| [WORK-2026-11-04-001](2026-11-04-001-evidence-review.md) | Byline and identity/affiliation evidence review | completed | 250 acquired / 240 parsed; 3 core admissions, 2 withheld; 402/538 candidate; 718-row triage, 5 existing triples corroborated; 97 tests; live DBs preserved |
| [WORK-2026-11-03-007](2026-11-03-007-html-report.md) | Standalone visual HTML report | completed | Offline399-node /533-edge explorer; evidence,coverage,print/export;80 tests and browser checks |
| [WORK-2026-11-03-006](2026-11-03-006-extended-collection.md) | Expanded implementation and staged collection | partial | 17 venues,14,909 eligible roster papers;245 acquired,235 parsed; separate Neo4j399 nodes /533 edges;72 tests;14 editions unresolved |
| [WORK-2026-11-03-005](2026-11-03-005-expand-conference-plan.md) | Expand conference scope and Sites plan | completed | 34 series / 31 planned 2023 editions; Sites v3 published; docs updated; no new data collected |
| [WORK-2026-11-03-004](2026-11-03-004-discovery-pilot-graph.md) | Discovery, frozen splits and pilot graph | completed | 5,046-paper roster; 100-paper pilot; Neo4j 154 nodes / 211 edges; replay verified; 48 tests passed |
| [WORK-2026-11-03-003](2026-11-03-003-next-steps-readiness.md) | Next steps and setup readiness | completed | Python/offline checks pass; Docker daemon ready; prioritize roster discovery and pilot |
| [WORK-2026-11-03-002](2026-11-03-002-progress-logging.md) | Progress logging and agent handoff | completed | Added status page, template, task history and contributor workflow |
| [WORK-2026-11-03-001](2026-11-03-001-repository-initialization.md) | Repository initialization (retrospective; work on 2026-11-02) | completed | Scaffold and offline checks; real pipeline and integration remain pending |

## What to save

| Record | Location | Update rule |
| --- | --- | --- |
| Current state, blockers and next action | `docs/status.md` | Refresh at task end; keep short |
| Objective, changes, evidence and handoff for each task/iteration | `docs/work-log/YYYY-MM-DD-NNN-short-slug.md` | Start early; finalize before handoff; later corrections are explicit |
| Long-term plan | `docs/roadmap.md` | Update when a capability/milestone changes |
| Durable design rationale | `docs/decisions.md` | Add a decision when needed; link from the work entry |
| Raw console output and run artifacts | `reports/runs/<work-id>/` | Unique run paths; ignored by Git |

Small Markdown records are intended to be committed with their related changes.
Local raw artifacts are not available in a fresh clone: the work entry must retain
the exact command, exit code, essential results and version/hash metadata needed
to understand or reproduce the outcome. If a result is essential for a release,
promote a small sanitized, permitted summary to an appropriate versioned report.
Do not force-add raw ignored logs.

## Everyday workflow

1. Read the current handoff and relevant history. Inspect actual files and Git
   state; old logs do not prove that today's code still passes.
2. Copy [the template](../templates/work-log.md) into this directory. Choose an
   unused date/three-digit sequence/slug and matching `WORK-YYYY-MM-DD-NNN` ID.
   Never replace an existing record. Mark the task `in_progress` and state its goal.
3. Perform the task. Checkpoint useful findings, failures and ongoing jobs during
   long work so an interrupted session can be resumed.
4. Record what changed, exact verification outcomes, local artifacts, decisions,
   limitations and the next action. Finalize as `completed`, `partial`, `blocked`
   or `cancelled`, then update this index and `docs/status.md`.
5. Include the concise work record in the normal Git commit with related code/docs
   when committing. Logging alone does not create a commit, remote or backup.

Use one entry per substantive task or meaningful iteration, not per shell command.
Ordinary conversation without project work/state changes needs no new entry.
Follow-up changes after finalization get a new linked entry. Preserve failed
experiments and original audit/test outcomes; append dated corrections when needed.

## Capturing command output

For example, after choosing the real work ID, run from the repository root in Bash:

```bash
mkdir -p reports/runs/WORK-YYYY-MM-DD-NNN
set -o pipefail
uv run pytest 2>&1 | tee reports/runs/WORK-YYYY-MM-DD-NNN/pytest.log
```

`pipefail` preserves a failing command's status through `tee`. Record the observed
exit code in the work entry. Use distinct filenames for reruns and preserve the
original failure. The same pattern works for a CLI command; the validator's
`--output` also writes a structured summary including input/config hashes.

Save observations, actions, decisions and evidence references. Do not dump full
chats, hidden reasoning, credentials, sensitive profile data or restricted paper
text into the journal.
