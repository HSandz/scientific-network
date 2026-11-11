# LaTeX research report

This directory contains the independently buildable academic report source for
the AAAI/IJCAI 2021--2025 scientific knowledge graph. The manuscript uses the
frozen production v4 graph and release-v4 analysis. Its AI assessment, historical
results, coverage gaps, and human-review status are kept distinct in the text.

## Build requirements

- TeX Live or an equivalent TeX distribution with pdfLaTeX, `latexmk`, BibTeX,
  `natbib`, `booktabs`, `tabularx`, `longtable`, `tikz`, `hyperref`,
  `cleveref`, and the other packages loaded by `preamble.tex`.
- The TeX Gyre Termes, New TX Math, and VnTeX packages (distributed as open TeX
  font/package resources).

XeLaTeX was not available in the authoring environment, and its installed
LuaLaTeX binary failed because the local `luaotfload` module was missing. The
project therefore uses pdfLaTeX with UTF-8 input, VnTeX's T5 encoding for
Vietnamese names, and TeX Gyre Termes text with New TX mathematics. The
`\VietnameseText{...}` macro in `preamble.tex` can wrap editable Vietnamese
names. No font files are bundled.

## Build

From this directory, run:

```sh
make
```

The compiler and bibliography passes are handled by `latexmk`. The output is
`build/main.pdf`; all auxiliary files remain under `build/`. Use `make clean` to
remove generated files.

## Structure and editing

- `main.tex`: cover, front matter, chapter order, appendices, and bibliography.
- `preamble.tex`: typography, page layout, headings, links, tables, and figures.
- `report-info.tex`: editable title, university/course, team, contribution,
  instructor, and submission-date fields. Replace bracketed values only from
  official records; do not infer student details.
- `chapters/`: eight report chapters and three appendices.
- `tables/`: reusable manuscript tables.
- `figures/`: report-specific renderings of frozen v4 measurements and
  deterministic bounded v4 network views. `figures/SOURCES.md` records each
  source artifact and the graph version used.
- `assets/uet.png`: original user-supplied UET logo, moved without alteration.
- `references.bib`: scholarly literature and authoritative software/data docs.

To update a figure, run `scripts/generate-figures.py` from the repository root
using the existing analysis environment and required pinned inputs. Inspect the
resulting PDF and PNG, caption, denominator and selection ledger. Keep source
paths, graph version, projection, and counting rules in `figures/SOURCES.md`.
Compilation depends only on the local figure files, not ignored source artifacts.

## Scientific scope and reproduction

The report references tracked release artifacts for counts and method versions.
The full graph, works cache, and database are intentionally not bundled. See
`../../docs/reproduce-remediation-v4.md` and Appendix B for the exact local
reproduction commands and required frozen input hashes. Re-acquiring current
provider responses is not byte-identical restoration.

## Report quality review (12 November 2026)

The visual/scientific pass is recorded in [REVIEW.md](REVIEW.md). Its write scope
is this directory only. The full baseline and final page renders/contact sheets
are local under ignored `review/`; the delivered manuscript is `build/main.pdf`.
Team/course placeholders remain editable solely in `report-info.tex`, reused by
the cover and contribution appendix.

The report now uses local vector PDF plots, with PNG inspection copies. Both
are reproducible from pinned v4 artifacts using `scripts/generate-figures.py`;
see [figures/SOURCES.md](figures/SOURCES.md) for selection definitions and input
requirements. Generation changes presentation only, and is unnecessary for
ordinary compilation. `Makefile` tracks PDF figure dependencies.

Render every page and produce contact sheets with:

```sh
# Run from repository root using the existing analysis environment.
.venv/bin/python report/latex/scripts/render-review.py \
  report/latex/build/main.pdf report/latex/review/final
.venv/bin/python report/latex/scripts/verify-report.py
```

Poppler's `pdftoppm`, `pdfinfo` and `pdftotext`, plus Pillow, support the review
scripts. Compilation continues to use pdfLaTeX and BibTeX. The report additionally
uses `placeins`, `needspace`, `etoolbox` and `tocloft` for layout/navigation.
Repository-wide tests and graph rebuilds are not part of this report-only pass.
