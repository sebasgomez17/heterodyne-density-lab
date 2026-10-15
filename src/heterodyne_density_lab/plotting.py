"""Reusable Matplotlib figures; scripts control displaying and exporting them."""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle


def configure_style(cfg):
    size={'screen':11,'document':10,'presentation':13}.get(cfg.plots.mode)
    if size is None:raise ValueError('Unknown plot mode')
    plt.rcParams.update({'font.family':cfg.plots.font,'font.size':size,'axes.grid':True,
        'grid.alpha':.25,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':cfg.plots.dpi})


def save_figure(fig,path,name,cfg):
    fmt=cfg.plots.figure_format.lower()
    if fmt not in ['pdf','png','svg']:raise ValueError('Figure format must be pdf, png, or svg')
    fig.savefig(path/f'{name}.{fmt}',bbox_inches='tight',pad_inches=cfg.plots.padding_inches)
    if not cfg.plots.show:plt.close(fig)


def geometry_figure(cfg,g):
    fig,axes=plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
    for ax,plane in zip(axes,['Object plane','Detector plane']):
        M=cfg.magnification if plane=='Detector plane' else 1
        ax.add_patch(Circle(np.asarray(cfg.port.center_m)*M*1e3,cfg.port.diameter_m/2*abs(M)*1e3,fill=False,color='tab:gray',label='Port'))
        ax.add_patch(Circle(np.asarray(cfg.beam.center_m)*M*1e3,cfg.beam.waist_m*abs(M)*1e3,fill=False,ls='--',color='tab:orange',label='Probe waist'))
        for j,b in enumerate(g.bounds_image):
            b=b/(1 if plane=='Detector plane' else cfg.magnification)*1e3
            ax.add_patch(Rectangle((min(b[0],b[1]),min(b[2],b[3])),abs(b[1]-b[0]),abs(b[3]-b[2]),
                fill=True,alpha=.7 if g.active[j] else .15,color='tab:blue'))
        ax.autoscale_view();ax.set_aspect('equal');ax.set_xlabel('x [mm]');ax.set_ylabel('y [mm]');ax.set_title(plane);ax.legend(fontsize=8)
    return fig


def reconstruction_figure(result):
    fig,axes=plt.subplots(2,1,figsize=(8,7),layout='constrained')
    ax=axes[0];r=result['r']*1e3;scale=1e19
    ax.plot(r,result['truth']/scale,label='True profile',color='black')
    ax.plot(r,result['pretzler_mean']/scale,'--',label='Mean Pretzler')
    ax.plot(r,result['spline_mean']/scale,label='Mean symmetric spline')
    ax.scatter(result['r_points']*1e3,result['points_mean']/scale,label='Pretzler points',s=22)
    if result['spline_profiles'] is not None and len(result['spline_profiles'])>1:
        lower,upper=np.percentile(result['spline_profiles'],[5,95],axis=0)
        ax.fill_between(r,lower/scale,upper/scale,alpha=.15,label='5–95% realization band')
    ax.axvline(result['r_sampled_max']*1e3,ls=':',color='gray',label='Max sampled radius')
    ax.set(xlabel='r [mm]',ylabel=r'$n_e$ [$10^{19}$ m$^{-3}$]',title='Density reconstruction');ax.legend(fontsize=9)
    e=result['ensemble'];g=e['workspace'].geometry;idx=e['indices'];x=g.effective_x[idx]*1e3;scaleh=1e18
    axes[1].errorbar(x,e['measurement']['line_density_m2'][idx]/scaleh,yerr=e['sigma_h']/scaleh,fmt='o',label='Exact phase-derived observable ± analytic σ')
    axes[1].scatter(x,e['h'][0]/scaleh,marker='x',label='First realization')
    axes[1].set(xlabel='Effective signed x [mm]',ylabel=r'$h$ [$10^{18}$ m$^{-2}$]',title='Finite-area chord measurements');axes[1].legend(fontsize=8)
    return fig


def noise_figure(result):
    e=result['ensemble'];n=e['noise'];x=np.arange(1,len(n['carrier_SNR'])+1)
    fig,axes=plt.subplots(2,2,figsize=(10,7),layout='constrained')
    axes[0,0].plot(x,n['peak_power_W']*1e3,'o-',label='Peak interference power')
    axes[0,0].axhline(e['power_limit']['element_limit_W']*1e3,ls='--',color='black',label='Configured limit');axes[0,0].set_ylabel('Power [mW]')
    axes[0,1].semilogy(x,n['carrier_SNR'],'o-');axes[0,1].set_ylabel('Carrier SNR')
    axes[1,0].semilogy(x,n['detector_asd'],'o-',label='Detector');axes[1,0].semilogy(x,n['shot_asd'],'s-',label='Shot');axes[1,0].set_ylabel(r'Baseband ASD [A/√Hz]')
    axes[1,1].semilogy(x,n['sigma_phase_rad'],'o-');axes[1,1].set_ylabel('Analytic phase σ [rad]')
    for ax in axes.flat:ax.set_xlabel('Physical detector element');ax.set_xticks(x[::max(1,len(x)//8)])
    axes[0,0].legend(fontsize=8);axes[1,0].legend(fontsize=8)
    return fig


def tuning_figure(tunings):
    n=len(tunings);cols=min(3,n);rows=(n+cols-1)//cols
    fig,axes=plt.subplots(rows,cols,figsize=(4*cols,3.3*rows),squeeze=False,layout='constrained')
    for ax,t in zip(axes.flat,tunings):
        score=np.asarray(t['score_surface'])
        im=ax.imshow(score,origin='lower',aspect='auto',extent=[min(t['alphas'])-.05,max(t['alphas'])+.05,min(t['upper_orders'])-.5,max(t['upper_orders'])+.5])
        ax.plot(t['alpha'],t['upper_order'],'rx',ms=10);ax.set(xlabel='α',ylabel='Requested upper order',title=t['design_name']);fig.colorbar(im,ax=ax,label='Training metric')
    for ax in list(axes.flat)[n:]:ax.set_visible(False)
    return fig


def scale_study_figures(rows):
    counts=sorted({row['SelectedChannels'] for row in rows},reverse=True)
    figures=[]
    for field,sd,label,factor in [('SplineRMS','SplineRMSStd','Full-radius spline RMS',1),('ScaleLengthRMS','ScaleLengthRMSStd',r'Full-radius $L_n$ error [%]',100)]:
        columns=min(3,len(counts));nrows=(len(counts)+columns-1)//columns
        fig,axes=plt.subplots(nrows,columns,figsize=(4.3*columns,3.4*nrows),squeeze=False,layout='constrained')
        for ax,count in zip(axes.flat,counts):
            names=list(dict.fromkeys(row['Design'] for row in rows if row['SelectedChannels']==count))
            for name in names:
                data=[row for row in rows if row['Design']==name]
                ax.plot([r['LnOverR'] for r in data],factor*np.array([r[field] for r in data]),'o-',label=name.partition(',')[2].strip() or 'Baseline')
            ax.set(xlabel=r'Prescribed $\ell_n/R$',ylabel=label,title=f'{count} digitized elements');ax.legend(fontsize=8)
        for ax in list(axes.flat)[len(counts):]:ax.set_visible(False)
        figures.append(fig)
    return figures


def power_figures(rows):
    profiles=sorted({row['LnOverR'] for row in rows});names=list(dict.fromkeys(row['Design'] for row in rows))
    fig,axes=plt.subplots(1,len(profiles),figsize=(5*len(profiles),5),squeeze=False,layout='constrained')
    for ax,profile in zip(axes.flat,profiles):
        for name in names:
            data=[r for r in rows if r['Design']==name and r['LnOverR']==profile]
            ax.errorbar([r['Power_W'] for r in data],[r['SplineRMS'] for r in data],yerr=[r['SplineRMSStd'] for r in data],fmt='o-',label=name)
        ax.set_xscale('log');ax.set(xlabel='Total detector-plane power [W]',ylabel='Full-radius spline RMS',title=rf'$\ell_n/R={profile:.2f}$')
    axes[0,-1].legend(fontsize=7)
    fig2,axes2=plt.subplots(1,2,figsize=(11,5),layout='constrained')
    nominal=profiles[len(profiles)//2]
    for name in names:
        data=[r for r in rows if r['Design']==name and r['LnOverR']==nominal]
        axes2[0].loglog([r['Power_W'] for r in data],[r['MedianCarrierSNR'] for r in data],'o-',label=name)
        axes2[1].loglog([r['Power_W'] for r in data],[r['PeakLinearityRatio'] for r in data],'o-',label=name)
    axes2[1].axhline(1,color='black',ls='--');axes2[0].set_ylabel('Median carrier SNR');axes2[1].set_ylabel('Peak power / configured linearity limit')
    for ax in axes2:ax.set_xlabel('Total detector-plane power [W]')
    axes2[1].legend(fontsize=7)
    return fig,fig2


def noise_contribution_figure(rows):
    fig,axes=plt.subplots(1,2,figsize=(11,5),layout='constrained')
    for name in dict.fromkeys(r['Design'] for r in rows):
        data=[r for r in rows if r['Design']==name];x=[r['LnOverR'] for r in data]
        axes[0].plot(x,[r['WeightingChange'] for r in data],'o-',label=name)
        axes[1].errorbar(x,[r['StochasticChange'] for r in data],yerr=[r['DetectorLimitedStd'] for r in data],fmt='o-',label=name)
    for ax,title in zip(axes,['Fixed weighting effect','Stochastic noise effect']):
        ax.axhline(0,color='black',ls=':');ax.set(xlabel=r'$\ell_n/R$',ylabel='Change in spline RMS',title=title)
    axes[1].legend(fontsize=7)
    return fig


def basis_figure(rows):
    fig,axes=plt.subplots(1,3,figsize=(13,4.5),layout='constrained');x=[r['RequestedNupper'] for r in rows]
    for ax,key,label,factor in zip(axes,['SplineFullRMS','ScaleLengthFullRMS','WeightedConditionNumber'],['Density RMS',r'$L_n$ error [%]','Weighted condition number'],[1,100,1]):
        ax.plot(x,np.array([r[key] for r in rows])*factor,'o-');ax.set(xlabel='Requested upper order',ylabel=label)
    axes[2].set_yscale('log');return fig
