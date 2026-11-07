# WORK-2026-11-08-026 — Release Phase 1: tooling fixes

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-08 03:30 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-08 03:08–03:30 +07:00 (system clock) |
| Contributor | Claude (Claude Code), at the user's request |
| Related task | [WORK-2026-11-08-025](2026-11-08-025-release-phase-0-housekeeping.md) |
| Git state | `main` at `6845216` at start; Phase 1 changes committed after this entry |

## Objective

Release-plan [Phase 1](../release-plan.md): fix the validator, the loader, the
readiness locks and the audit design before any release graph exists.

## Changes and findings

- **Validator** ([validate.py](../../src/scientific_network/graph/validate.py)): the
  venue, authorship, topic-label and leaf-parent checks use indexes built in one pass
  instead of scanning every edge per node.
- **Loader** ([load.py](../../src/scientific_network/graph/load.py)): labeled `MATCH`
  per relation from `RELATIONSHIPS`, 5,000-row batches each in its own transaction,
  per-label and per-relation count reconciliation, `MERGE` on `edge_id` and the
  project/version stamps kept. Foreign-ID checks and counts are now per label. The
  Neo4j error type and message are reported. A release graph (`release-…`) can only
  go to port 7689, and no other graph can (see D040 amendments).
- **Locks** ([analyze.py](../../src/scientific_network/analysis/analyze.py),
  [edge_audit.py](../../src/scientific_network/evaluation/edge_audit.py)): no
  readiness receipt is required, a supplied one is still verified, and size gates are
  recorded as `passed`/`failed` in the output. The frozen-config requirement stays.
- **Audit** (edge_audit.py,
  [review_sheet.py](../../src/scientific_network/evaluation/review_sheet.py)):
  `audit.review_design: split_with_overlap` assigns edges deterministically (overlap
  from the global sample, the rest alternating by seeded hash rank), writes one CSV
  row per edge and assigned reviewer plus context columns, and writes a
  self-contained HTML sheet next to the CSV. The scorer checks the assignment, accepts
  the direct verdict with an error category, and reports agreement (percent and
  Cohen's κ), error categories, and the course and project gates. `double_review`
  remains the default.
- Config: [quality-release-v1.yaml](../../configs/quality-release-v1.yaml) unchanged;
  its audit keys are now read. Docs: evaluation.md section, README sentence,
  AGENTS.md implementation note, D040 amendments.
- Not changed: the `cli.py` guard for old stages. Not implemented: scoring a partly
  completed audit (the "audit unfinished" fallback), which is a Phase 8 concern.
- The sheet reads optional properties that Phase 3 must write: paper `doi`,
  `openalex_id`, `pdf_url`; AUTHORED `byline_position`, `roster_name`;
  AFFILIATED_WITH `raw_affiliation_strings`; topic `definition` (listed in the module
  docstring). Missing ones leave the cell blank.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| Validator golden comparison: old and new `validate_graph` over the fixture and 28 defect-injected variants | passed; byte-identical error lists and order (sha256 `8455018e…`) | inline scripts; legacy output captured before the edit |
| Validator timing, plain invented graph (4 authors per paper) | 1k 0.02 s, 2k 0.05 s, 4k 0.08 s (was 7.05 s), **10k 0.28 s** | invented data, not project results |
| Validator timing, release-shaped invented graph (affiliations, topics, derived edges) | 10k papers, 80k base edges: 0.39 s base, `materialize` 3.4 s, validate with 119k edges 6.9 s (1k 0.5 s, 4k 2.6 s: linear) | invented data |
| Loader on a throwaway `neo4j:5.26.12-community` container (127.0.0.1:7699, no volumes, removed afterwards) | passed: fixture 0→14 nodes, 27 edges in 15 transactions; replay at batch size 5 unchanged; foreign graph version refused with nothing written; `02_integrity.cypher` returned no rows; `01_inventory.cypher` matched | `reports/runs/WORK-2026-11-08-026/` (ignored) |
| Loader on a 10k-paper invented graph (30,518 nodes, 119,516 edges) | passed: 19.3 s, 35 transactions; replay 14.7 s, counts unchanged; peak RSS 1.04 GB; integrity empty | same directory |
| `uv run pytest -q -p no:cacheprovider` | passed, exit 0; **273 passed, 1 skipped** (was 224) | `reports/runs/WORK-2026-11-08-026/pytest.log` |
| Mutation checks of the loader tests (unlabeled MATCH, one giant batch, guard removed) | each mutation failed the intended test; module restored byte-identical | inline |
| `research-network validate`, `freeze-audit-sample` (release quality config) and `analyze` (release analysis config) on the invented fixture | exit 0 each; synthetic protocol outputs only | `reports/runs/WORK-2026-11-08-026/cli/` |
| HTML sheet: CSV export logic run in Node 25; page rendered in headless Chrome; screenshot reviewed | passed: exported CSV scores cleanly, quoting round-trips, timezone offset correct, N cards rendered | tests in [test_edge_audit_split.py](../../tests/test_edge_audit_split.py) |
| `neo4j-five-year` compose service | not started; the integration run used a separate throwaway container | Phase 4 |

## Decisions

[D040 amendments](../decisions.md#d040-amendments): release graph port guard, optional
receipts with recorded gates, error categories.

## Open issues and limitations

- Loader timings used a 512 MB heap throwaway server and invented data, not the
  `neo4j-five-year` service or the release graph; Phase 4 repeats the load there.
- `build()` validates and re-derives the graph first; at 10k papers that dominates
  the ~19 s (about 7 s). Acceptable; not optimized.
- The sheet was exercised by scripted checks and one screenshot, not by a person
  clicking through it. Reviewers should try one edge and export before the full pass.
- The `.env` file still points `NEO4J_URI` at the pilot service; the guard handles it.

## Next step

Phase 2: OpenAlex acquisition (`data/interim/release-v1/works.jsonl`,
`reports/release-v1/acquisition.json`). Acceptance: derived DOIs for 13,617 roster
rows with no duplicates, rate-limit preflight logged, match rate reported at CP1.

## Corrections

None.
