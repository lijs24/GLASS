# Gate 13 real 200-frame WBPP comparison checkpoint

Date: 2026-05-13

Status: partial Gate 13 benchmark checkpoint. This records a real-data PixInsight/WBPP black-box comparison for the resident CUDA path, but it does not claim the full WBPP-like pipeline is complete.

## Scope

- Dataset: M38 H mono, 200 light frames plus 20 bias, 20 dark, and 20 flat frames staged under `C:\glass_runs\final_m38_h_200`.
- WBPP reference: user-generated PixInsight/WBPP black-box output only.
- GLASS path: resident CUDA calibration, external astroalign similarity matrices, CUDA matrix warp, and resident winsorized sigma integration.
- Local normalization: disabled.
- Weighting: none, matching the extracted WBPP FastIntegration history.
- Rejection: `winsorized_sigma`, matching the extracted WBPP FastIntegration history at a policy level. GLASS currently records this as a two-stage winsorized mean/std approximation.

## Commands

```powershell
.\.venv\Scripts\glass.exe run `
  --plan "C:\glass_runs\final_m38_h_200\processing_plan_flatfloor005.json" `
  --out "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_200_ref_light001_flat005_preview3072" `
  --backend cuda `
  --until-stage registration `
  --registration-method astroalign `
  --registration-preview-max-dimension 3072 `
  --tile-size 1024 `
  --flat-floor 0.05 `
  --reference-frame-id LIGHT_H_0001
```

```powershell
.\.venv\Scripts\glass.exe run `
  --plan "C:\glass_runs\final_m38_h_200\processing_plan_flatfloor005.json" `
  --out "C:\glass_runs\final_m38_h_200\glass_resident_external_matrix_astroalign_200_flat005_preview3072_matchedmasters_winsorized" `
  --backend cuda `
  --memory-mode resident `
  --until-stage integration `
  --local-normalization off `
  --integration-rejection winsorized_sigma `
  --integration-weighting none `
  --flat-floor 0.05 `
  --resident-registration external_matrix `
  --resident-registration-results "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_200_ref_light001_flat005_preview3072\registration_results.json"
```

```powershell
.\.venv\Scripts\glass.exe compare `
  --glass "C:\glass_runs\final_m38_h_200\glass_resident_external_matrix_astroalign_200_flat005_preview3072_matchedmasters_winsorized\integration\resident_master_H.fits" `
  --reference "C:\glass_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" `
  --out "C:\glass_runs\final_m38_h_200\resident_external_matrix_winsorized_200_vs_wbpp_compare_scaled.html" `
  --glass-time-seconds 54.03370799997356 `
  --reference-time-seconds 1092.541 `
  --glass-label "GLASS resident CUDA external-matrix winsorized scaled" `
  --reference-label "PixInsight WBPP FastIntegration" `
  --glass-scale 2.4922592800688463e-06 `
  --glass-offset 0.0013092293439297639 `
  --clip-low 0 `
  --clip-high 1
```

## Results

- WBPP black-box elapsed time: 1092.541 s.
- Tile GLASS astroalign registration preparation elapsed time: 2177.349 s.
  - Calibration cache: 565.933 s.
  - Quality metrics: 541.366 s.
  - Astroalign registration: 1070.050 s.
- Registration status: 200 rows; 1 reference, 192 ok, 7 failed.
- Failed frames were preserved in diagnostics and assigned zero integration weight by resident `external_matrix`; they were not silently integrated.
- Resident CUDA external-matrix winsorized run elapsed time: 54.034 s.
- Speedup versus WBPP black-box total for this resident run: 20.22x.
- Estimated resident peak VRAM: 47.312 GiB.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition, compute capability 12.0, 97886 MiB.

## Artifacts

- Registration artifact: `C:\glass_runs\final_m38_h_200\glass_tile_astroalign_200_ref_light001_flat005_preview3072\registration_results.json`.
- Resident run: `C:\glass_runs\final_m38_h_200\glass_resident_external_matrix_astroalign_200_flat005_preview3072_matchedmasters_winsorized`.
- Master output: `C:\glass_runs\final_m38_h_200\glass_resident_external_matrix_astroalign_200_flat005_preview3072_matchedmasters_winsorized\integration\resident_master_H.fits`.
- Weight map: `C:\glass_runs\final_m38_h_200\glass_resident_external_matrix_astroalign_200_flat005_preview3072_matchedmasters_winsorized\integration\resident_weight_map_H.fits`.
- Coverage map: `C:\glass_runs\final_m38_h_200\glass_resident_external_matrix_astroalign_200_flat005_preview3072_matchedmasters_winsorized\integration\resident_coverage_map_H.fits`.
- Low rejection map: `C:\glass_runs\final_m38_h_200\glass_resident_external_matrix_astroalign_200_flat005_preview3072_matchedmasters_winsorized\integration\resident_low_rejection_map_H.fits`.
- High rejection map: `C:\glass_runs\final_m38_h_200\glass_resident_external_matrix_astroalign_200_flat005_preview3072_matchedmasters_winsorized\integration\resident_high_rejection_map_H.fits`.
- Raw compare report: `C:\glass_runs\final_m38_h_200\resident_external_matrix_winsorized_200_vs_wbpp_compare.html`.
- Scaled compare report: `C:\glass_runs\final_m38_h_200\resident_external_matrix_winsorized_200_vs_wbpp_compare_scaled.html`.
- GLASS run report: `C:\glass_runs\final_m38_h_200\glass_resident_external_matrix_astroalign_200_flat005_preview3072_matchedmasters_winsorized\report.html`.

## Scaled compare metrics

The WBPP master is in a normalized XISF scale while GLASS writes ADU-scale FITS. A robust linear scale/offset was therefore applied to GLASS before the scaled report:

- Scale: 2.4922592800688463e-06.
- Offset: 0.0013092293439297639.
- Shape match: true.
- Scaled median absolute difference: 0.00015249.
- Scaled p90 absolute difference: 0.00025546.
- Scaled p99 absolute difference: 0.00541669.
- Scaled RMS difference: 0.01321733.
- Fit-pixel p99 absolute difference: 0.00126287 across 60,633,598 fit pixels.

## Known limitations

- This checkpoint does not include a fully clean-room GPU similarity/affine star matcher. The transform matrices are produced by open-source `astroalign` and then consumed by GLASS resident CUDA.
- The resident path uses full-frame VRAM residency for this dataset because 96 GiB is sufficient; the out-of-core path remains available but was not used for this speed result.
- Local Normalization remains disabled in this comparison.
- GLASS `winsorized_sigma` is currently a documented approximation, not a claim of PixInsight-identical rejection.
- Output scaling and XISF/FITS metadata semantics still differ from WBPP.
- Seven frames failed astroalign registration in both the WBPP black-box history and GLASS astroalign pass; they were excluded/zero-weighted.

## Tests

Command:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Result: 120 passed in 6.75 s.

## Clean-room compliance

Compliant. PixInsight/WBPP was used only as a black-box executable and through user-generated logs/history/output files. No official WBPP/PJSR source was read or copied.
