# S2-Gate 610 Status: Native Hardened Integration Timing Profile

## Gate

- Gate: S2-Gate 610
- Theme: isolate the real bottleneck inside resident hardened winsorized
  integration before rewriting CUDA kernel internals.
- Status: green

## Completed

- Added optional native `profile` support to
  `ResidentCalibratedStack.integrate_hardened_winsorized_sigma`.
- Kept the ordinary native return contract unchanged when `profile=false`.
- Updated the Python timed wrapper to request native profile data when
  available and fall back on older native builds.
- Added `hardened_winsorized_timing_s.native_profile` with:
  - `allocation_s`
  - `weights_upload_s`
  - `kernel_sync_s`
  - `download_s`
  - `free_s`
  - `downloaded_arrays`
  - `downloaded_bytes`
- Added focused CUDA/API and resident CLI tests for the profile fields.
- Ran a small real 200-light stream/wave probe and did not promote any runtime
  preset change because the total-time result was not strong enough.
- Updated algorithm source log, integration model, and Phase 2 plan.

## Commands Run

```powershell
cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" && ".\.venv\Scripts\cmake.exe" --build build --config Release --target _glass_cuda_native'

.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py -k "hardened_winsorized_sigma"
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py -k "hardened_winsorized_matches_cpu_baseline"

.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate610_native_integration_profile\real_200_default_profiled --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final

.\.venv\Scripts\python.exe -m ruff check cpp src tests
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Native rebuild: passed.
- Focused hardened CUDA tests: `4 passed, 50 deselected`.
- Focused resident CLI hardened parity test: `1 passed, 114 deselected`.
- Ruff: `All checks passed`.
- Full pytest: `1289 passed in 52.25 s`.

## Real 200-Light Validation

- Run path:
  `C:\glass_runs\phase2_s2_gate610_native_integration_profile\real_200_default_profiled`
- Total elapsed: `11.776640900294296 s`.
- `resident_calibration_integration`: `10.933877700008452 s`.
- Effective route: `native_cuda_resident_stack`.
- Kernel selector: `small_256`.
- Native hardened integration timing: `3.752243599970825 s`.
- Native profile:
  - `allocation_s=0.0013176`
  - `weights_upload_s=0.0000149`
  - `kernel_sync_s=3.6350664`
  - `download_s=0.1124195`
  - `free_s=0.0033262`
  - `downloaded_arrays=5`
  - `downloaded_bytes=863116800`
- `pipeline_contract.json`: passed.
- `resident_result_contract.json`: passed.
- Six integration FITS outputs are SHA256-identical to Gate609.

## Calibration Stream/Wave Probe

- Probe path:
  `C:\glass_runs\phase2_s2_gate610_calibration_stream_probe`
- Variants:
  - `streams8_wave8_fill25`: total `11.768737399834208 s`,
    light wall `3.2985527999699116 s`.
  - `streams8_wave4_fill25`: total `11.643945400021039 s`,
    light wall `3.15277440007776 s`.
  - `streams4_wave4_fill0`: total `11.609837000141852 s`,
    light wall `3.1602428999030963 s`.
  - `default_v4_repeat`: total `11.638017000281252 s`,
    light wall `3.1676417000126094 s`.
  - `streams4_wave4_fill0_repeat`: total `11.641277200076729 s`,
    light wall `3.19558820000384 s`.
- Decision: no default runtime preset change. The differences are small and
  not stable enough to justify another tuning/default gate.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Build toolkit observed during native rebuild: CUDA 13.2.

## Known Limitations

- This gate does not accelerate the hardened kernel by itself.
- The profile uses host-side chrono around CUDA calls. It is sufficient for
  stage-level bottleneck attribution, not a per-kernel Nsight replacement.
- The current hardened kernel remains a bounded local-array median/IQR
  prototype with 256-frame and 512-frame variants.

## Next Step

- Implement a kernel-internal optimization for hardened median/IQR integration.
- The Gate610 profile shows that the next useful work is not output-map D2H
  download (`~0.112 s`) but the kernel+sync section (`~3.635 s`).
- The preferred next gate is a scalable device-side selection/segmented
  reducer, validated against CPUStackEngine and the real 200-light run.

## Clean-Room Compliance

- This gate uses GLASS-owned CUDA wrapper timing, GLASS-owned kernels, GLASS
  tests, and user-owned real benchmark artifacts.
- No external or proprietary implementation source was inspected, copied,
  summarized, or reworked.
- Input image directories were treated as read-only.
