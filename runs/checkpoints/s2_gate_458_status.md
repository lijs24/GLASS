# S2-Gate 458 Status: Resident CUDA Histogram Source-DQ Threshold Reductions

## Gate

- Gate: S2-Gate 458
- Scope: Move opt-in `cosmetic_cuda` threshold statistics from sampled resident CPU sorting to resident CUDA histogram reductions.
- Status: passed
- Date: 2026-06-22 local

## Completed Work

- Added resident CUDA frame min/max/count, value histogram, and absolute-deviation histogram launchers.
- Added native `ResidentCalibratedStack.frame_histogram_robust_stats`.
- Exposed the method through `glass_cuda.ResidentCalibratedStack`.
- Updated `--resident-inline-source-dq cosmetic_cuda` to prefer resident histogram threshold statistics and fall back to Gate457 sampled stats only when the histogram API is unavailable.
- Updated resident source-DQ rows, resident strategy, resident pipeline artifacts, and CLI help to record:
  - `threshold_source=cuda_resident_histogram_median_mad_scalar`
  - `threshold_stats_domain=resident_calibrated_frame`
  - `materializes_host_frame=false`
  - `threshold_stats_bin_count`
  - `threshold_stats_histogram_download_bytes`
  - `threshold_stats_histogram_approximation`
- Kept default `resident_inline_source_dq=off` and CPU-mask `cosmetic` mode unchanged.

## Real 200-Light Results

- Primary accepted run: `C:\glass_runs\phase2_s2_gate_458_200\contract_parity_audit_required_20260622`
- Input: M38 H-alpha 200 lights, 20 bias, 20 dark, 20 flat.
- Resident inline source-DQ mode: `off` for real default-path regression.
- Internal GLASS run timing: `35.876992 s`.
- Outer PowerShell timing: `36.271231 s`.
- WBPP black-box elapsed: `1092.541 s`.
- Acceptance-audit speedup vs WBPP: `30.452414x`.
- Compare-report timing speedup vs WBPP: `30.121420x`.
- Integrated frames: `193/200`.
- Zero-weight quality-rejected frames: `7`.
- Compare:
  - shape match: true
  - coverage fraction: `0.9606526556`
  - coverage max: `193`
  - coverage median: `192`
  - RMS diff: `0.0016955712`
  - P99 absolute diff: `0.0004540284`
- Acceptance audit: passed.

## Commands Run

- `cmd.exe /c "call \"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat\" -arch=x64 -host_arch=x64 && .venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native"`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_source_dq.py tests/test_cuda_resident_stack.py::test_resident_stack_histogram_robust_stats_approximates_cpu_thresholds tests/test_cuda_resident_stack.py::test_resident_stack_sampled_robust_stats_matches_cpu_when_all_pixels_sampled tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_applies_inline_cosmetic_cuda_source_dq_without_mask_upload`
- `.\.venv\Scripts\python.exe -m ruff check src/glass/engine/resident_source_dq.py src/glass/engine/resident_cuda.py src/glass/engine/resident_source_dq_strategy.py src/glass/cli.py src/glass_cuda.py tests/test_resident_source_dq.py tests/test_cuda_resident_stack.py tests/test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_source_dq.py tests/test_resident_source_dq_strategy.py tests/test_cuda_resident_stack.py tests/test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe -m glass.cli run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_458_200\contract_parity_audit_required_20260622 --backend cuda --until-stage integration --memory-mode resident --resident-runtime-preset throughput-v1 --resident-h2d-mode pinned_ring --resident-output-maps audit --resident-registration similarity_cuda_triangle --resident-registration-quality-gate warn --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-rejection winsorized_sigma --resident-winsorized-mode fast_approx --integration-weighting none --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\.venv\Scripts\python.exe -m glass.cli compare --glass C:\glass_runs\phase2_s2_gate_458_200\contract_parity_audit_required_20260622\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_458_200\contract_parity_audit_required_20260622\s2_gate_458_compare.html --glass-time-seconds 36.2712312 --reference-time-seconds 1092.541 --glass-label GLASS-S2G458-contract-parity-audit --reference-label WBPP-blackbox --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_458_200\contract_parity_audit_required_20260622\integration\resident_coverage_map_H.fits --min-coverage 190`
- `.\.venv\Scripts\python.exe -m glass.cli resident-calibration-contract --run C:\glass_runs\phase2_s2_gate_458_200\contract_parity_audit_required_20260622 --out C:\glass_runs\phase2_s2_gate_458_200\contract_parity_audit_required_20260622\resident_calibration_contract_s2_gate_458.json --fail-on-failed`
- `.\.venv\Scripts\python.exe -m glass.cli resident-result-contract --run C:\glass_runs\phase2_s2_gate_458_200\contract_parity_audit_required_20260622 --out C:\glass_runs\phase2_s2_gate_458_200\contract_parity_audit_required_20260622\resident_result_contract_s2_gate_458.json --pixel-verify --fail-on-failed`
- `.\.venv\Scripts\python.exe -m glass.cli pipeline-contract --run C:\glass_runs\phase2_s2_gate_458_200\contract_parity_audit_required_20260622 --out C:\glass_runs\phase2_s2_gate_458_200\contract_parity_audit_required_20260622\pipeline_contract_s2_gate_458.json --pixel-verify --resident-calibration-contract-json C:\glass_runs\phase2_s2_gate_458_200\contract_parity_audit_required_20260622\resident_calibration_contract_s2_gate_458.json`
- `.\.venv\Scripts\python.exe -m glass.cli stack-engine-contract --run C:\glass_runs\phase2_s2_gate_458_200\contract_parity_audit_required_20260622 --out C:\glass_runs\phase2_s2_gate_458_200\contract_parity_audit_required_20260622\stack_engine_contract_s2_gate_458.json --expected-integration-engine cuda_resident_stack --resident-calibration-contract-json C:\glass_runs\phase2_s2_gate_458_200\contract_parity_audit_required_20260622\resident_calibration_contract_s2_gate_458.json --resident-result-contract-json C:\glass_runs\phase2_s2_gate_458_200\contract_parity_audit_required_20260622\resident_result_contract_s2_gate_458.json`
- `.\.venv\Scripts\python.exe -m glass.cli acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_458_200\contract_parity_audit_required_20260622 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_458_200\contract_parity_audit_required_20260622\s2_gate_458_compare.json --out C:\glass_runs\phase2_s2_gate_458_200\contract_parity_audit_required_20260622\phase2_contract_acceptance_audit_s2_gate_458.json --benchmark-contract benchmarks\phase2_m38_h_200_audit_maps_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate_458_200\contract_parity_audit_required_20260622\pipeline_contract_s2_gate_458.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate_458_200\contract_parity_audit_required_20260622\stack_engine_contract_s2_gate_458.json`

## Test Results

- Focused source-DQ/CUDA/CLI pytest: `12 passed`.
- Focused ruff: passed.
- Resident/source-DQ regression pytest: `116 passed`.
- Full pytest: `1087 passed in 47.85 s`.
- Native CUDA build: passed.
- Real 200-light acceptance audit: passed.

## Artifacts

- `runs/checkpoints/s2_gate_458_real_regression_summary.json`
- `runs/checkpoints/s2_gate_458_status.md`
- `C:\glass_runs\phase2_s2_gate_458_200\contract_parity_audit_required_20260622\s2_gate_458_compare.json`
- `C:\glass_runs\phase2_s2_gate_458_200\contract_parity_audit_required_20260622\s2_gate_458_compare.html`
- `C:\glass_runs\phase2_s2_gate_458_200\contract_parity_audit_required_20260622\resident_calibration_contract_s2_gate_458.json`
- `C:\glass_runs\phase2_s2_gate_458_200\contract_parity_audit_required_20260622\resident_result_contract_s2_gate_458.json`
- `C:\glass_runs\phase2_s2_gate_458_200\contract_parity_audit_required_20260622\pipeline_contract_s2_gate_458.json`
- `C:\glass_runs\phase2_s2_gate_458_200\contract_parity_audit_required_20260622\stack_engine_contract_s2_gate_458.json`
- `C:\glass_runs\phase2_s2_gate_458_200\contract_parity_audit_required_20260622\phase2_contract_acceptance_audit_s2_gate_458.json`

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
- Histogram thresholds are approximate: CUDA builds compact histograms, but the quantile bin scan remains host scalar over histogram bins.
- This gate does not change registration, warp, winsorized rejection, local normalization, or default frame admission.

## Next Gate

- Move source-DQ threshold extraction/application closer to a fully batched resident GPU path: batch histogram stats across frames, reduce host/device sync points, and measure opt-in `cosmetic_cuda` overhead on a heavy synthetic or real subset without weakening the 200-light contract-parity baseline.

## Clean-Room Compliance

- Compliant. This gate used GLASS source, GLASS synthetic fixtures, GLASS-generated artifacts, and user-owned 200-light outputs.
- Original image directories remained read-only.
- No official PixInsight/WBPP/PJSR implementation source was read, copied, summarized, or modified.
