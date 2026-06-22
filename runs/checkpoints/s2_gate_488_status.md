# S2-Gate 488 Status: Resident Grid Catalog Multi-Stream Batch

## Gate

- Gate: S2-Gate 488
- Status: passed
- Scope: reduce resident CUDA triangle-registration catalog scheduling time by
  dispatching the existing moving-frame grid-top-NMS catalog batch across a
  bounded CUDA stream pool, while preserving catalog math, centroid math,
  descriptor fitting, transform estimation, warp, rejection, DQ, and
  integration output semantics.

## Completed

- Added stream-aware native launch wrappers for:
  - `glass_star_grid_top_nms_candidates_f32_launch_stream`;
  - `glass_star_grid_top_nms_candidates_deterministic_f32_launch_stream`;
  - `glass_star_refine_centroids_f32_launch_stream`;
  - `glass_frame_sum_f32_launch_stream`.
- Updated `ResidentCalibratedStack.star_grid_top_nms_candidates_batch*` to
  create up to four CUDA streams, map independent per-frame scratch to streams,
  and synchronize each catalog, global-mean, and centroid-refine phase by
  stream.
- Added exception cleanup so batch streams are synchronized/destroyed before
  batch scratch buffers are released.
- Exposed `catalog_stream_count` and `catalog_sync_phase_count` through the
  Python wrapper.
- Updated resident CUDA artifacts, warnings, and HTML report rows to show
  `triangle_catalog_stream_count` and
  `triangle_catalog_sync_phase_count`.
- Updated focused tests, algorithm source documentation, and Phase 2 hardening
  notes.

## Commands Run

Native CUDA rebuild:

```powershell
$pybind = (& .\.venv\Scripts\python.exe -m pybind11 --cmakedir).Trim()
$ninja = (Resolve-Path .\.venv\Scripts\ninja.exe).Path
$cmd = 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe -S . -B build\native-cuda -G Ninja -DGLASS_BUILD_PYTHON_CUDA=ON -DGLASS_BUILD_CUDA=OFF -Dpybind11_DIR="' + $pybind + '" -DCMAKE_MAKE_PROGRAM="' + $ninja + '" -DCMAKE_CUDA_COMPILER="C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2\bin\nvcc.exe" -DCMAKE_CUDA_ARCHITECTURES=120 && .\.venv\Scripts\cmake.exe --build build\native-cuda --config Release'
cmd /c $cmd
```

Focused validation:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_grid_star_catalog_batch_reports_native_timing tests\test_gpu_star_detect.py::test_resident_stack_star_grid_top_nms_candidates_batch_matches_single_calls tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py tests\test_gpu_star_detect.py tests\test_resident_cuda_run.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m ruff check cpp src tests
```

Real 200-light warm A/B and reports:

```powershell
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real\runs\warm_catalog_multistream --backend cuda --memory-mode resident --resident-runtime-preset throughput-v1 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-integration-dispatch stack --resident-master-cache-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real\runs\warm_catalog_multistream\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real\compare\warm_vs_wbpp_scaled_coverage190.json --glass-scale 0.000008764434957115609 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real\runs\warm_catalog_multistream\integration\resident_coverage_map_H.fits --min-coverage 190 --diagnostics-dir C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real\compare\warm_vs_wbpp_scaled_coverage190_diagnostics
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real\runs\warm_catalog_multistream\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real\runs\warm_catalog_bulk_sync\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real\compare\warm_vs_gate487_master.json --glass-coverage-map C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real\runs\warm_catalog_multistream\integration\resident_coverage_map_H.fits --min-coverage 190
.\.venv\Scripts\glass.exe speedup-summary --glass-run C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real\runs\warm_catalog_multistream --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real\compare\warm_vs_wbpp_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real\speedup\warm_vs_wbpp_speedup_with_compare.json --markdown C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real\speedup\warm_vs_wbpp_speedup_with_compare.md --min-speedup 20
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real\runs\warm_catalog_multistream\manifest.json --glass-run C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real\runs\warm_catalog_multistream --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real\compare\warm_vs_wbpp_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real\acceptance\warm_threshold_acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real\acceptance\warm_threshold_acceptance_audit.md --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 20 --min-coverage-fraction 0.95 --max-rms-diff 0.01 --max-abs-diff-p99 0.01
.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real\runs\warm_catalog_multistream --out C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real\reports\warm_report.html --compare-json C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real\compare\warm_vs_wbpp_scaled_coverage190.json --acceptance-audit C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real\acceptance\warm_threshold_acceptance_audit.json
```

Full validation:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,memory.free,compute_cap --format=csv,noheader
git diff --check
```

## Test Results

- Native CUDA rebuild: passed with CUDA 13.2 and MSVC Build Tools.
- Focused node tests: `3 passed in 0.92s`.
- Focused resident/CUDA/CLI modules: `161 passed in 12.20s`.
- Ruff: `All checks passed!`.
- Full pytest: `1127 passed in 42.05s`.
- `git diff --check`: passed; only CRLF conversion warnings were reported.

## Real 200-Light Results

- Dataset: M38 H-alpha benchmark, `200` lights, `20` bias, `20` dark, `20`
  flats, user-generated WBPP black-box reference output.
- Output root:
  `C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real`.
- Gate487 baseline:
  `C:\glass_runs\phase2_s2_gate487_catalog_bulk_sync_ab_real`.
- Warm total: `19.822146899998188 s`.
- Gate487 warm total: `21.647297300049104 s`.
- Warm `master_build_or_load`: `0.30120559997158125 s`.
- Warm `light_read_upload_calibrate`: `3.5301597000216134 s`.
- Warm `resident_registration_component_accounted`:
  `2.1136693994931077 s` versus Gate487 `4.169362299743524 s`.
- Warm `resident_registration_warp`: `0.5559999998076819 s` versus Gate487
  `1.2312209998490289 s`.
- Warm `resident_integration`: `0.2864339000079781 s`.
- Warm `output_write`: `2.5641272999928333 s` versus Gate487
  `3.694475699972827 s`.
- Catalog timing model:
  `batch_multistream_bulk_download_centroid_multistream`.
- Catalog batch size: `199`.
- Catalog stream count: `4`.
- Catalog batch sync count: `4`.
- Catalog sync phase count: `3`.
- Catalog download mode: `bulk_full_capacity`.
- Catalog native sync: `0.6357767 s` -> `0.2153649 s`.
- Catalog native total: `0.9438554 s` -> `0.2573601 s`.
- Warm-vs-Gate487 GLASS master difference: RMS/p99/max all `0.0`.
- Warm-vs-WBPP scaled coverage>=190 compare:
  - coverage fraction: `0.960532609259836`;
  - RMS: `0.0017794216505176163`;
  - p99 absolute difference: `0.00042621337808668863`;
  - max absolute difference: `0.5499989986419678`.
- Warm GLASS vs WBPP speedup: `55.11718813869248x`.
- Threshold acceptance audit: `passed`.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- Driver: `596.21`.
- Total VRAM: `97887 MiB`.
- Sampled VRAM after final check: `824 MiB` used, `95776 MiB` free.

## Disk / Cleanup Note

- C: free after the gate: about `26.97 GiB`.
- No project cleanup was required for this run.
- If C: fills again, old `C:\glass_runs\phase2_s2_gate*` directories remain
  the preferred cleanup candidates. The source tree and user-owned raw image
  directories were not modified.

## Artifacts

- Summary:
  `C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real\gate488_real_ab_summary.json`.
- Warm report:
  `C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real\reports\warm_report.html`.
- Acceptance:
  `C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real\acceptance\warm_threshold_acceptance_audit.json`.
- Speedup:
  `C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real\speedup\warm_vs_wbpp_speedup_with_compare.json`.
- WBPP compare:
  `C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real\compare\warm_vs_wbpp_scaled_coverage190.json`.
- Gate487 baseline compare:
  `C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real\compare\warm_vs_gate487_master.json`.

## Known Limitations

- This is a CUDA scheduling optimization only. It does not change star
  detection thresholds, centroid math, triangle descriptors, transform
  estimation, warp interpolation, winsorized rejection, DQ semantics, or
  integration formulas.
- The stream pool is currently fixed to at most four streams; a later gate can
  make it adaptive based on GPU occupancy and scratch memory.
- The catalog work is still expressed as per-frame kernels. A deeper future
  optimization could use multi-frame kernels or CUDA Graph capture to reduce
  launch overhead further.
- FITS read/materialize worker time remains the visible throughput floor even
  when much of it is overlapped by the resident pipeline.

## Next Step

- Stay on Phase 2 substantive work:
  - StackEngine default path;
  - DQ/mask pipeline contract;
  - deeper I/O/upload overlap and resident scheduling;
  - numerical consistency checks after each 200-light performance change.

## Clean-Room Compliance

- This gate used GLASS-owned source code, GLASS CUDA kernels, GLASS-generated
  artifacts, user-owned M38 FITS inputs, and user-generated WBPP black-box
  outputs/timing only.
- It did not inspect or copy official PixInsight/WBPP/PJSR source code.
- It did not modify input image directories.
- It reorganizes GLASS native scheduling and diagnostics only; no proprietary
  formulas or external implementation details were imported.
