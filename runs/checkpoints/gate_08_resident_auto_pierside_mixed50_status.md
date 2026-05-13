# Gate 08 Increment: Real M38 Mixed PIERSIDE 50-Light Probe

## Gate

Gate 08 - Registration.

## Completed Content

- Ran a 50-light real M38 resident CUDA registration/integration probe with mixed pier sides.
- Selected 25 West-side lights (`F000061`-`F000085`) and 25 East-side lights (`F000137`-`F000161`), with `F000061` as reference.
- Used `--resident-star-prior auto_pierside` so same-side frames use the fast NCC prior and flipped-side frames use no NCC prior with a wider rotation search.
- Generated a run report after completion.

## Commands Run

- Generated filtered plan:
  - `C:\glass_runs\final_m38_h_200\glass_resident_similarity_auto_pierside_mixed50\processing_plan.json`
- Resident CUDA run:
  - `.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\final_m38_h_200\glass_resident_similarity_auto_pierside_mixed50\processing_plan.json --out C:\glass_runs\final_m38_h_200\glass_resident_similarity_auto_pierside_mixed50 --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection none --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_catalog --resident-star-threshold 350 --resident-star-max-candidates 128 --resident-star-tolerance-px 3.0 --resident-registration-max-shift 96 --resident-ncc-sample-stride 4 --resident-subpixel-radius-steps 4 --resident-subpixel-step 0.25 --resident-star-prior auto_pierside --resident-star-prior-radius-px 8 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-core-preselect-top-k 8 --reference-frame-id F000061`
- Report:
  - `.venv\Scripts\python.exe -m glass.cli report --run C:\glass_runs\final_m38_h_200\glass_resident_similarity_auto_pierside_mixed50 --out C:\glass_runs\final_m38_h_200\glass_resident_similarity_auto_pierside_mixed50\report.html`

## Test Results

- Full pytest before this probe: `151 passed in 11.08s`.
- Real mixed50 run completed through integration.
- `run_state.json` completed stages:
  - `master_calibration`
  - `resident_light_calibration`
  - `resident_registration`
  - `resident_integration`

## Real Probe Results

- Output directory:
  - `C:\glass_runs\final_m38_h_200\glass_resident_similarity_auto_pierside_mixed50`
- Report:
  - `C:\glass_runs\final_m38_h_200\glass_resident_similarity_auto_pierside_mixed50\report.html`
- Registration rows: `50`
- Status counts:
  - `reference`: `1`
  - `ok`: `48`
  - `failed`: `1`
- Orientation dispatch counts:
  - `reference`: `1`
  - `pierside_same`: `25`
  - `pierside_flipped`: `24`
- Same-side diagnostics:
  - `top_k=32`
  - pixel NCC min/mean/max: `0.883599 / 0.94622184 / 0.976626`
  - inliers min/mean/max: `48 / 62.44 / 89`
  - RMS min/mean/max: `0.7880619168 / 1.2354123664 / 1.6321291924 px`
- Flipped-side diagnostics:
  - `top_k=64`
  - successful pixel NCC min/mean/max includes one rejected low-quality candidate in the full NCC set; successful frames were all above the quality gate
  - successful inliers min/mean/max: `55 / 59.7826 / 62`
  - successful RMS min/mean/max: `1.1270568371 / 1.2675901651 / 1.4213343859 px`
- Failed frame:
  - `F000160`
  - reason: `pixel_ncc 0.00938479 < 0.75; selected_seed_inliers 3 < 16`
  - orientation mode: `pierside_flipped`

## Timing

- `master_build_or_load`: `0.2636 s` (masters already cached)
- `light_read_upload_calibrate`: `11.9240 s`
- `per_frame_registration_mean`: `24.1067 s`
- `resident_integration`: `0.0784 s`
- `output_write`: `0.3508 s`
- Estimated peak resident memory: `12.8614 GiB`

## CUDA Availability

- CUDA is available.
- Device observed by current environment and artifacts: NVIDIA RTX PRO 6000 Blackwell Workstation Edition, compute capability 12.0, about 97,886 MiB VRAM.

## Known Limitations

- This mixed-pier probe is still too slow for the final 200-light speed objective; flipped-side descriptor search remains the dominant cost.
- The flipped-side mode is robust enough to reject a bad frame, but it still uses a brute-force two-star similarity candidate strategy rather than a polygonal descriptor/RANSAC matcher.
- Registration rows are written only after the resident stage completes; future long real runs need incremental registration diagnostics for better resume/observability.

## Next Step

Implement or integrate a clean-room/open-source asterism descriptor matcher (quad/pentagon-style) and port candidate scoring to CUDA. This should reduce false seed volume and make flipped-side registration much faster than the current wide brute-force search.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source was read or modified.
- The run used FITS metadata, GLASS-owned CUDA registration, and GLASS-generated diagnostics only.
- Original input data directories were not modified.
