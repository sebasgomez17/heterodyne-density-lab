# Run scripts — author implementation pending

Write these five scripts with the same scientific coverage as their MATLAB
counterparts. Keep them short and put reusable scientific code in the installed
`heterodyne_density_lab` package.

| Planned file | Function |
| --- | --- |
| `main_density_design.py` | Single design and all requested summaries/figures |
| `study_density_scale_length.py` | Full-radius density and local scale-length errors |
| `study_detector_power_tradeoff.py` | Fixed-estimator power sweep with invalid powers marked |
| `study_detector_noise_contribution.py` | Separate noiseless/weighting/noise effects |
| `study_pretzler_basis_order.py` | Basis, rank, and condition-number diagnostic |

Users will run `poetry run python scripts/FILE.py` from the repository root.
Load editable configurations by repository-relative absolute paths; script-by-
path execution does not guarantee that the root is importable. Use an installed
shared configuration loader and `Path(__file__)` as described in the build guide.
Use a main guard, print meaningful progress, create output folders automatically,
and save configurations/units/version/seeds with results. Avoid silent overrides.

The files above are not supplied in 0.1.0; the author will write and comment them.
