# Gate 08 CUDA similarity fit checkpoint

Date: 2026-05-13

Status: completed incremental Gate 08/09 registration capability. This is not a full GPU star/asterism matcher; it adds the CUDA transform-estimation primitive needed after trustworthy matched star pairs exist.

## Completed work

- Added native CUDA matched-pair similarity fitting:
  - `estimate_similarity_from_pairs_f32(reference_x, reference_y, moving_x, moving_y)`
  - finite-pair filtering
  - moving-to-reference 3x3 similarity matrix
  - scale
  - rotation in radians
  - valid/input pair counts
  - RMS residual in pixels
- Added Python compatibility wrapper with CPU fallback for CPU-only installs.
- Added CUDA test coverage for scale, rotation, translation, RMS, and NaN-pair filtering.
- Updated CUDA backend and registration model docs to identify this as a building block for pure-GPU descriptor registration.

## Verification commands

```powershell
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" --build build\native-cuda --config Release --target _glass_cuda_native'
```

Result: native CUDA extension rebuilt successfully. An initial compile attempt exposed a dynamic shared-memory symbol conflict in the new kernel; the kernel shared-memory name was fixed and the rebuild passed.

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py::test_gpu_estimate_similarity_from_matched_pairs tests\test_gpu_registration_search.py tests\test_gpu_warp_vs_cpu.py
```

Result: 16 passed in 0.90 s.

```powershell
@'
import numpy as np, glass_cuda
moving = np.array([(0,0),(1,0),(0,1),(2,3)], dtype=np.float32)
angle = np.deg2rad(5.0)
scale = 1.02
linear = scale * np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]], dtype=np.float32)
translation = np.array([3.0, -2.0], dtype=np.float32)
reference = moving @ linear.T + translation
result = glass_cuda.estimate_similarity_from_pairs_f32(reference[:,0], reference[:,1], moving[:,0], moving[:,1])
print(result)
'@ | .\.venv\Scripts\python.exe -
```

Observed: `model=matched_pair_similarity_cuda`, `status=ok`, scale about `1.02`, rotation about `0.08726647`, RMS about `8.3e-08`.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Result: 125 passed in 7.04 s.

## CUDA availability

- CUDA backend available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Total VRAM reported by GLASS: 97,886 MiB.

## Known limitations

- This primitive assumes matched star pairs are already known. It does not perform descriptor matching, RANSAC, or robust outlier rejection.
- The fit is a 2D similarity model only: scale, rotation, and translation. Affine/homography estimation remain future registration gates.
- The native wrapper still downloads compact diagnostics and the final matrix to Python, which is acceptable for orchestration but not a full resident registration graph yet.
- Pipeline registration does not yet call this primitive automatically; current resident star-catalog registration remains translation-only.

## Next step

Use an open-source registration algorithm as the behavioral reference for matching, then port the descriptor scoring and robust inlier selection to CUDA so this similarity-fit primitive can replace the current external astroalign matrix bridge.

## Clean-room compliance

Compliant. This implementation uses generic 2D similarity least-squares formulas and GLASS CUDA code. No official WBPP/PJSR source was read or copied.
