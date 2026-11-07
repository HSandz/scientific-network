# WORK-2026-11-06-004 — Selective five-year PDF headers and source review

| Field | Value |
| --- | --- |
| Status | partial |
| Recorded | 2026-11-06T19:50:25+07:00 |
| Finalized | 2026-11-06T20:10:26+07:00 |
| Work performed | 2026-11-06 (Asia/Bangkok, UTC+07:00) |
| Contributor | Codex |
| Related task | [WORK-2026-11-06-003](2026-11-06-003-five-year-diagnostics.md) |
| Git state | main at 66e692d; previous uncommitted work preserved; no project commit/push |

## Objective

Proceed with selective PDF/header extraction and author/affiliation source triage
for exactly the 68 frozen development diagnostics. Preserve every old/new held-out
ID, metadata/raw artifact, historical graph and release threshold. No graph import.

## Changes and findings

- Added `extract-diagnostics` CLI, `preprocess/diagnostics.py`, separate
  `configs/five-year-headers-v1.yaml` and semantic tests. Historical extraction
  code, configs and frozen sample remain unchanged. D024 records the boundary.
- Before source access, verify every frozen sampling input, metadata/manifest/
  membership/selection/reserved-test hash, selected IDs, development group status
  and held-out title/PDF URL guards. Reject changed or duplicate inputs.
- **68 PDFs available locally, 283,508,927 bytes; 66 headers parsed / two review**.
  RSS 2025 p046/p108 return GROBID HTTP 500; rendered text is visible but
  `pdftotext` returns no first-page text. OCR/alternate conversion is pending.
- **47** papers have parsed affiliation blocks. **62** header titles and **48**
  complete roster bylines agree; **45** papers pass title/detail/roster/unique-name
  binding checks. **255** deduplicated author–paper–institution candidates;
  **56** exact author-specific provider institution matches. All remain review,
  with stable IDs/PDF/TEI hashes and support locators; no accepted triples/people.
- Printed development inspection on **five papers**: MLSys PDF corroborates roster
  full byline and five numbered marker mappings; metadata remains withheld. TEI
  omitted two institution entities and split another name. COLT editors were
  parsed as authors while the second actual author was omitted; its positional
  candidates remain unresolved. IJCAI shared printed block supports two candidate
  positions. RSS failure pages were rendered/inspected; no OCR installed.
- **Zero held-out access, new OpenAlex requests, external consolidation, model
  downloads, identity aliases, accepted identities/triples or graph imports**.
  PDFs, TEI, abstracts, raw logs and full candidate rows stay ignored/local.
- Base Neo4j and GROBID were healthy before collection: **154 nodes / 211 edges**.
  GROBID image `grobid/grobid:0.8.2-crf`, image ID
  `sha256:a1bfe7533e13ae9514d2b7d5e6cd2fff391c57d60bc3e48393471f90ad1718e0`.
  After collection Docker became unreachable. Desktop status/restart failed;
  post-run DB counts are unavailable. No DB write commands were issued.
- Updated current status, roadmap, workflow, instruction implementation paragraph,
  project specification, README and report. Native Site **v11 succeeded**, same
  public project/URL/audience. All 20 Plan sections and historical graph payload
  preserved; new aggregate header report/JSON downloads published.

## Verification

All raw command/check outputs are under ignored
`reports/runs/WORK-2026-11-06-004/`. Commands ran from repository root unless noted.

| Command/check | Outcome and exit code | Evidence |
| --- | --- | --- |
| `uv run pytest` | **130 passed in 3.44s**, exit 0 | `pytest-initial.txt`; no subsequent code changes |
| `uv run research-network extract-diagnostics --help` | Exit 0 | `cli-help.txt` |
| `uv run research-network schema` | Exit 0 | `schema.json` |
| `uv run research-network extract-diagnostics --input data/interim/five-year-acquired-v1/papers.json --manifest data/manifests/five-year-roster-v2/corpus_manifest.jsonl --splits data/manifests/five-year-splits-v1 --config configs/five-year-headers-v1.yaml --output data/interim/five-year-headers-v1 --cache data/raw/five-year-source-cache-v1` | First pass/replay **exit 1** for two preserved parse-review records; summaries identical | `extraction.txt`, `extraction-replay.txt` |
| Frozen/protected integrity | **7,297 files unchanged**; every original/expanded/new test file preserved; held-out overlap zero | `protected-before.json`, `integrity.json` |
| Evidence/cache validation | **269 distinct objects hash-verified**, zero new OpenAlex request records | `integrity.json` |
| Service preflight | Neo4j/GROBID HTTP 200; GROBID true; read-only Neo4j 154/211 | `services-before.json` |
| Service postflight | HTTP ConnectError; Docker daemon unreachable; no live count reconciliation possible | `services-after.json` |
| `docker desktop status` / `docker desktop start` | Exit 1; missing `/opt/docker-desktop/bin/com.docker.backend`; no Windows launcher/interop found | `docker-restart.txt` |
| Printed source checks | Five first pages inspected; observations only, not independent annotations | `data/manifests/five-year-printed-review-v1.json` |
| Site static build | 20 Plan sections / 264 unique IDs / zero iframe, object or embed; payload SHA unchanged | `site-build-check.json` |
| Browser local/live | Tabs, desktop1440/mobile390, no overflow or console errors, two new downloads HTTP200; live v11 counts/JSON verified | native browser checks and publication receipt |
| Large unignored new files | None; PDFs/raw/interim remain ignored | Git file inventory |
| `git diff --check` | Exit 0 | final whitespace check |

Initial routine inspection used nonexistent `tests/test_pipeline.py`; corrected by
reading the relevant modules/tests. One ad-hoc plain-Python import did not use the
locked environment and failed; subsequent project commands used `uv run`. These
errors did not change data or invalidate the passing suite. The first post-service
script stopped on ConnectError; a bounded second check recorded unavailability
and completed offline hash verification. Two GROBID failures are retained rather
than hidden by retries or empty-success outputs.

New method: `five-year-development-headers-v1`; sampling remains
`five-year-diagnostics-v1`; metadata remains `five-year-diagnostic-metadata-v1`.
Config/input/output hashes are in extraction `inputs.json` / `summary.json` and the
[aggregate report JSON](../../reports/five-year-headers-v1.metrics.json). Input
metadata SHA: `af4fb53e0623ccaca9a668fdbd68d8e2e162de779fa3161f59761cb6b0c0d8f2`.
Extracted papers SHA: `ce769d553056e1e8c2ed43d49b513645ee4e364bc4de116092247b7d91cc832c`.

## Artifacts

- [Measured PDF/header report](../../reports/five-year-headers-v1.md) and aggregate JSON.
- `data/interim/five-year-headers-v1/{papers,source-review,summary}.json` (ignored).
- [Small printed review ledger](../../data/manifests/five-year-printed-review-v1.json).
- [Site v11 publication receipt](../reference/sites-headers-publication-2026-11-06.json)
  and immutable `sites-headers-{plan,report}-2026-11-06.md` snapshots.
- Site source commit: `bc758ef0ca261521775288fdb3e4df2d4ba74822`.

## Decisions

[D024](../decisions.md#d024--frozen-development-pdf-headers-and-source-candidates-2026-11-06)
keeps all candidates unaccepted, requires complete byline/author-specific evidence,
and permits withheld PDFs for source inspection without identity/status overrides.
D022/D023 scope, assignments and scientific gates remain unchanged.

## Open issues and limitations

Two RSS text/conversion failures; COLT editor contamination, incomplete/split
institution entities and other byline/title disagreements remain. The original
MLSys metadata failure is clarified by printed evidence but not rewritten.
Public-ORCID publication corroboration and canonical works/identities remain
unimplemented for this five-year sample. Candidates and agent source inspections
are not independent accuracy, precision, recall or F1 measurements.

No five-year graph or size/quality release claim. Historical explorer399/533 and
candidate402/538 artifacts are unchanged, with no imports. Docker must be restored
outside the unavailable Desktop backend before further service work; end-state
DB contents were not rechecked. No task-owned collection or preview jobs remain
running after teardown. No project commit/push; unrelated edits preserved.

## Next step

Restore Docker availability, then add a versioned source-review-aware metadata/
header path: preserve the MLSys printed byline observation, correct COLT editors
and RSS text conversion, corroborate canonical works/public ORCID publications and
inspect author-specific printed markers. Require accepted evidence before a new
isolated graph; preserve every frozen test ID and unaccepted support. Acceptance
check: replayable source-bound decisions, no held-out overlap and meaningful tests.

## Corrections

None.

## Extraction checkpoint

2026-11-06T19:54:52+07:00: New extraction config and D024 written before PDF access.
130 offline tests passed (3.44s); offline `extract-diagnostics --help` exit 0.
Base Neo4j read-only 154/211; GROBID HTTP 200 / true. Extraction running with
immutable per-record checkpoints under `data/interim/five-year-headers-v1/`;
console evidence in `reports/runs/WORK-2026-11-06-004/extraction.txt`. Exactly
68 frozen development IDs validated; withheld MLSys PDF is source-review only.

### Source-review checkpoint — 2026-11-06T20:00:12+07:00

56/68 records checkpointed as parsed; no held-out access or graph writes.
Printed MLSys page 1 corroborates the roster full byline and five marker mappings,
while the citation export uses an initial. Acquisition remains withheld. TEI missed
two institution entities and preserved a broken line-wrap name; source observations
are candidates only. One IJCAI printed shared block corroborates two candidate
positions. Draft notes and source-only page rendering stay ignored in this run dir.

### Final measurement checkpoint — 2026-11-06T20:07:18+07:00

All 68 PDFs cached; 66 parsed / two GROBID HTTP 500 retained. Replay summary
identical, both runs exit 1. 255 affiliation candidates / 56 exact metadata matches
remain unaccepted; 45 papers pass binding checks. Five source notes saved, no
identity overrides. All 7,297 protected files unchanged; 269 source objects
verified; zero held-out overlap/new OpenAlex calls/DB writes. Docker became
unreachable after collection; Desktop restart failed (missing backend), so post
DB counts are unavailable. Public report and native Site passed local 1440/390
checks, 20 Plan sections, 264 unique IDs, zero embeds/errors and two HTTP 200
new downloads. Site publication is pending; collection/preview processes tracked
in this task and no collection jobs remain running.
