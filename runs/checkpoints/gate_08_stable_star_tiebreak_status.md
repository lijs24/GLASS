# Gate 8 Incremental Checkpoint: Stable CUDA Star Candidate Tie Breaks

## Gate

Gate 8: Registration

This is an incremental checkpoint inside Gate 8. It does not claim Gate 8 is complete.

## Completed Contents

- Added deterministic tie-breaking for equal-flux CUDA star candidates.
- Applied the same ordering to global top-N, grid winner, grid top-K, and final catalog sorting kernels.
- Added regression tests for saturated 2x2 plateaus so equal-flux stars are returned in stable row-major order.
- Re-ran the real full-resolution astroalign vs GLASS CUDA pair benchmark on:
  - `C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits`
  - `C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits`

## Commands Run

```powershell
cmd /c "call ""C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat"" -arch=x64 -host_arch=x64 && .venv\Scripts\cmake.exe --build build\native-cuda --config Release"

.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits" --moving "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits" --out "C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v33_current.json" --catalog-stars 64 --catalog-grid-top-cols 24 --catalog-grid-top-rows 16 --catalog-grid-top-per-cell 4 --catalog-nms-min-separation 64 --catalog-similarity-min-pair-distance 128 --catalog-similarity-min-scale 0.995 --catalog-similarity-max-scale 1.005 --catalog-similarity-max-rotation-rad 0.01 --catalog-similarity-top-k 8 --catalog-pixel-refine-radius 1.0 --catalog-pixel-refine-coarse-step 0.25 --catalog-pixel-refine-fine-radius 0.25 --catalog-pixel-refine-fine-step 0.0625 --catalog-pixel-refine-coarse-stride 4 --catalog-pixel-refine-final-stride 1

.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py
git diff --check
.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- `tests\test_gpu_registration_search.py`: `24 passed`
- Full suite: `139 passed in 7.09s`
- `git diff --check`: passed

## CUDA Status

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM reported by GLASS benchmark: 97886 MiB

## Real Pair Benchmark Summary

Artifact:

- `C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v33_current.json`

Image shape: `6422 x 9600`

Key timings:

- astroalign total: `9.733074 s`
- astroalign transform finding: `6.835126 s`
- astroalign apply transform: `2.897948 s`
- GLASS resident CUDA matrix warp using astroalign transform, device only: `0.007070 s`
- GLASS resident CUDA matrix warp using astroalign transform, upload plus device: `0.044971 s`
- GLASS resident CUDA autonomous catalog/pixel-refined alignment, upload plus device: `1.818251 s`

Observed speedups:

- Same-transform resident CUDA warp vs astroalign apply: `409.89x` device-only, `64.44x` upload plus device
- Autonomous resident CUDA catalog/pixel-refined alignment vs astroalign total: `5.47x` device-only, `5.35x` upload plus device

Agreement:

- Same-transform GPU warp output RMS difference vs astroalign apply: `12.016713 ADU`
- Autonomous resident CUDA agreement with astroalign: failed strict matrix threshold
- Autonomous translation delta: `0.916051 px`, threshold is `0.5 px`
- Autonomous output RMS difference: `43.959960 ADU`, threshold is `55.0 ADU`

## Known Limitations

- Gate 8 is still open. The autonomous CUDA alignment path is fast but does not yet pass the strict matrix agreement threshold against astroalign on this pair.
- Pixel-metric refinement can choose a candidate with slightly better whole-image RMS/NCC but worse star-transform agreement.
- The next fix should rank candidate transforms with star geometry consistency, not only image-wide pixel metrics.

## Next Step

Add a guarded transform selection policy for autonomous CUDA alignment:

- keep catalog similarity top candidates,
- evaluate pixel metrics,
- retain or re-rank by star inlier count and transform RMS,
- reject pixel refinement that moves the transform outside the star-supported solution basin.

## Clean-room Compliance

Compliant. This checkpoint used only GLASS source, generated benchmark artifacts, astroalign behavior as an external open-source reference, and user-provided FITS data. No PixInsight/WBPP/PJSR source was read, copied, summarized, or modified.
