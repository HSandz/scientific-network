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
- `figures/`: local copies of v4 release charts, the v4 topic-coverage chart,
  and deterministic bounded v4 network maps. `figures/SOURCES.md` records each
  source artifact and the graph version used.
- `assets/uet.png`: original user-supplied UET logo, moved without alteration.
- `references.bib`: scholarly literature and authoritative software/data docs.

To update a figure, regenerate it from its pinned source/configuration in the
repository, inspect its caption and denominator, then replace the corresponding
local PNG in `figures/`. Keep a source path, graph version, projection, and
counting rule in `figures/SOURCES.md`. Do not use ignored runtime outputs as
report dependencies.

## Scientific scope and reproduction

The report references tracked release artifacts for counts and method versions.
The full graph, works cache, and database are intentionally not bundled. See
`../../docs/reproduce-remediation-v4.md` and Appendix B for the exact local
reproduction commands and required frozen input hashes. Re-acquiring current
provider responses is not byte-identical restoration.
