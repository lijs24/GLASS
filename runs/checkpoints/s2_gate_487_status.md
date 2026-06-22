# S2-Gate 487 Status: Resident Grid Catalog Bulk One-Sync Batch

## Gate

- Gate: S2-Gate 487
- Status: passed
- Scope: reduce resident CUDA triangle-registration catalog orchestration by
  replacing per-frame grid-top-NMS batch synchronization/download with
  batch-owned buffers, one CUDA synchronization, and bulk count/catalog
  downloads, while preserving the existing catalog, centroid, descriptor,
  transform, warp, rejection, and integration math.

## Completed

- Reworked `ResidentCalibratedStack.star_grid_top_nms_candidates_batch*` in the
  native CUDA binding to allocate per-frame grid/output/count scratch for the
  whole moving-frame batch.
- The batch route now enqueues all grid-top-NMS catalog kernels, synchronizes
  once, downloads counts/stored counts in bulk, downloads catalog arrays in
  bulk, and returns the same per-frame Python catalog dictionaries.
- Centroid-enabled batch routes now copy pre-refine coordinates in bulk, compute
  global-mean centroid backgrounds with batched reductions when requested,
  launch all centroid-refine kernels before one synchronization, and download
  statuses in bulk.
- Added wrapper/artifact fields for `catalog_batch_size`,
  `catalog_batch_sync_count`, `catalog_download_mode`, and
  `catalog_centroid_refine_s`.
- Updated resident artifacts, warnings, and HTML report rows to expose the new
  timing model and batch evidence.
- Updated `docs/algorithm_sources.md` and
  `docs/phase2_algorithm_hardening.md`.

## Commands Run

Native CUDA rebuild:

```powershell
$pybind = (& .\.venv\Scripts\python.exe -m pybind11 --cmakedir).Trim()
$ninja = (Resolve-Path .\.venv\Scripts\ninja.exe).Path
cmd /c "call `"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat`" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe -S . -B build\native-cuda -G Ninja -DGLASS_BUILD_PYTHON_CUDA=ON -DGLASS_BUILD_CUDA=OFF -Dpybind11_DIR=`"$pybind`" -DCMAKE_MAKE_PROGRAM=`"$ninja`" -DCMAKE_CUDA_COMPILER=`"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2\bin\nvcc.exe`" -DCMAKE_CUDA_ARCHITECTURES=120 && .\.venv\Scripts\cmake.exe --build build\native-cuda --config Release"
```

Focused validation:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_grid_star_catalog_batch_reports_native_timing tests\test_gpu_star_detect.py::test_resident_stack_star_grid_top_nms_candidates_batch_matches_single_calls tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py tests\test_gpu_star_detect.py tests\test_resident_cuda_run.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m ruff check cpp src tests
```

Real 200-light warm A/B and reports:

```powershell
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real\runs\warm_catalog_bulk_sync --backend cuda --memory-mode resident --resident-runtime-preset throughput-v1 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-integration-dispatch stack --resident-master-cache-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real\runs\warm_catalog_bulk_sync\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real\compare\warm_vs_wbpp_scaled_coverage190.json --glass-scale 0.000008764434957115609 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real\runs\warm_catalog_bulk_sync\integration\resident_coverage_map_H.fits --min-coverage 190 --diagnostics-dir C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real\compare\warm_vs_wbpp_scaled_coverage190_diagnostics
.\.venv\Scripts\glass.exe speedup-summary --glass-run C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real\runs\warm_catalog_bulk_sync --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real\compare\warm_vs_wbpp_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real\speedup\warm_vs_wbpp_speedup_with_compare.json --markdown C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real\speedup\warm_vs_wbpp_speedup_with_compare.md --min-speedup 20
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real\runs\warm_catalog_bulk_sync\manifest.json --glass-run C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real\runs\warm_catalog_bulk_sync --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real\compare\warm_vs_wbpp_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real\acceptance\warm_threshold_acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real\acceptance\warm_threshold_acceptance_audit.md --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 20 --min-coverage-fraction 0.95 --max-rms-diff 0.01 --max-abs-diff-p99 0.01
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real\runs\warm_catalog_bulk_sync\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate487_current_head_ab_real\runs\warm_current_head\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real\compare\warm_vs_gate486_head_master.json --diagnostics-dir C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real\compare\warm_vs_gate486_head_diagnostics
.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real\runs\warm_catalog_bulk_sync --out C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real\reports\warm_report.html --compare-json C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real\compare\warm_vs_wbpp_scaled_coverage190.json --acceptance-audit C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real\acceptance\warm_threshold_acceptance_audit.json
```

Full validation:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,memory.free,compute_cap --format=csv,noheader
```

## Test Results

- Native CUDA rebuild: passed with CUDA 13.2 and MSVC Build Tools.
- Focused node tests: `3 passed in 0.44s`.
- Focused resident/CUDA/CLI modules: `161 passed in 12.31s`.
- Ruff: `All checks passed!`.
- Full pytest: `1127 passed in 42.00s`.

## Real 200-Light Results

- Dataset: M38 H-alpha benchmark, `200` lights, `20` bias, `20` dark, `20`
  flats, user-generated WBPP black-box reference output.
- Output root:
  `C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real`.
- Previous warm baseline:
  `C:\glass_runs\phase2_s2_gate487_current_head_ab_real`.
- Warm total: `21.647297300049104 s`.
- Previous warm total: `20.36849359999178 s`.
- Warm `master_build_or_load`: `0.29267189995152876 s`.
- Warm `light_read_upload_calibrate`: `3.511927100014873 s`.
- Warm `resident_registration_component_accounted`: `4.169362299743524 s`
  versus previous `4.203437800650955 s`.
- Warm `resident_registration_warp`: `1.2312209998490289 s` versus previous
  `1.258692299888935 s`.
- Warm `resident_integration`: `0.299204999988433 s`.
- Warm `output_write`: `3.694475699972827 s` versus previous
  `2.2861240999773145 s`.
- Catalog timing model: `batch_launch_one_sync_bulk_download_centroid_one_sync`.
- Catalog batch size: `199`.
- Catalog batch sync count: `1`.
- Catalog download mode: `bulk_full_capacity`.
- Catalog native sync: `0.8971051 s` -> `0.6357767 s`.
- Catalog native total: `0.9703687 s` -> `0.9438554 s`.
- Warm-vs-previous-GLASS master difference: RMS/p99/max all `0.0`.
- Warm-vs-WBPP scaled coverage>=190 compare:
  - RMS: `0.0017794216505176163`;
  - p99 absolute difference: `0.00042621337808668863`;
  - max absolute difference: `0.5499989986419678`.
- Warm GLASS vs WBPP speedup: `50.47008801405992x`.
- Threshold acceptance audit: `passed`.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- Driver: `596.21`.
- Total VRAM: `97887 MiB`.
- Sampled VRAM during final check: `824 MiB` used, `95776 MiB` free.

## Disk / Cleanup Note

- C: free after the gate: about `27.89 GiB`.
- Keep current Gate487 artifacts, Gate486 shared master cache, and
  `C:\gpwbpp_runs\final_m38_h_200` for the active 200-light evidence chain.
- If C: fills again, old `C:\glass_runs\phase2_s2_gate*` directories remain
  the preferred cleanup candidates. The source tree and user-owned raw image
  directories were not modified.

## Artifacts

- Summary:
  `C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real\gate487_real_ab_summary.json`.
- Warm report:
  `C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real\reports\warm_report.html`.
- Acceptance:
  `C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real\acceptance\warm_threshold_acceptance_audit.json`.
- Speedup:
  `C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real\speedup\warm_vs_wbpp_speedup_with_compare.json`.
- WBPP compare:
  `C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real\compare\warm_vs_wbpp_scaled_coverage190.json`.
- Baseline compare:
  `C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real\compare\warm_vs_gate486_head_master.json`.

## Known Limitations

- This is a scheduling optimization only. It does not change star detection,
  centroid math, triangle descriptors, transform estimation, warp interpolation,
  winsorized rejection, DQ semantics, or integration formulas.
- The batch still enqueues existing per-frame catalog kernels on the default
  stream; it reduces host synchronization/download overhead but does not yet
  fuse the full-frame scan/top-k/NMS work into a single multi-frame kernel.
- The local catalog sync target improved, but the single real warm run did not
  improve end-to-end total time because output map writing was slower in this
  sample.
- Output-write tail latency is now large enough to mask small compute-side
  improvements. Future performance gates should either reduce output-map writes
  or make a larger registration-side cut.

## Next Step

- Prefer a substantive performance gate over report-only work:
  - reduce output-map write tail for audit/science modes, or
  - deepen resident catalog batching beyond one-sync scheduling, or
  - continue the resident light I/O/upload overlap path if disk read wait grows
    again.
- Keep real 200-light A/B and zero-diff GLASS baseline compare after each
  performance-affecting change.

## Clean-Room Compliance

- This gate used GLASS-owned source code, GLASS CUDA kernels, GLASS-generated
  artifacts, user-owned M38 FITS inputs, and user-generated WBPP black-box
  outputs/timing only.
- It did not inspect or copy official PixInsight/WBPP/PJSR source code.
- It did not modify input image directories.
- It reorganizes GLASS native scheduling and diagnostics only; no proprietary
  formulas or external implementation details were imported.
