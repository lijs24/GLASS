# Gate 08 GPU similarity registration loop checkpoint

Date: 2026-05-13

Status: completed incremental controlled registration loop. This wires the new bounded-catalog CUDA similarity seed into an image-level helper and test: GPU star catalog extraction -> GPU similarity estimation -> GPU matrix warp.

## Completed work

- Added `gpwbpp.gpu.registration.register_similarity_from_star_catalogs_f32(...)`.
- The helper:
  - extracts compact reference/moving star catalogs with GPU star-candidate kernels;
  - estimates a moving-to-reference similarity matrix with `estimate_similarity_from_catalogs_f32`;
  - applies the matrix with `warp_matrix_bilinear_f32`;
  - returns aligned image, coverage map, and diagnostics.
- Added a synthetic image test with a known scale/rotation/translation star field.
- The test verifies:
  - the CUDA catalog similarity path is used;
  - enough detected catalog stars are retained;
  - inlier count reaches the known star count;
  - GPU warp improves image RMS;
  - the recovered matrix is close to the expected transform within catalog-detection tolerance.
- Updated CUDA backend and registration model docs to describe the controlled loop.

## Verification commands

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py::test_gpu_similarity_catalog_registration_aligns_synthetic_images
```

Result: 1 passed in 0.12 s.

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py tests\test_gpu_warp_vs_cpu.py
```

Result: 18 passed in 0.15 s.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Result: 127 passed in 7.07 s.

## CUDA availability

- CUDA backend available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Total VRAM reported by GPWBPP: 97,886 MiB.

## Known limitations

- The helper is a controlled diagnostic path, not the production pipeline registration policy yet.
- It still uses compact bounded catalogs and a brute-force two-star seed search; large real-frame catalogs need descriptor prefiltering and robust inlier selection.
- Star positions are currently local-maximum pixel coordinates, not full subpixel centroid refinements.
- The helper is non-resident at the Python wrapper level; it still downloads compact diagnostics and arrays through wrapper calls.

## Next step

Add GPU subpixel centroid refinement or descriptor prefiltering before trying this path against real calibrated M38 frames, then wire a gated `registration-method` option once it has robust pass/fail policy.

## Clean-room compliance

Compliant. The implementation uses GPWBPP-owned CUDA code and generic geometric registration formulas. No official WBPP/PJSR source was read or copied.
