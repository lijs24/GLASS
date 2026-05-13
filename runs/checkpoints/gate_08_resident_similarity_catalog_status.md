# Gate 08 Resident Similarity Catalog Checkpoint

## Gate
Gate 08: Registration

## Completed contents
- Added a production resident CUDA registration mode: `similarity_cuda_catalog`.
- The new mode operates after light calibration has uploaded frames into `ResidentCalibratedStack`.
- For each moving frame, it:
  - detects bounded resident GPU star catalogs with `star_top_candidates`;
  - optionally uses resident GPU NCC as a translation prior;
  - estimates a similarity matrix with CUDA catalog matching;
  - refines the selected matrix plus top-k candidates with resident multi-seed pixel metrics;
  - applies the final matrix with resident CUDA bilinear matrix warp.
- Added CLI support through `gpwbpp run --resident-registration similarity_cuda_catalog`.
- Added a resident CUDA smoke test that scans, plans, runs, and verifies a shifted two-light synthetic pair through the new mode.

## Commands run
- `.\\.venv\\Scripts\\python -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_catalog_aligns_shifted_pair`
- `.\\.venv\\Scripts\\python -m pytest -q tests/test_resident_cuda_run.py`
- `.\\.venv\\Scripts\\python -m pytest -q`
- `.\\.venv\\Scripts\\gpwbpp.exe run --help | Select-String -Pattern "similarity_cuda_catalog|resident-registration" -Context 1,2`
- `@' ... '@ | .\\.venv\\Scripts\\python -` to query CUDA capability through `gpwbpp_cuda`.

## Test results
- New resident similarity test: `1 passed in 0.25s`.
- Resident CUDA run tests: `8 passed in 0.63s`.
- Full test suite: `145 passed in 7.29s`.

## CUDA availability
- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Reported VRAM: 97886 MiB.
- Native backend loaded: yes.

## Known limitations
- Resident similarity mode currently uses resident top-flux catalogs, not the full grid-top-NMS selector used by the standalone benchmark path.
- Catalog arrays are small diagnostic/control data and still cross the Python boundary; calibrated image pixels, refinement, and matrix warp remain resident in GPU memory.
- Diagnostics are stored in registration warnings for now; a structured per-frame resident similarity diagnostics block should be added before large-scale production comparison runs.
- This is still similarity registration; affine/homography resident fitting remains future work.

## Next step
- Run `similarity_cuda_catalog` on a small real calibrated M38 subset and compare its per-frame registration outputs against the previous astroalign/external-matrix path before using it in the 200-light heavy integration benchmark.

## Clean-room compliance
- Compliant.
- No PixInsight/WBPP/PJSR source, script internals, or installation directories were read or modified.
- The implementation uses GPWBPP CUDA primitives and clean-room catalog/pixel metric registration logic.
