"""One measurement engine and one reconstruction engine, shared by every study."""
from functools import lru_cache
import warnings
import numpy as np
from scipy import linalg
from .configuration import DesignConfig
from .model import Workspace, detector_specs, detector_noise, power_limit, density_profile, DetectorLinearityError
from .native import ELECTRON_RADIUS_M, iq_samples
from .splines import SplineOperator
from .metrics import scale_length_errors, summary


def basis_values(r,ids,radius):
    r=np.asarray(r)[:,None];ids=np.asarray(ids)[None,:]
    values=1-(-1.0)**ids*np.cos(ids*np.pi*r/radius)
    values[:,ids[0]==0]=1
    return values

@lru_cache(maxsize=64)
def _spline_operator(x,radius,basis_count,lambda_value,candidates,clip,radial_points):
    from .configuration import Spline
    options=Spline(basis_count,lambda_value,candidates,clip)
    return SplineOperator(x,radius,options,np.linspace(0,radius,radial_points))


def make_measurements(cfg,workspace=None,normals=None):
    """Generate I/Q once, independent of the inverse model's basis/alpha.

    Returned arrays have samples first: (realizations, retained channels).
    Supply (realizations,2,channels) normal arrays for cross-language comparisons.
    """
    cfg.validate()
    workspace=Workspace(cfg) if workspace is None else workspace
    workspace.check(cfg);geom=workspace.geometry
    specs=detector_specs(cfg);lim=power_limit(cfg,geom,specs)
    if cfg.detector.enforce_linearity and cfg.heterodyne.total_power_W>lim['maximum_total_power_W']*(1+20*np.finfo(float).eps):
        raise DetectorLinearityError(f"Element {lim['critical_element']}: total power {cfg.heterodyne.total_power_W:g} W exceeds admissible {lim['maximum_total_power_W']:g} W")
    measurement=workspace.measurement(cfg)
    noise=detector_noise(cfg,geom,measurement,specs)
    included=geom.included.copy();excluded=np.zeros(len(included),dtype=bool)
    weighted=cfg.noise.model in ['detector_limited','detector_weighted_noiseless']
    if weighted and cfg.detector.minimum_line_density_SNR>0:
        excluded=included & (noise['line_density_SNR']<cfg.detector.minimum_line_density_SNR)
        included &= ~excluded
    indices=np.flatnonzero(included)
    if len(indices)==0:raise ValueError('No inversion channels remain after geometry/SNR filtering')
    true=measurement['line_density_m2'][indices]
    nmc=cfg.noise.realizations;factor=ELECTRON_RADIUS_M*cfg.heterodyne.wavelength_m
    if weighted:
        sigma=noise['sigma_h_m2'][indices]
        if not np.isfinite(sigma).all() or (sigma<=0).any():raise ValueError('Retained detector uncertainties must be finite and positive')
        if (noise['carrier_SNR'][indices]<cfg.detector.minimum_carrier_SNR).any():
            warnings.warn('Some retained channels have low carrier SNR; analytic phase weighting is approximate',RuntimeWarning,stacklevel=2)
        if noise['bandwidth_ratio']>=cfg.detector.cutoff_warning_fraction:
            warnings.warn('IF + ENBW approaches/exceeds the detector cutoff; no transfer-function correction is applied',RuntimeWarning,stacklevel=2)
    else:sigma=np.zeros(len(indices)) if cfg.noise.model=='noiseless' else np.abs(true)*cfg.noise.relative_level
    rng=np.random.Generator(np.random.PCG64(cfg.noise.seed))
    if cfg.noise.model=='detector_limited':
        normals=rng.standard_normal((nmc,2,len(indices))) if normals is None else np.asarray(normals)
        if normals.shape!=(nmc,2,len(indices)):raise ValueError('Supplied normals have incorrect ensemble shape')
        I,Q,phase,h=iq_samples(noise['carrier_A'][indices],noise['sigma_i_A'][indices],normals,factor)
    else:
        if normals is not None:raise ValueError('Externally supplied I/Q normals require detector_limited mode')
        h=np.broadcast_to(true,(nmc,len(indices))).copy()
        if cfg.noise.model=='relative':h*=1+cfg.noise.relative_level*rng.standard_normal(h.shape)
        phase=-factor*h
        if cfg.noise.model=='detector_weighted_noiseless':
            I=np.broadcast_to(noise['carrier_A'][indices].real,h.shape).copy()
            Q=np.broadcast_to(noise['carrier_A'][indices].imag,h.shape).copy()
        else:I=np.full(h.shape,np.nan);Q=I.copy()
    return dict(cfg=cfg.clone(),workspace=workspace,measurement=measurement,noise=noise,specs=specs,power_limit=lim,
        indices=indices,snr_excluded=excluded,h=h,I=I,Q=Q,phase=phase,sigma_h=sigma,weighted=weighted)


def reconstruct(ensemble,upper_order=None,alpha=None,retain_profiles=True,compute_scale=True):
    """Refit cached measured data. This function never redraws detector noise."""
    cfg=ensemble['cfg'];geom=ensemble['workspace'].geometry;indices=ensemble['indices']
    order=cfg.inversion.upper_order if upper_order is None else upper_order
    alpha=cfg.inversion.weighting_alpha if alpha is None else alpha
    if not isinstance(order,(int,np.integer)) or order<cfg.inversion.lower_order:raise ValueError('Invalid upper order')
    if not np.isfinite(alpha) or not 0<=alpha<=1:raise ValueError('alpha must lie in [0,1]')
    requested=np.r_[0 if cfg.inversion.include_constant else np.empty(0,dtype=int),np.arange(cfg.inversion.lower_order,order+1)].astype(int)
    Kfull=ensemble['workspace'].basis_matrix(cfg,order)[indices][:,requested]
    keep=len(requested)
    if keep>len(indices):
        if not cfg.inversion.enforce_rank_limit:raise ValueError('More basis coefficients than measurements')
        keep=len(indices)
    while keep and np.linalg.matrix_rank(Kfull[:,:keep])<keep:
        if not cfg.inversion.enforce_rank_limit:raise ValueError('Rank-deficient Pretzler matrix')
        keep-=1
    if keep==0:raise ValueError('Pretzler matrix has no independent leading columns')
    reduced=keep<len(requested)
    if reduced and cfg.inversion.warn_rank_reduction:
        warnings.warn(f'Requested {len(requested)} coefficients reduced to {keep} independent leading columns',RuntimeWarning,stacklevel=2)
    K=Kfull[:,:keep];ids=requested[:keep]
    row_scale=(ensemble['sigma_h']/np.median(ensemble['sigma_h']))**(-alpha) if ensemble['weighted'] else np.ones(len(indices))
    Ksolve=K*row_scale[:,None]
    condition=float(np.linalg.cond(K));wcondition=float(np.linalg.cond(Ksolve))
    if condition>cfg.inversion.condition_warning:
        warnings.warn(f'Poorly conditioned Pretzler matrix: cond={condition:.3g}',RuntimeWarning,stacklevel=2)
    # One SVD factorization for all realizations; avoids per-sample least squares.
    solver,_,rank,_=linalg.lstsq(Ksolve,np.diag(row_scale),lapack_driver='gelsd')
    if rank<keep:raise ValueError('Weighted solve is numerically rank deficient')
    radius=cfg.plasma.radius_m;r=np.linspace(0,radius,cfg.numerics.radial_points)
    truth=density_profile(r,cfg.plasma);peak=truth.max()
    x=geom.effective_x[indices];valid=np.isfinite(x)&(np.abs(x)<=radius)
    x=x[valid];rp=np.abs(x)
    if len(np.unique(np.round((rp/radius)**2,12)))<4:
        raise ValueError('Fewer than four unique reconstructed detector radii; adjust geometry or selected channels')
    F=basis_values(r,ids,radius);Fp=basis_values(rp,ids,radius)
    point_truth=density_profile(rp,cfg.plasma);sampled=r<=rp.max()
    support_x=tuple(np.r_[x,0,-radius,radius])
    support_matrix=np.vstack((Fp,F[0],F[-1],F[-1]))
    options=cfg.spline
    spline=_spline_operator(support_x,radius,options.basis_count,options.lambda_value,
        tuple(options.lambda_candidates),options.clip_nonnegative,len(r))
    h=ensemble['h'];nmc=len(h)
    errors={key:np.empty(nmc) for key in ['pretzler_points','pretzler_sampled','pretzler_full','spline_sampled','spline_full']}
    if compute_scale:errors['scale_length_full']=np.empty(nmc)
    coefficients=np.empty((nmc,keep));lambdas=np.empty(nmc)
    allp=np.empty((nmc,len(r))) if retain_profiles else None
    alls=np.empty((nmc,len(r))) if retain_profiles else None
    allpoints=np.empty((nmc,len(rp))) if retain_profiles else None
    meanp=np.zeros(len(r));means=meanp.copy();meanpoints=np.zeros(len(rp))
    firstp=firsts=firstpoints=None
    for start in range(0,nmc,cfg.noise.batch_size):
        stop=min(nmc,start+cfg.noise.batch_size);sl=slice(start,stop)
        A=h[sl]@solver.T
        npred=A@F.T;points=A@Fp.T
        smooth,lam=spline.apply(A@support_matrix.T)
        errors['pretzler_points'][sl]=np.sqrt(np.mean((points-point_truth)**2,axis=1))/peak
        errors['pretzler_sampled'][sl]=np.sqrt(np.mean((npred[:,sampled]-truth[sampled])**2,axis=1))/peak
        errors['pretzler_full'][sl]=np.sqrt(np.mean((npred-truth)**2,axis=1))/peak
        errors['spline_sampled'][sl]=np.sqrt(np.mean((smooth[:,sampled]-truth[sampled])**2,axis=1))/peak
        errors['spline_full'][sl]=np.sqrt(np.mean((smooth-truth)**2,axis=1))/peak
        if compute_scale:errors['scale_length_full'][sl]=scale_length_errors(r,truth,smooth)
        coefficients[sl]=A;lambdas[sl]=lam
        meanp+=npred.sum(axis=0);means+=smooth.sum(axis=0);meanpoints+=points.sum(axis=0)
        if start==0:firstp=npred[0].copy();firsts=smooth[0].copy();firstpoints=points[0].copy()
        if retain_profiles:allp[sl]=npred;alls[sl]=smooth;allpoints[sl]=points
    result=dict(ensemble=ensemble,K=K,K_solve=Ksolve,basis_ids=ids,requested_basis_ids=requested,
        requested_upper_order=int(order),used_upper_order=int(ids.max()),rank_reduced=reduced,matrix_rank=keep,
        weighting_alpha=float(alpha),condition_number=condition,weighted_condition_number=wcondition,
        coefficients=coefficients,spline_lambdas=lambdas,r=r,truth=truth,x_points=x,r_points=rp,
        sampled_mask=sampled,r_sampled_max=float(rp.max()),pretzler_mean=meanp/nmc,spline_mean=means/nmc,
        points_mean=meanpoints/nmc,pretzler_first=firstp,spline_first=firsts,points_first=firstpoints,
        pretzler_profiles=allp,spline_profiles=alls,point_profiles=allpoints)
    result.update({'error_'+key:value for key,value in errors.items()})
    result['error_summary']={key:summary(value) for key,value in errors.items()}
    return result


def simulate(cfg,workspace=None,normals=None,retain_profiles=True):
    return reconstruct(make_measurements(cfg,workspace,normals),retain_profiles=retain_profiles)


def measurement_rows(result):
    e=result['ensemble'];cfg=e['cfg'];g=e['workspace'].geometry;m=e['measurement'];n=e['noise'];lim=e['power_limit']
    indices=e['indices'];first={int(i):k for k,i in enumerate(indices)}
    rows=[]
    for j in range(len(g.active)):
        k=first.get(j)
        row=dict(Element=j+1,Selected=bool(g.active[j]),PassedGeometryCriteria=bool(g.included[j]),
            ExcludedBySNR=bool(e['snr_excluded'][j]),UsedInInversion=(k is not None),
            CenterXImage_m=g.centers_image[j,0],CenterXObject_m=g.centers_image[j,0]/cfg.magnification,
            EffectiveXObject_m=g.effective_x[j],PortTransmissionFraction=g.transmission[j],
            GeometricIlluminationFraction=g.illumination[j],RelativeProbePower=g.relative_probe_power[j],
            ProbePowerFraction=g.probe_fraction[j],ReferencePowerFraction=g.reference_fraction[j],VacuumOverlapFraction=g.vacuum_overlap[j],
            CombinedElementPower_W=n['combined_power_W'][j],ProbePower_W=n['probe_power_W'][j],ReferencePower_W=n['reference_power_W'][j],
            PeakInterferencePower_W=n['peak_power_W'][j],LinearityLimit_W=lim['element_limit_W'],
            EstimatedRelativeSensitivity=n['estimated_relative_sensitivity'][j],LinearityMargin_W=n['linearity_margin_W'][j],
            DetectorLinear=bool(n['detector_linear'][j]),PhotocurrentDC_A=n['photocurrent_dc_A'][j],
            IFCarrierCurrentPeak_A=abs(n['if_carrier_A'][j]),BasebandCarrierCurrentPeak_A=abs(n['carrier_A'][j]),
            BasebandDetectorNoiseASD_A_per_sqrtHz=n['detector_asd'][j],BasebandShotNoiseASD_A_per_sqrtHz=n['shot_asd'][j],
            BasebandTotalNoiseASD_A_per_sqrtHz=n['total_asd'][j],PhaseNoiseStd_rad=n['sigma_phase_rad'][j],
            LineDensityNoiseStd_m2=n['sigma_h_m2'][j],HeterodyneCarrierSNR=n['carrier_SNR'][j],LineDensitySNR=n['line_density_SNR'][j],
            ShotNoiseVarianceFraction=n['shot_variance_fraction'][j],PhaseNoiseApproximationValid=bool(n['phase_model_valid'][j]),
            PhaseTrue_rad=m['phase_rad'][j],PhaseNoisyFirst_rad=e['phase'][0,k] if k is not None else np.nan,
            IFirst_A=e['I'][0,k] if k is not None else np.nan,QFirst_A=e['Q'][0,k] if k is not None else np.nan,
            HeterodyneCoherence=m['coherence'][j],LineDensityLinearized_m2=m['linearized_line_density_m2'][j],
            LineDensityPhaseNonlinearity_m2=m['linearity_difference_m2'][j],LineDensityTrue_m2=m['line_density_m2'][j],
            LineDensityNoisyFirst_m2=e['h'][0,k] if k is not None else np.nan)
        rows.append(row)
    return rows
