"""Explicit SI-unit configuration, fresh defaults, and editable-file loading."""
from dataclasses import dataclass, field, asdict
from pathlib import Path
import importlib.util
import copy
import math

@dataclass
class Plasma:
    radius_m: float = 0.10
    peak_density_m3: float = 1e19
    background_density_m3: float = 0.0
    scale_length_m: float = 0.025
    exponent: float = 2.0

@dataclass
class Beam:
    waist_m: float = 0.037
    center_m: tuple = (0.0, 0.0)
    reference_mode: str = "matched_probe"
    reference_waist_m: float = 0.037
    reference_center_m: tuple = (0.0, 0.0)

@dataclass
class Port:
    diameter_m: float = 0.1397
    center_m: tuple = (0.0, 0.0)

@dataclass
class Sensor:
    model: str = "G12430-016D"
    center_image_m: tuple = (0.0, 0.0)
    active_elements: object = "all" # physical IDs 1..N, or boolean mask
    minimum_illumination_fraction: float = 0.05
    elements: int = 16
    width_m: float = 0.00045
    height_m: float = 0.001
    pitch_m: float = 0.0005

@dataclass
class Heterodyne:
    wavelength_m: float = 1.55e-6
    total_power_W: float = 0.05
    probe_fraction: float = 0.5
    frequency_Hz: float = 1e7
    bandwidth_Hz: float = 1e6

@dataclass
class Detector:
    specification_case: str = "typical"
    include_shot_noise: bool = True
    reverse_bias_V: float = 1.0
    enforce_linearity: bool = True
    minimum_relative_sensitivity: float = 0.99
    safety_factor: float = 1.0
    minimum_line_density_SNR: float = 0.0
    cutoff_warning_fraction: float = 0.8
    minimum_carrier_SNR: float = 5.0
    custom: dict = field(default_factory=dict)

@dataclass
class Inversion:
    lower_order: int = 1
    upper_order: int = 3
    diagnostic_max_order: int = 8
    include_constant: bool = True
    quadrature_points: int = 1000
    enforce_rank_limit: bool = True
    warn_rank_reduction: bool = True
    condition_warning: float = 1e6
    weighting_alpha: float = 1.0

@dataclass
class Spline:
    # Canonical open method: source MATLAB's penalized cubic B-spline.
    basis_count: int = 10
    lambda_value: float | None = None
    lambda_candidates: tuple = field(default_factory=lambda: tuple(10**(-8+12*k/79) for k in range(80)))
    clip_nonnegative: bool = False

@dataclass
class Noise:
    model: str = "detector_limited"
    realizations: int = 1
    seed: int = 1
    relative_level: float = 0.001
    batch_size: int = 256

@dataclass
class Numerics:
    element_order: int = 20
    line_points: int = 1000
    radial_points: int = 1000

@dataclass
class Plots:
    show: bool = False # headless-safe; set True for interactive windows
    geometry: bool = True
    reconstruction: bool = True
    noise: bool = True
    measurement_table: bool = True
    mode: str = "screen"
    font: str = "DejaVu Sans"
    output_directory: str = "output"
    figure_format: str = "pdf"
    dpi: int = 300
    padding_inches: float = 0.05

@dataclass
class DesignConfig:
    plasma: Plasma = field(default_factory=Plasma)
    beam: Beam = field(default_factory=Beam)
    port: Port = field(default_factory=Port)
    sensor: Sensor = field(default_factory=Sensor)
    heterodyne: Heterodyne = field(default_factory=Heterodyne)
    detector: Detector = field(default_factory=Detector)
    inversion: Inversion = field(default_factory=Inversion)
    spline: Spline = field(default_factory=Spline)
    noise: Noise = field(default_factory=Noise)
    numerics: Numerics = field(default_factory=Numerics)
    plots: Plots = field(default_factory=Plots)
    magnification: float = 0.057

    def validate(self):
        def positive(v, name):
            if not math.isfinite(v) or v <= 0: raise ValueError(f"{name} must be finite and positive")
        def integer(v, name, minimum):
            if isinstance(v, bool) or not isinstance(v, int) or v < minimum: raise ValueError(f"{name} must be integer >= {minimum}")
        for v, name in [(self.plasma.radius_m,'radius'),(self.plasma.peak_density_m3,'peak density'),
            (self.plasma.scale_length_m,'profile scale'),(self.plasma.exponent,'profile exponent'),
            (self.beam.waist_m,'beam waist'),(self.beam.reference_waist_m,'reference waist'),
            (self.port.diameter_m,'port diameter'),(self.heterodyne.wavelength_m,'wavelength'),
            (self.heterodyne.total_power_W,'total power'),(self.heterodyne.bandwidth_Hz,'bandwidth'),
            (self.heterodyne.frequency_Hz,'IF frequency')]: positive(v,name)
        if not 0 <= self.plasma.background_density_m3 <= self.plasma.peak_density_m3: raise ValueError('Background density must lie between zero and peak density')
        if not math.isfinite(self.magnification) or self.magnification == 0: raise ValueError('Magnification must be finite and nonzero')
        for c in [self.beam.center_m,self.beam.reference_center_m,self.port.center_m,self.sensor.center_image_m]:
            if len(c) != 2 or not all(math.isfinite(v) for v in c): raise ValueError('Centers must be two finite coordinates')
        if self.beam.reference_mode not in ['matched_probe','unclipped_gaussian']: raise ValueError('Unknown reference mode')
        if self.noise.model not in ['detector_limited','detector_weighted_noiseless','noiseless','relative']: raise ValueError('Unknown noise model')
        for v,name,m in [(self.noise.realizations,'realizations',1),(self.noise.batch_size,'batch size',1),
            (self.noise.seed,'seed',0),(self.numerics.element_order,'element order',1),
            (self.numerics.line_points,'line points',2),(self.numerics.radial_points,'radial points',3),
            (self.inversion.quadrature_points,'basis quadrature',2),(self.inversion.lower_order,'lower order',1),
            (self.inversion.upper_order,'upper order',self.inversion.lower_order),(self.spline.basis_count,'spline basis count',4)]: integer(v,name,m)
        if not 0 < self.heterodyne.probe_fraction < 1: raise ValueError('Probe fraction must lie in (0,1)')
        for v,name in [(self.inversion.weighting_alpha,'alpha'),(self.sensor.minimum_illumination_fraction,'illumination threshold')]:
            if not math.isfinite(v) or not 0 <= v <= 1: raise ValueError(f'{name} must lie in [0,1]')
        if not 0 < self.detector.safety_factor <= 1 or not 0 < self.detector.minimum_relative_sensitivity <= 1: raise ValueError('Invalid linearity criterion')
        for v,name in [(self.noise.relative_level,'relative noise'),(self.detector.minimum_line_density_SNR,'SNR filter'),
            (self.detector.minimum_carrier_SNR,'carrier SNR threshold'),(self.detector.cutoff_warning_fraction,'cutoff warning fraction')]:
            if not math.isfinite(v) or v < 0: raise ValueError(f'{name} must be nonnegative')
        lambdas = self.spline.lambda_candidates if self.spline.lambda_value is None else [self.spline.lambda_value]
        if len(lambdas)==0 or any(not math.isfinite(v) or v<0 for v in lambdas): raise ValueError('Spline penalties must be finite, nonnegative, and nonempty')
        return self

    def clone(self):
        return copy.deepcopy(self)

@dataclass
class DetectorDesign:
    name: str
    active_elements: object
    sensor_model: str = "G12430-016D"
    magnification: float = 0.057
    center_image_m: tuple = (0.0,0.0)

@dataclass
class Optimization:
    upper_orders: tuple = (2,3,4)
    alphas: tuple = field(default_factory=lambda: tuple(k/10 for k in range(11)))
    training_scales: tuple = (0.10,0.15,0.20,0.25,0.30)
    metric: str = "spline_full"
    nominal_power_W: float = 0.05
    realizations: int = 100
    seed: int = 1201

def default_designs():
    return [DetectorDesign(name,ids) for name,ids in [
        ('16 Elements',tuple(range(1,17))),('8 Elements, Full Coverage',(1,3,5,7,9,11,13,15)),
        ('8 Elements, Gradient Paired',(5,6,7,8,9,10,11,12)),('6 Elements, Broad Coverage',(3,5,7,9,11,13)),
        ('6 Elements, Inner Gradient Paired',(5,6,7,8,9,10)),('5 Elements, Inner-Mid Coverage',(5,7,9,11,13)),
        ('5 Elements, Gradient Plus Outer',(3,5,7,11,13)),('4 Elements, Gradient Band',(5,7,11,13)),
        ('4 Elements, Inner Gradient',(5,7,9,11))]]

@dataclass
class StudyConfig:
    designs: list = field(default_factory=default_designs)
    optimization: Optimization = field(default_factory=Optimization)
    scale_lengths: tuple = field(default_factory=lambda: tuple(0.10+0.025*k for k in range(9)))
    scale_realizations: int = 1000
    power_profiles: tuple = (0.10,0.20,0.30)
    power_log10_min: float = -3
    power_log10_max: float = -1
    power_points_per_decade: int = 8
    power_realizations: int = 1
    noise_realizations: int = 1
    basis_design_index: int = 0 # Python index into designs
    basis_profile: float = 0.15
    basis_orders: tuple = (2,3,4,5,6,7,8)
    basis_realizations: int = 1
    basis_metric: str = "spline_full"
    basis_tolerance: float = 0.01
    cache_tuning: bool = True
    output_mode: str = "presentation"

def apply_design(base, design):
    c=base.clone()
    c.sensor.model=design.sensor_model
    c.sensor.active_elements=design.active_elements
    c.sensor.center_image_m=design.center_image_m
    c.magnification=design.magnification
    return c

def load_configuration(path, factory, *args):
    """Load trusted user-edited Python by path; no sys.path mutation required."""
    path=Path(path).resolve()
    spec=importlib.util.spec_from_file_location('_hdl_user_config',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module,factory)(*args)
