# S2-Gate 468 Status: Resident Chunked Warp Metadata Upload Reuse

## Gate

- Gate: S2-Gate 468
- Scope: reduce resident chunked matrix-warp orchestration overhead by uploading
  frame-index and inverse-matrix metadata once per native batch call.
- Status: passed
- Date: 2026-06-22 local

## Completed Work

- Updated native chunked bilinear and Lanczos3 resident matrix warp paths:
  - prepare all frame indices and inverse matrices once for the full batch;
  - upload all index metadata once;
  - upload all inverse metadata once;
  - reuse device pointer offsets for each chunk;
  - keep output and coverage scratch allocation bounded by chunk capacity.
- Updated native batch workspace allocation:
  - output bytes remain `chunk_capacity * frame_bytes`;
  - coverage bytes remain `chunk_capacity * pixel_count`;
  - inverse bytes now cover all requested frames;
  - index bytes now cover all requested frames.
- Fixed a first-attempt bug before acceptance:
  - focused tests caught incorrect output because scatter used the unoffset
    index pointer for later chunks;
  - scatter now receives the same chunk-offset index pointer as the warp
    kernel.
- Added native timing fields:
  - `chunk_metadata_upload_mode`
  - `index_upload_count`
  - `inverse_upload_count`
- Added resident registration artifact fields:
  - `triangle_warp_batch_native_chunk_metadata_upload_mode`
  - `triangle_warp_batch_native_index_upload_count`
  - `triangle_warp_batch_native_inverse_upload_count`
- Updated resident memory planning so full-batch metadata bytes are counted.
- Updated tests and Phase 2 documentation.

## CUDA Status

- CUDA available: true.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Device memory: 97886 MiB.
- Multiprocessors: 188.
- Driver version from device list: 596.21.

## Validation

- Focused CUDA validation:
  - bilinear batch warp, five frames, `max_chunk_capacity_frames=2`;
  - Lanczos3 batch warp, five frames, `max_chunk_capacity_frames=2`;
  - both paths still use three chunks;
  - both paths now report `index_upload_count=1`;
  - both paths now report `inverse_upload_count=1`;
  - both paths report
    `chunk_metadata_upload_mode=single_device_batch_reused_by_chunks`;
  - both paths match CPU reference output.
- Memory model validation:
  - output/coverage bytes remain chunk-capacity bounded;
  - index/inverse bytes now cover the full planned warp frame count.
- Resident artifact validation:
  - default chunked CUDA triangle alignment records one metadata upload per
    kind in `resident_registration`.
- Broader resident/CUDA/CLI regression passed.
- Full pytest passed.

## Real 200-Light Baseline

- A new 200-light run was not launched for this gate.
- Reason: C: had only about `0.17 GiB` free during validation.
- This gate changes metadata upload scheduling and memory accounting only; it
  does not change interpolation equations, transform fitting, rejection,
  integration math, or frame admission.
- Applicable baseline remains S2-Gate465:
  - run:
    `C:\glass_runs\phase2_s2_gate_465_200\admission_capacity_default_parity_r3_20260622`
  - input: M38 H-alpha, 200 lights, 20 bias, 20 dark, 20 flat;
  - internal GLASS timing: `36.103794 s`;
  - outer PowerShell timing: `36.485266 s`;
  - WBPP black-box timing: `1092.541 s`;
  - speedup vs WBPP: `30.261113x`;
  - native chunk frames: `8`;
  - native chunk count: `24`;
  - expected metadata upload reduction: one index upload and one inverse upload
    per native batch call instead of per chunk;
  - compare RMS diff: `0.00170058`;
  - P99 absolute diff: `0.000459801`;
  - coverage fraction: `0.961043`.

## Commands Run

- `cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 >nul && ".\.venv\Scripts\cmake.exe" --build build\native-cuda-glass --config Release --target _glass_cuda_native'`
- `.\.venv\Scripts\ruff.exe check cpp src tests`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_warp_vs_cpu.py::test_resident_stack_matrix_bilinear_batch_respects_max_chunk_capacity tests\test_gpu_warp_vs_cpu.py::test_resident_stack_matrix_lanczos3_batch_respects_max_chunk_capacity tests\test_resident_cuda_run.py::test_resident_memory_estimate_counts_full_chunk_metadata_workspace tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_warp_vs_cpu.py tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Native build: passed.
- Ruff: passed.
- Focused pytest after fix: `4 passed in 0.58s`.
- Resident/CUDA/CLI pytest: `158 passed in 14.39s`.
- Full pytest: `1102 passed in 48.64s`.

## Artifacts

- `runs/checkpoints/s2_gate_468_chunk_metadata_upload_summary.json`
- `runs/checkpoints/s2_gate_468_status.md`

## Known Limitations

- Warp, coverage-reduce, and scatter kernels still launch once per chunk.
- This gate reduces repeated metadata uploads but does not fuse chunk kernels.
- A new 200-light output run was skipped because C: free space was too low.

## Clean-Room Compliance

- Compliant.
- No official PixInsight WBPP/PJSR source was read, summarized, copied, or used.
- WBPP evidence remains limited to user-generated black-box timing/output
  artifacts from earlier accepted baselines.
- User image input directories were not modified.
