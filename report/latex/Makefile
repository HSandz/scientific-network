LATEXMK ?= latexmk
BUILD := build
MAIN := main.tex

.PHONY: all clean
all: $(BUILD)/main.pdf

$(BUILD)/main.pdf: $(MAIN) preamble.tex report-info.tex references.bib $(wildcard chapters/*.tex) $(wildcard tables/*.tex) $(wildcard figures/*.tex) $(wildcard figures/*.png) assets/uet.png
	mkdir -p $(BUILD)
	$(LATEXMK) -pdf -bibtex -outdir=$(BUILD) -interaction=nonstopmode -halt-on-error -file-line-error $(MAIN)

clean:
	$(LATEXMK) -C -outdir=$(BUILD) $(MAIN)
	rm -f $(BUILD)/main.pdf
