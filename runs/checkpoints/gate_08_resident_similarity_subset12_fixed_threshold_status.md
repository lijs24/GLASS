# Gate 08 Resident Similarity 12-Light Fixed-Threshold Checkpoint

## Gate
Gate 08: Registration

## Completed contents
- Re-ran the same 12-light real M38 resident CUDA `similarity_cuda_catalog` validation with a fixed star threshold.
- Verified that fixed threshold `350` preserves the same 12/12 registration success as the auto-threshold trial run.
- Confirmed a large registration speed improvement by avoiding six auto-threshold catalog fit trials per frame.
- Generated an HTML report for the fixed-threshold validation run.

## Commands run
- `.venv\Scripts\gpwbpp.exe run --plan C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_similarity_catalog_subset12_starcore8\processing_plan.json --out C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_similarity_catalog_subset12_starcore8_fixed350 --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection none --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_catalog --resident-star-threshold 350 --resident-star-max-candidates 96 --resident-star-tolerance-px 3.0 --resident-registration-max-shift 24 --resident-ncc-sample-stride 4 --resident-subpixel-radius-steps 4 --resident-subpixel-step 0.25 --resident-star-prior ncc --resident-star-prior-radius-px 4 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-core-preselect-top-k 8 --reference-frame-id LIGHT_H_0001`
- `.venv\Scripts\gpwbpp.exe report --run C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_similarity_catalog_subset12_starcore8_fixed350 --out C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_similarity_catalog_subset12_starcore8_fixed350\report.html`

## Test results
- No code changed after commit `221cf22`; this checkpoint records a real-data parameter validation.
- Most recent full suite before this run: `149 passed in 7.34s`.

## Real-data validation
- Input plan: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_similarity_catalog_subset12_starcore8\processing_plan.json`
- Output run: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_similarity_catalog_subset12_starcore8_fixed350`
- Report: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_similarity_catalog_subset12_starcore8_fixed350\report.html`
- Frames: 12 H-filter M38 lights, `S000021` through `S000032`, full shape `6422x9600`.
- Registration mode: `similarity_cuda_catalog`.
- Star threshold mode: fixed.
- Star threshold: `350`.
- Catalog selector: resident grid-top-NMS with `24x16` cells.
- Star max candidates: `96`.
- Similarity top-k: `32`.
- Star-core preselect top-k: `8`.
- Registration result:
  - row count: `12`
  - ok/reference frames: `12`
  - failed frames: `0`
  - inliers min/max: `41/64`
  - max fit RMS: `1.6320525407791138 px`
  - min pixel NCC: `0.939968`
  - mean pixel NCC: `0.9585607272727272`
  - star guard statuses: `kept_star_core_metric=7`, `replaced_pixel_metric_with_star_core_metric=4`
- Timing:
  - fixed-threshold total elapsed: `90.04560349998064 s`
  - prior auto-threshold total elapsed: `425.300167999987 s`
  - fixed-threshold per-frame registration mean: `6.2258046416730695 s`
  - prior auto-threshold per-frame registration mean: `34.183201733321766 s`
  - speedup vs prior auto-threshold validation: about `4.72x` total and `5.49x` per-frame registration.
  - light read/upload/calibrate: `12.301200999994762 s`
  - resident integration: `0.07150419999379665 s`
- Memory estimate:
  - calibrated stack: `2.756023406982422 GiB`
  - resident base: `3.6746978759765625 GiB`
  - estimated peak: `4.134035155177116 GiB`

## CUDA availability
- CUDA available: yes.
- Native backend loaded: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Reported VRAM: 97886 MiB.

## Known limitations
- Fixed threshold `350` is validated for this M38 H subset; other targets/filters still need either auto-threshold calibration or a data-driven threshold selection pass.
- Registration remains the bottleneck, but fixed threshold makes 50-light and 200-light validation practical enough to run next.
- This checkpoint still uses `integration-rejection none` and `local-normalization off`.

## Next step
- Run a 50-light validation with fixed threshold `350`, resident grid-top-NMS, and star-core preselection before attempting the final 200-light WBPP-vs-GPWBPP comparison.

## Clean-room compliance
- Compliant.
- No PixInsight/WBPP/PJSR source, script internals, or installation directories were read or modified.
- This is a parameter validation using user-provided image data and GPWBPP clean-room CUDA code.
