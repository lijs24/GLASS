# Gate 08 Resident Similarity Quality Gate Checkpoint

## Gate
Gate 08: Registration

## Completed contents
- Added production quality gates for resident CUDA `similarity_cuda_catalog`.
- New registration policy fields:
  - `cuda_catalog_min_pixel_ncc`
  - `cuda_catalog_min_selected_seed_inliers`
- Frames that fail these quality gates are marked `failed`, assigned zero integration weight, and are not silently warped into integration.
- Recorded the quality gate thresholds in `resident_artifacts.json`.
- Added tests that verify both accepted and rejected resident similarity registrations.

## Commands run
- `.venv\Scripts\python -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_catalog_aligns_shifted_pair tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_catalog_rejects_low_quality_matrix`
- `.venv\Scripts\python -m pytest -q tests/test_resident_cuda_run.py tests/test_gpu_registration_search.py tests/test_gpu_star_detect.py`
- `.venv\Scripts\python -m pytest -q`

## Test results
- Targeted quality-gate tests: `2 passed in 0.36s`.
- Resident/CUDA registration affected suite: `46 passed in 1.02s`.
- Full test suite: `150 passed in 8.84s`.

## Real-data diagnosis that motivated the fix
- A 200-light resident rot-pi run completed with `200/200` status `ok`, but diagnostics showed `8` frames with pixel NCC below `0.75`.
- Several false-positive frames had only `4-5` selected seed inliers and were being allowed into integration.
- This violated the Gate 08 requirement that failed or unreliable registration must not silently enter integration.

## CUDA availability
- CUDA available: yes.
- Native backend loaded: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Reported VRAM: 97886 MiB.

## Known limitations
- Threshold choice remains data-dependent; for the current M38 200-light validation the next run should use `cuda_catalog_min_pixel_ncc=0.75` and `cuda_catalog_min_selected_seed_inliers=8`.
- Quality diagnostics are still emitted as warning strings in `registration_results.json`; a structured diagnostics schema remains desirable.

## Next step
- Re-run the 200-light resident rot-pi validation with the quality gates enabled, then compare against the existing astroalign/WBPP baseline artifacts.

## Clean-room compliance
- Compliant.
- No PixInsight/WBPP/PJSR source, script internals, or installation directories were read or modified.
- The fix uses GLASS's clean-room CUDA registration diagnostics.
