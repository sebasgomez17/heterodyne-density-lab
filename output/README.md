# Generated scientific outputs

Run scripts create unique UTC-stamped folders here. Single designs save CSV
profiles/measurement/error tables, JSON configuration/environment/diagnostics,
NPZ observation/reconstruction arrays, PDF figures, and runtime summaries. Studies
save CSV sweeps, global tuning JSON/figures, configuration and runtime records.
The cache/ subfolder contains content-keyed global tuning JSON, without pickle.

Outputs and caches are excluded from Git and the source release. Export chosen
publication figures deliberately into documentation/figures. The scientific
manual's figures are included as documentation inputs; normal runs do not
replace them. Nonfinite JSON diagnostics are represented by null, while CSV
invalid-power result fields use nan. NPZ arrays are numeric and use realizations
as their first axis; load with numpy.load(..., allow_pickle=False).
