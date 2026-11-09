# Corrected release v4 and prospective edge audit v2

This is a separately versioned correction, not an edit of release v3. The user
adopted the dated [amendment](../../docs/correction-amendment-2026-11-09.md).
Graph `release-d3c788c3114a` has 47,875 nodes, 225,731 edges, 32,189 researchers
and 110,026 factual edges. The graph SHA256 is
`6f665a946cec7473889a09e883a3ef88469de867cb1054d6a3b145239ea59c90`.
Global observed/singular ORCID evidence withholds conflicting IDs. Frozen topic
predictions, taxonomy and publication/citation claims are unchanged. See
[reproduction](../../docs/reproduce-remediation-v4.md), [change manifest](change-manifest.json),
[content freeze](content-freeze-v4.json) and [fresh analysis](analysis.json).

## Measured results and limits

The single precommitted-seed prospective audit completed all 350 assignments
(300 distinct edges): 200 global, ten per relation, 50 overlap. Global result:
**193/200 = 96.50% AI-assessed edge precision**, Wilson 95% interval
**92.95%–98.29%**; one incorrect, six unverifiable, zero missing. Unverifiable
counts incorrect. AI-only numeric point/Wilson checks pass. The supplements are
separate: R10 9/10, R9 8/10, other eight relations 10/10; n=10 intervals remain
wide. Overlap agreement is 49/50 (98%), Cohen kappa 0.6598639456. The six global
`wrong_identity` categories are unverifiable mappings, not six proved false
identities. See [complete results](audit-results-agent-v2.json).

`evaluation_kind=ai_agent_review`, `human_validation=not_performed`,
`reviewer_independence=not_established`, `verified_course_accuracy=not_established`.
Fresh contexts are not established independent validators. All 350 assignment
judgments reuse construction sources; 215 are primary-source and 135 secondary-only.
Wilson intervals exclude evaluator errors and shared-model/source bias.
A/B froze their original exports before one source-backed coordinator adjudication;
unknown model/provider/runtime IDs remain unknown. See [freeze](evaluation-freeze-v2.json),
[completion](completion-receipt-v2.json), [unchanged exports](completed/) and
[actual adjudication start](adjudication-start-receipt-v2.json).

The old errors motivated this correction. Seven semantic sampled edges repeat;
no new global edge overlaps any old sampled edge. Of 516 supporting papers,
24 overlap the earlier explicit packet frame. Of 237 batched raw OpenAlex
response hashes, 177 overlap: these are response hashes, **not 177 papers**.
See [exposure](sample-exposure-v2.json). This is not a controlled improvement
estimate over the original 176/200 (88%) failed audit, which remains preserved.

All 13,606 matched works, 65,469 raw authorship objects (including observed ORCID
arrays) and reference arrays were checked against 341 hashed cached responses:
[source verification](source-population-verification-v2.json). CITES packets
initially omitted full target records; during review the original cached target
records were supplied in additive [source supplements](source-supplement-manifest-v2.json),
without changing frozen base packets or giving verdicts. B made ten bounded
same-provider live supplemental reads. For two R10 aggregates B inspected 10/35
CAS generative supports and 17/107 USTC representation supports. The frozen binary
criterion is at least three source-backed papers, plus the recorded additional
inspection; this is **not exhaustive semantic verification of support_count**.
Complete source availability/hash checking is not semantic evaluation of every
support. Evidence depth and inspection limits remain part of interpretation.

Affiliation coverage still fails 80%: 48,259/65,469 matched byline positions
(73.71%), or 48,259/65,507 all official positions (73.67%). Accepted-only
48,259/50,437 (95.68%) is a conditional diagnostic. The old topic references/scores
remain historical and exposed: embedding/phrase micro F1 0.46666667/0.2300885,
precision 0.68627451/0.92857143, coverage 90%/26%; both miss the 0.95 precision
target. Exact [prediction/evidence/taxonomy equality](historical-topic-reuse-v2.json)
supports reuse, not a new untouched test. No model or threshold was tuned.

## Reproduce without overwriting evidence

A fresh clone does not contain permitted ignored raw caches, immutable works,
full graphs or source packets. Restore only from the original permitted local
sources, keeping exact paths and hashes in content/evaluator/completion freezes;
stop on any hash mismatch. Do not reacquire the corpus or regenerate a sample to
substitute for these inputs. Supplement and adjudication raw sources also need
restoration at their recorded paths. The scorer reads bound files and emits a new
result; use an unused output path (the example must not already exist):

```bash
uv run research-network score-agent-edge-review \
  --evaluation-freeze reports/release-v4/evaluation-freeze-v2.json \
  --completion-receipt reports/release-v4/completion-receipt-v2.json \
  --protocol configs/evaluation-agent-release-v2.yaml \
  --edge-ledger reports/release-v4/completed/edge-ledger.jsonl \
  --graph data/processed/release-graph-v4/graph.json \
  --quality configs/quality-agent-release-v2.yaml \
  --graph-freeze reports/release-v4/content-freeze-v4.json \
  --graph-summary reports/release-v4/graph-summary.json \
  --rubric reports/release-v4/reviewer-rubric-v2.md \
  --edge-packets reports/release-v4/audit/edge-review-sheet-reviewer-A.csv reports/release-v4/audit/edge-review-sheet-reviewer-B.csv reports/runs/WORK-2026-11-09-013/sources/A-edge-sources.jsonl reports/runs/WORK-2026-11-09-013/sources/B-edge-sources.jsonl \
  --edge-reviews reports/release-v4/completed/A-edges.csv reports/release-v4/completed/B-edges.csv \
  --adjudications reports/release-v4/completed/adjudications.csv \
  --adjudication-ledger reports/release-v4/completed/adjudication-ledger.jsonl \
  --adjudication-start-receipt reports/release-v4/adjudication-start-receipt-v2.json \
  --edge-output reports/runs/WORK-2026-11-09-013/REPRODUCTION-UNUSED-results.json
```

The original scoring command used the committed result path and ran once, exit 0.
Reproduction is a deterministic verification, not authorization for a new audit.
Tests and the isolated Neo4j checks are recorded in WORK-010 through WORK-014.
The current report is [report.md](../final-report/report.md). Its local package
receipt will be `local-package-receipt-v2.json` after the committed source build;
that later QA receipt is intentionally outside its own source snapshot.
No push, tag, Site publication, invitation or submission is performed. Real student
names/IDs/contributions, lecturer access and course AI-use rules remain pending.
