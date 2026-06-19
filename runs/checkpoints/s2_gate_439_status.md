# S2-Gate 439 Status: Resident Native-Direct FITS Decode Probe

## Result

Passed as a substantive runtime probe, with no default promotion.

Gate439 adds a native CUDA-extension FITS decode path that can decode simple
primary FITS images directly into caller-provided float32 buffers, including
the resident pinned host prefetch ring. The path is numerically correct on the
real M38 H 200-light benchmark, but the same-code warm-cache benchmark does not
beat the Gate438 astropy control, so `astropy` remains the default reader.

## Completed

- Added native binding `read_simple_fits_into_f32`.
- Added Python wrapper `glass_cuda.read_simple_fits_into_f32`.
- Added `read_simple_fits_image_native_direct_timed`.
- Added resident `--resident-fits-read-mode native_direct`.
- Recorded native file-read, decode, total, and bytes-read timings in resident
  I/O artifacts and fine timing.
- Added a native fast path for common `BITPIX=16, BZERO=32768` unsigned-FITS
  data used by the 200-light benchmark.
- Added focused tests for native direct FITS decode into pinned buffers and
  resident backend-count/timing artifacts.
- Updated Phase 2 hardening docs and algorithm source ledger.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m py_compile src\glass\io\fits_fast.py src\glass\engine\resident_cuda.py src\glass\cli.py src\glass_cuda.py

& cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 && .venv\Scripts\cmake.exe --build build\native-cuda-glass --target _glass_cuda_native --config Debug -j 8'

.\.venv\Scripts\python.exe -m pytest -q tests\test_fits_io.py tests\test_resident_cuda_run.py::test_cli_resident_cuda_records_native_direct_fits_backend

.\.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py

.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py tests\test_gpu_calibration_vs_cpu.py

.\.venv\Scripts\python.exe -m glass.cli run --plan "C:\glass_runs\final_m38_h_200\glass_current_20260514_154556\processing_plan.json" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate439_native_direct_fastpath_warm_20260619_215910" --backend cuda --memory-mode resident --resident-runtime-preset throughput-v1 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir "C:\glass_runs\final_m38_h_200\glass_s2_gate436_shared_master_cache_20260619_204953" --resident-fits-read-mode native_direct

.\.venv\Scripts\python.exe -m glass.cli report --run "C:\glass_runs\final_m38_h_200\glass_s2_gate439_native_direct_fastpath_warm_20260619_215910" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate439_native_direct_fastpath_warm_20260619_215910\report.html"

.\.venv\Scripts\python.exe -m glass.cli compare --glass "C:\glass_runs\final_m38_h_200\glass_s2_gate439_native_direct_fastpath_warm_20260619_215910\integration\resident_master_H.fits" --reference "C:\glass_runs\final_m38_h_200\glass_s2_gate438_astropy_control_warm_20260619_213148\integration\resident_master_H.fits" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate439_native_direct_fastpath_warm_20260619_215910\gate439_native_direct_fastpath_vs_gate438_astropy.html" --glass-label gate439_native_direct_fastpath --reference-label gate438_astropy_control

.\.venv\Scripts\python.exe -m pytest -q

.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_439_cuda_doctor.json
```

## Test Results

- Native direct FITS + resident contract focused tests: `10 passed in 0.41s`.
- CLI smoke tests: `30 passed in 4.85s`.
- CUDA resident/calibration focused tests: `36 passed in 0.25s`.
- Full test suite: `1032 passed in 39.04s`.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor report: `runs/checkpoints/s2_gate_439_cuda_doctor.json`.

## Real 200-Light Results

Native-direct fastpath run:

- Run:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate439_native_direct_fastpath_warm_20260619_215910`.
- FITS backend counts: `native_direct_simple=200`.
- Native bytes read: `24660480000`.
- `light_read_upload_calibrate`: `6.818247 s`.
- `light_read_wait_wall`: `4.769937 s`.
- Worker read cumulative: `41.957217 s`.
- Worker native file read cumulative: `18.553432 s`.
- Worker native decode cumulative: `23.034660 s`.
- Native H2D+calibrate/store: `1.400839 s`.
- Registration accounted: `3.606558 s`.
- Integration: `0.290767 s`.

Gate438 astropy control:

- Run:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate438_astropy_control_warm_20260619_213148`.
- FITS backend counts: `astropy_scaled_memmap=200`.
- `light_read_upload_calibrate`: `6.624954 s`.
- `light_read_wait_wall`: `3.939295 s`.
- Worker read cumulative: `37.972015 s`.
- Worker materialize/decode cumulative: `33.797579 s`.
- Native H2D+calibrate/store: `1.958448 s`.
- Registration accounted: `3.597218 s`.
- Integration: `0.288448 s`.

Comparison against Gate438 astropy control:

- Shape match: true.
- `rms_diff`: `0`.
- `relative_rms_diff`: `0`.
- `max_abs_diff`: `0`.
- `abs_diff_p999`: `0`.
- Compare report:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate439_native_direct_fastpath_warm_20260619_215910\gate439_native_direct_fastpath_vs_gate438_astropy.html`.

DQ and masks:

- DQ pixel closure: passed.
- Active frames: `193`.
- Masked frames: `7`.
- Unknown zero-weight frames: `0`.

## Known Limits

- Native-direct is not default because it is still slower than astropy control
  in the same-code real benchmark.
- The native path writes expanded float32 host buffers before H2D; this is now
  the main target for the next gate.
- The current fast path is tuned for simple primary FITS and the common
  `BITPIX=16, BZERO=32768` convention. Unsupported FITS forms remain on the
  explicit astropy path.

## Next Step

S2-Gate440 should prototype fused native decode-to-upload or GPU-side decode
staging for compact uint16/raw FITS payloads, preserving exact calibration
semantics while reducing host-side float32 materialization and memory traffic.

## Clean-Room Status

Compliant. Gate439 uses public FITS format semantics, GLASS-generated tests,
and GLASS real-run artifacts only. It does not inspect external proprietary
implementation source, modify input image directories, change registration or
rejection math, or create release artifacts.
