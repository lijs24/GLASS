# Gate 12 Increment: Real M38 200-Light Resident CUDA Run and WBPP Compare

- Gate: 12
- Date: 2026-05-13
- Status: completed as a resident CUDA timing/validation increment
- Commit: pending

## Completed

- Built a real M38 all-compatible subset satisfying the user's scale target:
  200 light frames plus 20 bias, 20 dark, and 20 flat frames.
- Ran `gpwbpp run --memory-mode resident` with:
  - resident CUDA calibration;
  - resident CUDA NCC + subpixel translation registration;
  - resident bilinear translation warp;
  - resident winsorized sigma integration;
  - output master, weight, coverage, low rejection, and high rejection maps.
- Compared the GPWBPP master against the existing PixInsight/WBPP black-box
  FastIntegration master.
- Verified GPWBPP was faster on this run and produced a shape-matching output
  with small scaled median absolute difference.

## Commands Run

```powershell
$base='C:\gpwbpp_runs\final_m38_h_200'; $run=Join-Path $base 'gpwbpp_resident_ncc_winsorized_allcal_200'; New-Item -ItemType Directory -Force -Path $run | Out-Null; .\.venv\Scripts\gpwbpp.exe subset --manifest (Join-Path $base 'manifest.json') --out (Join-Path $run 'manifest.json') --plan-out (Join-Path $run 'processing_plan.json') --filter H --exposure-s 600 --light-limit 200 --all-compatible-calibration
$base='C:\gpwbpp_runs\final_m38_h_200'; $run=Join-Path $base 'gpwbpp_resident_ncc_winsorized_allcal_200'; .\.venv\Scripts\gpwbpp.exe run --plan (Join-Path $run 'processing_plan.json') --out $run --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration translation_ncc_subpixel --resident-registration-max-shift 64 --resident-subpixel-radius-steps 2 --resident-subpixel-step 0.5
$run='C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_allcal_200'; $ref='C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf'; .\.venv\Scripts\gpwbpp.exe compare --gpwbpp (Join-Path $run 'integration\resident_master_H.fits') --reference $ref --out (Join-Path $run 'resident_vs_wbpp_fastintegration_scaled_compare.html') --gpwbpp-time-seconds 363.1756594000035 --reference-time-seconds 1092.541 --gpwbpp-label "GPWBPP resident NCC 200 scaled" --reference-label "PixInsight WBPP FastIntegration" --gpwbpp-scale 1.5259021896696422e-05 --clip-low 0 --clip-high 1
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Result

- 200-light subset plan: executable, 0 warnings.
- Resident CUDA run: completed through integration.
- Compare report: generated successfully.
- Full pytest after the run: 101 passed.

## Real M38 Resident Run Result

- Run directory:
  `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_allcal_200`
- Selected frames:
  - 200 light.
  - 20 bias.
  - 20 dark.
  - 20 flat.
  - Shape: 9600x6422.
- Master frame input counts used by resident run:
  - bias_count: 20.
  - dark_count: 20.
  - flat_count: 20.
- Registration model: `translation_ncc_subpixel`.
- Registration results: 200 total; 1 reference, 199 ok, 0 failed.
- Translation range:
  - dx min/max: -65.0 / 38.5 px.
  - dy min/max: -59.5 / 65.0 px.
- Resident timing:
  - total run timing: 363.176 s.
  - master build/load: 18.324 s.
  - resident allocate and master upload: 0.514 s.
  - light read/upload/calibrate: 38.550 s.
  - per-frame registration mean: 1.513 s.
  - resident winsorized integration: 0.318 s.
  - output write: 0.832 s.
- Memory estimate:
  - calibrated stack: 45.934 GiB.
  - resident base: 46.852 GiB.
  - estimated peak: 47.312 GiB.

## WBPP Compare Result

- WBPP black-box elapsed: 1092.541 s.
- GPWBPP resident elapsed: 363.176 s.
- Speedup vs WBPP: 3.008x.
- Shape match: true.
- Scaled compare transform:
  - scale: 1 / 65535.
  - clip: [0, 1].
- Scaled direct diff:
  - median absolute diff: 8.15e-05.
  - p90 absolute diff: 2.70e-04.
  - p99 absolute diff: 7.52e-03.
  - RMS diff: 0.01344.
- Robust fit-pixel stats:
  - fit fraction: 0.9835.
  - fit-pixel RMS diff: 0.001809.
  - fit-pixel p99 absolute diff: 0.001568.

## CUDA Availability

- CUDA native extension: available.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Artifacts

- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_allcal_200\manifest.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_allcal_200\processing_plan.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_allcal_200\registration_results.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_allcal_200\resident_artifacts.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_allcal_200\integration_results.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_allcal_200\run_timing.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_allcal_200\integration\resident_master_H.fits`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_allcal_200\integration\resident_weight_map_H.fits`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_allcal_200\integration\resident_coverage_map_H.fits`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_allcal_200\integration\resident_low_rejection_map_H.fits`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_allcal_200\integration\resident_high_rejection_map_H.fits`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_allcal_200\resident_vs_wbpp_fastintegration_compare.html`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_allcal_200\resident_vs_wbpp_fastintegration_compare.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_allcal_200\resident_vs_wbpp_fastintegration_scaled_compare.html`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_allcal_200\resident_vs_wbpp_fastintegration_scaled_compare.json`

## Known Limitations

- This is not yet a complete WBPP-equivalent scientific result:
  Local Normalization remains disabled in the resident path.
- Resident registration is still translation-only and reports NCC diagnostics,
  not star-model RMS or affine/similarity transforms.
- Winsorized sigma is the current two-stage mean/std approximation, not a
  byte-for-byte PixInsight FastIntegration reproduction.
- GPWBPP is faster and broadly comparable after scaling, but differences remain
  and should be attributed to registration model, Local Normalization,
  weighting, rejection, crop/mask policy, and normalization semantics.

## Next Step

- Implement or wire resident Local Normalization and stronger star/descriptor
  registration before claiming full WBPP replacement equivalence.

## Clean-room Compliance

- No official PixInsight WBPP/PJSR source was read, copied, summarized, or
  modified.
- The WBPP result used here is a user-generated black-box output artifact.
- Original input data directories were not modified.
