"""Build portable CFFI API extension, without importing scientific dependencies."""
import sys
from cffi import FFI

ffibuilder = FFI()
ffibuilder.cdef("""
int hdl_abel_density(size_t, const double *, double, double, double, double, double, int, double *);
int hdl_abel_basis(size_t, const double *, double, int, int, double *);
int hdl_phasor(size_t, size_t, const double *, const double *, double, double *, double *, double *);
int hdl_iq_samples(size_t, size_t, const double *, const double *, const double *, const double *, double,
                   double *, double *, double *, double *);
""")
ffibuilder.set_source(
    "heterodyne_density_lab._core", '#include "hdl_core.h"',
    sources=["csrc/hdl_core.c"], include_dirs=["csrc"],
    libraries=[] if sys.platform == "win32" else ["m"],
    extra_compile_args=["/O2"] if sys.platform == "win32" else ["-O3"],
)
