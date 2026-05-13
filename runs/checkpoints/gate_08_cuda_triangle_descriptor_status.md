# Gate 08 Checkpoint: CUDA triangle descriptor primitive

## Gate

Gate 08: Registration.

## Completed content

- Added `glass_cuda.triangle_asterism_descriptors_f32(...)`.
- Added a CUDA kernel that computes local nearest-neighbor triangle side-ratio descriptors from compact star catalogs.
- Added native pybind11 binding and Python compatibility wrapper.
- Exported the function through `glass.gpu.registration`.
- Added GPU test coverage comparing CUDA descriptor output to the GLASS-owned CPU triangle bridge.
- Updated CUDA and registration documentation.

## Commands run

- `.\\.venv\\Scripts\\python.exe -m ruff check src\\glass_cuda.py src\\glass\\gpu\\registration.py tests\\test_gpu_registration_search.py`
- `.\\.venv\\Scripts\\cmake.exe --build build\\native-cuda --config Release`
- `cmd.exe /d /s /c 'call "C:\\Program Files (x86)\\Microsoft Visual Studio\\2022\\BuildTools\\Common7\\Tools\\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .venv\\Scripts\\cmake.exe --build build\\native-cuda --config Release'`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_gpu_registration_search.py::test_gpu_triangle_asterism_descriptors_match_cpu_bridge`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_gpu_registration_search.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `git diff --check`

## Test results

- Ruff on touched Python files: `All checks passed!`.
- Native CUDA build: succeeded after initializing the VS BuildTools developer environment for the current command.
- New targeted descriptor test: `1 passed in 0.13s`.
- GPU registration test module: `26 passed in 0.17s`.
- Full pytest suite: `154 passed in 7.18s`.
- `git diff --check`: no whitespace errors; only Git CRLF conversion warnings.

## CUDA availability

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- Total VRAM: 97886 MiB
- Native backend: available

## Known limitations

- This is descriptor generation only; descriptor matching and RANSAC-style hypothesis selection are not yet fully on the GPU.
- The current wrapper downloads compact descriptor arrays for host-side deduplication and area ordering.
- The descriptor family is triangle-based. PixInsight public material describes newer polygonal descriptor families; quads/pentagons remain future work.
- The native build emits CUDA header C4819 warnings under the current Windows code page, but the build succeeds.

## Next step

Move descriptor matching and candidate similarity hypothesis scoring to CUDA using the descriptor arrays produced here, then wire the accepted candidate into resident matrix warp and the 200-light benchmark path.

## Clean-room compliance

Compliant. No PixInsight/WBPP/PJSR source code was read or used. This CUDA primitive implements GLASS-owned local triangle descriptor generation and is validated only against GLASS's CPU bridge.
