# WORK-2026-11-08-035 — Topic-review allocation and Phase 8 tooling

| Field | Value |
| --- | --- |
| Status | partial |
| Recorded | 2026-11-08 14:10 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-08 +07:00 |
| Contributor | Codex, at the user's request |
| Related task | [WORK-2026-11-08-034](2026-11-08-034-phase-8-report-draft.md) |
| Git state | Base `main` commit `f78c6fc`; local checkpoint commit follows this entry |

## Objective

Apply the user's topic-review allocation (30 papers per reviewer, 10 shared),
prepare hash-bound blind review packets, and finish Phase 8 scoring support that
does not require inventing human annotations.

## Changes and findings

- Added deterministic venue-stratified assignment generation and the
  `prepare-topic-review-packets` command. Reviewer A/B each receive 30 papers,
  with 12 AAAI and 18 IJCAI apiece; the 10-paper overlap contains four AAAI and
  six IJCAI papers. The union is all 50 frozen test papers (60 judgments).
- Generated reviewer-specific CSV and HTML packets and
  `reports/release-v1/audit/topic-review-allocation.json`. The master sheet and
  frozen test manifest are unchanged. The HTML hides predictions, fixes the
  reviewer ID and requires a note when no topic leaf applies.
- Bound the allocation manifest and all four reviewer sheet hashes in
  `reports/release-v1/freeze.json`; the frozen graph hash remains unchanged.
- Before the local checkpoint commit, corrected a portability issue found in the
  frozen CSVs: both CSV writers now emit LF, the existing edge/master/reviewer
  sheets were normalized, and dependent allocation/freeze hashes were refreshed.
  The graph hash is unchanged.
- Rechecked Docker: `neo4j-five-year` is healthy. Prior v1/v2 inventory, integrity
  and replay receipts remain recorded in [WORK-031](2026-11-08-031-release-neo4j-loads.md);
  this task changes no loader/query code, so no database reload was needed.
- Added `score-topic-review` to compare graph v1 phrase labels with graph v2
  embedding labels. It weights each paper to total one, scores overlap judgments
  at one half each, and reports agreement only on the overlap. Disagreement stays
  in the data; no consensus labels are manufactured. The command refuses blank
  reviewer packets, so no evaluation score was produced.
- Updated D040, evaluation instructions, report draft, README and status. Phase 8
  remains incomplete until human reviews are returned and scored.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `uv sync --locked --group dev --extra analysis` | passed, exit 0 | audited 36 installed packages |
| `uv run pytest` | 363 passed, 1 skipped, exit 0 (final run) | `reports/runs/WORK-2026-11-08-035/pytest-final4.log`; skip is the existing empty parameterized stage case |
| `uv run pytest tests/test_topic_eval.py tests/test_topic_review_sheet.py -q` | 8 passed, exit 0 | assignment, prediction-blindness, weighting, overlap and complete scorer fixture |
| `uv run research-network prepare-topic-review-packets --master-sheet reports/release-v1/audit/topic-label-sheet.csv --topic-test data/manifests/release-v1/topic-test.jsonl --taxonomy configs/topics-release-v1.yaml --output-dir reports/release-v1/audit` | passed, exit 0; A=30, B=30, union=50, overlap=10 | reviewer files and allocation manifest under `reports/release-v1/audit/` |
| Re-run `prepare-topic-review-packets` with output `reports/runs/WORK-2026-11-08-035/reproduced-packets-final` | passed; CSV/HTML hashes match the delivered packets | `reports/runs/WORK-2026-11-08-035/topic-packets-reproduce.json` |
| `uv run research-network validate --input data/processed/release-graph-v2/graph.json --config configs/quality-release-v1.yaml --require-size --output reports/runs/WORK-2026-11-08-035/graph-v2-validation.json` | passed, exit 0; 52,415 nodes, 275,438 edges, 124,619 factual edges, 10/10 relations | structural only; accuracy not measured |
| `uv run research-network score-topic-review --help` | passed, exit 0 | CLI exposes the completed-review scoring inputs |
| `uv run research-network score-topic-review --reviewer-a reports/release-v1/audit/topic-label-sheet-reviewer-A.csv --reviewer-b reports/release-v1/audit/topic-label-sheet-reviewer-B.csv --output reports/runs/WORK-2026-11-08-035/topic-eval-should-not-exist-final.json` | refused as expected, exit 1; no output created | blank packets fail completion check; this is not an evaluation result |
| `git diff --check`, local README/report link check, packet/freeze/hash check | passed | status remains under 60 lines; frozen graph SHA matches `freeze.json` |
| Follow-up CSV/hash portability check | passed; edge sheet, topic master, allocation manifest and both reviewer CSV hashes match worktree bytes, staged Git blobs and freeze references | regenerated reviewer packets are byte-identical to delivered CSV/HTML sheets; graph SHA unchanged |
| Live read-only Neo4j v2 recheck after Docker start | passed; 52,415 nodes, 275,438 relationships, all ten predicates, only v2 graph version, zero integrity-query rows | `reports/runs/WORK-2026-11-08-035/neo4j-live-inventory-integrity.json` |
| `uv sync --locked --group dev --extra analysis` (follow-up) | passed, exit 0 | 36 installed packages audited |
| `uv run pytest` (after LF-writer change) | 363 passed, 1 skipped, exit 0 | `reports/runs/WORK-2026-11-08-035/pytest-line-endings-fix.log` |
| `prepare-topic-review-packets` reproduced after LF-writer change | passed, exit 0; A=30, B=30, union=50, overlap=10; generated CSV/HTML hashes match delivered packet hashes | `reports/runs/WORK-2026-11-08-035/packets-reproduced-line-endings/` |

One initial freeze-update helper exited 1 because it expected a manifest self-hash
inside the saved manifest; the helper was corrected to store that hash in the
outer freeze record. One initial synthetic scorer test lacked a `Path` import; it
was fixed before the final passing suite. Neither failure altered source inputs or
the graph.

## Decisions

See the dated D040 amendments in [`decisions.md`](../decisions.md): the user chose
30/30 with 10 shared, and topic metrics weight each paper equally while retaining
separate reviewer labels on overlap papers.

## Open issues and limitations

Actual edge reviews, topic annotations, reviewer identity/contribution details,
course AI-use disclosure and the lecturer-access choice are outstanding. No edge
precision or topic quality score is available. The release remains uncertified.

## Next step

Reviewers complete and return the A/B topic CSVs and edge-review exports. Run
`score-topic-review` and `score-edge-audit`, then finish report results, enter
real team details, and verify the final PDF page count.

## Corrections

2026-11-08 14:41 +07:00: The follow-up hash audit found CRLF/mixed line endings
in frozen CSVs while Git stores LF. Writers now explicitly emit LF and all
freeze/allocation references match the canonical staged bytes. The first live
Neo4j helper attempt stopped before connecting because `python-dotenv` could not
infer `.env` from stdin; rerunning with the explicit ignored `.env` path passed.
