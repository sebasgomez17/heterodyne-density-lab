"""Validate reconstruction, smoothing, randomness, and fixed-estimator studies."""
import warnings
import numpy as np
import pytest
from threadpoolctl import threadpool_limits
from scipy.interpolate import BSpline
from heterodyne_density_lab.configuration import DesignConfig,StudyConfig,default_designs,apply_design
from heterodyne_density_lab.model import Workspace,DetectorLinearityError
from heterodyne_density_lab.reconstruction import simulate,make_measurements,reconstruct,basis_values
from heterodyne_density_lab.splines import SplineOperator
from heterodyne_density_lab.metrics import scale_length_errors
from heterodyne_density_lab.studies import tune,run_scale_length,run_power,run_noise_contribution,run_basis_order

@pytest.fixture(autouse=True)
def single_thread():
    with threadpool_limits(limits=1):yield


def test_cached_spline_matches_independent_single_sample_algorithm():
    cfg=DesignConfig();x=np.array([-.09,-.07,-.04,-.02,.02,.04,.07,.09,0,-.1,.1]);r=np.linspace(0,.1,101)
    op=SplineOperator(x,.1,cfg.spline,r)
    rng=np.random.default_rng(5);y=rng.normal(size=(5,len(x)))*1e19
    actual,lam=op.apply(y)
    u,group=np.unique(np.round((np.abs(x)/.1)**2,12),return_inverse=True)
    count=np.bincount(group);n=max(4,min(10,len(u)));knots=np.r_[np.zeros(4),np.arange(1,n-3)/(n-3),np.ones(4)]
    B=BSpline.design_matrix(u,knots,3).toarray();Bw=B*np.sqrt(count[:,None]);normal=Bw.T@Bw
    penalty=np.diff(np.eye(n),n=2,axis=0);penalty=penalty.T@penalty
    evalB=BSpline.design_matrix((r/.1)**2,knots,3).toarray()
    for m in range(len(y)):
        average=np.bincount(group,weights=y[m])/count;weighted=average*np.sqrt(count);scale=np.max(np.abs(weighted))
        ys=weighted/scale;score=[];coeff=[]
        for penalty_value in cfg.spline.lambda_candidates:
            A=normal+penalty_value*penalty+1e-12*np.eye(n)
            solution=np.linalg.solve(A,Bw.T@ys);dof=np.trace(np.linalg.solve(A,normal))
            score.append(np.mean((Bw@solution-ys)**2)/max(1-dof/len(u),np.sqrt(np.finfo(float).eps))**2);coeff.append(solution)
        best=int(np.argmin(score))
        assert lam[m]==cfg.spline.lambda_candidates[best]
        np.testing.assert_allclose(actual[m],evalB@coeff[best]*scale,rtol=5e-9,atol=1e10)


def test_reuse_batch_invariance_and_weighted_solve():
    cfg=DesignConfig();cfg.noise.realizations=47;cfg.spline.lambda_value=.01
    e=make_measurements(cfg);r=reconstruct(e)
    direct=np.linalg.lstsq(r['K_solve'],(e['h']*(e['sigma_h']/np.median(e['sigma_h']))**-1).T,rcond=None)[0].T
    np.testing.assert_allclose(r['coefficients'],direct,rtol=1e-11,atol=1e8)
    e['cfg'].noise.batch_size=7;rb=reconstruct(e)
    np.testing.assert_allclose(r['spline_profiles'],rb['spline_profiles'],rtol=1e-13,atol=1e6)
    np.testing.assert_allclose(r['error_scale_length_full'],rb['error_scale_length_full'],rtol=1e-10,atol=1e-12)
    low=reconstruct(e,2,.5);assert e['h'].shape==(47,16);assert low['coefficients'].shape==(47,3)
    same=make_measurements(cfg)
    np.testing.assert_array_equal(e['h'],same['h'])
    rmetrics=reconstruct(e,retain_profiles=False)
    np.testing.assert_allclose(rmetrics['error_spline_full'],rb['error_spline_full'])
    assert rmetrics['spline_profiles'] is None


def test_iq_normal_shape_and_statistics():
    from heterodyne_density_lab.native import iq_samples
    carrier=np.array([2.+1j]);sigma=np.array([.1]);normals=np.random.default_rng(10).normal(size=(100000,2,1))
    I,Q,phi,h=iq_samples(carrier,sigma,normals,1.)
    assert abs(I.mean()-2)<.001;assert abs(Q.mean()-1)<.001
    assert abs(I.std()-.1)<.001;assert abs(Q.std()-.1)<.001
    np.testing.assert_allclose(phi,np.arctan2(Q,I));np.testing.assert_array_equal(h,-phi)
    with pytest.raises(ValueError):iq_samples(carrier,sigma,np.zeros((3,1)),1.)

@pytest.mark.parametrize('mode',['noiseless','detector_weighted_noiseless','relative','detector_limited'])
def test_all_noise_modes_and_metrics(mode):
    cfg=DesignConfig();cfg.noise.model=mode;cfg.noise.realizations=5
    result=simulate(cfg)
    assert np.isfinite(result['spline_profiles']).all()
    assert np.all((result['error_scale_length_full']>=0)&(result['error_scale_length_full']<=1))
    if mode in ['noiseless','detector_weighted_noiseless']:
        np.testing.assert_array_equal(result['spline_profiles'][0],result['spline_profiles'][1])


def test_linearity_rejection_rank_guard_and_all_layouts():
    cfg=DesignConfig();cfg.heterodyne.total_power_W=.1
    with pytest.raises(DetectorLinearityError):simulate(cfg)
    cfg.heterodyne.total_power_W=.05;cfg.noise.model='noiseless';cfg.inversion.upper_order=12
    with warnings.catch_warnings():
        warnings.simplefilter('ignore');r=simulate(cfg)
    assert r['rank_reduced'];assert r['matrix_rank']<=8
    cfg.inversion.enforce_rank_limit=False
    with pytest.raises(ValueError,match='Rank-deficient'):simulate(cfg)
    cfg=DesignConfig();cfg.noise.model='noiseless'
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        for design in default_designs():assert np.isfinite(simulate(apply_design(cfg,design))['spline_mean']).all()


def test_scale_metric_infinite_and_zero_conventions():
    r=np.linspace(0,1,101);truth=np.ones(101)
    np.testing.assert_allclose(scale_length_errors(r,truth,truth),0)
    np.testing.assert_allclose(scale_length_errors(r,truth,np.exp(-r)),1)


def test_global_tuning_and_four_studies_smoke():
    cfg=DesignConfig();cfg.numerics.radial_points=151
    study=StudyConfig();study.designs=study.designs[:1];design=study.designs[0]
    opt=study.optimization;opt.realizations=3;opt.upper_orders=(2,3);opt.alphas=(0,.5,1);opt.training_scales=(.1,.2)
    study.scale_lengths=(.1,.2);study.scale_realizations=3;study.power_profiles=(.2,);study.power_points_per_decade=1
    study.noise_realizations=3;study.basis_realizations=3;study.basis_orders=(2,3,4)
    w=Workspace(apply_design(cfg,design))
    with warnings.catch_warnings():
        warnings.simplefilter('ignore');t=tune(cfg,design,opt,w)
    surface=t['score_surface'];assert t['score']==surface.min()
    assert len(run_scale_length(cfg,design,study,t,w))==2
    power=run_power(cfg,design,study,t,w);assert not power[-1]['ValidLinear'];assert np.isnan(power[-1]['SplineRMS'])
    noise=run_noise_contribution(cfg,design,study,t,w);assert len(noise)==2
    assert np.isclose(noise[0]['WeightingChange'],noise[0]['WeightedNoiselessRMS']-noise[0]['NoiselessRMS'])
    basis=run_basis_order(cfg,design,study,t,w);assert len(basis)==3

@pytest.mark.parametrize('model',['G12430-032D','G12430-046D','custom'])
def test_full_reconstruction_other_detector_models(model):
    cfg=DesignConfig();cfg.sensor.model=model;cfg.noise.model='noiseless'
    if model=='custom':
        cfg.detector.custom=dict(responsivity_A_per_W=.95,nep_W_per_sqrtHz=2e-14,cutoff_frequency_Hz=30e6,linearity_limit_W=.02)
    r=simulate(cfg)
    assert np.isfinite(r['spline_mean']).all()
    assert len(r['ensemble']['indices'])>=8
