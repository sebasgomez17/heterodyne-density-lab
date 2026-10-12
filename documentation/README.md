# LaTeX documentation scaffold

`main.tex` is an original document outline for Heterodyne Density Lab. It contains
structure, headings, author prompts, a configuration table outline, API groupings,
and labeled figure slots. Scientific prose, equations, references, and results
are intentionally left for the author. It does not copy the old LaTeX document.

## Runtime versus author requirements

Users running the Python package do not need LaTeX. Install it only if editing
and building this document. The provided source uses standard `article`,
`geometry`, `amsmath`, `amssymb`, `graphicx`, `booktabs`, and `hyperref` packages.
No shell escape, minted, bibliography processor, or Python plotting run is
required to build the outline.

## Optional fresh-system LaTeX setup

**macOS:** install [BasicTeX](https://www.tug.org/mactex/morepackages.html) for a
smaller TeX distribution, or MacTeX for the complete collection. Add
`/Library/TeX/texbin` to PATH if it is not present. With BasicTeX, install any
missing packages with `tlmgr`; `latexmk` is optional. For example, in Terminal:

```bash
export PATH="/Library/TeX/texbin:$PATH"
sudo tlmgr update --self
sudo tlmgr install latexmk geometry amsmath booktabs hyperref
pdflatex --version
```

**Windows:** install [Basic MiKTeX](https://miktex.org/howto/install-miktex) for the
current user and allow its missing-package installation as appropriate. Reopen
PowerShell and run `pdflatex --version`. Use the direct PowerShell recipe below;
there is no need to install GNU Make or Perl just to compile this outline.
For Windows ARM64, check TeX distribution availability; an x64 TeX process under
Windows emulation can build a PDF independently of the native Python/C target.

**Ubuntu:** in Terminal:

```bash
sudo apt update
sudo apt install texlive-latex-base texlive-latex-recommended latexmk make
pdflatex --version
latexmk --version
```

Equivalent packages work on other distributions. These downloads are optional
and separate from the Poetry environment.

## Build with Make on macOS/Linux

From the repository root:

```bash
cd documentation
make
```

The Makefile calls `latexmk` with the supplied `latexmkrc`, which places outputs
in `documentation/build/`. The resulting PDF is `build/main.pdf`.

```bash
make clean
make distclean
```

`clean` removes auxiliary files while keeping the PDF. `distclean` asks latexmk
to remove generated files including the PDF. Source and figure inputs remain.

## Build directly without Make or latexmk

macOS/Linux, from `documentation/`:

```bash
mkdir -p build
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
```

Windows PowerShell, from the repository root:

```powershell
Set-Location documentation
New-Item -ItemType Directory -Force -Path build | Out-Null
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
if ($LASTEXITCODE -ne 0) { throw 'LaTeX build failed' }
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
if ($LASTEXITCODE -ne 0) { throw 'LaTeX build failed' }
```

A second run resolves the contents and figure references. Rerun if LaTeX requests
another pass. `latexmk -pdf main.tex` is an alternative if latexmk is installed;
Perl may be needed for latexmk on Windows. The direct pdflatex recipe avoids that.

## Figure slots

See [figures/README.md](figures/README.md). Each slot expects a PDF filename and
has a stable label. If that file is absent, a framed filename placeholder is
shown, so the outline compiles immediately. Replace each placeholder with your
own exported figure and write a real caption/interpretation before publication.
Do not publish the placeholder captions as validated scientific findings.

The source uses manual bibliography placeholders to avoid another build tool.
Replace them with real citations, or deliberately adopt BibTeX/Biber and update
the build instructions. Keep its displayed document/package version consistent
with `pyproject.toml`; the outline currently says 0.1.0.
