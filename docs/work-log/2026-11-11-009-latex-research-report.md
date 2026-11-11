# WORK-2026-11-11-009 — Final cleanup and LaTeX research report

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-12T00:48:15+07:00 (Asia/Bangkok) |
| Work performed | 11–12 November 2026 |
| Contributor | Codex, GPT-6.1 Sol |
| Related task | [WORK-2026-11-11-008](2026-11-11-008-final-cleanup-submission-readiness.md) |
| Git state | `main` at `bcdd3fd` when work began; unrelated uncommitted Task2D files and WORK-006 preserved and not included in this task |

## Objective

Complete the two small cleanup fixes and frozen human-packet regeneration, then
write and compile a substantive academic report from the frozen production-v4
graph. Preserve all graph, source and review decisions; move the supplied UET
logo unchanged; retain unrelated Task2D work.

## Changes and findings

- Updated `sprint_audit._postblind_html` to choose nonempty `potential_issue`,
  then nonempty `reason`, then the neutral fallback, with HTML escaping retained.
  Made the additional initial-review instructions conditional on metadata that
  confirms a post-blind page. Added regressions for null/empty concerns, escaping,
  flagged/unflagged packets and legacy callers.
- Regenerated both reviewers' HTML and flagged post-blind pages. The original
  80-edge sample hash remains
  `2e5cb63ffe6c6f93c349bd730953c4c06f5cb782e020f9611b7a6446a10ea00d`. The
  20 random IDs, six risk IDs and four flagged IDs remain in the packet manifest;
  each reviewer has 27 unique cases, selection tags are retained, answers are
  blank, and initial pages omit AI concerns. Updated manifest hashes cover the
  changed HTML files; CSVs and allocation data remain byte-identical. The Luna
  decisions and frozen production graph were not changed.
- Created the standalone project at `report/latex/`: eight chapters, three
  appendices, editable `report-info.tex`, two TikZ diagrams, reusable tables,
  source manifest for ten copied release figures, verified BibTeX sources,
  Makefile, README and ignored build directory. The manuscript reports v4 as
  production and v5 only as an identity-sensitivity scenario. It describes the
  193/200 v4 result as AI-assessed, not human-verified accuracy, and records the
  73.71% affiliation coverage gap. Extracted PDF text is approximately 13,375
  words.
- Moved the supplied 1200×1200 RGBA logo into `assets/uet.png` without alteration
  (SHA-256 `ffc8994bb202aaac7b7cbfa6e07346ad72fad89b5d725e06341530bbf083b044`).
  Copied report PNGs match their recorded source bytes.
- The bounded delegated scientific review completed, but its agent reports that
  no explicit model/reasoning override or inherited values were exposed. The
  report states this limitation and does not claim the review was GPT-6-Luna
  High. The separate sprint-audit model and effort remain as recorded in its
  frozen manifest.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `uv run pytest -q tests/test_sprint_audit.py tests/test_edge_audit_split.py` (repo root) | Passed; 51 tests | Cleanup regression coverage |
| `make clean && make` (`report/latex/`) | Passed; latexmk/pdfLaTeX and BibTeX produced a 50-page A4 PDF (2,132,807 bytes) | `report/latex/build/main.pdf`; SHA-256 `f26f507056df2ba77ba1e6fa673637c63d2b862273c1fda47f4e5e53674d8ade` |
| LaTeX/BibTeX/reference check | All 15 cited keys resolve; all bibliography entries are cited; no missing files, undefined citations/references or replacement characters | `report/latex/build/main.log`, compiled PDF |
| PDF visual inspection | Cover/logo, landscape schema, pipeline, architecture, audit and results tables, analytical plots, appendices and bibliography inspected; cover and appendix pagination corrected | Rendered pages; schema page is rotated landscape |
| Packet, freeze and source-copy checks | Passed: sample and packet hashes match; reviewer IDs/tags and blank answer fields verified; initial concerns hidden and post-blind details present; graph/logo hashes and ten figure-copy hashes match | `reports/final-quality-sprint/sampling-manifest.json`, `report/latex/figures/SOURCES.md` |
| `git diff --check` | Passed | Working tree |
| Official citation URL / metadata checks | Proceedings and tool documentation links returned HTTP 200 (some canonical redirects); Reimers pages verified against ACL Anthology as 3982–3992 | `report/latex/references.bib`, ACL Anthology and Crossref records |

The available build uses pdfLaTeX with VnTeX T5 support and TeX Gyre Termes;
XeLaTeX was unavailable and LuaLaTeX lacked `luaotfload-main`. The final log has
three sub-4-point overfull boxes and a font-shape substitution warning; no table
extends past the page and no critical layout warning remains. The full Python
suite and Neo4j integration were not run because this task changed only focused
review rendering and report sources, not graph/query code.

## Decisions

Keep the report's primary evidence bound to graph `release-d3c788c3114a` and its
recorded artifacts. Preserve historical and current audit denominators
separately. Do not present AI judgments as human ground truth or verified course
accuracy. No graph, data, topic prediction, database, Explorer or deployment
changes were made.

## Open issues and limitations

Team member names and IDs, actual contribution summaries, faculty/course
identifier, instructor/advisor, actual submission date and course-required
AI-use wording remain editable placeholders. Human validation and verified
semantic accuracy remain unestablished. The exact model/effort of the delegated
report reviewer remains unavailable. Minor noncritical LaTeX warnings are
recorded above.

## Next step

Complete `report/latex/report-info.tex` and the contribution table from official
records, check course AI disclosure requirements, then have the team proofread
the PDF before submission. No external submission or publication was performed.

## Corrections

None.
