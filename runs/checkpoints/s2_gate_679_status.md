# S2-Gate 679 Status: Hardened Reducer Launch-Shape Audit

## Gate

S2-Gate 679.

## Completed Content

- Added a native resident hardened winsorized integration profile field:
  `hardened_kernel_threads_per_block=256`.
- Emitted the field in both native count-map branches so full-audit and reduced
  output-map routes share the same launch-shape contract.
- Added focused CUDA resident tests that assert the profile field for weighted,
  large-frame, and unit-positive count-map paths.
- Ran real 200-light launch-shape candidates for 128, 512, and final profiled
  256-thread defaults.
- Rejected 128/512 block-size tuning as a negative optimization result. Both
  candidates were bitwise identical to the 256-thread control across all six
  integration FITS outputs, but both were slower.
- Updated integration, hardening, validation, and algorithm-source docs.

## Commands Run

```powershell
cmd.exe /s /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 >nul && "C:\Users\ljs\WORK\astro\gpuwbpp\.venv\Scripts\cmake.exe" --build build --config Release --target _glass_cuda_native -j 8'
.\.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py -k "hardened_winsorized_sigma"
.\.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate679_wave_fill_mode\runs_20260626_140000\single_wait_fresh --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final
.\.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate679_hardened_threads\runs_20260626_143000\threads128_candidate --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final
.\.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate679_hardened_threads\runs_20260626_143000\threads512_candidate --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final
.\.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate679_hardened_threads\runs_20260626_143000\threads256_profile_default --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final
.\.venv\Scripts\python.exe -m glass.cli phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate679_hardened_threads\runs_20260626_143000\threads256_profile_default --out C:\glass_runs\phase2_s2_gate679_hardened_threads\gate679_phase2_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate679_hardened_threads\gate679_phase2_mainline_audit.md --min-lights 200 --min-active-frames 193 --max-masked-frames 7 --fail-on-not-green
.\.venv\Scripts\python.exe -m glass.cli resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate679_wave_fill_mode\runs_20260626_140000\single_wait_fresh --candidate-run C:\glass_runs\phase2_s2_gate679_hardened_threads\runs_20260626_143000\threads256_profile_default --out C:\glass_runs\phase2_s2_gate679_hardened_threads\gate679_default_profile_vs_fresh_regression.json --markdown C:\glass_runs\phase2_s2_gate679_hardened_threads\gate679_default_profile_vs_fresh_regression.md --max-elapsed-ratio 1.05 --min-active-frame-count 193 --max-masked-frame-count 7 --fail-on-failure
.\.venv\Scripts\python.exe -m glass.cli resident-runtime-compare --run fresh256=C:\glass_runs\phase2_s2_gate679_wave_fill_mode\runs_20260626_140000\single_wait_fresh --run threads128=C:\glass_runs\phase2_s2_gate679_hardened_threads\runs_20260626_143000\threads128_candidate --run threads512=C:\glass_runs\phase2_s2_gate679_hardened_threads\runs_20260626_143000\threads512_candidate --run profiled256=C:\glass_runs\phase2_s2_gate679_hardened_threads\runs_20260626_143000\threads256_profile_default --baseline-label fresh256 --out C:\glass_runs\phase2_s2_gate679_hardened_threads\gate679_threads_runtime_compare.json --markdown C:\glass_runs\phase2_s2_gate679_hardened_threads\gate679_threads_runtime_compare.md
.\.venv\Scripts\python.exe -m pytest -q
```

The 128-thread and 512-thread runs used temporary CUDA launch-shape patches
that were reverted before the final profiled 256-thread default.

## Test Results

- Focused final CUDA test:
  `20 passed, 57 deselected in 0.57 s`.
- Phase 2 mainline audit:
  passed, failed checks `[]`, input lights `200`, active frames `193`.
- Regression of final profiled 256-thread default against fresh 256-thread
  control:
  passed, failed checks `[]`, elapsed ratio `1.0220616179844362`.
- Runtime compare:
  best label `fresh256`; final profiled 256-thread resident integration ratio
  `0.9994896017595635`.
- Full pytest:
  `1420 passed in 65.33 s`.

## Real 200-Light Timing Summary

- Fresh 256-thread control:
  - resident integration: `3.3787344000302255 s`
  - native kernel sync: `3.2560789 s`
- 128-thread candidate:
  - resident integration: `3.5057293999707326 s`
  - native kernel sync: `3.3859033 s`
- 512-thread candidate:
  - resident integration: `3.4998344000196084 s`
  - native kernel sync: `3.3783218 s`
- Final profiled 256-thread default:
  - resident integration: `3.3770098999375477 s`
  - native kernel sync: `3.2540928 s`

## CUDA Availability

CUDA was available on this workstation. The native CUDA extension built and the
real 200-light resident CUDA runs completed.

## Known Limitations

- Gate679 is not a new speedup gate. It is a negative optimization and audit
  gate that prevents more simple block-size tuning from consuming Phase 2 time.
- The final profiled 256-thread run was slightly slower than the fresh
  256-thread control in total elapsed time due to surrounding light-stage
  variance, while resident integration was effectively unchanged.
- Build warnings remain: the existing Windows codepage warning and an existing
  signed/unsigned comparison warning.

## Next Step

Return to substantive mainline work:

- deterministic cooperative/segmented reducer redesign for resident hardened
  integration, or
- H2D/read/calibration overlap and pinned-buffer pipelining for the
  light-read/upload/calibrate bucket.

Do not spend additional gates on 128/256/512 block-size retesting unless the
kernel algorithm itself changes.

## Clean-Room Compliance

Compliant. This gate used only GLASS-owned CUDA/profile code, GLASS tests, and
user-owned real benchmark artifacts. It did not read, copy, summarize, or
rework proprietary PixInsight/WBPP/PJSR source, and it did not modify input
image directories.
