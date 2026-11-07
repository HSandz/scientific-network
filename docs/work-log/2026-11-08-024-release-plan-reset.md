# WORK-2026-11-08-024 — Independent review and release plan reset

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-08 03:25 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-08 02:00–03:25 +07:00 |
| Contributor | Claude (Claude Code), at the user's request |
| Related task | [WORK-2026-11-08-023](2026-11-08-023-recsys-2025-browser-source-audit.md) (cancelled) |
| Git state | `main` at `f565d87`, clean at start; this task's documentation changes are uncommitted |

## Objective

Review the project against the course requirements and the agent's recent work,
then write a plan the next agent session (Claude or Codex) can execute before the
11 November deadline.

## Changes and findings

- Review findings:
  - No release graph exists; the largest is the 402/538 2023 candidate.
  - Thirteen P01 source tasks after roster v10 changed no roster.
  - The G01 and P02 gates cannot pass by the deadline.
  - D009's ORCID-only identity and PDF-plus-exact-match affiliation rules resolved
    7% of author positions and 3% of affiliations, and no researcher appeared on
    two papers.
  - `analyze` and `freeze-audit-sample` refuse real graphs without a readiness
    receipt.
  - The validator is quadratic, the loader matches nodes without labels, and the
    final report is only an outline.
- Feasibility checks for the new scope:
  - All 13,617 AAAI/IJCAI 2021–2025 rows yield unique DOIs.
  - Keyless OpenAlex returned 24 of 24 sampled DOIs, with complete per-author data.
  - Sampled ICML papers are arXiv-only in OpenAlex.
- Added [D040](../decisions.md#d040--release-reset-for-the-11-november-submission-2026-11-08)
  and the [release plan](../release-plan.md): phases 0–9, checkpoints, evidence
  rules, audit design, fallbacks, report outline and a technical reference.
- Rewrote [AGENTS.md](../../AGENTS.md):
  - added a "read first" pointer to the release plan;
  - replaced the scope and resolution rules;
  - set Site publishing to once at the end;
  - added a status size limit and a commit rule;
  - corrected stale implementation claims.

  All evidence-integrity rules are kept.
- Replaced [status.md](../status.md) with a short handoff and phase checklist. The
  previous file is preserved unchanged as
  [status-archive-2026-11-08.md](../reference/status-archive-2026-11-08.md).
- Closed WORK-023 as cancelled. Added pointer notes to `README.md`,
  `project-plan.md`, `roadmap.md`, `five-year-execution-plan.md`,
  `pregraph-completion-plan.md` and `evaluation.md`.
- No code, config, roster, split, enrichment, graph or database changes.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `uv run --locked pytest -q -p no:cacheprovider` (after the edits) | passed, exit 0; 218 passed, 1 skipped | `reports/runs/WORK-2026-11-08-024/pytest.log` |
| `uv run research-network validate --input tests/fixtures/synthetic_graph.json` | passed, exit 0 (synthetic, structural only) | `reports/runs/WORK-2026-11-08-024/validate.json` |
| Yield on `data/processed/extended-resolved-v3/graph.json` | 85/1,206 author positions (7.0%); 188/248 papers without a researcher; 38 affiliation observations; 0 researchers with ≥2 papers; 1 CITES | Inline inspection |
| Validator timing on invented graphs | 1k papers 0.37 s, 2k 1.47 s, 4k 7.05 s (quadratic) | `reports/runs/WORK-2026-11-08-024/bench_validate.py` |
| DOI derivation over roster v10 (sha256 `84ff8ca7…`) | 13,617/13,617 derivable, 0 duplicates | Inline script |
| Keyless OpenAlex probes (no key or email sent) | 24/24 DOIs found; sampled authors had IDs, institutions and raw strings; abstracts and references present; 6/6 ICML samples arXiv-only; NeurIPS 2021 1,197 source works against 2,334 roster papers | Public API responses, not cached |
| Held-out IDs in scope (`five-year-splits-v1/membership.jsonl`) | IJCAI: 80 test, 38 development, 1 review, 3,588 pool; AAAI absent | Inline script |
| Services and memory at 02:30 | `neo4j`, `neo4j-extended` healthy and `grobid` up for 19 h; 2.8 GiB available, swap full | `docker ps`, `free -h` |

## Decisions

[D040](../decisions.md#d040--release-reset-for-the-11-november-submission-2026-11-08).

## Open issues and limitations

- The user should confirm or change the release-plan §2 defaults (scope,
  reviewers), commit these documents, stop the old services and fill in
  `docs/team.md`.
- OpenAlex per-request costs for filter queries were not measured with the key.
  Phase 2 preflights the allowance.
- The OpenAlex checks were small samples, not a coverage measurement.

## Next step

Start a new session at release-plan Phase 0. Acceptance: the Phase 0 exit check in
the [release plan](../release-plan.md) is met and ticked in `docs/status.md`.

## Corrections

None.
