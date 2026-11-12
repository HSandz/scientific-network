# Bilingual course-report redesign

Status: complete. Session: 2026-11-12, Asia/Bangkok (+07:00).
Final checkpoint: 2026-11-12T08:13:44+07:00.
Baseline: `main` at `4b265c8`; unrelated identity-quality edits preserved.
Write scope: `report/latex/` only, per explicit user instruction; repository-wide
journal/status writes were superseded for this task.

## Objective and changes

Replaced the 46-page research-paper narrative with five-chapter English and
Vietnamese course reports, **23 pages each**. Shared source infrastructure,
editable submission details, verified facts/tables, localized figures, real
accepted-edge example, and independent language entry points are implemented.
Ten figures per edition; ten pages of actual network analysis. Background,
architecture, historical experiment/audit narratives and long appendices were
removed from the active report. Necessary source/coverage/uncertainty facts and
brief AI-use disclosure remain. No graph, analysis or quality data were changed.

Production version: `release-d3c788c3114a`. Full original source/PDF, Git state
and protected hashes are preserved under ignored `review/redesign/baseline/`;
original source also remains at `4b265c8`. Legacy chapters/tables/figures and
`REVIEW.md` remain intact. Original figure manifest is retained byte-for-byte
as `figures/SOURCES-46-PAGE.md`.

## Checks and outcomes

- Full original report and relevant source/provenance/code artifacts were read.
  Frozen v4 graph/summary/analysis and accepted example edges were checked;
  experimental identity candidates were excluded from active manuscripts.
- Fresh `gpt-6-luna`, reasoning `high`, bounded read-only factual and bilingual
  reviews completed. Corrections and exact review scope are recorded in
  `BILINGUAL-CHECKS.md`; final integration belongs to the primary agent.
- `make -C report/latex clean` then `make -C report/latex all`: exit 0; 23/23 pages.
  Explicit `make ... en` and `make ... vi` also exit 0, up to date afterward.
- `.venv/bin/python report/latex/scripts/verify-report.py`: exit 0; matching
  numerical literals, shared figures/selections, accepted example objects,
  protected input/logo hashes, citations, fonts and A4 geometry. No out-of-page
  or text-width outliers. Final LaTeX logs have no warnings or over/underfull boxes.
- `scripts/render-review.py` on each final PDF: exit 0, all 46 pages rendered,
  six contact sheets visually inspected; listed high-resolution pages and
  separate Vietnamese typography proof inspected. Diacritics, labels, math,
  tables, figures and navigation render correctly. No broken or blank pages.
- `git diff --check -- report/latex`: exit 0. Outside-report tracked diff equals
  saved baseline patch; protected graph, source cache, analysis, summary and UET
  logo hashes unchanged. Unrelated initial untracked files were not edited.

## Failures resolved and interpretation boundaries

XeLaTeX is absent; LuaLaTeX fails due missing local luaotfload/font resources.
Used tested pdfLaTeX + VnTeX/T5 + TeX Gyre Termes fallback. An early verifier
pattern falsely matched a prohibited standalone percentage inside `12.90%`;
its numeric boundary was corrected. High-resolution review found overlapping
long predicate labels in the new example; short codes plus a legend fixed them.
The final language review clarified a Vietnamese AI judgment and two metric
labels. None of these repairs changed measured data.

No new source collection, classifier/analysis run, graph-quality experiment,
Neo4j integration check or repository-wide tests were performed. Recorded
release checks are labeled historical in the report. No push/deployment occurred.
Local source checkpoint uses subject `Redesign course report in English and Vietnamese`.

## Artifacts and next step

`build/report-en.pdf`, `build/report-vi.pdf`, `README.md`, `REVIEW-BILINGUAL.md`,
`BILINGUAL-CHECKS.md`, `figures/SOURCES.md`. Exact PDF hashes, commands, source
pins, visual-review details and selection rules are in those records. Raw logs,
page images, contact sheets, verification JSON and baseline backup stay ignored
under `review/redesign/`.

Next: team completes names, IDs, contributions, faculty, instructor, course code
and actual submission date in `report-info.tex`, confirms disclosure wording,
arranges lecturer access and performs final human proofreading. Rebuild/recheck
the covers after entering real names. No personal details were invented.
