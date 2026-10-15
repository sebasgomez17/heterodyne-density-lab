"""Run main density design. Edit config/*.py for persistent settings."""
from pathlib import Path
from heterodyne_density_lab.entrypoints import run

if __name__ == "__main__":
    run("main_density_design", Path(__file__).resolve().parents[1])
