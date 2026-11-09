# Work log and session handoff

Read [current status](../status.md) first, then the latest relevant entries below.
The journal records completed and incomplete work for both teammates and future
agent sessions. It complements [the roadmap](../roadmap.md) and
[decision register](../decisions.md).

## Work history

| [WORK-2026-11-09-005](2026-11-09-005-report-completion.md) | Measured report and renderer | completed | Measured report/README, reproducibility and renderer; 19-page preview/six figures inspected; final snapshot package follows |

| [WORK-2026-11-09-004](2026-11-09-004-agent-source-review.md) | Source-backed agent evaluation and scoring | completed | Full AI review/scoring: 88% edge precision, failed gates; topic F1 .4667 embedding/.2301 phrase; 419 tests passed/1 skip |

| [WORK-2026-11-09-003](2026-11-09-003-agent-evaluator-freeze.md) | Agent evaluator implementation and freeze | completed | Provenance-bound scorer and 19 regressions; 403 passed/1 skip; matching agent packets and pre-review freeze ready |

| [WORK-2026-11-09-002](2026-11-09-002-agent-led-evaluation-handoff.md) | Agent-led evaluation and fresh-session handoff | completed | User-authorized D040 amendment removes waiting for human annotations; declared source/evaluator protocol and execution prompt ready; scorer implementation and real evaluation are next |

| [WORK-2026-11-09-001](2026-11-09-001-pre-audit-review.md) | Review corrected pre-audit package | completed | No blocking finding; fresh tests/validation, frozen and historical hashes, canonical preservation, live read-only Neo4j and figure reproduction pass; independent review is next |

| [WORK-2026-11-08-037](2026-11-08-037-pre-audit-corrections.md) | Pre-audit technical corrections | completed | Corrected frozen taxonomy, verified preservation and Neo4j replay, implemented audit fallbacks, froze consistent reviewer packets; human quality remains unmeasured |

| [WORK-2026-11-08-036](2026-11-08-036-progress-review.md) | Current progress review | completed | Fresh tests, graph/hash and live Neo4j checks pass; taxonomy inconsistency and missing audit fallbacks found; quality scores and final delivery remain pending |

| [WORK-2026-11-08-035](2026-11-08-035-topic-review-allocation.md) | Topic-review allocation and Phase 8 tooling | partial | 30/30 reviewer packets with 10 overlap are hash-bound; topic scorer implemented; actual edge/topic annotations and scores remain pending |

| [WORK-2026-11-08-034](2026-11-08-034-phase-8-report-draft.md) | Phase 8 report drafting before reviewer returns | partial | Report sections 1–11 drafted with measured results and six embedded figures; independent scoring and topic allocation need human input |

| [WORK-2026-11-08-033](2026-11-08-033-release-phase-7-freeze.md) | Release Phase 7 freeze and review preparation | completed | v2 graph/config freeze; 200-edge global plus per-type packet with 50 overlap; prediction-blind topic sheet verified; report methods started |

| [WORK-2026-11-08-032](2026-11-08-032-release-phase-6-analysis.md) | Release Phase 6 analysis | completed | D040 release metrics, six figures/tables, source-linked findings and criteria-based shortlists; semantic review remains pending |

| [WORK-2026-11-08-031](2026-11-08-031-release-neo4j-loads.md) | Release Phases 4–5: isolated Neo4j loads and replay | completed | v1 and v2 inventory/integrity passed; both versions replayed idempotently; v2 is current in `neo4j-five-year` |

| [WORK-2026-11-08-030](2026-11-08-030-release-phase-5-embedding-development.md) | Release Phase 5: embedding topics and graph v2 | partial | Frozen development-only classifier; graph v2 validates; prediction-blind topic sheet ready; Neo4j load awaits WSL Docker integration |

| [WORK-2026-11-08-029](2026-11-08-029-release-phase-5-topic-test-freeze.md) | Release Phase 5: freeze topic test IDs | completed (Phase 5 partial) | Hash-bound 30 IJCAI + 20 AAAI topic-test sample frozen before tuning; model work remains pending |

| [WORK-2026-11-08-028](2026-11-08-028-release-phase-3-verification.md) | Release Phase 3: verify and rebuild graph v1 | completed | Structural validation and all size gates pass; 36,680 researchers, 124,619 factual edges, ten relations; Phase 4 awaits Docker Desktop WSL integration |

Newest recorded entry first. Status describes the bounded task, not overall
project completion. Dates use Asia/Bangkok (UTC+07:00).

| ID | Task | Status | Outcome |
| --- | --- | --- | --- |
| [WORK-2026-11-08-027](2026-11-08-027-release-phase-2-openalex-acquisition.md) | Release Phase 2: OpenAlex acquisition | completed | 13,606 of 13,617 roster papers matched by DOI (99.92%), 11 in review, 0 not found; 330 duplicate-DOI records handled by an official-landing-page rule; $0.034 allowance used |
| [WORK-2026-11-08-026](2026-11-08-026-release-phase-1-tooling.md) | Release Phase 1: tooling fixes | completed | Validator indexed (10k papers 0.28 s, was quadratic); labeled, batched loader with release-port guard (10k-paper invented graph loads in 19 s on a throwaway server); no readiness locks, size gates recorded; split-with-overlap audit with HTML review sheet; 273 passed / 1 skipped |
| [WORK-2026-11-08-025](2026-11-08-025-release-phase-0-housekeeping.md) | Release Phase 0: housekeeping | completed | `neo4j-five-year` service and `release-v1`, `quality-release-v1`, `analysis-release-v1` configs added; compose validated, service not started; 224 passed / 1 skipped |
| [WORK-2026-11-08-024](2026-11-08-024-release-plan-reset.md) | Independent review and release plan reset | completed | D040 and [release plan](../release-plan.md): AAAI + IJCAI 2021–2025 graph via DOI-matched OpenAlex evidence, feasible audit; source closure stopped; AGENTS.md and status replaced (old status archived); no code or data changes |
| [WORK-2026-11-08-023](2026-11-08-023-recsys-2025-browser-source-audit.md) | P01 RecSys 2025 browser source audit | cancelled | Stopped by the user; raw captures left unanalyzed in ignored run artifacts; superseded by D040; v10 unchanged |
| [WORK-2026-11-08-022](2026-11-08-022-cikm-2025-browser-source-capture.md) | P01 CIKM 2025 browser source capture | partial | Captured five official pages; 827 accepted IDs versus 852 proceedings links, incomplete title/byline crosswalk and reuse terms; D039 keeps v10 unchanged; Sites helper failed before checkout, Site remains v18 |
| [WORK-2026-11-08-021](2026-11-08-021-acmmm-2024-browser-source-review.md) | P01 ACM Multimedia 2024 browser source review | partial | Recaptured 1,149-ID file and call shell; full roster/reuse unresolved, D038 keeps edition unavailable; v10 and frozen assignments verified; Site helper failed before checkout |
| [WORK-2026-11-07-020](2026-11-07-020-icdm-2025-offline-source-audit.md) | P01 ICDM 2025 accepted-list audit | partial | 175 accepted-page entries captured with response metadata; CFP short-track wording, incomplete program/proceedings join and reuse terms keep the edition unresolved; v10 and frozen assignments remain unchanged |
| [WORK-2026-11-07-019](2026-11-07-019-p01-cikm-2025-source-recheck.md) | P01 CIKM 2025 source recheck | partial | Search-rendered official track pages are route evidence only; 0/55 local DNS hosts resolved and both direct captures failed (curl 6); v10 and protected assignments remain unchanged |
| [WORK-2026-11-07-018](2026-11-07-018-icdm-2021-source-closure.md) | P01 ICDM 2021 source closure | partial | 197 accepted-list IDs match the official schedule; 42 additional schedule IDs are in workshops/PhD Panel; IEEE Xplore returned 418 and reuse rights remain unresolved; v10/frozen assignments preserved; public Site remains v18 because helper DNS fails |
| [WORK-2026-11-07-017](2026-11-07-017-p01-acmmm-2024-source-closure.md) | P01 ACM Multimedia 2024 source closure | partial | Captured 1,149 unique official IDs; stats report 1,150 acceptances; track/proceedings join and reuse terms unresolved; v10/76,629 assignments preserved; approved Sites helper failed before checkout on DNS |
| [WORK-2026-11-07-016](2026-11-07-016-p09-evaluation-contracts.md) | P09 component evaluation contracts | partial | Added hash-bound offline component scoring, review/adjudication checks and coverage; synthetic protocol tests only; 218 passed / 1 skipped; real evaluation gated; approved Site helper failed before checkout on DNS |
| [WORK-2026-11-07-015](2026-11-07-015-offline-analysis-stage.md) | P09 offline named-projection analysis | partial | Implemented gated five-projection metrics and strict-filter sensitivity; 216 tests pass; synthetic protocol only; P01/P02 blockers remain |
| [WORK-2026-11-07-014](2026-11-07-014-p09-offline-contracts.md) | P09 offline edge-audit packet utilities | partial | Added post-build-gated deterministic sample and two-review packet scorer; 212 tests pass; v4 synthetic-only scorer smoke; P01/P02 blockers remain |
| [WORK-2026-11-07-013](2026-11-07-013-p02-resource-snapshot.md) | P02 local resource snapshot | partial | Workspace has 783.40 GiB free disk; selected existing artifacts total 3.65 GiB apparent size; Docker storage is inaccessible; one reviewer reported with no exact hours, second unconfirmed |
| [WORK-2026-11-07-012](2026-11-07-012-pregraph-source-followup.md) | Pregraph source and Site follow-up | partial | CIKM 2025 official proceedings route identified but not locally captured; v10 hashes and frozen assignments verified; Sites helper DNS failed before checkout, so no Site push or publication; public Site stays v18 |
| [WORK-2026-11-07-011](2026-11-07-011-acm-siam-source-route-review.md) | ACM/SIAM official source-route review | partial | Official accepted/program leads found across eight venue families; local DNS failed and proceedings links returned 403; v10's 42 output hashes and frozen counts verified; no roster changes |
| [WORK-2026-11-07-010](2026-11-07-010-ieee-edition-route-review.md) | ICDM/ICRA/IROS official edition-route review | partial | Official route leads found, but no complete local rosters; all 15 years unresolved, v10 and frozen assignments protected; Sites helper DNS failed before checkout, so source was not audited/built, Report remains unpublished and public Site stays v18 |
| [WORK-2026-11-07-009](2026-11-07-009-iclr-official-roster-access.md) | ICLR official roster access retry | partial | Official v2 group metadata identifies submission invitation; notes endpoint returns HTTP 403 challenge; no roster captured; five ICLR years unresolved; Site v18 |
| [WORK-2026-11-07-008](2026-11-07-008-aamas-2023-followup.md) | AAMAS 2023 official identifier scan | partial | Six source hashes verified; 196 exploratory byline joins, 41 without unique candidates; edition remains unresolved and v10/frozen inputs unchanged; existing public Site v17 |
| [WORK-2026-11-07-007](2026-11-07-007-miccai-2022-source-followup.md) | MICCAI 2022 official source-route follow-up | partial | 573 Society / 576 Springer records; 558 unique title pairs; edition unresolved, v10 and frozen inputs unchanged; 37 source hashes verified; Site v16 published; no paper PDFs, split, enrichment or graph |
| [WORK-2026-11-07-006](2026-11-07-006-miccai-2024-source-closure.md) | MICCAI 2024 official source closure | partial | V10 reconciles 856 Society papers to 856 Springer chapters; Site v15 published; 98 eligible editions / 91,355 included; 62 source gaps remain; no enrichment or graph |
| [WORK-2026-11-07-005](2026-11-07-005-aamas-2023-reconciliation.md) | AAMAS 2023 roster reconciliation | partial | 225/237 exact-title joins; 12 title gaps and 35 byline differences; author index covers only 154 distinct main-paper IDs; edition remains unresolved |
| [WORK-2026-11-07-004](2026-11-07-004-miccai-source-review.md) | MICCAI official roster closure | partial | V9 adds 2021/2023/2025 (2,288 records); 2022/2024 remain unresolved; 97 eligible editions / 90,499 included; 63 gaps; 198 tests; no enrichment or graph; public Site v14 |
| [WORK-2026-11-07-003](2026-11-07-003-iclr-source-review.md) | ICLR official source-route review | partial | Official routes found; 2024 counts agree at 2,260, 2025 proceedings/fact-sheet counts differ 3,703/3,704; local API 403/DNS failure prevented hash-bound rosters; no editions added |
| [WORK-2026-11-07-002](2026-11-07-002-aamas-roster-closure.md) | Continue P01 with AAMAS source closure | partial | Roster v8: 94 eligible / 88,211 included; four AAMAS years closed, 2023 unresolved; 66 gaps remain; 193 tests; P02 no-go |
| [WORK-2026-11-07-001](2026-11-07-001-p01-edition-closure.md) | Continue P01 edition closure | partial | Roster v7: 90 eligible / 87,404 included; 10 official no-edition findings; 70 adapter/access gaps and P02 no-go remain; 187 tests; public Site v14 |
| [WORK-2026-11-06-009](2026-11-06-009-pregraph-source-closure.md) | Pregraph source closure and feasibility | partial | ICAPS 2025 resolved in roster v6; 181 tests; 81 gaps and P02 no-go remain; Site v14 awaits credential-transmission approval |
| [WORK-2026-11-06-008](2026-11-06-008-pregraph-completion-plan.md) | Complete pregraph prerequisite plan | completed (planning only) | P00–P10, 82-gap backlog, independent evidence/coverage, twelve readiness gates; no implementation/collection |
| [WORK-2026-11-06-007](2026-11-06-007-source-recovery.md) | Official OJS source recovery | completed | 88 eligible editions / 85,802 included; 82 gaps; 177 tests; frozen inputs preserved; Site v14 |
| [WORK-2026-11-06-006](2026-11-06-006-pregraph-readiness.md) | Pregraph evidence closure and readiness freeze | partial | 55 accepted/13 withheld sources; 12 triples; 156 tests; full readiness false; no graph; Site v13 |
| [WORK-2026-11-06-005](2026-11-06-005-five-year-corroboration.md) | Reviewed sources and public ORCID corroboration | completed | 49 source-eligible papers; 10 people / 11 authorships / one triple; 345 review rows; 145 tests; services healthy; Site v12 |
| [WORK-2026-11-06-004](2026-11-06-004-five-year-headers.md) | Selective five-year PDF headers and source review | partial | 68 PDFs / 66 parsed; 255 affiliation candidates, 56 exact metadata matches, none accepted; 130 tests; Site v11; Docker post-check unavailable |
| [WORK-2026-11-06-003](2026-11-06-003-five-year-diagnostics.md) | Correct source tracks, freeze diagnostics and collect metadata | partial | 79 eligible editions / 75,655 included; 68 diagnostics + 170 tests frozen; 67 metadata, 36 strict matches; 120 tests; services healthy; Site v10 |
| [WORK-2026-11-06-002](2026-11-06-002-five-year-collection.md) | Start five-year official roster collection | partial | 73,714 records; 67 eligible editions; all 170 statuses; 14,909 assignments preserved; no enrichment/graph; 108 tests; Site v7 |
| [WORK-2026-11-06-001](2026-11-06-001-five-year-execution-plan.md) | Deadline-driven five-year execution readiness plan | completed | 11 Nov deadline; dated tasks, 170 pending review rows, effort scenarios; Site v6; 97 tests; original data/configs/splits preserved; no research execution |
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

