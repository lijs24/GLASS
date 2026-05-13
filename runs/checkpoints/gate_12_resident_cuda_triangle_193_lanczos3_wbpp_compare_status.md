# Gate 12 Resident CUDA Triangle 193-frame Lanczos3 WBPP Compare Status

## Gate

Gate 12 real-data CUDA/WBPP-like benchmark sub-checkpoint.

## Completed Content

- Re-ran the real M38 H-alpha benchmark with the same 200-light plan and the same 7 PixInsight/WBPP FastIntegration failed frames excluded from integration.
- Used the resident high-VRAM CUDA path with triangle-descriptor similarity registration.
- Applied the new resident CUDA Lanczos3 matrix warp with a clean-room local clamping threshold of `0.30`.
- Generated GLASS integration products, maps, run state, timing JSON, HTML report, and WBPP black-box comparison reports.

## Commands Run

```powershell
.\.venv\Scripts\glass.exe run --plan "C:\glass_runs\final_m38_h_200\processing_plan.json" --out "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3" --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 96 --resident-star-tolerance-px 3 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-ncc-sample-stride 4 --reference-frame-id LIGHT_H_0136 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158 --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.30
.\.venv\Scripts\glass.exe report --run "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3" --out "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3\report.html"
.\.venv\Scripts\glass.exe compare --glass "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3\integration\resident_master_H.fits" --reference "C:\glass_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3\compare_vs_wbpp_fastintegration_unscaled.html" --glass-time-seconds 111.94882199994754 --reference-time-seconds 1092.541 --glass-label "GLASS resident CUDA triangle Lanczos3 193 WBPP-failed-excluded" --reference-label "PixInsight WBPP FastIntegration"
.\.venv\Scripts\glass.exe compare --glass "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3\integration\resident_master_H.fits" --reference "C:\glass_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3\compare_vs_wbpp_fastintegration_scaled.html" --glass-time-seconds 111.94882199994754 --reference-time-seconds 1092.541 --glass-label "GLASS resident CUDA triangle Lanczos3 193 WBPP-failed-excluded scaled" --reference-label "PixInsight WBPP FastIntegration" --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127
```

## Test Results

- Latest code validation before this real-data run:
  - Ruff: passed.
  - Targeted CUDA/resident tests: `20 passed in 3.01s`.
  - Full test suite: `161 passed in 7.56s`.
- This checkpoint adds benchmark artifacts only; no code was changed after the green test run.

## Real-data Results

- Output directory: `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3`.
- GLASS total elapsed: `111.94882199994754 s`.
- PixInsight/WBPP black-box elapsed: `1092.541 s`.
- Speedup: `9.75928982978054x`.
- Registration statuses: 192 ok, 1 reference, 7 excluded, 0 failed.
- Resident reference frame: `F000196` / original `LIGHT_H_0136`.
- Warp interpolation: `lanczos3`.
- Warp clamping threshold: `0.3`.
- Estimated peak memory: `47.3117358982563 GiB`.

## Output Artifacts

- GLASS master: `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3\integration\resident_master_H.fits`.
- Weight map: `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3\integration\resident_weight_map_H.fits`.
- Coverage map: `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3\integration\resident_coverage_map_H.fits`.
- Low/high rejection maps:
  - `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3\integration\resident_low_rejection_map_H.fits`.
  - `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3\integration\resident_high_rejection_map_H.fits`.
- HTML report: `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3\report.html`.
- Unscaled compare: `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3\compare_vs_wbpp_fastintegration_unscaled.html`.
- Scaled compare: `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3\compare_vs_wbpp_fastintegration_scaled.html`.

## Scaled Compare Summary

- Shape match: true.
- Applied GLASS scale: `8.764434957115609e-06`.
- Applied GLASS offset: `0.0006274500691899127`.
- Mean difference: `-0.0008743904416223945`.
- RMS difference: `0.012474273859075652`.
- Absolute difference p50: `7.260881830006838e-05`.
- Absolute difference p90: `0.00013712106738239527`.
- Absolute difference p99: `0.0021627108892425632`.
- Absolute difference p99.9: `0.20893197426822768`.
- Max absolute difference: `0.5395518892910331`.

## CUDA Availability

- CUDA available: yes.
- Native backend: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Known Limitations

- The WBPP comparison is black-box and does not claim algorithmic identity.
- The 7 frames excluded here are the same frames observed as failed in WBPP FastIntegration history, all with `totalPairMatches: 0`.
- Low-percentile and mid-percentile differences are small after scaling, but high-percentile residuals remain. Likely contributors include star matching details, interpolation/clamping differences, rejection details, and normalization/output scaling differences.
- Local normalization is still disabled in this resident comparison.
- The resident high-VRAM path intentionally prioritizes current-data peak throughput over the full out-of-core path.

## Next Step

- Investigate the high-percentile residuals by comparing registered previews or per-frame residual diagnostics, then decide whether to tune Lanczos clamping/interpolation or focus next on GPU Local Normalization.

## Clean-room Compliance

- Compliant. WBPP was used only as a black-box reference through user-generated outputs, logs, and XISF processing history.
- No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or used as implementation input.
