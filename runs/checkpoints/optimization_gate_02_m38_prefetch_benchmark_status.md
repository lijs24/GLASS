# Optimization Gate 02 Benchmark: M38 Resident Prefetch

## Gate

Optimization Gate 02 benchmark.

## Completed content

- Benchmarked the new resident CPU RAM prefetch queue on the real M38 H-alpha 200-light parity run.
- Tested queue depths 2 and 4 against the new `prefetch=0` fine-timing baseline.
- Generated reports and previous-baseline compare reports.
- Confirmed prefetch does not change the integrated master.

## Commands

```powershell
.\.venv\Scripts\gpwbpp.exe run --plan "C:\gpwbpp_runs\final_m38_h_200\processing_plan.json" --out "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3_prefetch2" --backend cuda --memory-mode resident --resident-prefetch-frames 2 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 96 --resident-star-tolerance-px 3 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-ncc-sample-stride 4 --reference-frame-id LIGHT_H_0136 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158 --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.30
.\.venv\Scripts\gpwbpp.exe run --plan "C:\gpwbpp_runs\final_m38_h_200\processing_plan.json" --out "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3_prefetch4" --backend cuda --memory-mode resident --resident-prefetch-frames 4 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 96 --resident-star-tolerance-px 3 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-ncc-sample-stride 4 --reference-frame-id LIGHT_H_0136 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158 --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.30
.\.venv\Scripts\gpwbpp.exe report --run "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3_prefetch2" --out "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3_prefetch2\report.html"
.\.venv\Scripts\gpwbpp.exe report --run "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3_prefetch4" --out "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3_prefetch4\report.html"
.\.venv\Scripts\gpwbpp.exe compare --gpwbpp "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3_prefetch2\integration\resident_master_H.fits" --reference "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3_finetiming\integration\resident_master_H.fits" --out "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3_prefetch2\compare_vs_finetiming.html" --gpwbpp-time-seconds 0 --reference-time-seconds 0 --gpwbpp-label "GPWBPP prefetch2" --reference-label "GPWBPP finetiming"
.\.venv\Scripts\gpwbpp.exe compare --gpwbpp "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3_prefetch4\integration\resident_master_H.fits" --reference "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3_finetiming\integration\resident_master_H.fits" --out "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3_prefetch4\compare_vs_finetiming.html" --gpwbpp-time-seconds 0 --reference-time-seconds 0 --gpwbpp-label "GPWBPP prefetch4" --reference-label "GPWBPP finetiming"
```

Code validation before these real-data runs:

```powershell
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp\engine\resident_cuda.py src\gpwbpp\report\html_report.py src\gpwbpp\cli.py tests\test_resident_cuda_run.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q
```

## Test result

- Ruff: all checks passed.
- Full pytest: 180 passed in 8.05 s.
- Real-data `prefetch=2`: completed successfully.
- Real-data `prefetch=4`: completed successfully.
- Both prefetch masters compare exactly equal to the `prefetch=0` fine-timing baseline: shape match true, RMS diff 0.0, max absolute diff 0.0.

## Timing comparison

| Run | Total s | Light loop s | Foreground read wait s | Worker read/decode s | H2D+cal/store s | Reg/warp s | Integration s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| prefetch=0 | 113.246565 | 50.240121 | 35.604337 | n/a | 3.588800 | 59.400628 | 0.298604 |
| prefetch=2 | 110.474105 | 48.395545 | 33.439177 | 38.716751 | 3.631436 | 58.394983 | 0.309403 |
| prefetch=4 | 111.380498 | 49.388550 | 34.215015 | 40.078917 | 3.682103 | 58.428539 | 0.299492 |

Best observed run:

- `prefetch=2`
- Total improvement vs fine-timing baseline: 2.772460 s.
- Speedup vs fine-timing baseline: 1.0251x.
- Speedup vs PixInsight/WBPP black-box 1092.541 s: about 9.89x.

## Artifacts

- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3_prefetch2`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3_prefetch4`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3_prefetch2\compare_vs_finetiming.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3_prefetch4\compare_vs_finetiming.json`

## CUDA availability

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: yes.

## Optimization conclusion

- Python-side CPU RAM prefetch is correct and gives a small real benefit.
- Queue depth 2 is better than depth 4 on this external-storage workload.
- The current foreground read wait remains about 33.4 s even with prefetch; this points to disk/CPU decode and hidden synchronization rather than CUDA kernel math.
- Registration/warp remains the largest single bucket at about 58.4 s.

## Next step

- Highest-impact path: batch resident registration/warp to reduce the 58 s bucket.
- Secondary path: native pinned host buffers plus async H2D streams. This should be implemented only after adding native split timing inside `ResidentCalibratedStack.calibrate_frame`, because current H2D+cal/store is already only about 3.6 s.

## Clean-room compliance

- Compliant. No PixInsight/WBPP/PJSR source files were read, copied, summarized, or modified.
- The benchmark used only GPWBPP artifacts and previous black-box WBPP timing/output references.
- No original data directory was modified.
