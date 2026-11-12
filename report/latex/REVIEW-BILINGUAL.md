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
