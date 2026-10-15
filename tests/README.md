# Numerical validation

Install optional test tools with `poetry install --with dev`, then run
`poetry run pytest` from the repository root. Independent analytic/transformed
quadrature and direct NumPy references check C integration, finite-area phasors,
power/noise scaling, spline/GCV equivalence, batched solves, modes/metrics,
randomness, rank guards, all source detector layouts, and fixed-estimator studies.

See `guides/VALIDATION.md` for measured results and remaining platform validation.
The suite does not claim a direct MATLAB runtime comparison: that application
is unavailable in the validation environment. Same-rule reference tests and
analytic convergence checks establish the numerical comparisons actually made.
