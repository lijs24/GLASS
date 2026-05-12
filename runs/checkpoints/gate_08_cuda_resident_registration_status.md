# Gate 08 Increment: Resident CUDA Registration Timing Path

- Gate: 08
- Date: 2026-05-13
- Status: completed
- Commit: pending

## Completed

- Added resident CUDA frame-to-frame registration methods on
  `ResidentCalibratedStack`:
  - `estimate_translation_to_reference(...)`
  - `estimate_translation_subpixel_to_reference(...)`
  - `apply_translation_bilinear_frame(...)`
- The resident path estimates integer NCC, refines with subpixel NCC, and warps
  a resident calibrated frame in place without re-uploading the two images
  through standalone wrapper calls.
- Extended `benchmarks/compare_astroalign_gpu_alignment.py` with
  `gpwbpp_cuda_resident_ncc_subpixel`.
- Added resident CUDA regression coverage for subpixel estimate plus bilinear
  warp against a synthetic shifted star field.
- Updated CUDA backend and registration model docs.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check benchmarks\compare_astroalign_gpu_alignment.py src\gpwbpp_cuda.py tests\test_cuda_resident_stack.py
$pybind = (& .\.venv\Scripts\python.exe -m pybind11 --cmakedir).Trim(); $ninja = (Resolve-Path .\.venv\Scripts\ninja.exe).Path; $cmd = 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe -S . -B build\native-cuda -G Ninja -DGPWBPP_BUILD_PYTHON_CUDA=ON -DGPWBPP_BUILD_CUDA=OFF -Dpybind11_DIR="' + $pybind + '" -DCMAKE_MAKE_PROGRAM="' + $ninja + '" -DCMAKE_CUDA_COMPILER="C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2\bin\nvcc.exe" -DCMAKE_CUDA_ARCHITECTURES=120 && .\.venv\Scripts\cmake.exe --build build\native-cuda --config Release'; cmd /c $cmd
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py tests\test_gpu_registration_search.py
.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --width 512 --height 512 --synthetic-dx 7 --synthetic-dy -5 --max-shift 16 --catalog-grid-cols 8 --catalog-grid-rows 8 --catalog-prior-radius 4 --out runs\alignment_compare\astroalign_vs_gpu_alignment_resident_synth.json
.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference C:\gpwbpp_runs\final_m38_h_200\gpwbpp_cuda_run\calib_cache\calibrated\calibrated_F000061.fits --moving C:\gpwbpp_runs\final_m38_h_200\gpwbpp_cuda_run\calib_cache\calibrated\calibrated_F000080.fits --center-crop 1024 --max-shift 128 --subpixel-radius-steps 4 --subpixel-step 0.25 --catalog-max-shift 20 --catalog-grid-cols 8 --catalog-grid-rows 8 --catalog-threshold-sigma 6 --catalog-tolerance-px 3 --catalog-prior-radius 4 --out runs\alignment_compare\astroalign_vs_gpu_alignment_resident_m38_crop_061_080.json
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Result

- Ruff: all checks passed.
- Native CUDA build: passed.
- Targeted resident/registration tests: 16 passed.
- Full pytest: 99 passed.
- Synthetic 512x512 resident comparison:
  - Astroalign: 0.2760 s, RMS 0.0085.
  - Resident CUDA NCC + subpixel, device-only: 0.00135 s, RMS 0.0.
  - Resident CUDA upload + device: 0.00167 s.
  - Device-only speedup over astroalign: 204.55x.
- M38 calibrated 1024x1024 crop comparison:
  - Astroalign: 0.3221 s, RMS 72.35, 24 matched control points.
  - Standalone CUDA NCC + subpixel: 0.1308 s, RMS 63.80.
  - Resident CUDA NCC + subpixel, device-only: 0.0703 s, RMS 63.80.
  - Resident CUDA upload + device: 0.0713 s.
  - Device-only speedup over astroalign: 4.58x.
  - Upload + device speedup over astroalign: 4.52x.

## CUDA Availability

- CUDA native extension: available.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Artifacts

- `runs/alignment_compare/astroalign_vs_gpu_alignment_resident_synth.json`
- `runs/alignment_compare/astroalign_vs_gpu_alignment_resident_m38_crop_061_080.json`

## Known Limitations

- Resident registration is still translation-only.
- The benchmark uses preselected calibrated crop frames; it is not the final
  200+ light full WBPP/GPWBPP comparison.
- The resident path demonstrates the high-VRAM timing model but still needs to
  be wired into the full pipeline's calibration to registration to integration
  resident execution path.
- Similarity, affine, homography, descriptor-level matching, Lanczos policy,
  and full-frame resident multi-light registration remain future gates.

## Next Step

- Wire resident registration into the real resident run stage so calibrated
  frames can stay in VRAM through registration, bilinear warp, and integration
  for the larger M38 timing test.

## Clean-room Compliance

- No official PixInsight WBPP/PJSR source was read, copied, summarized, or
  modified.
- Astroalign is used only as an open-source behavioral comparison reference.
- Original input data directories were not modified.
