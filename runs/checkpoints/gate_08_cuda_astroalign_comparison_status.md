# Gate 08 CUDA Alignment Comparison Status

- Gate: 08 registration
- Date: 2026-05-13
- Scope:
  - Added a narrow pure-CUDA integer translation estimator:
    `estimate_translation_search_f32(reference, moving, max_shift_x, max_shift_y)`.
  - The estimator scores all integer shifts with normalized cross-correlation
    and selects the best shift on device.
  - Added a reproducible comparison benchmark against the open-source
    `astroalign` package:
    `benchmarks/compare_astroalign_gpu_alignment.py`.
  - Added an optional `align` dependency extra for `astroalign`.

## Commands

```powershell
.\.venv\Scripts\python.exe -m pip install --progress-bar off --retries 1 --timeout 20 -i https://pypi.tuna.tsinghua.edu.cn/simple astroalign
cmd /c ""C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 && "C:\Users\ljs\WORK\astro\gpuwbpp\.venv\Scripts\python.exe" -m cmake --build build\native-cuda --config Debug"
.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py tests\test_gpu_warp_vs_cpu.py
.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --out runs\alignment_compare\astroalign_vs_gpu_alignment.json --width 512 --height 512 --synthetic-dx 7 --synthetic-dy -5 --max-shift 16
.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference C:\gpwbpp_runs\final_m38_h_200\gpwbpp_cuda_run\calib_cache\calibrated\calibrated_F000061.fits --moving C:\gpwbpp_runs\final_m38_h_200\gpwbpp_cuda_run\calib_cache\calibrated\calibrated_F000080.fits --center-crop 1024 --max-shift 128 --out runs\alignment_compare\astroalign_vs_gpu_alignment_m38_crop_061_080.json
```

## Test Results

- Targeted pytest: 2 passed.
- Synthetic astroalign comparison:
  - Image shape: 512 x 512.
  - Truth moving shift: dx=7, dy=-5.
  - Astroalign: dx=-6.9993, dy=4.9992, elapsed 2.8927 s, RMS 0.0085.
  - GPWBPP CUDA: dx=-7, dy=5, elapsed 0.0602 s, RMS 0.0.
  - Speedup in this controlled test: 48.0x.
- Real M38 calibrated crop comparison:
  - Source frames: calibrated_F000061.fits vs calibrated_F000080.fits.
  - Crop: center 1024 x 1024.
  - Astroalign: dx=9.5867, dy=0.8982, elapsed 0.3207 s, RMS 72.35.
  - GPWBPP CUDA: dx=9, dy=1, elapsed 0.1268 s, RMS 81.49.
  - Speedup in this crop test: 2.53x.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Artifacts

- `runs/alignment_compare/astroalign_vs_gpu_alignment.json`
- `runs/alignment_compare/astroalign_vs_gpu_alignment_m38_crop_061_080.json`

## Known Limitations

- The CUDA estimator currently supports integer translation only.
- It does not yet estimate subpixel shifts, rotation, scale, affine terms, or
  higher-order warp interpolation.
- On adjacent real M38 frames with about one pixel of subpixel drift, the
  integer NCC path can choose dx=0 where astroalign estimates dx about 1.05.
  The wider 061-to-080 crop confirms the GPU path finds the nearest integer
  translation to astroalign.
- Astroalign is used only as an open-source comparison reference and is not
  part of GPWBPP runtime alignment.

## Next Step

Move from integer NCC translation to a fully GPU star-catalog alignment path:
GPU top-N catalog ranking, device-side triangle/asterism matching, subpixel
centroid refinement, similarity/affine scoring, and GPU warp application.

## Clean-Room

No official PixInsight WBPP/PJSR source was read or used. The comparison uses
synthetic data, GPWBPP-generated calibrated FITS outputs, and the open-source
astroalign package as an external behavioral reference.
