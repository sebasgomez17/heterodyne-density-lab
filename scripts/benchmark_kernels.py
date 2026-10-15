"""Benchmark C kernels against the same trapezoidal rule in NumPy (not MATLAB).

Run: poetry run python scripts/benchmark_kernels.py
Outputs are reproducible inputs and measured local timings; speedups are machine-specific.
"""
from pathlib import Path
import time
import numpy as np
from threadpoolctl import threadpool_limits
from heterodyne_density_lab.configuration import load_configuration
from heterodyne_density_lab.model import Workspace
from heterodyne_density_lab import native
from heterodyne_density_lab.outputs import new_run,write_json


def density_numpy(x,p,nq):
    t=np.linspace(0,1,nq);smax=np.sqrt(np.maximum(p.radius_m**2-x*x,0))
    r=np.sqrt(x[:,None]**2+(smax[:,None]*t)**2)
    density=(p.peak_density_m3-p.background_density_m3)*np.exp(-(r/p.scale_length_m)**p.exponent/p.exponent)+p.background_density_m3
    return 2*smax*np.trapezoid(density,t,axis=1)


def basis_numpy(x,R,order,nq):
    t=np.linspace(0,1,nq);smax=np.sqrt(np.maximum(R*R-x*x,0))
    r=np.sqrt(x[:,None]**2+(smax[:,None]*t)**2)
    out=np.empty((len(x),order+1))
    for n in range(order+1):
        values=np.ones_like(r) if n==0 else 1-(-1)**n*np.cos(n*np.pi*r/R)
        out[:,n]=2*smax*np.trapezoid(values,t,axis=1)
    return out


def timed(function,repeats=9):
    function();samples=[]
    for _ in range(repeats):
        t=time.perf_counter();function();samples.append(time.perf_counter()-t)
    return float(np.median(samples))


def main():
    root=Path(__file__).resolve().parents[1]
    cfg=load_configuration(root/'config/default_design.py','make_default_design')
    w=Workspace(cfg);x=w.x_unique;nq=cfg.numerics.line_points;order=cfg.inversion.diagnostic_max_order
    native_density=lambda:native.abel_density(x,cfg.plasma,nq)
    numpy_density=lambda:density_numpy(x,cfg.plasma,nq)
    native_basis=lambda:native.abel_basis(x,cfg.plasma.radius_m,order,cfg.inversion.quadrature_points)
    numpy_basis=lambda:basis_numpy(x,cfg.plasma.radius_m,order,cfg.inversion.quadrature_points)
    with threadpool_limits(limits=1):
        pairs=[('density_abel',native_density,numpy_density),('basis_abel',native_basis,numpy_basis)]
        rows=[]
        for name,c,ref in pairs:
            a,b=c(),ref();np.testing.assert_allclose(a,b,rtol=1e-12,atol=1e-14 if name=='basis_abel' else 1e3)
            tc=timed(c);tr=timed(ref)
            rows.append(dict(kernel=name,c_seconds=tc,numpy_seconds=tr,numpy_over_c=tr/tc,
                relative_max_difference=float(np.max(np.abs(a-b))/np.max(np.abs(b)))))
    path=new_run(root,cfg,'benchmark_kernels')
    report=dict(unique_impact_parameters=len(x),quadrature_points=nq,basis_max_order=order,repeats=9,
        comparator='NumPy implementation of original trapezoidal rule; no MATLAB timing claim',rows=rows)
    write_json(path/'benchmark.json',report);print(report);print('Outputs:',path)

if __name__=='__main__':main()
