# Computation steps and efficiency decisions

The scientific sequence below is implemented. It keeps the supplied model's
mathematics while sharing one forward/measurement/inversion engine among scripts.

| Step | Computation | Reuse / efficiency |
| --- | --- | --- |
| 1 | Validate SI configuration and construct physical sensor elements | One Workspace per detector design |
| 2 | Tensor Gauss–Legendre detector quadrature; signed image/object mapping; Gaussian probe/reference and circular port | Geometry independent of density, optical power, basis order, and alpha |
| 3 | Normalize complete beams; compute element powers, overlap, centroids, illumination masks | Centered Gaussian port integral is analytic; offset ports use polar quadrature |
| 4 | Sum cross weights over y because plasma phase is y-independent | Exactly the same tensor-quadrature sums; removes repeated phasor/basis output work |
| 5 | Deduplicate absolute transverse nodes across physical elements | The MATLAB source already deduplicated within each element; this extends reuse |
| 6 | Integrate the finite-support Abel density with the same transformed trapezoidal rule | Streaming C loops avoid large temporary radius/density matrices; cache up to 16 profiles |
| 7 | Form finite-area complex phasors; vacuum-calibrated principal phases and equivalent line densities | C weighted trigonometric accumulation on reduced nodes; reuse for power/noise comparisons |
| 8 | Check peak-cycle optical power on every physical element; compute detector/shot noise and ideal I/Q gains | Reject inadmissible power before costly forward calculations |
| 9 | Apply geometry/SNR selection and create seeded noisy I/Q measurements | One ensemble per training profile, reused across every order/alpha candidate |
| 10 | Integrate constant/cosine Pretzler basis and finite-area forward matrix | Cache a maximum-order bank; one cosine per integration node with recurrence for higher orders |
| 11 | Limit to independent leading columns and form tempered row weights | One small SVD solve operator per candidate, applied to all realizations |
| 12 | Evaluate Pretzler density at detector radii and on the dense radial grid | Batched matrix products through established BLAS-backed NumPy/SciPy |
| 13 | Add Pretzler-derived center/edge support, merge duplicate u=(abs(x)/R)^2 radii, and fit cubic penalized spline | Cached basis/normal/penalty/hat matrices for every lambda; choose GCV per realization in batches |
| 14 | Compute density RMS, local scale-length RMS, distributions, tables, and plots | Metrics-only study mode retains arrays of errors, not every dense profile |
| 15 | Aggregate training scores; select one global order/alpha; perform fixed-estimator sweeps | Content-keyed tuning JSON reused by separate script processes |

## Preserved mathematical choices

- Finite-support generalized exponential profiles and singularity-free Abel
  integration with the source's trapezoidal rule.
- Exact finite-area complex phasors; a linearized finite-area Pretzler inverse
  matrix. Their mismatch is a reported model limitation at large intra-element phase.
- Source detector tables/approximate linearity digitizations, vacuum peak-cycle
  admissibility, ideal I/Q conversion factors, and independent quadrature noise.
- Constant/cosine Pretzler basis, tempered weighting, rank protection,
  multiplicity-weighted even spline support, second coefficient-difference
  penalty, 1e-12 ridge, and per-realization GCV.
- Central study settings, shared training ensembles, fixed global estimators,
  source layouts/grids/counts and seed formulas, and separate study scripts.

## Consolidation and deliberate changes

One `reconstruct` function handles ordinary simulation, cached refits, tuning,
and the basis diagnostic; there are no duplicated solve/spline loops. One open
penalized B-spline replaces the original toolbox-dependent auto-selection.
The algebraic objective is the original fallback's objective; no unverified
mapping to MATLAB's proprietary smoothing parameter is introduced.

Noise uses NumPy PCG64. Equal seed integers do not imply equal MATLAB/Python
samples. External normal arrays can be supplied for controlled comparisons.
Array layouts place realizations first. SVD-based small least squares replaces
repeated per-realization backslash calls. Reductions and accumulated sums may
differ in their last floating-point bits; numerical tolerances are explicit.

Python retains optimized linear algebra rather than rebuilding BLAS/LAPACK in
C. C handles the streaming quadrature and phase kernels. No mandatory OpenMP,
GPU, C++ runtime, fast-math, or CPU-specific optimization flags are required.
Scripts limit BLAS to one thread for small systems; library callers control
their own thread policy. The default batch size is 256 and configurable.

## Measured performance and limits

See VALIDATION.md for local benchmarks. The measured comparisons are against
NumPy versions of the same rule, not against a running MATLAB application.
Full study runtimes include figure/file export and depend on cache availability,
CPU, compiler, dependency versions, batch size, thread settings, and numerical
resolution. Cached tuning never substitutes a different configuration: its key
includes the physics, training settings, actual Python/extension hashes and
relevant versions. Clear/recompute the cache through --refresh-tuning if desired.

Changing the optical geometry requires a new Workspace; changing plasma/power
within its supported scope uses keyed calculations. Cache sizes are bounded.
Changing radius or basis quadrature changes its bank key. Profile changes alter
the forward-cache key. Optional SNR filtering can change the retained matrix,
so row selection and rank checks are performed for each measurement ensemble.
