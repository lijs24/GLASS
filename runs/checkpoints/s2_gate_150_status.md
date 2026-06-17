# S2-Gate 150 Status - Tile-Local Rejection/Registration Experiment Plan

## Gate

S2-Gate 150: tile-local rejection/registration experiment plan.

## Completed

- Added `glass tile-local-rejection-registration-plan`.
- Converted S2-Gate 149 frame-level rejection/registration evidence into an
  explicit measured-experiment command queue.
- Generated candidate run commands from the baseline 200-light resident
  `run_command.txt`.
- Planned four opt-in candidates:
  - `agreement_flag_only`
  - `agreement_soft_downweight`
  - `agreement_strict_downweight`
  - `exclude_top6_hotspot_frames`
- Emitted compare and acceptance-audit commands because reference, manifest,
  WBPP result, and benchmark contract inputs were available.
- Added focused unit and CLI smoke coverage.
- Updated Phase 2 planning and algorithm-source documentation.

## Real-Data Artifacts

- Experiment plan JSON:
  `C:\glass_runs\phase2_s2_gate_150_rejection_registration_plan\rejection_registration_experiment_plan.json`
- Experiment plan Markdown:
  `C:\glass_runs\phase2_s2_gate_150_rejection_registration_plan\rejection_registration_experiment_plan.md`
- Doctor report:
  `runs\checkpoints\s2_gate_150_doctor.json`

## Real-Data Results

- Candidate count: `4`.
- Hotspot frames selected for diagnostic exclusion:
  `F000100`, `F000101`, `F000102`, `F000103`, `F000104`, `F000105`.
- Source recommendation:
  `prioritize_registration_agreement_rejection_interaction`.
- Plan recommendation:
  `run_soft_downweight_then_exclude_hotspot_control`.
- Each candidate includes:
  - `run`
  - `compare_reference`
  - `acceptance_audit`

Candidate intent:

| candidate | intent |
| --- | --- |
| `agreement_flag_only` | record low-agreement frames without agreement downweighting |
| `agreement_soft_downweight` | reduce downweight strength by lowering the agreement threshold to `0.6` |
| `agreement_strict_downweight` | increase downweight strength by raising the agreement threshold to `0.9` |
| `exclude_top6_hotspot_frames` | diagnostic control excluding the six highest-rejection focus/top-family frames |

This gate does not run the heavy candidates. It creates the auditable command
queue needed to run them one at a time under the same compare and acceptance
contracts.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_tile_local_rejection_registration_plan.py tests\test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\ruff.exe check src\glass\report\tile_local_rejection_registration_plan.py src\glass\cli.py tests\test_tile_local_rejection_registration_plan.py tests\test_cli_smoke.py
.\.venv\Scripts\glass.exe tile-local-rejection-registration-plan --audit C:\glass_runs\phase2_s2_gate_149_rejection_registration\new_region_rejection_registration_audit.json --root C:\glass_runs\phase2_s2_gate_150_rejection_registration_plan --base-run-command C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200\run_command.txt --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --manifest C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200\manifest.json --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --benchmark-contract benchmarks\phase2_m38_h_200_contract.json --out C:\glass_runs\phase2_s2_gate_150_rejection_registration_plan\rejection_registration_experiment_plan.json --markdown C:\glass_runs\phase2_s2_gate_150_rejection_registration_plan\rejection_registration_experiment_plan.md --glass-scale 8.764434957115609e-06 --glass-offset 0 --min-coverage 1 --soft-agreement-score 0.6 --strict-agreement-score 0.9 --exclude-top-count 6
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_150_doctor.json
```

## Test Results

- Focused pytest: `3 passed in 0.89s`.
- Full pytest: `382 passed in 25.80s`.
- Ruff: `All checks passed`.
- Doctor: passed and wrote `runs\checkpoints\s2_gate_150_doctor.json`.

## CUDA Status

- CUDA wrapper importable: yes.
- CUDA native extension loaded: yes.
- CUDA available: yes.
- GPU 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.
- Recommended package: `cuda`.

## Known Limitations

- This gate is planning only. It does not execute the candidate integrations.
- Candidate commands must still be run and measured before any scientific or
  performance conclusion is drawn.
- The `exclude_top6_hotspot_frames` candidate is a diagnostic control, not a
  production policy proposal.
- Local normalization remains disabled in this benchmark path.

## Next Step

S2-Gate 151 should execute the first low-risk candidate,
`agreement_soft_downweight`, then run compare and acceptance-audit from the
plan. Acceptance must cover runtime, frame accounting, DQ maps, coverage, and
full-frame agreement before considering any further experiment.

## Clean-Room Compliance

Compliant. This gate consumes GLASS audit artifacts and user-provided
GLASS/WBPP result paths only. No proprietary implementation source was read,
copied, summarized, or reworked.
