# Scientific Network — bilingual course reports

The English and Vietnamese editions use the same frozen production v4 graph,
`release-d3c788c3114a`. Each is **23 pages**, reduced from the previous 46-page
English report. The five chapters emphasize data, graph construction, inventory,
network insights, and conclusions. Ten figures appear in each edition.

## Build

```sh
cd report/latex
make en       # build/report-en.pdf
make vi       # build/report-vi.pdf
make all      # both editions
```

`latexmk` runs pdfLaTeX and BibTeX until cross-references settle. `make clean`
removes the two editions' generated build files. `main.tex` is a compatibility
entry point for the English edition; the supported output names are above.

Ordinary compilation uses only the report's local sources, tables, figures and
logo. The graph, API caches, models and database are not needed. Both languages'
vector figure PDFs are included as source assets; PNGs are inspection copies.
`build/` and `review/` are ignored local output directories.

Required: a TeX Live installation with `latexmk`, pdfLaTeX, BibTeX, VnTeX,
TeX Gyre Termes, New TX Math, and the packages in `preamble.tex` (including
TikZ, `natbib`, `booktabs`, `tabularx`, `siunitx`, `hyperref`, `xurl`,
`titlesec`, `tocloft`, `fancyhdr`, `placeins`, `needspace` and `microtype`).
No font files are distributed.

XeLaTeX is unavailable in this authoring environment. The installed LuaLaTeX
fails because `luaotfload-main` and associated font metrics are unavailable.
The tested fallback is **pdfLaTeX + UTF-8 VnTeX/T5 + TeX Gyre Termes**.
Vietnamese uses T5 throughout, including bold, italic, captions and TikZ;
English uses T1 with T5 available for names. Plot labels use DejaVu Sans.
The separate glyph proof and rendered reports were inspected visually; see
[REVIEW-BILINGUAL.md](REVIEW-BILINGUAL.md).

## Editing

| Path | Purpose |
| --- | --- |
| `main-en.tex`, `main-vi.tex` | Independently compilable language entry points |
| `document.tex`, `preamble.tex` | Shared cover, chapter order, typography and navigation |
| `report-info.tex` | Editable names, IDs, contributions, faculty, instructor, course code and date |
| `en/`, `vi/` | Separate overview and five chapter sources |
| `data/facts.tex`, `data/fact-manifest.json` | Generated shared counts and pinned sources |
| `data/construction-example.json` | Actual accepted v4 example nodes, edges and observations |
| `tables/bilingual-*.tex` | Shared tables with language-specific labels |
| `figures/bilingual-*.tex` | Shared pipeline and real-example TikZ diagrams |
| `figures/en/`, `figures/vi/` | Localized plots with identical data and selections |
| `assets/uet.png` | Original UET logo, unchanged |
| `references.bib` | Shared bibliography; localized access notes |

Names, IDs, faculty, instructor, course code and submission date are populated
from the user's supplied details. Only the actual-contribution fields remain
as placeholders; no contributions were inferred. `\VietnameseText{...}` supports
accented names in the English cover. Rebuild and inspect the covers after edits.

## Regenerating shared tables and figures

Optional regeneration requires the repository's existing `.venv` environment
(Matplotlib, NumPy and NetworkX) and the **exact frozen inputs**, including the
ignored v4 graph. It does not collect data, infer new topics or rerun network
analysis. From this directory:

```sh
make figures
```

This runs `scripts/prepare-data.py` and
`scripts/generate-figures.py --language en`, then `--language vi`. The scripts
check input SHA-256 pins and write only inside this report directory. Do not
edit generated numerical tables manually. See [figures/SOURCES.md](figures/SOURCES.md)
for denominators, selection rules, input paths and receipts. Reacquiring current
API responses cannot restore the original source bytes.

## Verification and rendered review

From the repository root, with Poppler (`pdftoppm`, `pdfinfo`, `pdftotext`,
`pdffonts`) and Pillow installed:

```sh
.venv/bin/python report/latex/scripts/verify-report.py
.venv/bin/python report/latex/scripts/render-review.py \
  report/latex/build/report-en.pdf report/latex/review/redesign/en-final
.venv/bin/python report/latex/scripts/render-review.py \
  report/latex/build/report-vi.pdf report/latex/review/redesign/vi-final
```

The verifier needs the pinned graph/analysis inputs. It checks counts, numerical
source parity, accepted example edges, figure selections, fonts, references,
page geometry, overflow and protected hashes. It writes
`review/redesign/verification.json`; it does **not** certify visual quality.
Inspect all page images/contact sheets and important pages at higher resolution.
The language checklist is [BILINGUAL-CHECKS.md](BILINGUAL-CHECKS.md); final build,
visual review and content changes are in [REVIEW-BILINGUAL.md](REVIEW-BILINGUAL.md).

The standalone typography proof can be rebuilt from this directory:

```sh
mkdir -p review/redesign
pdflatex -interaction=nonstopmode -halt-on-error \
  -output-directory=review/redesign scripts/vietnamese-proof.tex
pdftoppm -scale-to 1800 -singlefile -png \
  review/redesign/vietnamese-proof.pdf review/redesign/vietnamese-proof
```

## Preserved original and project resources

The complete original report source remains in Git at `4b265c8`; the previous
chapters, tables, root figure assets and [REVIEW.md](REVIEW.md) are retained as
historical material and are not included by the new entry points. The exact
46-page baseline PDF and a complete source ZIP are preserved locally under
`review/redesign/baseline/`. Original figure provenance is retained byte-for-byte
in [figures/SOURCES-46-PAGE.md](figures/SOURCES-46-PAGE.md).

- [Repository](https://github.com/HSandz/scientific-network)
- [Research Explorer](https://scientific-network-explorer.pages.dev/)
- [Frozen-v4 reproduction guide](../../docs/reproduce-remediation-v4.md)

Repository access for the lecturer still needs to be arranged according to the
latest recorded private-repository access check. No publication or deployment
is part of this report task.
