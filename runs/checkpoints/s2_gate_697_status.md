# S2 Gate 697 Status: Hardened Rejection-Candidate Bounds Skip

- Gate: `S2 Gate 697`
- Date: `2026-06-26`
- Status: `green`
- Branch: `main`
- Objective: continue Phase 2 mainline integration hardening by adding an exact resident CUDA reducer branch that can skip rejection-candidate counting when per-pixel sample min/max proves there are no low/high rejection candidates.

## Completed

- Updated the bounded resident hardened winsorized CUDA kernel in `cpp/cuda/integration_kernels.cu`.
  - Records finite sample `min/max` during the first per-pixel sample collection pass.
  - Skips the rejection-count scan when `sample_min >= low_threshold` and `sample_max <= high_threshold`.
  - Keeps strict `<` / `>` rejection semantics and existing no-rejection initial accumulation.
- Updated the over-512 radix-select prototype to reuse its first finite-sample pass for no-rejection accumulation.
- Added native profile fields in `cpp/src/native_bindings.cpp`.
  - `rejection_candidate_bounds_fast_path_enabled`
  - `rejection_candidate_bounds_fast_path_model`
  - `rejection_candidate_bounds_fast_path_counter`
- Extended CUDA parity tests in `tests/test_cuda_resident_stack.py`.
- Updated `docs/algorithm_sources.md`.
- Updated `docs/phase2_algorithm_hardening.md`.

## Commands Run

- Native build:
  - `cmd /c VsDevCmd.bat ... && .venv\Scripts\cmake.exe --build build --config Release --target _glass_cuda_native`
- Focused tests:
  - `.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_no_reject_initial_sum_matches_cpu tests\test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_radix_select_over_512_matches_cpu tests\test_resident_cuda_run.py::test_cli_resident_cuda_hardened_winsorized_matches_cpu_baseline`
- Real 200-light candidate:
  - `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate697_bounds_skip\runs_20260627_080000\bounds_skip_candidate --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
- Real mainline audit:
  - `.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate697_bounds_skip\runs_20260627_080000\bounds_skip_candidate --out C:\glass_runs\phase2_s2_gate697_bounds_skip\gate697_bounds_skip_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate697_bounds_skip\gate697_bounds_skip_mainline_audit.md`
- Real A/B:
  - `.venv\Scripts\glass.exe phase2-mainline-ab --baseline-run C:\glass_runs\phase2_s2_gate695_index_select\runs_20260627_063000\default_after_index_code --candidate-run C:\glass_runs\phase2_s2_gate697_bounds_skip\runs_20260627_080000\bounds_skip_candidate --out C:\glass_runs\phase2_s2_gate697_bounds_skip\gate697_bounds_skip_vs_gate695_default_ab.json --markdown C:\glass_runs\phase2_s2_gate697_bounds_skip\gate697_bounds_skip_vs_gate695_default_ab.md`
  - `.venv\Scripts\glass.exe phase2-mainline-ab --baseline-run C:\glass_runs\phase2_s2_gate696_native_completion_prestart\runs_20260627_070000\prestart_candidate --candidate-run C:\glass_runs\phase2_s2_gate697_bounds_skip\runs_20260627_080000\bounds_skip_candidate --out C:\glass_runs\phase2_s2_gate697_bounds_skip\gate697_bounds_skip_vs_gate696_prestart_ab.json --markdown C:\glass_runs\phase2_s2_gate697_bounds_skip\gate697_bounds_skip_vs_gate696_prestart_ab.md`
  - `.venv\Scripts\glass.exe phase2-mainline-ab --baseline-run C:\glass_runs\phase2_s2_gate694_no_reject_initial_sum\runs_20260627_050000\no_reject_initial_sum_candidate --candidate-run C:\glass_runs\phase2_s2_gate697_bounds_skip\runs_20260627_080000\bounds_skip_candidate --out C:\glass_runs\phase2_s2_gate697_bounds_skip\gate697_bounds_skip_vs_gate694_ab.json --markdown C:\glass_runs\phase2_s2_gate697_bounds_skip\gate697_bounds_skip_vs_gate694_ab.md`
- Full test suite:
  - `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Native build: passed.
- Focused CUDA/CLI tests: `3 passed in 3.63s`.
- Full pytest: `1441 passed in 70.27s`.

## CUDA

- CUDA available: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Multiprocessors: `188`
- Driver version: `596.21`

## Real 200-Light Evidence

- Candidate run:
  - `C:\glass_runs\phase2_s2_gate697_bounds_skip\runs_20260627_080000\bounds_skip_candidate`
- Mainline audit:
  - `C:\glass_runs\phase2_s2_gate697_bounds_skip\gate697_bounds_skip_mainline_audit.json`
  - Status: passed.
  - Input lights: `200`.
  - Active/masked: `193 / 7`.
- A/B vs Gate695 default:
  - `C:\glass_runs\phase2_s2_gate697_bounds_skip\gate697_bounds_skip_vs_gate695_default_ab.json`
  - Status: passed.
  - Elapsed ratio: `1.0421339130508445`.
  - Integration map hashes: all `6 / 6` matched.
  - Component ratio, resident integration: `3.2635820999275893 s -> 3.2714636999880895 s`, ratio `1.002415015102784`.
- A/B vs Gate696 prestart:
  - `C:\glass_runs\phase2_s2_gate697_bounds_skip\gate697_bounds_skip_vs_gate696_prestart_ab.json`
  - Status: passed.
  - Elapsed ratio: `1.0403123150886688`.
  - Integration map hashes: all `6 / 6` matched.
  - Component ratio, resident integration: `3.262477900017984 s -> 3.2714636999880895 s`, ratio `1.0027542868474468`.
- A/B vs Gate694:
  - `C:\glass_runs\phase2_s2_gate697_bounds_skip\gate697_bounds_skip_vs_gate694_ab.json`
  - Status: passed.
  - Elapsed ratio: `1.095392429864429`.
  - Integration map hashes: all `6 / 6` matched.

## Candidate Timing

- `resident_light_read_upload_calibrate`: `3.6238525999942794 s`
- `resident_registration_warp`: `0.26383820036426187 s`
- `resident_local_normalization`: `0.3621815999504179 s`
- `resident_integration`: `3.2714636999880895 s`
- `resident_output_write`: `0.26158560009207577 s`

## Native Hardened Profile

- `kernel_sync_s`: `3.1450256`
- `download_s`: `0.1223979`
- `count_map_dtype`: `uint16`
- `download_mode`: `full`
- `sample_reuse_strategy`: `frame_mask_global_reread_unit_positive_weights`
- `rejection_candidate_bounds_fast_path_enabled`: `true`
- `rejection_candidate_bounds_fast_path_model`: `skip_rejection_count_scan_when_sample_min_max_within_final_thresholds`
- `no_rejection_initial_accumulation_fast_path_enabled`: `true`

## Interpretation

- This gate is green because it preserves numerical output, contracts, DQ/map closure, and full test coverage.
- This gate is not a visible speed win on the current 200-light benchmark.
- The real 200-light resident integration component was essentially neutral (`~1.002x` versus Gate695/Gate696), and total elapsed variance was dominated by the read/upload/calibration component.
- The branch is kept because it is exact and may help lower-rejection datasets, but it must not be presented as benchmark acceleration.

## Known Limitations

- No per-pixel fast-path application counter is materialized, intentionally avoiding atomic overhead in the default kernel.
- The reducer remains a per-thread local-array implementation for <=512 positive samples.
- The larger required integration optimization is still a cooperative or segmented device-side reducer, or another larger measured 200-light component.

## Next Step

- Gate698 should avoid another small reducer branch.
- Prefer a larger mainline target:
  - cooperative/segmented resident winsorized reducer design and prototype, or
  - a real default-path I/O/upload/calibration overlap improvement with repeated 200-light A/B, or
  - a StackEngine/DQ contract gap that changes actual runtime behavior rather than only evidence transfer.

## Clean-Room

- Clean-room constraints respected.
- No PixInsight/WBPP/PJSR source was read or used.
- Only GLASS source, tests, local run artifacts, and generated benchmark outputs were inspected.
