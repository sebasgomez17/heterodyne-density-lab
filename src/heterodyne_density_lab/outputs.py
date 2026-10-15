"""Human-readable, versioned outputs and content-keyed tuning cache (no pickle)."""
from pathlib import Path
from dataclasses import asdict, is_dataclass
from importlib.metadata import version
import csv
import hashlib
import json
import platform
import subprocess
import sys
import uuid
from datetime import datetime, timezone
import numpy as np
import scipy


def serializable(obj):
    if is_dataclass(obj):return serializable(asdict(obj))
    if isinstance(obj,dict):return {str(k):serializable(v) for k,v in obj.items()}
    if isinstance(obj,(tuple,list)):return [serializable(v) for v in obj]
    if isinstance(obj,np.ndarray):return serializable(obj.tolist())
    if isinstance(obj,(float,np.floating)):return float(obj) if np.isfinite(obj) else None
    if isinstance(obj,(np.integer,np.bool_)):return obj.item()
    if isinstance(obj,Path):return str(obj)
    return obj


def write_json(path,obj):
    Path(path).write_text(json.dumps(serializable(obj),indent=2,allow_nan=False)+'\n',encoding='utf-8')


def write_csv(path,rows):
    if not rows:return
    with Path(path).open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def new_run(root,cfg,name):
    base=Path(cfg.plots.output_directory)
    if not base.is_absolute():base=Path(root)/base
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    path=base/f'{name}_{stamp}';path.mkdir(parents=True,exist_ok=False)
    versions={name:version(name) for name in ['heterodyne-density-lab','numpy','scipy','matplotlib','cffi','threadpoolctl']}
    try:commit=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],stderr=subprocess.DEVNULL,text=True,timeout=2).strip()
    except (OSError,subprocess.SubprocessError):commit=None
    write_json(path/'configuration.json',cfg)
    write_json(path/'environment.json',dict(versions=versions,python=sys.version,platform=platform.platform(),
        architecture=platform.machine(),git_commit=commit,utc_timestamp=stamp,random_generator='NumPy PCG64'))
    return path


def cached_tuning(root,base,design,study,workspace,force=False):
    from .studies import tune
    scientific=asdict(base);scientific.pop('plots')
    # Hash actual Python modules and extension as well as configuration/version.
    from . import _core
    digest=hashlib.sha256()
    for f in sorted(Path(__file__).parent.glob('*.py')):digest.update(f.read_bytes())
    digest.update(Path(_core.__file__).read_bytes())
    key={'base':scientific,'design':asdict(design),'optimization':asdict(study.optimization),
        'version':version('heterodyne-density-lab'),'numpy':np.__version__,'scipy':scipy.__version__,
        'code':digest.hexdigest()}
    fingerprint=hashlib.sha256(json.dumps(serializable(key),sort_keys=True).encode()).hexdigest()
    directory=Path(base.plots.output_directory)
    if not directory.is_absolute():directory=Path(root)/directory
    cache=directory/'cache'/f'tuning_{fingerprint}.json'
    if study.cache_tuning and not force and cache.exists():
        try:
            stored=json.loads(cache.read_text())
            if stored.get('fingerprint')==fingerprint:
                print(f'  Reusing cached global tuning for {design.name}',flush=True)
                return stored['tuning']
        except (OSError,ValueError,KeyError):pass
    result=tune(base,design,study.optimization,workspace)
    if study.cache_tuning:
        cache.parent.mkdir(parents=True,exist_ok=True)
        temp=cache.with_suffix('.'+uuid.uuid4().hex+'.tmp')
        write_json(temp,dict(fingerprint=fingerprint,tuning=result))
        temp.replace(cache)
    return result


def save_reconstruction(path,result):
    from .reconstruction import measurement_rows
    e=result['ensemble'];r=result['r']
    rows=[dict(Radius_m=radius,TrueDensity_m3=t,MeanPretzlerDensity_m3=p,MeanSplineDensity_m3=s,
        FirstPretzlerDensity_m3=pf,FirstSplineDensity_m3=sf) for radius,t,p,s,pf,sf in zip(r,result['truth'],
            result['pretzler_mean'],result['spline_mean'],result['pretzler_first'],result['spline_first'])]
    write_csv(path/'density_profiles.csv',rows)
    write_csv(path/'measurement_table.csv',measurement_rows(result))
    write_csv(path/'error_summary.csv',[dict(Metric=key,**value) for key,value in result['error_summary'].items()])
    write_json(path/'diagnostics.json',{key:result[key] for key in ['requested_upper_order','used_upper_order','rank_reduced',
        'matrix_rank','weighting_alpha','condition_number','weighted_condition_number','r_sampled_max','basis_ids']})
    arrays={key:result[key] for key in ['r','truth','coefficients','spline_lambdas','pretzler_profiles','spline_profiles','point_profiles'] if result[key] is not None}
    arrays.update(line_density_m2=e['h'],I_A=e['I'],Q_A=e['Q'],phase_rad=e['phase'],element_ids=e['indices']+1)
    np.savez_compressed(path/'ensemble.npz',**arrays)
