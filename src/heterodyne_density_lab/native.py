"""Checked array boundary for the compiled, allocation-free numerical kernels."""
import numpy as np
try:
    from ._core import ffi, lib
except ImportError as exc:
    raise ImportError("C extension missing. Follow README step 3 to build inside the Poetry environment.") from exc

ELECTRON_RADIUS_M = 2.8179403262e-15

def _array(x):
    a = np.ascontiguousarray(x, dtype=np.float64)
    if not np.isfinite(a).all():
        raise ValueError("Native kernel inputs must be finite")
    return a

def _ptr(a, output=False):
    return ffi.from_buffer("double[]" if output else "const double[]", a)

def _check(status):
    if status:
        raise ValueError("Invalid native-kernel dimensions or physical parameters")

def _integer(value, minimum, name):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or not minimum <= value <= 2147483647:
        raise ValueError(f"{name} must be an integer >= {minimum} fitting a C int")
    return int(value)

def abel_density(x, plasma, points):
    points = _integer(points, 2, "Quadrature points")
    params = [plasma.radius_m, plasma.peak_density_m3, plasma.background_density_m3, plasma.scale_length_m, plasma.exponent]
    if not np.isfinite(params).all() or min(plasma.radius_m, plasma.scale_length_m, plasma.exponent) <= 0:
        raise ValueError("Invalid Abel profile parameters")
    a = _array(x)
    out = np.empty(a.shape)
    _check(lib.hdl_abel_density(a.size, _ptr(a), plasma.radius_m, plasma.peak_density_m3,
        plasma.background_density_m3, plasma.scale_length_m, plasma.exponent, int(points), _ptr(out, True)))
    return out

def abel_basis(x, radius, max_order, points):
    max_order = _integer(max_order, 0, "Maximum basis order")
    points = _integer(points, 2, "Quadrature points")
    if not np.isfinite(radius) or radius <= 0:
        raise ValueError("Radius must be finite and positive")
    a = _array(x)
    out = np.empty(a.shape + (max_order + 1,))
    _check(lib.hdl_abel_basis(a.size, _ptr(a), radius, int(max_order), int(points), _ptr(out, True)))
    return out

def phasor(h, weights, factor):
    if not np.isfinite(factor) or factor <= 0: raise ValueError("Phase factor must be finite and positive")
    h, weights = _array(h), _array(weights)
    if h.ndim != 2 or weights.shape != h.shape:
        raise ValueError("Phasor inputs must have equal (elements, transverse_nodes) shapes")
    if (weights < 0).any(): raise ValueError("Phasor weights cannot be negative")
    out = [np.empty(h.shape[0]) for _ in range(3)]
    _check(lib.hdl_phasor(*h.shape, _ptr(h), _ptr(weights), factor, *[_ptr(a, True) for a in out]))
    return out[0] + 1j*out[1], out[2]

def iq_samples(carrier, sigma, normals, factor):
    if not np.isfinite(factor) or factor <= 0: raise ValueError("Phase factor must be finite and positive")
    carrier = np.asarray(carrier, dtype=np.complex128)
    re, im, sigma, normals = _array(carrier.real), _array(carrier.imag), _array(sigma), _array(normals)
    if carrier.ndim != 1 or sigma.shape != carrier.shape or normals.ndim != 3 or normals.shape[1:] != (2, carrier.size):
        raise ValueError("I/Q normals must have shape (realizations, 2, channels)")
    if (sigma < 0).any():
        raise ValueError("Noise standard deviations cannot be negative")
    out = [np.empty((normals.shape[0], carrier.size)) for _ in range(4)]
    _check(lib.hdl_iq_samples(carrier.size, normals.shape[0], _ptr(re), _ptr(im), _ptr(sigma),
        _ptr(normals), factor, *[_ptr(a, True) for a in out]))
    return tuple(out)
