# Current project status

Updated: **2026-11-08 03:10 +07:00**. Deadline: **11 November 2026**.
Plan: [release plan](release-plan.md) under [D040](decisions.md#d040--release-reset-for-the-11-november-submission-2026-11-08).
History before D040: [archived status](reference/status-archive-2026-11-08.md) and the [work log](work-log/README.md).
Latest entry: [WORK-2026-11-08-025](work-log/2026-11-08-025-release-phase-0-housekeeping.md).

## State

- Release scope: AAAI + IJCAI 2021–2025, 13,617 papers from roster v10. Roster and
  source work is closed for this release.
- No release graph exists yet. The pilot (154/211), 2023 diagnostic (399/533) and
  candidate (402/538) graphs are historical diagnostics only.
- Tests: 224 passed, 1 skipped (WORK-025).
- Services: `neo4j`, `neo4j-extended` and `grobid` stopped; `neo4j-five-year` is
  defined in `compose.yaml` but not started (Phase 4).
- Release configs: `configs/release-v1.yaml`, `quality-release-v1.yaml`,
  `analysis-release-v1.yaml`.

## Phase checklist

- [x] P0 Housekeeping: old services stopped; `neo4j-five-year` service defined; release configs created
- [ ] P1 Tooling fixes: validator indexed; loader labeled and batched; receipt locks removed; split-with-overlap review; tests pass
- [ ] P2 OpenAlex acquisition: `works.jsonl` and `acquisition.json`; match rate reported (**CP1**, Sun 14:00)
- [ ] P3 Graph v1: all ten relations, validated, `graph-summary.json`
- [ ] P4 Neo4j: loaded, integrity clean, re-import idempotent (**CP2**, Sun 22:00)
- [ ] P5 Topics: test set frozen first; classifier frozen; graph v2 loaded; label sheet ready
- [ ] P6 Analysis: `analysis.json`, figures, findings draft (**CP3**, Mon 16:00)
- [ ] P7 Freeze: `freeze.json`; edge and topic review sheets delivered (**CP4**, Mon 20:00)
- [ ] Human review returned: edge audit and topic labels (Tue 12:00)
- [ ] P8 Scoring, full report draft, README rewrite (**CP5**, Tue 20:00)
- [ ] P9 PDF, release tag, submission (**CP6**, Wed 11 Nov 12:00)

## Next action

Phase 1 (tooling fixes), starting with the quadratic validator in
`graph/validate.py`, then the loader, the receipt locks and the audit design.

## Waiting on the user

- Fill in `docs/team.md` (names, student IDs, roles); decide lecturer repo access;
  check whether the course requires disclosing AI-tool use.
- Start `neo4j-five-year` when Phase 4 asks.
- Reserve review time Mon 20:00 → Tue 12:00 (about 4 h each for two reviewers).
