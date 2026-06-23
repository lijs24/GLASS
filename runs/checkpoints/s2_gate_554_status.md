# S2-Gate 554 Status: Opt-In Ready-First Batch Selector

- Gate: S2-Gate 554
- Date: 2026-06-23
- Branch: `main`
- Checkpoint summary: `runs/checkpoints/s2_gate_554_ready_batch_select_summary.json`
- Result: green checkpoint, opt-in scheduler hook retained, default path unchanged

## Completed

- Added opt-in `GLASS_RESIDENT_READY_BATCH_SELECT=1` for the default callback-release resident prefetch path.
- Added `_LightPrefetcher.ready_indices_batch(...)` to select up to the calibration batch limit from currently ready candidate frames.
- Preserved the no-env default behavior: single ready-index selection remains active unless the environment variable is set.
- Recorded batch-selection policy and counters in `resident_io_pipeline`, `resident_io_overlap`, and resident light pipeline profile knobs.
- Added focused tests for batch selection, opt-in artifact counters, and disabled-by-default counters.

## Commands Run

- Python syntax check:
  `.venv\Scripts\python.exe -m py_compile src\glass\engine\resident_cuda.py src\glass\engine\resident_light_pipeline_profile.py`
- Focused ready-index/batch/default tests:
  `.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_light_prefetcher_ready_index_selects_completed_candidate tests/test_resident_cuda_run.py::test_light_prefetcher_ready_indices_batch_selects_multiple_completed_candidates tests/test_resident_cuda_run.py::test_cli_resident_cuda_callback_queue_releases_inside_native_batch tests/test_resident_cuda_run.py::test_cli_resident_cuda_callback_queue_clamps_fetch_batch_to_prefetch_depth`
- Resident CUDA local tests:
  `.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py tests/test_cuda_resident_stack.py`
- Full tests:
  `.venv\Scripts\python.exe -m pytest -q`
- Real 200-light validation:
  - default no-env resident CUDA run;
  - opt-in run with `GLASS_RESIDENT_READY_BATCH_SELECT=1`;
  - SHA256 comparison against Gate553 default baseline.

## Test Results

- Focused ready-index/batch/default tests: `4 passed in 0.91 s`
- Resident CUDA local tests: `154 passed in 9.68 s`
- Full pytest: `1189 passed in 44.03 s`

## Real 200-Light Validation

- Run root:
  `C:\glass_runs\phase2_s2_gate554_ready_batch_select\final_20260623_165105`
- Gate553 baseline:
  `C:\glass_runs\phase2_s2_gate553_wave_fill_matrix\runs_20260623_163435\default_release_postpatch`
- Default no-env run:
  `C:\glass_runs\phase2_s2_gate554_ready_batch_select\final_20260623_165105\default_noenv`
- Opt-in run:
  `C:\glass_runs\phase2_s2_gate554_ready_batch_select\final_20260623_165105\ready_batch_select_optin`
- Full metrics:
  `C:\glass_runs\phase2_s2_gate554_ready_batch_select\final_20260623_165105\gate554_final_metrics_summary.json`
- Frame count: 200 lights
- Active frame count after registration masks: 193
- Masked frames: `F000160`, `F000213`, `F000214`, `F000215`, `F000216`, `F000217`, `F000218`

| Run | Shell s | Resident stage s | Light read/upload/calibrate s | Registration/warp s | Batch policy | Batch selected |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| Gate553 default baseline | `5.434383` | `5.063190` | `2.556746` | `0.257933` | n/a | n/a |
| Gate554 default no-env | `5.429829` | `5.031444` | `2.588569` | `0.256978` | `env_disabled_default` | `0` |
| Gate554 opt-in | `5.306247` | `4.938021` | `2.554957` | `0.253479` | `env_enabled` | `200` |

## Numerical Validation

Both Gate554 runs are SHA256-identical to the Gate553 default baseline for all six output FITS artifacts:

- `resident_master_H.fits`: `8BC069CE6858AB5E065B5D9AF297C35C36D4240C13980546E43CFB480115E110`
- `resident_weight_map_H.fits`: `5862111EE6F527A40671AC13F1FAA43F037C90271F872F27AF4ACF17040FBFE8`
- `resident_coverage_map_H.fits`: `B87517BE794A3B4BDCFF0D8536EE0188DA6AFA54ED2BE818BD911BA6CF1BE1B3`
- `resident_low_rejection_map_H.fits`: `F1181E0CE52A7FF77B988AFAF8A8911A1BEAF94DF54B25B0AA51014CB0D66E23`
- `resident_high_rejection_map_H.fits`: `ADB66C931C5A48D6E0D7F5C2FCBCC58481420AD4912304843A3802089050C805`
- `resident_dq_map_H.fits`: `934F661119CE18BBCAC1D369488AED4D959669C6EF614D6076D74BE06E69CCFB`

Resident StackEngine surface contract and DQ pixel closure passed.

## CUDA

- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB

## Decision

- The batch selector remains opt-in behind `GLASS_RESIDENT_READY_BATCH_SELECT=1`.
- The default resident path is not changed or promoted.
- The real run's shell/stage timing is slightly faster for opt-in, but the light-stage delta versus Gate553 is only `-0.001789 s`, so the result is treated as safe instrumentation rather than a decisive performance win.

## Known Limitations

- Ready-queue wait remains about `1.16 s`; batch selection alone does not remove the underlying wait/orchestration cost.
- Shell timings are sensitive to warm-cache and output-write variation; the light read/upload/calibrate stage is the main optimization target.
- This gate does not address resident registration/warp, LN, or rejection math.

## Next Step

- Continue the mainline with a real optimization that reduces ready-queue wait or Python/native orchestration while preserving bitwise output identity and the current default fast path.

## Clean-Room

- This gate uses GLASS-owned scheduler code, GLASS artifacts, and user-provided FITS data only.
- No external implementation source was inspected or copied.
- The gate does not change calibration formulas, registration, warp, rejection, DQ, integration, accepted frames, or output pixels.
