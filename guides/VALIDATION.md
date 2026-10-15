# Executed validation and remaining checks

Prepared 2026-10-12. The scientific implementation was executed on Linux
x86_64, CPython 3.12.14, GCC 13.3.0, Poetry 2.5.1, NumPy 2.5.4,
SciPy 1.18.1, Matplotlib 3.11.2, CFFI 2.1.1, and threadpoolctl 3.7.0.

## Numerical and distribution checks

- 31 tests passed: analytic/same-rule Abel quadrature, direct basis cosines,
  signed imaging/reference modes/full tensor phasors, weak/zero/wrapped phase,
  detector power/noise/linearity, source layouts, geometry invalidation,
  sample-wise spline/GCV reference, batch invariance, independent weighted solve,
  I/Q statistics, all noise modes, rank protection, bounded scale metrics,
  invalid inputs/SNR filtering, zero-overlap phase conventions, full 32/46/custom detector reconstruction, and global tuning/four-study workflows.
- All five scientific scripts completed using the source's full default grids
  and Monte Carlo counts, including all nine study detector layouts.
- Poetry metadata and lockfile consistency passed. Native editable installation,
  isolated setuptools source/wheel builds, required source-archive content, and
  installing from the source archive into a separate target all passed.
- The compiled extension imported from that separate installed target and ran
  a baseline reconstruction. This reused the validated interpreter/dependencies;
  it was not a fresh operating-system installation.
- Compatible locked dependency wheel tags were checked for CPython 3.12/3.13
  across Linux x86_64/ARM64, macOS Intel/Apple Silicon, Windows x64/ARM64.
  This confirms artifact availability, not native execution.
- The scientific manual compiled with its provided figure inputs and build files.
  Its pages were rendered and visually inspected; generated source figures and
  compiled PDF are included in the release.

## Full default execution record

Measured wall time includes scientific calculation and file/figure export.
Other processes and warm caches affect the timings.

| Script | Approximate wall time | Training cache |
| --- | ---: | --- |
| main_density_design | 1.6 s | Not used |
| study_density_scale_length | 8.9 s | Computed global tuning |
| study_detector_power_tradeoff | 3.7 s | Reused matching tuning |
| study_detector_noise_contribution | 2.8 s | Reused matching tuning |
| study_pretzler_basis_order | 0.6 s | Reused matching tuning |

The baseline single realization produced about 0.01998 full-radius spline RMS
and 0.2087 bounded local-scale-length RMS. These are seeded synthetic outputs,
not general accuracy promises. The centered baseline's configured maximum
combined detector-plane power was approximately 0.0516906 W.

## Kernel benchmark

160 unique impact parameters, 1000 quadrature nodes, double precision, median
of nine repetitions after warm-up, using the same mathematical trapezoidal rule.

| Kernel | C via CFFI | NumPy reference | Reference / C |
| --- | ---: | ---: | ---: |
| Density Abel | 1.15 ms | 2.00 ms | 1.73× |
| Order-0–8 Abel basis bank | 4.94 ms | 21.55 ms | 4.36× |

Relative maximum differences were about 3e-15. Run
`poetry run python scripts/benchmark_kernels.py` for measurements on your machine.
No actual MATLAB timing was available. This comparison does not establish a
MATLAB speedup or guarantee these ratios for whole studies or other hardware.
The manual also includes finite-radius Gaussian analytic convergence data.

## Native-platform and original-application limits

Native macOS Intel/Apple Silicon, Windows 11 x64/ARM64, Linux ARM64, and Python
3.13 execution were not available here. Fresh-system installation guides are
provided. The GitHub Actions workflow covers six runner architectures and
both Python versions after you push, but it has not been executed by this work.
Its Windows x64 runner uses Server 2025, while the ARM64 runner uses Windows 11.
Manual clean desktop installs remain valuable even after CI passes.

A running MATLAB installation was unavailable. Comparisons use independent
NumPy implementations of the provided mathematical rules and analytic identities,
not direct MATLAB-generated fixtures. The canonical open penalized spline is
the source's fallback method; the proprietary toolbox algorithm is intentionally
not reproduced. Noise uses PCG64, so equal cross-language seed integers are not
identical random samples. Use identical supplied normals for controlled future
comparisons, or evaluate stochastic distributions with sufficient sample sizes.
