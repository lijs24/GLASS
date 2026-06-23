# S2-Gate 557 Status: Remaining-Index Set Cursor

- Gate: S2-Gate 557
- Date: 2026-06-23
- Branch: `main`
- Checkpoint summary: `runs/checkpoints/s2_gate_557_remaining_set_summary.json`
- Result: green checkpoint, default resident scheduler remaining-frame maintenance optimized

## Completed

- Replaced the resident calibration loop's mutable `remaining_indices` list with `remaining_index_set`.
- Added a monotonic cursor for sequential fallback ordering.
- Changed `ready_index(...)` to reuse an internal set directly when one is supplied by the resident scheduler.
- Recorded the remaining-index model and ready-index set reuse count in resident artifacts and the light pipeline profile.
- Added focused direct prefetcher and CLI artifact/profile tests.

## Commands Run

- Python syntax check:
  `.venv\Scripts\python.exe -m py_compile src\glass\engine\resident_cuda.py src\glass\engine\resident_light_pipeline_profile.py`
- Focused tests:
  `.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_light_prefetcher_ready_index_selects_completed_candidate tests/test_resident_cuda_run.py::test_light_prefetcher_ready_indices_batch_selects_multiple_completed_candidates tests/test_resident_cuda_run.py::test_cli_resident_cuda_callback_queue_releases_inside_native_batch tests/test_resident_cuda_run.py::test_cli_resident_cuda_callback_queue_clamps_fetch_batch_to_prefetch_depth`
- Resident CUDA/profile tests:
  `.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py tests/test_cuda_resident_stack.py tests/test_resident_light_pipeline_profile.py`
- Full tests:
  `.venv\Scripts\python.exe -m pytest -q`
- Real 200-light postpatch default validation.

## Test Results

- Focused prefetcher/CLI tests: `4 passed in 0.91 s`
- Resident CUDA/profile tests: `157 passed in 9.62 s`
- Full pytest: `1189 passed in 43.94 s`

## Real 200-Light Validation

- Gate556 baseline:
  `C:\glass_runs\phase2_s2_gate556_ready_intersection_light\runs_20260623_171238\default_ready_intersection_light`
- Postpatch default:
  `C:\glass_runs\phase2_s2_gate557_remaining_set\runs_20260623_171847\default_remaining_set`
- Full summary:
  `C:\glass_runs\phase2_s2_gate557_remaining_set\runs_20260623_171847\gate557_remaining_set_summary.json`
- Frame count: 200 lights
- Active frame count after registration masks: 193
- Masked frame count: 7

| Run | Shell s | Resident stage s | Light read/upload/calibrate s | Ready wait s | Remaining model | Set reuse | SHA256 vs Gate556 |
| --- | ---: | ---: | ---: | ---: | --- | ---: | --- |
| Gate556 default baseline | `5.248958` | `4.894711` | `2.414014` | `0.741134` | old list/remove | n/a | baseline |
| Gate557 postpatch default | `5.195597` | `4.838175` | `2.405829` | `0.745701` | `set_with_sequential_cursor` | `200` | identical |

## Numerical Validation

The postpatch default run is SHA256-identical to the Gate556 default baseline for all six output FITS artifacts:

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

- Keep `set_with_sequential_cursor` as the default resident remaining-index model.
- Keep ready-batch/native-queue opt-in gates disabled by default.
- Treat the timing improvement as modest but directionally aligned with larger-frame-count scheduler scaling.

## Known Limitations

- This gate reduces Python bookkeeping, not physical read/H2D readiness.
- The remaining bottleneck is still the read/H2D/calibration pipeline and ready wait.
- This gate does not change registration/warp, LN, rejection, or DQ semantics.

## Clean-Room

- This gate uses GLASS-owned scheduler code, GLASS artifacts, and user-provided FITS data only.
- No external implementation source was inspected or copied.
- The gate does not change calibration formulas, registration, warp, rejection, DQ, integration, accepted frames, or output pixels.
