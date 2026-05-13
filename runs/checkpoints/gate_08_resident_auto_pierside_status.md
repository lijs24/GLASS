# Gate 08 Increment: Resident CUDA Auto-PIERSIDE Registration Dispatch

## Gate

Gate 08 - Registration.

## Completed Content

- Added `--resident-star-prior auto_pierside` for resident CUDA `similarity_cuda_catalog`.
- The mode reads `PIERSIDE` from `FrameRecord.header_summary` or FITS headers only.
- Same pier-side frames use the fast NCC-constrained similarity prior.
- Opposite pier-side frames disable the NCC prior and use a wider rotation search for meridian-flip pairs.
- Resident registration diagnostics now record effective prior, orientation mode, PIERSIDE values, effective top-k, and effective max rotation.
- `resident_artifacts.json` records the same-side and flipped-side dispatch policy.
- Updated CUDA backend documentation.

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py tests/test_gpu_registration_search.py tests/test_gpu_star_detect.py`
- `.venv\Scripts\python.exe -m pytest -q`
- Metadata-only real header dispatch probe:
  - `LIGHT_H_0061.fits -> LIGHT_H_0062.fits`: `pierside_same`, effective prior `ncc`
  - `LIGHT_H_0061.fits -> LIGHT_H_0077.fits`: `pierside_flipped`, effective prior `none`
  - `LIGHT_H_0061.fits -> LIGHT_H_0153.fits`: `pierside_flipped`, effective prior `none`

## Test Results

- Targeted tests: `47 passed in 0.96s`
- Full suite: `151 passed in 7.60s`

## CUDA Availability

- CUDA is available.
- Device observed by existing benchmark artifacts: NVIDIA RTX PRO 6000 Blackwell Workstation Edition, compute capability 12.0, about 97,886 MiB VRAM.

## Known Limitations

- This is a dispatch and diagnostics improvement, not a new matcher.
- The same-side path still depends on the NCC prior being a good coarse guide after calibration.
- The flipped-side path widens the search and is therefore still slower than same-side registration.
- `PIERSIDE` is not yet promoted into the core metadata header map for every scan output; the resident path falls back to metadata-only FITS header reads when the manifest lacks it.
- Current real 200-light resident similarity run remains slower than WBPP; this change prepares the next faster mixed-orientation run by avoiding the expensive flipped-frame search on same-side frames.

## Next Step

Run a small then full real M38 resident similarity test with `--resident-star-prior auto_pierside`, same-side top-k kept small, and flipped-side top-k/rotation widened. Compare registration failures, per-frame registration timing, and final master against the previous qgate run and WBPP black-box output.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source was read or modified.
- The implementation uses FITS metadata and GLASS-owned CUDA registration code only.
- Input data directories were not modified.
