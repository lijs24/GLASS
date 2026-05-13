# Optimization Gate 03 Benchmark: M38 Registration Component Timing

## Gate

Optimization Gate 03 benchmark.

## Completed content

- Re-ran the M38 H-alpha 200-light resident CUDA parity command with `prefetch=2` and registration component timing enabled.
- Generated an HTML report and compare report against the previous `prefetch=2` baseline.
- Confirmed instrumentation does not change the master.
- Identified the dominant registration substage.

## Commands

```powershell
.\.venv\Scripts\glass.exe run --plan "C:\glass_runs\final_m38_h_200\processing_plan.json" --out "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3_prefetch2_regtiming" --backend cuda --memory-mode resident --resident-prefetch-frames 2 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 96 --resident-star-tolerance-px 3 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-ncc-sample-stride 4 --reference-frame-id LIGHT_H_0136 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158 --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.30
.\.venv\Scripts\glass.exe report --run "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3_prefetch2_regtiming" --out "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3_prefetch2_regtiming\report.html"
.\.venv\Scripts\glass.exe compare --glass "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3_prefetch2_regtiming\integration\resident_master_H.fits" --reference "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3_prefetch2\integration\resident_master_H.fits" --out "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3_prefetch2_regtiming\compare_vs_prefetch2.html" --glass-time-seconds 0 --reference-time-seconds 0 --glass-label "GLASS regtiming" --reference-label "GLASS prefetch2"
```

Code validation from Gate 03:

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py src\glass\report\html_report.py tests\test_resident_cuda_run.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q
```

## Test result

- Ruff: all checks passed.
- Full pytest: 180 passed in 8.13 s.
- Real-data run: completed successfully.
- Compare vs previous `prefetch=2`: shape match true, RMS diff 0.0, max absolute diff 0.0.

## Real-data timing

- Total resident stage elapsed: 111.385636 s.
- Light loop: 49.290596 s.
- Foreground read wait: 34.271282 s.
- Background worker read/decode: 39.534848 s.
- H2D + calibrate + resident store: 3.666545 s.
- Registration/warp total: 58.390720 s.
- Resident integration: 0.303852 s.

Registration component timing:

| Component | Seconds |
| --- | ---: |
| triangle_pixel_refine | 37.927054 |
| triangle_moving_catalog | 15.045235 |
| triangle_descriptor_fit | 3.463903 |
| triangle_warp | 1.633834 |
| triangle_moving_descriptors | 0.236536 |
| triangle_reference_catalog | 0.066467 |
| triangle_reference_descriptors | 0.001813 |
| triangle_threshold_select | 0.000189 |
| Python orchestration/uninstrumented | 0.015690 |

## Artifacts

- Run directory: `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3_prefetch2_regtiming`
- Report: `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3_prefetch2_regtiming\report.html`
- Resident artifacts: `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3_prefetch2_regtiming\resident_artifacts.json`
- Compare report: `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3_prefetch2_regtiming\compare_vs_prefetch2.json`

## CUDA availability

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: yes.

## Optimization conclusion

- Pixel refinement is the dominant registration bottleneck at about 65% of the registration/warp time.
- Moving-frame catalog detection is the second bottleneck at about 26%.
- Descriptor fitting and actual warp are much smaller.
- Python orchestration is negligible after measuring the native call boundaries, so CUDA Graphs around Python calls are not the first lever.

## Next step

- First optimization target: reduce or batch `triangle_pixel_refine`.
- Candidate tactics:
  - expose a runtime final-sample-stride override and benchmark stride 2/4 against the current stride 1 parity result;
  - use a two-stage policy where only low-confidence frames run full stride 1;
  - batch candidate refinement across frames in native CUDA once the acceptable quality/speed tradeoff is known.
- Second optimization target: cache or batch moving catalog generation across all frames.

## Clean-room compliance

- Compliant. No PixInsight/WBPP/PJSR source files were read, copied, summarized, or modified.
- No original data directory was modified.
