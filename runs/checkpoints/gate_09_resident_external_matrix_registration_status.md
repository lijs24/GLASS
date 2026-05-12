# Gate 09 Resident External Matrix Registration Status

Gate: 09 - warp streaming / resident matrix-registration bridge

Date: 2026-05-13

## Completed content

- Added resident CUDA registration mode `external_matrix`.
- Added CLI option `--resident-registration-results` for consuming a prior `registration_results.json` artifact.
- Resident external matrix mode:
  - preserves excluded/failed/reference frame handling;
  - preserves matched-stars, inliers, RMS, transform model, matrix, and source warnings from the external registration artifact;
  - applies accepted translation matrices with resident translation bilinear warp;
  - applies accepted similarity/affine matrices with resident CUDA matrix bilinear warp;
  - sets zero integration weight for missing, failed, or excluded rows.
- Added regression coverage in `tests/test_resident_cuda_run.py`.
- Updated `docs/registration_model.md` and `docs/cuda_backend.md`.

## Commands run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp\engine\resident_cuda.py src\gpwbpp\cli.py tests\test_resident_cuda_run.py
```

Result: passed.

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py tests\test_cuda_resident_stack.py tests\test_gpu_warp_vs_cpu.py
```

Result: 24 passed.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Result: 117 passed.

## CUDA availability

CUDA was available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB

## Test result

The resident pipeline can now ingest an external registration artifact and apply a non-translation similarity matrix with the resident CUDA matrix warp before integration. The new CLI path is covered by a synthetic two-light resident run.

## Known limitations

- `external_matrix` still depends on a prior registration artifact; GPWBPP's owned GPU similarity/affine matcher is not complete.
- The external matrix path trusts the source artifact's accepted status and does not yet recompute star-model residuals on GPU.
- Homography, Lanczos, distortion models, and full tile/window Local Normalization remain later gates.

## Next step

Run tile-mode astroalign registration on a small real subset, feed its `registration_results.json` into resident `external_matrix`, and compare the resident CUDA matrix-warp integration against the tile-mode matrix warp output before scaling back to the 200-light benchmark.

## Clean-room compliance

This increment used GPWBPP-owned code, test-generated registration artifacts, and open-source astroalign-compatible matrix semantics already present in our artifacts. No PixInsight/WBPP/PJSR official source code was read, copied, summarized, or modified.
