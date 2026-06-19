# S2-Gate440 Status: Fused Native FITS U16 GPU Decode Staging

## Gate

S2-Gate440

## Result

Passed. This gate adds an explicit resident CUDA fast path for compact primary
FITS light frames with `BITPIX=16`, `BSCALE=1`, `BZERO=32768`, and no `BLANK`.
The path reads raw FITS payload bytes into pinned host buffers, uploads compact
2-byte pixels, decodes unsigned camera values on the GPU, and fuses that decode
with resident calibration.

This is not promoted to the default automatic path yet. The default remains the
existing compatible FITS reader unless the user selects
`--resident-fits-read-mode native_u16_gpu`.

## Completed Work

- Added native raw FITS payload reader for compatible u16/BZERO frames.
- Added pinned uint8 host staging buffers for raw FITS reads.
- Added resident CUDA raw big-endian u16 + BZERO decode/calibration kernel.
- Added resident stack Python wrapper for batched raw-u16 GPU decode.
- Added `--resident-fits-read-mode native_u16_gpu` CLI mode.
- Added artifact fields for raw GPU decode enablement, compact H2D bytes, and
  avoided float32 host materialization bytes.
- Added focused tests for raw FITS I/O, resident stack GPU decode/calibration,
  and CLI artifact contract.
- Updated Phase 2 algorithm hardening notes and source registry.

## Commands Run

- `.\.venv\Scripts\python.exe -m py_compile src\glass_cuda.py src\glass\io\fits_fast.py src\glass\engine\resident_cuda.py src\glass\cli.py`
- `cmd.exe /c call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 && .venv\Scripts\cmake.exe --build build\native-cuda-glass --target _glass_cuda_native --config Debug -j 8`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_fits_io.py tests\test_cuda_resident_stack.py::test_resident_stack_calibrates_u16be_raw_on_gpu_like_cpu tests\test_resident_cuda_run.py::test_cli_resident_cuda_records_native_u16_gpu_decode_backend`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py tests\test_gpu_calibration_vs_cpu.py tests\test_resident_cuda_run.py::test_cli_resident_cuda_records_native_direct_fits_backend tests\test_resident_cuda_run.py::test_cli_resident_cuda_records_native_u16_gpu_decode_backend`
- `.\.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\final_m38_h_200\glass_current_20260514_154556\processing_plan.json --out C:\glass_runs\final_m38_h_200\glass_s2_gate440_native_u16_gpu_warm_20260619_223129 --backend cuda --memory-mode resident --resident-runtime-preset throughput-v1 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\final_m38_h_200\glass_s2_gate436_shared_master_cache_20260619_204953 --resident-fits-read-mode native_u16_gpu`
- `.\.venv\Scripts\python.exe -m glass.cli report --run C:\glass_runs\final_m38_h_200\glass_s2_gate440_native_u16_gpu_warm_20260619_223129 --out C:\glass_runs\final_m38_h_200\glass_s2_gate440_native_u16_gpu_warm_20260619_223129\report.html`
- `.\.venv\Scripts\python.exe -m glass.cli compare --gpwbpp C:\glass_runs\final_m38_h_200\glass_s2_gate440_native_u16_gpu_warm_20260619_223129\integration\master_light_H.fits --reference C:\glass_runs\final_m38_h_200\glass_s2_gate438_astropy_control_warm_20260619_213148\integration\master_light_H.fits --out C:\glass_runs\final_m38_h_200\glass_s2_gate440_native_u16_gpu_warm_20260619_223129\gate440_native_u16_gpu_vs_gate438_astropy.html`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_440_cuda_doctor.json`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused raw-u16/CUDA/CLI tests: `12 passed in 0.74s`
- CLI smoke tests: `30 passed in 5.52s`
- Resident/CUDA focused tests: `39 passed in 0.75s`
- Full suite: `1035 passed in 38.32s`

## CUDA Availability

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- CUDA native extension: loaded
- Doctor artifact: `runs/checkpoints/s2_gate_440_cuda_doctor.json`

## Real 200-Light Validation

Dataset/run root:
`C:\glass_runs\final_m38_h_200\glass_s2_gate440_native_u16_gpu_warm_20260619_223129`

Control runs:

- Gate438 astropy control:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate438_astropy_control_warm_20260619_213148`
- Gate439 native-direct float32 host decode:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate439_native_direct_fastpath_warm_20260619_215910`

Timing summary:

| Path | Total s | Light read/upload/calibrate s | Read wait s | Worker read cumulative s | Native H2D+cal s | Registration s | Integration s | Output write s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Gate438 astropy | 17.288 | 6.625 | 3.939 | 37.972 | 1.958 | 3.597 | 0.288 | 2.251 |
| Gate439 native_direct | 17.858 | 6.818 | 4.770 | 41.957 | 1.401 | 3.607 | 0.291 | 2.519 |
| Gate440 native_u16_gpu | 13.939 | 3.502 | 2.268 | 20.659 | 0.732 | 3.597 | 0.292 | 2.218 |

Gate440 vs Gate438:

- Total elapsed improvement: 17.288 s to 13.939 s
- Light read/upload/calibrate improvement: 6.625 s to 3.502 s
- Native H2D+calibrate/store improvement: 1.958 s to 0.732 s
- FITS backend counts: `native_u16be_raw=200`
- Raw H2D bytes: 24,660,480,000
- Avoided float32 host materialization bytes: 49,320,960,000

Numerical agreement:

- Gate440 vs Gate438 astropy master: RMS 0, relative RMS 0, max abs diff 0,
  p99.9 abs diff 0.
- Gate440 vs Gate439 native-direct master: RMS 0, relative RMS 0, max abs diff
  0, p99.9 abs diff 0.

DQ/mask contract:

- Active frames: 193
- Masked frames: 7
- Unknown zero-weight frames: 0
- DQ passed: true
- Masked frame ids: `F000160`, `F000213`, `F000214`, `F000215`, `F000216`,
  `F000217`, `F000218`

## Artifacts

- Summary JSON: `runs/checkpoints/s2_gate_440_native_u16_gpu_summary.json`
- CUDA doctor JSON: `runs/checkpoints/s2_gate_440_cuda_doctor.json`
- Run report: `C:\glass_runs\final_m38_h_200\glass_s2_gate440_native_u16_gpu_warm_20260619_223129\report.html`
- Compare vs astropy control:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate440_native_u16_gpu_warm_20260619_223129\gate440_native_u16_gpu_vs_gate438_astropy.html`
- Compare vs native-direct control:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate440_native_u16_gpu_warm_20260619_223129\gate440_native_u16_gpu_vs_gate439_native_direct.html`
- Resident artifacts:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate440_native_u16_gpu_warm_20260619_223129\resident_artifacts.json`
- DQ closure:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate440_native_u16_gpu_warm_20260619_223129\resident_dq_pixel_closure.json`

## Known Limitations

- Raw GPU decode is limited to simple primary FITS frames matching
  `BITPIX=16`, `BSCALE=1`, `BZERO=32768`, and no `BLANK`.
- The mode currently requires `--resident-runtime-preset throughput-v1`, because
  it depends on batched callback-release resident calibration.
- It is explicit-only in this gate and is not yet the guarded automatic default.
- It does not parse compressed/tiled FITS, extensions, XISF, non-standard scale
  metadata, or unsigned representations without BZERO.
- This gate did not run PixInsight/WBPP; it compared against prior GLASS astropy
  and native-direct controls on the same 200-light dataset.

## Next Step

S2-Gate441 should implement a guarded compatible auto-selection policy for this
raw-u16 GPU path:

- Select it automatically only when every light in the resident group matches
  the exact safe FITS contract.
- Fall back to astropy-compatible reading with explicit artifact reasons.
- Preserve zero-diff validation against the compatible path.
- Keep the public default conservative until the guard is fully proven.

## Source Boundary

This gate used GLASS source code, public FITS format behavior, local synthetic
tests, and user-owned output artifacts. It did not read or derive code from
official PixInsight/WBPP/PJSR source.
