# C numerical kernels

`hdl_core.c`/`hdl_core.h` implement four allocation-free double-precision routines:
trapezoidal Abel density integration, all-order Abel basis integration, weighted
complex phasors, and noisy I/Q demodulation. Python owns contiguous buffers and
validates finite values/shapes before CFFI calls. Complex values use real/imaginary
buffers for MSVC portability. The public header documents layouts and status codes.

`build_ffi.py` builds the out-of-line API extension `heterodyne_density_lab._core`
using setuptools. GCC/Clang builds use -O3 and libm; MSVC uses /O2 and no libm.
No mandatory OpenMP, CUDA, C++ runtime, native CPU flags, or fast-math is required.
Rebuild after modifying the header/source/builder using the root README command.
Compiled binaries are local build products and are excluded from source releases.
