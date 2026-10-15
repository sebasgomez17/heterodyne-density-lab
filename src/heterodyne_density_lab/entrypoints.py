"""Shared script setup/output path; all five entry scripts call this runner."""
from pathlib import Path
import argparse
import time
import numpy as np
import matplotlib
from threadpoolctl import threadpool_limits
from .configuration import load_configuration, apply_design
from .model import Workspace
from .reconstruction import simulate, measurement_rows
from .outputs import new_run,write_csv,write_json,save_reconstruction,cached_tuning


def run(kind,root):
    parser=argparse.ArgumentParser(description=f'Heterodyne Density Lab: {kind}')
    parser.add_argument('--quick',action='store_true',help='Explicit reduced study/ensemble preset for installation checks; not a converged scientific study')
    parser.add_argument('--refresh-tuning',action='store_true',help='Recompute global tuning rather than reusing a matching cache')
    args=parser.parse_args()
    root=Path(root)
    cfg=load_configuration(root/'config/default_design.py','make_default_design')
    if not cfg.plots.show:matplotlib.use('Agg')
    from . import plotting
    start=time.perf_counter()
    cfg.validate()
    with threadpool_limits(limits=1,user_api='blas'):
        if kind=='main_density_design':
            if args.quick:cfg.noise.realizations=min(cfg.noise.realizations,16)
            path=new_run(root,cfg,kind);result=simulate(cfg)
            save_reconstruction(path,result);plotting.configure_style(cfg)
            if cfg.plots.geometry:plotting.save_figure(plotting.geometry_figure(cfg,result['ensemble']['workspace'].geometry),path,'imaging_geometry',cfg)
            if cfg.plots.reconstruction:plotting.save_figure(plotting.reconstruction_figure(result),path,'density_reconstruction',cfg)
            if cfg.plots.noise:plotting.save_figure(plotting.noise_figure(result),path,'detector_noise_budget',cfg)
            print(f"Used order: {result['used_upper_order']}; alpha: {result['weighting_alpha']:.2f}; weighted cond: {result['weighted_condition_number']:.4g}")
            print(f"Maximum configured total power: {result['ensemble']['power_limit']['maximum_total_power_W']:.6g} W")
            print(result['error_summary'])
            if cfg.plots.measurement_table:
                for row in measurement_rows(result):
                    print(f"Element {row['Element']:2d}: used={row['UsedInInversion']} phase={row['PhaseTrue_rad']:.6g} rad carrier SNR={row['HeterodyneCarrierSNR']:.5g}")
        else:
            study=load_configuration(root/'config/study_config.py','make_study_config',cfg)
            if args.quick:
                study.designs=study.designs[:1];study.optimization.realizations=8;study.optimization.training_scales=(.10,.20,.30)
                study.optimization.upper_orders=(2,3);study.optimization.alphas=(0,.5,1)
                study.scale_lengths=(.10,.20,.30);study.scale_realizations=16;study.power_points_per_decade=2
                study.noise_realizations=16;study.basis_orders=(2,3,4);study.basis_realizations=16;study.basis_design_index=0
            cfg.plots.mode=study.output_mode;path=new_run(root,cfg,kind);write_json(path/'study_configuration.json',study)
            plotting.configure_style(cfg)
            from . import studies
            runners={'study_density_scale_length':studies.run_scale_length,'study_detector_power_tradeoff':studies.run_power,
                'study_detector_noise_contribution':studies.run_noise_contribution,'study_pretzler_basis_order':studies.run_basis_order}
            designs=study.designs if kind!='study_pretzler_basis_order' else [study.designs[study.basis_design_index]]
            rows=[];tunings=[]
            for design in designs:
                print(f'Global tuning / study: {design.name}',flush=True)
                workspace=Workspace(apply_design(cfg,design))
                tuning=cached_tuning(root,cfg,design,study,workspace,args.refresh_tuning);tunings.append(tuning)
                print(f"  Fixed order={tuning['upper_order']}, alpha={tuning['alpha']:.2f}, training score={tuning['score']:.5g}",flush=True)
                rows.extend(runners[kind](cfg,design,study,tuning,workspace))
            write_csv(path/'study_results.csv',rows);write_json(path/'global_tuning.json',tunings)
            if kind=='study_pretzler_basis_order':
                if not np.isfinite(study.basis_tolerance) or study.basis_tolerance<0:
                    raise ValueError('Basis diagnostic tolerance must be finite and nonnegative')
                best=min(rows,key=lambda row:row['SelectionMetricMean'])
                threshold=(1+study.basis_tolerance)*best['SelectionMetricMean']
                eligible=[row for row in rows if row['SelectionMetricMean']<=threshold+20*np.finfo(float).eps*max(1,abs(threshold))]
                simplest=min(eligible,key=lambda row:row['RequestedNupper'])
                write_json(path/'basis_selection.json',dict(metric=study.basis_metric,
                    global_requested_order=tunings[0]['upper_order'],diagnostic_best=best,
                    relative_tolerance=study.basis_tolerance,sparsest_within_tolerance=simplest))
                print(f"Global order={tunings[0]['upper_order']}; single-profile diagnostic best={best['RequestedNupper']}; within-tolerance order={simplest['RequestedNupper']}")
            plotting.save_figure(plotting.tuning_figure(tunings),path,'global_tuning',cfg)
            if kind=='study_density_scale_length':
                figures=plotting.scale_study_figures(rows);names=['study_scale_length_density','study_scale_length_local_error']
            elif kind=='study_detector_power_tradeoff':figures=plotting.power_figures(rows);names=['study_power_tradeoff','study_power_operating_window']
            elif kind=='study_detector_noise_contribution':figures=[plotting.noise_contribution_figure(rows)];names=['study_noise_contribution']
            else:figures=[plotting.basis_figure(rows)];names=['study_basis_order']
            for fig,name in zip(figures,names):plotting.save_figure(fig,path,name,cfg)
        elapsed=time.perf_counter()-start
        write_json(path/'run_summary.json',dict(script=kind,elapsed_seconds=elapsed,quick_preset=args.quick,
            status='completed',blas_thread_limit=1))
        print(f'Completed in {elapsed:.2f} s. Outputs: {path}',flush=True)
    if cfg.plots.show:
        import matplotlib.pyplot as plt
        plt.show()
