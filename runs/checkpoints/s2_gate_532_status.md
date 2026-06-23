# S2-Gate 532 Status: Resident Master Cache Mmap Load

## Gate

S2-Gate 532 continues the Phase 2 mainline light-pipeline optimization. Resident
master-cache hits now load GLASS-generated `.npy` master bias/dark/flat files
with read-only NumPy mmap before uploading them to the resident CUDA stack.

## Completed

- Added `_load_cached_resident_master()` in `src/glass/engine/resident_cuda.py`.
- Switched matching and aggregate resident master-cache hit loads from eager
  `np.load()` to `np.load(..., mmap_mode="r")`.
- Recorded `cache_hit_load_mode=npy_mmap_readonly` in cache-hit master stats.
- Added a focused regression asserting cache hits return `np.memmap` arrays.
- Ran a real M38 H-alpha 200-light resident CUDA validation with audit maps.
- Compared all six Gate532 audit maps against Gate531 bitwise.
- Ran scaled GLASS-vs-WBPP black-box compare and acceptance audit.

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_master_stack_engine.py::test_resident_matching_master_cache_uses_stack_engine_contract`
- `.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_grid_star_catalog_batch_reports_native_timing tests\test_resident_cuda_run.py::test_cli_resident_cuda_shared_master_cache_reuses_across_runs`
- `.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate532_master_mmap_real\runs_20260623_124500\master_mmap_default --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- `.venv\Scripts\glass.exe compare --glass <Gate532 resident_master_H.fits> --reference <WBPP fastIntegration.xisf> --glass-scale 1.545301547671945e-05 --glass-offset=-9.765786009702931e-05 --ignore-border-px 128 --glass-coverage-map <Gate532 resident_coverage_map_H.fits> --min-coverage 190`
- `.venv\Scripts\glass.exe acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run <Gate532 run> --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json <Gate532 compare json> --min-active-frames 190`
- `.venv\Scripts\python.exe -m pytest -q`

## Results

- Focused tests: `3 passed`.
- Full pytest: `1174 passed in 43.29s`.
- Real 200-light internal runtime: `5.448489899979904 s`.
- Real 200-light shell runtime: `5.819167 s`.
- Master cache hit count: `1`.
- Cache hit load mode: `npy_mmap_readonly`.
- Master build/load timing improved from Gate531 `0.35347919998457655 s`
  to Gate532 `0.29116860002977774 s`.
- Gate532 master, weight map, coverage map, low rejection map, high rejection
  map, and DQ map are bitwise identical to Gate531.
- GLASS-vs-WBPP scaled compare: coverage fraction `0.9892770479074376`, RMS
  `0.0004279821839256963`, p99 absolute difference
  `0.0001313822576776147`.
- Acceptance audit: `passed`.
- Internal speedup versus WBPP black-box `1092.541 s`: `200.5217996281923x`.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Artifacts

- Summary: `runs/checkpoints/s2_gate_532_master_mmap_summary.json`.
- Real run root:
  `C:\glass_runs\phase2_s2_gate532_master_mmap_real\runs_20260623_124500`.
- Validation run:
  `C:\glass_runs\phase2_s2_gate532_master_mmap_real\runs_20260623_124500\master_mmap_default`.
- Compare report:
  `C:\glass_runs\phase2_s2_gate532_master_mmap_real\runs_20260623_124500\master_mmap_default\compare_vs_wbpp_fastintegration_scaled_coverage190.html`.
- Acceptance audit:
  `C:\glass_runs\phase2_s2_gate532_master_mmap_real\runs_20260623_124500\master_mmap_default\acceptance_audit_scaled.json`.

## Known Limits

- This gate optimizes warm/shared master-cache hit loading only; cold master
  construction is unchanged.
- The full pinned prefetch probe with 200 raw frames regressed runtime, so it
  was not promoted. The next high-memory design should decouple pageable raw
  RAM caching from a smaller pinned H2D staging ring.
- Resident timing still has nested component fields that should not be treated
  as wall-clock sums; wall-clock light-pipeline and real run timings remain the
  governing performance evidence.

## Next

- Implement and validate a two-tier resident raw-cache/pinned-ring scheduler, or
  a bitwise-safe resident warp/integration fusion that removes the current
  Lanczos3 warp scratch/scatter pass.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned code, GLASS-generated resident cache
artifacts, GLASS tests, and user-generated WBPP black-box timing/reference
outputs only. It does not read external implementation source and does not
modify input image directories.
