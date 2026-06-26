# S2 Gate 698 Status: Default Native Completion Prestart

- Gate: `S2 Gate 698`
- Date: `2026-06-26`
- Status: `green`
- Branch: `main`
- Objective: make the previously experimental native completion prestart route the guarded default for resident CUDA native completion calibration, with an explicit environment rollback.

## Completed

- Updated `src/glass/engine/resident_cuda.py`.
  - No-env default now records `native_completion_prestart_policy=default_native_completion_calibration`.
  - `GLASS_RESIDENT_NATIVE_COMPLETION_PRESTART=1` records `env_enabled`.
  - `GLASS_RESIDENT_NATIVE_COMPLETION_PRESTART=0` records `env_disabled` and falls back to the ordinary native completion queue.
  - Prestart remains active only when native completion calibration is already enabled and native prestart methods are available.
- Added resident IO artifact field:
  - `native_completion_prestart_policy`
- Updated resident CUDA tests in `tests/test_resident_cuda_run.py`.
  - Default prestart path.
  - Explicit env enable path.
  - Explicit env disable rollback path.
  - Existing completion-calibration and v4 preset expectations.
- Updated `docs/phase2_algorithm_hardening.md`.
- Updated `docs/algorithm_sources.md`.

## Commands Run

- Focused prestart tests:
  - `.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py -k "native_completion_prestart"`
- Focused native completion tests:
  - `.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py -k "native_completion"`
- Focused stale assertion regression:
  - `.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_u16_completion_calibration_is_opt_in`
- Full test suite:
  - `.venv\Scripts\python.exe -m pytest -q`
- Real 200-light candidate:
  - `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate698_default_prestart\runs_20260627_090000\default_prestart_candidate --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
- Real mainline audit:
  - `.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate698_default_prestart\runs_20260627_090000\default_prestart_candidate --out C:\glass_runs\phase2_s2_gate698_default_prestart\gate698_default_prestart_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate698_default_prestart\gate698_default_prestart_mainline_audit.md`
- Real A/B:
  - `.venv\Scripts\glass.exe phase2-mainline-ab --baseline-run C:\glass_runs\phase2_s2_gate697_bounds_skip\runs_20260627_080000\bounds_skip_candidate --candidate-run C:\glass_runs\phase2_s2_gate698_default_prestart\runs_20260627_090000\default_prestart_candidate --out C:\glass_runs\phase2_s2_gate698_default_prestart\gate698_default_prestart_vs_gate697_ab.json --markdown C:\glass_runs\phase2_s2_gate698_default_prestart\gate698_default_prestart_vs_gate697_ab.md`
  - `.venv\Scripts\glass.exe phase2-mainline-ab --baseline-run C:\glass_runs\phase2_s2_gate696_native_completion_prestart\runs_20260627_070000\prestart_candidate --candidate-run C:\glass_runs\phase2_s2_gate698_default_prestart\runs_20260627_090000\default_prestart_candidate --out C:\glass_runs\phase2_s2_gate698_default_prestart\gate698_default_prestart_vs_gate696_ab.json --markdown C:\glass_runs\phase2_s2_gate698_default_prestart\gate698_default_prestart_vs_gate696_ab.md`

## Test Results

- Focused prestart tests: `3 passed, 138 deselected in 2.05 s`.
- Focused native completion tests: `6 passed, 135 deselected in 2.90 s`.
- Focused stale assertion regression: `1 passed in 1.24 s`.
- Full pytest: `1443 passed in 70.03 s`.
- Note: the first full pytest after the policy change found two stale test assumptions about the old non-prestart default. They were fixed before continuing to real data.

## CUDA

- CUDA available: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Multiprocessors: `188`
- Driver version: `596.21`

## Real 200-Light Evidence

- Candidate run:
  - `C:\glass_runs\phase2_s2_gate698_default_prestart\runs_20260627_090000\default_prestart_candidate`
- Candidate output size:
  - `56` files, about `1.295 GB`
- Mainline audit:
  - `C:\glass_runs\phase2_s2_gate698_default_prestart\gate698_default_prestart_mainline_audit.json`
  - Status: passed.
  - Input lights: `200`.
  - Active/masked: `193 / 7`.
- A/B vs Gate697:
  - `C:\glass_runs\phase2_s2_gate698_default_prestart\gate698_default_prestart_vs_gate697_ab.json`
  - Status: passed.
  - Elapsed ratio: `0.9438602383093226`.
  - Integration map hashes: all `6 / 6` matched.
  - Component ratio failures: `0`.
  - `resident_light_read_upload_calibrate`: `3.6238525999942794 s -> 3.0857310999417678 s`, ratio `0.851505687606234`.
  - `resident_integration`: `3.2714636999880895 s -> 3.326978600001894 s`, ratio `1.016969437873942`.
- A/B vs Gate696:
  - `C:\glass_runs\phase2_s2_gate698_default_prestart\gate698_default_prestart_vs_gate696_ab.json`
  - Status: passed.
  - Elapsed ratio: `0.9819094296357141`.
  - Integration map hashes: all `6 / 6` matched.
  - Component ratio failures: `0`.
  - `resident_light_read_upload_calibrate`: `3.498033900046721 s -> 3.0857310999417678 s`, ratio `0.882132989020076`.
  - `resident_integration`: `3.262477900017984 s -> 3.326978600001894 s`, ratio `1.0197704634209335`.

## Candidate Timing

- `resident_light_read_upload_calibrate`: `3.0857310999417678 s`
- `resident_registration_warp`: `0.26680679921992123 s`
- `resident_local_normalization`: `0.37221059994772077 s`
- `resident_integration`: `3.326978600001894 s`
- `resident_output_write`: `0.2952664999756962 s`
- Native file-read cumulative time:
  - `light_native_path_calibration_file_read`: `29.480449400000005 s`
  - `light_read_supply_overlap_saved`: `26.470344100058238 s`

## Interpretation

- This gate is green because the default runtime behavior changed, full tests passed, the real 200-light route passed mainline audit, and all six tracked integration FITS outputs are bit-identical against Gate696 and Gate697.
- The change is a practical scheduling improvement for the current resident CUDA default path, not a new scientific algorithm.
- The main remaining bottleneck is still the read-supply/native completion file-read and orchestration envelope, followed by resident integration.

## Known Limitations

- Single-run timing remains sensitive to external storage and OS cache state.
- The native completion prestart queue overlaps read supply with master-cache work but does not reduce the underlying file-read cumulative time.
- This gate does not address resident registration/warp batching, cooperative/segmented integration, or all-GPU star catalog orchestration.

## Next Step

- Gate699 should return to a larger mainline target:
  - resident registration/warp batch orchestration reduction, or
  - a cooperative/segmented resident winsorized reducer prototype, or
  - a real I/O/upload pipeline improvement that reduces native file-read or host/device orchestration on the 200-light benchmark.

## Clean-Room

- Clean-room constraints respected.
- No PixInsight/WBPP/PJSR source was read or used.
- Only GLASS source, tests, local run artifacts, and generated benchmark outputs were inspected.
