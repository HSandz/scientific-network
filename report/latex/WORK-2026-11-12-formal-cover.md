# Formal bilingual cover update

Status: completed. Recorded: 2026-11-12T08:33:36+07:00 (Asia/Bangkok).
Baseline HEAD: `34e43de`; the separate 50%–50% contribution-page update is
already present and uncommitted. All changes must remain uncommitted.
Write scope: `report/latex/` only.

The user requested a more formal cover and supplied Group 9, Topic 29 and the
official Vietnamese topic title. Add these to shared configuration, translate
the topic accurately for English, and revise the cover hierarchy while
preserving the original UET logo, supplied submission facts and separate
contribution page. Rebuild and inspect both covers; verify that later pages and
scientific content remain unchanged.

## Changes

- Added shared `ReportGroupNumber`, `ReportTopicNumber` and `ReportTopicTitle`
  fields in `report-info.tex`: Group 9, Topic 29, and the user's exact Vietnamese
  topic wording. English: “International Network of Authors and Research
  Organizations in Artificial Intelligence (AI).” The international scope,
  authors, organizations and AI subject are preserved in both languages.
- Moved the shared cover to `cover.tex`, with a formal hierarchy: university
  and faculty, original UET logo, report type and course/code, group/topic,
  full topic title and corpus subtitle, instructor, aligned member/ID rows,
  then place and date. Used restrained blue rules and readable serif text.
- Preserved both supplied names/IDs, instructor, date and all other course
  details. The separate 50%–50% contribution table is unchanged.
- Updated README editing guidance. All scientific prose, figures and tables
  remain unchanged.

## Verification

| Check | Outcome |
| --- | --- |
| `make -C report/latex all` | Exit 0; both editions remain **24 pages**. |
| `.venv/bin/python report/latex/scripts/verify-report.py` | Exit 0; portrait A4, fonts, glyph/reference logs, numerical parity, frozen inputs, example edges, figures and original logo pass. |
| `scripts/render-review.py`, both PDFs | Exit 0; all 48 page images and six contact sheets generated and inspected. |
| Covers at 1800px resolution | Pass in both languages; full title fits, names/diacritics are intact, logo proportions preserved, no clipping or overlap. |
| Extracted cover fields | Group/topic/title, both names/IDs, instructor, course code and date match supplied details. |
| Pixel comparison with preceding PDFs | Every page 2–24 is identical in both languages. |
| Final build logs | No warnings, overfull/underfull boxes, missing characters or unresolved references. |
| `git diff --check -- report/latex` | Exit 0. |
| Outside-report tracked diff vs task start | Byte-identical; unrelated edits preserved. |

Local build/verification logs, saved preceding PDFs, cover PNGs, full page
renders/contact sheets and `focused-checks.json` are under
`review/formal-cover-2026-11-12/`. Complete current verifier receipt:
`review/redesign/verification.json`.

## Outcome and next step

Both formal covers are complete and ready for human review. No graph,
production code, quality result, database or external application was changed.
No staging, commit, push or deployment was performed. All report changes,
including the preceding contribution-page update, remain **uncommitted** as
requested. Next: final human proofreading and separately authorized submission.
