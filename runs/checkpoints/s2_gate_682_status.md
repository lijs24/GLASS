# S2-Gate 682 Status: Native Completion 250us Lane-Fill Default

## Gate

- Gate: S2-Gate 682
- Status: green
- Date: 2026-06-26 Asia/Shanghai
- Scope: resident CUDA native-completion read/H2D/calibration scheduling

## Completed

- Promoted the `throughput-v4-native-completion` preset from
  `single_wait_25us` to `single_wait_250us`.
- Kept `resident_native_completion_wave_fill_mode=single_wait`.
- Preserved explicit CLI overrides for
  `--resident-native-completion-wave-fill-us`.
- Added CLI preset coverage for the new default and explicit wait-us override.
- Updated resident CUDA runtime-preset smoke coverage to expect
  `single_wait_250us`.
- Updated Phase 2, integration, validation, and algorithm-source docs.

## Commands Run

- `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate682_wave_fill_probe\runs_20260626_180000\wave100 --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-native-completion-wave-fill-us 100`
- `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate682_wave_fill_probe\runs_20260626_180000\wave250 --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-native-completion-wave-fill-us 250`
- `.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py::test_resident_runtime_preset_throughput_v4_native_completion_applies_default_values tests/test_cli_smoke.py::test_resident_runtime_preset_defaults_to_throughput_v4_native_completion tests/test_cli_smoke.py::test_resident_runtime_preset_respects_explicit_completion_wave_fill_us tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_completion_runtime_preset_is_cli_opt_in`
- `.venv\Scripts\python.exe -m ruff check src/glass/cli.py tests/test_cli_smoke.py tests/test_resident_cuda_run.py`
- `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate682_wave_fill_default\runs_20260626_183000\default_250us --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
- `.venv\Scripts\glass.exe resident-runtime-compare --run queue32_default=C:\glass_runs\phase2_s2_gate680_completion_ring\runs_20260626_160000\queue32_default --run wave250_probe=C:\glass_runs\phase2_s2_gate682_wave_fill_probe\runs_20260626_180000\wave250 --run default_250us=C:\glass_runs\phase2_s2_gate682_wave_fill_default\runs_20260626_183000\default_250us --baseline-label queue32_default --out C:\glass_runs\phase2_s2_gate682_wave_fill_default\gate682_default_250us_runtime_compare.json --markdown C:\glass_runs\phase2_s2_gate682_wave_fill_default\gate682_default_250us_runtime_compare.md`
- `.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate680_completion_ring\runs_20260626_160000\queue32_default --candidate-run C:\glass_runs\phase2_s2_gate682_wave_fill_default\runs_20260626_183000\default_250us --out C:\glass_runs\phase2_s2_gate682_wave_fill_default\gate682_default_250us_regression_gate.json --markdown C:\glass_runs\phase2_s2_gate682_wave_fill_default\gate682_default_250us_regression_gate.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure`
- `.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate682_wave_fill_default\runs_20260626_183000\default_250us --out C:\glass_runs\phase2_s2_gate682_wave_fill_default\gate682_default_250us_phase2_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate682_wave_fill_default\gate682_default_250us_phase2_mainline_audit.md --min-lights 200 --min-active-frames 190 --max-masked-frames 10 --fail-on-not-green`
- Direct FITS comparison script against Gate680 25us baseline.
- `.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py::test_resident_runtime_preset_throughput_v4_native_completion_applies_default_values tests/test_cli_smoke.py::test_resident_runtime_preset_defaults_to_throughput_v4_native_completion tests/test_cli_smoke.py::test_resident_runtime_preset_respects_explicit_completion_wave_fill_us tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_completion_runtime_preset_is_cli_opt_in tests/test_resident_runtime_compare.py tests/test_resident_regression_gate.py tests/test_phase2_mainline_audit.py`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused CLI/resident CUDA tests: `4 passed in 1.50 s`.
- Focused gate/audit tests: `19 passed in 1.33 s`.
- Ruff: passed.
- Full pytest: `1424 passed in 66.38 s`.

## Real 200-Light Validation

- Baseline: `C:\glass_runs\phase2_s2_gate680_completion_ring\runs_20260626_160000\queue32_default`
- Probes:
  - `C:\glass_runs\phase2_s2_gate682_wave_fill_probe\runs_20260626_180000\wave100`
  - `C:\glass_runs\phase2_s2_gate682_wave_fill_probe\runs_20260626_180000\wave250`
- Promoted default candidate:
  `C:\glass_runs\phase2_s2_gate682_wave_fill_default\runs_20260626_183000\default_250us`
- Dataset plan:
  `C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json`
- Input lights: `200`
- Active/masked frames: `193 / 7`
- Candidate launched without an explicit wave-fill flag.
- Candidate wave-fill policy: `single_wait_250us`
- Candidate wave-fill strategy: `micro_poll_yield`
- Candidate total elapsed: `11.735124099999666 s`
- Baseline total elapsed: `12.245715199969709 s`
- Candidate/baseline elapsed ratio: `0.9583045096482967`
- Candidate `light_read_upload_calibrate`: `3.2267182000214234 s`
- Baseline `light_read_upload_calibrate`: `3.391568800085224 s`
- Candidate `light_h2d_calibrate_store`: `2.5775656999321654 s`
- Baseline `light_h2d_calibrate_store`: `2.750575099955313 s`
- Candidate native completion waves: `157`
- Baseline native completion waves: `183`
- Candidate multi-frame waves: `40`
- Baseline multi-frame waves: `17`
- Candidate max wave frames: `3`
- Baseline max wave frames: `2`
- Runtime compare best label: `default_250us`
- Phase 2 mainline audit: passed, failed checks `[]`
- Resident regression gate: passed, failed checks `[]`
- Direct FITS comparison: `resident_master_H.fits`, weight map, coverage map,
  low rejection map, high rejection map, and DQ map were bitwise identical.

## Artifacts

- Runtime compare:
  `C:\glass_runs\phase2_s2_gate682_wave_fill_default\gate682_default_250us_runtime_compare.json`
- Regression gate:
  `C:\glass_runs\phase2_s2_gate682_wave_fill_default\gate682_default_250us_regression_gate.json`
- Phase 2 mainline audit:
  `C:\glass_runs\phase2_s2_gate682_wave_fill_default\gate682_default_250us_phase2_mainline_audit.json`
- FITS result comparison:
  `C:\glass_runs\phase2_s2_gate682_wave_fill_default\gate682_result_compare_queue32_vs_default250.json`
- Candidate run directory:
  `C:\glass_runs\phase2_s2_gate682_wave_fill_default\runs_20260626_183000\default_250us`

## CUDA

- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- Driver: 596.21
- VRAM reported to GLASS: 97886 MiB

## Known Limitations

- This gate changes scheduling only; it does not implement a new native
  completion queue architecture or a cooperative reducer.
- The 250us default is validated on the current 200-light M38 H benchmark and
  remains overrideable for other storage/GPU combinations.
- The measured improvement depends on completion timing and storage behavior,
  so future default-promotion evidence should keep using the real 200-light
  regression and bitwise-output checks.

## Next Step

- Treat `single_wait_250us` as the new resident CUDA baseline and continue with
  a deeper native completion lane-fill/multi-buffer overlap gate: reduce
  single-frame waves further, increase lane utilization, and keep the same
  mainline/regression/FITS-comparison evidence chain.

## Clean-Room Compliance

- No external or proprietary implementation source was inspected, copied,
  summarized, or reworked.
- Validation used GLASS-owned code, GLASS-generated artifacts, and user-owned
  benchmark data only.
- Input image directories were treated as read-only.
