# S2-Gate 462 Status: Resident Chunked Warp Default Promotion

## Gate

- Gate: S2-Gate 462
- Scope: Promote resident matrix batch warp dispatch from loop-batched to chunked by default.
- Status: passed
- Date: 2026-06-22 local

## Completed Work

- Ran an explicit `--resident-warp-batch-dispatch chunked` 200-light probe and verified compare/contracts.
- Changed `glass run`, `glass audit`, and `run_resident_calibration_integration` defaults to `chunked`.
- Kept the low-level `glass_cuda.ResidentCalibratedStack.apply_matrix_*_frames(..., dispatch="loop")` wrapper default unchanged for direct API compatibility.
- Updated resident CLI tests to assert default chunked warp provenance:
  - `native_chunked_batch_warp_scatter_one_sync`
  - `chunked_device_batch`
  - chunk workspace/output/coverage bytes
  - warp/coverage/scatter kernel launch counts
- Verified a no-explicit-dispatch 200-light run records `warp_batch_dispatch=chunked`.

## Real 200-Light Results

- Primary accepted default run: `C:\glass_runs\phase2_s2_gate_462_200\default_chunked_contract_parity_20260622`
- Explicit chunked probe: `C:\glass_runs\phase2_s2_gate_462_200\chunked_warp_probe_20260622`
- Input: M38 H-alpha 200 lights, 20 bias, 20 dark, 20 flat.
- Resident inline source-DQ mode: `off`.
- Internal GLASS run timing: `36.018981 s`.
- Outer PowerShell timing: `36.420235 s`.
- WBPP black-box elapsed: `1092.541 s`.
- Acceptance-audit speedup vs WBPP: `30.332368x`.
- Compare-report timing speedup vs WBPP: `29.998187x`.
- Integrated frames: `193/200`.
- Zero-weight quality-rejected frames: `7`.
- Estimated resident peak VRAM: `47.311736 GiB`.
- Compare:
  - shape match: true
  - coverage fraction: `0.9609903295`
  - coverage max: `193`
  - coverage median: `192`
  - RMS diff: `0.0016983322`
  - P99 absolute diff: `0.0004534698`
- Acceptance audit: passed.

## Chunked Warp Evidence

- `warp_batch_dispatch=chunked`
- `triangle_warp_batch=true`
- `triangle_warp_batch_mode=native_matrix_lanczos3_frames`
- `triangle_warp_batch_timing_model=native_chunked_batch_warp_scatter_one_sync`
- `triangle_warp_batch_frame_count=192`
- `triangle_warp_batch_fallback_frame_count=0`
- `triangle_warp_batch_native_chunk_frames=8`
- `triangle_warp_batch_native_chunk_count=24`
- `triangle_warp_batch_native_warp_kernel_launches=24`
- `triangle_warp_batch_native_coverage_reduce_kernel_launches=24`
- `triangle_warp_batch_native_scatter_kernel_launches=24`
- `triangle_warp_batch_native_workspace_bytes=2466048352`
- `triangle_warp_batch_native_total_s=0.9816314`
- `triangle_warp_batch_native_sync_s=0.9584914`
- Measured warp segment improved from Gate461 loop-batched `3.566975 s` to default chunked `3.359520 s`.

## Stage Timing Notes

- Total internal timing: `36.018981 s`.
- Master build/load: `11.429790 s`.
- Resident light read/upload/calibrate wall: `14.666512 s`.
- Native FITS file-read worker cumulative: `20.429808 s`.
- Consumer read wait wall: `2.187345 s`.
- CUDA calibration store: `0.798585 s`.
- Resident registration warp: `3.359520 s`.
- Resident registration component accounted: `10.752467 s`.
- Resident integration: `0.486308 s`.
- Output write: `2.215231 s`.

## Commands Run

- `.\.venv\Scripts\python.exe -m pytest -q tests/test_gpu_warp_vs_cpu.py::test_resident_stack_matrix_bilinear_batch_warp_matches_cpu_reference tests/test_gpu_warp_vs_cpu.py::test_resident_stack_matrix_lanczos3_batch_warp_matches_cpu_reference tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair`
- `.\.venv\Scripts\python.exe -m glass.cli run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_462_200\chunked_warp_probe_20260622 --backend cuda --until-stage integration --memory-mode resident --resident-runtime-preset throughput-v1 --resident-h2d-mode pinned_ring --resident-output-maps audit --resident-registration similarity_cuda_triangle --resident-registration-quality-gate warn --resident-warp-interpolation lanczos3 --resident-warp-batch-dispatch chunked --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-rejection winsorized_sigma --resident-winsorized-mode fast_approx --integration-weighting none --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\.venv\Scripts\python.exe -m glass.cli compare --glass C:\glass_runs\phase2_s2_gate_462_200\chunked_warp_probe_20260622\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_462_200\chunked_warp_probe_20260622\s2_gate_462_compare.html --glass-time-seconds 36.8736654 --reference-time-seconds 1092.541 --glass-label GLASS-S2G462-chunked-warp-probe --reference-label WBPP-blackbox --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_462_200\chunked_warp_probe_20260622\integration\resident_coverage_map_H.fits --min-coverage 190`
- `.\.venv\Scripts\python.exe -m glass.cli acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_462_200\chunked_warp_probe_20260622 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_462_200\chunked_warp_probe_20260622\s2_gate_462_compare.json --out C:\glass_runs\phase2_s2_gate_462_200\chunked_warp_probe_20260622\phase2_contract_acceptance_audit_s2_gate_462.json --benchmark-contract benchmarks\phase2_m38_h_200_audit_maps_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate_462_200\chunked_warp_probe_20260622\pipeline_contract_s2_gate_462.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate_462_200\chunked_warp_probe_20260622\stack_engine_contract_s2_gate_462.json`
- `.\.venv\Scripts\python.exe -m ruff check src\glass\cli.py src\glass\engine\resident_cuda.py tests\test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair tests/test_resident_cuda_run.py::test_cli_resident_cuda_triangle_default_uses_gpu_centroid_without_pixel_refine tests/test_resident_cuda_run.py::test_cli_resident_cuda_auto_dispatch_keeps_lanczos_rejection_on_stack tests/test_gpu_warp_vs_cpu.py::test_resident_stack_matrix_lanczos3_batch_warp_matches_cpu_reference`
- `.\.venv\Scripts\python.exe -m glass.cli run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_462_200\default_chunked_contract_parity_20260622 --backend cuda --until-stage integration --memory-mode resident --resident-runtime-preset throughput-v1 --resident-h2d-mode pinned_ring --resident-output-maps audit --resident-registration similarity_cuda_triangle --resident-registration-quality-gate warn --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-rejection winsorized_sigma --resident-winsorized-mode fast_approx --integration-weighting none --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\.venv\Scripts\python.exe -m glass.cli compare --glass C:\glass_runs\phase2_s2_gate_462_200\default_chunked_contract_parity_20260622\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_462_200\default_chunked_contract_parity_20260622\s2_gate_462_default_compare.html --glass-time-seconds 36.4202346 --reference-time-seconds 1092.541 --glass-label GLASS-S2G462-default-chunked-contract-parity --reference-label WBPP-blackbox --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_462_200\default_chunked_contract_parity_20260622\integration\resident_coverage_map_H.fits --min-coverage 190`
- `.\.venv\Scripts\python.exe -m glass.cli resident-calibration-contract --run C:\glass_runs\phase2_s2_gate_462_200\default_chunked_contract_parity_20260622 --out C:\glass_runs\phase2_s2_gate_462_200\default_chunked_contract_parity_20260622\resident_calibration_contract_s2_gate_462_default.json --fail-on-failed`
- `.\.venv\Scripts\python.exe -m glass.cli resident-result-contract --run C:\glass_runs\phase2_s2_gate_462_200\default_chunked_contract_parity_20260622 --out C:\glass_runs\phase2_s2_gate_462_200\default_chunked_contract_parity_20260622\resident_result_contract_s2_gate_462_default.json --pixel-verify --fail-on-failed`
- `.\.venv\Scripts\python.exe -m glass.cli pipeline-contract --run C:\glass_runs\phase2_s2_gate_462_200\default_chunked_contract_parity_20260622 --out C:\glass_runs\phase2_s2_gate_462_200\default_chunked_contract_parity_20260622\pipeline_contract_s2_gate_462_default.json --pixel-verify --resident-calibration-contract-json C:\glass_runs\phase2_s2_gate_462_200\default_chunked_contract_parity_20260622\resident_calibration_contract_s2_gate_462_default.json`
- `.\.venv\Scripts\python.exe -m glass.cli stack-engine-contract --run C:\glass_runs\phase2_s2_gate_462_200\default_chunked_contract_parity_20260622 --out C:\glass_runs\phase2_s2_gate_462_200\default_chunked_contract_parity_20260622\stack_engine_contract_s2_gate_462_default.json --expected-integration-engine cuda_resident_stack --resident-calibration-contract-json C:\glass_runs\phase2_s2_gate_462_200\default_chunked_contract_parity_20260622\resident_calibration_contract_s2_gate_462_default.json --resident-result-contract-json C:\glass_runs\phase2_s2_gate_462_200\default_chunked_contract_parity_20260622\resident_result_contract_s2_gate_462_default.json`
- `.\.venv\Scripts\python.exe -m glass.cli acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_462_200\default_chunked_contract_parity_20260622 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_462_200\default_chunked_contract_parity_20260622\s2_gate_462_default_compare.json --out C:\glass_runs\phase2_s2_gate_462_200\default_chunked_contract_parity_20260622\phase2_contract_acceptance_audit_s2_gate_462_default.json --benchmark-contract benchmarks\phase2_m38_h_200_audit_maps_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate_462_200\default_chunked_contract_parity_20260622\pipeline_contract_s2_gate_462_default.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate_462_200\default_chunked_contract_parity_20260622\stack_engine_contract_s2_gate_462_default.json`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_gpu_warp_vs_cpu.py tests/test_cuda_resident_stack.py tests/test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused default chunked pytest: `4 passed`.
- Focused ruff: passed.
- Resident CUDA run pytest: `66 passed in 8.78 s`.
- GPU warp/resident stack/CLI smoke pytest: `82 passed in 6.21 s`.
- Full pytest: `1092 passed in 47.56 s`.
- Explicit chunked 200-light acceptance audit: passed.
- Default chunked 200-light acceptance audit: passed.

## Artifacts

- `runs/checkpoints/s2_gate_462_real_regression_summary.json`
- `runs/checkpoints/s2_gate_462_status.md`
- `C:\glass_runs\phase2_s2_gate_462_200\chunked_warp_probe_20260622\s2_gate_462_compare.json`
- `C:\glass_runs\phase2_s2_gate_462_200\chunked_warp_probe_20260622\phase2_contract_acceptance_audit_s2_gate_462.json`
- `C:\glass_runs\phase2_s2_gate_462_200\default_chunked_contract_parity_20260622\s2_gate_462_default_compare.json`
- `C:\glass_runs\phase2_s2_gate_462_200\default_chunked_contract_parity_20260622\s2_gate_462_default_compare.html`
- `C:\glass_runs\phase2_s2_gate_462_200\default_chunked_contract_parity_20260622\resident_calibration_contract_s2_gate_462_default.json`
- `C:\glass_runs\phase2_s2_gate_462_200\default_chunked_contract_parity_20260622\resident_result_contract_s2_gate_462_default.json`
- `C:\glass_runs\phase2_s2_gate_462_200\default_chunked_contract_parity_20260622\pipeline_contract_s2_gate_462_default.json`
- `C:\glass_runs\phase2_s2_gate_462_200\default_chunked_contract_parity_20260622\stack_engine_contract_s2_gate_462_default.json`
- `C:\glass_runs\phase2_s2_gate_462_200\default_chunked_contract_parity_20260622\phase2_contract_acceptance_audit_s2_gate_462_default.json`

## CUDA Status

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- CUDA toolkit used by current native extension: 13.2.

## Known Limitations

- Chunked dispatch uses additional temporary output and coverage workspace.
- The native allocator can reduce chunk capacity on allocation failure, but memory planning/reporting does not yet predict chunk capacity or fallback reasons.
- The low-level `glass_cuda` wrapper keeps `dispatch="loop"` as its direct API default for compatibility; high-level `run`/`audit`/engine default is chunked.
- This gate does not change star detection, descriptor fitting, matrix estimation, rejection, local normalization, source-DQ, or frame admission.

## Next Gate

- Add chunked warp memory-planning/report evidence: predicted chunk capacity, workspace budget, fallback capacity, and warning/fallback diagnostics in reports/contracts.

## Clean-Room Compliance

- Compliant. This gate used GLASS source, GLASS synthetic fixtures, GLASS-generated artifacts, and user-owned 200-light outputs.
- Original image directories remained read-only.
- No official PixInsight/WBPP/PJSR implementation source was read, copied, summarized, or modified.
