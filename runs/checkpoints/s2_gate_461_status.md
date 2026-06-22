# S2-Gate 461 Status: Resident Triangle Translation Warp Batch Closure

## Gate

- Gate: S2-Gate 461
- Scope: Make the real `similarity_cuda_triangle` resident path batch translation-like matrix warps instead of short-circuiting them into per-frame warp calls.
- Status: passed
- Date: 2026-06-22 local

## Completed Work

- Updated `_apply_resident_registration_matrix_batch` so translation-like matrices remain in the native matrix batch path when batch support is available.
- Changed the non-pixel-refine `similarity_cuda_triangle` main loop to defer accepted frame warps until after registration has collected the batch.
- Added per-frame warning backfill for batch warp provenance:
  - `resident_registration_application=matrix_lanczos3_batch`
  - `triangle_warp_batch=true`
  - `triangle_warp_batch_timing_model=native_loop_batched_inverse_one_sync`
- Added a helper-level regression test proving translation-like matrices no longer bypass native batch warp.
- Kept registration matrix estimation, star detection, descriptor fitting, interpolation math, frame admission, source-DQ, and rejection unchanged.

## Real 200-Light Results

- Primary accepted run: `C:\glass_runs\phase2_s2_gate_461_200\batched_triangle_warp_contract_parity_20260622`
- Input: M38 H-alpha 200 lights, 20 bias, 20 dark, 20 flat.
- Resident inline source-DQ mode: `off`.
- Internal GLASS run timing: `36.563496 s`.
- Outer PowerShell timing: `36.964415 s`.
- WBPP black-box elapsed: `1092.541 s`.
- Acceptance-audit speedup vs WBPP: `29.880649x`.
- Compare-report timing speedup vs WBPP: `29.556562x`.
- Integrated frames: `193/200`.
- Zero-weight quality-rejected frames: `7`.
- Estimated resident peak VRAM: `47.311736 GiB`.
- Compare:
  - shape match: true
  - coverage fraction: `0.9610885108`
  - coverage max: `193`
  - coverage median: `192`
  - RMS diff: `0.0017102906`
  - P99 absolute diff: `0.0004569016`
- Acceptance audit: passed.

## Warp Evidence

- `triangle_warp_batch=true`
- `triangle_warp_batch_mode=native_matrix_lanczos3_frames`
- `triangle_warp_batch_timing_model=native_loop_batched_inverse_one_sync`
- `triangle_warp_batch_frame_count=192`
- `triangle_warp_batch_fallback_frame_count=0`
- `triangle_warp_batch_native_inverse_upload_mode=single_device_batch`
- `triangle_warp_batch_native_total_s=0.9305689`
- `triangle_warp_batch_native_sync_s=0.9222798`
- Registration warnings now contain 192 `resident_registration_application=matrix_lanczos3_batch` entries.
- Measured warp segment improved from Gate460's `4.386194 s` to `3.566975 s`.

## Stage Timing Notes

- Total internal timing: `36.563496 s`.
- Master build/load: `12.068745 s`.
- Resident light read/upload/calibrate wall: `15.340621 s`.
- Native FITS file-read worker cumulative: `20.591341 s`.
- Consumer read wait wall: `2.209258 s`.
- CUDA calibration store: `0.803243 s`.
- Resident registration warp: `3.566975 s`.
- Resident registration component accounted: `11.139882 s`.
- Resident integration: `0.456845 s`.
- Output write: `2.399752 s`.
- The total wall clock remains dominated by I/O/master build/orchestration variance even though the warp segment improved.

## Commands Run

- `.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_resident_registration_matrix_batch_keeps_translation_matrices_batched`
- `.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py tests\test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_gpu_warp_vs_cpu.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_resident_registration_matrix_batch_keeps_translation_matrices_batched tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair tests/test_resident_cuda_run.py::test_cli_resident_cuda_triangle_default_uses_gpu_centroid_without_pixel_refine tests/test_resident_cuda_run.py::test_cli_resident_cuda_auto_dispatch_keeps_lanczos_rejection_on_stack`
- `.\.venv\Scripts\python.exe -m glass.cli run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_461_200\batched_triangle_warp_contract_parity_20260622 --backend cuda --until-stage integration --memory-mode resident --resident-runtime-preset throughput-v1 --resident-h2d-mode pinned_ring --resident-output-maps audit --resident-registration similarity_cuda_triangle --resident-registration-quality-gate warn --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-rejection winsorized_sigma --resident-winsorized-mode fast_approx --integration-weighting none --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\.venv\Scripts\python.exe -m glass.cli compare --glass C:\glass_runs\phase2_s2_gate_461_200\batched_triangle_warp_contract_parity_20260622\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_461_200\batched_triangle_warp_contract_parity_20260622\s2_gate_461_compare.html --glass-time-seconds 36.9644145 --reference-time-seconds 1092.541 --glass-label GLASS-S2G461-batched-warp-contract-parity --reference-label WBPP-blackbox --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_461_200\batched_triangle_warp_contract_parity_20260622\integration\resident_coverage_map_H.fits --min-coverage 190`
- `.\.venv\Scripts\python.exe -m glass.cli resident-calibration-contract --run C:\glass_runs\phase2_s2_gate_461_200\batched_triangle_warp_contract_parity_20260622 --out C:\glass_runs\phase2_s2_gate_461_200\batched_triangle_warp_contract_parity_20260622\resident_calibration_contract_s2_gate_461.json --fail-on-failed`
- `.\.venv\Scripts\python.exe -m glass.cli resident-result-contract --run C:\glass_runs\phase2_s2_gate_461_200\batched_triangle_warp_contract_parity_20260622 --out C:\glass_runs\phase2_s2_gate_461_200\batched_triangle_warp_contract_parity_20260622\resident_result_contract_s2_gate_461.json --pixel-verify --fail-on-failed`
- `.\.venv\Scripts\python.exe -m glass.cli pipeline-contract --run C:\glass_runs\phase2_s2_gate_461_200\batched_triangle_warp_contract_parity_20260622 --out C:\glass_runs\phase2_s2_gate_461_200\batched_triangle_warp_contract_parity_20260622\pipeline_contract_s2_gate_461.json --pixel-verify --resident-calibration-contract-json C:\glass_runs\phase2_s2_gate_461_200\batched_triangle_warp_contract_parity_20260622\resident_calibration_contract_s2_gate_461.json`
- `.\.venv\Scripts\python.exe -m glass.cli stack-engine-contract --run C:\glass_runs\phase2_s2_gate_461_200\batched_triangle_warp_contract_parity_20260622 --out C:\glass_runs\phase2_s2_gate_461_200\batched_triangle_warp_contract_parity_20260622\stack_engine_contract_s2_gate_461.json --expected-integration-engine cuda_resident_stack --resident-calibration-contract-json C:\glass_runs\phase2_s2_gate_461_200\batched_triangle_warp_contract_parity_20260622\resident_calibration_contract_s2_gate_461.json --resident-result-contract-json C:\glass_runs\phase2_s2_gate_461_200\batched_triangle_warp_contract_parity_20260622\resident_result_contract_s2_gate_461.json`
- `.\.venv\Scripts\python.exe -m glass.cli acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_461_200\batched_triangle_warp_contract_parity_20260622 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_461_200\batched_triangle_warp_contract_parity_20260622\s2_gate_461_compare.json --out C:\glass_runs\phase2_s2_gate_461_200\batched_triangle_warp_contract_parity_20260622\phase2_contract_acceptance_audit_s2_gate_461.json --benchmark-contract benchmarks\phase2_m38_h_200_audit_maps_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate_461_200\batched_triangle_warp_contract_parity_20260622\pipeline_contract_s2_gate_461.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate_461_200\batched_triangle_warp_contract_parity_20260622\stack_engine_contract_s2_gate_461.json`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_gpu_warp_vs_cpu.py tests/test_cuda_resident_stack.py`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused helper pytest: `1 passed`.
- Focused ruff: passed.
- Resident CUDA run pytest: `66 passed in 8.78 s`.
- GPU warp/resident stack pytest: `51 passed in 0.50 s`.
- Full pytest: `1092 passed in 52.06 s`.
- Real 200-light acceptance audit: passed.

## Artifacts

- `runs/checkpoints/s2_gate_461_real_regression_summary.json`
- `runs/checkpoints/s2_gate_461_status.md`
- `C:\glass_runs\phase2_s2_gate_461_200\batched_triangle_warp_contract_parity_20260622\s2_gate_461_compare.json`
- `C:\glass_runs\phase2_s2_gate_461_200\batched_triangle_warp_contract_parity_20260622\s2_gate_461_compare.html`
- `C:\glass_runs\phase2_s2_gate_461_200\batched_triangle_warp_contract_parity_20260622\resident_calibration_contract_s2_gate_461.json`
- `C:\glass_runs\phase2_s2_gate_461_200\batched_triangle_warp_contract_parity_20260622\resident_result_contract_s2_gate_461.json`
- `C:\glass_runs\phase2_s2_gate_461_200\batched_triangle_warp_contract_parity_20260622\pipeline_contract_s2_gate_461.json`
- `C:\glass_runs\phase2_s2_gate_461_200\batched_triangle_warp_contract_parity_20260622\stack_engine_contract_s2_gate_461.json`
- `C:\glass_runs\phase2_s2_gate_461_200\batched_triangle_warp_contract_parity_20260622\phase2_contract_acceptance_audit_s2_gate_461.json`

## CUDA Status

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- CUDA toolkit used by current native extension: 13.2.

## Known Limitations

- The default warp batch dispatch remains `loop`; this gate does not yet promote the chunked scatter batch warp path.
- Total 200-light runtime remained in the same 36-second band because I/O, master build/load, and orchestration variance still dominate wall clock.
- This gate does not change star detection, descriptor fitting, matrix estimation, rejection, local normalization, source-DQ, or frame admission.

## Next Gate

- Evaluate and harden `--resident-warp-batch-dispatch chunked` against the same 200-light contract, then promote it only if it preserves numerical contracts and improves or explains runtime.

## Clean-Room Compliance

- Compliant. This gate used GLASS source, GLASS synthetic fixtures, GLASS-generated artifacts, and user-owned 200-light outputs.
- Original image directories remained read-only.
- No official PixInsight/WBPP/PJSR implementation source was read, copied, summarized, or modified.
