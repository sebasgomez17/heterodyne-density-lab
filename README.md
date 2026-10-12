# Heterodyne Density Lab

Python/C project for designing a one-dimensional heterodyne interferometer and
reconstructing the radial electron density of a cylindrically symmetric plasma.
The user edits Python configuration files and runs individual Python scripts
inside a Poetry-managed virtual environment. Computational kernels will be
written in C and called from Python through CFFI.

**Version 0.1.0 is a scaffold.** Installation and dependency checks can run now.
The scientific modules, configuration files, C kernels, CFFI builder, and five
run scripts are to be written by the author. The scientific run commands below
are the intended interface once those files exist; they cannot produce results
in this scaffold. See the [implementation guide](guides/BUILD_FROM_SCRATCH.md).

The original MATLAB implementation remains in
[heterodyne_density_reconstruction](https://github.com/sebasgomez17/heterodyne_density_reconstruction).
This repository starts a separate version series at 0.1.0. It includes no MATLAB
sources and its LaTeX document is an original outline for the author to fill in.
The proposed repository URL below becomes usable after its owner creates it.

## Requirements and installation choices

| Component | Requirement |
| --- | --- |
| Python | Standard 64-bit CPython 3.12 or 3.13; use 3.13 on macOS/Windows |
| Poetry | Poetry 2.2 or newer within the 2.x series |
| C compiler | Apple Clang on macOS; GCC on Linux; MSVC on Windows |
| Internet | Needed for initial downloads and dependency installation |
| Operating system | Target macOS 14+ Intel/Apple Silicon, Windows 11 x64/ARM64, Linux x86_64/ARM64 |
| LaTeX | Optional; needed only to build the documentation |
| Git | Optional for running; useful for cloning and contributing |

The target list is an implementation goal, not a completed validation claim.
Use a standard GIL-enabled Python build. Free-threaded Python, PyPy, 32-bit
Python, and mixed Python/compiler architectures are outside this initial scope.
Ubuntu 24.04 LTS has a complete Linux installation recipe below. Other modern
Linux systems need equivalent compiler, Python-header, and libffi packages.

Python 3.13 is a conservative default with native dependency wheels for the
selected architectures. Python 3.12 also allows Ubuntu 24.04's supplied Python
to work without building an interpreter. The dependency lower bounds include
Windows ARM64 wheels. The lockfile fixes the exact dependency versions; it does
not certify their numerical equivalence or every platform's installation.

A Poetry virtual environment isolates Python packages. It is not an operating
system VM. No VirtualBox, Windows guest, MATLAB, Anaconda, GPU toolkit, full
Visual Studio IDE, or Homebrew installation is needed for the primary recipes.
The implemented release will distribute C source with this project; install
the compiler once and use it to build the extension locally.

## 1. Install Python and a C compiler on a fresh system

Open the detailed guide matching your operating system and complete it first:

- [macOS: Intel and Apple Silicon](guides/INSTALL_MACOS.md)
- [Windows 11: x64 and ARM64](guides/INSTALL_WINDOWS.md)
- [Linux: x86_64 and ARM64](guides/INSTALL_LINUX.md)

These guides include the downloads, PATH setup, correct-interpreter checks,
compiler checks, and Poetry installation. In brief, macOS uses the python.org
installer plus `xcode-select --install`; Windows uses the python.org installer
plus Microsoft C++ Build Tools; Ubuntu uses `apt` for Python and GCC. `g++` is a
C++ compiler; this project uses `clang`, `gcc`, or MSVC `cl` for C.

After installation, `poetry --version` must show 2.x (at least 2.2).
Do not type commands into Python's `>>>` prompt. Use Terminal on macOS/Linux
and PowerShell on Windows; the Windows guide explains the compiler shell.

## 2. Download this repository

The simplest route avoids installing Git: open
[the repository](https://github.com/sebasgomez17/heterodyne-density-lab), select
**Code → Download ZIP**, and extract it. A ZIP of the main branch normally
extracts as `heterodyne-density-lab-main`. A release ZIP may have another folder
name. Open a terminal inside the extracted folder containing `pyproject.toml`.
For example, if extracted into Downloads:

macOS/Linux:

```bash
cd "$HOME/Downloads/heterodyne-density-lab-main"
```

Windows PowerShell (adjust if Downloads is elsewhere):

```powershell
Set-Location "$HOME\Downloads\heterodyne-density-lab-main"
```

Alternatively, if Git is already installed:

```text
git --version
git clone https://github.com/sebasgomez17/heterodyne-density-lab.git
cd heterodyne-density-lab
```

The URL is a proposed name; until the repository exists, extract the supplied
scaffold archive and work in its `heterodyne-density-lab` folder.

## 3. Select Python explicitly and install dependencies

Run all remaining commands from the repository root, not from `scripts/`.
Do not run project installation commands with `sudo` or an administrator shell.
Do not activate another project's virtual environment first.

macOS:

```bash
python3.13 --version
poetry env use python3.13
poetry install --only main
poetry run python -m pip install --no-deps --force-reinstall --no-build-isolation -e .
```

Ubuntu 24.04:

```bash
python3.12 --version
poetry env use python3.12
export CC=gcc
poetry install --only main
poetry run python -m pip install --no-deps --force-reinstall --no-build-isolation -e .
```

Windows PowerShell:

```powershell
py -3.13 --version
$ProjectPython = py -3.13 -c "import sys; print(sys.executable)"
poetry env use "$ProjectPython"
poetry install --only main
poetry run python -m pip install --no-deps --force-reinstall --no-build-isolation -e .
```

For another supported Python installation, pass its full executable path to
`poetry env use`. See the Linux guide if the OS's default Python is newer than
the supported range. `poetry.toml` puts this project's environment in `.venv`.
The lockfile is supplied: ordinary users do not need `poetry lock` or `poetry add`.
Poetry downloads the dependency files automatically; users do not download
NumPy, SciPy, Matplotlib, CFFI, setuptools, or wheel individually.

Use normal package mode: Poetry installs the local Python namespace too. Do not
copy the example project's `--no-root` option here. The second command installs
the local project through its declared setuptools backend inside the same Poetry
environment. This explicit backend step is required to compile the future CFFI
extension; Poetry's own root editable installation does not run setuptools'
`cffi_modules` hook. `--no-deps` keeps locked dependencies unchanged, and
`--no-build-isolation` uses the installed CFFI/setuptools/wheel build requirements.
The same command currently installs scaffold metadata without C computation.

## 4. Verify the actual project environment

These commands work in Terminal and PowerShell:

```text
poetry env info
poetry run python --version
poetry run python -c "import sys, platform; print(sys.executable); print(platform.machine()); print('64-bit:', sys.maxsize > 2**32); print('virtual environment:', sys.prefix != sys.base_prefix); assert (3,12) <= sys.version_info[:2] < (3,14); assert sys.maxsize > 2**32; assert sys.prefix != sys.base_prefix"
poetry run python -c "import numpy, scipy, matplotlib, cffi; print('numpy', numpy.__version__); print('scipy', scipy.__version__); print('matplotlib', matplotlib.__version__); print('cffi', cffi.__version__)"
poetry run python -c "import heterodyne_density_lab; from importlib.metadata import version; print(heterodyne_density_lab.__file__); print(version('heterodyne-density-lab'))"
```

Expect an executable under `.venv`, a matching 64-bit architecture, and package
version `0.1.0`. The import confirms the namespace/installation only; it does
not confirm numerical functions exist or the C extension was built.

After the author adds `build_ffi.py`, `setup.py`, and the C sources as described
in the implementation guide, the explicit backend installation command above
will compile the extension. Then also
run:

```text
poetry run python -c "from heterodyne_density_lab._core import ffi, lib; print('CFFI extension imported successfully')"
```

The `_core` check is intentionally unavailable in the present scaffold. It must
be required before declaring the implemented Python/C release usable.

## 5. Configure and run the scientific scripts (after implementation)

The planned editable files are `config/default_design.py` and
`config/study_config.py`. Start with the default design, then modify physical
parameters, selected detector elements, seed, numerical resolution, or plotting
controls. Study settings belong in the shared study configuration. They must
not be silently changed inside a run script.

| Planned script | Purpose |
| --- | --- |
| `scripts/main_density_design.py` | Single design, geometry, reconstruction, and noise summaries |
| `scripts/study_density_scale_length.py` | Primary spatial-resolution study |
| `scripts/study_detector_power_tradeoff.py` | Optical-power sweep with linearity checks |
| `scripts/study_detector_noise_contribution.py` | Fixed-estimator noise and weighting decomposition |
| `scripts/study_pretzler_basis_order.py` | Basis-order, rank, and conditioning diagnostic |

Once implemented, use the same commands on every OS:

```text
poetry run python scripts/main_density_design.py
poetry run python scripts/study_density_scale_length.py
poetry run python scripts/study_detector_power_tradeoff.py
poetry run python scripts/study_detector_noise_contribution.py
poetry run python scripts/study_pretzler_basis_order.py
```

No manual activation is needed: `poetry run` selects the environment. The planned
scripts load configuration relative to the repository using `pathlib`; the
implementation guide describes imports that work when running a script by path.
They should create their output directories automatically.

The intended output location is `output/`, with a separate folder per run/study.
Preserve configuration, random seed, package version, and numerical settings
beside the CSV tables and figures. Export publication figures deliberately into
`documentation/figures/`; ordinary runs should not overwrite document figures.
For a display-free Linux session, the author should support saving plots with
Matplotlib's `Agg` backend and no GUI requirement.

## Rebuilding, updates, and environment maintenance

After changing C code or CFFI declarations, rebuild from the repository root:

```text
poetry run python -m pip install --no-deps --force-reinstall --no-build-isolation -e .
```

This is the post-implementation rebuild path, not a command that adds C kernels
to the scaffold. Build requirements are already installed in the Poetry
environment. It preserves the locked Python dependencies and reinstalls the
local extension. Use a compiler-enabled shell on Windows.

After downloading an updated release, read `CHANGELOG.md`, run
`poetry install --only main`, then repeat the explicit backend installation
command from step 3. If installation finds the local project
already installed after C changes, use the rebuild command explicitly. Rebuild
when changing Python version or CPU architecture; compiled files cannot be
copied between operating systems or interpreters.

Inspect or remove the environment with:

```text
poetry env info
poetry env list
poetry env remove --all
```

Removal deletes the environment's packages; recreate it with the selection and
installation steps above. It does not remove source/configuration files. If
adding dependencies as a developer, use `poetry add PACKAGE`, then review and
commit both `pyproject.toml` and `poetry.lock`. Do not edit the lockfile manually.

## Documentation and developer guidance

- [Build from scratch and reproduce every feature](guides/BUILD_FROM_SCRATCH.md)
- [Complete MATLAB-to-Python/C mapping](guides/MIGRATION_CHECKLIST.md)
- [LaTeX structure, figures, and optional installation](documentation/README.md)
- [Python configuration contract](config/README.md)
- [Script contract](scripts/README.md)
- [C interface contract](csrc/README.md)
- [Validation plan](tests/README.md)
- [Scaffold checks actually performed](guides/SCAFFOLD_VALIDATION.md)

Runtime users do not need LaTeX. Developers can install optional Python tools
with `poetry install --with dev` once the main setup works.

## Troubleshooting

| Symptom | Next check |
| --- | --- |
| `poetry` not found | Complete the OS guide's PATH step and reopen the terminal |
| Python version rejected | Select 3.12/3.13 explicitly; the OS default may differ |
| Python opens the Microsoft Store | Use `py -3.13`; see Windows app-alias instructions |
| MSVC compiler not found | Use the configured developer shell and correct target architecture |
| Linux `Python.h` missing | Install headers for the selected Python, not another version |
| Extension import gives wrong architecture | Recreate `.venv` and rebuild with matching Python/compiler |
| Large SciPy/Matplotlib source build starts | Check the lockfile, Python/OS versions, architecture, and wheel availability |
| `scripts/...` missing or `_core` absent | Scientific implementation is pending in 0.1.0 |
| Power rejected by the scientific code | Check per-element peak power against the configured typical-linearity criterion |
| Too few independent measurements | Inspect selected channels, geometry masks, unique radii, and rank limits |

Source builds of scientific dependencies can require extra compilers/libraries;
GCC/MSVC alone is intended to build this project's C kernels. Use an OS and
Python combination with dependency wheels to keep installation small.
The compiler check is separate from the numerical validation of the model.

## License and official references

MIT; see [LICENSE](LICENSE). The copyright handle may be replaced by the
maintainer's preferred legal name before publishing. Third-party dependencies
retain their own licenses. Cite the original scientific sources and detector
datasheets in the new documentation; the MIT license does not grant rights to
redistribute manufacturer documents or figures.

- [Python downloads](https://www.python.org/downloads/)
- [Python 3.13 installer series](https://www.python.org/downloads/release/python-31316/)
- [Poetry installation](https://python-poetry.org/docs/#installation)
- [Poetry environments](https://python-poetry.org/docs/managing-environments/)
- [CFFI overview](https://cffi.readthedocs.io/en/stable/overview.html)
- [CFFI setuptools integration](https://cffi.readthedocs.io/en/stable/cdef.html)

Installation references checked on 2026-10-12. Package names and version bounds
are deliberate starting choices, not a promise of compatibility with future
major releases.
