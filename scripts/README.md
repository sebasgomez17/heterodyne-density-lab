# Individual run scripts

Run from the repository root through `poetry run python scripts/FILE.py`.

| Script | Purpose |
| --- | --- |
| main_density_design.py | Single design, geometry/reconstruction/noise figures and tables |
| study_density_scale_length.py | Density and local scale-length error versus profile scale |
| study_detector_power_tradeoff.py | Fixed-estimator power sweep, operating window, inadmissible NaNs |
| study_detector_noise_contribution.py | Fixed-estimator deterministic weighting and stochastic noise effects |
| study_pretzler_basis_order.py | Fixed-alpha order, rank, and conditioning diagnostic |
| benchmark_kernels.py | Optional local C-versus-NumPy quadrature timing/accuracy check |

The five scientific scripts are thin entry points to one shared runner. Editable
files are loaded by absolute repository-relative paths, with no sys.path edits.
Each scientific script accepts --quick for a labeled reduced check and
--refresh-tuning to recompute a matching global tuning cache. Normal runs use the
original source's scientific grids/sample counts. Unique run folders prevent
silent overwrite; seeds, configuration, software versions, results and timings
are saved. Results/figures are generated locally, not published automatically.
