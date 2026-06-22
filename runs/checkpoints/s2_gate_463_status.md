# S2-Gate 463 Status: Chunked Warp Workspace Memory Planning

## Gate

- Gate: S2-Gate 463
- Scope: account for resident chunked warp temporary workspace in memory planning and reports.
- Status: passed
- Date: 2026-06-22 local

## Completed Work

- Added a Python resident memory model for native chunked matrix warp workspace.
- Mirrored the native preferred chunk capacity rule: `min(warp_frame_count, 8)`.
- Added planned and observed chunked workspace fields to resident artifacts and integration outputs.
- Added peak memory fields with and without chunked warp workspace:
  - `estimated_peak_without_chunked_warp_gib`
  - `estimated_peak_includes_chunked_warp_workspace`
  - `estimated_peak_gib`
- Exposed `triangle_warp_batch_dispatch` in resident registration artifacts.
- Added HTML resident summary columns for chunked warp dispatch, workspace model, capacity, workspace MiB, and peak memory terms.
- Fixed observed workspace accounting to trust native `batch_workspace_bytes` when present. `inverse_batch_bytes` is cumulative upload volume, not persistent workspace allocation.
- Updated tests for the pure memory model, resident CUDA artifact, and HTML report.
- Updated `docs/phase2_algorithm_hardening.md` and `docs/algorithm_sources.md`.

## Real 200-Light Results

- Run: `C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622`
- Input: M38 H-alpha, 200 lights, 20 bias, 20 dark, 20 flat.
- Backend: CUDA resident stack.
- Registration: `similarity_cuda_triangle`.
- Warp interpolation: `lanczos3`.
- Warp batch dispatch: `chunked`.
- Local normalization: off.
- Rejection: `winsorized_sigma`.
- Weighting: none.
- Integrated frames: `193/200`.
- Zero-weight / quality-rejected frames: `7`.
- Internal GLASS run timing: `37.830311 s`.
- Outer PowerShell timing: `38.237783 s`.
- WBPP black-box elapsed: `1092.541 s`.
- Acceptance-audit speedup vs WBPP: `28.880043x`.
- Compare-report speedup vs WBPP: `28.572289x`.
- Acceptance audit: `121/121` checks passed.

## Chunked Workspace Evidence

- `triangle_warp_batch_dispatch=chunked`
- `triangle_warp_batch_timing_model=native_chunked_batch_warp_scatter_one_sync`
- `triangle_warp_batch_frame_count=192`
- `triangle_warp_batch_fallback_frame_count=0`
- `triangle_warp_batch_native_chunk_frames=8`
- `triangle_warp_batch_native_chunk_count=24`
- `triangle_warp_batch_native_workspace_bytes=2466048352`
- Planned chunked workspace bytes: `2466048352`
- Observed chunked workspace bytes: `2466048352`
- Planned capacity frames: `8`
- Observed capacity frames: `8`
- Previous hot-set-only peak estimate: `47.311736 GiB`
- New peak estimate including chunked workspace: `49.608422 GiB`
- Chunked workspace contribution: `2.296687 GiB`

## Compare Metrics

- Shape match: true.
- Coverage fraction at `min_coverage=190`: `0.9609334611`.
- Coverage max: `193`.
- Coverage median: `192`.
- RMS diff: `0.0016886629`.
- P99 absolute diff: `0.0004594617`.

## Stage Timing Notes

- Master build/load: `12.934916 s`.
- Light read/upload/calibrate: `16.193770 s`.
- Light read/decode worker cumulative: `20.459233 s`.
- Light read wait wall: `2.183284 s`.
- Resident registration/warp: `3.506292 s`.
- Resident registration component accounted: `11.026490 s`.
- Resident integration: `0.402360 s`.
- Output write: `2.307586 s`.

## Commands Run

- `.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py src\glass\report\html_report.py tests\test_resident_cuda_run.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_resident_memory_estimate_includes_chunked_warp_workspace tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair tests\test_cli_smoke.py::test_cli_report_includes_resident_artifacts`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py tests\test_gpu_warp_vs_cpu.py tests\test_cuda_resident_stack.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m glass.cli run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622 --backend cuda --until-stage integration --memory-mode resident --resident-runtime-preset throughput-v1 --resident-h2d-mode pinned_ring --resident-output-maps audit --resident-registration similarity_cuda_triangle --resident-registration-quality-gate warn --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-rejection winsorized_sigma --resident-winsorized-mode fast_approx --integration-weighting none --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\.venv\Scripts\python.exe -m glass.cli compare --glass C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622\s2_gate_463_compare.html --glass-time-seconds 38.2377834 --reference-time-seconds 1092.541 --glass-label GLASS-S2G463-chunked-workspace-contract-parity --reference-label WBPP-blackbox --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622\integration\resident_coverage_map_H.fits --min-coverage 190`
- `.\.venv\Scripts\python.exe -m glass.cli resident-calibration-contract --run C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622 --out C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622\resident_calibration_contract_s2_gate_463.json --fail-on-failed`
- `.\.venv\Scripts\python.exe -m glass.cli resident-result-contract --run C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622 --out C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622\resident_result_contract_s2_gate_463.json --pixel-verify --fail-on-failed`
- `.\.venv\Scripts\python.exe -m glass.cli pipeline-contract --run C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622 --out C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622\pipeline_contract_s2_gate_463.json --pixel-verify --resident-calibration-contract-json C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622\resident_calibration_contract_s2_gate_463.json`
- `.\.venv\Scripts\python.exe -m glass.cli stack-engine-contract --run C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622 --out C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622\stack_engine_contract_s2_gate_463.json --expected-integration-engine cuda_resident_stack --resident-calibration-contract-json C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622\resident_calibration_contract_s2_gate_463.json --resident-result-contract-json C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622\resident_result_contract_s2_gate_463.json`
- `.\.venv\Scripts\python.exe -m glass.cli acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622\s2_gate_463_compare.json --out C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622\phase2_contract_acceptance_audit_s2_gate_463.json --benchmark-contract benchmarks\phase2_m38_h_200_audit_maps_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622\pipeline_contract_s2_gate_463.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622\stack_engine_contract_s2_gate_463.json`
- `.\.venv\Scripts\python.exe -m glass.cli report --run C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622 --acceptance-audit C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622\phase2_contract_acceptance_audit_s2_gate_463.json --out C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622\s2_gate_463_report.html`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --allow-cpu-only --json runs\checkpoints\s2_gate_463_doctor.json`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Ruff: passed.
- Focused tests: `3 passed`.
- Full pytest: `1093 passed in 53.22 s`.
- Resident calibration contract: passed.
- Resident result contract: passed.
- Pipeline contract: passed.
- StackEngine contract: passed.
- Acceptance audit: passed.

## Artifacts

- `runs/checkpoints/s2_gate_463_real_regression_summary.json`
- `runs/checkpoints/s2_gate_463_status.md`
- `runs/checkpoints/s2_gate_463_doctor.json`
- `C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622\resident_artifacts.json`
- `C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622\s2_gate_463_compare.json`
- `C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622\s2_gate_463_compare.html`
- `C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622\resident_calibration_contract_s2_gate_463.json`
- `C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622\resident_result_contract_s2_gate_463.json`
- `C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622\pipeline_contract_s2_gate_463.json`
- `C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622\stack_engine_contract_s2_gate_463.json`
- `C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622\phase2_contract_acceptance_audit_s2_gate_463.json`
- `C:\glass_runs\phase2_s2_gate_463_200\chunked_workspace_contract_parity_r3_20260622\s2_gate_463_report.html`

## CUDA Status

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Recommended package: cuda13.

## Known Limitations

- The new memory model reports preferred and observed chunk capacity, but it does not yet make a pre-run admission/fallback decision against a user-provided VRAM budget.
- The real regression keeps local normalization off and source-DQ off to preserve the current contract-parity benchmark path.
- The low-level `glass_cuda` resident stack wrapper still keeps `dispatch="loop"` as its direct API default for compatibility; high-level run/audit/engine default remains chunked.
- This gate changes planning/reporting only; it does not change calibration, star detection, registration fitting, warp interpolation, rejection, source-DQ, or integration pixel math.

## Next Gate

- Use the new resident peak terms for a pre-run VRAM admission scheduler that can choose resident full-frame, reduced chunk capacity, or tiled fallback mode before allocation.

## Clean-Room Compliance

- Compliant.
- Used GLASS code, GLASS synthetic/focused tests, GLASS artifacts, and user-owned M38 H-alpha benchmark outputs.
- Original image directories remained read-only.
- No official PixInsight/WBPP/PJSR implementation source was read, copied, summarized, or modified.
