LATEXMK ?= latexmk

.PHONY: all pdf clean distclean
all: pdf

pdf:
	$(LATEXMK) -pdf main.tex

clean:
	$(LATEXMK) -c main.tex

distclean:
	$(LATEXMK) -C main.tex
