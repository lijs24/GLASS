# S2-Gate 707 Status: Native Completion H2D Timing Policy

## Gate

S2-Gate 707: make native-completion H2D elapsed telemetry an explicit policy and
validate whether disabling elapsed sampling should become the default.

## Completed Content

- Added native policy key `native_completion_collect_h2d_elapsed` for the
  resident native-completion calibration paths.
- Kept detailed H2D elapsed collection enabled by default in the resident path
  and direct native API.
- Added resident env control:
  - unset: `default_enabled`;
  - `GLASS_RESIDENT_NATIVE_COMPLETION_H2D_TIMING=1`: `env_enabled`;
  - `GLASS_RESIDENT_NATIVE_COMPLETION_H2D_TIMING=0`: `env_disabled`;
  - invalid non-empty values: `env_invalid_disabled`.
- Added resident artifact/profile fields:
  `native_completion_h2d_elapsed_collection_policy`,
  `native_completion_h2d_elapsed_collection_enabled`,
  `native_completion_h2d_elapsed_sample_count`, and
  `native_completion_h2d_elapsed_skipped_count`.
- Preserved CUDA event query/synchronize safety for pinned-buffer reuse when
  elapsed sampling is disabled; only `cudaEventElapsedTime` telemetry sampling
  is skipped.
- Updated documentation in:
  - `docs/phase2_algorithm_hardening.md`;
  - `docs/integration_model.md`;
  - `docs/known_limitations.md`;
  - `docs/validation.md`;
  - `docs/algorithm_sources.md`.

## Commands Run

- Native rebuild:
  `cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .venv\Scripts\cmake.exe --build build --config Release --target _glass_cuda_native -j 8'`
- Focused tests:
  `.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_light_pipeline_profile.py tests/test_cuda_resident_stack.py -k "native_completion or prestart" tests/test_resident_cuda_run.py -k "native_completion"`
- Ruff:
  `.\.venv\Scripts\python.exe -m ruff check src/glass/engine/resident_cuda.py src/glass/engine/resident_light_pipeline_profile.py tests/test_resident_light_pipeline_profile.py tests/test_resident_cuda_run.py`
- Full tests:
  `.\.venv\Scripts\python.exe -m pytest -q`
- Real 200-light mainline audit:
  `gate707_default_mainline_audit.json`
- Real 200-light A/B against Gate705:
  `gate707_default_vs_gate705_phase2_mainline_ab.json`
- Real 200-light disabled-vs-default A/B:
  `gate707_disabled_vs_default_phase2_mainline_ab.json`
- Real 200-light resident regression against Gate705:
  `gate707_default_vs_gate705_regression.json`
- CUDA device probe through `glass_cuda`.

## Test Results

- Native rebuild: passed.
- Focused tests: `7 passed, 220 deselected in 2.40s`.
- Ruff: passed.
- Full pytest: `1452 passed in 73.14s`.

## Real 200-Light Validation

Run root:

`C:\glass_runs\phase2_s2_gate707_h2d_timing_policy\runs_20260626_130000`

Default-enabled run:

`C:\glass_runs\phase2_s2_gate707_h2d_timing_policy\runs_20260626_130000\default_h2d_timing_enabled`

Gate705 baseline:

`C:\glass_runs\phase2_s2_gate705_completion_wavefill\runs_20260626_120000\default_promoted_multi1000`

Key results:

| Metric | Gate705 | Gate707 default-enabled | Disabled candidate |
| --- | ---: | ---: | ---: |
| Total elapsed | `10.727156800101511 s` | `10.697529399883933 s` | `11.084137099911459 s` |
| Light read/upload/calibrate | `2.982370199984871 s` | `2.9152304000454023 s` | `3.044296000036411 s` |
| Resident integration | `2.627562499954365 s` | `2.589988899999298 s` | `2.6099305000388995 s` |
| H2D elapsed policy | not recorded | `default_enabled` | disabled-candidate artifact |
| H2D elapsed samples/skips | not recorded | `200 / 0` | `0 / 200` |

Phase 2 mainline A/B versus Gate705:

- Passed: `true`.
- Elapsed ratio: `0.997238093861246`.
- Failed checks: `[]`.
- Hash mismatches: `0`.
- Missing tracked maps: `0`.
- Component ratios: all passed.

Disabled candidate versus Gate707 default:

- Passed output contracts: `true`.
- Elapsed ratio: `1.0361399053534472`.
- `light_read_upload_calibrate` ratio: `1.0442728643296937`.
- Conclusion: disabling H2D elapsed collection is not promoted. It remains an
  explicit diagnostic opt-out through
  `GLASS_RESIDENT_NATIVE_COMPLETION_H2D_TIMING=0`.

## CUDA Availability

CUDA available: yes.

Detected device:

- Name: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver: `596.21`
- Native backend: `true`

## Known Limitations

- This is telemetry and policy hardening, not a science algorithm change.
- The disabled telemetry branch did not improve the current real 200-light
  workload and should not be treated as a default optimization.
- Remaining substantive targets are still resident read/H2D/calibration overlap,
  registration/warp batching, and larger reducer work.
- Single-run timing remains affected by external storage/cache variability.

## Next Step

Return to a substantive mainline gate: improve actual resident calibration
read/H2D overlap, resident registration/warp batching, or resident integration
kernel structure under the existing Phase 2 mainline A/B guard.

## Clean-Room Compliance

Compliant. This gate used GLASS-owned code, GLASS tests, and user-owned
benchmark artifacts only. No external or proprietary implementation source was
inspected, copied, summarized, or reworked. Original image directories remained
read-only.
