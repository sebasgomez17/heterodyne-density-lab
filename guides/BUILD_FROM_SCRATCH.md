# Implementation and development guide

Version 0.1.0 now contains the scientific implementation. Start with README.md
for setup and run commands, COMPUTATION_PLAN.md for the numerical sequence,
MIGRATION_CHECKLIST.md for the per-file source coverage, and the scientific
LaTeX manual for equations, algorithm choices, and limitations.

## Public library workflow

```python
from heterodyne_density_lab.configuration import DesignConfig
from heterodyne_density_lab.model import Workspace
from heterodyne_density_lab.reconstruction import make_measurements, reconstruct, simulate

cfg = DesignConfig()
cfg.noise.realizations = 100
workspace = Workspace(cfg)
result = simulate(cfg, workspace)

ensemble = make_measurements(cfg, workspace)
ols = reconstruct(ensemble, upper_order=3, alpha=0.0)
wls = reconstruct(ensemble, upper_order=3, alpha=1.0)
```

The two refits use identical measured I/Q samples. `retain_profiles=False`
returns summary profiles/errors without keeping dense per-realization arrays;
`compute_scale=False` skips derivative metrics when a tuning score does not
need them. External standard normals have shape (realizations,2,channels) and
are accepted by make_measurements/simulate only in detector_limited mode.

Use the editable config factories for script runs. Adding a study usually means
calling the existing measurement/reconstruction engine with explicit settings
and reporting the new independent variable; avoid copying the solver or spline.
No scientific work occurs at module import.

## C changes and packaging

`csrc/hdl_core.h` defines the public, allocation-free double-buffer API.
`native.py` checks dtype/layout, dimensions, finite inputs, and status returns.
`build_ffi.py` contains preprocessor-free CFFI declarations and uses set_source
with the header and C source. `setup.py` provides the standard cffi_modules hook;
metadata/dependencies remain in pyproject.toml.

After C/header/builder changes, from the repository root:

```text
poetry run python -m pip install --no-deps --force-reinstall --no-build-isolation -e .
poetry run python -c "from heterodyne_density_lab._core import ffi, lib; print('C extension import OK')"
```

Use the OS guide's compiler-enabled environment; on Linux export CC=gcc where
needed. Poetry's own root editable installer does not run setuptools' hook, so
keep the explicit backend step. Do not replace the backend with poetry-core
and assume the hook survives. Build isolation needs declared CFFI requirements;
normal editable builds use the installed locked build tools.

## Validation and release

```text
poetry install --with dev
poetry run pytest
poetry check --lock
poetry run python -m build
```

Inspect the source archive for builder/header/kernels and test installing it,
not just a Git checkout. Native wheels are platform-specific. The GitHub source
route intentionally requires a user compiler. Do not commit .venv, binaries,
cache/results, or documentation auxiliary files. Source figures and the compiled
manual are deliberately distributable documentation artifacts.

Update project.version, version.txt and CHANGELOG.md together. The version is
queried through installed metadata; do not add an independent version literal.
Any model/algorithm change should add meaningful numerical tests and update
the manual. Compare common random arrays for deterministic stochastic-algorithm
checks; seed equality across languages is not sufficient.

## Continuous integration

.github/workflows/scientific-tests.yml runs numerical and entry-point checks on
six native runner architectures and Python 3.12/3.13 after you push. It tests
source/wheel building too. Its Windows x64 runner is Server 2025; Windows ARM64
uses Windows 11. Hosted-runner tests do not replace a manual clean desktop
installation check. This workflow was prepared but not executed here.

## Updating the repository you already created

Copy the release's project contents into the existing local repository root.
Keep its .git folder and local environment. Review configuration changes before
replacing custom settings. Rebuild the native extension and run the tests, then:

```text
git status
git add .
git commit -m "Implement heterodyne simulation and density reconstruction"
git push
```

The release archive contains no Git metadata and does not create/push a repository
on your behalf. The original MATLAB repository stays separate. Native macOS,
Windows x64/ARM64, and Linux ARM64 execution must still be validated on those
systems; the current executed numerical checks are on Linux x86_64.
