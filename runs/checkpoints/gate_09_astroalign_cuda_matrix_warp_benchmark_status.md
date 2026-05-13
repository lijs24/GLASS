# Gate 09 Astroalign CUDA Matrix Warp Benchmark Status

Gate: 09 - warp streaming / external transform CUDA application benchmark

Date: 2026-05-13

## Completed content

- Extended `benchmarks/compare_astroalign_gpu_alignment.py` to split astroalign timing into:
  - transform search (`find_elapsed_s`)
  - pixel resampling (`apply_elapsed_s`)
- Added benchmark paths that apply astroalign's own similarity matrix through GLASS:
  - standalone `glass_cuda.warp_matrix_bilinear_f32`
  - resident `ResidentCalibratedStack.apply_matrix_bilinear_frame`
- Added result fields for matrix-warp RMS, valid-pixel coverage, resident upload/device/download timing, and speedups against astroalign `apply_transform`.
- Updated `docs/registration_model.md` to describe the benchmark's separation of matching cost from pixel-resampling cost.

## Commands run

```powershell
.\.venv\Scripts\python.exe -m ruff check benchmarks\compare_astroalign_gpu_alignment.py
```

Result: passed.

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_warp_vs_cpu.py tests\test_cuda_resident_stack.py
```

Result: 18 passed.

```powershell
.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --width 512 --height 512 --synthetic-dx 7 --synthetic-dy -5 --max-shift 16 --catalog-grid-cols 8 --catalog-grid-rows 8 --catalog-prior-radius 4 --out runs\alignment_compare\astroalign_vs_gpu_matrix_warp_synth.json
```

Result: passed. The synthetic diagnostic produced `runs/alignment_compare/astroalign_vs_gpu_matrix_warp_synth.json`.

Key synthetic result:

- astroalign total: 0.2485 s
- astroalign apply_transform: 0.0406 s
- resident CUDA matrix warp device time: 0.000318 s
- resident CUDA matrix warp device speedup vs astroalign apply_transform: 127.4x
- resident upload+device speedup vs astroalign apply_transform: 64.1x

```powershell
.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference C:\glass_runs\final_m38_h_200\glass_cuda_run\calib_cache\calibrated\calibrated_F000061.fits --moving C:\glass_runs\final_m38_h_200\glass_cuda_run\calib_cache\calibrated\calibrated_F000080.fits --center-crop 1024 --max-shift 128 --subpixel-radius-steps 4 --subpixel-step 0.25 --catalog-max-shift 20 --catalog-grid-cols 8 --catalog-grid-rows 8 --catalog-threshold-sigma 6 --catalog-tolerance-px 3 --catalog-prior-radius 4 --out runs\alignment_compare\astroalign_vs_gpu_matrix_warp_m38_crop_061_080.json
```

Result: passed. The real-data diagnostic produced `runs/alignment_compare/astroalign_vs_gpu_matrix_warp_m38_crop_061_080.json`.

Key M38 calibrated-crop result:

- image shape: 1024 x 1024
- astroalign total: 0.3795 s
- astroalign transform search: 0.3031 s
- astroalign apply_transform: 0.0764 s
- standalone CUDA matrix warp: 0.0624 s, RMS 67.01
- resident CUDA matrix warp device time: 0.000784 s, RMS 67.01
- resident CUDA matrix warp device speedup vs astroalign apply_transform: 97.46x
- resident upload+device speedup vs astroalign apply_transform: 42.54x

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Result: 116 passed.

## CUDA availability

CUDA was available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB

## Test result

The benchmark now cleanly separates the CPU astroalign matching step from the pixel warp step and verifies that GLASS can apply astroalign's similarity matrix with CUDA. The resident path shows the intended high-VRAM behavior: pixels stay on device for the warp, and only compact timing/diagnostic output is reported.

## Known limitations

- Astroalign still supplies the transform matrix in this benchmark; this is not yet a fully GLASS-owned GPU similarity/affine matcher.
- The standalone CUDA matrix warp includes host/device transfer overhead and can be slower on very small images.
- The main resident 200-light pipeline still needs automatic wiring from similarity/affine registration results into the resident matrix warp.

## Next step

Connect non-translation registration matrices to the resident run path and validate frame acceptance/quality diagnostics before scaling the matrix-warp path to the full 200-light benchmark.

## Clean-room compliance

This increment used open-source astroalign as an external reference and user-generated GLASS calibrated FITS artifacts. No PixInsight/WBPP/PJSR official source code was read, copied, summarized, or modified.
