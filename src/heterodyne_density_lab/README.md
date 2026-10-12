# Scientific Python package — author implementation pending

The supplied `__init__.py` establishes an importable namespace only. Write shared
configuration loading/validation, geometry, optical forward modeling, detectors,
reconstruction, metrics, study orchestration, plots, and export modules here.
See the migration checklist for a complete suggested mapping.

The future native extension is `heterodyne_density_lab._core`. A wrapper module
validates arrays and return codes, then calls its CFFI `lib` functions in batches.
Use installed metadata for the version instead of duplicating a version literal.
Do not trigger a simulation, plotting, or compilation just by importing a module.
