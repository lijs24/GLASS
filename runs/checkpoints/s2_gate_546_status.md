# S2-Gate 546 Status: Native Queue Inline-Drain Probe

## Gate

- Gate: S2-Gate 546
- Status: green
- Theme: resident CUDA I/O/completion scheduling
- Checkpoint summary: `runs/checkpoints/s2_gate_546_inline_queue_drain_summary.json`

## Completed

- Added explicit `GLASS_RESIDENT_NATIVE_QUEUE_DRAIN_MODE=inline`.
- Kept `thread` as the queue opt-in default drain mode.
- Shared native queue completion materialization between thread and inline
  drain paths.
- Recorded `native_queue_read_drain_mode`,
  `native_queue_read_inline_wait_count`, and
  `native_queue_read_thread_wait_count` in resident artifacts and resident
  light pipeline profiles.
- Added tests proving inline mode is explicit and thread mode remains default.

## Commands Run

- Focused tests:
  `.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_u16_queue_read_is_opt_in tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_u16_queue_read_default_drain_is_thread tests/test_resident_cuda_run.py::test_cli_resident_cuda_default_fits_read_mode_is_guarded_auto`
- Full tests:
  `.venv\Scripts\python.exe -m pytest -q`
- Inline 200-light run:
  `GLASS_RESIDENT_NATIVE_QUEUE_READ=1 GLASS_RESIDENT_NATIVE_QUEUE_DRAIN_MODE=inline glass run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate546_inline_queue_drain\runs_20260623_160000\native_queue_inline_release --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- Thread-drain 200-light run:
  `GLASS_RESIDENT_NATIVE_QUEUE_READ=1 glass run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate546_inline_queue_drain\runs_20260623_160000\native_queue_thread_release ...`

## Test Results

- Focused tests: `3 passed in 1.16s`
- Full pytest: `1184 passed in 44.47s`

## CUDA

- CUDA available: yes
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver: `596.21`
- Native backend: available
- Raw FITS read queue binding: available

## Real 200-Light Evidence

- Thread-drain queue:
  `C:\glass_runs\phase2_s2_gate546_inline_queue_drain\runs_20260623_160000\native_queue_thread_release`
- Inline-drain queue:
  `C:\glass_runs\phase2_s2_gate546_inline_queue_drain\runs_20260623_160000\native_queue_inline_release`
- Thread shell/internal elapsed:
  `5.500654 s` / `5.139208300039172 s`
- Inline shell/internal elapsed:
  `5.56227 s` / `5.198796700045932 s`
- Inline versus thread:
  `0.9889225082565212x`, `0.061615999999999893 s` slower
- Thread versus recorded WBPP black-box elapsed `1092.541 s`:
  `198.62020043434833x`
- Inline versus recorded WBPP black-box elapsed:
  `196.41998680394875x`

## Timing Details

- Thread drain:
  backend `native_u16be_raw_queue: 200`,
  queue submit/complete/workers `200 / 200 / 16`,
  queue cumulative native read `25.162665299999983 s`,
  thread wait count `206`,
  inline wait count `0`,
  light read/upload/calibrate `2.5636506999726407 s`,
  ready wait `1.163724199985154 s`,
  out-of-order frames `68`,
  registration/warp `0.254920499806758 s`,
  integration `0.3027371999924071 s`.
- Inline drain:
  backend `native_u16be_raw_queue: 200`,
  queue submit/complete/workers `200 / 200 / 16`,
  queue cumulative native read `25.23642249999999 s`,
  inline wait count `201`,
  thread wait count `0`,
  light read/upload/calibrate `2.561797199945431 s`,
  ready wait `1.1658721001003869 s`,
  out-of-order frames `155`,
  registration/warp `0.25686300004599616 s`,
  integration `0.3037078999914229 s`.

## Numerical Validation

- Inline and thread queue runs are SHA256-identical for master, weight map,
  coverage map, low/high rejection maps, and DQ map.
- Inline also matches Gate545 fresh default hashes.
- Thread-vs-inline hash report:
  `C:\glass_runs\phase2_s2_gate546_inline_queue_drain\hash_compare_thread_vs_inline.json`
- Gate545-default hash report:
  `C:\glass_runs\phase2_s2_gate546_inline_queue_drain\hash_compare_gate545_default.json`
- WBPP comparison is inherited through bitwise output identity:
  RMS `0.0004279821839256963`, p99 abs diff
  `0.0001313822576776147`, robust-fit RMS
  `4.2529498303511286e-05`, coverage fraction
  `0.9892770479074376`, compared pixels `56997300`.

## Decision

- Do not promote inline drain.
- Queue opt-in default remains `thread`.
- Reason: inline is bitwise-correct but slower in the same 200-light session.

## Known Limitations

- Inline drain is an explicit experiment, not a promoted optimization.
- The queue path itself remains opt-in behind
  `GLASS_RESIDENT_NATIVE_QUEUE_READ=1`.
- The next meaningful target is not another Python drain rearrangement, but a
  native read-to-calibration wave coordinator that avoids Python completion
  materialization.

## Clean-Room Compliance

- Compliant.
- This gate uses GLASS code, user image data, GLASS artifacts, and
  user-generated timing/reference outputs.
- It does not inspect external implementation source, does not modify raw input
  directories, and does not change calibration, registration, warp, rejection,
  DQ, integration, accepted frames, or output pixels.
