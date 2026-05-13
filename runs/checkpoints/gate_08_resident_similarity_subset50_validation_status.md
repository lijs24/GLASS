# Gate 08 Resident Similarity 50-Light Validation Checkpoint

## Gate
Gate 08: Registration

## Completed contents
- Ran a 50-light real M38 validation with production resident CUDA `similarity_cuda_catalog`.
- Used fixed threshold `350`, resident grid-top-NMS catalogs, resident NCC prior, and GPU star-core seed preselection/guard.
- Increased `resident_registration_max_shift` to `96` and prior radius to `8` after diagnosing that the failed 50-light attempt contained true shifts up to about `75 px`.
- Verified all 50 frames completed registration/integration with no failed frames.
- Compared resident translations against the existing astroalign similarity registration artifact for the same 50-light subset.
- Generated an HTML report for the validation run.

## Commands run
- `.venv\Scripts\gpwbpp.exe run --plan C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_similarity_catalog_subset50_starcore8_fixed350\processing_plan.json --out C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_similarity_catalog_subset50_starcore8_fixed350_shift96 --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection none --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_catalog --resident-star-threshold 350 --resident-star-max-candidates 96 --resident-star-tolerance-px 3.0 --resident-registration-max-shift 96 --resident-ncc-sample-stride 4 --resident-subpixel-radius-steps 4 --resident-subpixel-step 0.25 --resident-star-prior ncc --resident-star-prior-radius-px 8 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-core-preselect-top-k 8 --reference-frame-id LIGHT_H_0001`
- `.venv\Scripts\gpwbpp.exe report --run C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_similarity_catalog_subset50_starcore8_fixed350_shift96 --out C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_similarity_catalog_subset50_starcore8_fixed350_shift96\report.html`

## Test results
- No code changed after commit `221cf22`; this checkpoint records a real-data scale validation.
- Most recent full suite before this run: `149 passed in 7.34s`.

## Failed parameter attempt
- Attempted the same 50-light run with `resident_registration_max_shift=24` and prior radius `4`.
- Result: `43/50` ok/reference, `7` failed.
- Diagnosis: existing astroalign similarity output shows several late frames have true translations around `-50` to `-75 px`; `max_shift=24` was insufficient.

## Real-data validation
- Input plan: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_similarity_catalog_subset50_starcore8_fixed350\processing_plan.json`
- Output run: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_similarity_catalog_subset50_starcore8_fixed350_shift96`
- Report: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_similarity_catalog_subset50_starcore8_fixed350_shift96\report.html`
- Frames: 50 H-filter M38 lights, full shape `6422x9600`.
- Calibration frames in plan: `20` bias, `20` dark, `20` flat.
- Registration mode: `similarity_cuda_catalog`.
- Reference frame: `S000061`.
- Star threshold: fixed `350`.
- Catalog selector: resident grid-top-NMS with `24x16` cells.
- Star max candidates: `96`.
- Similarity top-k: `32`.
- Star-core preselect top-k: `8`.
- Max shift: `96`.
- Prior radius: `8`.
- Registration result:
  - row count: `50`
  - ok/reference frames: `50`
  - failed frames: `0`
  - inliers min/max: `38/64`
  - max fit RMS: `1.8141518831253052 px`
  - mean fit RMS: `1.3170007065850862 px`
  - min pixel NCC: `0.892177`
  - mean pixel NCC: `0.9391480612244898`
  - translation delta vs astroalign max: `1.395028813214906 px`
  - translation delta vs astroalign mean: `0.32238281489519865 px`
  - translation deltas greater than `2 px`: `0`
  - star guard statuses: `kept_star_core_metric=29`, `replaced_pixel_metric_with_star_core_metric=20`
- Timing:
  - total elapsed: `378.4687266999972 s`
  - per-frame registration mean: `7.122048972001067 s`
  - light read/upload/calibrate: `19.831604400009383 s`
  - resident integration: `0.07822379999561235 s`
  - output write: `0.33450789999915287 s`
- Memory estimate:
  - calibrated stack: `11.483430862426758 GiB`
  - resident base: `12.402105331420898 GiB`
  - estimated peak: `12.861442752182484 GiB`

## CUDA availability
- CUDA available: yes.
- Native backend loaded: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Reported VRAM: 97886 MiB.

## Known limitations
- Registration is green at 50 frames but still dominates runtime; 200-light registration is expected to take roughly four times longer unless optimized further.
- This run used `integration-rejection none` and `local-normalization off`; those remain later scale-up steps.
- Detailed resident similarity diagnostics are still emitted as warning strings rather than a structured diagnostics object.

## Next step
- Run the final 200-light validation with `resident_registration_max_shift=96`, fixed threshold `350`, grid-top-NMS, and star-core preselection; then compare timing and output against the WBPP/astroalign baseline artifacts.

## Clean-room compliance
- Compliant.
- No PixInsight/WBPP/PJSR source, script internals, or installation directories were read or modified.
- Comparison used user-generated astroalign/GPWBPP artifacts and clean-room CUDA registration logic.
