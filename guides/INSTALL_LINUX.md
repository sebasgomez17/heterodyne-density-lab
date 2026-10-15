# Fresh Linux setup — x86_64 and ARM64

The primary recipe is Ubuntu 24.04 LTS on x86_64 or ARM64, using distribution
CPython 3.12 and GCC. It is a native setup; no OS virtual machine or Conda is
required. Other Linux distributions need equivalent system packages.

## 1. Install Python, headers, and compiler on Ubuntu 24.04

Open Terminal:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-dev python3-pip build-essential libffi-dev pkg-config curl ca-certificates
```

This installs Python, venv support, pip, Python headers, GCC, `make`, and headers
for building CFFI itself if a wheel is unavailable. `build-essential` includes
C++ tools too; compile the project's `.c` files with `gcc` rather than `g++`.
Git is optional: `sudo apt install git` if using the clone route.

Verify:

```bash
cat /etc/os-release
uname -m
command -v python3.12
python3.12 --version
python3.12 -c "import sys, platform; print(sys.executable); print(platform.machine()); print('64-bit:', sys.maxsize > 2**32); assert sys.version_info[:2] == (3,12); assert sys.maxsize > 2**32"
python3.12 -m pip --version
gcc --version
make --version
```

Expect `x86_64` or `aarch64` and Python 3.12.x. Distribution patch/backport
versions may differ from python.org's newest patch number.
Check that the development headers match:

```bash
python3.12 -c "import sysconfig; from pathlib import Path; p=Path(sysconfig.get_path('include'))/'Python.h'; print(p); assert p.exists()"
```

Compile and execute a tiny C program:

```bash
CompilerCheckDir=$(mktemp -d)
printf 'int main(void) { return 0; }\n' > "$CompilerCheckDir/check.c"
gcc "$CompilerCheckDir/check.c" -o "$CompilerCheckDir/check"
"$CompilerCheckDir/check"
printf 'Compiler program exit status: %s\n' "$?"
```

Expect exit status 0. The temporary files may be removed afterward.

## 2. Install Poetry

Use the [official installer](https://python-poetry.org/docs/#installation),
which isolates Poetry from the OS's managed Python packages:

```bash
curl -sSL https://install.python-poetry.org | python3.12 -
export PATH="$HOME/.local/bin:$PATH"
printf '\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$HOME/.bashrc"
poetry --version
```

Append the PATH line once. This is Ubuntu's usual interactive bash setup; if
you use zsh, place the line in `~/.zshrc` instead. Reopen Terminal and check
`poetry --version` again. Use Poetry 2.x, at least 2.2. To select the version
used to generate the lockfile, the installer accepts `--version 2.5.1` after `-`.

Do not use `sudo pip`, `pip --break-system-packages`, or install project
libraries into the OS interpreter. The Poetry installer and `.venv` avoid that.

## 3. Install the project

Extract the project ZIP or clone it and enter its root folder:

```bash
poetry env use python3.12
export CC=gcc
poetry install --only main
poetry run python -m pip install --no-deps --force-reinstall --no-build-isolation -e .
poetry run python --version
poetry run python -c "import platform; print(platform.machine())"
```

Continue with README steps 4–5. The explicit backend installation will compile this project's
C extension from the supplied builder and kernels.

## Other Linux releases or distributions

The package accepts standard CPython 3.12 and 3.13. Check the distribution's
Python version before choosing it. A default Python 3.14/3.15 or 3.11 does not
meet this initial package's supported range.

On distributions whose default Python is supported, install Python, venv,
matching development headers, GCC, libffi development headers, pkg-config,
curl, and trusted CA certificates through the distribution's package manager.
For example, Fedora's package names commonly include `python3`, `python3-devel`,
`python3-pip`, `gcc`, `make`, `libffi-devel`, `pkgconf-pkg-config`, `curl`, and
`ca-certificates`. Confirm the Python version; package names alone do not
select a supported version. Do not overwrite the distribution's system Python.

If the OS default is outside the range, install Poetry with that OS Python
(Poetry 2.x requires Python 3.10+) and let Poetry install a separate interpreter.
For Ubuntu releases with a newer default, install the same apt packages from
step 1, then use `python3` to run the Poetry installer instead of `python3.12`.
After setting PATH and entering the repository root:

```bash
poetry python install 3.13
poetry python list
```

Poetry downloads a managed standalone CPython, distinct from python.org's
installer. Copy the exact executable path from the displayed list and pass it
to `poetry env use /absolute/path/to/python3.13`, then run
`poetry install --only main` followed by the root README's explicit backend
installation command. For a GCC build, run `export CC=gcc` in the same terminal before the backend
installation. Some standalone interpreters were built using Clang and would
otherwise select `clang`, which may not be installed. Check the selected
interpreter's `Python.h` path
using the header-check command above with `poetry run python`; standalone
builds normally include it. Run every environment check in the root README.
This is the alternative route; it requires internet and a supported standalone
build for that architecture. It is documented by
[Poetry's Python commands](https://python-poetry.org/docs/commands/#python-install).

The initial Linux target is modern glibc-based x86_64/ARM64. Alpine/musl and
other CPU architectures need separate dependency/build validation and are not
covered by the fresh-system recipe. On a server without a desktop, save figures
using Matplotlib's `Agg` backend; do not install a desktop only to generate plots.
