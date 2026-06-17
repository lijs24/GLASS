# S2-Gate 154 Status: Runtime-Focused Candidate Sweep Plan

## Gate

- Gate: S2-Gate 154
- Status: green
- Completed at: 2026-06-17
- Scope: planning gate for runtime-only variants of the accepted `agreement_soft_downweight` candidate.

## Completed Content

- Added `glass candidate-runtime-sweep-plan`.
- Added `src/glass/report/candidate_runtime_sweep_plan.py`.
- Added focused tests in `tests/test_candidate_runtime_sweep_plan.py`.
- Added CLI smoke coverage for `candidate-runtime-sweep-plan`.
- Updated `docs/phase2_algorithm_hardening.md`.
- Updated `docs/algorithm_sources.md`.
- Generated real-data Gate154 plan artifacts under `C:\glass_runs\phase2_s2_gate_154_runtime_sweep_plan`.

## Real-Data Artifacts

- `C:\glass_runs\phase2_s2_gate_154_runtime_sweep_plan\candidate_runtime_sweep_plan.json`
- `C:\glass_runs\phase2_s2_gate_154_runtime_sweep_plan\candidate_runtime_sweep_plan.md`
- `runs\checkpoints\s2_gate_154_doctor.json`

## Commands Run

- `.\.venv\Scripts\ruff.exe check src\glass\report\candidate_runtime_sweep_plan.py tests\test_candidate_runtime_sweep_plan.py src\glass\cli.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_candidate_runtime_sweep_plan.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\glass.exe candidate-runtime-sweep-plan --comparison C:\glass_runs\phase2_s2_gate_152_candidate_comparison\candidate_comparison.json --root C:\glass_runs\phase2_s2_gate_154_runtime_sweep_plan --base-run-command C:\glass_runs\phase2_s2_gate_151_repair\agreement_soft_downweight_retry1\run_command.txt --baseline-run C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200 --baseline-compare-json C:\glass_runs\phase2_s2_gate_152_candidate_comparison\baseline_no_border_vs_reference.json --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --manifest C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200\manifest.json --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --benchmark-contract benchmarks\phase2_m38_h_200_contract.json --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --min-coverage 190 --min-speedup-vs-reference 20 --out C:\glass_runs\phase2_s2_gate_154_runtime_sweep_plan\candidate_runtime_sweep_plan.json --markdown C:\glass_runs\phase2_s2_gate_154_runtime_sweep_plan\candidate_runtime_sweep_plan.md`
- `.\.venv\Scripts\ruff.exe check .`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_154_doctor.json`

## Test Results

- Focused pytest: 12 passed in 1.84 s before the no-fail-on-failed correction; focused follow-up: 2 passed in 0.18 s.
- Full pytest: 388 passed in 26.13 s.
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

## Planned Variants

1. `retry_settings_control`
   - Changed options: none
   - Purpose: rerun the accepted candidate settings as a warm control.

2. `prefetch12_workers6`
   - Changed options: `--resident-prefetch-frames 12`, `--resident-prefetch-workers 6`
   - Purpose: test whether retry slowdown was host I/O/decode contention.

3. `prefetch20_workers8`
   - Changed options: `--resident-prefetch-frames 20`, `--resident-prefetch-workers 8`
   - Purpose: test deeper resident prefetch with the same worker count.

4. `batch16_wave4`
   - Changed options: `--resident-calibration-batch-frames 16`, `--resident-calibration-wave-frames 4`
   - Purpose: test lower launch/orchestration overhead.

5. `streams2_batch8`
   - Changed options: `--resident-calibration-streams 2`, `--resident-calibration-batch-frames 8`
   - Purpose: test whether lower stream fanout reduces synchronization overhead.

## Known Limitations

- This is a planning gate only; it does not run the 200-light variants.
- Planned commands are path-specific to the current benchmark artifacts.
- The plan intentionally does not fail single candidate-comparison commands on failed candidates, so failed variants can remain visible in the final sweep summary.
- Science options are inherited from the accepted candidate command and are not independently revalidated by this planning gate.

## Next Step

- S2-Gate 155 should execute the planned runtime variants sequentially, generate reference/baseline compares, acceptance audits, candidate-comparison artifacts, and the final `candidate-comparison-sweep` summary. Stop at the first infrastructure failure, but preserve candidate failures as comparison rows.

## Clean-Room Compliance

- This gate used GLASS-owned command/comparison artifacts and user-generated black-box reference paths only.
- It did not read or summarize official PixInsight/WBPP source code.
- It did not read image pixels or execute integration.
- It did not alter CUDA kernels, resident integration defaults, scientific formulas, or input image directories.
