# Gate 08 Increment: Real M38 Resident NCC Winsorized Subset 50 With 20/20/20 Calibration

- Gate: 08
- Date: 2026-05-13
- Status: completed
- Commit: pending

## Completed

- Used the new `gpwbpp subset --all-compatible-calibration` mode to build a
  larger real M38 subset that satisfies the calibration-frame count target for
  this scale step.
- Ran full-size resident CUDA calibration, resident NCC+subpixel translation
  registration, bilinear resident warp, and winsorized sigma integration.
- Verified the selected subset contains 50 light frames plus 20 bias, 20 dark,
  and 20 flat frames.
- Verified all 49 non-reference light frames register successfully.

## Commands Run

```powershell
$base='C:\gpwbpp_runs\final_m38_h_200'; $run=Join-Path $base 'gpwbpp_resident_ncc_subset50_allcal_probe'; .\.venv\Scripts\gpwbpp.exe run --plan (Join-Path $run 'processing_plan.json') --out $run --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration translation_ncc_subpixel --resident-registration-max-shift 24 --resident-subpixel-radius-steps 2 --resident-subpixel-step 0.5
.\.venv\Scripts\python.exe -m pytest -q
```

The subset plan was generated in the previous checkpoint with:

```powershell
$base='C:\gpwbpp_runs\final_m38_h_200'; $run=Join-Path $base 'gpwbpp_resident_ncc_subset50_allcal_probe'; New-Item -ItemType Directory -Force -Path $run | Out-Null; .\.venv\Scripts\gpwbpp.exe subset --manifest (Join-Path $base 'manifest.json') --out (Join-Path $run 'manifest.json') --plan-out (Join-Path $run 'processing_plan.json') --filter H --exposure-s 600 --light-limit 50 --all-compatible-calibration
```

## Test Result

- Resident CUDA run: completed through integration.
- Full pytest after the run: 101 passed.

## Real M38 Resident Run Result

- Run directory:
  `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_subset50_allcal_probe`
- Selected subset summary:
  - 110 total frames.
  - 50 light frames.
  - 20 bias frames.
  - 20 dark frames.
  - 20 flat frames.
  - Shape: 9600x6422.
- Master frame input counts used by resident run:
  - bias_count: 20.
  - dark_count: 20.
  - flat_count: 20.
- Registration model: `translation_ncc_subpixel`.
- Registration results: 50 total; 1 reference, 49 ok, 0 failed.
- Translation range:
  - dx min/max: -25.0 / 16.5 px.
  - dy min/max: -16.5 / 4.5 px.
- Resident timing:
  - master build/load: 17.625 s.
  - resident allocate and master upload: 0.225 s.
  - light read/upload/calibrate: 9.506 s.
  - per-frame registration mean: 0.383 s.
  - resident winsorized integration: 0.192 s.
  - output write: 0.871 s.
- Memory estimate:
  - calibrated stack: 11.483 GiB.
  - resident base: 12.402 GiB.
  - estimated peak: 12.861 GiB.
- Output diagnostics:
  - finite pixels: 61,651,200.
  - nonfinite pixels: 0.
  - mean: 111.185.
  - std: 255.837.
  - min/max: -1634.695 / 50208.781.

## CUDA Availability

- CUDA native extension: available.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Artifacts

- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_subset50_allcal_probe\manifest.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_subset50_allcal_probe\processing_plan.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_subset50_allcal_probe\registration_results.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_subset50_allcal_probe\resident_artifacts.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_subset50_allcal_probe\integration_results.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_subset50_allcal_probe\integration\resident_master_H.fits`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_subset50_allcal_probe\integration\resident_weight_map_H.fits`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_subset50_allcal_probe\integration\resident_coverage_map_H.fits`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_subset50_allcal_probe\integration\resident_low_rejection_map_H.fits`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_subset50_allcal_probe\integration\resident_high_rejection_map_H.fits`

## Known Limitations

- This is still a 50-light scale step, not the final 200-light WBPP/GPWBPP
  acceptance comparison.
- Resident registration is translation-only and has no star-model RMS yet.
- Resident Local Normalization is still disabled.
- Winsorized sigma is the current two-stage mean/std approximation, not a
  byte-for-byte PixInsight FastIntegration reproduction.

## Next Step

- Run the same all-compatible-calibration resident mode on the full 200-light
  M38 plan, then compare timing and image statistics against WBPP black-box
  artifacts.

## Clean-room Compliance

- No official PixInsight WBPP/PJSR source was read, copied, summarized, or
  modified.
- Only GPWBPP outputs, user-provided M38 data, and black-box comparison artifacts
  were used.
- Original input data directories were not modified.
