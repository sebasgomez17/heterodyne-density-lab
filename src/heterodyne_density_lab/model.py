"""Finite-area optics and detector physics; geometry and Abel integrals are reused."""
from dataclasses import dataclass
from collections import OrderedDict
import warnings
import numpy as np
from scipy.special import roots_legendre
from . import native

class DetectorLinearityError(ValueError):
    """Requested optical power exceeds the configured typical-linearity boundary."""

@dataclass
class Geometry:
    model: str
    centers_image: np.ndarray
    bounds_image: np.ndarray
    active: np.ndarray
    included: np.ndarray
    x_nodes: np.ndarray
    cross_weights: np.ndarray
    effective_x: np.ndarray
    effective_y: np.ndarray
    probe_fraction: np.ndarray
    reference_fraction: np.ndarray
    vacuum_overlap: np.ndarray
    transmission: np.ndarray
    illumination: np.ndarray
    relative_probe_power: np.ndarray
    probe_integral: float
    reference_integral: float
    port_transmission: float


def density_profile(r, plasma):
    r=np.asarray(r,dtype=float)
    if not np.isfinite(r).all() or (r<0).any(): raise ValueError('Radial positions must be finite and nonnegative')
    inside=(r<=plasma.radius_m)
    values=(plasma.peak_density_m3-plasma.background_density_m3)*np.exp(
        -(r/plasma.scale_length_m)**plasma.exponent/plasma.exponent)+plasma.background_density_m3
    return np.where(inside,values,0.0)


def _geometry_signature(cfg):
    from dataclasses import asdict
    return repr((asdict(cfg.sensor),asdict(cfg.beam),asdict(cfg.port),cfg.magnification,cfg.numerics.element_order))


def prepare_geometry(cfg):
    cfg.validate()
    sensor=cfg.sensor
    dimensions={'G12430-016D':(16,.45e-3,1e-3,.50e-3),
        'G12430-032D':(32,.20e-3,1e-3,.25e-3),'G12430-046D':(46,.20e-3,1e-3,.25e-3)}
    model=sensor.model.upper()
    if model=='CUSTOM':
        ne,width,height,pitch=sensor.elements,sensor.width_m,sensor.height_m,sensor.pitch_m
    elif model in dimensions: ne,width,height,pitch=dimensions[model]
    else: raise ValueError(f'Unsupported sensor model {sensor.model}')
    if not isinstance(ne,int) or ne<1 or not all(np.isfinite([width,height,pitch])) or min(width,height,pitch)<=0 or pitch<width:
        raise ValueError('Invalid sensor dimensions/pitch')
    centers=np.column_stack((sensor.center_image_m[0]+(np.arange(ne)-(ne-1)/2)*pitch,np.full(ne,sensor.center_image_m[1])))
    bounds=np.column_stack((centers[:,0]-width/2,centers[:,0]+width/2,centers[:,1]-height/2,centers[:,1]+height/2))
    active=np.zeros(ne,dtype=bool)
    selected=sensor.active_elements
    if isinstance(selected,str):
        if selected.lower()!='all': raise ValueError('active_elements must be all, IDs, or a boolean mask')
        active[:]=True
    else:
        selected=np.asarray(selected)
        if selected.dtype==bool:
            if selected.shape!=(ne,): raise ValueError('Active mask length differs from physical element count')
            active=selected.copy()
        else:
            if selected.ndim!=1 or not np.isfinite(selected).all() or (selected!=np.rint(selected)).any() or ((selected<1)|(selected>ne)).any():
                raise ValueError('Active detector IDs must be integers 1..N')
            active[selected.astype(int)-1]=True
    q=cfg.numerics.element_order
    nodes,weights=roots_legendre(q)
    xi=centers[:,0,None]+width/2*nodes
    yi=centers[:,1,None]+height/2*nodes
    xo=xi/cfg.magnification; yo=yi/cfg.magnification
    X=xo[:,:,None];Y=yo[:,None,:]
    area=width*height/4*weights[:,None]*weights[None,:]
    gp=np.exp(-2*((X-cfg.beam.center_m[0])**2+(Y-cfg.beam.center_m[1])**2)/cfg.beam.waist_m**2)
    mask=(X-cfg.port.center_m[0])**2+(Y-cfg.port.center_m[1])**2 <= (cfg.port.diameter_m/2)**2
    probe=gp*mask
    reference=probe if cfg.beam.reference_mode=='matched_probe' else np.exp(-2*((X-cfg.beam.reference_center_m[0])**2+
        (Y-cfg.beam.reference_center_m[1])**2)/cfg.beam.reference_waist_m**2)
    cross=area*np.sqrt(probe*reference)
    pa=(area*probe).sum(axis=(1,2));ra=(area*reference).sum(axis=(1,2));ca=cross.sum(axis=(1,2))
    unblocked=(area*gp).sum(axis=(1,2))
    transmission=np.divide(pa,unblocked,out=np.zeros(ne),where=unblocked>0)
    illumination=(area*mask).sum(axis=(1,2))/(width*height)
    # Collapse y exactly on the tensor-product quadrature; phase and basis depend only on x.
    marginal=cross.sum(axis=2)
    normalized=np.divide(marginal,ca[:,None],out=np.zeros_like(marginal),where=ca[:,None]>0)
    xeff=np.where(ca>0,(normalized*xo).sum(axis=1),np.nan)
    yeff=np.divide((cross*Y).sum(axis=(1,2)),ca,out=np.full(ne,np.nan),where=ca>0)
    radius=cfg.port.diameter_m/2
    if tuple(cfg.beam.center_m)==tuple(cfg.port.center_m):
        probe_object=np.pi*cfg.beam.waist_m**2/2*(-np.expm1(-2*radius**2/cfg.beam.waist_m**2))
    else:
        rn,rw=roots_legendre(max(80,4*q));r=radius*(rn+1)/2;theta=2*np.pi*np.arange(max(256,8*q))/max(256,8*q)
        xx=cfg.port.center_m[0]+r[:,None]*np.cos(theta);yy=cfg.port.center_m[1]+r[:,None]*np.sin(theta)
        shape=np.exp(-2*((xx-cfg.beam.center_m[0])**2+(yy-cfg.beam.center_m[1])**2)/cfg.beam.waist_m**2)
        probe_object=np.sum(radius/2*rw*r*shape.mean(axis=1)*2*np.pi)
    reference_object=probe_object if cfg.beam.reference_mode=='matched_probe' else np.pi*cfg.beam.reference_waist_m**2/2
    pi=cfg.magnification**2*probe_object;ri=cfg.magnification**2*reference_object
    if min(pi,ri)<=0 or not np.isfinite([pi,ri]).all(): raise ValueError('Zero or invalid integrated beam power')
    relative=np.divide(pa,pa.max(),out=np.zeros(ne),where=pa.max()>0)
    included=active & (transmission>=sensor.minimum_illumination_fraction) & (ca>pa.max()*1e-14)
    if not included.any(): raise ValueError('No detector elements satisfy geometry selection')
    return Geometry(model,centers,bounds,active,included,xo,normalized,xeff,yeff,pa/pi,ra/ri,ca/np.sqrt(pi*ri),
        transmission,illumination,relative,pi,ri,probe_object/(np.pi*cfg.beam.waist_m**2/2))

class Workspace:
    """Bounded in-memory caches scoped to one physical geometry (no stale disk optics)."""
    def __init__(self,cfg):
        self.geometry=prepare_geometry(cfg)
        self.signature=_geometry_signature(cfg)
        self._basis={}
        self._profiles=OrderedDict()
        self.x_unique,self.x_inverse=np.unique(np.abs(self.geometry.x_nodes),return_inverse=True)

    def check(self,cfg):
        if _geometry_signature(cfg)!=self.signature: raise ValueError('Workspace geometry differs from configuration; create a new Workspace')

    def basis_matrix(self,cfg,max_order):
        self.check(cfg)
        key=(cfg.plasma.radius_m,cfg.inversion.quadrature_points)
        bank=self._basis.get(key)
        if bank is None or bank.shape[1]<=max_order:
            values=native.abel_basis(self.x_unique,cfg.plasma.radius_m,max_order,cfg.inversion.quadrature_points)
            expanded=values[self.x_inverse].reshape(self.geometry.x_nodes.shape+(max_order+1,))
            bank=np.einsum('jq,jqb->jb',self.geometry.cross_weights,expanded)
            self._basis[key]=bank
            if len(self._basis)>4: self._basis.pop(next(iter(self._basis)))
        return bank[:,:max_order+1]

    def measurement(self,cfg):
        self.check(cfg)
        p=cfg.plasma
        key=(p.radius_m,p.peak_density_m3,p.background_density_m3,p.scale_length_m,p.exponent,
            cfg.numerics.line_points,cfg.heterodyne.wavelength_m)
        if key in self._profiles:
            self._profiles.move_to_end(key)
            return self._profiles[key]
        h=native.abel_density(self.x_unique,p,cfg.numerics.line_points)[self.x_inverse].reshape(self.geometry.x_nodes.shape)
        factor=native.ELECTRON_RADIUS_M*cfg.heterodyne.wavelength_m
        normalized,linear=native.phasor(h,self.geometry.cross_weights,factor)
        phase=np.angle(normalized);absent=self.geometry.vacuum_overlap<=0
        phase[absent]=np.nan;linear[absent]=np.nan
        coherence=np.abs(normalized);coherence[absent]=np.nan
        overlap=self.geometry.vacuum_overlap*normalized
        vacuum_raw=self.geometry.vacuum_overlap*np.sqrt(self.geometry.probe_integral*self.geometry.reference_integral)
        out={'phase_rad':phase,'line_density_m2':-phase/factor,'linearized_line_density_m2':linear,
            'linearity_difference_m2':-phase/factor-linear,'coherence':coherence,
            'plasma_overlap_fraction':overlap,'normalized_phasor':normalized,
            'vacuum_cross_phasor_raw':vacuum_raw,'plasma_cross_phasor_raw':vacuum_raw*normalized}
        self._profiles[key]=out
        if len(self._profiles)>16:self._profiles.popitem(last=False)
        return out


def detector_specs(cfg):
    model=cfg.sensor.model.upper();d=cfg.detector
    if d.specification_case not in ['typical','conservative']:raise ValueError('Unknown detector specification case')
    if model=='CUSTOM':
        out=dict(d.custom)
        for name in ['responsivity_A_per_W','nep_W_per_sqrtHz','cutoff_frequency_Hz']:
            if name not in out or not np.isfinite(out[name]) or out[name]<=0: raise ValueError(f'Custom detector needs positive {name}')
        for name in ['dark_current_A','terminal_capacitance_F','shunt_resistance_Ohm']:out.setdefault(name,float('nan'))
        limit=out.get('linearity_limit_W',float('inf'))
        if not (limit>0):raise ValueError('Custom linearity limit must be positive if supplied')
        out.update(allowed_linearity_power_W=limit,linearity_curve_power_W=np.array([]),linearity_curve_relative_sensitivity=np.array([]))
    else:
        if model not in ['G12430-016D','G12430-032D','G12430-046D']:raise ValueError('Unsupported detector model')
        if model=='G12430-016D':
            values=(.95,2e-14,30e6,500e-12,60e-12,100e6) if d.specification_case=='typical' else (.85,4e-14,15e6,2500e-12,100e-12,20e6)
        else:
            values=(.95,1e-14,60e6,250e-12,35e-12,200e6) if d.specification_case=='typical' else (.85,3e-14,25e6,1250e-12,60e-12,40e6)
        out=dict(zip(['responsivity_A_per_W','nep_W_per_sqrtHz','cutoff_frequency_Hz','dark_current_A','terminal_capacitance_F','shunt_resistance_Ohm'],values))
        if d.reverse_bias_V not in [0,1]:raise ValueError('Built-in linearity curves exist only for 0 or 1 V bias')
        if model=='G12430-016D' and d.reverse_bias_V==1:
            powers=[0,2,4,5,5.5,6,6.2,6.4,6.6,6.8,7,7.2,7.4];response=[1,1,1,.999,.998,.994,.990,.985,.975,.960,.940,.915,.900]
        elif model=='G12430-016D':
            powers=[0,.5,.8,1,1.2,1.4,1.6,1.8,2];response=[1,1,.998,.995,.990,.975,.950,.920,.900]
        elif d.reverse_bias_V==1:
            powers=[0,1,2,2.5,3,3.2,3.4,3.6,3.8,4,4.2,4.4,4.6];response=[1,1,.999,.997,.992,.990,.985,.975,.960,.945,.920,.905,.890]
        else:
            powers=[0,.3,.5,.7,.8,.9,1];response=[1,1,.997,.990,.970,.940,.900]
        powers=np.asarray(powers)*1e-3;response=np.asarray(response)
        target=d.minimum_relative_sensitivity
        if not response.min()<=target<=response.max():raise ValueError('Sensitivity target lies outside digitized linearity range')
        # Reverse before unique: use the highest-power point on each response plateau.
        unique,at=np.unique(response[::-1],return_index=True)
        limit=float(np.interp(target,unique,powers[::-1][at]))
        out.update(linearity_limit_W=limit,allowed_linearity_power_W=d.safety_factor*limit,
            linearity_curve_power_W=powers,linearity_curve_relative_sensitivity=response)
    out.update(model=model,specification_case=d.specification_case,linearity_is_typical=(model!='CUSTOM'),
        requested_wavelength_m=cfg.heterodyne.wavelength_m,peak_sensitivity_wavelength_m=1.55e-6,
        spectral_range_m=(.9e-6,1.7e-6) if model!='CUSTOM' else None)
    if model!='CUSTOM' and not .9e-6<=cfg.heterodyne.wavelength_m<=1.7e-6:
        warnings.warn('Wavelength lies outside the G12430 range; built-in responsivity/NEP remain the 1.55 µm approximation',RuntimeWarning,stacklevel=2)
    return out


def power_limit(cfg,geometry,specs=None):
    specs=detector_specs(cfg) if specs is None else specs
    f=cfg.heterodyne.probe_fraction
    coeff=f*geometry.probe_fraction+(1-f)*geometry.reference_fraction+2*np.sqrt(f*(1-f))*geometry.vacuum_overlap
    per=np.divide(specs['allowed_linearity_power_W'],coeff,out=np.full(coeff.shape,np.inf),where=coeff>0)
    return {'maximum_total_power_W':float(per.min()),'critical_element':int(np.argmin(per)+1),
        'peak_coefficients':coeff,'per_element_total_limit_W':per,'element_limit_W':specs['allowed_linearity_power_W']}


def detector_noise(cfg,geometry,measurement,specs=None):
    specs=detector_specs(cfg) if specs is None else specs
    h=cfg.heterodyne;d=cfg.detector;R=specs['responsivity_A_per_W'];f=h.probe_fraction
    pp=h.total_power_W*f*geometry.probe_fraction;pr=h.total_power_W*(1-f)*geometry.reference_fraction
    dc=R*(pp+pr)
    if_carrier=2*R*h.total_power_W*np.sqrt(f*(1-f))*measurement['plasma_overlap_fraction']
    carrier=np.sqrt(2)/np.pi*if_carrier
    peak=pp+pr+2*h.total_power_W*np.sqrt(f*(1-f))*geometry.vacuum_overlap
    input_detector=np.full(dc.shape,R*specs['nep_W_per_sqrtHz'])
    input_shot=np.sqrt(2*1.602176634e-19*dc) if d.include_shot_noise else np.zeros(dc.shape)
    gain=2/np.pi;detector_asd=gain*input_detector;shot_asd=gain*input_shot;total=np.hypot(detector_asd,shot_asd)
    sigma=total*np.sqrt(h.bandwidth_Hz)
    phase_sigma=np.divide(sigma,np.abs(carrier),out=np.full(sigma.shape,np.inf),where=np.abs(carrier)>0)
    sigma_h=phase_sigma/(native.ELECTRON_RADIUS_M*h.wavelength_m)
    snr=np.divide(np.abs(carrier),sigma,out=np.zeros(sigma.shape),where=sigma>0)
    density_snr=np.abs(measurement['line_density_m2'])/sigma_h
    curve=specs['linearity_curve_power_W']
    sensitivity=np.interp(peak,curve,specs['linearity_curve_relative_sensitivity'],right=np.nan) if curve.size else np.ones(peak.shape)
    return dict(probe_power_W=pp,reference_power_W=pr,combined_power_W=pp+pr,peak_power_W=peak,
        photocurrent_dc_A=dc,if_carrier_A=if_carrier,carrier_A=carrier,detector_asd=detector_asd,
        shot_asd=shot_asd,total_asd=total,sigma_i_A=sigma,sigma_phase_rad=phase_sigma,sigma_h_m2=sigma_h,
        carrier_SNR=snr,line_density_SNR=density_snr,shot_variance_fraction=np.divide(shot_asd**2,total**2,out=np.zeros(total.shape),where=total>0),
        phase_model_valid=snr>=d.minimum_carrier_SNR,estimated_relative_sensitivity=sensitivity,
        linearity_margin_W=specs['allowed_linearity_power_W']-peak,
        detector_linear=peak<=specs['allowed_linearity_power_W']*(1+20*np.finfo(float).eps),
        bandwidth_ratio=(h.frequency_Hz+h.bandwidth_Hz)/specs['cutoff_frequency_Hz'])
