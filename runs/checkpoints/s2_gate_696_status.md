# S2 Gate 696 Status: Native Completion Read-Prestart

- Gate: `S2 Gate 696`
- Date: `2026-06-26`
- Status: `green`
- Branch: `main`
- Objective: Phase 2 mainline progress: reduce I/O + upload + calibration wall time by starting resident native FITS raw reads before master load/upload, while keeping output maps bitwise stable.

## Completed

- Added an opt-in resident native completion prestart queue in `cpp/src/native_bindings.cpp`.
  - `begin_fits_u16be_bzero_paths_completion_queue_read_timed`
  - `finish_fits_u16be_bzero_paths_completion_queue_calibration_timed`
  - `cancel_fits_u16be_bzero_paths_completion_queue_read`
- Added Python wrappers in `src/glass_cuda.py`.
- Wired pipeline opt-in through `GLASS_RESIDENT_NATIVE_COMPLETION_PRESTART=1`.
- Added artifact fields recording prestart support/request/enablement, frame counts, timing window, cancellation count, mismatch count, and mode strings.
- Added CUDA unit coverage and resident pipeline smoke coverage.

## Commands Run

- Native build:
  - `cmd /c VsDevCmd.bat ... && .venv\Scripts\cmake.exe --build build --config Release --target _glass_cuda_native`
- Focused tests:
  - `.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_prestarts_u16be_completion_read_before_master_upload tests\test_resident_cuda_run.py::test_cli_resident_cuda_native_completion_prestart_is_env_opt_in`
  - `.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_calibrates_u16be_paths_completion_queue_on_gpu_like_cpu tests\test_resident_cuda_run.py::test_cli_resident_cuda_native_u16_completion_calibration_is_opt_in tests\test_resident_cuda_run.py::test_cli_resident_cuda_native_completion_runtime_preset_is_cli_opt_in`
- Real 200-light candidate:
  - `GLASS_RESIDENT_NATIVE_COMPLETION_PRESTART=1`
  - `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate696_native_completion_prestart\runs_20260627_070000\prestart_candidate --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
- Real mainline audit:
  - `.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate696_native_completion_prestart\runs_20260627_070000\prestart_candidate --out C:\glass_runs\phase2_s2_gate696_native_completion_prestart\gate696_prestart_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate696_native_completion_prestart\gate696_prestart_mainline_audit.md`
- Real A/B:
  - `.venv\Scripts\glass.exe phase2-mainline-ab --baseline-run C:\glass_runs\phase2_s2_gate694_no_reject_initial_sum\runs_20260627_050000\no_reject_initial_sum_candidate --candidate-run C:\glass_runs\phase2_s2_gate696_native_completion_prestart\runs_20260627_070000\prestart_candidate --out C:\glass_runs\phase2_s2_gate696_native_completion_prestart\gate696_prestart_vs_gate694_ab.json --markdown C:\glass_runs\phase2_s2_gate696_native_completion_prestart\gate696_prestart_vs_gate694_ab.md`
  - `.venv\Scripts\glass.exe phase2-mainline-ab --baseline-run C:\glass_runs\phase2_s2_gate695_index_select\runs_20260627_063000\default_after_index_code --candidate-run C:\glass_runs\phase2_s2_gate696_native_completion_prestart\runs_20260627_070000\prestart_candidate --out C:\glass_runs\phase2_s2_gate696_native_completion_prestart\gate696_prestart_vs_gate695_default_ab.json --markdown C:\glass_runs\phase2_s2_gate696_native_completion_prestart\gate696_prestart_vs_gate695_default_ab.md`
- Full test suite:
  - `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Native build: passed.
- Focused CUDA/prestart tests: `2 passed`.
- Native completion regression tests: `3 passed`.
- Full pytest: `1441 passed in 67.02s`.

## CUDA

- CUDA available: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Multiprocessors: `188`

## Real 200-Light Evidence

- Candidate run:
  - `C:\glass_runs\phase2_s2_gate696_native_completion_prestart\runs_20260627_070000\prestart_candidate`
- Mainline audit:
  - `C:\glass_runs\phase2_s2_gate696_native_completion_prestart\gate696_prestart_mainline_audit.json`
  - Status: passed
  - Input lights: `200`
  - Active/masked: `193 / 7`
- A/B vs Gate694:
  - `C:\glass_runs\phase2_s2_gate696_native_completion_prestart\gate696_prestart_vs_gate694_ab.json`
  - Status: passed
  - Elapsed ratio: `1.0529457490571623`
  - Hash mismatches/missing maps: `0 / 0`
  - Worst component ratio: `1.1063440276413337`
- A/B vs Gate695 default-after-code:
  - `C:\glass_runs\phase2_s2_gate696_native_completion_prestart\gate696_prestart_vs_gate695_default_ab.json`
  - Status: passed
  - Elapsed ratio: `1.0017510106683878`
  - Hash mismatches/missing maps: `0 / 0`
  - `light_read_upload_calibrate`: `3.676609499962069 s -> 3.498033900046721 s`

## Prestart Observations

- Prestart enabled: `true`
- Prestart frame count: `200`
- Prestart cancel count: `0`
- Prestart batch index mismatch count: `0`
- Begin-to-finish-start window: `0.4400172 s`
- Prestart total wall: `2.2024434 s`
- Calibration batch mode: `fits_u16be_bzero_native_completion_prestart_calibration_batch`
- Timing model: `native_completion_prestarted_queue_read_overlap_then_h2d_gpu_decode_calibration`
- Native read cumulative: `30.603285099999994 s`
- Native file-read cumulative: `30.54319320000001 s`

## Known Limitations

- Prestart is opt-in through `GLASS_RESIDENT_NATIVE_COMPLETION_PRESTART=1`; it is not promoted to the default preset.
- The real run improved the light read/upload/calibration component versus Gate695 default, but total elapsed was essentially neutral because other stages varied.
- The implementation intentionally preserves the existing native completion path as the default and carries duplicated C++ scheduling logic; a later refactor should share queue-drain code.
- This gate does not solve the larger resident registration/warp and integration kernel ceilings.

## Next Step

- Gate697 should return to resident GPU stage completeness and performance:
  - either resident registration descriptor/scoring batching to reduce Python orchestration and host/device traffic,
  - or a more substantial cooperative/segmented resident winsorized reducer rather than another small scratch/index variant.

## Clean-Room

- Clean-room constraints respected.
- No PixInsight/WBPP/PJSR source was read or used.
- Only GLASS source, tests, local run artifacts, and generated benchmark outputs were inspected.
