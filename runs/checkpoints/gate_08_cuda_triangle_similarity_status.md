# Gate 08 Checkpoint: CUDA triangle descriptor similarity scoring

## Gate

Gate 08: Registration.

## Completed content

- Added `glass_cuda.estimate_similarity_from_triangle_descriptors_f32(...)`.
- Added a CUDA candidate scorer that:
  - filters triangle descriptor pairs by side-ratio radius;
  - tries both ordered-triangle orientations;
  - fits moving-to-reference similarity matrices from triangle vertices;
  - scores compact catalogs with mutual nearest-neighbor inliers.
- Added Python compatibility wrapper and `glass.gpu.registration` export.
- Added a CUDA test recovering a known synthetic similarity transform from triangle descriptors.
- Updated CUDA and registration documentation.

## Commands run

- `.\\.venv\\Scripts\\python.exe -m ruff check src\\glass_cuda.py src\\glass\\gpu\\registration.py tests\\test_gpu_registration_search.py`
- `cmd.exe /d /s /c 'call "C:\\Program Files (x86)\\Microsoft Visual Studio\\2022\\BuildTools\\Common7\\Tools\\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .venv\\Scripts\\cmake.exe --build build\\native-cuda --config Release'`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_gpu_registration_search.py::test_gpu_triangle_descriptor_similarity_recovers_catalog_transform`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_gpu_registration_search.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\python.exe -c "import glass_cuda as c; print('cuda_available', c.cuda_available()); print(c.list_devices())"`
- `git diff --check`

## Test results

- Ruff on touched Python files: `All checks passed!`.
- Native CUDA build: succeeded after initializing the VS BuildTools developer environment for the current command.
- New targeted triangle similarity test: `1 passed in 0.94s`.
- GPU registration test module: `27 passed in 0.16s`.
- Full pytest suite: `155 passed in 7.52s`.
- `git diff --check`: no whitespace errors; only Git CRLF conversion warnings.

## CUDA availability

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- Total VRAM: 97886 MiB
- Native backend: available

## Known limitations

- The primitive is validated on a controlled synthetic catalog. Real M38 pair acceptance and 200-light resident wiring are not complete.
- Descriptor generation still downloads compact descriptor arrays for host-side deduplication and ordering.
- The scorer returns the best seed matrix but does not yet run a full multi-hypothesis RANSAC/refit loop from descriptor matches.
- The native build emits CUDA header C4819 warnings under the current Windows code page, but the build succeeds.

## Next step

Wire the triangle descriptor similarity scorer into a controlled image-pair benchmark: GPU star extraction -> CUDA triangle descriptors -> CUDA triangle similarity seed -> CUDA matrix warp -> numeric comparison against `astroalign` and existing catalog-similarity paths.

## Clean-room compliance

Compliant. No PixInsight/WBPP/PJSR source code was read or used. This implements GLASS-owned triangle descriptor candidate scoring and validates it against synthetic known-truth catalogs only.
