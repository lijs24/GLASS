# S2-Gate 12 Status: Performance Regression Diagnostics

## Gate

S2-Gate 12: Performance Regression Diagnostics

## Completed

- Added `timing_baseline` to `benchmarks/phase2_m38_h_200_contract.json`.
- Added benchmark performance diagnostics that compare current resident CUDA
  stage timings with the Phase 1 release baseline.
- Acceptance audit now emits non-blocking `performance_regression` diagnostics
  in JSON and Markdown while preserving existing hard pass/fail checks.
- Fixed the Phase 2 recommended `/goal` text in
  `docs/phase2_algorithm_hardening.md` so the long goal lives in the document
  and the interactive goal can stay short.
- Updated `docs/algorithm_sources.md` with the benchmark diagnostics source log.

## Commands Run

- `.\.venv\Scripts\python.exe -m pytest -q tests\test_acceptance_audit.py`
- `.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_10_200\glass_flatfloor005_20260531_183101 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_10_200\glass_flatfloor005_20260531_183101\compare_vs_reference_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate_10_200\glass_flatfloor005_20260531_183101\phase2_contract_acceptance_audit_s2_gate_12.json --markdown C:\glass_runs\phase2_s2_gate_10_200\glass_flatfloor005_20260531_183101\phase2_contract_acceptance_audit_s2_gate_12.md --min-active-frames 190 --min-speedup 20 --benchmark-contract benchmarks\phase2_m38_h_200_contract.json`
- `.\.venv\Scripts\python.exe -m ruff check src\glass\report\benchmark_contract.py src\glass\report\acceptance_audit.py tests\test_acceptance_audit.py`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_import.py tests\test_cuda_device_info.py tests\test_cuda_smoke.py tests\test_gpu_calibration_vs_cpu.py tests\test_gpu_master_frames_vs_cpu.py tests\test_gpu_warp_vs_cpu.py tests\test_gpu_integration_vs_cpu.py`
- Queried `glass_cuda` device information from the project virtualenv.

## Test Results

- Focused acceptance audit tests: `4 passed`.
- Ruff focused check: `All checks passed`.
- Full pytest suite: `229 passed`.
- CUDA targeted tests: `17 passed`.
- Real 200-light acceptance audit: passed.

## Real Benchmark Diagnostic Output

Artifact:

- `C:\glass_runs\phase2_s2_gate_10_200\glass_flatfloor005_20260531_183101\phase2_contract_acceptance_audit_s2_gate_12.json`
- `C:\glass_runs\phase2_s2_gate_10_200\glass_flatfloor005_20260531_183101\phase2_contract_acceptance_audit_s2_gate_12.md`

Current audit status:

- Overall acceptance: passed.
- Speedup vs external reference: `28.004x`.
- Worst timing regression: `output_write`.
- `output_write`: `3.3451026000548154 s` vs baseline
  `0.9690760000376031 s`, factor `3.4518475330366405`.
- Next largest actionable stages:
  - `master_build_or_load`: factor `1.397289023294393`.
  - `light_read_upload_calibrate`: factor `1.3062102535294842`.
  - `resident_integration`: factor `1.1724520153085045`.

## CUDA

- CUDA extension built: yes.
- CUDA available: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.

## Known Limits

- Stage-level timing regressions are diagnostics, not hard acceptance failures.
  The hard runtime contract remains the total runtime envelope.
- The current editable-tree run is still slower than the Phase 1 release
  baseline, but remains inside the allowed total runtime contract.
- The next optimization should target output map writing first, then master
  build/load and the light read/upload/calibration pipeline.

## Next Step

S2-Gate 13 should recover runtime by reducing `output_write` overhead and then
attack master-frame loading/building and light read/upload/calibration. Keep the
200-light contract audit as the required regression guard.

## Clean-Room

Compliant. This gate uses GLASS artifacts, user-generated benchmark outputs,
and timing measurements only. No proprietary implementation source was used.
