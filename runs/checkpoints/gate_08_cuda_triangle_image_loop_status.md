# Gate 08 Checkpoint: CUDA triangle descriptor image loop

## Gate

Gate 08: Registration.

## Completed content

- Added `glass.gpu.registration.register_triangle_descriptor_similarity_f32(...)`.
- The helper wires a controlled image-pair loop:
  - GPU star catalog extraction;
  - CUDA triangle descriptor generation;
  - CUDA triangle-descriptor similarity scoring;
  - CUDA matrix warp.
- Added a synthetic image-pair test showing the loop improves alignment for a rotated/translated star field.
- Updated CUDA and registration documentation.

## Commands run

- `.\\.venv\\Scripts\\python.exe -m ruff check src\\glass\\gpu\\registration.py tests\\test_gpu_registration_search.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_gpu_registration_search.py::test_gpu_triangle_descriptor_image_registration_improves_alignment`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_gpu_registration_search.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`

## Test results

- Ruff on touched Python files: `All checks passed!`.
- New targeted image-loop test: `1 passed in 0.14s`.
- GPU registration test module: `28 passed in 0.17s`.
- Full pytest suite: `156 passed in 7.55s`.

## CUDA availability

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- Total VRAM: 97886 MiB
- Native backend: available

## Known limitations

- The helper is validated on synthetic image data only in this checkpoint.
- Real calibrated M38 pair agreement versus `astroalign` has not been rerun with this helper yet.
- Resident pipeline integration and 200-light benchmark wiring remain future work.
- The descriptor path is still triangle-based and does not yet implement PixInsight-style polygonal descriptor families.

## Next step

Extend `benchmarks/compare_astroalign_gpu_alignment.py` to include this triangle-descriptor image loop on the calibrated M38 pair, recording timing, matrix agreement, and common-valid-pixel differences versus `astroalign`.

## Clean-room compliance

Compliant. No PixInsight/WBPP/PJSR source code was read or used. The helper composes GLASS-owned CUDA primitives and is validated against synthetic known-truth image data.
