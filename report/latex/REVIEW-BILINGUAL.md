# Bilingual course-report redesign and rendered review

Completed 12 November 2026 (Asia/Bangkok, +07:00). Baseline branch `main`,
HEAD `4b265c8`. Write scope: `report/latex/` only. The original
[REVIEW.md](REVIEW.md) remains a historical record.

## Delivered reports and content changes

| Edition | Pages including cover and references | Output |
| --- | ---: | --- |
| Original English baseline | 46 | `review/redesign/baseline/report-original-46-pages.pdf` |
| Redesigned English | **23** | `build/report-en.pdf` |
| Complete Vietnamese | **23** | `build/report-vi.pdf` |

Each edition is half the baseline length, using 12pt serif text, A4 portrait,
25mm margins and 1.14 line spacing. There are no landscape pages or forced
figure lists. The body allocates two pages to data, four to construction, two to
inventory/quality, ten to network analysis, and one to conclusion/limitations.
Cover, overview, compact TOC and references occupy four further pages.

- Replaced the abstract and keyword block with a short project overview and
  repository, Explorer and reproduction links.
- Removed separate background/related-work, architecture, experimental-design
  and discussion chapters. Removed the long appendices and historical
  version-comparison/audit-configuration narratives from the active document.
- Consolidated scope, source roles, matching, metadata and coverage in Chapter 1;
  construction, NLP, identities, schema and one real graph example in Chapter 2;
  inventory and concise evidence-quality context in Chapter 3.
- Rewrote analysis around questions: publication/topic change, researcher
  connectivity, organizational collaboration, communities/centrality and
  within-corpus citations. Ended with five quantified findings. Combined
  conclusion, material limitations, next steps and a short AI-use disclosure.
- Kept the seven unresolved historical DOI discrepancies and the later guard's
  prospective effect explicit. Kept denominators, withheld identities,
  affiliation gaps, inferred-topic uncertainty, source-reused AI assessments
  and the in-corpus citation boundary. Neither edition presents structural
  validation or automated judgments as independent human accuracy evidence.

The original chapters, tables and root figure assets remain unused but intact.
The exact original PDF and full source ZIP are saved under the ignored baseline
folder; the complete original source is also available at Git `4b265c8`.

## Figures and provenance

Ten figures per edition: eight measured plots and two TikZ diagrams.

| Action | Figures |
| --- | --- |
| Retained and localized | Topic trends; community topic profiles; sector matrix; top academia–industry pair ranking; Bo An neighborhood; citation ranking |
| Combined | Researcher degree CCDF and component sizes in one two-panel figure |
| Added | Official publication-by-year/venue chart; accepted-edge ECG ODE-GAN example |
| Retained and translated | Corrected parallel-branch data-to-graph pipeline |
| Removed from active document | Separate coverage plot (compact table instead); citation-neighborhood plot (ranking and Informer example suffice); system-architecture diagram |

All selections and numerical arrays remain frozen. Figure text is localized;
official names/titles/identifiers remain original. The example uses real v4
nodes, accepted edges and two paper-specific affiliation observations; no
invented entities or relationships. Long edge predicates in that diagram were
replaced with short codes and a full legend after high-resolution inspection
found an overlapping venue label.

[figures/SOURCES.md](figures/SOURCES.md) gives pins, source paths, denominators,
selection rules and English/Vietnamese receipts. The previous manifest is
preserved byte-for-byte as `figures/SOURCES-46-PAGE.md`. The UET bitmap is
byte-identical to the baseline and retains its aspect ratio.

## Build and automated checks

Executed from repository root unless indicated:

```sh
make -C report/latex clean
make -C report/latex all
.venv/bin/python report/latex/scripts/verify-report.py
.venv/bin/python report/latex/scripts/render-review.py \
  report/latex/build/report-en.pdf report/latex/review/redesign/en-final
.venv/bin/python report/latex/scripts/render-review.py \
  report/latex/build/report-vi.pdf report/latex/review/redesign/vi-final
git diff --check -- report/latex
```

All completed with exit 0. The `en` and `vi` targets are built separately by
`all`. Both PDFs have 23 portrait A4 pages, zero rotated pages, ten figure
references and the same nine bibliography keys. Final logs contain no LaTeX
warnings, overfull/underfull boxes, missing glyphs or unresolved references.
No extracted word lies outside the page or the expected text-width bounds.

The verifier checks corresponding narrative numerical literals, shared macros,
figure data/selection equality, accepted example edges/observations, exact
frozen input hashes, logo bytes, embedded fonts and bibliography references.
It passed for both final PDFs. This is report verification, not a new graph
quality experiment. Database integrity checks described in the manuscripts
remain historical release records; no database, classifier, collection or
repository-wide test suite was rerun.

Local check records: `review/redesign/final-clean.log`, `final-build.log`,
`final-verification.log`, `verification.json`, extracted text/bounding boxes,
font reports, and `scope-verification.json`. The outside-report tracked diff
matches `baseline/outside-diff.patch` exactly. All initial unrelated tracked
identity-quality edits and untracked files remain untouched. Nested bilingual
vector PDFs are explicitly unignored so a source checkout can build offline.

## Vietnamese typography and language review

XeLaTeX was absent. Installed LuaLaTeX failed due missing `luaotfload-main` and
font metrics. The working fallback is pdfLaTeX, VnTeX/T5 and TeX Gyre Termes,
with New TX Math; plots use DejaVu Sans. No font binaries are bundled.

The separate `scripts/vietnamese-proof.tex` tests ă, â, ê, ô, ơ, ư, đ, all
lowercase/uppercase tone combinations, regular/bold/italic/bold-italic, actual
report phrases, accented name samples clearly marked as glyph tests, and long
TikZ text. Its PDF and 1800px PNG were inspected. Real team names are still
placeholders and must be checked after entry.

Vietnamese cover, body, headings, captions, tables, diagram labels, plot labels,
TOC, running text and bibliography access notes were also inspected. Accents
and tone marks are intact; there are no missing-glyph boxes or unexpected font
substitutions. Bilingual numerical/semantic checks and the actual fresh
GPT-6-Luna High reviews, including resolved corrections, are recorded in
[BILINGUAL-CHECKS.md](BILINGUAL-CHECKS.md). The final small corrections were
verified by the primary agent; no later delegated signoff is implied.

## Full rendered-page inspection

Every page of each final PDF was rendered at 100 dpi: **46 page images total**.
All six numbered contact sheets were inspected. Important pages were also
inspected individually at 1800px height. Page numbers below are PDF positions,
including the unnumbered cover and roman-numbered front matter.

| PDF pages | Content checked in both editions | Result |
| --- | --- | --- |
| 1 | UET logo, title, course/team fields, accented cover text | Pass |
| 2–3 | Overview, links, compact TOC, navigation/page numbers | Pass |
| 4–5 | Source table, historical caveat, publication chart, coverage table | Pass |
| 6–9 | Pipeline, NLP/identity text, portrait schema, example edges/legend | Pass |
| 10–11 | Node/edge inventory and evidence-quality text | Pass |
| 12–14 | Topic panels, combined structure plot, annual counts, organization definitions | Pass |
| 15–16 | Sector matrix and organization-pair ranking | Pass |
| 17–19 | Community heatmap, centrality table, neighborhood labels and caption | Pass |
| 20–21 | Citation ranking, Informer example, five findings | Pass |
| 22–23 | One-page conclusion/limitations/disclosure, resolved references | Pass |

High-resolution details: English pages 6, 8, 9, 12, 13, 15, 16, 17, 19, 20;
Vietnamese pages 1, 6, 7, 8, 9, 11, 12, 13, 15, 16, 17, 18, 19, 20, 23.
Files: `review/redesign/{en,vi}-final/details/page-NN.png`.
Contact sheets: `review/redesign/{en,vi}-final/contact-{01,02,03}.jpg`.

No unexpected blank or landscape pages, cropped/overlapping labels, broken
math, detached captions, missing figures/citations or unreadable tables remain.
A few chapter endings have ordinary whitespace; none is a nearly empty spill
page. Plot labels and the longest Vietnamese headings fit at their intended
sizes. Diagram predicate overlap was fixed and the corrected page rechecked.

## Remaining editable details

`report-info.tex` contains explicit placeholders for two member names/IDs,
actual contributions, faculty, instructor, course code and actual submission
date. Do not infer them. The team should complete these, confirm the short
AI-use disclosure against course rules, arrange lecturer repository access,
and perform final human proofreading. Recheck covers after entering the names.
No source data, quality result, production graph, Explorer, database or external
deployment was modified. Nothing was pushed or published.

## Final PDF SHA-256

- `build/report-en.pdf`: `45129ca86a44417ffc519488e905930f5baeb01de04d7608f1d98f231a992a8c`
- `build/report-vi.pdf`: `568d7a9f3957d0ca0d96674befa95fea70639471d32be8ed1f958112014f29da`

## Submission-details addendum — 12 November 2026

The user-supplied team/course/faculty/instructor/date fields are now filled
in `report-info.tex`; only actual contributions remain placeholders. Both
editions rebuild to 23 pages and pass the report verifier. New cover renders
were inspected for names, diacritics and layout. All pages were rendered again;
pages 2–23 are pixel-identical to the previously inspected renders.

Current hashes supersede the preceding PDF hashes. Full checks and local
artifact paths: [submission update](WORK-2026-11-12-submission-details.md).

- `build/report-en.pdf`: `fd0f3321e769359edebdadd433d3ddb67ff2532b677ed144f4e4e8c842d3e6e1`
- `build/report-vi.pdf`: `5ccb464ed34f328971d1747de31a7e58572d917fabc201c5191313cf79ba1e6c`

## Equal-contribution page addendum — 12 November 2026

Contributions now occupy a separate front-matter page (PDF page 2), with a
translated table and TOC entry. Each member has **50%**, with the same shared
responsibilities as requested by the user. All supplied names, IDs and course
details remain filled; no contribution placeholders remain. Both editions now
have **24 portrait A4 pages**, compared with 23 immediately before this update
and 46 in the original English report.

Both builds and the report verifier pass. All 48 pages were rendered again and
all six contact sheets inspected. Both contribution tables were inspected at
1800px resolution, along with the Vietnamese cover, TOC and conclusion. The
Vietnamese names, headings and table text retain their diacritics; there are no
missing glyphs, overlapping columns, clipped text or unresolved citations.
The second member's name wraps naturally to two lines in both tables.

New PDF pages 5–22 and 24 are pixel-identical to the corresponding pages of the
preceding edition; scientific results and figures are unchanged. The conclusion
only drops the obsolete request to fill personal/course placeholders. Outside
the report, the tracked diff is identical to the preserved baseline.

Checks, minor verification/layout fixes and exact scope are recorded in
[the contribution update](WORK-2026-11-12-contributions.md). Local renders and
focused results: `review/contributions-2026-11-12/`; full automated receipt:
`review/redesign/verification.json`. This update remains **uncommitted** at the
user's request. The following hashes supersede previous PDF hashes:

- `build/report-en.pdf`: `dcfb3751cb4ec7cc8e35291583a272ceb4e614b0f444e599061f656d6b0228ff`
- `build/report-vi.pdf`: `98e11998adff056554280edc6890e6b0316915b2703635b34b203882e9dff817`

## Formal-cover addendum — 12 November 2026

Both covers now use a more formal institutional layout and include the
user-supplied **Group 9 / Topic 29**. The Vietnamese title is preserved exactly:
“Mạng lưới các tác giả và tổ chức nghiên cứu về Trí tuệ nhân tạo (AI) Quốc tế.”
The English title is “International Network of Authors and Research
Organizations in Artificial Intelligence (AI).” Group, topic and translated
title are editable in `report-info.tex`; the shared layout is in `cover.tex`.

The original UET logo, faculty, course/code, instructor, member names/IDs and
date remain correct. The separate equal-contribution page is preserved. Both
editions remain **24 portrait A4 pages** and pass the build and full report
verifier. All 48 pages were rendered again and all six contact sheets inspected;
both covers were also inspected at 1800px resolution. Long titles, bold accents
and member details fit cleanly. Every page after the cover is pixel-identical
to the preceding edition.

Full checks and scope: [formal-cover update](WORK-2026-11-12-formal-cover.md).
Local artifacts: `review/formal-cover-2026-11-12/`. All changes remain
**uncommitted**. Current hashes supersede the preceding hashes:

- `build/report-en.pdf`: `4dc2674f42ee32846dad4d95a574269373334b22947e20ee69b63b8977de4ddf`
- `build/report-vi.pdf`: `04a631c72c5ad1b0ee01c8c281c123c53e3208f3946943b25e2bffa34c3d5921`

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

## Formal-heading addendum — 2026-11-12T08:44:27+07:00

Replaced question-style and conversational section headings with formal
noun phrases in both editions (11 matching revisions per language). The
analysis headings now describe publication/topic trends, researcher and
organization collaboration, community structure/centrality, and within-corpus
citations. Both TOCs are updated. All chapter text other than the section
heading strings is byte-identical to the task-start sources.

Both PDFs remain 24 portrait A4 pages and pass compilation and the full report
verifier. All 48 pages were rendered and all six contact sheets inspected; both
TOCs and the longest Vietnamese heading were additionally inspected at 1800px.
No layout or Vietnamese accent problems were found. Build logs are clean.
Full checks: [formal-heading update](WORK-2026-11-12-formal-headings.md).
Local artifacts: `review/formal-headings-2026-11-12/`.
Changes remain **uncommitted**. Current hashes supersede previous hashes:

- `build/report-en.pdf`: `3ba6f490dd3aef2e6afed26a60ff908dbe9d2719588c27141e66625b9055bdf8`
- `build/report-vi.pdf`: `dc51fb55b3c212b03752eb1c6ebbaac00b0c391bb2c5880795bb9fb2fc15c552`


## Graph-version labels removed — 2026-11-12T08:59:47+07:00

Removed graph-version references from both rendered reports, including the
overview, chapters and diagram captions. Exact frozen source provenance remains
in internal manifests and verification inputs. Findings and material limitations
are unchanged, including the seven unresolved DOI discrepancies.

Both editions compile and pass the report verifier, remaining 24 portrait A4
pages each. All 48 final pages were rendered and all six contact sheets inspected;
high-resolution data pages in both languages and the Vietnamese pipeline also
passed visual inspection. No broken diacritics, clipping or layout defects remain.
An initial sparse-page spill from an expanded DOI caveat was corrected by concise
wording preserving its meaning; the final checks passed.

Full record: [graph-version label update](WORK-2026-11-12-graph-version-labels.md).
Artifacts: `review/graph-version-label-removal-2026-11-12/`.
Changes remain **uncommitted**. Current PDF hashes supersede earlier hashes:

- `build/report-en.pdf`: `e2f1e78d4e4189483e0b7d778add9ad0db9e621c26201012dc32241c8545f89f`
- `build/report-vi.pdf`: `4327c71155b2d93d11ecc5787cea2ca3105b6328e250019568ff200fb418e1b2`


## Consolidated LLM review wording — 12 November 2026

One neutral review passage per edition identifies GPT-6.1-Sol for report review.
Repeated evaluator-related caveats and the concluding AI-use disclosure removed.
Recorded numerical outcomes remain unchanged. Both builds and the full verifier
pass; each PDF remains 24 portrait A4 pages. Quality and conclusion pages in both
languages were rendered and visually checked, including Vietnamese diacritics.
See [work record](WORK-2026-11-12-llm-wording.md) and
`review/llm-wording-2026-11-12/`. Changes remain uncommitted.
Current hashes supersede previous hashes:

- `build/report-en.pdf`: `5419661c7a37c7bd361e90bbf7d01ed2d9de109e2db8b056771a63fb6ea53b5e`
- `build/report-vi.pdf`: `2a6bf4a48a024f59d03374d54094b30e8eed9c850e17f44643866941ef7e51e1`
