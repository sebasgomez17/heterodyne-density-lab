"""Run study detector noise contribution. Edit config/*.py for persistent settings."""
from pathlib import Path
from heterodyne_density_lab.entrypoints import run

if __name__ == "__main__":
    run("study_detector_noise_contribution", Path(__file__).resolve().parents[1])
