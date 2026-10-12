# Fresh Windows 11 setup — x64 and ARM64

Use standard 64-bit CPython and a matching C compiler target. ARM64 support is a
project target; it must be validated on Windows ARM64 before being advertised
as tested. Scientific dependencies have ARM64 wheels, but that alone does not
validate this project's future extension.

## 1. Check architecture and install Python

Open Settings → System → About → **System type**. Choose x64 for an Intel/AMD
x64 processor or ARM64 for an ARM-based processor.

1. Open the [Python 3.13 release page](https://www.python.org/downloads/release/python-31316/).
2. In the file list, download **Windows installer (64-bit)** for x64 or
   **Windows installer (ARM64)** for native ARM64. The 3.13 ARM64 installer is
   labeled experimental by Python; validate native operation. Choose the normal
   installer, not an embeddable ZIP or a 32-bit/free-threaded installation.
3. Run the installer. Enable **Add python.exe to PATH**, pip, and the Python
   launcher where those options are offered. The normal installation includes
   headers needed to compile extensions. Accept the path-length option if offered.
4. Close and reopen PowerShell.

Check:

```powershell
py -3.13 --version
py -3.13 -c "import sys, platform; print(sys.executable); print(platform.machine()); print('64-bit:', sys.maxsize > 2**32); assert sys.version_info[:2] == (3,13); assert sys.maxsize > 2**32"
py -3.13 -m pip --version
```

Expect `AMD64` for x64 or `ARM64` for native ARM. If the launcher is unavailable,
use the full installed `python.exe` path instead of `py -3.13` in these commands.
An x64 interpreter running in emulation requires an x64 extension; it does not
establish native ARM64 support.

If `python` opens the Microsoft Store, use the explicit launcher above. If
needed, turn off conflicting Python app execution aliases in Settings → Apps
→ Advanced app settings → App execution aliases. Do not change PATH to a
random Python installation to hide a version/architecture mismatch.

## 2. Install the C compiler

Download the standalone **Build Tools for Visual Studio** through Microsoft's
[C++ Build Tools page](https://visualstudio.microsoft.com/visual-cpp-build-tools/).
In the Visual Studio Installer:

- Select the **Desktop development with C++** workload.
- Include a current MSVC x64/x86 toolset and Windows SDK for x64.
- For ARM64, also select the MSVC **ARM64/ARM64EC build tools** component for
  the installed toolset; build this extension for **ARM64**, not ARM64EC.
- Keep the Windows SDK. The full Visual Studio IDE is not necessary.

Installer labels vary between toolset releases; use Microsoft's
[installation guide](https://learn.microsoft.com/en-us/cpp/overview/acquire-msvc)
and [command-line guide](https://learn.microsoft.com/en-us/cpp/build/building-on-the-command-line).
The workload's name mentions C++, but its `cl` compiler also compiles C files.

For x64, open **x64 Native Tools Command Prompt for VS** from Start. For ARM64,
use an ARM64-target developer prompt if provided. Otherwise open the developer
command prompt and initialize the ARM64 cross-tool environment by running the
installed `VC\Auxiliary\Build\vcvarsall.bat` with `amd64_arm64` (also named
`x64_arm64` in current documentation). For example, for VS 2022 Build Tools:

```bat
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" amd64_arm64
```

Use the actual installation path shown by the installer; newer versions may
have a different directory. This selects an x64-host compiler producing ARM64
code, which can run under x64 emulation on Windows ARM. Do not use its default
x86 target. In the configured command prompt check `cl` and the target:

```bat
cl
echo %VSCMD_ARG_TGT_ARCH%
```

`cl` with no source prints its banner and may return a nonzero status; that is
normal. The target should be `x64` or `arm64` as intended.

For the remaining commands use PowerShell inheriting this compiler environment:

```bat
powershell -NoExit
```

Now inside that PowerShell:

```powershell
Get-Command cl
$env:VSCMD_ARG_TGT_ARCH
py -3.13 -c "import platform; print(platform.machine())"
$CompilerCheckDir = Join-Path $env:TEMP ([guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $CompilerCheckDir | Out-Null
Set-Content -Path "$CompilerCheckDir\check.c" -Value 'int main(void) { return 0; }' -Encoding ascii
Push-Location $CompilerCheckDir
cl /nologo check.c /Fe:check.exe
if ($LASTEXITCODE -ne 0) { throw 'C compilation failed' }
.\check.exe
if ($LASTEXITCODE -ne 0) { throw 'C executable failed' }
Pop-Location
```

Expect no exception. Use this configured PowerShell for initial installation
and rebuilds. Regular PowerShell is sufficient for running already-built scripts.
Do not use WSL as a substitute for validating native Windows installation.

## 3. Install Poetry and make it discoverable

In PowerShell:

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -3.13 -
$PoetryBin = Join-Path $env:APPDATA 'Python\Scripts'
$env:Path = "$PoetryBin;$env:Path"
poetry --version
```

For future terminal sessions, open **Edit environment variables for your
account**, edit the **user** Path, and add `%APPDATA%\Python\Scripts` as a new
entry. Preserve existing entries. Reopen the compiler-enabled PowerShell and
verify `poetry --version` again. If installation reports another executable
location, use the path it reports. No execution-policy change or environment
activation script is needed for `poetry run`.

Use Poetry 2.x, at least 2.2. To select the lockfile's installer version explicitly:

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -3.13 - --version 2.5.1
```

## 4. Select Python and install the project

Extract the project ZIP and enter its root in this PowerShell. Then:

```powershell
$ProjectPython = py -3.13 -c "import sys; print(sys.executable)"
poetry env use "$ProjectPython"
poetry install --only main
poetry run python -m pip install --no-deps --force-reinstall --no-build-isolation -e .
poetry run python --version
poetry run python -c "import platform; print(platform.machine())"
```

Continue with the root README's full environment checks and, after
implementation, its script commands. On ARM64, both the project Python and
compiled extension must be ARM64. If a dependency starts a lengthy source build,
check interpreter architecture and wheel availability first; ordinary users
should not need Fortran, BLAS, or a Matplotlib source-build toolchain.

Compiler updates may need a new developer shell. After editing C code or
switching architectures, use the README rebuild steps. Native target support
must be tested separately from x64 emulation on ARM hardware.
