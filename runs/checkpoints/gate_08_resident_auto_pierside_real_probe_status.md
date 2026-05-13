# Gate 08 Increment: Real M38 Auto-PIERSIDE Probe

## Gate

Gate 08 - Registration.

## Completed Content

- Ran a real M38 three-light resident CUDA probe with `--resident-star-prior auto_pierside`.
- Selected frames:
  - `F000061` / `LIGHT_H_0001.fits` as reference, `PIERSIDE=West`
  - `F000062` / `LIGHT_H_0002.fits` as same-side moving frame, `PIERSIDE=West`
  - `F000137` / `LIGHT_H_0077.fits` as flipped-side moving frame, `PIERSIDE=East`
- Confirmed the resident diagnostics dispatch per frame:
  - `F000062`: `pierside_same`, effective prior `ncc`, `top_k=32`, `max_abs_rotation_rad=0.01`
  - `F000137`: `pierside_flipped`, effective prior `none`, `top_k=64`, `max_abs_rotation_rad=3.2`
- Both moving frames registered successfully and passed quality gates.

## Commands Run

- Generated filtered plan:
  - `C:\glass_runs\final_m38_h_200\glass_resident_similarity_auto_pierside_probe3_flip\processing_plan.json`
- Resident CUDA run:
  - `.venv\Scripts\glass.exe run --plan C:\glass_runs\final_m38_h_200\glass_resident_similarity_auto_pierside_probe3_flip\processing_plan.json --out C:\glass_runs\final_m38_h_200\glass_resident_similarity_auto_pierside_probe3_flip --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection none --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_catalog --resident-star-threshold 350 --resident-star-max-candidates 128 --resident-star-tolerance-px 3.0 --resident-registration-max-shift 96 --resident-ncc-sample-stride 4 --resident-subpixel-radius-steps 4 --resident-subpixel-step 0.25 --resident-star-prior auto_pierside --resident-star-prior-radius-px 8 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-core-preselect-top-k 8 --reference-frame-id F000061`

## Test Results

- Full pytest before this probe: `151 passed in 7.60s`.
- Real probe run completed through integration.
- `run_state.json` completed stages:
  - `master_calibration`
  - `resident_light_calibration`
  - `resident_registration`
  - `resident_integration`
- `failed_frame_count=0`.

## Real Probe Results

- Output directory:
  - `C:\glass_runs\final_m38_h_200\glass_resident_similarity_auto_pierside_probe3_flip`
- Registration diagnostics:
  - `F000062`: status `ok`, inliers `89`, RMS `0.7880619168 px`, pixel NCC `0.976626`
  - `F000137`: status `ok`, inliers `62`, RMS `1.3638278246 px`, pixel NCC `0.897666`
- Timing:
  - `master_build_or_load`: `9.7307 s`
  - `light_read_upload_calibrate`: `10.3336 s`
  - `per_frame_registration_mean`: `15.6435 s`
  - `resident_integration`: `0.0692 s`

## CUDA Availability

- CUDA is available.
- Device observed by current environment and artifacts: NVIDIA RTX PRO 6000 Blackwell Workstation Edition, compute capability 12.0, about 97,886 MiB VRAM.

## Known Limitations

- This was a 3-light probe, not the final 200-light timing comparison.
- The flipped frame path is still substantially more expensive than the same-side path.
- The `F000062` same-side matrix remains GLASS-owned and not forced to match astroalign exactly.
- The metadata ID offset is important: `F000061` maps to `LIGHT_H_0001.fits` because calibration frames occupy earlier frame IDs in the full manifest.

## Next Step

Run a larger real subset with mixed pier sides, then the full 200-light resident similarity run with `auto_pierside`. Compare registration timing and final master against the previous 200-light qgate artifact and the WBPP black-box output.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source was read or modified.
- Only FITS headers and GLASS-owned CUDA registration diagnostics were used.
- Original input data directories were not modified.
