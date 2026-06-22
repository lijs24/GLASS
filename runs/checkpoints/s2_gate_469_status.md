# S2-Gate 469 Status: Resident Chunked Warp Fused Postprocess

## Gate

- Gate: S2-Gate 469
- Scope: reduce resident chunked matrix-warp per-chunk launch overhead by
  fusing coverage-reduce and scatter into one CUDA postprocess kernel.
- Status: passed
- Date: 2026-06-22 local

## Completed Work

- Added CUDA launcher `glass_warp_batch_scatter_reduce_f32_launch`.
- The fused kernel:
  - reads chunked warp output scratch;
  - reads chunked warp coverage scratch;
  - writes warped pixels back to the resident stack by frame index;
  - accumulates per-pixel coverage in the same launch.
- Updated native chunked matrix warp paths:
  - `ResidentCalibratedStack.apply_matrix_bilinear_frames`
  - `ResidentCalibratedStack.apply_matrix_lanczos3_frames`
- Preserved output scratch and coverage scratch, so in-place warp safety is
  unchanged.
- Added native timing fields:
  - `postprocess_mode`
  - `postprocess_enqueue_s`
  - `postprocess_kernel_launches`
- Kept legacy coverage/scatter fields for compatibility; in fused mode their
  independent launch counts are zero.
- Added resident registration artifact fields:
  - `triangle_warp_batch_native_postprocess_enqueue_s`
  - `triangle_warp_batch_native_postprocess_mode`
  - `triangle_warp_batch_native_postprocess_kernel_launches`
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
  - bilinear one-chunk path matches CPU reference;
  - bilinear three-chunk reduced-capacity path matches CPU reference;
  - Lanczos3 one-chunk path matches CPU reference;
  - Lanczos3 three-chunk reduced-capacity path matches CPU reference;
  - chunked paths report `postprocess_mode=fused_scatter_reduce`;
  - independent coverage-reduce launch count is `0`;
  - independent scatter launch count is `0`;
  - fused postprocess launch count equals chunk count.
- Resident artifact validation:
  - small CUDA triangle-alignment run records fused postprocess mode and launch
    count in `resident_registration`.
- Broader resident/CUDA/CLI regression passed.
- Full pytest passed.

## Real 200-Light Baseline

- A new 200-light run was not launched for this gate.
- Reason: C: had only about `0.141 GiB` free during validation.
- This gate changes chunk postprocess scheduling only; it does not change
  interpolation equations, transform fitting, rejection, integration math, or
  frame admission.
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
  - expected postprocess launch reduction: coverage/scatter launches from `48`
    to `24` fused postprocess launches;
  - compare RMS diff: `0.00170058`;
  - P99 absolute diff: `0.000459801`;
  - coverage fraction: `0.961043`.

## Commands Run

- `cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 >nul && ".\.venv\Scripts\cmake.exe" --build build\native-cuda-glass --config Release --target _glass_cuda_native'`
- `.\.venv\Scripts\ruff.exe check cpp src tests`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_warp_vs_cpu.py::test_resident_stack_matrix_bilinear_batch_warp_matches_cpu_reference tests\test_gpu_warp_vs_cpu.py::test_resident_stack_matrix_bilinear_batch_respects_max_chunk_capacity tests\test_gpu_warp_vs_cpu.py::test_resident_stack_matrix_lanczos3_batch_warp_matches_cpu_reference tests\test_gpu_warp_vs_cpu.py::test_resident_stack_matrix_lanczos3_batch_respects_max_chunk_capacity tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_warp_vs_cpu.py tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Native build: passed.
- Ruff: passed.
- Focused pytest: `5 passed in 1.09s`.
- Resident/CUDA/CLI pytest: `158 passed in 14.35s`.
- Full pytest: `1102 passed in 47.79s`.

## Artifacts

- `runs/checkpoints/s2_gate_469_fused_warp_postprocess_summary.json`
- `runs/checkpoints/s2_gate_469_status.md`

## Known Limitations

- Chunked warp still launches one warp kernel and one fused postprocess kernel
  per chunk.
- A new 200-light output run was skipped because C: free space was too low.
- Further optimization likely needs CUDA Graph capture, stream batching, or a
  fused matrix-warped integration path.

## Clean-Room Compliance

- Compliant.
- No official PixInsight WBPP/PJSR source was read, summarized, copied, or used.
- WBPP evidence remains limited to user-generated black-box timing/output
  artifacts from earlier accepted baselines.
- User image input directories were not modified.
