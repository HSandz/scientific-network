LATEXMK ?= latexmk
BUILD := build
SOURCES := $(wildcard *.tex en/*.tex vi/*.tex en/chapters/*.tex vi/chapters/*.tex tables/bilingual-*.tex figures/bilingual-*.tex data/*.tex) references.bib assets/uet.png
.PHONY: all en vi clean figures verify
all: en vi
en: $(BUILD)/report-en.pdf
vi: $(BUILD)/report-vi.pdf
$(BUILD)/report-en.pdf: $(SOURCES) $(wildcard figures/en/*.pdf)
	mkdir -p $(BUILD)
	$(LATEXMK) -pdf -bibtex -jobname=report-en -outdir=$(BUILD) -interaction=nonstopmode -halt-on-error -file-line-error main-en.tex
$(BUILD)/report-vi.pdf: $(SOURCES) $(wildcard figures/vi/*.pdf)
	mkdir -p $(BUILD)
	$(LATEXMK) -pdf -bibtex -jobname=report-vi -outdir=$(BUILD) -interaction=nonstopmode -halt-on-error -file-line-error main-vi.tex
figures:
	../../.venv/bin/python scripts/prepare-data.py
	../../.venv/bin/python scripts/generate-figures.py --language en
	../../.venv/bin/python scripts/generate-figures.py --language vi
verify:
	../../.venv/bin/python scripts/verify-report.py
clean:
	$(LATEXMK) -C -jobname=report-en -outdir=$(BUILD) main-en.tex
	$(LATEXMK) -C -jobname=report-vi -outdir=$(BUILD) main-vi.tex
