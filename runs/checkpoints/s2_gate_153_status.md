# S2-Gate 153 Status: Candidate Comparison Sweep Summary

## Gate

- Gate: S2-Gate 153
- Status: green
- Completed at: 2026-06-17
- Scope: artifact-level sweep summary over measured `candidate-comparison` artifacts.

## Completed Content

- Added `glass candidate-comparison-sweep`.
- Added `src/glass/report/candidate_comparison_sweep.py`.
- Added focused tests in `tests/test_candidate_comparison_sweep.py`.
- Added CLI smoke coverage for `candidate-comparison-sweep`.
- Updated `docs/phase2_algorithm_hardening.md`.
- Updated `docs/algorithm_sources.md`.
- Generated real-data Gate153 artifacts under `C:\glass_runs\phase2_s2_gate_153_candidate_sweep`.

## Real-Data Artifacts

- `C:\glass_runs\phase2_s2_gate_153_candidate_sweep\agreement_soft_downweight_initial_failed_comparison.json`
- `C:\glass_runs\phase2_s2_gate_153_candidate_sweep\agreement_soft_downweight_initial_failed_comparison.md`
- `C:\glass_runs\phase2_s2_gate_153_candidate_sweep\candidate_comparison_sweep.json`
- `C:\glass_runs\phase2_s2_gate_153_candidate_sweep\candidate_comparison_sweep.md`
- `runs\checkpoints\s2_gate_153_doctor.json`

## Commands Run

- `.\.venv\Scripts\ruff.exe check src\glass\report\candidate_comparison_sweep.py tests\test_candidate_comparison_sweep.py src\glass\cli.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_candidate_comparison.py tests\test_candidate_comparison_sweep.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\glass.exe candidate-comparison --baseline-run C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200 --candidate-run C:\glass_runs\phase2_s2_gate_150_rejection_registration_plan\runs\agreement_soft_downweight --candidate-id agreement_soft_downweight_initial_failed --baseline-compare-json C:\glass_runs\phase2_s2_gate_152_candidate_comparison\baseline_no_border_vs_reference.json --candidate-compare-json C:\glass_runs\phase2_s2_gate_150_rejection_registration_plan\compare\agreement_soft_downweight_vs_reference_contract.json --candidate-acceptance-json C:\glass_runs\phase2_s2_gate_150_rejection_registration_plan\acceptance\agreement_soft_downweight_acceptance_contract.json --min-speedup-vs-reference 20 --out C:\glass_runs\phase2_s2_gate_153_candidate_sweep\agreement_soft_downweight_initial_failed_comparison.json --markdown C:\glass_runs\phase2_s2_gate_153_candidate_sweep\agreement_soft_downweight_initial_failed_comparison.md`
- `.\.venv\Scripts\glass.exe candidate-comparison-sweep --comparison C:\glass_runs\phase2_s2_gate_153_candidate_sweep\agreement_soft_downweight_initial_failed_comparison.json --comparison C:\glass_runs\phase2_s2_gate_152_candidate_comparison\candidate_comparison.json --out C:\glass_runs\phase2_s2_gate_153_candidate_sweep\candidate_comparison_sweep.json --markdown C:\glass_runs\phase2_s2_gate_153_candidate_sweep\candidate_comparison_sweep.md --fail-on-no-passed`
- `.\.venv\Scripts\ruff.exe check .`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_153_doctor.json`

## Test Results

- Focused pytest: 14 passed in 2.05 s.
- Full pytest: 386 passed in 34.41 s.
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

## Candidate Sweep Result

- Candidate count: 2
- Passed candidate count: 1
- Top candidate: `agreement_soft_downweight`
- Top status: passed
- Recommendation: `run_runtime_sweep_for_top_candidate`

### Ranked Candidates

1. `agreement_soft_downweight`
   - Status: passed
   - Runtime: 26.005688100121915 s
   - Speedup versus reference: 42.011616681462776x
   - Reference RMS: 0.0014945534429799121
   - Reference abs diff p99: 0.00043544556712731865
   - Recommendation: `eligible_but_needs_runtime_sweep`

2. `agreement_soft_downweight_initial_failed`
   - Status: failed
   - Runtime: 483.80420529982075 s
   - Speedup versus reference: 2.258229647513989x
   - Failed required checks: `candidate_acceptance_passed`, `candidate_minimum_speedup_vs_reference`
   - Recommendation: `hold_candidate`

## Known Limitations

- This gate ranks existing candidate-comparison artifacts only.
- It does not execute integration or image comparison.
- The measured sweep has only two samples: the failed first soft-downweight attempt and the retry success.
- The winning candidate still needs a runtime-focused sweep before any default promotion.

## Next Step

- S2-Gate 154 should create or execute a bounded runtime sweep for `agreement_soft_downweight`, varying only runtime-sensitive orchestration settings while keeping the successful reference agreement, frame accounting, and acceptance contracts fixed.

## Clean-Room Compliance

- This gate used GLASS-owned JSON artifacts and user-generated black-box reference comparison evidence only.
- It did not read or summarize official PixInsight/WBPP source code.
- It did not read image pixels during the sweep step.
- It did not alter CUDA kernels, resident integration defaults, scientific formulas, or input image directories.
