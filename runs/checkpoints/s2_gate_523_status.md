# S2-Gate 523 Status: Resident Output Diagnostics Sampled Percentiles

## Gate

- Gate: S2-Gate 523
- Theme: Resident audit-path performance hardening
- Date: 2026-06-23

## Completed

- Added deterministic stride-sampled percentile diagnostics for large resident
  output arrays.
- Kept exact `np.percentile` diagnostics for small arrays.
- Kept full-frame exact `min`, `max`, `mean`, `std`, finite/non-finite counts,
  and clipping counts.
- Recorded percentile provenance in `output_diagnostics.statistics` and
  `output_diagnostics.normalization_probe`:
  - `percentile_method`
  - `percentile_approximation`
  - `percentile_sample_pixels`
  - `percentile_total_pixels`
  - `percentile_stride`
- Added focused tests for exact small-array diagnostics and sampled large-array
  diagnostics.

## Real 200-Light Validation

- Run root:
  `C:\glass_runs\phase2_s2_gate523_output_diagnostics_sample\runs_20260623_105417`
- Input plan:
  `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`
- Shared master cache:
  `C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- Warm repeat with shared master cache:
  - internal: `6.617358400020748 s`
  - shell: `6.9960698 s`
- Full run with per-run master cache policy:
  - internal: `13.876236599928234 s`
  - shell: `14.230714599999999 s`
- WBPP black-box baseline: `1092.541 s`
- Warm shell speedup versus WBPP: `156.1649656497138x`

## Profile Evidence

- Before profile:
  `C:\glass_runs\phase2_s2_gate523_profile_current_main\runs_20260623_105222\warm_profile_current.prof`
- After profile:
  `C:\glass_runs\phase2_s2_gate523_output_diagnostics_sample\runs_20260623_105417\warm_profile_sampled_diagnostics.prof`
- `_output_diagnostics` cumulative time:
  - before: about `0.828 s`
  - after: `0.265952 s`
  - saved: about `0.562048 s`
- Percentile time:
  - before: about `0.457 s`
  - after: `0.012514 s`
  - saved: about `0.444486 s`
- Profile internal elapsed delta: `-0.5677271001040936 s`

## Numerical Results

- Gate523 warm-repeat master vs Gate522 warm-repeat master:
  - RMS: `0.0`
  - p99 absolute difference: `0.0`
  - max absolute difference: `0.0`
- Gate523 full run vs Gate523 warm-repeat:
  - RMS: `0.0`
  - p99 absolute difference: `0.0`
  - max absolute difference: `0.0`
- GLASS vs WBPP black-box robust linear-fit comparison:
  - RMS: `0.0015009512947433384`
  - p99 absolute difference: `0.00034034321741462114`
  - fit fraction: `0.982980688129347`

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py tests\test_cuda_resident_stack.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py -k "output_diagnostics"
.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_523_doctor.json
.\.venv\Scripts\python.exe -m json.tool runs\checkpoints\s2_gate_523_output_diagnostics_sample_summary.json
.\.venv\Scripts\python.exe -m pytest -q
```

Real validation used the same 200-light M38 H-alpha resident CUDA command line
as Gate522/current-main A/B:

```powershell
glass run --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-output-maps audit
```

## Test Results

- Ruff: passed
- Focused output diagnostics tests: `2 passed, 47 deselected`
- JSON validation: passed
- Full pytest: `1169 passed in 42.62s`

## CUDA

- CUDA available: yes
- CUDA wrapper importable: yes
- Native extension loaded: yes
- GPU 0:
  `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver: `596.21`

## Artifacts

- Checkpoint summary:
  `runs/checkpoints/s2_gate_523_output_diagnostics_sample_summary.json`
- Doctor JSON:
  `runs/checkpoints/s2_gate_523_doctor.json`
- External summary:
  `C:\glass_runs\phase2_s2_gate523_output_diagnostics_sample\runs_20260623_105417\gate523_output_diagnostics_sample_summary.json`
- Compare reports:
  - `C:\glass_runs\phase2_s2_gate523_output_diagnostics_sample\runs_20260623_105417\compare_gate523_vs_gate522.html`
  - `C:\glass_runs\phase2_s2_gate523_output_diagnostics_sample\runs_20260623_105417\compare_full_vs_warm_repeat.html`
  - `C:\glass_runs\phase2_s2_gate523_output_diagnostics_sample\runs_20260623_105417\compare_gate523_vs_wbpp.html`

## Known Limitations

- This is an audit-path diagnostics performance gate, not a science-pixel
  algorithm change.
- Large-array diagnostic percentiles are approximate by design and are marked
  as such in artifacts.
- Full per-run-cache timing is still dominated by master build/load and I/O
  variance; this gate does not solve cold-cache master creation.

## Next Step

- Return to the larger substantive bottlenecks:
  - resident light read/upload/calibration overlap;
  - resident registration/warp batching and GPU-resident orchestration.

## Clean-Room Compliance

- Compliant.
- Only GLASS code, GLASS-generated artifacts, and user-generated WBPP
  black-box outputs were read.
- No official PixInsight/WBPP/PJSR source was accessed.
- Original input image directories were treated as read-only.
