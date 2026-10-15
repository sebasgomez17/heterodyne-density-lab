"""Peak-normalized density errors and bounded local scale-length errors."""
import numpy as np

def scale_length(r,profiles):
    profiles=np.atleast_2d(profiles)
    gradient=np.gradient(profiles,np.asarray(r),axis=1)
    maximum=np.max(np.abs(gradient),axis=1,keepdims=True)
    tolerance=1e-12*maximum
    with np.errstate(divide='ignore',invalid='ignore'):
        length=np.abs(profiles)/np.abs(gradient)
    length[np.abs(gradient)<=tolerance.repeat(profiles.shape[1],axis=1)]=np.inf
    return length

def scale_length_errors(r,truth,reconstructed):
    true=scale_length(r,truth)[0]
    rec=scale_length(r,reconstructed)
    finite=np.isfinite(rec)&np.isfinite(true)[None,:]
    with np.errstate(invalid='ignore',divide='ignore'):
        den=rec+true
        error=np.where(finite & (den>0),np.abs(rec-true)/den,1.0)
    error[finite & (den==0)]=0.0
    error[np.isinf(rec)&np.isinf(true)[None,:]]=0.0
    return np.sqrt(np.mean(error[:,np.asarray(r)>0]**2,axis=1))

METRIC_KEYS={'pretzler_points':'error_pretzler_points','pretzler_sampled':'error_pretzler_sampled',
    'pretzler_full':'error_pretzler_full','spline_sampled':'error_spline_sampled',
    'spline_full':'error_spline_full','scale_length_full':'error_scale_length_full'}

def metric_values(name,result):
    if name not in METRIC_KEYS:raise ValueError(f'Unknown metric {name}; choose from {tuple(METRIC_KEYS)}')
    return result[METRIC_KEYS[name]]

def summary(values):
    values=np.asarray(values)
    return {'mean':float(np.mean(values)),'std':float(np.std(values,ddof=1)) if values.size>1 else 0.0,
        'median':float(np.median(values)),'p05':float(np.percentile(values,5)),'p95':float(np.percentile(values,95))}
