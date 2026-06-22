# S2-Gate 459 Status: Resident CUDA Batched Histogram Source-DQ Thresholds

## Gate

- Gate: S2-Gate 459
- Scope: Batch opt-in `cosmetic_cuda` histogram threshold extraction across resident calibrated frames.
- Status: passed
- Date: 2026-06-22 local

## Completed Work

- Added native `ResidentCalibratedStack.frames_histogram_robust_stats`.
- Reused one set of resident histogram work buffers across all requested frames in the batch.
- Exposed the batch method through `glass_cuda.ResidentCalibratedStack`.
- Added `inline_cosmetic_thresholds_batch_from_resident_stack`.
- Updated the resident batch calibration path to compute `cosmetic_cuda` threshold infos once per calibrated batch and then apply the existing CUDA threshold mask kernel per frame.
- Extended source-DQ rows and component summaries with:
  - `threshold_stats_batch_native_method`
  - `threshold_stats_batch_frame_count`
  - `threshold_stats_batch_total_s`
  - `threshold_stats_batch_device_alloc_s`
  - `threshold_stats_batch_histogram_download_bytes`
  - `threshold_stats_batch_minmax_partial_download_bytes`
  - `threshold_stats_batch_reuses_device_work_buffers`
- Kept default `resident_inline_source_dq=off` unchanged.

## Real 200-Light Results

- Primary accepted run: `C:\glass_runs\phase2_s2_gate_459_200\contract_parity_audit_required_20260622`
- Input: M38 H-alpha 200 lights, 20 bias, 20 dark, 20 flat.
- Resident inline source-DQ mode: `off` for real default-path regression.
- Internal GLASS run timing: `36.545063 s`.
- Outer PowerShell timing: `36.957384 s`.
- WBPP black-box elapsed: `1092.541 s`.
- Acceptance-audit speedup vs WBPP: `29.895721x`.
- Compare-report timing speedup vs WBPP: `29.562184x`.
- Integrated frames: `193/200`.
- Zero-weight quality-rejected frames: `7`.
- Compare:
  - shape match: true
  - coverage fraction: `0.9608971115`
  - coverage max: `193`
  - coverage median: `192`
  - RMS diff: `0.0016637013`
  - P99 absolute diff: `0.0004515570`
- Acceptance audit: passed.

## Commands Run

- `cmd.exe /c "call \"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat\" -arch=x64 -host_arch=x64 && .venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native"`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_source_dq.py::test_inline_cosmetic_thresholds_batch_from_resident_stack_records_batch_histogram_stats tests/test_resident_source_dq.py::test_inline_cosmetic_thresholds_from_resident_stack_records_histogram_native_stats tests/test_cuda_resident_stack.py::test_resident_stack_batch_histogram_robust_stats_reuses_work_buffers tests/test_cuda_resident_stack.py::test_resident_stack_histogram_robust_stats_approximates_cpu_thresholds tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_applies_inline_cosmetic_cuda_source_dq_without_mask_upload`
- `.\.venv\Scripts\python.exe -m ruff check src/glass/engine/resident_source_dq.py src/glass/engine/resident_cuda.py src/glass_cuda.py tests/test_resident_source_dq.py tests/test_cuda_resident_stack.py tests/test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_source_dq.py tests/test_resident_source_dq_strategy.py tests/test_cuda_resident_stack.py tests/test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe -m glass.cli run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_459_200\contract_parity_audit_required_20260622 --backend cuda --until-stage integration --memory-mode resident --resident-runtime-preset throughput-v1 --resident-h2d-mode pinned_ring --resident-output-maps audit --resident-registration similarity_cuda_triangle --resident-registration-quality-gate warn --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-rejection winsorized_sigma --resident-winsorized-mode fast_approx --integration-weighting none --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\.venv\Scripts\python.exe -m glass.cli compare --glass C:\glass_runs\phase2_s2_gate_459_200\contract_parity_audit_required_20260622\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_459_200\contract_parity_audit_required_20260622\s2_gate_459_compare.html --glass-time-seconds 36.9573843 --reference-time-seconds 1092.541 --glass-label GLASS-S2G459-contract-parity-audit --reference-label WBPP-blackbox --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_459_200\contract_parity_audit_required_20260622\integration\resident_coverage_map_H.fits --min-coverage 190`
- `.\.venv\Scripts\python.exe -m glass.cli resident-calibration-contract --run C:\glass_runs\phase2_s2_gate_459_200\contract_parity_audit_required_20260622 --out C:\glass_runs\phase2_s2_gate_459_200\contract_parity_audit_required_20260622\resident_calibration_contract_s2_gate_459.json --fail-on-failed`
- `.\.venv\Scripts\python.exe -m glass.cli resident-result-contract --run C:\glass_runs\phase2_s2_gate_459_200\contract_parity_audit_required_20260622 --out C:\glass_runs\phase2_s2_gate_459_200\contract_parity_audit_required_20260622\resident_result_contract_s2_gate_459.json --pixel-verify --fail-on-failed`
- `.\.venv\Scripts\python.exe -m glass.cli pipeline-contract --run C:\glass_runs\phase2_s2_gate_459_200\contract_parity_audit_required_20260622 --out C:\glass_runs\phase2_s2_gate_459_200\contract_parity_audit_required_20260622\pipeline_contract_s2_gate_459.json --pixel-verify --resident-calibration-contract-json C:\glass_runs\phase2_s2_gate_459_200\contract_parity_audit_required_20260622\resident_calibration_contract_s2_gate_459.json`
- `.\.venv\Scripts\python.exe -m glass.cli stack-engine-contract --run C:\glass_runs\phase2_s2_gate_459_200\contract_parity_audit_required_20260622 --out C:\glass_runs\phase2_s2_gate_459_200\contract_parity_audit_required_20260622\stack_engine_contract_s2_gate_459.json --expected-integration-engine cuda_resident_stack --resident-calibration-contract-json C:\glass_runs\phase2_s2_gate_459_200\contract_parity_audit_required_20260622\resident_calibration_contract_s2_gate_459.json --resident-result-contract-json C:\glass_runs\phase2_s2_gate_459_200\contract_parity_audit_required_20260622\resident_result_contract_s2_gate_459.json`
- `.\.venv\Scripts\python.exe -m glass.cli acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_459_200\contract_parity_audit_required_20260622 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_459_200\contract_parity_audit_required_20260622\s2_gate_459_compare.json --out C:\glass_runs\phase2_s2_gate_459_200\contract_parity_audit_required_20260622\phase2_contract_acceptance_audit_s2_gate_459.json --benchmark-contract benchmarks\phase2_m38_h_200_audit_maps_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate_459_200\contract_parity_audit_required_20260622\pipeline_contract_s2_gate_459.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate_459_200\contract_parity_audit_required_20260622\stack_engine_contract_s2_gate_459.json`

## Test Results

- Focused source-DQ/CUDA/CLI pytest: `5 passed`.
- Focused ruff: passed.
- Resident/source-DQ regression pytest: `118 passed`.
- Full pytest: `1089 passed in 47.88 s`.
- Native CUDA build: passed.
- Real 200-light acceptance audit: passed.

## Artifacts

- `runs/checkpoints/s2_gate_459_real_regression_summary.json`
- `runs/checkpoints/s2_gate_459_status.md`
- `C:\glass_runs\phase2_s2_gate_459_200\contract_parity_audit_required_20260622\s2_gate_459_compare.json`
- `C:\glass_runs\phase2_s2_gate_459_200\contract_parity_audit_required_20260622\s2_gate_459_compare.html`
- `C:\glass_runs\phase2_s2_gate_459_200\contract_parity_audit_required_20260622\resident_calibration_contract_s2_gate_459.json`
- `C:\glass_runs\phase2_s2_gate_459_200\contract_parity_audit_required_20260622\resident_result_contract_s2_gate_459.json`
- `C:\glass_runs\phase2_s2_gate_459_200\contract_parity_audit_required_20260622\pipeline_contract_s2_gate_459.json`
- `C:\glass_runs\phase2_s2_gate_459_200\contract_parity_audit_required_20260622\stack_engine_contract_s2_gate_459.json`
- `C:\glass_runs\phase2_s2_gate_459_200\contract_parity_audit_required_20260622\phase2_contract_acceptance_audit_s2_gate_459.json`

## CUDA Status

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- CUDA toolkit used for native build: 13.2.

## Known Limitations

- `cosmetic_cuda` is opt-in and defaults to `off`.
- The real 200-light contract-parity run used `resident_inline_source_dq=off` because enabling cosmetic source-DQ intentionally changes sample admission.
- Batch histogram thresholds still synchronize and scan compact histogram bins per frame on the host.
- This gate does not change registration, warp, winsorized rejection, local normalization, or default frame admission.

## Next Gate

- Continue moving resident source-DQ toward fully GPU-resident batch execution by batching threshold-apply launches and/or moving quantile bin scans device-side, then measure opt-in `cosmetic_cuda` overhead on a heavier stack while preserving the 200-light default benchmark.

## Clean-Room Compliance

- Compliant. This gate used GLASS source, GLASS synthetic fixtures, GLASS-generated artifacts, and user-owned 200-light outputs.
- Original image directories remained read-only.
- No official PixInsight/WBPP/PJSR implementation source was read, copied, summarized, or modified.
