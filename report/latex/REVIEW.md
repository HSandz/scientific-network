# Report visual and scientific review — 12 November 2026

Status: complete. Scope: `report/latex/` only.
Final verification: 2026-11-12, 02:48 +07:00 (Asia/Bangkok).

Baseline HEAD: `d19fef9`. Existing unrelated stabilization edits are preserved.
The user's strict report-only boundary supersedes repository-wide journal/status
updates for this session; all review records and temporary renders stay here.

Primary integration/layout editor: GPT-6.1 Sol. Bounded read-only factual review:
GPT-6-Luna, high reasoning effort, explicitly selected in a fresh context.

Baseline: clean `make clean && make`, 50 pages; compiled copy retained in
`review/before/main.pdf`. All 50 pages were rendered and inspected through six
numbered contact sheets and detailed problem-page views before editing.
Confirmed defects included overlapping workflow nodes, landscape schema,
cramped architecture, verbose navigation lists, misplaced floats, weak network
maps, sparse continuation pages and an unnecessary appendix spill.

Final artifact: [`build/main.pdf`](build/main.pdf), **46 portrait A4 pages**,
678,295 bytes. SHA-256:
`db64a4135ac9460302e2bf9bc0136a1f0398fcec037427cd41afaed1eb880c19`.

## Visual changes and final inspection

- Rebuilt Figures 3.1 and 4.1 with clear branches, aligned boxes and unobstructed
  arrows. Identity/affiliation and topic processing are independent; graph JSON
  supplies SQLite, independently of analysis. Detailed final PDF pages 17–18
  show readable labels and no overlaps or hyphenated node text.
- Table 3.1 covers all ten predicates in portrait with four concise columns
  (PDF page 16). Acceptance/weight details remain in Section 3.7 and Appendix A.
- Shortened chapter headings, prevented chapter-title hyphenation, and added
  selective float barriers/space reservations. Evaluation tables follow complete
  introductory paragraphs. Collaboration/citation figures stay in their sections.
  The former orphan ending is integrated; Appendix A fits one page (42).
- Re-rendered all ten measured plots as vector PDFs with matching PNG copies.
  Topic trends use small multiples, community profiles use wrapped topic labels,
  and sector/citation charts have readable axes and labels. Captions carry
  provenance and counting definitions instead of embedded tiny footnotes.
- Replaced weak maps with twelve organization pairs, a 13-node/24-edge induced
  researcher neighborhood, and a directed 13-paper/12-edge citation subset.
  Exact IDs, selection rules and accepted edges are in `figures/SOURCES.md`,
  `render-receipt.json`, and three edge CSVs. No new measurements were invented.
- Short captions reduce navigation to two contents pages plus one page each of
  figures and tables. Including the abstract, front matter after the cover is
  five pages. Bibliography fits one readable page. Team fields are shared between
  cover and Appendix C through `report-info.tex`; the original logo is unchanged.

After the final clean build, **all 46 pages** were rendered again at 100 dpi and
visually inspected in `review/final/contact-01.jpg` through `contact-06.jpg`.
This includes cover, abstract, contents/lists, eight chapters, every figure/table,
three appendices and bibliography. Twenty detailed page images (1900 px high)
were inspected for dense content, including pages 1, 16–18, 21, 23–24, 28–37,
42, 45 and 46. Updated diagrams, coverage and bibliography were re-inspected
after the last edits. No significant overlap, clipping, unexpected blank page,
float-induced orphan paragraph, distorted logo or unreadable chart remains.
Intermediate builds exposed additional spacing/label defects; these were fixed
and superseded by this final inspection.

## Scientific corrections

- Historical v4 acquisition lacked DOI equality in a singleton fallback. Seven
  unresolved discrepancies affect 21 byline positions. The later guard does not
  repair the frozen graph. Work/source equivalence remains unverified; the
  13,606 matched-work count is preserved. Sources: `reports/quality-v5/baseline-audit.json`
  and `reports/quality-v5/task2b-v1/doi-reconciliation.md`.
- Distinguished 48,259 accepted authorship positions with institution support
  from 74,485 source author–institution observations across matched bylines,
  including withheld positions. Coverage remains 48,259/65,469 = 73.71%.
- Corrected the sector prose to 10,956, matching the frozen matrix. Clarified
  SQLite construction from evidence/affiliation records and removed the service
  identifier from main prose. Preserved v4/v5, AI/human, structural/semantic,
  coverage/accuracy and centrality/influence distinctions.
- Protected bibliography proper nouns/acronyms. Eight scholarly DOIs were checked
  against Crossref; Sentence-BERT pages were checked against official ACL BibTeX.
  An initial concurrent Crossref attempt received rate limits; sequential retries
  succeeded. All eight documentation/source URLs returned HTTP 200 after redirects.
  No references were added. Evidence is under ignored `review/bibliography-*.json`.

## Checks performed

All commands below exited 0, from the repository root unless noted:

```sh
.venv/bin/python report/latex/scripts/generate-figures.py
(cd report/latex && make clean && make)
.venv/bin/python report/latex/scripts/render-review.py report/latex/build/main.pdf report/latex/review/final
.venv/bin/python report/latex/scripts/verify-report.py
sha256sum -c report/latex/review/protected-inputs.sha256
git diff --check -- report/latex
```

The final build uses latexmk, pdfLaTeX and BibTeX; logs are
`review/final-clean.log`, `review/final-build.log`, and `build/main.log`.
`review/final/verification.json` records 46 A4 pages, zero rotations, zero
overfull boxes, no undefined references/citations or missing characters, and no
words outside either page or text-width bounds. It also verifies pinned input
hashes, the unchanged logo, accepted selected edges/endpoints, induced researcher
edges and citation direction. All embedded fonts are included in the PDF.
A separate Vietnamese alphabet/text PDF was rendered and visually inspected;
no missing glyphs were found. The build retains the baseline's noncritical
generic font-shape substitution warning; it is not a warning-free build.

Frozen graph and analysis hashes match the initial protected-input receipt.
All task writes stayed under `report/latex/`; outside-scope status still lists
only the initial unrelated stabilization files. No repository-wide tests, graph
rebuild, model run, database mutation, push, deployment or external submission
was performed.

## Remaining limitations and next step

Names, student IDs, actual contributions, faculty, course code, instructor and
submission date remain editable placeholders in `report-info.tex`. Complete them
from official records and rebuild before submission. Seven DOI cases, incomplete
affiliation coverage and unestablished independent human validation remain
scientific limitations, not issues this presentation-only pass can resolve.
Fresh-context Luna review was bounded factual proofreading, not a new graph audit.
