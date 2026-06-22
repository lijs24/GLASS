# S2-Gate 466 Status: Native Chunk-Capacity Warp Dispatch

## Gate

- Gate: S2-Gate 466
- Scope: move resident CUDA matrix-warp reduced chunk-capacity control from
  Python-level batch splitting into the native chunked warp dispatcher.
- Status: passed
- Date: 2026-06-22 local

## Completed Work

- Added native `max_chunk_capacity_frames` support to chunked resident matrix
  batch warp bindings:
  - `apply_matrix_bilinear_frames`
  - `apply_matrix_lanczos3_frames`
- Updated native chunked warp workspace allocation so an explicit positive max
  capacity clamps the initial chunk capacity before the existing OOM fallback.
- Added native timing metadata:
  - `batch_max_chunk_capacity_frames`
  - `batch_capacity_source`
- Updated `src/glass_cuda.py` wrappers to validate and pass the new argument.
- Updated resident CUDA execution so admission-selected reduced capacity is
  passed to native once instead of splitting the frame indices in Python.
- Preserved the full-capacity/default path: no forced max capacity is supplied
  for `resident_full_frame`, so the native allocator remains
  `native_preferred`.
- Added focused CUDA tests for bilinear and Lanczos3 native reduced-capacity
  output and CPU agreement.
- Updated Phase 2 documentation and the algorithm-source matrix.

## CUDA Status

- CUDA available: true.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Device memory: 97886 MiB.
- Multiprocessors: 188.
- Driver version from device list: 596.21.

## Validation

- Focused native CUDA validation:
  - bilinear batch warp, five frames, `max_chunk_capacity_frames=2`;
  - Lanczos3 batch warp, five frames, `max_chunk_capacity_frames=2`;
  - each path reports `batch_capacity_source=explicit_max_chunk_capacity`,
    `batch_chunk_frames=2`, `batch_chunk_count=3`, and
    `native_chunked_batch_warp_scatter_one_sync`;
  - each path uses only two-frame output/coverage workspace;
  - GPU output and weight maps match CPU references.
- Resident engine validation:
  - reduced capacity now makes one stack call for all five frame indices;
  - native receives `max_chunk_capacity_frames=2`;
  - no Python-level chunk splitting is required for reduced-capacity execution.
- Broader CUDA/resident/CLI regression passed.
- Full pytest passed.

## Real 200-Light Baseline

- A new 200-light run was not launched for this gate.
- Reason: C: had only about `0.404 GiB` free during validation, while a new
  large output directory would risk disk exhaustion.
- Applicable baseline remains S2-Gate465 because the default 200-light path is
  still unforced `native_preferred` chunked dispatch:
  - run:
    `C:\glass_runs\phase2_s2_gate_465_200\admission_capacity_default_parity_r3_20260622`
  - input: M38 H-alpha, 200 lights, 20 bias, 20 dark, 20 flat;
  - internal GLASS timing: `36.103794 s`;
  - outer PowerShell timing: `36.485266 s`;
  - WBPP black-box timing: `1092.541 s`;
  - speedup vs WBPP: `30.261113x`;
  - native chunk frames: `8`;
  - native chunk count: `24`;
  - capacity source: `native_preferred`;
  - compare RMS diff: `0.00170058`;
  - P99 absolute diff: `0.000459801`;
  - coverage fraction: `0.961043`.

## Commands Run

- `cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 >nul && ".\.venv\Scripts\cmake.exe" --build build\native-cuda-glass --config Release --target _glass_cuda_native'`
- `.\.venv\Scripts\ruff.exe check src\glass_cuda.py src\glass\engine\resident_cuda.py tests\test_resident_cuda_run.py tests\test_gpu_warp_vs_cpu.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_warp_vs_cpu.py::test_resident_stack_matrix_bilinear_batch_respects_max_chunk_capacity tests\test_gpu_warp_vs_cpu.py::test_resident_stack_matrix_lanczos3_batch_respects_max_chunk_capacity tests\test_resident_cuda_run.py::test_resident_registration_matrix_batch_honors_chunk_capacity`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_warp_vs_cpu.py tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Native build: passed.
- Ruff: passed.
- Focused pytest: `3 passed in 0.30s`.
- Broader CUDA/resident/CLI pytest: `157 passed in 14.53s`.
- Full pytest: `1101 passed in 48.05s`.

## Artifacts

- `runs/checkpoints/s2_gate_466_native_capacity_summary.json`
- `runs/checkpoints/s2_gate_466_status.md`

## Known Limitations

- Native reduced-capacity dispatch now avoids Python-level splitting, but chunks
  still execute serially inside one native call.
- Gate466 did not create a new large 200-light output because local C: free
  space was too low.
- The next substantive optimization should continue reducing
  registration/warp orchestration overhead or move back to DQ/mask default-path
  contracts.

## Clean-Room Compliance

- Compliant.
- No official PixInsight WBPP/PJSR source was read, summarized, copied, or used.
- WBPP evidence remains limited to user-generated black-box timing/output
  artifacts from earlier accepted baselines.
- User image input directories were not modified.
