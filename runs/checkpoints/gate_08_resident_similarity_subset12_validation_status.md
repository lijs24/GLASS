# Gate 08 Resident Similarity 12-Light Validation Checkpoint

## Gate
Gate 08: Registration

## Completed contents
- Ran a 12-light real M38 validation with the production resident CUDA `similarity_cuda_catalog` path.
- Used resident grid-top-NMS star catalogs and resident GPU star-core seed preselection/guard.
- Verified all 12 frames completed registration/integration with no failed frames.
- Generated an HTML report for the validation run.

## Commands run
- `.venv\Scripts\python -m pytest -q tests/test_resident_cuda_run.py tests/test_gpu_registration_search.py tests/test_gpu_star_detect.py`
- `.venv\Scripts\python -m pytest -q`
- `.venv\Scripts\glass.exe run --plan C:\glass_runs\final_m38_h_200\glass_resident_similarity_catalog_subset12_starcore8\processing_plan.json --out C:\glass_runs\final_m38_h_200\glass_resident_similarity_catalog_subset12_starcore8 --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection none --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_catalog --resident-star-threshold 0 --resident-star-max-candidates 96 --resident-star-tolerance-px 3.0 --resident-registration-max-shift 24 --resident-ncc-sample-stride 4 --resident-subpixel-radius-steps 4 --resident-subpixel-step 0.25 --resident-star-prior ncc --resident-star-prior-radius-px 4 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-core-preselect-top-k 8 --reference-frame-id LIGHT_H_0001`
- `.venv\Scripts\glass.exe report --run C:\glass_runs\final_m38_h_200\glass_resident_similarity_catalog_subset12_starcore8 --out C:\glass_runs\final_m38_h_200\glass_resident_similarity_catalog_subset12_starcore8\report.html`

## Test results
- Resident/CUDA registration affected suite: `45 passed in 0.83s`.
- Full test suite: `149 passed in 7.34s`.

## Real-data validation
- Input plan: `C:\glass_runs\final_m38_h_200\glass_resident_similarity_catalog_subset12_starcore8\processing_plan.json`
- Output run: `C:\glass_runs\final_m38_h_200\glass_resident_similarity_catalog_subset12_starcore8`
- Report: `C:\glass_runs\final_m38_h_200\glass_resident_similarity_catalog_subset12_starcore8\report.html`
- Frames: 12 H-filter M38 lights, `S000021` through `S000032`, full shape `6422x9600`.
- Registration mode: `similarity_cuda_catalog`.
- Catalog selector: resident grid-top-NMS with `24x16` cells.
- Star max candidates: `96`.
- Similarity top-k: `32`.
- Star-core preselect top-k: `8`.
- Star-core guard: enabled.
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
  - total elapsed: `425.300167999987 s`
  - light read/upload/calibrate: `12.089642700040713 s`
  - per-frame registration mean: `34.183201733321766 s`
  - resident integration: `0.07120960002066568 s`
  - output write: `0.33645220001926646 s`
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
- Registration is now robust on this 12-light subset, but registration time is still dominated by per-frame catalog similarity trial/refinement orchestration.
- The run used `integration-rejection none` and `local-normalization off`; later gates must re-enable LN and rejection after registration scaling is stable.
- `registration_results.json` still stores detailed resident similarity diagnostics in warning strings.
- This is a validation checkpoint, not the final 200-light WBPP-vs-GLASS benchmark.

## Next step
- Use the same parameters on a 50-light subset, profile registration trial/refinement time, and then scale to the final 200-light benchmark.

## Clean-room compliance
- Compliant.
- No PixInsight/WBPP/PJSR source, script internals, or installation directories were read or modified.
- The validation used user-provided astronomical image data and GLASS's clean-room resident CUDA registration path.
