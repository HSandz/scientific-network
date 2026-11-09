# WORK-2026-11-09-004 — Source-backed agent evaluation and scoring

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-09T12:36:35.109772+07:00 (Asia/Bangkok; started 01:52 +07:00) |
| Work performed | 2026-11-09 +07:00 |
| Contributor | Codex coordinator; isolated evaluator contexts /root/reviewer_a and /root/reviewer_b |
| Related task | WORK-2026-11-09-003 |
| Git state | main, checkpoint A `03173df`; review/scoring checkpoint follows |

## Objective

Complete blind topics before edge exposure, inspect all assignments from sources, preserve disagreements, adjudicate and score with honest AI scope.

## Changes and findings

- Both fresh A/B contexts completed 60 blind topic judgments over 50 papers, frozen before edge exposure. All 350 edge assignments/300 unique edges completed; 11 overlap conflicts source-adjudicated with initial decisions retained. Completion receipt binds 23 files.
- Global AI-assessed precision: 176/200 = 88.00%, Wilson 95% interval 82.7657%–91.8020%; 23 incorrect, one unverifiable, zero missing. Course point comparison and both project precision checks fail. Per-type supplements stay separate. Overlap agreement 39/50 (78%), Cohen kappa 0.1851851852.
- Embedding topic micro P/R/F1 .68627451/.35353535/.46666667, coverage 45/50; phrase .92857143/.13131313/.23008850, coverage 13/50. Paper-normalized effective weight 50; zero unreviewable, one considered empty set. Topic overlap exact agreement 10/10 does not establish independent gold accuracy.
- Actual model/provider IDs remain unknown. Human validation not performed; evaluator independence/verified course accuracy not established. Main edge evidence: 123 primary, 227 secondary-only assignment rows; 349 reuse construction source, one independent main source.
- Source arrays `author.observed_orcids` remain in raw/full works but are omitted from resolver conflict handling and projected source packets. Nine overlapping identifier disputes independently checked in raw arrays; detailed finding in `docs/post-audit-findings.md`. Graph/classifier/sample unchanged: `release-9d4a6fb20f63`, graph SHA256 `c23ef82c97fcb539b4b1c279e8ff42378bdb102e80fe851acf1a42e816a727b8`.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `uv run pytest` | 0; 419 passed/1 existing empty-parameterization skip, 22.12s | ignored `reports/runs/WORK-2026-11-09-004/pytest-checkpoint.log` |
| `uv run research-network schema` | 0; valid schema JSON | same run directory/schema.json |
| `score-agent-review` with complete bound inputs | 1; outputs written, numeric gates fail; no provenance refusal | exact command in `docs/reproduce-agent-evaluation.md`; run log `score-agent-review.log`; `reports/release-v3/*agent.json` |
| Structural/size validation | passed | `reports/release-v3/structural-validation.json` |
| Frozen hashes/read-only Neo4j 7689 | 66 hashes pass, 52,415 nodes/275,438 edges; six integrity queries zero rows | `frozen-database-verification.json` |
| Secret/tracked-content check | 1,280 tracked files, two actual configured secrets checked, zero matches; no tracked PDFs/raw payloads/credentials | local diagnostic; no secret text recorded |
| External URLs | eight report DOIs pass; GitHub HTTP504 not_verified; SSH remote refs read successfully, no tags | `report-external-link-checks-v2.json`; no external mutation |

Preparation errors preserved in run records: missing output directory and CSV field-size limit resolved; legacy check fields inconsistent with unverifiable votes corrected in versioned A/B completion receipts without changing verdicts. Coordinator initially checked singular ORCID only and did not reproduce array conflicts; actual raw array inspection corrected that diagnostic before adjudication. Smoke report rendered 18 A4 pages/six figures; a later smoke refused packaging while report changed. Neither is the final package. Runtime clock jumped; actual timestamps recorded without inferred review duration.

## Decisions

See D040 dated execution amendment in `docs/decisions.md`. No post-audit graph correction, classifier tuning or sample change. Unknown provenance remains unknown.

## Open issues and limitations

Source/model reuse and judge error limit all scores. Final report/PDF/package follow in WORK-005/006. Real team facts/course rules and separately authorized external delivery remain pending; no human annotation wait.

## Next step

Finish measured report/README, render and inspect the local PDF, then package permitted committed sources without raw data or credentials.

## Corrections

None.
