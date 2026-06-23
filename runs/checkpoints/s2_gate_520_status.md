# S2-Gate 520 Status: Adaptive Native DQ Dispatch

## Gate

- Gate: S2-Gate 520
- Name: Adaptive resident DQ native dispatch
- Status: green
- Branch: `main`
- Scope: runtime dispatch and performance recovery for the resident DQ map
  host scanner.

## Completed

- Profiled the Gate519 native-host DQ path and found the local native
  extension build was unoptimized for this scanner. `_resident_dq_map` spent
  about `5.089 s` in native host DQ work on the current Debug-flavored native
  build.
- Added `_glass_cuda_native.resident_dq_map_host_f32_optimized()`.
- Added Python wrapper APIs:
  - `glass_cuda.resident_dq_map_host_f32_optimized()`
  - `glass_cuda.resident_dq_map_host_f32_preferred()`
- Changed resident `_resident_dq_map(..., return_stats=True)` to call native
  DQ only when it is available and preferred.
- Added `GLASS_RESIDENT_DQ_NATIVE_HOST` diagnostics override:
  - `native`, `force`, `1`, `true`, `yes`, `on` force native when available;
  - `python`, `fallback`, `0`, `false`, `no`, `off` force Python fallback.
- Added focused tests for fallback dispatch, native dispatch, optimized-build
  preference, and environment overrides.
- Ran a real M38 H-alpha 200-light A/B using the same plan and WBPP black-box
  reference as Gate519.

## Commands Run

- `python -m cProfile -o C:\glass_runs\phase2_s2_gate520_profile_current\runs_20260623_101144\warm_repeat.prof ...`
- `python -m pstats ...` to identify the `_resident_dq_map` native-host DQ
  regression.
- `cmd /c "call C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build --config Release"`
- `.\.venv\Scripts\python.exe -m ruff check src\glass_cuda.py src\glass\engine\resident_cuda.py tests\test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py -k "resident_dq_map or resident_dq_coverage_provenance"`
- `.\.venv\Scripts\python.exe -m glass.cli doctor`
- `.\.venv\Scripts\python.exe -m pytest -q`
- Real 200-light warm and full runs used:
  - `glass run --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit`
  - warm/default shared master cache outputs under
    `C:\glass_runs\phase2_s2_gate520_adaptive_dq_dispatch\runs_20260623_101337\warm_auto`
    and `...\warm_repeat_auto`
  - full per-run cache output under
    `C:\glass_runs\phase2_s2_gate520_adaptive_dq_dispatch\runs_20260623_101337\full_run_cache_policy_run`
- Compare reports:
  - Gate520 warm-repeat vs Gate519 warm-repeat
  - Gate520 full run vs Gate520 warm-repeat
  - Gate520 warm-repeat vs WBPP black-box master

## Test Results

- Ruff: passed.
- Focused DQ dispatch/provenance tests: `10 passed, 76 deselected in 0.42s`.
- Full pytest: `1164 passed in 42.34s`.
- CUDA doctor: passed.

## CUDA Status

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.
- Local native DQ optimization flag: false for the current local native build,
  so the default dispatch used the Python fallback for DQ map stats.

## Real 200-Light Results

- Run root:
  `C:\glass_runs\phase2_s2_gate520_adaptive_dq_dispatch\runs_20260623_101337`
- Summary artifact:
  `runs/checkpoints/s2_gate_520_adaptive_dq_dispatch_summary.json`
- Input light frames: `200`.
- Active integrated frames: `193`.
- Warm-repeat shared-cache GLASS:
  - internal total: `7.791562700003851 s`
  - shell wall: `8.173170299999999 s`
- Full per-run-cache GLASS:
  - internal total: `12.324912499985658 s`
  - shell wall: `12.7043354 s`
- WBPP black-box elapsed: `1092.541 s`.
- Speedup versus WBPP:
  - warm internal: `140.22103678886648x`
  - warm shell: `133.67407748741024x`
  - full internal: `88.6449295280004x`
  - full shell: `85.99749342259966x`
- Regression recovery versus Gate519:
  - warm shell saved `3.0260962000000013 s`
  - full shell saved `2.9291234 s`

## Numerical Validation

- Gate520 warm-repeat vs Gate519 warm-repeat: bitwise match
  (`rms_diff=0.0`, `abs_diff_p99=0.0`, `max_abs_diff=0.0`).
- Gate520 full run vs Gate520 warm-repeat: bitwise match
  (`rms_diff=0.0`, `abs_diff_p99=0.0`, `max_abs_diff=0.0`).
- Gate520 warm-repeat vs WBPP black-box master:
  - shape match: true
  - robust-fit RMS over fit pixels: `0.0015009512947433384`
  - robust-fit p99 absolute difference: `0.00034034321741462114`
  - robust-fit fraction: `0.982980688129347`

## Known Limitations

- The native host DQ scanner is still useful only when compiled as an optimized
  native build. Debug or unknown native builds now keep the faster Python
  fallback by default.
- This gate does not change calibration formulas, registration, warp,
  winsorized rejection, DQ bit definitions, integration math, accepted-frame
  decisions, or output pixels.
- The next major runtime bottlenecks remain:
  - resident light read/upload/calibration orchestration;
  - resident registration/warp batching and Python/native synchronization.

## Disk Cleanup Note

- C drive had about `441 GB` free during this gate.
- Workspace size was about `2.374 GB`.
- Large generated evidence directories were:
  - `C:\glass_runs`: about `80.473 GB`
  - `C:\gpwbpp_runs`: about `83.686 GB`
- No cleanup was performed because the latest 200-light A/B artifacts are still
  active evidence. If space becomes tight, old `C:\glass_runs\phase2_s2_gate50x`
  and earlier temporary run roots are the best candidates after preserving their
  checkpoint summaries.

## Next Step

- Continue Phase 2 substantive gates on:
  - I/O, decode, H2D upload, and calibration overlap;
  - resident registration/warp batch residency;
  - numeric consistency against the 200-light WBPP black-box reference.

## Clean-Room Compliance

- No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or
  reworked.
- Validation used only GLASS code, GLASS-generated artifacts, the user-staged
  M38 H-alpha dataset, and user-generated WBPP black-box timing/output files.
- Input image directories were treated as read-only.
