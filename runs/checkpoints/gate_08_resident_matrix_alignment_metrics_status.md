# Gate 08 Increment: Resident Matrix Alignment Metrics

Date: 2026-05-13

## Completed contents

- Added `ResidentCalibratedStack.matrix_alignment_metrics_to_reference(...)` to the native CUDA backend.
- Added the public Python wrapper in `src/gpwbpp_cuda.py`.
- Added a resident-stack test that compares resident GPU matrix metrics against the standalone CUDA matrix metric.
- Extended `benchmarks/compare_astroalign_gpu_alignment.py` so the astroalign vs GPWBPP comparison records resident matrix-metric timing.
- Updated CUDA and registration documentation with the new resident metric path and refreshed M38 pair timing.

## Commands run

- `cmd /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .venv\Scripts\cmake.exe --build build\native-cuda --config Release'`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py tests\test_gpu_registration_search.py`
- `.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits" --moving "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits" --out "C:\gpwbpp_runs\final_m38_h_200\astroalign_vs_gpwbpp_gpu_pair_S000061_S000062_full_benchmark_v16_resident_matrix_metrics.json"`
- `git diff --check`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test results

- Targeted CUDA registration/resident tests: `31 passed in 0.15s`
- Full suite: `132 passed in 6.84s`
- `git diff --check`: passed, with only Windows LF-to-CRLF warnings.

## Real pair benchmark

Artifact:

- `C:\gpwbpp_runs\final_m38_h_200\astroalign_vs_gpwbpp_gpu_pair_S000061_S000062_full_benchmark_v16_resident_matrix_metrics.json`

Input pair:

- Reference: `calibrated_S000061.fits`
- Moving: `calibrated_S000062.fits`
- Shape: `6422 x 9600`

Key timing:

- astroalign total: `9.6299 s`
- astroalign find transform: `6.7897 s`
- astroalign apply transform: `2.8402 s`
- GPWBPP standalone CUDA matrix warp using astroalign matrix: `0.1456 s`
- GPWBPP resident CUDA matrix warp device time using astroalign matrix: `0.0069 s`
- GPWBPP standalone CUDA matrix metrics: `0.0382 s`
- GPWBPP resident CUDA matrix metrics device time: `0.0015 s`

Key consistency diagnostics:

- Common valid pixels for CUDA matrix warp vs astroalign apply: `61,632,460`
- Median absolute difference vs astroalign apply: `3.98 ADU`
- RMS difference vs astroalign apply: `12.02 ADU`
- Resident matrix metric RMS to reference: `76.35 ADU`
- Resident matrix metric NCC to reference: `0.9767`

## CUDA availability

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97,886 MiB
- Multiprocessors: 188

## Known limitations

- The accepted production-quality transform in this comparison is still astroalign's open-source transform matrix. GPWBPP CUDA owns the warp and metric path here.
- The pure GPWBPP GPU catalog-similarity candidate remains marked `accepted=false` on this pair because its matrix and output image do not yet agree closely enough with the astroalign reference.
- Resident matrix metrics validate candidate matrices without host materialization, but descriptor-level GPU star matching and robust similarity/affine acceptance still need more work.

## Next step

- Improve the pure GPU star matcher so the GPWBPP-owned catalog similarity matrix passes the same agreement checks currently satisfied by the astroalign-provided matrix.

## Clean-room compliance

- This increment used project code, CUDA kernels, tests, and the open-source astroalign package as an external reference.
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or used as implementation material.
- Original image data were read only; generated benchmark artifacts were written under `C:\gpwbpp_runs`.
