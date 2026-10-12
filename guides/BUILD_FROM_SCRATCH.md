# Build the Python/C project from scratch

This guide describes the work for the author. The 0.1.0 archive already provides
the README files, version/license metadata, a locked Poetry environment, a
package namespace, and a compilable LaTeX outline. It deliberately contains no
scientific implementation. The target is complete feature coverage of the
supplied MATLAB snapshot, with native execution on the requested systems.

## 1. Adopt the repository identity and source layout

Recommended name: **Heterodyne Density Lab**. Repository/distribution:
`heterodyne-density-lab`; import name: `heterodyne_density_lab`. The name is a
suggestion, not a checked trademark or reserved PyPI name. Before publication,
check GitHub/PyPI availability and change the project URLs if choosing another
name. The author field/copyright currently use the supplied GitHub handle.

Start with this scaffold in an empty directory. Keep the original MATLAB
repository separate. Do not copy its Git metadata or machine-generated files.
The intended structure is:

| Location | Responsibility |
| --- | --- |
| `pyproject.toml` | Package metadata, dependency ranges, build requirements |
| `poetry.lock` | Resolved runtime/developer Python dependencies |
| `poetry.toml` | Place the project environment in `.venv` |
| `src/heterodyne_density_lab/` | Importable scientific Python modules |
| `csrc/` | Portable C headers and numerical kernels |
| `build_ffi.py` (to write) | CFFI declarations and compilation recipe |
| `setup.py` (to write) | Small setuptools/CFFI packaging bridge |
| `config/` | Author-written, user-editable Python configurations |
| `scripts/` | Five author-written run/study scripts |
| `tests/` | Numerical, interface, and reproducibility validation |
| `output/` | Local run artifacts, excluded from Git |
| `documentation/` | Original LaTeX outline and documentation builds |
| `guides/` | Installation and migration guidance |

The only supplied package Python file is the namespace `__init__.py` with a
docstring. It performs no computations. Add your modules in stages rather than
adding empty scientific files that appear to work.

## 2. Establish the environment and first checks

Follow the root README on the development machine, then install developer tools:

```text
poetry install --with dev
poetry check --lock
```

`pyproject.toml` declares NumPy, SciPy, Matplotlib, CFFI, setuptools, and wheel. Python's
standard library can handle paths, configuration snapshots, CSV, logging, and
metadata, so pandas or a configuration framework is not initially necessary.
Use SciPy/NumPy's established solvers rather than adding another mandatory BLAS
or LAPACK system installation for users. Their wheels supply optimized
numerics on the target systems. Runtime dependencies are not selected because
a particular MATLAB toolbox exists: choose an explicit open algorithm.

The `setuptools.build_meta` backend is intentional. Poetry remains the dependency
manager and environment runner. The backend implements CFFI's documented
`cffi_modules` integration. Build requirements include CFFI even though it is
also a runtime dependency: isolated builds need their own declared requirements.
The runtime setuptools/wheel dependencies also enable deliberate in-environment
extension builds/rebuilds. Do not change the backend to poetry-core and assume
the setuptools CFFI hook will still run.

The supplied lockfile was generated with Poetry 2.5.1. Re-resolve it when
changing dependencies, then validate the new resolution on every target.
Poetry's lock does not pin a global Python interpreter, OS packages, or C
compiler. Isolated build dependencies follow `[build-system].requires` rather
than the runtime lock; record tool versions for reproducible release builds.

## 3. Freeze the numerical specification before translating

Use [MIGRATION_CHECKLIST.md](MIGRATION_CHECKLIST.md) as the coverage checklist.
Its inventory comes from the attached source files, not just the old README.
The source's default power is **50 mW**; its README still mentions 1 mW. Its
study configuration has **nine selected-channel layouts** on the 16-element
model, while built-in detector support also includes 32- and 46-element models.
`main_density_design.m` applies explicit profile, channel, and Monte Carlo
overrides. Decide which are the new baseline versus an example configuration;
document each choice instead of copying stale text.

Record reference outputs from the original repository for noiseless calculations
and selected Monte Carlo cases. Store compact numeric fixtures, not the MATLAB
source, in the new tests if permitted. Capture units, detector tables, design
settings, noise assumptions, metric definitions, and rank behavior. The source
may reject a requested power due to linearity; record the exception or NaN
policy rather than treating that as a translation failure.

In particular, preserve all four noise modes (`detector_limited`,
`detector_weighted_noiseless`, `noiseless`, and legacy `relative`), both reference
beam modes, built-in and custom detector specifications, optional filters,
linearity enforcement, rank protection, diagnostics, and all plots/exports.

## 4. Write configuration files and Python orchestration

Write `config/default_design.py` and `config/study_config.py` first. Use a
configuration factory returning a fresh dataclass or dictionary; avoid mutable
shared defaults. Keep SI units and documented field names. A user edits these
files with a normal text editor; no notebook or GUI is required.

Separate baseline parameters from study candidates and sweep settings. Validate
inputs at entry: positive radius/wavelength, valid magnification, legal power
fractions, finite arrays, channel indices, sufficient quadrature, valid seeds,
and required custom detector fields. Preserve signed magnification and the
object/image-plane distinction. Use physical detector IDs 1..N in user-facing
configuration and tables, then convert once to zero-based internal array indices.
Specify and test that conversion.

Put shared code in the importable package, not in the run scripts. The scripts
should load a configuration, call the package, print summaries, and save plots
and tables. Avoid hidden overrides. Use main guards so importing a script does
not start a study.

To make `poetry run python scripts/NAME.py` reliable, do not assume the repository
root is on Python's import path. A recommended pattern is for each script to
find its repository root from `Path(__file__).resolve().parents[1]` and use a
shared loader in the installed package to load the editable configuration file
by its full path with `importlib.util`. Alternatively package the configuration
namespace explicitly. Do not add ad hoc `sys.path` edits in every script.
Resolve output paths against that root (or an explicit user-selected directory).

Choose a result container that separates geometry, measurement data, inversion,
spline outputs, noise summaries, and metrics. Retain units in table column names,
requested/used basis orders, uncertainty diagnostics, rank/conditioning, masks,
and exact-vs-linearized measurement differences. Make output creation automatic.

## 5. Reproduce the mathematical pipeline in small stages

Implement and validate in this order:

1. Density profile, bounded plasma support, Abel line integrals, and quadrature.
2. Detector coordinates, active-channel masks, signed imaging, beam/port
   clipping, and finite-area quadrature/normalization.
3. Separate probe/reference power distributions, complex phasors, vacuum
   calibration, phase, and the small-phase diagnostic.
4. Detector specifications, peak interference power, typical-linearity limits,
   shot/detector noise, ideal I/Q scaling, and carrier/bandwidth warnings.
5. Pretzler basis and forward matrix, rank limiting, stable weighted solve,
   sampled points, and reconstruction grids.
6. Symmetric smoothing spline, metrics, result tables, and figures.
7. Measurement reuse and one global `(Nupper, alpha)` selection per detector
   design, followed by the four physical/diagnostic studies.

The symmetric coordinate `u=(|x|/R)^2` is part of the model, not an incidental
MATLAB syntax choice. Preserve duplicate/opposite-side grouping and weights.
The supplied code has two spline algorithms: MATLAB's Curve Fitting Toolbox
smoothing spline and a penalized cubic B-spline fallback. Reproduce the fallback
as a transparent open reference. Provide an open smoothing-spline route if
reproducing both modes, but verify its objective, weights, boundary conditions,
and parameter mapping explicitly. SciPy's smoothing parameter is not assumed
to equal MATLAB's parameter. Any nonidentical parameter/automatic-selection
behavior needs a documented equivalence decision and numerical comparison.
Do not label a new solver as an exact toolbox reproduction without evidence.

## 6. Write the C kernels and a clear CFFI boundary

Use CFFI's **out-of-line API mode**: declarations describe a C API; a generated
Python extension is compiled and imported once. This avoids separately asking
users to find/load a platform DLL by path. Use normal C sources with include
paths and source lists in one builder; Python sees `ffi` and `lib` from the
compiled `heterodyne_density_lab._core` module.

Keep expensive quadrature, batched profile/phasor evaluation, and suitable
Monte Carlo array kernels in C. Python handles configuration, orchestration,
plots, diagnostics, and calls to optimized NumPy/SciPy linear algebra. Profile
first: a C loop is not automatically faster than a batched BLAS-backed solve.
Use large array calls rather than crossing CFFI for individual scalars.

Define a small header such as `csrc/hdl_core.h`. Prefer input/output buffers
owned by Python, explicit lengths, `double` values, and integer return codes.
Represent complex inputs/outputs with real/imaginary buffers for portable MSVC
C support. Declare shape, layout, ownership, units, and error semantics in the
header/API documentation. Keep data lifetime valid through `ffi.from_buffer`.
Validate dtype (`float64`), C-contiguity, size, and writability before passing
pointers. Do not return pointers to local/temporary C storage. Avoid callbacks
inside numerical loops. Check every return code.

Use double precision, check allocations if you allocate, reject invalid inputs,
protect against size overflow, and use portable math/constants. Link `libm` on
POSIX where needed; do not add `m` as an MSVC library. Select compiler flags
by platform: MSVC flags are not GCC flags. Avoid C99 variable-length arrays,
POSIX-only APIs, platform-specific intrinsics, and compiler-specific complex
features unless wrapped with an explicit supported alternative.

Start with one serial implementation. Do not require OpenMP, CUDA, or
`-march=native` for this portable first release. Avoid fast-math until you have
validated its effect on cancellation, phases, errors, and reproducibility.
A reproducible randomized implementation should accept noise arrays generated
with an explicit Python RNG, or define and test a portable C RNG/seed protocol.

## 7. Connect CFFI to installation (packaging guidance)

After your header/kernels and builder exist, add this packaging bridge as
`setup.py` at the repository root:

```python
from setuptools import setup

setup(cffi_modules=["build_ffi.py:ffibuilder"])
```

This snippet is packaging guidance, not a supplied scientific implementation.
Your `build_ffi.py` exports an `FFI` instance named `ffibuilder`. Call `cdef` with
preprocessor-free public declarations, then `set_source` with module name
`heterodyne_density_lab._core`, a C snippet including your header, the C source
list, include directories, and appropriate library/compiler flags. Do not pass
an arbitrary header containing `#include` directives directly to `cdef`.

Make paths robust for repository and source-distribution builds. The same build
must work when the source is extracted elsewhere. Do not import the package's
scientific Python modules at build time: build isolation may not contain
NumPy/SciPy. A plain buffer interface avoids requiring NumPy headers just to
compile your kernels. Configure CFFI through setuptools, not a manual `cc`
command that forgets Python's extension suffix/link options.

The current `MANIFEST.in` anticipates `build_ffi.py`, `setup.py`, and `csrc/*.c`
and `*.h`. Before these files exist, the setuptools source build may warn that
their patterns are empty; those warnings are expected for the scaffold. Once
implemented, inspect the source archive to ensure the builder/header/kernels
are really present. A developer who clones Git and a user who extracts a source
release should follow the same installation recipe.

Poetry installs dependencies and a root editable namespace, but that root
installation does not invoke setuptools' `cffi_modules` hook. The README therefore
always follows Poetry installation with this explicit backend command. With your
builder enabled, it performs both the initial native build and later rebuilds:

```text
poetry run python -m pip install --no-deps --force-reinstall --no-build-isolation -e .
poetry run python -c "from heterodyne_density_lab._core import ffi, lib; print('C extension import OK')"
```

Never silently fall back to slow Python if the C extension fails to import.
A clear import/build error with the compiler-guide link is more useful.

## 8. Validate equivalence and numerical robustness

Follow `tests/README.md`. Compare deterministic quantities first. Identical
MATLAB and Python integer seeds do not produce identical Gaussian arrays.
For exact algorithm comparisons, use the same stored noise/quadrature arrays;
for stochastic behavior, compare moments and metric distributions with stated
sample sizes and confidence/tolerance criteria.

Test physical invariants, coordinate/index conventions, zero-density and
small-phase limits, matched-beam calibration, quadrature convergence, detector
power splitting and peak-power rejection, weighted solves, spline parity and
central derivative, ill-conditioned geometry, and unsupported/invalid inputs.
Share one measurement ensemble across candidate hyperparameters exactly as the
original workflow does. Tune on a training ensemble and hold the estimator fixed
through sweeps; keep basis-order scans diagnostic rather than oracle tuning.

Confirm batch sizes bound memory. Benchmark representative whole studies and
peak memory, recording CPU, OS, Python/dependency/compiler versions, threads,
configuration, sample count, and seed. Report speed gains only after measuring
correct implementations with comparable accuracy.

## 9. Complete original documentation

Fill in `documentation/main.tex`: its headings cover the model, algorithms,
configuration/API, studies, performance, validation, and limitations. Each
figure slot compiles as a labeled placeholder until a real PDF is exported.
Write your own derivations and captions; do not copy manufacturer figure artwork
without the necessary permission. Cite original research and datasheets.

Explain known limitations, including cylindrical symmetry, no optical
propagation model, no absolute multi-fringe phase tracking, ideal vacuum/IQ
calibration, detector-equivalent noise assumptions, and typical-linearity data.
Document the chosen spline algorithm and any controlled differences from the
MATLAB implementation. Build with the supplied Makefile or direct commands.

## 10. Verify installation on every target before publishing a usable release

The environment validated while preparing this scaffold is Linux x86_64 with
Python 3.12. The installed namespace/dependencies and document build can be
checked; there is no implemented C extension to validate yet. For a completed
release, separately test clean macOS Intel and Apple Silicon, Windows x64 and
native ARM64, and Linux x86_64 and ARM64. Do not substitute x64 emulation for
an ARM64 result. Record each OS/Python/compiler combination and all five runs.

A useful future CI matrix covers Linux/macOS/Windows, Python 3.12/3.13, with
native architecture runners where available. Keep unavailable combinations
marked untested and add real hardware validation where CI lacks coverage.
Check source-distribution installation as well as a checkout; packaging failures
can appear only in the source release.

When tests exist:

```text
poetry run pytest
poetry check --lock
poetry run python -m build
```

`python -m build` uses the declared setuptools backend and produces an sdist
plus wheel. `poetry build` should not be assumed to invoke the alternate CFFI
backend in the same way. The wheel is platform-specific after CFFI integration;
do not distribute it as a universal Python-only wheel. Ordinary GitHub users
can keep compiling from source as requested.

## 11. Version and create the GitHub repository

`pyproject.toml` is the version source of truth. Query it through installed
metadata at runtime using `importlib.metadata.version('heterodyne-density-lab')`.
Do not add a second independent `__version__` literal. Update `version.txt` and
`CHANGELOG.md` in the same change. A `poetry version` operation updates metadata,
not those prose files automatically; run `poetry check --lock` afterward and
refresh the lockfile only if needed. Keep a clear migration/version policy while
0.x interfaces are evolving.

Create an empty **heterodyne-density-lab** repository under `sebasgomez17`.
Do not auto-generate another README/license if importing these files. Install
Git if necessary, then in this project's root:

```text
git init
git add .
git status
git commit -m "Add Python/C project scaffold and documentation"
git branch -M main
git remote add origin https://github.com/sebasgomez17/heterodyne-density-lab.git
git push -u origin main
```

Use GitHub's normal authentication when Git requests it. Review staged files
before committing, including generated outputs and credentials. This archive
includes no existing Git history; create the new repository yourself.
Tag 0.1.0 as a scaffold only if you want that public checkpoint. When the first
scientific release is validated, update its status/changelog/version and create
a corresponding Git tag and source release. Keep README claims consistent with
what actually works.

## Primary references

- [CFFI API-mode overview](https://cffi.readthedocs.io/en/stable/overview.html)
- [CFFI wrappers and setuptools integration](https://cffi.readthedocs.io/en/stable/cdef.html)
- [Setuptools pyproject configuration](https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html)
- [PyPA package build frontend](https://build.pypa.io/en/stable/)
- [Poetry environment commands](https://python-poetry.org/docs/managing-environments/)
