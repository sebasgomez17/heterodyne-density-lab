# Editable Python configurations — author implementation pending

Write `default_design.py` and `study_config.py` here. They should return a fresh
validated configuration, using dictionaries or dataclasses. The run scripts
load these files by absolute path from the repository; users edit them directly.
The loader belongs in the installed package. No user CLI/configuration framework
is required.

Keep these groups explicit: plasma, probe/reference beams, port, signed imaging,
optical wavelength, heterodyne settings, sensor selection/centering/illumination,
detector specifications/linearity, reconstruction weights, noise/Monte Carlo,
Pretzler basis/rank limits, spline parameters, numerical grids, plotting/export.
Use meters, m^-3, watts, hertz, and a documented optical-radius convention.
User-facing physical detector IDs are 1-based; internal indices can be 0-based.

The study file defines all detector layouts, training profiles, candidate
Nupper/alpha values, fixed global tuning, seeds, sample counts, sweeps, and output
settings. Preserve the nine source layouts and all four studies. Configuration
filenames/fields are a proposed interface until the author implements them.

Decide explicitly whether to adopt the supplied source's 50 mW default or a
new baseline. The old README's 1 mW description differs from the source. Main
script overrides should become a named example, not undocumented defaults.

Output defaults should resolve to the repository's `output/` folder. Exports
for the LaTeX document are deliberate, separate operations. Save a serializable
configuration snapshot beside every scientific run's outputs.
