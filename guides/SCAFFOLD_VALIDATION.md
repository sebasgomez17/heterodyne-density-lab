# Scaffold validation record — 2026-10-12

The following checks were performed while preparing version 0.1.0. They validate
infrastructure and instructions, not a translated scientific model.

| Check | Result |
| --- | --- |
| Poetry metadata and lock consistency (`poetry check --lock`) | Passed |
| Locked runtime dependencies and optional developer tools | Installed on Linux x86_64 |
| Root editable namespace through Poetry | Passed |
| Explicit setuptools editable installation inside the Poetry environment | Passed |
| README interpreter, 64-bit, virtual-environment, dependency, namespace, and version checks | Passed |
| Setuptools source distribution and scaffold wheel build | Passed; empty future-source patterns warn as expected |
| CFFI out-of-line API packaging/compiler probe in a separate temporary copy | Built with GCC and called successfully |
| Locked wheel tags for all six target OS/architecture combinations and Python 3.12/3.13 | Compatible wheel entries found for locked dependencies |
| All local Markdown document links | Resolved |
| Original MATLAB function inventory | All 33 `.m` files mapped |
| LaTeX build through `make`/latexmk | Passed with 13 figure placeholders; final log has no layout/reference warnings |

Environment: Linux x86_64; CPython 3.12.14; Poetry 2.5.1; GCC 13.3.0;
NumPy 2.5.4; SciPy 1.18.1; Matplotlib 3.11.2; CFFI 2.1.1;
setuptools 82.0.1; wheel 0.48.0.

The compiler probe contained only a tiny arithmetic function, solely to validate
the future packaging contract. It is not included in the deliverable. No
scientific algorithm, C kernel, configuration implementation, run script, or
scientific numerical test is supplied or claimed to pass.

Wheel-tag availability is not native platform execution, and does not validate
OS installation steps on real macOS/Windows machines. The developer must still
validate clean native installs and all scientific runs on every target. The
compiled LaTeX preview is a temporary verification output; the archive supplies
its source, build files, and figure slots rather than a completed scientific PDF.
