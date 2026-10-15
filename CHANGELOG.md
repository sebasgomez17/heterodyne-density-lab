# Change history

## 0.1.0 — 2026-10-12

### Scientific implementation

- Portable CFFI API kernels for trapezoidal Abel profile/basis integrals,
  finite-area phasors, and batched I/Q phase recovery.
- Signed imaging, detector/port/beam geometry, both reference modes, built-in
  16/32/46-element and custom sensor/detector support.
- Explicit optical-power accounting, typical-linearity enforcement on all
  physical elements, detector/shot noise, IF/IQ scaling, and analytic diagnostics.
- All four noise modes, optional SNR exclusion, rank-protected Pretzler
  inversion, tempered weighting, and a symmetric penalized cubic B-spline.
- Five individual scripts with shared editable Python configuration, all nine
  detector layouts, global joint tuning, and fixed-estimator study sweeps.
- Measurement reuse, transverse weight reduction, global impact deduplication,
  batched solves/GCV, bounded memory caches, and content-keyed tuning reuse.
- CSV/JSON/NPZ outputs, headless-safe plots, reproducibility records, explicit
  quick presets, numerical tests, and a kernel benchmark script.

### Documentation and distribution

- Fresh macOS/Windows/Linux installation recipes, Poetry metadata/lockfile,
  MIT license, original scientific LaTeX source, compiled manual, and real figures.
- Scientific computation plan, module/API descriptions, migration map, and
  measured validation/performance record.

### Deliberate differences from the original MATLAB package

- One canonical open spline algorithm replaces proprietary-toolbox auto selection.
- NumPy PCG64 generates random variates; MATLAB and Python seed integers are not
  expected to produce identical stochastic samples.
- Realizations are the first array axis. Public configuration uses descriptive
  SI-unit names, and the physical detector-ID convention remains 1-based.
- Plotting is headless and saves outputs by default; interactive display is opt-in.
- Rank-reduction reporting includes measurement-count truncation.

Linux x86_64 execution is validated. Native macOS/Windows/ARM64 execution and
bitwise comparisons with a running MATLAB installation remain outstanding.
