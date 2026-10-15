"""Run study density scale length. Edit config/*.py for persistent settings."""
from pathlib import Path
from heterodyne_density_lab.entrypoints import run

if __name__ == "__main__":
    run("study_density_scale_length", Path(__file__).resolve().parents[1])
