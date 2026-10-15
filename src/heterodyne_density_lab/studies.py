"""Global joint tuning and fixed-estimator studies, without repeated physics."""
import numpy as np
import warnings
from .configuration import apply_design
from .model import Workspace, power_limit
from .reconstruction import make_measurements, reconstruct
from .metrics import metric_values, summary


def tune(base,design,optimization,workspace=None):
    cfg=apply_design(base,design)
    cfg.noise.model='detector_limited';cfg.noise.realizations=optimization.realizations
    cfg.heterodyne.total_power_W=optimization.nominal_power_W
    orders=np.asarray(sorted(set(optimization.upper_orders)))
    alphas=np.asarray(sorted(set(optimization.alphas)),dtype=float)
    profiles=np.asarray(optimization.training_scales,dtype=float)
    if orders.size==0 or not np.equal(orders,np.floor(orders)).all() or (orders<cfg.inversion.lower_order).any():raise ValueError('Invalid tuning orders')
    if alphas.size==0 or not np.isfinite(alphas).all() or ((alphas<0)|(alphas>1)).any():raise ValueError('Invalid tuning alpha values')
    if profiles.size==0 or not np.isfinite(profiles).all() or (profiles<=0).any():raise ValueError('Training scales must be positive')
    cfg.inversion.upper_order=int(orders.max())
    workspace=Workspace(cfg) if workspace is None else workspace
    workspace.basis_matrix(cfg,int(orders.max()))
    sums=np.zeros((len(orders),len(alphas)));sumsq=sums.copy();used=sums.copy();reduced=np.zeros(sums.shape,bool)
    profile_score=np.empty((len(profiles),*sums.shape))
    total=0
    for k,scale in enumerate(profiles):
        cfg.plasma.scale_length_m=float(scale*cfg.plasma.radius_m);cfg.noise.seed=optimization.seed+k+1
        e=make_measurements(cfg,workspace)
        for a,alpha in enumerate(alphas):
            for q,order in enumerate(orders):
                r=reconstruct(e,int(order),float(alpha),retain_profiles=False,compute_scale=(optimization.metric=='scale_length_full'))
                v=metric_values(optimization.metric,r)
                sums[q,a]+=v.sum();sumsq[q,a]+=np.sum(v*v);profile_score[k,q,a]=v.mean()
                used[q,a]=r['used_upper_order'];reduced[q,a]|=r['rank_reduced']
        total+=len(e['h'])
    score=sums/total
    std=np.sqrt(np.maximum((sumsq-total*score**2)/max(1,total-1),0))
    # MATLAB tie order is column-major: lower alpha first, then lower order.
    flat=int(np.argmin(score.ravel(order='F')));q,a=np.unravel_index(flat,score.shape,order='F')
    if q==len(orders)-1:warnings.warn(f'Tuning optimum for {design.name} is on upper order boundary',RuntimeWarning,stacklevel=2)
    return dict(design_name=design.name,upper_order=int(orders[q]),used_upper_order=int(used[q,a]),alpha=float(alphas[a]),
        metric=optimization.metric,score=float(score[q,a]),std=float(std[q,a]),upper_orders=orders,alphas=alphas,
        training_scales=profiles,score_surface=score,std_surface=std,profile_score=profile_score,
        used_order_surface=used,rank_reduced_surface=reduced,nominal_power_W=optimization.nominal_power_W,
        maximum_total_power_W=power_limit(cfg,workspace.geometry)['maximum_total_power_W'])


def run_scale_length(base,design,study,tuning,workspace):
    cfg=apply_design(base,design);cfg.noise.model='detector_limited'
    cfg.noise.realizations=study.scale_realizations;cfg.heterodyne.total_power_W=study.optimization.nominal_power_W
    rows=[]
    for k,scale in enumerate(study.scale_lengths):
        cfg.plasma.scale_length_m=float(scale*cfg.plasma.radius_m);cfg.noise.seed=3000+100*(study.designs.index(design)+1)+k+1
        r=reconstruct(make_measurements(cfg,workspace),tuning['upper_order'],tuning['alpha'],retain_profiles=False)
        s=r['error_summary']
        rows.append(dict(Design=design.name,Sensor=design.sensor_model,LnOverR=scale,SelectedChannels=len(np.flatnonzero(workspace.geometry.active)),
            Nupper=tuning['upper_order'],UsedNupper=r['used_upper_order'],Alpha=tuning['alpha'],SplineRMS=s['spline_full']['mean'],
            SplineRMSStd=s['spline_full']['std'],ScaleLengthRMS=s['scale_length_full']['mean'],ScaleLengthRMSStd=s['scale_length_full']['std'],
            WeightedConditionNumber=r['weighted_condition_number']))
    return rows


def run_power(base,design,study,tuning,workspace):
    cfg=apply_design(base,design);cfg.noise.model='detector_limited';cfg.noise.realizations=study.power_realizations
    points=1+int(round((study.power_log10_max-study.power_log10_min)*study.power_points_per_decade))
    if points<2:raise ValueError('Power sweep requires at least two logarithmic points')
    powers=np.logspace(study.power_log10_min,study.power_log10_max,points)
    maximum=power_limit(cfg,workspace.geometry)['maximum_total_power_W'];rows=[]
    for ip,power in enumerate(powers):
        admissible=(not cfg.detector.enforce_linearity) or power<=maximum*(1+20*np.finfo(float).eps)
        cfg.heterodyne.total_power_W=float(power)
        for k,scale in enumerate(study.power_profiles):
            row=dict(Design=design.name,LnOverR=scale,Power_W=power,ValidLinear=bool(power<=maximum*(1+20*np.finfo(float).eps)),
                Reconstructed=admissible,Nupper=tuning['upper_order'],Alpha=tuning['alpha'],SplineRMS=np.nan,SplineRMSStd=np.nan,
                MedianCarrierSNR=np.nan,PeakLinearityRatio=power/maximum)
            if admissible:
                cfg.plasma.scale_length_m=float(scale*cfg.plasma.radius_m);cfg.noise.seed=5000+1000*(study.designs.index(design)+1)+100*(ip+1)+k+1
                e=make_measurements(cfg,workspace)
                r=reconstruct(e,tuning['upper_order'],tuning['alpha'],retain_profiles=False,compute_scale=False)
                s=r['error_summary']['spline_full'];row.update(SplineRMS=s['mean'],SplineRMSStd=s['std'],MedianCarrierSNR=float(np.median(e['noise']['carrier_SNR'][e['indices']])))
            rows.append(row)
    return rows


def run_noise_contribution(base,design,study,tuning,workspace):
    cfg=apply_design(base,design);cfg.heterodyne.total_power_W=study.optimization.nominal_power_W;rows=[]
    for k,scale in enumerate(study.scale_lengths):
        cfg.plasma.scale_length_m=float(scale*cfg.plasma.radius_m);values={}
        for mode in ['noiseless','detector_weighted_noiseless','detector_limited']:
            cfg.noise.model=mode;cfg.noise.realizations=study.noise_realizations if mode=='detector_limited' else 1
            cfg.noise.seed=7100+100*(study.designs.index(design)+1)+k+1
            r=reconstruct(make_measurements(cfg,workspace),tuning['upper_order'],tuning['alpha'],retain_profiles=False,compute_scale=False)
            values[mode]=r['error_summary']['spline_full']
        a,b,c=(values[mode]['mean'] for mode in ['noiseless','detector_weighted_noiseless','detector_limited'])
        rows.append(dict(Design=design.name,LnOverR=scale,Nupper=tuning['upper_order'],Alpha=tuning['alpha'],
            NoiselessRMS=a,WeightedNoiselessRMS=b,DetectorLimitedRMS=c,DetectorLimitedStd=values['detector_limited']['std'],
            WeightingChange=b-a,StochasticChange=c-b))
    return rows


def run_basis_order(base,design,study,tuning,workspace):
    cfg=apply_design(base,design);cfg.noise.model='detector_limited';cfg.noise.realizations=study.basis_realizations
    cfg.plasma.scale_length_m=study.basis_profile*cfg.plasma.radius_m
    cfg.heterodyne.total_power_W=study.optimization.nominal_power_W;cfg.noise.seed=9001
    orders=sorted(set(study.basis_orders));workspace.basis_matrix(cfg,max(orders));e=make_measurements(cfg,workspace);rows=[]
    for order in orders:
        r=reconstruct(e,order,tuning['alpha'],retain_profiles=False)
        rows.append(dict(Design=design.name,RequestedNupper=order,UsedNupper=r['used_upper_order'],
            SplineFullRMS=r['error_summary']['spline_full']['mean'],ScaleLengthFullRMS=r['error_summary']['scale_length_full']['mean'],
            WeightedConditionNumber=r['weighted_condition_number'],MatrixRank=r['matrix_rank'],RankReduced=r['rank_reduced'],Alpha=tuning['alpha'],
            SelectionMetric=study.basis_metric,SelectionMetricMean=float(np.mean(metric_values(study.basis_metric,r)))))
    return rows
