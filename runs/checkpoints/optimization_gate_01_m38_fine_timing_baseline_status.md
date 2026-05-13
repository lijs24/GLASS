# Optimization Gate 01: M38 Fine Timing Baseline

## Gate

Optimization Gate 01.

## Completed content

- Re-ran the real M38 H-alpha 200-light resident CUDA parity command with the new fine timing schema.
- Generated a fresh HTML report with resident timing split columns.
- Compared the new output master against the previous accepted resident CUDA baseline.
- Confirmed the new instrumentation does not change the integrated master.

## Dataset

- Root: `C:\gpwbpp_runs\final_m38_h_200`
- Plan: `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`
- Lights: 200
- Integrated active set: 193 lights, with the same 7 WBPP-failed frames excluded as the previous parity run.
- Calibration: 20 bias, 20 dark, 20 flat in the copied working package.
- Original source data directories were not modified.

## Commands

```powershell
.\.venv\Scripts\gpwbpp.exe run --plan "C:\gpwbpp_runs\final_m38_h_200\processing_plan.json" --out "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3_finetiming" --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 96 --resident-star-tolerance-px 3 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-ncc-sample-stride 4 --reference-frame-id LIGHT_H_0136 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158 --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.30
.\.venv\Scripts\gpwbpp.exe report --run "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3_finetiming" --out "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3_finetiming\report.html"
.\.venv\Scripts\gpwbpp.exe compare --gpwbpp "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3_finetiming\integration\resident_master_H.fits" --reference "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3\integration\resident_master_H.fits" --out "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3_finetiming\compare_vs_previous_resident.html" --gpwbpp-time-seconds 113.24656499992125 --reference-time-seconds 111.94882199994754 --gpwbpp-label "GPWBPP finetiming" --reference-label "GPWBPP previous resident baseline"
```

Validation commands from the code checkpoint remain:

```powershell
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp\engine\resident_cuda.py src\gpwbpp\report\html_report.py tests\test_resident_cuda_run.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q
```

## Test result

- Ruff: all checks passed.
- Full pytest: 180 passed in 8.03 s.
- Real-data run: completed successfully.
- Previous-master compare: exact match, all reported absolute differences are 0.0.

## Real-data timing

- Total resident stage elapsed: 113.246565 s.
- Previous resident baseline: 111.948822 s.
- PixInsight/WBPP black-box elapsed: 1092.541 s.
- Speedup vs WBPP black-box: about 9.65x for this rerun.

Fine timing from `resident_artifacts.json`:

- `light_read_upload_calibrate`: 50.240121 s.
- `light_read_decode`: 35.604337 s.
- `light_h2d_calibrate_store`: 3.588800 s.
- `light_loop_unaccounted`: 10.956037 s.
- `resident_registration_warp`: 59.400628 s.
- `resident_integration`: 0.298604 s.
- `output_write`: 0.911272 s.
- `master_build_or_load`: 9.823396 s.

## Artifacts

- Run directory: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3_finetiming`
- HTML report: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3_finetiming\report.html`
- Resident artifacts: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3_finetiming\resident_artifacts.json`
- Previous-master compare: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3_finetiming\compare_vs_previous_resident.json`

## CUDA availability

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: yes.

## Optimization conclusions

- The resident integration kernel is already near negligible for this workload.
- The read/decode portion is the dominant part of the load/calibration bucket; pinned memory and async H2D alone cannot remove the full 50 s unless CPU-side prefetch/decode overlaps registration/warp work.
- The H2D+calibrate+resident-store binding bucket is only about 3.6 s, so kernel math is not the current calibration bottleneck.
- Registration/warp is now the largest single bucket at about 59.4 s. The next registration optimization should target batched resident star catalog/descriptor/scoring/warp scheduling and reduce per-frame orchestration.

## Known limitations

- `light_loop_unaccounted` is still about 11.0 s and needs more instrumentation inside path normalization, Python loop overhead, and any hidden synchronization in the native binding.
- This checkpoint measures the current implementation; it does not implement double buffering, pinned memory, async H2D, CUDA Graphs, or batched registration yet.

## Next step

- Implement Optimization Gate 02: resident I/O pipeline overlap. Use CPU RAM prefetch plus a bounded queue first, then pinned host staging and async H2D in the native binding if the Python-level prefetch shows measurable benefit.
- In parallel or next, implement Optimization Gate 03: batch resident registration/warp dispatch to reduce the 59.4 s bucket.

## Clean-room compliance

- Compliant. No PixInsight/WBPP/PJSR source files were read, copied, summarized, or modified.
- The WBPP comparison remains black-box and uses only user-generated logs/outputs.
- No original data directory was modified.
