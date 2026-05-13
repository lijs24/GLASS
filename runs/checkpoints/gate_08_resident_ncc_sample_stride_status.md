# Gate 08 Increment: Resident NCC Sample Stride

Date: 2026-05-13

## Gate

Gate 08 / registration increment.

## Completed Content

- Added an optional `sample_stride` parameter to CUDA integer NCC translation search and subpixel NCC refinement.
- Exposed the option through:
  - `glass_cuda.estimate_translation_search_f32(..., sample_stride=1)`
  - `glass_cuda.estimate_translation_subpixel_ncc_f32(..., sample_stride=1)`
  - `ResidentCalibratedStack.estimate_translation_to_reference(..., sample_stride=1)`
  - `ResidentCalibratedStack.estimate_translation_subpixel_to_reference(..., sample_stride=1)`
  - CLI flag `--resident-ncc-sample-stride`
- Default remains `1`, preserving full-pixel NCC behavior.
- Resident CUDA run artifacts now record `ncc_sample_stride`.
- Documentation updated in `docs/cuda_backend.md` and `docs/registration_model.md`.
- Added CUDA tests for standalone and resident sample-stride paths.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass_cuda.py src\glass\engine\resident_cuda.py src\glass\cli.py tests\test_gpu_registration_search.py tests\test_resident_cuda_run.py
```

Result: `All checks passed!`

```powershell
$pybind = (& .\.venv\Scripts\python.exe -m pybind11 --cmakedir).Trim()
$ninja = (Resolve-Path .\.venv\Scripts\ninja.exe).Path
cmd /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe -S . -B build\native-cuda -G Ninja -DGLASS_BUILD_PYTHON_CUDA=ON -DGLASS_BUILD_CUDA=OFF -Dpybind11_DIR="<pybind11 cmake dir>" -DCMAKE_MAKE_PROGRAM="<ninja>" -DCMAKE_CUDA_COMPILER="C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2\bin\nvcc.exe" -DCMAKE_CUDA_ARCHITECTURES=120 && .\.venv\Scripts\cmake.exe --build build\native-cuda --config Release'
```

Result: configure succeeded; build result `ninja: no work to do.`

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Result: `110 passed in 5.99s`

## Real-Data Diagnostics

Resident M38 subset12 baseline:

- Run: `C:\glass_runs\final_m38_h_200\glass_resident_ncc_subset12`
- Registration mode: resident CUDA `translation_ncc_subpixel`
- Elapsed: `18.7239103000029 s`

Resident M38 subset12 with `--resident-ncc-sample-stride 4`:

- Run: `C:\glass_runs\final_m38_h_200\glass_resident_ncc_stride4_subset12`
- Status counts: `1 reference`, `11 ok`
- Elapsed: `15.676582099986263 s`
- Compared frames: `12`
- Mean translation delta vs stride-1 baseline: `0.08333333333333333 px`
- Max translation delta vs stride-1 baseline: `1.0 px`

Astroalign vs GLASS CUDA two-frame diagnostic:

- Artifact: `runs/diagnostics/astroalign_vs_gpu_m38_light0001_0003/result.json`
- Pair: M38 `LIGHT_H_0001.fits` reference and `LIGHT_H_0003.fits` moving, full frame `6422 x 9600`
- Common input: FITS `BSCALE/BZERO` applied, calibrated with existing GLASS master dark/flat, flat floor `0.05`
- Astroalign full-frame affine: `6.658273199980613 s`
- GLASS CUDA standalone NCC+warp stride 1: `0.6261521999840625 s`, refined shift `(4.5, 0.5)`
- GLASS CUDA standalone NCC+warp stride 4: `0.23493669996969402 s`, refined shift `(4.5, 0.5)`
- GLASS resident upload+estimate+warp+download stride 1: `0.506568199954927 s`, refined shift `(4.5, 0.5)`
- GLASS resident upload+estimate+warp+download stride 4: `0.1733166000340134 s`, refined shift `(4.5, 0.5)`

## CUDA Availability

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- Total VRAM: 97886 MiB
- Native backend: true

## Known Limitations

- `sample_stride` is a speed/accuracy tradeoff. The default remains full-resolution stride `1`.
- This increment accelerates translation NCC scoring only. It is not a substitute for full star-based affine/similarity registration.
- The subset12 diagnostic is encouraging, but a larger 50/200-light sweep is still needed before selecting a non-default stride for final real-data comparisons.
- The astroalign comparison uses a two-frame full-resolution diagnostic and is not a final registration benchmark for all WBPP stages.

## Next Step

Run a larger resident NCC stride sweep on the 200-light M38 set, then decide whether stride `4` is safe enough for the formal speed comparison or whether the star/affine GPU path should become the primary registration path.

## Clean-Room Compliance

Compliant. This work used project-owned CUDA code, project tests, generated GLASS artifacts, user-provided raw frames, and public/open Python package behavior. It did not read, copy, summarize, or modify PixInsight/WBPP/PJSR source code.
