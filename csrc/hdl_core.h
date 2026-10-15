#ifndef HDL_CORE_H
#define HDL_CORE_H
#include <stddef.h>
/* All arrays are contiguous float64 buffers owned by Python. No allocation.
   Return 0 on success, 1 for invalid dimensions/parameters.
   Abel outputs: nx densities or nx*(max_order+1) row-major basis integrals. */
int hdl_abel_density(size_t nx, const double *x, double R, double n0,
                     double nbase, double ln, double na, int nq, double *out);
int hdl_abel_basis(size_t nx, const double *x, double R, int max_order,
                   int nq, double *out);
int hdl_phasor(size_t ne, size_t q, const double *h, const double *weights,
               double phase_factor, double *re, double *im, double *linear);
/* normals layout: (nmc,2,ne); output arrays: (nmc,ne). */
int hdl_iq_samples(size_t ne, size_t nmc, const double *carrier_re,
                   const double *carrier_im, const double *sigma,
                   const double *normals, double phase_factor,
                   double *I, double *Q, double *phase, double *density);
#endif
