# S2-Gate 464 Status: Resident VRAM Admission Scheduler

## Gate

- Gate: S2-Gate 464
- Scope: add a pre-run resident CUDA VRAM admission scheduler using the Gate463 chunked-warp workspace model.
- Status: passed
- Date: 2026-06-22 local

## Completed Work

- Added `build_resident_memory_admission` to estimate resident CUDA peak VRAM before large allocation.
- Grouped light frames by filter and shape, then estimated each group's calibrated-stack, output-map, and chunked-warp workspace demand.
- Added capacity options for preferred and reduced chunked-warp capacities.
- Made explicit `--vram-budget-gb` a blocking budget for resident `glass run` and `glass audit`.
- Recorded detected device-total safety budget as evidence when no explicit budget is supplied.
- Inserted a timed `resident_memory_admission` stage before source-DQ strategy and resident CUDA allocation.
- Wrote `resident_memory_admission.json` and attached it to `run_state.json`.
- Added failed-state handling for explicit budget admission failures.
- Added `--vram-budget-gb` and `--ram-budget-gb` to `glass audit`.
- Fixed admission frame-exclusion accounting to use the same id/file-name/stem token matching used by resident execution.
- Added tests for reduced-chunk recommendations, explicit-budget blocking, stem-token exclusion, CLI failure state, and existing resident/report smoke paths.
- Updated `docs/phase2_algorithm_hardening.md` and `docs/algorithm_sources.md`.

## CUDA Status

- CUDA available: true.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Device memory: 97886 MiB.
- Driver version from device list: 596.21.

## Real 200-Light Results

- Run: `C:\glass_runs\phase2_s2_gate_464_200\memory_admission_contract_parity_r2_20260622`
- Input: M38 H-alpha, 200 lights, 20 bias, 20 dark, 20 flat.
- Backend: CUDA resident stack.
- Registration: `similarity_cuda_triangle`.
- Warp interpolation: `lanczos3`.
- Warp batch dispatch: `chunked`.
- Local normalization: off.
- Rejection: `winsorized_sigma`.
- Weighting: none.
- Integrated / weighted frames: `193/200`.
- Zero-weight / quality-rejected frames: `7`.
- Internal GLASS run timing: `37.538072 s`.
- Outer PowerShell timing: `37.950770 s`.
- WBPP black-box elapsed: `1092.541 s`.
- Acceptance-audit speedup vs WBPP: `29.104877x`.
- Acceptance audit: passed.

## Admission Evidence

- Artifact: `C:\glass_runs\phase2_s2_gate_464_200\memory_admission_contract_parity_r2_20260622\resident_memory_admission.json`
- Status: `passed`.
- Blocking: false.
- Recommended action: `resident_full_frame`.
- Budget source: `device_total_memory_safety_fraction`.
- Budget: `86.032617 GiB`.
- Estimated peak: `49.608422 GiB`.
- Headroom: `36.424195 GiB`.
- Light frame count: `200`.
- Planned active frame count after excludes: `193`.
- Planned warp frame count: `192`.
- Preferred chunk capacity: `8`.
- Planned chunked-warp workspace: `2466048352` bytes.
- Admission stage timing: `0.003681 s`.

## Chunked Warp Evidence

- `triangle_warp_batch_dispatch=chunked`
- `triangle_warp_batch_timing_model=native_chunked_batch_warp_scatter_one_sync`
- `triangle_warp_batch_frame_count=192`
- `triangle_warp_batch_native_chunk_frames=8`
- `triangle_warp_batch_native_chunk_count=24`
- `triangle_warp_batch_native_workspace_bytes=2466048352`
- Observed workspace bytes matched the planned workspace bytes.
- Resident registration warp timing: `3.351694 s`.

## Compare Metrics

- Compare report: `C:\glass_runs\phase2_s2_gate_464_200\memory_admission_contract_parity_r2_20260622\s2_gate_464_compare.html`
- Compare JSON: `C:\glass_runs\phase2_s2_gate_464_200\memory_admission_contract_parity_r2_20260622\s2_gate_464_compare.json`
- Shape match: true.
- Coverage fraction at `min_coverage=190`: `0.9609726007`.
- Compared pixels: `59245114`.
- RMS diff: `0.0016529161`.
- P99 absolute diff: `0.0004501914`.

## Contract Results

- Resident calibration contract: passed.
- Resident result contract: passed with pixel verification.
- Pipeline contract: passed with pixel verification.
- StackEngine contract: passed.
- StackEngine default-promotion ready: true.
- Acceptance audit: passed.
- HTML report: `C:\glass_runs\phase2_s2_gate_464_200\memory_admission_contract_parity_r2_20260622\s2_gate_464_report.html`

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m ruff check src\\glass\\engine\\resident_cuda.py src\\glass\\cli.py tests\\test_resident_cuda_run.py tests\\test_cli_smoke.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_resident_cuda_run.py::test_resident_memory_admission_recommends_reduced_chunk_capacity tests\\test_resident_cuda_run.py::test_resident_memory_admission_counts_stem_excludes tests\\test_resident_cuda_run.py::test_resident_memory_admission_blocks_explicit_budget tests\\test_cli_smoke.py::test_cli_resident_run_blocks_explicit_low_vram_budget`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_resident_cuda_run.py tests\\test_cli_smoke.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_gpu_warp_vs_cpu.py tests\\test_cuda_resident_stack.py`
- `.\\.venv\\Scripts\\python.exe -m glass.cli run --plan C:\\gpwbpp_runs\\final_m38_h_200\\processing_plan.json --out C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622 --backend cuda --until-stage integration --memory-mode resident --resident-runtime-preset throughput-v1 --resident-h2d-mode pinned_ring --resident-output-maps audit --resident-registration similarity_cuda_triangle --resident-registration-quality-gate warn --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-rejection winsorized_sigma --resident-winsorized-mode fast_approx --integration-weighting none --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\\.venv\\Scripts\\python.exe -m glass.cli compare --glass C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622\\integration\\resident_master_H.fits --reference C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\master\\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622\\s2_gate_464_compare.html --glass-time-seconds 37.9507698 --reference-time-seconds 1092.541 --glass-label GLASS-S2G464-memory-admission-contract-parity --reference-label WBPP-blackbox --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622\\integration\\resident_coverage_map_H.fits --min-coverage 190`
- `.\\.venv\\Scripts\\python.exe -m glass.cli resident-calibration-contract --run C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622 --out C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622\\s2_gate_464_resident_calibration_contract.json --markdown C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622\\s2_gate_464_resident_calibration_contract.md --fail-on-failed`
- `.\\.venv\\Scripts\\python.exe -m glass.cli resident-result-contract --run C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622 --out C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622\\s2_gate_464_resident_result_contract.json --markdown C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622\\s2_gate_464_resident_result_contract.md --pixel-verify --pixel-verify-tile-size 2048 --fail-on-failed`
- `.\\.venv\\Scripts\\python.exe -m glass.cli pipeline-contract --run C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622 --out C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622\\s2_gate_464_pipeline_contract.json --markdown C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622\\s2_gate_464_pipeline_contract.md --pixel-verify --pixel-verify-tile-size 2048 --resident-calibration-contract-json C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622\\s2_gate_464_resident_calibration_contract.json`
- `.\\.venv\\Scripts\\python.exe -m glass.cli stack-engine-contract --run C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622 --out C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622\\s2_gate_464_stack_engine_contract.json --markdown C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622\\s2_gate_464_stack_engine_contract.md --scope all --expected-integration-engine cuda_resident_stack --resident-calibration-contract-json C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622\\s2_gate_464_resident_calibration_contract.json --resident-result-contract-json C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622\\s2_gate_464_resident_result_contract.json --require-default-ready`
- `.\\.venv\\Scripts\\python.exe -m glass.cli acceptance-audit --manifest C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622\\manifest.json --glass-run C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622 --wbpp-result C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\wbpp_blackbox_result.json --compare-json C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622\\s2_gate_464_compare.json --out C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622\\s2_gate_464_acceptance_audit.json --markdown C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622\\s2_gate_464_acceptance_audit.md --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 2.0 --min-coverage-fraction 0.95 --max-rms-diff 0.01 --max-abs-diff-p99 0.01 --benchmark-contract benchmarks\\phase2_m38_h_200_audit_maps_contract.json --pipeline-contract-json C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622\\s2_gate_464_pipeline_contract.json --stack-engine-contract-json C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622\\s2_gate_464_stack_engine_contract.json`
- `.\\.venv\\Scripts\\python.exe -m glass.cli report --run C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622 --out C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622\\s2_gate_464_report.html --acceptance-audit C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622\\s2_gate_464_acceptance_audit.json --stack-engine-contract C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622\\s2_gate_464_stack_engine_contract.json --pipeline-contract C:\\glass_runs\\phase2_s2_gate_464_200\\memory_admission_contract_parity_r2_20260622\\s2_gate_464_pipeline_contract.json`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`

## Test Results

- Ruff: passed.
- Focused admission tests: `4 passed in 0.72s`.
- Resident/CLI suite: `102 passed in 14.39s`.
- GPU warp/resident stack suite: `51 passed in 0.60s`.
- Full pytest: `1097 passed in 48.22s`.

## Known Limitations

- Reduced chunk capacity is currently an admission recommendation and explicit-budget guard; native batch warp capacity selection remains allocator-driven at runtime.
- With no explicit `--vram-budget-gb`, the device-total safety budget is recorded as evidence and does not block a run.
- This gate does not change pixel math, registration math, rejection math, or source-DQ behavior.

## Next Step

- S2-Gate465 should plumb the admitted/recommended chunk capacity into the resident chunked warp dispatcher or add an explicit reduced-capacity runtime option, then validate the same 200-light contract.

## Clean-Room Compliance

- Compliant.
- No official PixInsight WBPP/PJSR source was read, copied, summarized, or reworked.
- WBPP was used only through user-generated black-box timing and output artifacts.
- Input image directories were treated as read-only.
