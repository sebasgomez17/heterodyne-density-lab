"""Independent identities and direct NumPy quadrature check the C/optics boundary."""
import numpy as np
import pytest
from scipy.special import erf, roots_legendre
from heterodyne_density_lab.configuration import DesignConfig, apply_design, default_designs
from heterodyne_density_lab.model import Workspace,prepare_geometry,detector_noise,detector_specs,power_limit,density_profile
from heterodyne_density_lab import native


def trap_reference(x,p,points):
    x=np.abs(np.asarray(x));smax=np.sqrt(np.maximum(p.radius_m**2-x**2,0))
    t=np.linspace(0,1,points);radius=np.sqrt(x[:,None]**2+(smax[:,None]*t)**2)
    values=(p.peak_density_m3-p.background_density_m3)*np.exp(-(radius/p.scale_length_m)**p.exponent/p.exponent)+p.background_density_m3
    return np.where(x<p.radius_m,2*smax*np.trapezoid(values,t,axis=1),0)

@pytest.mark.parametrize('exponent',[1.3,2,3.5])
def test_c_abel_matches_original_trapezoid(exponent):
    cfg=DesignConfig();cfg.plasma.exponent=exponent
    x=np.array([0,.001,.017,-.064,.09999,.10,.13])
    expected=trap_reference(x,cfg.plasma,711)
    np.testing.assert_allclose(native.abel_density(x,cfg.plasma,711),expected,rtol=2e-14,atol=1e2)


def test_gaussian_abel_analytic_and_constant_profile():
    cfg=DesignConfig();p=cfg.plasma;x=np.linspace(0,p.radius_m,31)
    expected=p.peak_density_m3*np.exp(-x*x/(2*p.scale_length_m**2))*np.sqrt(2*np.pi)*p.scale_length_m*erf(np.sqrt(np.maximum(p.radius_m**2-x*x,0))/(np.sqrt(2)*p.scale_length_m))
    errors=[]
    for q in [101,401,1601]:errors.append(np.max(np.abs(native.abel_density(x,p,q)-expected))/expected.max())
    assert errors[-1]<errors[0]/200
    p.background_density_m3=p.peak_density_m3
    np.testing.assert_allclose(native.abel_density(x,p,97),2*p.peak_density_m3*np.sqrt(np.maximum(p.radius_m**2-x*x,0)),rtol=3e-14,atol=1e3)


def test_basis_direct_cosines_vs_c_recurrence():
    x=np.array([0,.019,-.083,.10]);R=.10;nq=603;t=np.linspace(0,1,nq)
    maximum=np.sqrt(np.maximum(R*R-x*x,0));rad=np.sqrt(x[:,None]**2+(maximum[:,None]*t)**2)
    ref=[]
    for n in range(15):
        value=np.ones_like(rad) if n==0 else 1-(-1)**n*np.cos(n*np.pi*rad/R)
        ref.append(2*maximum*np.trapezoid(value,t,axis=1))
    np.testing.assert_allclose(native.abel_basis(x,R,14,nq),np.array(ref).T,rtol=1e-13,atol=1e-14)

@pytest.mark.parametrize('mode',['matched_probe','unclipped_gaussian'])
@pytest.mark.parametrize('M',[.057,-.057])
def test_collapsed_y_is_full_tensor_quadrature(mode,M):
    cfg=DesignConfig();cfg.magnification=M;cfg.beam.reference_mode=mode
    cfg.beam.reference_center_m=(.007,-.002);cfg.port.center_m=(.003,.001)
    cfg.numerics.element_order=11;cfg.numerics.line_points=281
    g=prepare_geometry(cfg);workspace=Workspace(cfg);measured=workspace.measurement(cfg)
    nodes,w=roots_legendre(cfg.numerics.element_order)
    for j,bounds in enumerate(g.bounds_image):
        xc=(bounds[0]+bounds[1])/2;yc=(bounds[2]+bounds[3])/2
        hx=(bounds[1]-bounds[0])/2;hy=(bounds[3]-bounds[2])/2
        X,Y=np.meshgrid((xc+hx*nodes)/M,(yc+hy*nodes)/M,indexing='ij')
        area=hx*hy*w[:,None]*w[None,:]
        gp=np.exp(-2*((X-cfg.beam.center_m[0])**2+(Y-cfg.beam.center_m[1])**2)/cfg.beam.waist_m**2)
        port=(X-cfg.port.center_m[0])**2+(Y-cfg.port.center_m[1])**2<=(cfg.port.diameter_m/2)**2
        probe=gp*port
        ref=probe if mode=='matched_probe' else np.exp(-2*((X-cfg.beam.reference_center_m[0])**2+(Y-cfg.beam.reference_center_m[1])**2)/cfg.beam.reference_waist_m**2)
        cross=area*np.sqrt(probe*ref)
        h=trap_reference(X.ravel(),cfg.plasma,cfg.numerics.line_points).reshape(X.shape)
        normalized=(cross*np.exp(-1j*native.ELECTRON_RADIUS_M*cfg.heterodyne.wavelength_m*h)).sum()/cross.sum()
        np.testing.assert_allclose(measured['normalized_phasor'][j],normalized,rtol=1e-13,atol=2e-15)
        np.testing.assert_allclose(g.effective_x[j],(cross*X).sum()/cross.sum(),atol=2e-16)


def test_zero_density_small_phase_and_principal_wrap():
    cfg=DesignConfig();w=Workspace(cfg)
    cfg.plasma.peak_density_m3=0
    m=w.measurement(cfg)
    np.testing.assert_allclose(m['phase_rad'],0,atol=0)
    np.testing.assert_allclose(m['coherence'],1,atol=1e-15)
    cfg.plasma.peak_density_m3=1e15;m=w.measurement(cfg)
    np.testing.assert_allclose(m['line_density_m2'],m['linearized_line_density_m2'],rtol=2e-13)
    cfg.plasma.peak_density_m3=2e22;m=w.measurement(cfg)
    assert (np.abs(m['phase_rad'])<=np.pi).all()


def test_power_noise_scaling_and_safety_on_unselected_elements():
    cfg=DesignConfig();g=prepare_geometry(cfg);w=Workspace(cfg);m=w.measurement(cfg)
    n=detector_noise(cfg,g,m);cfg.detector.include_shot_noise=False;n0=detector_noise(cfg,g,m)
    np.testing.assert_allclose(n0['sigma_i_A'],2/np.pi*.95*2e-14*np.sqrt(1e6))
    np.testing.assert_allclose(n['sigma_phase_rad'],n['sigma_i_A']/np.abs(n['carrier_A']))
    np.testing.assert_allclose(n['if_carrier_A'],np.pi/np.sqrt(2)*n['carrier_A'])
    assert np.all(n['sigma_i_A']>=n0['sigma_i_A'])
    np.testing.assert_allclose(n['peak_power_W'],2*n['combined_power_W'],rtol=1e-14)
    limit=power_limit(cfg,g);cfg.sensor.active_elements=(1,3,5,7,11)
    limited=power_limit(cfg,prepare_geometry(cfg))
    assert limited['maximum_total_power_W']==limit['maximum_total_power_W']
    assert np.isclose(detector_specs(cfg)['allowed_linearity_power_W'],.0062)
    cfg.detector.reverse_bias_V=0
    assert np.isclose(detector_specs(cfg)['allowed_linearity_power_W'],.0012)


def test_workspace_invalidation_and_sensor_models():
    cfg=DesignConfig();w=Workspace(cfg);cfg.magnification=.06
    with pytest.raises(ValueError,match='Workspace geometry'):w.check(cfg)
    for model,count in [('G12430-016D',16),('G12430-032D',32),('G12430-046D',46)]:
        cfg.sensor.model=model;assert len(prepare_geometry(cfg).active)==count
    cfg.sensor.model='custom';cfg.sensor.elements=19
    assert len(prepare_geometry(cfg).active)==19
    cfg.sensor.pitch_m=cfg.sensor.width_m/2
    with pytest.raises(ValueError):prepare_geometry(cfg)

@pytest.mark.parametrize('points',[1,10.5,True,-3])
def test_invalid_native_quadrature_rejected(points):
    with pytest.raises(ValueError):native.abel_density([0],DesignConfig().plasma,points)


def test_native_nonfinite_and_invalid_shape_rejected():
    with pytest.raises(ValueError):native.abel_basis([0],.1,-1,10)
    with pytest.raises(ValueError):native.abel_density([np.nan],DesignConfig().plasma,10)
    with pytest.raises(ValueError):native.phasor([[1]],[[1]],float('inf'))
    cfg=DesignConfig();cfg.detector.minimum_line_density_SNR=1e10
    from heterodyne_density_lab.reconstruction import simulate
    with pytest.raises(ValueError,match='No inversion channels'):simulate(cfg)


def test_unilluminated_detector_phase_is_undefined():
    cfg=DesignConfig();cfg.port.diameter_m=.04;w=Workspace(cfg);m=w.measurement(cfg)
    absent=w.geometry.vacuum_overlap==0
    assert absent.any()
    assert np.isnan(m['phase_rad'][absent]).all()
    assert np.isnan(m['linearized_line_density_m2'][absent]).all()
    assert np.isnan(m['coherence'][absent]).all()
    np.testing.assert_array_equal(m['vacuum_cross_phasor_raw'][absent],0)
