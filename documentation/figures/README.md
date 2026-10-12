# Figure slots for the author

Export your own vector PDF figures using these filenames. The document shows a
framed placeholder when an input is missing. You can change the filenames,
formats, and captions deliberately in `main.tex`; keep labels stable for references.
PDF is preferred for scientific line plots. This folder contains no generated
scientific figures or manufacturer artwork.

| Expected file | LaTeX label | Intended figure |
| --- | --- | --- |
| `density_profiles.pdf` | `fig:density-profiles` | Density profiles and profile parameters |
| `imaging_geometry.pdf` | `fig:geometry` | Object/image geometry, beam, port, and detector elements |
| `measurement_chain.pdf` | `fig:measurement-chain` | Measurement and reconstruction pipeline |
| `detector_noise_budget.pdf` | `fig:noise-budget` | Detector, quadrature, and phase-noise budget |
| `detector_linearity.pdf` | `fig:linearity` | Typical linearity curves and chosen operating criterion |
| `spline_comparison.pdf` | `fig:splines` | Pretzler and symmetric spline reconstruction comparison |
| `global_tuning.pdf` | `fig:tuning` | Global joint hyperparameter selection |
| `study_scale_length.pdf` | `fig:scale-length-study` | Primary density-scale-length study |
| `study_power_tradeoff.pdf` | `fig:power-study` | Detector-power tradeoff with operating-range constraints |
| `runtime_scaling.pdf` | `fig:runtime` | Runtime and memory scaling for representative studies |
| `quadrature_convergence.pdf` | `fig:convergence` | Numerical convergence and reference agreement |
| `study_noise_contribution.pdf` | `fig:noise-study` | Noise and weighting decomposition |
| `study_basis_order.pdf` | `fig:basis-study` | Basis-order diagnostics |

Each figure caption is a topic prompt, not a scientific result. Fill in axis
units, geometry/parameters, sample counts, estimator settings, and uncertainty
meaning. Export plots deliberately; regular runs write to `output/` instead.
