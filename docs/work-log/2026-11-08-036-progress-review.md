# WORK-2026-11-08-036 — Current progress review

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-08 23:42 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-08 +07:00 |
| Contributor | Codex, at the user's request |
| Related task | [WORK-2026-11-08-035](2026-11-08-035-topic-review-allocation.md) |
| Git state | Clean `main` at `951b9c5` before review |

## Objective

Review the current requirements, implementation and release evidence against D040.
Verify progress without changing the frozen graph, collecting data, filling human
reviews or advancing publication. Changes are limited to the required handoff records.

## Changes and findings

- Read the course brief, D040, schema, configs, report and findings. Traced DOI
  acquisition, identity/affiliation resolution, phrase/embedding topics, graph
  derivation/validation, Neo4j loading, analysis, review preparation and scoring.
- Phases 0–7 have execution checkpoints; Phase 8 has tools and a report draft,
  but no human scores. Frozen v2 is `release-5d830ffcbdf4`, SHA-256
  `b79e456b22488ca8f753fb0884afd5c6a89afeeeaffec07d89ce83b2c5c141fb`.
- **High priority: taxonomy inconsistency before audit.**
  [`resolve/release_topics.py`](../../src/scientific_network/resolve/release_topics.py)
  lines 90–106 retain v1 Topic nodes and taxonomy edges/evidence. All 20 v2 Topic
  nodes say `taxonomy-v0.1`; the classifier and blind topic sheets use
  `taxonomy-release-v1`. Generative-modeling and graph-ML definitions differ.
  Four unique sampled HAS_TOPIC edges (five reviewer rows) visibly show the old
  definitions. Hash integrity passes despite this internal semantic inconsistency.
  Resolve before independent review; a frozen-graph correction requires a new
  version, validation, load and audit under D040.
- **Medium priority: audit fallbacks missing.** `evaluation/edge_audit.py`
  lines 73–74 reject one reviewer; lines 460–474 require every assignment. This
  prevents D040's single-reviewer and incomplete-audit fallbacks. The normal
  two-person complete-packet route is implemented and covered by passing tests.
- **Report corrections:** section 4's author-position denominator applies only
  to matched works: 65,469 versus 65,507 across all scoped roster rows (38 on
  unmatched papers). Section 11's “has not been pushed” statement is stale:
  live remote main matches review base `951b9c599f9ba5495cacc7cf88a7ba712e036657`.
  No remote release tags were found. The report was not rewritten in this review.
- Fresh database reads match the frozen graph; six integrity queries return no
  rows. Accepted affiliation observations checked against works have raw strings;
  no repeated-ID paper still accepts that repeated author ID. These are
  consistency checks, not semantic accuracy measurements.
- Changed only this entry, its index and status. No code, frozen graph/config/
  packet, report result, service or public Site changed.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `git status --porcelain=v1` | passed, exit 0; clean before work | Base `951b9c5` |
| `uv sync --locked --group dev --extra analysis` | passed, exit 0; 36 installed packages audited | run directory `uv-sync.log` |
| `uv run pytest` | 363 passed, 1 skipped, exit 0; 16.79 s | run directory `pytest.log`; existing empty stage parameterization skipped |
| `uv run research-network validate --input data/processed/release-graph-v2/graph.json --config configs/quality-release-v1.yaml --require-size --output reports/runs/WORK-2026-11-08-036/graph-v2-validation.json` | passed, exit 0; 52,415 nodes, 275,438 edges, 36,680 resolved researchers, 124,619 factual edges, 10 predicates; no structural errors | structural only |
| `uv run python reports/runs/WORK-2026-11-08-036/check-evidence.py` | corrected helper passed, exit 0; all 18 graph/baseline/works/config/test/analysis/packet hash references match, including tracked HEAD blob bytes | `evidence-check-final.json`; taxonomy mismatch documented above |
| `docker compose ps --format json`; `uv run python reports/runs/WORK-2026-11-08-036/check-neo4j.py` | passed, exit 0; healthy service, inventory matches, six zero-row integrity results, only v2 graph version | `neo4j-read-only.json`; no imports or mutations |
| `uv run python reports/runs/WORK-2026-11-08-036/check-fallbacks.py` | exit 0; one-reviewer scratch config rejected as observed | `fallback-check.json`; no review judgments manufactured |
| `uv run research-network score-topic-review --reviewer-a reports/release-v1/audit/topic-label-sheet-reviewer-A.csv --reviewer-b reports/release-v1/audit/topic-label-sheet-reviewer-B.csv --output reports/runs/WORK-2026-11-08-036/blank-topic-result-must-not-exist.json` | expected refusal, exit 1; unreviewed row; no output created | not an evaluation score |
| `git ls-remote origin refs/heads/main 'refs/tags/*'` | passed, exit 0; remote main matches review base; no tags | lecturer access/public visibility not checked |
| Tracked-file/delivery inspection; `git diff --check` | passed; no tracked `.env`, PDF or raw/interim/processed data except `.gitkeep`; no quality result or final PDF | team/report input remains pending |

Artifacts above are under `reports/runs/WORK-2026-11-08-036/` (ignored).
The first evidence helper exited 1 because `str.splitlines()` split an embedded
Unicode separator; file-line iteration fixed the helper, with source data unchanged.
An initial read of nonexistent `graph-summary-v2.json` exited 1; the correct file
is `graph-v2-summary.json`. One handoff patch was rejected before changes because
it deleted and added the same path; corrected updates were applied sequentially.
No acquisition, model download/inference, graph rebuild, analysis rerun, import
replay, PDF render or Site publication was run. Existing analysis/replay receipts
remain historical; their input hashes and live inventory/integrity were checked.

## Decisions

None. Review only; D040 remains controlling.

## Open issues and limitations

Taxonomy consistency and the audit fallbacks remain unresolved findings. Tracked
review packets are blank; no edge precision/Wilson or topic P/R/F1 result exists.
Real team identities/contributions, course AI-use disclosure, a verified ≥10-page
PDF, release tag and lecturer access remain outstanding. Tests and structural
validation do not close these gaps.

## Next step

Resolve taxonomy consistency through a documented new graph/version and matching
review context before independent judgments. Then complete and score the reviews,
finish the report/team record, and verify the PDF/release package. Preserve the
current freeze and earlier records.

## Corrections

None.
