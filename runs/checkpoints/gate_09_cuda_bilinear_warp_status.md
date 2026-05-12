# Gate 09 Increment: CUDA Bilinear Translation Warp

- Gate: 09
- Date: 2026-05-13
- Status: completed
- Commit: pending

## Completed

- Added native CUDA `warp_translation_bilinear_f32` for floating-point
  translation warp with bilinear interpolation.
- Added Python wrapper and CPU fallback in `gpwbpp_cuda.py`.
- Re-exported the CUDA warp primitive through `gpwbpp.gpu.warp`.
- Added CPU/GPU parity test for subpixel bilinear translation.
- Added a catalog-refinement-to-warp test that estimates a refined translation
  on the GPU and applies it with CUDA bilinear warp.
- Updated CUDA and registration docs to mark the current validated scope.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m cmake --build build\native-cuda --config Debug
.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_warp_vs_cpu.py tests\test_gpu_registration_search.py
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp_cuda.py src\gpwbpp\gpu\warp.py tests\test_gpu_warp_vs_cpu.py
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Result

- Native CUDA build: passed, no rebuild needed.
- Targeted CUDA warp/registration tests: 7 passed.
- Ruff: all checks passed.
- Full pytest: 94 passed.

## CUDA Availability

- CUDA native extension: available.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend loaded: true.

## Known Limitations

- Warp is translation-only.
- Interpolation is bilinear only; Lanczos and policy-selectable resampling are
  future work.
- The wrapper currently copies host arrays to/from the device for the standalone
  test path; the fully resident high-VRAM pipeline still needs a resident warp
  method to avoid host transfer between stages.
- Similarity, affine, homography, and tile-streaming/resident transform
  application remain incomplete.

## Next Step

- Convert the validated bilinear warp primitive into a resident GPU path so a
  calibrated frame can remain in VRAM through registration, warp, local
  normalization, and integration.

## Clean-room Compliance

- No official PixInsight WBPP/PJSR source was read, copied, summarized, or
  modified.
- Astroalign remains an open-source external comparison reference only; it is
  not runtime logic for GPWBPP.
- Input data directories were not modified.
