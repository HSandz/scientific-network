# Separate contribution page

Status: completed. Recorded: 2026-11-12T08:29:52+07:00 (Asia/Bangkok).
Baseline: `34e43de`. Scope: `report/latex/` only. The user explicitly requested
that this change remain uncommitted. Preserve existing unrelated changes.

Move contributions from the covers to a dedicated bilingual front-matter page,
with member, student ID, percentage and description columns. The user requested
equal contributions: record 50% each and shared project responsibilities rather
than inventing different leadership roles. Verify both editions and page layout.

## Changes

- Added `contributions.tex` as a dedicated page immediately after the cover,
  with a table of names, student IDs, percentages and descriptions, plus a TOC
  entry in each language. Removed contribution rows from the covers.
- Filled both percentages as **50%** and used the same shared responsibilities:
  data collection/preprocessing, graph construction/NLP topics, network
  analysis/visualization, and report writing/review. Shared values remain
  editable in `report-info.tex`; all supplied submission facts are preserved.
- Removed the obsolete instruction to complete personal/course placeholders
  from both conclusions and updated the compilation README.
- Excluded the cover from the verifier's text-density heuristic: moving the
  contributions reduced the English cover to exactly 65 words. The original
  threshold still applies to every subsequent text page. Visual inspection
  confirms the cover is intentional and complete.

## Checks and artifacts

| Check | Outcome |
| --- | --- |
| `make -C report/latex all` | Exit 0; English and Vietnamese each have **24 portrait A4 pages** (previously 23; original report 46). |
| `.venv/bin/python report/latex/scripts/verify-report.py` | Exit 0; frozen inputs, example edges, bilingual values, figure selections, logo, embedded fonts, references and geometry pass. |
| Full render with `scripts/render-review.py`, both PDFs | Exit 0; 48 page images and six contact sheets, all inspected. |
| High-resolution inspection | Both contribution tables, Vietnamese cover, TOC and conclusion pass; accents and tone marks are intact. Covers and all contact sheets checked in both languages. |
| Focused extracted-text/config checks | Both names/IDs, supplied cover fields, two 50% values summing to 100, separate page and translated TOC entries pass; no submission placeholders. |
| Pixel comparison against preceding edition | New pages 5–22 and 24 are identical to old pages 4–21 and 23, respectively, in both languages. |
| `git diff --check -- report/latex` | Exit 0. |
| Outside-report tracked diff vs original baseline | Byte-identical; unrelated identity-quality edits remain untouched. |

Local records and renders: `review/contributions-2026-11-12/`, including
`build.log`, `verification.log`, `focused-checks.json`, language page/contact
images and high-resolution details. The verifier's complete current receipt is
`review/redesign/verification.json`.

An initial table underfull-box warning was resolved by terminating the table
paragraph; final logs have no warnings, overfull/underfull boxes, missing glyphs
or unresolved references. The first focused name check used layout extraction,
which interleaves columns when the second name wraps; raw reading-order
extraction confirms the complete name. No PDF content correction was needed.

## Outcome and next step

Both updated PDFs are ready for human proofreading. No new graph analysis,
database operation or repository-wide test suite was run for this report-only
change. No external action, staging or commit was performed: **this change
remains uncommitted as explicitly requested**. Next: team review of the shared
contribution statement and final submission.

## Contribution introduction removed — 2026-11-12T08:37:20+07:00

Removed the exact bilingual introductory paragraph at the user's request.
The dedicated page, table and 50% shares remain. Both PDFs rebuilt successfully
and remain 24 pages. Both changed pages were rendered and inspected: the table
follows the heading cleanly and Vietnamese accents remain intact. Build logs
are clean and the report verifier passes. Its text-density heuristic now treats
the dedicated contribution table separately from body pages. Checks/renders:
`build/contribution-paragraph-removal*.log` and
`build/contributions-{en,vi}-updated.png`. No commit was made.

Current PDF hashes supersede previous hashes:

- `build/report-en.pdf`: `15e9d367b0519dd48e6b1e16133fdfaab28b492cf195bfc419e40e5b10e91d6f`
- `build/report-vi.pdf`: `0c28d9a441155ae3b67a3bf0cf5d3bb060b81cddbd500f23aa9b0b22f6fbe2ed`

## Complementary contribution descriptions — 2026-11-12T08:39:13+07:00

At the user's request, replaced the identical descriptions with complementary
responsibilities in both languages, retaining 50% each. San's entry covers data
collection/preprocessing, paper matching, entity resolution, graph construction
and researcher/organization collaboration analysis. Minh's entry covers NLP
topics, graph validation, topic/citation analysis and visualization. Both entries
include shared report writing and review. These editable descriptions supersede
the earlier shared-description wording.

`make -C report/latex all` and the report verifier passed (exit 0). Both PDFs
remain 24 pages with clean build logs. Both changed contribution pages were
rendered at 1400px and inspected: no clipping, overlap or broken Vietnamese
accents. Checks/renders: `build/contribution-roles*.log` and
`build/contributions-{en,vi}-updated.png`. README editing guidance updated.
No commit was made. Current hashes supersede earlier hashes:

- `build/report-en.pdf`: `7fd283002ba1aeaa7d2c57251b4d7a471391e1c2024995395ceff8d249018e80`
- `build/report-vi.pdf`: `27f8ceb107c4453d6a6a9f4f2aeed4ae3fa5ac2ef2ca1f268f089c7625890c5e`
