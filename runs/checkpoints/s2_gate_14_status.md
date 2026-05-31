# S2-Gate 14 Status: Resident Parallel Output Write Diagnostics

## Gate

S2-Gate 14: Resident Parallel Output Write Diagnostics

## Completed

- Added resident output writes through a bounded worker pool.
- Preserved the S2-Gate 13 dtype contract:
  - master and weight maps remain `float32`
  - coverage, low-rejection, and high-rejection maps remain integer count maps
- Added `mode`, `workers`, per-file timing, and storage diagnostics under
  `resident_artifacts.json -> artifacts[0].output_write`.
- Added a focused test for parallel resident output writing and integer FITS
  count-map output.
- Updated `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Commands Run

- `.\.venv\Scripts\python.exe -m pytest -q tests\test_fits_io.py tests\test_cuda_resident_stack.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py tests\test_fits_io.py`
- `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_14_200\parallel_outputs_cold_20260531 --backend cuda --until-stage integration --memory-mode resident --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_14_200\parallel_outputs_cold_20260531\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_14_200\parallel_outputs_cold_20260531\compare_vs_reference_scaled_coverage190.html --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_14_200\parallel_outputs_cold_20260531\integration\resident_coverage_map_H.fits --min-coverage 190`
- `.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_14_200\parallel_outputs_cold_20260531 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_14_200\parallel_outputs_cold_20260531\compare_vs_reference_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate_14_200\parallel_outputs_cold_20260531\phase2_contract_acceptance_audit_s2_gate_14.json --markdown C:\glass_runs\phase2_s2_gate_14_200\parallel_outputs_cold_20260531\phase2_contract_acceptance_audit_s2_gate_14.md --min-active-frames 190 --min-speedup 20 --benchmark-contract benchmarks\phase2_m38_h_200_contract.json`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_import.py tests\test_cuda_device_info.py tests\test_cuda_smoke.py tests\test_gpu_calibration_vs_cpu.py tests\test_gpu_master_frames_vs_cpu.py tests\test_gpu_warp_vs_cpu.py tests\test_gpu_integration_vs_cpu.py tests\test_cuda_resident_stack.py`
- Queried `glass_cuda` device information from the project virtualenv.

## Test Results

- Focused tests: `27 passed`.
- Ruff focused check: `All checks passed`.
- Full pytest suite: `231 passed`.
- CUDA targeted tests: `35 passed`.
- Real 200-light contract audit: passed.

## Real Benchmark Results

Artifacts:

- Run: `C:\glass_runs\phase2_s2_gate_14_200\parallel_outputs_cold_20260531`
- Compare JSON: `C:\glass_runs\phase2_s2_gate_14_200\parallel_outputs_cold_20260531\compare_vs_reference_scaled_coverage190.json`
- Acceptance audit JSON: `C:\glass_runs\phase2_s2_gate_14_200\parallel_outputs_cold_20260531\phase2_contract_acceptance_audit_s2_gate_14.json`
- Acceptance audit Markdown: `C:\glass_runs\phase2_s2_gate_14_200\parallel_outputs_cold_20260531\phase2_contract_acceptance_audit_s2_gate_14.md`

Cold-output runtime:

- GLASS elapsed: `35.78988500009291 s`.
- Speedup vs external reference: `30.52653005163788x`.
- RMS diff: `0.001558294284488301`.
- P99 absolute diff: `0.00043095467146486016`.
- Coverage fraction: `0.9574613308418977`.

Output-write diagnostics:

- Mode: `threaded`.
- Workers: `5`.
- `output_write`: `2.416421700036153 s`.
- Per-file timing:
  - master: `2.415881099877879 s`
  - weight: `2.414679800160229 s`
  - coverage: `1.6960402999538928 s`
  - low rejection: `1.6794035998173058 s`
  - high rejection: `1.6485369999427348 s`

Comparison to prior checkpoints:

- S2-Gate 10 `output_write`: `3.3451026000548154 s`.
- S2-Gate 13 accepted hot-cache `output_write`: `2.479025000007823 s`.
- S2-Gate 14 cold-output `output_write`: `2.416421700036153 s`.

## CUDA

- CUDA extension built: yes.
- CUDA available: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.

## Known Limits

- Parallel FITS writes are still storage-bandwidth limited. The wall-clock time
  now tracks the slowest master/weight write rather than the sum of all five
  output files, but `output_write` remains above the 1.15 warning factor.
- This gate does not change scientific calculations, rejection, registration,
  calibration, or the output master values.
- A future gate should introduce an explicit output-map policy or a lower-level
  fast FITS writer to reduce the remaining output-write cost.

## Next Step

S2-Gate 15 should pivot from write-path scheduling to the larger remaining cold
runtime contributors: master-frame build/load and the light read/upload/
calibration pipeline. The most promising path is better cache reuse semantics
plus double-buffered prefetch/decode/H2D scheduling.

## Clean-Room

Compliant. This gate changes GLASS-owned output scheduling and diagnostics and
uses only GLASS artifacts plus user-generated benchmark/reference outputs for
validation.
