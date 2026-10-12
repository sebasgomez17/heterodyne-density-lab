# Portable C sources — author implementation pending

Write a public API header (suggested `hdl_core.h`) and C source files here.
Suggested kernel groups: Abel quadrature, detector-area quadrature, batched
complex phasors, Pretzler basis/forward-matrix integrals, and suitable Monte Carlo
array operations. Choose boundaries by profiling and numerical validation.

Use a plain C interface: `double` buffers, explicit sizes, documented units,
Python-owned memory where possible, and checked integer status returns. Pass
complex values as separate real/imaginary buffers for consistent MSVC support.
Avoid implicit ownership, Python callbacks inside loops, C99 VLAs, POSIX-only
functions, unchecked allocations, and mandatory OpenMP/CUDA dependencies.

The author writes root `build_ffi.py` and `setup.py`. The builder should export
`ffibuilder`, use out-of-line CFFI API mode, declare the header API, and compile
`heterodyne_density_lab._core`. Setuptools installs it into the project environment.
Use compiler-specific flags; link `m` only on platforms requiring it. Generated
`.so`/`.pyd` binaries are ignored and must be rebuilt per platform/interpreter.

This scaffold has no C source or builder. See the build guide's packaging bridge
and the installation guides before implementing the interface.
