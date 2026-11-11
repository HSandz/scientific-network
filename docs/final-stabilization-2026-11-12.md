# Final repository stabilization — 12 November 2026

## Initial state

- Branch `main` was at `c4daf1d`, equal to `origin/main`. The last commits included
  the compiled research report and prior cleanup receipts.
- The worktree already contained unfinished Task2D identity changes in
  `identity_evaluation.py`, `identity_review.py`, `identity_validation.py`,
  `identity_integrity.py`, and WORK-006. They were preserved separately. The
  DOI tests and WORK-001 were already the in-progress stabilization changes.
- Production graph v4 was the frozen `release-d3c788c3114a` artifact. No report,
  figure, PDF, graph, source cache or database was edited in this task.

## Confirmed findings and local fixes

### DOI acquisition

Current `openalex_release.py` binds batch results to requested DOIs, retries
missing results through the singleton endpoint, and checks returned DOI, title
and author count before accepting a match. Duplicate DOI records qualify for
official-landing-page disambiguation only after DOI/title/count agreement. A
singleton mismatch remains review; a landing-page match cannot rescue a duplicate
with the wrong DOI.

Added two focused regressions in `tests/test_release_acquisition.py` for a wrong
DOI returned again on singleton retry and a wrong-DOI duplicate linked to the
official page. No runtime acquisition correction was needed. The seven historical
v4 DOI disagreements remain ambiguous: titles and bylines do not prove version
equivalence, and no graph history was rewritten.

### Flagged graph cases and review packets

The four AI-flagged cases remain in the issue ledger, reviewer CSV contexts and
post-blind pages: `b8ad1484…` and `26b21916…` (RESEARCHES_TOPIC), `cc8efc4b…`
(AUTHORED), and `6e057242…` (CONTRIBUTES_TO_TOPIC). The Luna evidence review was
AI-assessed (`gpt-6-luna`, high effort); it is not independent human ground truth.
The topic challenges concern substantive support thresholds. The authorship case
retains conflicting official/canonical display-name evidence; the raw OpenAlex
authorship name matches the byline. No production edge was removed.

The frozen 80-edge sample hash remains
`2e5cb63ffe6c6f93c349bd730953c4c06f5cb782e020f9611b7a6446a10ea00d`. The 20
random IDs, six diagnostic IDs, and all four flagged cases remain represented.
Each reviewer has 27 unique cases, answers are blank, AI concerns are absent from
the initial sheets and present only in the post-blind pages, and both CSV schemas
match. Diagnostic-only cases remain outside the probability sample. The issue
ledger's evidence-ID lists are not fully reconciled with packet context, and some
locators use different fragment notation. Frozen packets were left unchanged.

### Explorer filter reliability

The public Explorer allowed venue/year filters on the default 10-predicate
heterogeneous preset, while the API's documented contract requires the
Researcher → Paper → Topic preset. A live IJCAI filter interaction remained in a
loading state; a direct read-only request for the incompatible query returned
HTTP 422 with that preset requirement. The local frontend now switches to the
supported preset when a venue or narrowed-year filter is applied, and clears
those paper filters if the user switches away. The change is covered by a focused
Playwright regression. It was not deployed.

## Inspected and intentionally unchanged

- Seven historical DOI disagreements, all four AI-flagged edges, and their source
  locators remain unresolved evidence, not automatic graph corrections.
- Historical identity uncertainty, 73.71% affiliation coverage against the 80%
  target, and inferred-topic limitations are already documented. No author model,
  affiliation reconstruction, corpus collection or graph rebuild was warranted.
- Task2D work remains uncommitted and has no dedicated candidate-binding/source-
  verifier regression coverage. The passing suite does not complete that work.
- Human review and verified course accuracy remain unestablished. No full 80-edge
  audit or 511-case identity review was rerun.

## Validation performed

| Check | Result |
| --- | --- |
| `uv sync --locked --group dev --extra analysis --extra report` | Passed |
| `uv run pytest -q` | 650 passed, 1 skipped (existing empty CLI-stage parameter set) |
| Release-v4 `research-network validate --require-size` | Passed, zero errors, all 10 relation types present; structural only |
| `npm run build` | Passed; existing advisory for an ECharts chunk over 500 kB |
| Focused Playwright filter regression | 1 passed |
| Playwright contract suite | 8 passed |
| `git diff --check` | Passed |
| Frozen v3/v4, works, configs and 80-edge sample hashes | Matched their recorded receipts |
| Human packets | 20 random, 6 diagnostics, 4 flagged; 27 unique/member, blank answers, post-blind concerns and CSV schemas checked |

V4 graph SHA-256 is
`6f665a946cec7473889a09e883a3ef88469de867cb1054d6a3b145239ea59c90`; v3 graph
SHA-256 is `c23ef82c97fcb539b4b1c279e8ff42378bdb102e80fe851acf1a42e816a727b8`;
retained works SHA-256 is
`2b7f3bc15ad46398e9f55ece060536050215238355e9580d2689f00005f55047`. The
structural report is `reports/runs/WORK-2026-11-12-001/v4-structural-validation.json`.
Structural validity does not establish semantic accuracy. No Neo4j integration
check or write was run.

The read-only live smoke loaded graph summary and analytics; Bo An search,
inspection, evidence navigation and graph API requests returned HTTP 200. The
browser recorded no console errors before or during the filter check. The filter
request did not settle in the browser; the separate direct API response was HTTP
422 as described above. The local regression verifies the corrected request and
filter reset behavior without changing the public deployment.

The existing 1,754-member ZIP passed its recorded SHA-256 and CRC checks. It is
bound to source commit `f3b00d4`, not the current checkout; no replacement package
or PDF was generated.

## Reproduction and remaining blockers

Installation uses the locked `uv` command above. Reproducing graph or analysis
requires restoring the ignored v3/v4 graphs, matched works, roster and original
source caches and verifying their recorded hashes; current API reacquisition is
not byte-identical restoration. See [the reproduction guide](reproduce-remediation-v4.md).
The repository is private (`gh repo view` reports `PRIVATE`; an anonymous GitHub
request returns 404), so lecturer access to source is unresolved. The local package
is historical and ignored. The public Explorer URL remains available, but does not
provide reproducible source/cache access. Official team/course details and delivery
authorization remain pending.

## Changed files and final state

Stabilization changes are limited to the DOI regression tests, Explorer filter
handling and its regression, this report, status and work-log records. Unrelated
Task2D files remain uncommitted. The stabilization set is committed locally from
`c4daf1d`. No LaTeX report, figure or PDF, graph/database, deployment, remote ref
or external submission was changed.
