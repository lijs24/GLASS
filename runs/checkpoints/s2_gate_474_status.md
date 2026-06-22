# S2-Gate 474 Status: Resident 200-Light A/B Matrix Runner

- Gate: S2-Gate 474
- Status: green checkpoint
- Date: 2026-06-22

## Completed

- Added a resident 200-light A/B plan builder for the real M38 H-alpha dataset.
- Added a readiness guard that records GPU free VRAM, GPU utilization, driver, and target disk free space.
- Added a dry-run/non-dry-run executor for the planned command matrix.
- Added CLI commands:
  - `glass resident-ab-matrix-plan`
  - `glass resident-ab-matrix-execute`
- Generated the real-data A/B plan and dry-run execution artifacts:
  - `runs/checkpoints/s2_gate_474_ab_matrix_plan.json`
  - `runs/checkpoints/s2_gate_474_ab_matrix_plan.md`
  - `runs/checkpoints/s2_gate_474_ab_matrix_execution_dry_run.json`
- Updated Phase 2 and algorithm-source documentation.

## Command Artifacts

The planned matrix covers:

- Baseline: `throughput_v1_lanczos3_parity`
  - resident CUDA
  - `throughput-v1`
  - Lanczos3 warp interpolation
  - registered-stack integration dispatch
- Candidate: `throughput_v2_fused_bilinear`
  - resident CUDA
  - `throughput-v2-fused`
  - bilinear warp interpolation
  - auto/fused integration dispatch

Both variants include planned commands for:

- `glass run`
- `glass compare` against the user-generated WBPP black-box master
- `glass acceptance-audit --benchmark-contract-profile resident_cuda_dq_v1`
- `benchmarks/summarize_wbpp_speedup.py`
- `glass report`

The candidate additionally includes GLASS candidate-vs-baseline compare.

## Commands Run

```powershell
.\.venv\Scripts\glass.exe resident-ab-matrix-plan --root C:\glass_runs\phase2_s2_gate474_ab_matrix_plan --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --min-coverage 190 --out runs\checkpoints\s2_gate_474_ab_matrix_plan.json --markdown runs\checkpoints\s2_gate_474_ab_matrix_plan.md
.\.venv\Scripts\glass.exe resident-ab-matrix-execute --plan runs\checkpoints\s2_gate_474_ab_matrix_plan.json --out runs\checkpoints\s2_gate_474_ab_matrix_execution_dry_run.json --dry-run
.\.venv\Scripts\python.exe -m ruff check src tests docs
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_ab_matrix_plan.py tests\test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\python.exe -m pytest -q
nvidia-smi --query-gpu=name,memory.total,memory.used,utilization.gpu,driver_version --format=csv,noheader,nounits
.\.venv\Scripts\python.exe -c "import glass_cuda as g; print('cuda_available', g.cuda_available()); print('devices', g.list_devices() if hasattr(g, 'list_devices') else 'no-list-devices')"
```

## Test Results

- `ruff check src tests docs`: passed.
- Focused pytest:
  - `tests/test_resident_ab_matrix_plan.py`
  - `tests/test_cli_smoke.py::test_cli_help_commands`
  - result: `7 passed in 1.84s`
- Full pytest:
  - result: `1113 passed in 48.91s`

## CUDA Status

- CUDA available to GLASS: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- Driver: `596.21`
- Total VRAM: about `97886 MiB`
- Current `nvidia-smi` readiness sample:
  - total: `97887 MiB`
  - used: `18894 MiB`
  - utilization: `100%`

## Real-Data Status

- The 200-light A/B plan targets the staged M38 H-alpha real dataset:
  - `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`
  - `C:\gpwbpp_runs\final_m38_h_200\manifest.json`
- The user-generated WBPP black-box reference remains:
  - `C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf`
- The heavy non-dry-run A/B was intentionally not launched because the GPU was still at `100%` utilization.

## Known Limitations

- The readiness sample is point-in-time. The next real run must recheck or regenerate the plan once the GPU is idle.
- This gate changes orchestration and auditability only. It does not change calibration, registration, interpolation, rejection, DQ, integration math, or CUDA kernels.
- The fused candidate remains opt-in and must pass real 200-light acceptance before any default promotion.

## Next Step

Run the real 200-light A/B matrix in a clean GPU window:

```powershell
.\.venv\Scripts\glass.exe resident-ab-matrix-execute --plan runs\checkpoints\s2_gate_474_ab_matrix_plan.json --out runs\checkpoints\s2_gate_474_ab_matrix_execution_real.json --fail-on-failed --fail-on-blocked
```

If the old readiness sample remains blocked, regenerate the plan first with `glass resident-ab-matrix-plan` so the execution artifact records the clean GPU state.

## Clean-Room Compliance

- This gate uses only GLASS-owned code, GLASS-generated run artifacts, user-staged image metadata paths, and user-generated WBPP black-box outputs.
- No official PixInsight/WBPP/PJSR source was read, copied, summarized, or reworked.
- Input image directories are not modified.
