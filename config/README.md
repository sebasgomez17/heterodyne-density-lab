# Editable Python configuration

`default_design.py` returns a fresh `DesignConfig`; edit its factory for persistent
single-design changes. `study_config.py` returns a fresh `StudyConfig` and defines
shared detector layouts, tuning candidates/training profiles, seeds/sample counts,
and sweeps. The full default schema is in `configuration.py` and the scientific
manual. All lengths are meters, powers watts, density m^-3, frequency/ENBW hertz.

Active detector selections use physical IDs 1..N (or a full boolean mask). The
study's `basis_design_index` is a normal zero-based Python list index. Defaults
follow the supplied source, including 50 mW optical power, all 16 elements, and
one baseline realization; former main-script overrides are optional examples.

Do not change physics inside a study run script. The optional `--quick` switch
is a labeled installation-check preset, recorded in saved configuration JSON.
Every run creates its output directory and saves its configuration/environment.
Set `cfg.plots.show=True` for interactive figures; the default is saving PDFs
without opening windows. Set figure_format to png/svg if preferred.
