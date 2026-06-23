# S2-Gate 529 Status: Release Native DQ Default Guard

## Gate

S2-Gate 529: keep the measured resident DQ default on the faster Python fast
path, even when the optional native host DQ scanner is built in Release mode.

## Completed

- Built `_glass_cuda_native` in a true Release CMake configuration for the local
  validation run.
- Measured the same M38 H-alpha 200-light resident CUDA route with forced Python
  DQ, Release-native default DQ, and post-change default DQ.
- Changed `glass_cuda.resident_dq_map_host_f32_preferred()` so native DQ is no
  longer auto-promoted by Release build status alone.
- Kept explicit diagnostic overrides:
  - `GLASS_RESIDENT_DQ_NATIVE_HOST=native`
  - `GLASS_RESIDENT_DQ_NATIVE_HOST=auto_native`
- Updated focused resident DQ dispatch tests.
- Ran GLASS-vs-WBPP black-box compare for the post-change default output.
- Removed the temporary `build-release-native` directory after validation.

## Commands

- `cmake -S . -B build-release-native -G Ninja -DGLASS_BUILD_PYTHON_CUDA=ON -DGLASS_BUILD_CUDA=OFF -DCMAKE_BUILD_TYPE=Release ...`
- `cmake --build build-release-native --target _glass_cuda_native -j 8`
- `python -m pytest -q tests/test_resident_cuda_run.py::test_resident_dq_map_native_preference_honors_build_and_env tests/test_resident_cuda_run.py::test_resident_dq_map_dispatch_uses_python_when_native_not_preferred tests/test_resident_cuda_run.py::test_resident_dq_map_dispatch_uses_native_when_preferred`
- Real 200-light A/B under `C:\glass_runs\phase2_s2_gate529_native_dq_release\runs_20260623_115631`
- `glass compare --glass ...\postchange_default\integration\resident_master_H.fits --reference ...\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --min-coverage 190 --ignore-border-px 128`
- `glass doctor --json runs\checkpoints\s2_gate_529_doctor.json --allow-cpu-only`
- `python -m pytest -q`

## Results

- Focused dispatch tests: `3 passed`.
- Full pytest: `1171 passed in 43.33s`.
- Forced Python DQ: shell `6.309335 s`, internal `5.963001099938992 s`.
- Release-native default before policy guard: shell `6.893114 s`, internal
  `6.527206999948248 s`.
- Post-change default: shell `6.16666 s`, internal `5.814741600072011 s`.
- Post-change default is `0.7264539999999995 s` faster than the Release-native
  host DQ default in the same run window.
- Post-change default vs forced Python DQ: master, weight, coverage, low/high
  rejection, and DQ maps are bitwise identical.
- Post-change default vs forced native DQ: the same six maps are bitwise
  identical.
- WBPP black-box compare:
  - shape match: `true`
  - coverage fraction: `0.9892770479074376`
  - robust-fit RMS over fit pixels: `4.25294994505585e-05`
  - robust-fit p99 absolute difference over fit pixels:
    `0.00011365715225056788`
  - shell speedup versus WBPP black-box `1092.541 s`: `177.16900234486738x`

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.
- Doctor artifact: `runs/checkpoints/s2_gate_529_doctor.json`.

## Artifacts

- Summary: `runs/checkpoints/s2_gate_529_native_dq_release_guard_summary.json`.
- External run root:
  `C:\glass_runs\phase2_s2_gate529_native_dq_release\runs_20260623_115631`.
- WBPP compare report:
  `C:\glass_runs\phase2_s2_gate529_native_dq_release\runs_20260623_115631\postchange_default\compare_vs_wbpp_fastintegration.html`.

## Known Limitations

- The generic native host DQ scanner remains available for diagnostics, but is
  not the default because it is slower than the Python fast path on the real
  200-light route.
- The next native DQ promotion should be a specialized count-map scanner that
  respects the resident fast-path assumptions and is promoted only after this
  same A/B benchmark shows a real win.

## Next Step

Return to larger mainline runtime targets: resident registration/warp batching
and light-pipeline overlap, especially consumer wait and H2D/calibration
synchronization.

## Clean-Room Compliance

Compliant. This gate used GLASS-owned code, GLASS-generated artifacts, and the
user-generated WBPP black-box output/timing only. It did not inspect external
implementation source or modify input image directories.
