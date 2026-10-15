"""Shared study designs, training ensemble, and sweep configuration."""
from heterodyne_density_lab.configuration import StudyConfig

def make_study_config(base):
    study = StudyConfig()
    # Edit counts/grids here; scientific defaults match the supplied source.
    # study.designs = study.designs[:1]  # optional focused study
    # study.scale_realizations = 1000
    return study
