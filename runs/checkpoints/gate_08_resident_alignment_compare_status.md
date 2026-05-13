# Gate 08 Resident Alignment Compare Status

- Gate: 08 registration / alignment diagnostics
- Date: 2026-05-13
- Status: code and tests passed; real two-frame comparison produced useful speed data but the autonomous catalog/pixel-refine path did not pass the strict matrix-agreement gate.

## Completed

- Exposed `ResidentCalibratedStack.refine_matrix_translation_candidates_to_reference()` through the native CUDA binding and Python shim.
- Added a CUDA resident multi-seed pixel-metric refine test using already-loaded device frames.
- Extended `benchmarks/compare_astroalign_gpu_alignment.py` with a resident catalog similarity pixel-refine path:
  - uploads the reference and moving image once into `ResidentCalibratedStack`;
  - scores top-K catalog similarity seed matrices on the GPU;
  - applies the selected matrix warp in-place on the resident moving frame;
  - downloads through `integrate_mean(weights=[0, 1])` for inspection and astroalign comparison.

## Commands

- `cmd /c "call \"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat\" -arch=x64 -host_arch=x64 && .venv\Scripts\cmake.exe --build build\native-cuda --config Release"`
- `.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py tests\test_benchmarks.py`
- `.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits" --moving "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits" --out "C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v29_resident_pixel_refine.json" --catalog-stars 64 --catalog-grid-top-cols 24 --catalog-grid-top-rows 16 --catalog-grid-top-per-cell 4 --catalog-nms-min-separation 64 --catalog-similarity-min-pair-distance 128 --catalog-similarity-min-scale 0.995 --catalog-similarity-max-scale 1.005 --catalog-similarity-max-rotation-rad 0.01 --catalog-similarity-top-k 8 --catalog-pixel-refine-radius 1.0 --catalog-pixel-refine-coarse-step 0.25 --catalog-pixel-refine-fine-radius 0.25 --catalog-pixel-refine-fine-step 0.0625 --catalog-pixel-refine-coarse-stride 4 --catalog-pixel-refine-final-stride 1`
- `.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits" --moving "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits" --out "C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v30_resident_pixel_refine_top32.json" --catalog-stars 64 --catalog-grid-top-cols 24 --catalog-grid-top-rows 16 --catalog-grid-top-per-cell 4 --catalog-nms-min-separation 64 --catalog-similarity-min-pair-distance 128 --catalog-similarity-min-scale 0.995 --catalog-similarity-max-scale 1.005 --catalog-similarity-max-rotation-rad 0.01 --catalog-similarity-top-k 32 --catalog-pixel-refine-radius 1.0 --catalog-pixel-refine-coarse-step 0.25 --catalog-pixel-refine-fine-radius 0.25 --catalog-pixel-refine-fine-step 0.0625 --catalog-pixel-refine-coarse-stride 4 --catalog-pixel-refine-final-stride 1`
- `git diff --check`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Targeted tests: `25 passed in 1.47s`
- Full tests: `137 passed in 7.12s`
- `git diff --check`: passed

## CUDA

- CUDA available: yes
- Native extension: built successfully
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB

## Real Two-Image Comparison

Input images:

- Reference: `C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits`
- Moving: `C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits`
- Shape: 6422 x 9600

Key result from `v29_resident_pixel_refine`:

- astroalign total: 9.576 s
- astroalign find transform: 6.747 s
- astroalign apply transform: 2.830 s
- GLASS resident catalog similarity pixel-refine device time: 1.776 s
- GLASS resident catalog similarity pixel-refine upload + device time: 1.820 s
- Speedup vs astroalign total: 5.39x device-only, 5.26x including upload
- GPU resident matrix warp using astroalign matrix: 0.0073 s device-only, 0.0447 s upload + device
- GPU resident matrix-warp speedup vs astroalign apply: 389.9x device-only, 63.4x including upload
- GPU matrix metrics on astroalign transform: resident device time 0.0019 s

Agreement result:

- GPU matrix warp using astroalign matrix matched the same transform path closely enough for kernel comparison: RMS diff vs astroalign apply on common valid pixels was 12.02 ADU.
- Autonomous resident catalog similarity pixel-refine did not pass the current strict matrix-agreement gate:
  - translation delta vs astroalign: 0.916 px, threshold 0.5 px
  - scale delta: 4.7e-6, threshold 1e-3
  - rotation delta: 1.2e-4 rad, threshold 1e-3
  - output RMS diff: 43.96 ADU, threshold 55 ADU
- The failure is therefore primarily the selected translation seed, not scale/rotation or GPU warp arithmetic.

## Known Limitations

- The autonomous catalog similarity top-K seed selection is not yet stable enough for this pair; repeated runs can select a different seed cluster.
- Pixel-metric refinement can choose the transform with lower whole-image RMS while still differing from astroalign's star-control-point transform by more than 0.5 px.
- Current resident path is a benchmark capability; the production resident registration stage still needs this multi-seed refine policy wired into the full pipeline decision logic.

## Next Step

- Make autonomous GPU registration more deterministic and WBPP-like:
  - preserve more diverse seed clusters by spatial/transform bins;
  - score final seeds with a star-weighted or masked metric instead of whole-image RMS only;
  - record both pixel-optimal and star-transform-optimal candidates;
  - require agreement between star inliers and pixel metric before accepting a frame.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source was read or used.
- The comparison used user-generated calibrated FITS artifacts and open-source `astroalign` behavior as an external reference.
- Original input directories were not modified.
