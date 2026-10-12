# Complete migration checklist

This inventory is grounded in the supplied ZIP's current `.m` sources. All
Python/C paths below are proposed files to be authored, not existing scientific
implementations. The archive contains 33 MATLAB files. The original MATLAB
repository remains separate; no MATLAB sources are included here.

## Source snapshot details that need deliberate treatment

| Item | Supplied source value/behavior |
| --- | --- |
| Nominal version label | 5.0; version history dated 2026-08-20 |
| Default density profile | R=0.10 m, n0=1e19 m^-3, nbase=0, ln=0.025 m, na=2 |
| Default wavelength / beam radius | 1.55 µm / w0=37 mm (field 1/e, intensity 1/e²) |
| Default port / magnification | Circular 139.7 mm diameter / signed M=0.057 |
| Default total detector-plane power | 50 mW in source; old README says 1 mW |
| Default heterodyne settings | Equal probe/reference split, 10 MHz IF, 1 MHz ENBW |
| Default detector / noise | G12430-016D, all elements, detector_limited, 1 realization, seed 1 |
| Default reconstruction | Nlower=1, Nupper=3, constant basis included, alpha=1 |
| Default linearity | Enforced, typical 99% sensitivity, 1 V bias, safety factor 1 |
| Main-script explicit overrides | ln=0.02 m; channels 5–12; center [0,0]; 1000 realizations; 50 mW |
| Study tuning | Nupper=2..4; alpha=0..1 by 0.1; training ln/R=[0.10,0.15,0.20,0.25,0.30]; 100 realizations; seed 1201 |
| Scale-length sweep | ln/R=0.10..0.30 at 9 points, 1000 realizations |
| Power study | ln/R=[0.10,0.20,0.30], log10 P=-3..-1, 8 points/decade, 1 realization |
| Noise-contribution sweep | Same scale-length grid, 1 realization, fixed tuned estimator |
| Basis diagnostic | First study design, ln/R=0.15, Nupper=2..max(8, available), 1 realization |

These values describe the attached snapshot, not a validated universal design.
Do not adopt physical values simply because an old README mentions them.

## Required scientific behavior

- [ ] Generalized-exponential density with finite support and SI units.
- [ ] Abel integration using converged quadrature and bounded batching.
- [ ] Signed imaging, beam centers, circular port, finite detector-element areas,
  illumination/transmission masks, physical IDs, and object/image coordinates.
- [ ] Matched-probe and unclipped-Gaussian reference beam modes.
- [ ] Exact complex finite-area phasor, vacuum calibration, ideal atan2 phase,
  phase-derived line density, and small-phase diagnostic.
- [ ] G12430-016D, -032D, -046D and custom sensors/specifications.
- [ ] Typical/conservative responsivity/noise specifications, custom fields,
  detector-equivalent/shot noise, IF bandwidth and low-SNR warnings.
- [ ] Peak-cycle interference power, bias-dependent typical linearity curves,
  sensitivity criterion, safety factor, hard rejection, and sweep NaNs.
- [ ] Noisy I/Q generation with original ideal demodulator conversion factors;
  analytic high-SNR uncertainty used for weighting/diagnostics, not to replace I/Q.
- [ ] All four noise modes including legacy relative line-density noise.
- [ ] Pretzler constant/cosine basis, finite-area matrix, optional rank limiting,
  requested/used order, rank/condition warnings, and stable solve.
- [ ] OLS, tempered inverse-variance weighting, full WLS, optional SNR exclusions.
- [ ] Symmetric smoothing, both open equivalents of source spline routes,
  duplicate grouping/count weights, fixed/automatic smoothing, optional clipping.
- [ ] Existing-measurement reuse across Nupper/alpha candidates, one shared
  ensemble per training profile, global tuning per design, fixed estimator sweeps.
- [ ] All density/sample-range/full-radius metrics and local scale-length metric.
- [ ] Five scripts, nine selected-channel layouts, all four studies and outputs.
- [ ] Geometry/reconstruction/noise figures, style presets, figure export controls,
  measurement tables, statistical summaries, and configuration snapshots.
- [ ] Matching error/warning behavior, documented algorithm differences, native
  setup on every requested OS/architecture, numerical convergence and performance.

The fallback penalized B-spline is fully specified in source. MATLAB Curve
Fitting Toolbox's smoothing-spline behavior requires an explicit open
replacement/parameter-equivalence policy; matching a function name is insufficient.

## Study detector layouts in the supplied source

All nine use G12430-016D with M=0.057 and image center [0,0]. Built-in 32/46-element
models remain required even though they are not selected by this current list.

| Source study label | Active physical detector IDs (1-based) |
| --- | --- |
| 16 Elements | 1–16 |
| 8 Elements, Full Coverage | 1, 3, 5, 7, 9, 11, 13, 15 |
| 8 Elements, Gradient Paired | 5, 6, 7, 8, 9, 10, 11, 12 |
| 6 Elements, Broad Coverage | 3, 5, 7, 9, 11, 13 |
| 6 Elements, Inner Gradient Paired | 5, 6, 7, 8, 9, 10 |
| 5 Elements, Inner-Mid Coverage | 5, 7, 9, 11, 13 |
| 5 Elements, Gradient Plus Outer | 3, 5, 7, 11, 13 |
| 4 Elements, Gradient Band | 5, 7, 11, 13 |
| 4 Elements, Inner Gradient | 5, 7, 9, 11 |

## Per-file translation map

Package module names without a directory prefix belong under
`src/heterodyne_density_lab/`. Grouping functions into modules is optional;
feature coverage and a clear public API matter more than a one-file-per-function
translation. Track completion of each source responsibility.

| Done | MATLAB file | Proposed Python/C destination | Responsibility |
| --- | --- | --- | --- |
| ☐ | `apply_study_design.m` | `studies.py` | Apply per-design geometry, centering, selection, and settings |
| ☐ | `fit_symmetric_smoothing_spline.m` | `splines.py` | Even-coordinate fit, duplicate merging, weighted smoothing, parameter policy |
| ☐ | `calculate_detector_power_limit.m` | `detectors.py` | Configured peak-power admissibility for the actual geometry |
| ☐ | `export_design_figure.m` | `export.py` | Figure formats, resolution, padding, and output mode |
| ☐ | `evaluate_nupper_sweep.m` | `diagnostics.py` | Basis-order scan, metric selection, and tolerance logic |
| ☐ | `line_integrated_density.m` | `forward.py + C Abel kernels` | Bounded-support Abel quadrature and blocked evaluation |
| ☐ | `build_pretzler_matrix.m` | `inversion.py + C basis quadrature` | Finite-area linearized forward matrix, rank/conditioning guards |
| ☐ | `density_profile.m` | `profiles.py + C profile kernels` | Generalized exponential inside R, zero outside R |
| ☐ | `evaluate_reconstruction_metric.m` | `metrics.py` | Named metric selection and aggregate scoring |
| ☐ | `study_detector_noise_contribution.m` | `scripts/study_detector_noise_contribution.py` | Fixed-estimator weighting/noise decomposition |
| ☐ | `plot_detector_noise_budget.m` | `plotting.py` | Per-element detector/shot/IQ/phase noise diagnostics |
| ☐ | `calculate_detector_noise.m` | `detectors.py` | Carrier, noise ASD, I/Q conversion, analytic phase uncertainty |
| ☐ | `get_detector_specs.m` | `detectors.py` | Typical/conservative/custom data and bias-dependent linearity curves |
| ☐ | `run_density_reconstruction.m` | `reconstruction.py` | Full measurement, noise, solve, spline, and result-table pipeline |
| ☐ | `study_pretzler_basis_order.m` | `scripts/study_pretzler_basis_order.py` | Underfit/rank/condition diagnostic with fixed selected alpha |
| ☐ | `apply_plot_style.m` | `plot_style.py` | Apply font, format, and output-mode style |
| ☐ | `study_density_scale_length.m` | `scripts/study_density_scale_length.py` | Primary spatial-resolution sweep with globally fixed estimator |
| ☐ | `check_curve_fitting_toolbox.m` | `installation checks + splines.py` | Replace proprietary toolbox check with open solver availability/validation |
| ☐ | `main_density_design.m` | `scripts/main_density_design.py` | Single design and all selected summaries/figures |
| ☐ | `plot_reconstruction_results.m` | `plotting.py` | Truth, sampled inversion, spline, confidence/statistical summaries |
| ☐ | `prepare_measurement_geometry.m` | `geometry.py + C quadrature` | Masks, clipping, quadrature weights, beam power, effective coordinates |
| ☐ | `pretzler_basis.m` | `inversion.py + C basis kernels` | Constant/cosine basis with consistent IDs and normalization |
| ☐ | `bspline_design_matrix.m` | `splines.py` | Cubic basis, knots, and evaluation consistent with open fallback |
| ☐ | `study_detector_power_tradeoff.m` | `scripts/study_detector_power_tradeoff.py` | Representative-profile power sweeps and invalid-power NaNs |
| ☐ | `optimize_reconstruction_hyperparameters.m` | `studies.py` | Global joint tuning on common I/Q measurement ensembles |
| ☐ | `get_plot_style.m` | `plot_style.py` | Screen/document/presentation style definitions |
| ☐ | `plot_imaging_geometry.m` | `plotting.py` | Object/image planes, port/beam, finite selected detector elements |
| ☐ | `make_study_config.m` | `config/study_config.py` | Central layouts, candidates, profiles, seeds, sweeps, outputs |
| ☐ | `calculate_heterodyne_phase_measurement.m` | `forward.py + C phasor kernels` | Finite-area phasor, calibration, atan2, linearization diagnostics |
| ☐ | `make_sensor_geometry.m` | `geometry.py` | Built-in/custom detector elements and active-channel convention |
| ☐ | `evaluate_density_scale_length_error.m` | `metrics.py` | Bounded symmetric scale-length error and derivative handling |
| ☐ | `reconstruct_existing_measurements.m` | `reconstruction.py` | Reuse measured ensembles at other basis orders/weights |
| ☐ | `make_default_design.m` | `config/default_design.py` | Full explicit SI baseline configuration |

## Outputs and scientific limitations

Preserve the measurement-table contents with units: physical IDs, masks,
image/object/effective coordinates, transmission and power fractions, probe and
reference/combined/peak powers, linearity limits/margins/validity, true/measured
line densities, uncertainties, complex/IQ/phase/coherence diagnostics, and
phase-linearization differences. Preserve error-summary distributions and
requested/used basis IDs, matrices, conditioning, sampled radius, spline outputs.
Use the original result/table definitions as the exact field inventory while
implementing; a shorter renamed schema must still retain every quantity.

Keep the original limitations explicit: no propagated optical field, ideal
reference calibration/demodulation, principal-phase wrapping with no absolute
multi-fringe tracking, limited detector-equivalent noise coverage, typical
rather than guaranteed linearity curves, cylindrical symmetry, and y-uniformity.
New effects should be optional documented extensions, not silent changes to
baseline physics.

Complete the open port against the actual source snapshot, then use the original
repository only to produce reference fixtures/results. Do not claim matching
Monte Carlo results based solely on equal numeric seed values across languages.
