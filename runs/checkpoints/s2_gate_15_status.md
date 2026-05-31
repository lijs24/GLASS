# S2-Gate 15 Status: Shared Resident Master Cache

## Gate

S2-Gate 15: Shared Resident Master Cache

## Completed

- Added `--resident-master-cache-dir` for `glass run` and `glass audit`.
- Kept default resident master cache run-local, while enabling an explicit
  opt-in shared cache across output directories.
- Fingerprinted shared cache entries from calibration group ids, frame metadata,
  file size/mtime, image shape/filter, flat-bias semantics, and calibration
  policy.
- Added cache diagnostics to `resident_artifacts.json`: `cache_scope`,
  `cache_dir`, `cache_key`, `cache_base_key`, `cache_fingerprint`, and
  `cache_hit`.
- Added resident I/O pipeline diagnostics for `master_cache_dir` and
  `master_cache_scope`.
- Added a CUDA CLI test proving a second run in a different output directory
  reuses the shared master cache.
- Updated `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Commands Run

- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_shared_master_cache_reuses_across_runs tests\test_resident_cuda_run.py::test_cli_resident_cuda_uses_planner_matching_master_sets tests\test_cli_smoke.py::test_cli_help_commands`
- `.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py src\glass\cli.py tests\test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py tests\test_cli_smoke.py tests\test_cuda_resident_stack.py`
- `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_15_200\shared_cache_seed_20260531 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_15_200\shared_cache_hit_20260531 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_15_200\shared_cache_hit_20260531\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_15_200\shared_cache_hit_20260531\compare_vs_reference_scaled_coverage190.html --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_15_200\shared_cache_hit_20260531\integration\resident_coverage_map_H.fits --min-coverage 190`
- `.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_15_200\shared_cache_hit_20260531 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_15_200\shared_cache_hit_20260531\compare_vs_reference_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate_15_200\shared_cache_hit_20260531\phase2_contract_acceptance_audit_s2_gate_15.json --markdown C:\glass_runs\phase2_s2_gate_15_200\shared_cache_hit_20260531\phase2_contract_acceptance_audit_s2_gate_15.md --min-active-frames 190 --min-speedup 20 --benchmark-contract benchmarks\phase2_m38_h_200_contract.json`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_import.py tests\test_cuda_device_info.py tests\test_cuda_smoke.py tests\test_gpu_calibration_vs_cpu.py tests\test_gpu_master_frames_vs_cpu.py tests\test_gpu_warp_vs_cpu.py tests\test_gpu_integration_vs_cpu.py tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py`
- Queried `glass_cuda` device information from the project virtualenv.

## Test Results

- Focused shared-cache tests: `3 passed`.
- Resident/CLI/CUDA focused tests: `38 passed`.
- Ruff focused check: `All checks passed`.
- Full pytest suite: `232 passed`.
- CUDA targeted tests: `50 passed`.
- Real 200-light cache-hit contract audit: passed.

## Real Benchmark Results

Artifacts:

- Shared cache: `C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache`
- Seed run: `C:\glass_runs\phase2_s2_gate_15_200\shared_cache_seed_20260531`
- Cache-hit run: `C:\glass_runs\phase2_s2_gate_15_200\shared_cache_hit_20260531`
- Compare JSON: `C:\glass_runs\phase2_s2_gate_15_200\shared_cache_hit_20260531\compare_vs_reference_scaled_coverage190.json`
- Acceptance audit JSON: `C:\glass_runs\phase2_s2_gate_15_200\shared_cache_hit_20260531\phase2_contract_acceptance_audit_s2_gate_15.json`
- Acceptance audit Markdown: `C:\glass_runs\phase2_s2_gate_15_200\shared_cache_hit_20260531\phase2_contract_acceptance_audit_s2_gate_15.md`

Seed run:

- GLASS elapsed: `34.03384030004963 s`.
- `cache_hit`: `false`.
- `master_build_or_load`: `11.75958489999175 s`.
- `light_read_upload_calibrate`: `17.540674000047147 s`.
- `output_write`: `2.212147400015965 s`.

Cache-hit run:

- GLASS elapsed: `30.652673700125888 s`.
- Speedup vs external reference: `35.64260040374595x`.
- `cache_hit`: `true`.
- `master_build_or_load`: `0.8837811001576483 s`.
- RMS diff: `0.001558294284488301`.
- P99 absolute diff: `0.00043095467146486016`.
- Coverage fraction: `0.9574613308418977`.

## CUDA

- CUDA extension built: yes.
- CUDA available: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.

## Known Limits

- Cache lookup fingerprints use metadata plus file size/mtime rather than full
  pixel checksums to avoid reading all calibration pixels during lookup.
- Shared cache is opt-in. Default behavior remains run-local.
- Cache-hit benchmark still shows I/O/decode/H2D timing variance; S2-Gate 16
  should focus on the light read/upload/calibration pipeline.

## Next Step

S2-Gate 16 should optimize `light_read_upload_calibrate` by improving the
prefetch/decode/H2D/calibrate overlap and by separating wall-clock timing from
worker cumulative timing in the benchmark diagnostics.

## Clean-Room

Compliant. This gate changes GLASS-owned cache semantics and uses only GLASS
artifacts plus user-generated benchmark/reference outputs for validation.
