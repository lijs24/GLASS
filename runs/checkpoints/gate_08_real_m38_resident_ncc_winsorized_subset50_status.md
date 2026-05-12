# Gate 08 Increment: Real M38 Resident NCC Winsorized Subset 50

- Gate: 08
- Date: 2026-05-13
- Status: completed
- Commit: pending

## Completed

- Built a larger real M38 subset from the existing
  `C:\gpwbpp_runs\final_m38_h_200\manifest.json`.
- Ran full-size resident CUDA calibration, resident NCC+subpixel translation
  registration, bilinear resident warp, and winsorized sigma integration.
- Verified output master, weight map, coverage map, low rejection map, and high
  rejection map are written for the 50-light run.
- This is the largest resident NCC pipeline test after wiring the new resident
  registration mode, but it is still below the final 200-light acceptance run.

## Commands Run

```powershell
$base='C:\gpwbpp_runs\final_m38_h_200'; $run=Join-Path $base 'gpwbpp_resident_ncc_winsorized_subset50'; .\.venv\Scripts\gpwbpp.exe subset --manifest (Join-Path $base 'manifest.json') --out (Join-Path $run 'manifest.json') --plan-out (Join-Path $run 'processing_plan.json') --filter H --exposure-s 600 --light-limit 50 --bias-limit 20 --dark-limit 20 --flat-limit 20
$base='C:\gpwbpp_runs\final_m38_h_200'; $run=Join-Path $base 'gpwbpp_resident_ncc_winsorized_subset50'; .\.venv\Scripts\gpwbpp.exe run --plan (Join-Path $run 'processing_plan.json') --out $run --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration translation_ncc_subpixel --resident-registration-max-shift 24 --resident-subpixel-radius-steps 2 --resident-subpixel-step 0.5
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Result

- Subset plan: executable, 0 warnings.
- Selected subset summary:
  - 71 total frames.
  - 50 light frames.
  - 11 dark frames.
  - 6 bias frames.
  - 4 flat frames.
  - Shape: 9600x6422.
- Resident CUDA run: completed through integration.
- Full pytest after the run: 100 passed.

## Real M38 Resident Run Result

- Run directory:
  `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_subset50`
- Registration model: `translation_ncc_subpixel`.
- Registration results: 50 total; 1 reference, 49 ok, 0 failed.
- Translation range:
  - dx min/max: -25.0 / 16.5 px.
  - dy min/max: -16.5 / 4.5 px.
- Resident timing:
  - master build/load: 9.420 s.
  - resident allocate and master upload: 0.218 s.
  - light read/upload/calibrate: 9.493 s.
  - per-frame registration mean: 0.383 s.
  - resident winsorized integration: 0.184 s.
  - output write: 0.841 s.
- Memory estimate:
  - calibrated stack: 11.483 GiB.
  - resident base: 12.402 GiB.
  - estimated peak: 12.861 GiB.
- Output diagnostics:
  - finite pixels: 61,651,200.
  - nonfinite pixels: 0.
  - mean: 111.366.
  - std: 254.516.
  - min/max: -1937.644 / 50244.941.

## CUDA Availability

- CUDA native extension: available.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Artifacts

- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_subset50\manifest.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_subset50\processing_plan.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_subset50\registration_results.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_subset50\resident_artifacts.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_subset50\integration_results.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_subset50\integration\resident_master_H.fits`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_subset50\integration\resident_weight_map_H.fits`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_subset50\integration\resident_coverage_map_H.fits`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_subset50\integration\resident_low_rejection_map_H.fits`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_subset50\integration\resident_high_rejection_map_H.fits`

## Known Limitations

- This is a 50-light real subset, not the final 200-light WBPP/GPWBPP acceptance
  comparison.
- Matching calibration selection still yields only 11 dark, 6 bias, and 4 flat
  frames for this subset; final acceptance must use a selection satisfying the
  user target of at least 20 calibration frames per type.
- Resident registration is translation-only and has no star-model RMS yet.
- Resident Local Normalization is still disabled.
- Winsorized sigma is the current two-stage mean/std approximation, not a
  byte-for-byte PixInsight FastIntegration reproduction.

## Next Step

- Build or select a 200-light plan that also includes at least 20 matching bias,
  dark, and flat frames, then run the same resident mode and compare with the
  existing WBPP black-box artifacts.

## Clean-room Compliance

- No official PixInsight WBPP/PJSR source was read, copied, summarized, or
  modified.
- Only GPWBPP outputs, user-provided M38 data, and black-box comparison artifacts
  were used.
- Original input data directories were not modified.
