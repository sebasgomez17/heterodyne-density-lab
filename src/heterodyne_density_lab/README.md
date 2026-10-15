# Scientific package

| Module | Responsibility |
| --- | --- |
| configuration.py | SI dataclasses, validation, design application, trusted Python file loader |
| native.py | Checked CFFI buffer boundary and physical phase constant |
| model.py | Geometry, cached Abel/phasor forward model, detector specifications/power/noise |
| splines.py | Cached even penalized cubic B-spline and per-realization GCV |
| metrics.py | Density and bounded local scale-length metrics |
| reconstruction.py | Measurement ensembles, reused inversion, batched profiles and diagnostics |
| studies.py | Global tuning and fixed-estimator sweeps |
| outputs.py | Versioned CSV/JSON/NPZ output and content-keyed tuning cache |
| plotting.py | Shared scientific figures and style/export controls |
| entrypoints.py | Shared run-script orchestration |

Use `DesignConfig`, `Workspace`, `make_measurements`, `reconstruct`, and `simulate`
from their modules. Scientific arrays use realizations first: observations
(M,J), coefficients (M,B), profiles (M,G). Geometry indices are zero-based;
exported detector IDs and editable active-channel IDs are 1-based. No simulation
runs on package import. The compiled `_core` extension must be built first.
