# Scientific LaTeX documentation

`main.tex` is the original scientific manual for the implemented Python/C
package. It contains the physical model, numerical equations, configuration/API,
study logic, reproducibility/performance records, validation, limitations, and
primary references. Real figures were generated from the new code using default
scientific configurations. `main.pdf` is the compiled manual.

## Runtime versus author requirements

Users running the Python package do not need LaTeX. Install it only if editing
and building this document. The provided source uses standard `article`,
`geometry`, `amsmath`, `amssymb`, `graphicx`, `booktabs`, and `hyperref` packages.
No shell escape, minted, bibliography processor, or Python plotting run is
required to build the manual.

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
there is no need to install GNU Make or Perl just to compile this manual.
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
in `documentation/build/`. The resulting PDF is `build/main.pdf`, also copied to `main.pdf`.

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

## Scientific figures and provenance

See [figures/README.md](figures/README.md). All document figures are provided
as vector PDFs, with real captions and references in the scientific source.
They were generated from the default baseline/full study results and analytic
or same-rule comparisons. The manual identifies panels that show selected
layouts or only one noise realization. Manufacturer artwork is not included.
`validation_data.json` retains numeric convergence and benchmark data.

The direct pdflatex commands generate `build/main.pdf`. After successful builds,
copy it to `main.pdf` if updating the distributed manual. On Windows PowerShell:

```powershell
Copy-Item build/main.pdf main.pdf
```

Normal scientific runs save figures to output/. Export publication figures into
figures/ deliberately, keeping configuration/seeds and captions consistent.
The manual uses a manual bibliography, so no BibTeX/Biber setup is required.
