# S2-Gate 522 Status: Resident DQ Int16 Runtime Map

## Gate

- Gate: S2-Gate 522
- Theme: DQ/mask memory-contract hardening and resident 200-light validation
- Date: 2026-06-23

## Completed

- Added a checked runtime dtype for resident DQ bitfield construction.
- Kept direct resident DQ helper behavior on `uint32` by default.
- Routed the resident CUDA pipeline DQ bitfield through `int16`, matching the
  FITS DQ artifact dtype.
- Removed count-map rounding from the DQ output writer path because DQ is a
  bitfield artifact, not a count map.
- Recorded `dq_map_runtime_dtype` in resident and integration artifacts.
- Added focused DQ dtype tests.
- Ran real 200-light validation on the M38 H-alpha benchmark.
- Checked C drive/project storage before continuing; C had `428.54 GB` free, so
  no cleanup was performed.

## Real 200-Light Validation

- Run root:
  `C:\glass_runs\phase2_s2_gate522_dq_int16_runtime\runs_20260623_104044`
- Input plan:
  `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`
- Shared master cache:
  `C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- Active integrated frames: `193`
- Warm repeat with shared master cache:
  - internal: `7.029533999972045 s`
  - shell: `7.3860233 s`
- Full run with per-run master cache policy:
  - internal: `12.840817800024524 s`
  - shell: `13.2148972 s`
- WBPP black-box baseline: `1092.541 s`
- Warm shell speedup versus WBPP: `147.92005868706102x`
- Full shell speedup versus WBPP: `82.67573318770184x`

## Numerical Results

- Gate522 warm-repeat master vs Gate521 warm-repeat master:
  - RMS: `0.0`
  - p99 absolute difference: `0.0`
  - max absolute difference: `0.0`
- Gate522 full run vs Gate522 warm-repeat:
  - RMS: `0.0`
  - p99 absolute difference: `0.0`
  - max absolute difference: `0.0`
- Gate522 DQ map vs Gate521 DQ map:
  - different pixels: `0`
  - max absolute difference: `0`
- GLASS vs WBPP black-box robust linear-fit comparison:
  - RMS: `0.0015009512947433384`
  - p99 absolute difference: `0.00034034321741462114`
  - fit fraction: `0.982980688129347`

## Profile Evidence

- Profile:
  `C:\glass_runs\phase2_s2_gate522_dq_int16_runtime\runs_20260623_104044\warm_profile_int16.prof`
- `_resident_dq_map`: `1.3252872 s`
- Gate521 `_resident_dq_map` baseline: `1.3696953 s`
- `_write_resident_outputs`: `0.2833296 s`
- Gate521 output-write profile baseline: `0.388811 s`
- Runtime DQ map memory for `9600x6422`:
  - previous `uint32`: `246604800` bytes
  - current `int16`: `123302400` bytes
  - saved: `123302400` bytes, about `117.59 MiB`

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py -k "resident_dq_map or resident_dq_coverage_provenance or resident_cuda_run_writes_integration_artifacts"
.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_522_doctor.json
.\.venv\Scripts\python.exe -m json.tool runs\checkpoints\s2_gate_522_dq_int16_runtime_summary.json
.\.venv\Scripts\python.exe -m pytest -q
```

Real validation commands used `glass run --backend cuda --memory-mode resident
--until-stage integration --local-normalization off --integration-rejection
winsorized_sigma --integration-weighting none --resident-registration
similarity_cuda_triangle --resident-warp-interpolation lanczos3
--resident-output-maps audit` against the 200-light M38 H-alpha plan.

## Test Results

- Ruff: passed
- Focused DQ/resident tests: `13 passed, 76 deselected`
- JSON validation: passed
- Full pytest: `1168 passed in 43.58s`

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
  `runs/checkpoints/s2_gate_522_dq_int16_runtime_summary.json`
- Doctor JSON:
  `runs/checkpoints/s2_gate_522_doctor.json`
- External summary:
  `C:\glass_runs\phase2_s2_gate522_dq_int16_runtime\runs_20260623_104044\gate522_dq_int16_runtime_summary.json`
- Compare reports:
  - `C:\glass_runs\phase2_s2_gate522_dq_int16_runtime\runs_20260623_104044\compare_gate522_vs_gate521.html`
  - `C:\glass_runs\phase2_s2_gate522_dq_int16_runtime\runs_20260623_104044\compare_full_run_vs_warm_repeat.html`
  - `C:\glass_runs\phase2_s2_gate522_dq_int16_runtime\runs_20260623_104044\compare_gate522_vs_wbpp.html`

## Known Limitations

- This is a DQ/mask runtime memory-contract gate, not a new science-pixel
  algorithm gate.
- End-to-end warm/full timings are close to Gate521 and are treated as
  run-to-run variance; the measured improvement is component-level.
- Native host DQ remains disabled by default on this local Debug-like build
  unless the optimized native preference probe passes or an override is used.

## Next Step

- Return to the substantive 200-light A/B line:
  - resident light-pipeline overlap and pinned-memory scheduling;
  - resident registration/warp batching and GPU-resident orchestration;
  - repeated real A/B timing and numerical agreement reporting.

## Clean-Room Compliance

- Compliant.
- Only GLASS code, GLASS-generated artifacts, and user-generated WBPP
  black-box outputs were read.
- No official PixInsight/WBPP/PJSR source was accessed.
- Original input image directories were treated as read-only.
