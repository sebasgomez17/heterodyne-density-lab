"""Edit this factory for a single design. Values use SI units."""
from heterodyne_density_lab.configuration import DesignConfig

def make_default_design():
    cfg = DesignConfig()
    # Example: cfg.plasma.scale_length_m = 0.02
    # Example: cfg.sensor.active_elements = (5, 6, 7, 8, 9, 10, 11, 12)
    # Example: cfg.noise.realizations = 1000
    # cfg.plots.show = True  # open interactive windows after saving
    return cfg
