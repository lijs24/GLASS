# Optimization Gate 07: CUDA Catalog Shared-memory Sort

## Gate

Optimization Gate 07

## Completed

- Replaced the grid/NMS catalog path's single-thread candidate sort with a shared-memory parallel odd-even sort for candidate grids up to 4096 entries.
- Kept the exact same candidate selection and NMS stages; the change is limited to ordering the grid candidate buffer before NMS.
- Preserved the old single-thread sort as a fallback for larger candidate buffers.

## Commands Run

- `cmd /c "call ""C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat"" -arch=x64 -host_arch=x64 >nul && ""<repo>\.venv\Scripts\cmake.exe"" --build build\native-cuda --config Release --target _glass_cuda_native"`
- `.venv\Scripts\python.exe -m pytest -q tests\test_gpu_star_detect.py tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Targeted CUDA star/resident tests: `12 passed`.
- Full pytest: `181 passed in 8.02s`.

## CUDA Status

CUDA is available through the native backend.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Native backend: true

## Known Limitations

- This still sorts one frame's candidate grid at a time inside the existing launch sequence.
- It does not yet fuse candidate generation, sorting, NMS, and descriptor generation into a single persistent resident pipeline.
- A real M38 benchmark is required to quantify the effect on the 14.9 s moving-catalog phase.

## Next Step

Run the same M38 resident triangle benchmark as the current best `cand48_batchcatalog` run, then compare timing, SHA/quality, and WBPP acceptance metrics.

## Clean-room Compliance

Compliant. This gate only modified GLASS-owned CUDA code and used project tests. It did not read, copy, summarize, or modify PixInsight/WBPP/PJSR official source code, and it did not touch original image data.
