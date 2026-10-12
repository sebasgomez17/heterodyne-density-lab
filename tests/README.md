# Numerical and platform validation plan

The author will write tests as the scientific implementation is added. This
folder contains a plan, not tests passing an unimplemented algorithm. Running
pytest before adding tests may return pytest's no-tests-collected exit status.

## Deterministic model checks

- Zero-density phase, bounded-support analytic/known Abel transforms, endpoint
  behavior, and convergence with line/element quadrature order.
- Signed magnification, element centers, finite detector areas, active masks,
  port clipping, beam normalization, and custom detector geometry.
- Separate probe/reference powers, matched/unclipped reference modes, vacuum
  phase calibration, exact phasors, and small-phase agreement.
- Typical/conservative/custom detector specifications, shot noise toggle,
  peak-cycle power and typical-linearity interpolation/limits, and cutoff/SNR warnings.
- C vs Python reference buffers, shape/layout/precision, error returns, all
  supported architectures, and invalid/empty input behavior.

## Reconstruction and statistical checks

- Pretzler basis integrals, rank limiting/warnings, unweighted/tempered/weighted
  solves, relative-noise legacy mode, condition numbers, and measurement reuse.
- Both open spline routes, duplicate grouping/weights, parity, central derivative,
  nonnegative clipping, and explicit smoothing-parameter equivalence policy.
- Full-radius/sample-range density metrics and bounded local scale-length error,
  including zero derivatives and edge cases.
- All four noise modes and documented I/Q mean/variance. Use identical externally
  supplied random arrays for deterministic MATLAB comparisons; same seed values
  alone do not give the same MATLAB/Python random stream.
- Fixed global hyperparameter selection using shared ensembles; hold selected
  estimator settings fixed through physical sweeps.
- Every source detector layout, all five run scripts, plot/export modes, table
  column units, automatic output creation, and saved configuration/version/seed.

## Installation and release checks

Run separate clean-install checks on macOS Intel/Apple Silicon, Windows 11
x64/native ARM64, and Linux x86_64/ARM64, for the supported Python versions.
Include source-release installation, native `_core` import, and all five scripts.
Record OS/compiler/Python/dependency versions and mark untested targets honestly.
Benchmark whole representative studies only after numerical convergence and
accuracy agree. Do not introduce mirrored tests that only restate implementation.

When tests exist, install the optional tools and run:

```text
poetry install --with dev
poetry run pytest
```
