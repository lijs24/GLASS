# Gate 08 CUDA catalog similarity seed checkpoint

Date: 2026-05-13

Status: completed incremental pure-GPU registration seed. This is not the final GLASS star descriptor/RANSAC matcher; it is the first CUDA primitive that estimates a similarity transform directly from two bounded star catalogs without astroalign supplying matched pairs.

## Completed work

- Added native CUDA bounded-catalog similarity seed matching:
  - `estimate_similarity_from_catalogs_f32(reference_x, reference_y, moving_x, moving_y, tolerance_px=2.0, min_pair_distance=2.0)`
  - ordered two-star pair candidate generation on the GPU
  - per-candidate similarity fit on the GPU
  - inlier scoring against the reference catalog on the GPU
  - best-candidate matrix, scale, rotation, inlier count, RMS, and candidate count diagnostics
- Added Python wrapper with CPU fallback for CPU-only installs.
- Added CUDA tests using a synthetic similarity transform plus catalog outliers.
- Updated CUDA backend and registration docs to separate:
  - matched-pair similarity fit
  - bounded-catalog similarity seed matching
  - future robust descriptor/RANSAC work

## Verification commands

```powershell
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" --build build\native-cuda --config Release --target _glass_cuda_native'
```

Result: native CUDA extension rebuilt successfully. An initial compile attempt used a CUDA runtime infinity constant not exposed in this build; it was replaced with the existing project float-max literal and the rebuild passed.

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py::test_gpu_estimate_similarity_from_catalogs_scores_pair_candidates tests\test_gpu_registration_search.py
```

Result: 12 passed in 0.85 s.

```powershell
@'
import numpy as np, glass_cuda
moving = np.array([(10,11),(25,14),(18,34),(41,37),(53,21),(63,45)], dtype=np.float32)
angle = np.deg2rad(-4.0); scale = 0.985
linear = scale*np.array([[np.cos(angle), -np.sin(angle)],[np.sin(angle), np.cos(angle)]], dtype=np.float32)
translation = np.array([-1.75, 4.5], dtype=np.float32)
reference = moving @ linear.T + translation
moving_catalog = np.vstack([moving, np.array([[90,90]], dtype=np.float32)])
reference_catalog = np.vstack([reference, np.array([[4,4]], dtype=np.float32)])
result = glass_cuda.estimate_similarity_from_catalogs_f32(reference_catalog[:,0], reference_catalog[:,1], moving_catalog[:,0], moving_catalog[:,1], 0.15, 3.0)
print(result)
'@ | .\.venv\Scripts\python.exe -
```

Observed: `model=catalog_pair_similarity_cuda`, `status=ok`, `inliers=6`, `candidate_count=1764`, scale about `0.985`, rotation about `-0.069813`, RMS about `1.1e-06`.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Result: 126 passed in 7.08 s.

## CUDA availability

- CUDA backend available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Total VRAM reported by GLASS: 97,886 MiB.

## Known limitations

- This primitive is intentionally brute-force and intended for compact bounded catalogs, not full all-star catalogs.
- Scoring currently uses nearest-reference inlier counting, not mutual assignment as the final acceptance criterion.
- It does not yet include descriptor prefiltering, RANSAC iterations, or affine/homography models.
- The resident pipeline does not yet call this primitive automatically; current resident registration remains translation-only unless an external matrix artifact is provided.

## Next step

Wire this bounded-catalog similarity seed into a controlled registration path on synthetic data, then compare it with the astroalign bridge before attempting full real-frame catalogs.

## Clean-room compliance

Compliant. This uses generic two-point 2D similarity geometry and GLASS CUDA code. No official WBPP/PJSR source was read or copied.
