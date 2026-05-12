# Gate 08 Increment: Real M38 Resident NCC Subset Run

- Gate: 08
- Date: 2026-05-13
- Status: completed
- Commit: pending

## Completed

- Built a real M38 subset from the existing
  `C:\gpwbpp_runs\final_m38_h_200\manifest.json`.
- Ran `gpwbpp run --memory-mode resident` with the new
  `translation_ncc_subpixel` resident CUDA registration mode on full-size
  calibrated frames.
- Verified that non-reference frames are registered on the resident stack before
  integration.
- Kept the test subset modest: 12 light frames and the matching calibration
  frames selected by the existing subset planner.

## Commands Run

```powershell
$base='C:\gpwbpp_runs\final_m38_h_200'; $run=Join-Path $base 'gpwbpp_resident_ncc_subset12'; New-Item -ItemType Directory -Force -Path $run | Out-Null; .\.venv\Scripts\gpwbpp.exe subset --manifest (Join-Path $base 'manifest.json') --out (Join-Path $run 'manifest.json') --plan-out (Join-Path $run 'processing_plan.json') --filter H --exposure-s 600 --light-limit 12 --bias-limit 10 --dark-limit 10 --flat-limit 10
$base='C:\gpwbpp_runs\final_m38_h_200'; $run=Join-Path $base 'gpwbpp_resident_ncc_subset12'; .\.venv\Scripts\gpwbpp.exe run --plan (Join-Path $run 'processing_plan.json') --out $run --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection none --integration-weighting none --flat-floor 0.05 --resident-registration translation_ncc_subpixel --resident-registration-max-shift 24 --resident-subpixel-radius-steps 2 --resident-subpixel-step 0.5
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Result

- Subset plan: executable, 0 warnings.
- Selected subset summary:
  - 32 total frames.
  - 12 light frames.
  - 10 dark frames.
  - 6 bias frames.
  - 4 flat frames.
  - Shape: 9600x6422.
- Resident CUDA run: completed through integration.
- Full pytest after the run: 100 passed.

## Real M38 Resident Run Result

- Run directory:
  `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_subset12`
- Registration model: `translation_ncc_subpixel`.
- Registration results: 12 total; 1 reference, 11 ok, 0 failed.
- Measured examples:
  - `S000022`: dx=0.5, dy=0.0.
  - `S000023`: dx=4.5, dy=0.5.
  - `S000024`: dx=4.5, dy=0.5.
  - Last frame `S000032`: dx=-4.5, dy=-2.5.
- Resident timing:
  - master build/load: 9.184 s.
  - resident allocate and master upload: 0.145 s.
  - light read/upload/calibrate: 2.306 s.
  - per-frame registration mean: 0.358 s.
  - resident integration: 0.075 s.
  - output write: 0.364 s.
- Memory estimate:
  - calibrated stack: 2.756 GiB.
  - resident base: 3.675 GiB.
  - estimated peak: 4.134 GiB.

## CUDA Availability

- CUDA native extension: available.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Artifacts

- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_subset12\manifest.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_subset12\processing_plan.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_subset12\registration_results.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_subset12\resident_artifacts.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_subset12\integration_results.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_subset12\integration\resident_master_H.fits`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_subset12\integration\resident_weight_map_H.fits`

## Known Limitations

- This was a 12-light real subset, not the final 200-light acceptance run.
- The subset planner could only select 6 bias and 4 flat frames matching the
  requested constraints; this is acceptable for this Gate-08 smoke/scale step
  but not sufficient for the final 20+ calibration-frame target.
- Resident registration remains translation-only and has no star-model RMS yet.
- Local Normalization remains disabled in the resident path.
- Rejection was disabled for this timing sanity run.

## Next Step

- Scale to a larger real subset with all available calibration frames and
  enable winsorized/sigma rejection, then compare outputs against the existing
  WBPP black-box artifacts before the final 200-light run.

## Clean-room Compliance

- No official PixInsight WBPP/PJSR source was read, copied, summarized, or
  modified.
- Only GPWBPP outputs, user-provided M38 data, and black-box comparison artifacts
  were used.
- Original input data directories were not modified.
