# WORK-2026-11-11-004 — Task2B identity recovery and evaluation

| Field | Value |
| --- | --- |
| Status | completed feasible implementation/evaluation; independent semantic labels unavailable |
| Recorded | 2026-11-11T17:48:28+07:00 (Asia/Bangkok; entry creation time) |
| Finalized | 2026-11-11T18:18:24+07:00 |
| Contributor | Codex |
| Git state | Initially clean main at294e029; implementation checkpoint eab4dce; local only |

## Objective

Investigate DOI/name abstentions, freeze an independent-reference evaluation design,
implement bounded recovery and compare an isolated candidate against frozen v4/v3.
Preserve all earlier evidence, judgments, topics, public application and databases.

## Changes and findings

- Verified actual baseline graph/source counts and v3 decisions. All170 target IDs
  and683 positions have classifications, uncertainty and cached paper context.
- Seven DOI discrepancies have separate official/journal Crossref records and no
  explicit deposited version relation; retain all21 positions as ambiguous. Fixed
  singleton matching equality; original source bytes unchanged.
- Forty bounded free public requests:14 Crossref,20 ORCID person,5 ORCID works,
  one academic profile. Five public alias certificates; no independent gold claim.
- Final candidate `release-identity-v5-503aafe10a31`, graph SHA256
  `85ff09d0a5e6a42160a3c98fad3f63941a2b412213490f4c7f744ed5e2ba4d4e`.
  Gains253 versus v3 (185 formatting,50 declared-alias,18 missing-ID alternate);
  zero v3 losses/reassignments. Counts/denominators and limitations live in the
  [measured report](../../reports/quality-v5/task2b-v1/implementation-report.md).
- Probability assignment/pair draws and separate diagnostics frozen before recovery.
  Blind packets/A-B assignments and paired scorer implemented; actual scoring with
  zero independent labels correctly returns null semantic metrics/intervals.
- Existing materializer recomputes R7–R10; retained institution sets/exclusions,
  original evidence and protected topic/citation/publication content are preserved.

## Exact checks and outcomes

- `uv sync --locked --group dev --extra analysis`:exit0; baseline `uv run pytest -q`:
  573 passed/7 skips. Restored optional report extra using `uv sync --locked --group
  dev --extra analysis --extra report`:exit0; no dependency/lock changes.
- `uv run pytest -q tests/test_identity_recovery_v5.py tests/test_mentions_v5.py
  tests/test_release_acquisition.py`:115 passed,exit0. Final `uv run pytest -q`:
  603 passed/one existing empty-parameter skip,exit0.
- `uv run python -m scientific_network.resolve.candidate_v5 --config
  configs/identity-candidate-v5-release-v4-final.yaml --output-dir
  data/processed/identity-candidate-v5-release-v4-final --report-dir
  reports/quality-v5/task2b-v1/candidate-v4-final`:exit0. Separate full replay under
  `reports/runs/WORK-2026-11-11-004/replay-final-*`:exit0; all five data files and
  rankings byte-identical; comparison equal after recorded path normalization.
- `uv run research-network validate --input
  data/processed/identity-candidate-v5-release-v4-final/graph.json --config
  configs/quality-release-v1.yaml --require-size --output
  reports/quality-v5/task2b-v1/candidate-v4-final/structural-validation.json`:
  exit0,zero errors,derived support/weights and all size checks pass.
- Three-way comparison CLI and missing-reference scorer:exit0. Original341 raw
  work objects and40 public evidence objects hash-checked; all779 recorded original
  files and protected directory membership unchanged. Packet hashes match freeze.
  [Receipt](../../reports/quality-v5/task2b-v1/validation-receipt.json).
- Failures retained:ignored `inspect.py` shadowed stdlib (renamed);new fixture lacked
  a directory (fixed;114 pass/one fail before fix);intermediate comparison reason-key
  order varied despite equal values (sorted in final v5.5). Intermediate candidates,
  logs and reports preserved; final counts unchanged.
- Neo4j integration not run:no load/query/service changes. No DB, Explorer, topic,
  infrastructure, push or deploy work. Exact reproducible commands, input/config/
  transitive-code hashes and artifacts are in the linked README and receipt.

## Decisions and limitations

[Task2B D040 amendment](../decisions.md). Independent identity precision/recall/F1
and true merge/split rates remain unmeasured; source consistency and greater coverage
are not semantic accuracy. No promotion of this development candidate or production
replacement. Identity ceiling remains below the end-to-end affiliation target.

## Next step

Obtain independently adjudicated identity references using the frozen packets and
score v4/v3/revision on identical units. Continue targeted identity verification;
Task3 interfaces exist but affiliation enrichment alone cannot meet its target.
No Task3 work was started. Full handoff: [README](../../reports/quality-v5/task2b-v1/README.md).

## Corrections

Historical work entries and artifacts unchanged; superseding notes identify the
preserved intermediate Task2B run. No silent rewriting of prior audit judgments.
