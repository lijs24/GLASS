# S2-Gate 530 Status: Native Count-Map DQ Fast Path

## Gate

S2-Gate 530: implement and validate a native resident DQ fast path for the
verified count-map case in the real 200-light pipeline.

## Completed

- Added `_glass_cuda_native.resident_dq_map_count_maps_i16`.
- Added `glass_cuda.resident_dq_map_count_maps_i16*` wrappers and preference
  handling.
- Routed `_resident_dq_map` to the native count-map path only when all fast-path
  preconditions are true:
  - finite count maps;
  - nonnegative count maps;
  - valid master/weight diagnostics;
  - `dq_dtype=np.int16`.
- Kept the generic strict native DQ scanner and Python fallback available.
- Added focused parity, preference, and dispatch tests.
- Built the local native extension in Release mode for validation.
- Ran two real 200-light forced-Python/native-count A/B pairs.
- Ran a GLASS-vs-WBPP black-box compare for the fastest native-count repeat.

## Commands

- `cmake -S . -B build-release-native -G Ninja -DGLASS_BUILD_PYTHON_CUDA=ON -DGLASS_BUILD_CUDA=OFF -DCMAKE_BUILD_TYPE=Release ...`
- `cmake --build build-release-native --target _glass_cuda_native -j 8`
- `python -m pytest -q tests/test_resident_cuda_run.py::test_resident_dq_map_count_maps_native_matches_fast_python_when_available tests/test_resident_cuda_run.py::test_resident_dq_map_count_maps_native_preference_honors_env tests/test_resident_cuda_run.py::test_resident_dq_map_dispatch_uses_native_count_maps_fast_path tests/test_resident_cuda_run.py::test_resident_dq_map_valid_master_nonnegative_count_fast_path_matches_strict`
- Real 200-light A/B under `C:\glass_runs\phase2_s2_gate530_native_count_dq\runs_20260623_120726`
- `glass compare --glass ...\native_count_r2\integration\resident_master_H.fits --reference ...\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --min-coverage 190 --ignore-border-px 128`
- `glass doctor --json runs\checkpoints\s2_gate_530_doctor.json --allow-cpu-only`

## Results

- Focused tests before native rebuild: `3 passed, 1 skipped`.
- Focused tests after native rebuild: `4 passed`.
- Full pytest: `1174 passed in 43.19s`.
- First forced-Python DQ run: shell `6.273116 s`, internal
  `5.905352900037542 s`.
- First native count-map DQ run: shell `6.091866 s`, internal
  `5.724182699981611 s`.
- Repeat forced-Python DQ run: shell `6.33212 s`, internal
  `5.973562000028323 s`.
- Repeat native count-map DQ run: shell `6.027409 s`, internal
  `5.67795159999514 s`.
- Two-run average:
  - Python shell: `6.302618 s`
  - native shell: `6.059637499999999 s`
  - average shell gain: `0.2429805000000007 s`
  - native shell ratio: `0.9614476872943909`
- Native artifacts record `native_host_fast_count_maps`.
- A post-field validation run records
  `dq_map_stats_backend=native_host_fast_count_maps`,
  `dq_map_stats_profile=resident_valid_master_nonnegative_count_map_native_i16`,
  and `dq_map_stats_native_method=resident_dq_map_count_maps_i16`.
- Native count-map DQ and forced Python DQ outputs are bitwise identical for:
  master, weight, coverage, low rejection, high rejection, and DQ maps.
- WBPP black-box compare for `native_count_r2`:
  - shape match: `true`
  - coverage fraction: `0.9892770479074376`
  - robust-fit RMS over fit pixels: `4.25294994505585e-05`
  - robust-fit p99 absolute difference over fit pixels:
    `0.00011365715225056788`
  - shell speedup versus WBPP black-box `1092.541 s`: `181.26213104171296x`

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.
- Doctor artifact: `runs/checkpoints/s2_gate_530_doctor.json`.

## Artifacts

- Summary: `runs/checkpoints/s2_gate_530_native_count_dq_summary.json`.
- External run root:
  `C:\glass_runs\phase2_s2_gate530_native_count_dq\runs_20260623_120726`.
- WBPP compare report:
  `C:\glass_runs\phase2_s2_gate530_native_count_dq\runs_20260623_120726\native_count_r2\compare_vs_wbpp_fastintegration.html`.

## Known Limitations

- This is a host-native DQ builder, not a fully GPU-resident DQ reduction.
- The improvement is modest because the current full route is already near six
  seconds; larger remaining targets are resident registration/warp and
  light-pipeline overlap.
- The native fast path is intentionally limited to the verified resident
  count-map preconditions; arbitrary arrays still use strict fallback behavior.

## Next Step

Move to larger runtime components: resident registration/warp batching and
light-pipeline read/H2D overlap.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned DQ flag semantics, GLASS-generated
artifacts, and user-generated WBPP black-box output/timing only. It does not
inspect external implementation source or modify input image directories.
