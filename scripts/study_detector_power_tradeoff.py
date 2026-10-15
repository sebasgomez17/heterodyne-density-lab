"""Run study detector power tradeoff. Edit config/*.py for persistent settings."""
from pathlib import Path
from heterodyne_density_lab.entrypoints import run

if __name__ == "__main__":
    run("study_detector_power_tradeoff", Path(__file__).resolve().parents[1])
