# Fresh macOS setup — Intel and Apple Silicon

This recipe targets macOS 14 or newer. A newer supported macOS is preferable;
the scientific dependencies may require a newer OS than Python itself does.
Use the native architecture throughout: `arm64` on Apple Silicon and `x86_64`
on Intel. These are installation instructions for the 0.1.0 Python/C implementation, not a record of completed Mac validation.

## 1. Install Python

1. Open the [Python 3.13 release page](https://www.python.org/downloads/release/python-31316/)
   and download the **macOS installer**. Use a maintained 3.13 patch release.
2. Run the `.pkg` installer with the normal options. The universal installer
   supports Intel and Apple Silicon. Do not select a free-threaded interpreter.
3. Open `/Applications/Python 3.13/` and run **Install Certificates.command**
   if provided; this sets up certificates used for HTTPS downloads.
4. Close and reopen Terminal. Use a native Terminal on Apple Silicon: Finder
   → Applications → Utilities → Terminal → Get Info should have **Open using
   Rosetta** unchecked, if that option is present.

Verify explicitly:

```bash
sw_vers -productVersion
uname -m
command -v python3.13
python3.13 --version
python3.13 -c "import sys, platform; print(sys.executable); print(platform.machine()); print('64-bit:', sys.maxsize > 2**32); assert sys.version_info[:2] == (3,13); assert sys.maxsize > 2**32"
python3.13 -m pip --version
```

`platform.machine()` should match the native hardware. If `python3.13` cannot be
found, check `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13`.
Use that full path if needed. Do not replace Apple's system Python.

## 2. Install the C compiler

In Terminal:

```bash
xcode-select --install
```

Accept the Command Line Tools installer and wait for it to finish. The tools
include Clang, the system SDK, `make`, and Git; a full Xcode download is unnecessary.
If macOS reports that the tools already exist, continue with verification:

```bash
xcode-select -p
xcrun --find clang
clang --version
make --version
git --version
```

Compile and execute a tiny C program using a temporary directory:

```bash
CompilerCheckDir=$(mktemp -d)
printf 'int main(void) { return 0; }\n' > "$CompilerCheckDir/check.c"
clang "$CompilerCheckDir/check.c" -o "$CompilerCheckDir/check"
"$CompilerCheckDir/check"
printf 'Compiler program exit status: %s\n' "$?"
```

Expect exit status 0. The temporary files may be removed after this check.
Use `clang`, not `g++`, for C. No Homebrew package is needed for this recipe.

## 3. Install Poetry

Use the [official Poetry installer](https://python-poetry.org/docs/#installation)
with the selected Python:

```bash
curl -sSL https://install.python-poetry.org | python3.13 -
```

Add its executable directory to the current session and future zsh sessions:

```bash
export PATH="$HOME/.local/bin:$PATH"
printf '\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$HOME/.zprofile"
poetry --version
```

Run the append command once. The usual macOS login shell is zsh. If you use bash,
put the same PATH line in `~/.bash_profile` instead. Close and reopen Terminal,
then check `poetry --version` again. Use Poetry 2.x, at least 2.2.

If a future installer installs Poetry 3.x, use the installer's explicit version
option, for example `curl -sSL https://install.python-poetry.org | python3.13 - --version 2.5.1`.
The 0.1.0 lockfile was generated with Poetry 2.5.1.

## 4. Install this project

Download/extract the repository ZIP or clone it, then enter its root folder.
Continue with README steps 2–5. The key environment selection is:

```bash
poetry env use python3.13
poetry install --only main
poetry run python -m pip install --no-deps --force-reinstall --no-build-isolation -e .
poetry run python --version
poetry run python -c "import platform; print(platform.machine())"
```

The last line must still show the native architecture. Compile/import it through the README workflow. Do not copy an Intel `.so`
onto Apple Silicon or reuse an environment created through Rosetta.

If CFFI itself is forced to build from source, it may need libffi and pkg-config.
The normal wheel-based installation avoids that extra setup. See
[CFFI platform instructions](https://cffi.readthedocs.io/en/stable/installation.html)
for that exceptional case. Do not force source builds for ordinary installation.
