# Gate 12 resident CUDA triangle 200-light WBPP comparison status

Date: 2026-05-13 14:51:49 +08:00

## Gate

Gate 12: End-to-end CUDA WBPP-like pipeline

This is a substantive real-data progress checkpoint, not a claim that Gate 12
is fully complete. It validates a 200-light high-VRAM CUDA run and compares it
to the existing PixInsight/WBPP black-box run.

## Completed

- Ran GLASS resident CUDA on the full M38 H dataset:
  - Light: 200.
  - Bias: 20.
  - Dark: 20.
  - Flat: 20.
  - Image shape: 9600x6422.
- Used the new resident `similarity_cuda_triangle` registration mode.
- Kept calibrated frames resident in VRAM, then applied resident matrix bilinear
  warp and resident winsorized sigma integration.
- Matched the WBPP black-box reference frame choice by using
  `LIGHT_H_0136`.
- Generated full output maps:
  - master light.
  - weight map.
  - coverage map.
  - low rejection map.
  - high rejection map.
- Generated HTML report and WBPP comparison reports.

## Commands Run

```powershell
.\.venv\Scripts\glass.exe run --plan "C:\glass_runs\final_m38_h_200\processing_plan.json" --out "C:\glass_runs\final_m38_h_200\glass_resident_triangle_200_fixed350_ref136_winsorized" --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 96 --resident-star-tolerance-px 3 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-ncc-sample-stride 4 --reference-frame-id LIGHT_H_0136
.\.venv\Scripts\glass.exe compare --glass "C:\glass_runs\final_m38_h_200\glass_resident_triangle_200_fixed350_ref136_winsorized\integration\resident_master_H.fits" --reference "C:\glass_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out "C:\glass_runs\final_m38_h_200\glass_resident_triangle_200_fixed350_ref136_winsorized\compare_vs_wbpp_fastintegration.html" --glass-time-seconds 113.3219756000326 --reference-time-seconds 1092.541 --glass-label "GLASS resident CUDA triangle 200" --reference-label "PixInsight WBPP FastIntegration"
.\.venv\Scripts\glass.exe compare --glass "C:\glass_runs\final_m38_h_200\glass_resident_triangle_200_fixed350_ref136_winsorized\integration\resident_master_H.fits" --reference "C:\glass_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out "C:\glass_runs\final_m38_h_200\glass_resident_triangle_200_fixed350_ref136_winsorized\compare_vs_wbpp_fastintegration_scaled.html" --glass-time-seconds 113.3219756000326 --reference-time-seconds 1092.541 --glass-label "GLASS resident CUDA triangle 200 scaled" --reference-label "PixInsight WBPP FastIntegration" --glass-scale 0.000007190655869859117 --glass-offset 0.0007891069600940803
.\.venv\Scripts\glass.exe report --run "C:\glass_runs\final_m38_h_200\glass_resident_triangle_200_fixed350_ref136_winsorized" --out "C:\glass_runs\final_m38_h_200\glass_resident_triangle_200_fixed350_ref136_winsorized\report.html"
```

## Test Results

- GLASS run status: completed through resident integration.
- Total GLASS time: 113.3219756000326 s.
- PixInsight/WBPP black-box time:
  - External timing: 1092.541 s.
  - Reported WBPP line: `WeightedBatchPreprocessing: 18:03.17`.
- Speedup vs WBPP black-box: 9.64103382609653x.
- Registration status counts:
  - 199 ok.
  - 1 reference.
  - 0 failed.
- Resident reference frame: `F000196`, matching requested `LIGHT_H_0136`.
- Resident registration mean: 0.2970380189985735 s/frame.
- Resident winsorized integration: 0.3110651999595575 s.
- Estimated peak resident memory: 47.3117358982563 GiB.
- Output finite pixels: 61651200.
- Output nonfinite pixels: 0.

## Comparison Results

Reference:

`C:\glass_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf`

Candidate:

`C:\glass_runs\final_m38_h_200\glass_resident_triangle_200_fixed350_ref136_winsorized\integration\resident_master_H.fits`

Raw comparison:

- Shape match: true.
- Timing speedup: 9.64103382609653x.
- Raw RMS difference is dominated by intensity-scale mismatch because the WBPP
  XISF master is in normalized 0..1-like units while GLASS currently writes ADU
  float output.

Scaled comparison using robust fit:

- Applied scale: 0.000007190655869859117.
- Applied offset: 0.0007891069600940803.
- Median absolute difference: 7.875263690948486e-05.
- p90 absolute difference: 0.00015138322487473488.
- p99 absolute difference: 0.0026698620524257324.
- p99.9 absolute difference: 0.2090340380728072.
- RMS difference: 0.012565779327689769.
- Mean difference: -0.0008841272540703833.

Artifacts:

- `C:\glass_runs\final_m38_h_200\glass_resident_triangle_200_fixed350_ref136_winsorized\integration\resident_master_H.fits`
- `C:\glass_runs\final_m38_h_200\glass_resident_triangle_200_fixed350_ref136_winsorized\integration\resident_weight_map_H.fits`
- `C:\glass_runs\final_m38_h_200\glass_resident_triangle_200_fixed350_ref136_winsorized\integration\resident_coverage_map_H.fits`
- `C:\glass_runs\final_m38_h_200\glass_resident_triangle_200_fixed350_ref136_winsorized\integration\resident_low_rejection_map_H.fits`
- `C:\glass_runs\final_m38_h_200\glass_resident_triangle_200_fixed350_ref136_winsorized\integration\resident_high_rejection_map_H.fits`
- `C:\glass_runs\final_m38_h_200\glass_resident_triangle_200_fixed350_ref136_winsorized\report.html`
- `C:\glass_runs\final_m38_h_200\glass_resident_triangle_200_fixed350_ref136_winsorized\compare_vs_wbpp_fastintegration.html`
- `C:\glass_runs\final_m38_h_200\glass_resident_triangle_200_fixed350_ref136_winsorized\compare_vs_wbpp_fastintegration_scaled.html`

## CUDA

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: available.

## Known Limitations

- WBPP integrated 193 of 200 frames; this GLASS run accepted all 200 frames.
  Frame-quality rejection parity is still pending.
- GLASS uses resident bilinear matrix warp, not WBPP/StarAlignment-equivalent
  Lanczos/clamping.
- Local normalization was off in this run.
- GLASS writes ADU-like FITS output; WBPP master is normalized XISF, so the
  strongest comparison currently requires robust scale/offset matching.
- The resident triangle descriptor path still routes compact catalogs through
  Python orchestration.

## Next Step

Implement frame-quality rejection parity and GPU Lanczos/clamping warp, then
rerun the 200-light comparison with the same accepted-frame set as WBPP.

## Clean-room Compliance

Compliant. WBPP was used only as a black-box executable and output/log source.
No PixInsight/WBPP/PJSR source code was read, copied, summarized, or modified.
