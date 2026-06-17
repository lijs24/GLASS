# S2-Gate 156 Status: Prefetch/Worker Matrix Planning and Preflight

## Gate

- Gate: S2-Gate 156
- Status: green for matrix planning and preflight diagnostics
- Completed at: 2026-06-17
- Scope: add generated prefetch-frame/prefetch-worker matrix planning to `glass candidate-runtime-sweep-plan` and generate the next executable 200-light matrix plan.

## Completed Content

- Extended `glass candidate-runtime-sweep-plan` with:
  - `--prefetch-frame`
  - `--prefetch-worker`
- Added matrix generation in `src/glass/report/candidate_runtime_sweep_plan.py`.
- Added test coverage for generated prefetch/worker matrices.
- Generated the real 3x3 confirmation plan under `C:\glass_runs\phase2_s2_gate_156_prefetch_matrix`.
- Ran a CUDA execution preflight on `prefetch10_workers5`; it stopped before completion because the GPU was already occupied by an unrelated training process.
- Updated `docs/phase2_algorithm_hardening.md`.
- Updated `docs/algorithm_sources.md`.

## Real-Data Artifacts

- Matrix plan JSON: `C:\glass_runs\phase2_s2_gate_156_prefetch_matrix\candidate_runtime_sweep_plan.json`
- Matrix plan Markdown: `C:\glass_runs\phase2_s2_gate_156_prefetch_matrix\candidate_runtime_sweep_plan.md`
- Failed preflight run timing: `C:\glass_runs\phase2_s2_gate_156_prefetch_matrix\runs\prefetch10_workers5\run_timing.json`
- Doctor report: `runs\checkpoints\s2_gate_156_doctor.json`

## Planned Matrix

- Prefetch frames: 10, 12, 14
- Prefetch workers: 5, 6, 7
- Variant count: 9

Variants:

1. `prefetch10_workers5`
2. `prefetch10_workers6`
3. `prefetch10_workers7`
4. `prefetch12_workers5`
5. `prefetch12_workers6`
6. `prefetch12_workers7`
7. `prefetch14_workers5`
8. `prefetch14_workers6`
9. `prefetch14_workers7`

## Commands Run

- `.\.venv\Scripts\ruff.exe check src\glass\report\candidate_runtime_sweep_plan.py tests\test_candidate_runtime_sweep_plan.py src\glass\cli.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_candidate_runtime_sweep_plan.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\glass.exe candidate-runtime-sweep-plan --comparison C:\glass_runs\phase2_s2_gate_152_candidate_comparison\candidate_comparison.json --root C:\glass_runs\phase2_s2_gate_156_prefetch_matrix --base-run-command C:\glass_runs\phase2_s2_gate_151_repair\agreement_soft_downweight_retry1\run_command.txt --baseline-run C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200 --baseline-compare-json C:\glass_runs\phase2_s2_gate_152_candidate_comparison\baseline_no_border_vs_reference.json --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --manifest C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200\manifest.json --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --benchmark-contract benchmarks\phase2_m38_h_200_contract.json --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --min-coverage 190 --min-speedup-vs-reference 20 --prefetch-frame 10 --prefetch-frame 12 --prefetch-frame 14 --prefetch-worker 5 --prefetch-worker 6 --prefetch-worker 7 --out C:\glass_runs\phase2_s2_gate_156_prefetch_matrix\candidate_runtime_sweep_plan.json --markdown C:\glass_runs\phase2_s2_gate_156_prefetch_matrix\candidate_runtime_sweep_plan.md`
- Executed the first planned `prefetch10_workers5` run as a preflight.
- `.\.venv\Scripts\ruff.exe check .`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_156_doctor.json`
- `nvidia-smi --query-gpu=name,memory.total,memory.used,utilization.gpu,temperature.gpu --format=csv,noheader`
- `Get-CimInstance Win32_Process` for the GPU-owning Python processes.

## Test Results

- Focused pytest: 13 passed in 1.93 s.
- Full pytest: 389 passed in 26.08 s.
- Ruff: all checks passed.
- Doctor: completed successfully.

## CUDA Availability

- CUDA wrapper importable: true
- CUDA native extension loaded: true
- CUDA available: true
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21

## Preflight Result

- Attempted variant: `prefetch10_workers5`
- Result: failed before resident execution completed.
- Error: `cudaMalloc(resident calibrated stack) failed: out of memory`
- Failed stage elapsed: 17.36150659993291 s
- GPU state after failure:
  - Memory used: 77517 MiB / 97887 MiB
  - GPU utilization: 100%
  - Temperature: 84 C
- Identified GPU-owning processes:
  - PID 4308: `C:\Users\ljs\WORK\astro\aidenoise\.venv\Scripts\python.exe ASTERIS_train_130apo_sharded.py`
  - PID 70932: `C:\Users\ljs\AppData\Local\Programs\Python\Python312\python.exe ASTERIS_train_130apo_sharded.py`
  - PID 78628: multiprocessing worker for PID 70932

## Known Limitations

- The 3x3 matrix was not executed because an unrelated ASTERIS training process occupied most of the GPU memory.
- No unrelated user process was killed or modified.
- The generated matrix plan is ready to execute when GPU memory is available.
- This gate changes planning/orchestration only; it does not alter resident defaults, CUDA kernels, science settings, or input data.

## Next Step

- S2-Gate 157 should execute `C:\glass_runs\phase2_s2_gate_156_prefetch_matrix\candidate_runtime_sweep_plan.json` after the ASTERIS training process releases GPU memory, then generate the final `candidate_runtime_sweep.json` and decide whether `prefetch12_workers6` remains best or a nearby setting wins.

## Clean-Room Compliance

- This gate used GLASS-owned command/comparison artifacts and user-generated black-box reference paths only.
- It did not read or summarize official PixInsight/WBPP source code.
- It did not modify input image directories.
- It did not alter CUDA kernels, resident integration defaults, or scientific formulas.
