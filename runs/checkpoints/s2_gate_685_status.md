# S2-Gate 685 Status: Native Completion Overlap Semantics

## Gate

- Gate: S2-Gate 685
- Theme: resident native-completion read-supply overlap telemetry
- Status: green

## Completed

- Added effective `read_supply_*` timing fields to resident CUDA artifacts.
- Preserved legacy prefetch `worker_*` and `light_read_wait_wall` semantics.
- Exposed native-completion worker/file-read/wait/hidden-stage fields in
  `resident_light_pipeline_profile`.
- Extended `resident-runtime-compare` to display effective read-supply worker
  time and to derive the same fields from older Gate684 artifacts.
- Added focused tests for profile, runtime compare, and native resident CLI
  artifact contracts.
- Ran a real 200-light resident CUDA candidate against Gate684.

## Commands

- `.venv\Scripts\python.exe -m ruff check src/glass/engine/resident_cuda.py src/glass/engine/resident_light_pipeline_profile.py src/glass/report/resident_runtime_compare.py tests/test_resident_light_pipeline_profile.py tests/test_resident_cuda_run.py tests/test_resident_runtime_compare.py`
- `.venv\Scripts\python.exe -m pytest -q tests/test_resident_light_pipeline_profile.py tests/test_resident_runtime_compare.py tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_u16_completion_calibration_is_opt_in`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate685_native_overlap_semantics\runs_20260626_223000\default_overlap_semantics --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
- `.venv\Scripts\glass.exe resident-runtime-compare --run gate684_auto_std=C:\glass_runs\phase2_s2_gate684_native_read_backend_policy\runs_20260626_211500\default_auto_std_warm --run gate685_overlap=C:\glass_runs\phase2_s2_gate685_native_overlap_semantics\runs_20260626_223000\default_overlap_semantics --baseline-label gate684_auto_std --out C:\glass_runs\phase2_s2_gate685_native_overlap_semantics\gate685_runtime_compare.json --markdown C:\glass_runs\phase2_s2_gate685_native_overlap_semantics\gate685_runtime_compare.md`
- `.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate684_native_read_backend_policy\runs_20260626_211500\default_auto_std_warm --candidate-run C:\glass_runs\phase2_s2_gate685_native_overlap_semantics\runs_20260626_223000\default_overlap_semantics --out C:\glass_runs\phase2_s2_gate685_native_overlap_semantics\gate685_regression_gate.json --markdown C:\glass_runs\phase2_s2_gate685_native_overlap_semantics\gate685_regression_gate.md --max-elapsed-ratio 1.10 --min-active-frame-count 193 --max-masked-frame-count 7 --fail-on-failure`
- `.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate685_native_overlap_semantics\runs_20260626_223000\default_overlap_semantics --out C:\glass_runs\phase2_s2_gate685_native_overlap_semantics\gate685_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate685_native_overlap_semantics\gate685_mainline_audit.md --min-lights 200 --min-active-frames 193 --max-masked-frames 7 --fail-on-not-green`

## Test Results

- Ruff: passed.
- Focused tests: `8 passed in 0.66 s`.
- Full pytest: `1426 passed in 66.10 s`.
- Real 200-light regression gate: passed, failed checks `[]`.
- Phase 2 mainline audit: passed, failed checks `[]`.
- Output comparison versus Gate684:
  - direct SHA256: all six integration FITS outputs identical;
  - array compare: all six integration FITS outputs array-identical with
    `max_abs=0.0` and `rms=0.0`.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Real 200-Light Result

- Candidate run:
  `C:\glass_runs\phase2_s2_gate685_native_overlap_semantics\runs_20260626_223000\default_overlap_semantics`
- Total elapsed: `12.43947100022342 s`.
- Gate684 baseline elapsed: `11.66652269999031 s`.
- Elapsed ratio: `1.0662535290171555`.
- Active/masked frames: `193 / 7`.
- Effective read-supply telemetry:
  - `read_supply_model=native_completion_calibration`;
  - `read_supply_effective_backend=std_ifstream`;
  - `read_supply_worker_cumulative_s=30.826195000000002`;
  - `read_supply_file_read_cumulative_s=30.780779700000004`;
  - `read_supply_consumer_wait_wall_s=0.03785769999999997`;
  - `read_supply_overlap_saved_s=27.324453300009186`;
  - `read_supply_worker_to_wall_ratio=8.80310360986387`;
  - `read_supply_overlap_efficiency=0.8864036998406447`.

## Known Limits

- This gate is telemetry hardening only; it does not improve wall time.
- Single-run timing is still affected by external storage/cache state.
- The legacy prefetch timing fields remain for compatibility and are not the
  right bottleneck signal for native-completion calibration.

## Next Step

- Return to substantive resident CUDA optimization. Best next targets:
  native H2D/calibrate/store wall time, resident integration kernel time, or
  batching more registration/warp orchestration inside resident CUDA.

## Clean-Room Compliance

- Uses only GLASS-owned timing variables, GLASS-generated artifacts, tests, and
  user-owned benchmark data.
- Does not inspect external implementation source.
- Does not modify input image directories.
- Does not change scientific image math or output pixels.
