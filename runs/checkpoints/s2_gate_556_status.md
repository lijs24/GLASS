# S2-Gate 556 Status: Ready-Set Intersection Selector

- Gate: S2-Gate 556
- Date: 2026-06-23
- Branch: `main`
- Checkpoint summary: `runs/checkpoints/s2_gate_556_ready_intersection_summary.json`
- Result: green checkpoint, default ready-first selector complexity reduced, opt-in scheduler paths not promoted

## Completed

- Changed ready-first selection to intersect the current ready set with candidate and pending frame sets.
- Preserved selection ordering: single selection still returns the smallest ready candidate; batch selection still consumes sorted ready candidates up to the batch limit.
- Recorded `prefetch_ready_candidate_probe_mode=ready_set_intersection` in `resident_io_pipeline`, `resident_io_overlap`, and resident light pipeline profile knobs.
- Kept `GLASS_RESIDENT_READY_BATCH_SELECT`, `GLASS_RESIDENT_NATIVE_QUEUE_READ`, and `GLASS_RESIDENT_NATIVE_BATCH_READ` opt-in after same-default p32 A/B showed no stable stage/shell promotion case.
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
- Real 200-light scheduler candidate A/B:
  - default repeat;
  - ready batch opt-in;
  - native queue opt-in;
  - native batch opt-in;
  - native queue inline variants.
- Real 200-light postpatch default validation.

## Test Results

- Focused prefetcher/CLI tests: `4 passed in 0.91 s`
- Resident CUDA/profile tests: `157 passed in 9.60 s`
- Full pytest: `1189 passed in 43.94 s`

## Real 200-Light Validation

- Gate555 default baseline:
  `C:\glass_runs\phase2_s2_gate555_prefetch32_default\runs_20260623_170124\default_prefetch32_postpatch`
- Candidate matrix:
  `C:\glass_runs\phase2_s2_gate556_scheduler_candidates\runs_20260623_170611`
- Candidate combination matrix:
  `C:\glass_runs\phase2_s2_gate556_scheduler_candidates\combos_20260623_170712`
- Final postpatch default:
  `C:\glass_runs\phase2_s2_gate556_ready_intersection_light\runs_20260623_171238\default_ready_intersection_light`
- Full final summary:
  `C:\glass_runs\phase2_s2_gate556_ready_intersection_light\runs_20260623_171238\gate556_ready_intersection_light_summary.json`
- Frame count: 200 lights
- Active frame count after registration masks: 193
- Masked frame count: 7

| Run | Shell s | Resident stage s | Light read/upload/calibrate s | Ready wait s | Selector / backend | SHA256 vs Gate555 |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| Gate555 default baseline | `5.251073` | `4.872004` | `2.417012` | `0.748604` | old ready scan / `native_u16be_raw` | baseline |
| Gate556 postpatch default | `5.248958` | `4.894711` | `2.414014` | `0.741134` | `ready_set_intersection` / `native_u16be_raw` | identical |
| Candidate default repeat | `5.076926` | `4.707955` | `2.429361` | `0.745074` | old ready scan / `native_u16be_raw` | identical |
| Candidate ready-batch opt-in | `5.091549` | `4.734076` | `2.413701` | `0.769515` | ready batch env / `native_u16be_raw` | identical |
| Candidate native queue opt-in | `5.211115` | `4.843345` | `2.402654` | `0.754001` | native queue thread / `native_u16be_raw_queue` | identical |
| Candidate native batch opt-in | `5.246128` | `4.895505` | `2.438893` | `0.754998` | native batch env / `native_u16be_raw_batch` | identical |
| Candidate native queue inline | `5.200585` | `4.835087` | `2.409111` | `0.757858` | native queue inline / `native_u16be_raw_queue` | identical |

## Numerical Validation

The postpatch default run is SHA256-identical to the Gate555 default baseline for all six output FITS artifacts:

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

- Keep ready-set intersection as the default ready-first selector.
- Do not promote ready-batch, native queue, native batch, or inline native queue variants.
- Treat this gate as a scalable scheduler complexity reduction rather than a major 200-light performance win.

## Known Limitations

- The 200-light timing delta is small and dominated by scheduling/IO variance.
- The remaining bottleneck is ready wait plus read/H2D orchestration, not candidate membership scanning alone.
- This gate does not change registration/warp, LN, rejection, or DQ semantics.

## Clean-Room

- This gate uses GLASS-owned scheduler code, GLASS artifacts, and user-provided FITS data only.
- No external implementation source was inspected or copied.
- The gate does not change calibration formulas, registration, warp, rejection, DQ, integration, accepted frames, or output pixels.
