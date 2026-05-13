# Optimization Gate 06: Resident Catalog Batch Scheduling

## Gate

Optimization Gate 06

## Completed

- Added `ResidentCalibratedStack.star_grid_top_nms_candidates_batch` to the native CUDA binding.
- Reused one set of device scratch buffers across a batch of resident frames for grid/NMS star catalog extraction.
- Added the public `gpwbpp_cuda.ResidentCalibratedStack.star_grid_top_nms_candidates_batch` wrapper.
- Wired `similarity_cuda_triangle` resident registration to batch moving-frame grid/NMS catalogs when:
  - grid catalog mode is enabled;
  - the star threshold is fixed;
  - the native batch method is available.
- Added `triangle_moving_catalog_batch` timing and resident artifact fields:
  - `triangle_catalog_batch`
  - `triangle_catalog_batch_mode`
- Added tests for native batch-vs-single catalog equality and resident triangle artifact/timing coverage.

## Commands Run

- `.venv\Scripts\cmake.exe --build build\native-cuda --config Release --target _gpwbpp_cuda_native`
  - Initial plain-shell build failed because the MSVC/Windows SDK include environment was not loaded.
- `cmd /c "call ""C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat"" -arch=x64 -host_arch=x64 >nul && ""C:\Users\ljs\WORK\astro\gpuwbpp\.venv\Scripts\cmake.exe"" --build build\native-cuda --config Release --target _gpwbpp_cuda_native"`
- `.venv\Scripts\ruff.exe check src\gpwbpp_cuda.py src\gpwbpp\engine\resident_cuda.py tests\test_gpu_star_detect.py tests\test_resident_cuda_run.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_gpu_star_detect.py::test_resident_stack_star_grid_top_nms_candidates_batch_matches_single_calls tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -c "import gpwbpp_cuda, json; print(json.dumps(gpwbpp_cuda.list_devices(), ensure_ascii=False))"`

## Test Results

- Ruff: passed.
- Targeted CUDA/resident tests: `2 passed`.
- Full pytest: `181 passed in 8.00s`.

## CUDA Status

CUDA is available through the native backend.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Native backend: true

## Known Limitations

- The new batch path still launches and synchronizes once per frame internally; it removes repeated scratch allocation and Python catalog calls, but it is not yet a single fully fused batched CUDA kernel.
- D2H catalog copies still occur per frame because triangle descriptor fitting currently consumes host-visible catalog arrays.
- This checkpoint validates synthetic/unit correctness only. A real M38 benchmark is still required to quantify the speed impact.

## Next Step

Run the fixed-threshold M38 resident triangle benchmark with the same accepted settings as the current best run, compare total and component timings, then generate/record the acceptance compare report if the result remains within tolerance.

## Clean-room Compliance

Compliant. This gate only changed GPWBPP-owned CUDA/Python code and tests. It did not read, copy, summarize, or modify PixInsight/WBPP/PJSR official source code, and it did not touch original image data.
