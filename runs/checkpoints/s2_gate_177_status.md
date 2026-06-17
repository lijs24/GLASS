# S2-Gate 177 Status: Resident Result-Contract Parity In StackEngine Audit

## Gate

S2-Gate 177: Resident Result-Contract Parity In StackEngine Audit.

## Completed

- Added `glass stack-engine-contract --resident-result-contract-json`.
- StackEngine contract audits now attach resident CUDA result-contract evidence
  to matching resident integration outputs by index or filter.
- Resident CUDA integration outputs with matching passing resident
  result-contracts now report:
  - `resident_result_contract_passed=true`
  - `result_contract_passed=true`
  - `stack_engine_contract_ready=true`
- Adoption gap accounting now treats resident CUDA integration result-contract
  parity as ready while keeping full default-promotion blockers for non-`all`
  scope or missing calibration surfaces.
- HTML and Markdown reports expose resident result-contract attachment/parity.
- Candidate runtime sweep plans now generate a `resident-result-contract` step
  before `stack-engine-contract`, and pass
  `--resident-result-contract-json` into the StackEngine contract command.
- Candidate runtime sweep execution remains compatible with older plans that do
  not contain the new step.
- Added regression tests for resident parity, CLI JSON input, report visibility,
  and runtime sweep plan/execution ordering.
- Updated Phase 2 planning and algorithm-source documentation.

## Real Artifacts

- Root:
  `C:\glass_runs\phase2_s2_gate_177_resident_stack_parity`
- StackEngine parity contract JSON:
  `C:\glass_runs\phase2_s2_gate_177_resident_stack_parity\resident_stack_parity_contract.json`
- StackEngine parity contract Markdown:
  `C:\glass_runs\phase2_s2_gate_177_resident_stack_parity\resident_stack_parity_contract.md`
- Acceptance JSON:
  `C:\glass_runs\phase2_s2_gate_177_resident_stack_parity\acceptance_resident_stack_parity.json`
- Acceptance Markdown:
  `C:\glass_runs\phase2_s2_gate_177_resident_stack_parity\acceptance_resident_stack_parity.md`
- HTML report:
  `C:\glass_runs\phase2_s2_gate_177_resident_stack_parity\report_resident_stack_parity.html`
- Runtime sweep plan:
  `C:\glass_runs\phase2_s2_gate_177_resident_stack_parity\runtime_plan.json`
- Runtime sweep dry-run execution:
  `C:\glass_runs\phase2_s2_gate_177_resident_stack_parity\runtime_plan_execution_dry_run.json`
- Doctor report:
  `runs\checkpoints\s2_gate_177_doctor.json`

## Real Artifact Summary

- StackEngine parity contract status: `passed`
- Resident result-contract attached: `true`
- Integration `result_contract_passed`: `true`
- Integration `resident_result_contract_passed`: `true`
- Adoption gap count: `0`
- Adoption recommendation: `stack_engine_default_ready`
- Default promotion ready: `false`
- Remaining default-promotion blockers:
  - `scope_not_all`
  - `missing_calibration_surface`
- Acceptance status: `failed`
- Acceptance failed checks after parity:
  - `contract_stack_engine_default_promotion_ready`
  - `contract_stack_engine_default_promotion_scope`
  - `contract_stack_engine_default_promotion_blocker_count`
- Previous Gate176 resident-surface failures removed:
  - `contract_stack_engine_default_promotion_recommendation`
  - `contract_stack_engine_default_promotion_gap_count`
- Speedup versus black-box reference remains `46.82815250883293x`.
- Runtime sweep dry-run step order:
  `run -> compare_reference -> compare_baseline -> resident_result_contract -> stack_engine_contract -> pipeline_contract -> acceptance_audit -> candidate_comparison`

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_stack_engine_contract.py tests/test_candidate_runtime_sweep_plan.py tests/test_candidate_runtime_sweep_execute.py tests/test_cli_smoke.py::test_cli_report_summarizes_stack_engine_contract tests/test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\ruff.exe check src/glass/report/stack_engine_contract.py src/glass/report/html_report.py src/glass/report/candidate_runtime_sweep_plan.py src/glass/report/candidate_runtime_sweep_execute.py src/glass/cli.py tests/test_stack_engine_contract.py tests/test_candidate_runtime_sweep_plan.py tests/test_candidate_runtime_sweep_execute.py tests/test_cli_smoke.py

$root = 'C:\glass_runs\phase2_s2_gate_177_resident_stack_parity'
New-Item -ItemType Directory -Force -Path $root | Out-Null
.\.venv\Scripts\glass.exe stack-engine-contract --run C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1 --scope integration --expected-integration-engine cuda_resident_stack --resident-result-contract-json C:\glass_runs\phase2_s2_gate_169_resident_result_contract\resident_result_contract.json --out "$root\resident_stack_parity_contract.json" --markdown "$root\resident_stack_parity_contract.md"
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_160_preset_confirmation\compare\throughput_v1_vs_reference.json --benchmark-contract benchmarks\phase2_m38_h_200_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate_170_pipeline_resident_contract\pipeline_contract.json --stack-engine-contract-json "$root\resident_stack_parity_contract.json" --out "$root\acceptance_resident_stack_parity.json" --markdown "$root\acceptance_resident_stack_parity.md"
.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1 --acceptance-audit "$root\acceptance_resident_stack_parity.json" --pipeline-contract C:\glass_runs\phase2_s2_gate_170_pipeline_resident_contract\pipeline_contract.json --stack-engine-contract "$root\resident_stack_parity_contract.json" --out "$root\report_resident_stack_parity.html"

.\.venv\Scripts\glass.exe candidate-runtime-sweep-plan --comparison C:\glass_runs\phase2_s2_gate_160_preset_confirmation\comparison\throughput_v1_candidate_comparison.json --root "$root\runtime_plan" --base-run-command C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1\run_command.txt --baseline-run C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1 --baseline-compare-json C:\glass_runs\phase2_s2_gate_160_preset_confirmation\compare\throughput_v1_vs_baseline.json --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master_H.fits --manifest C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200\manifest.json --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --benchmark-contract benchmarks\phase2_m38_h_200_contract.json --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --min-coverage 190 --min-speedup-vs-reference 20 --variant retry_settings_control --out "$root\runtime_plan.json" --markdown "$root\runtime_plan.md"
.\.venv\Scripts\glass.exe candidate-runtime-sweep-execute --plan "$root\runtime_plan.json" --out "$root\runtime_plan_execution_dry_run.json" --dry-run

.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_177_doctor.json
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,driver_version --format=csv,noheader,nounits
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused pytest: `17 passed in 1.47s`
- Focused ruff: `All checks passed`
- Full ruff: `All checks passed`
- Full pytest: `439 passed in 24.72s`
- GLASS doctor: passed and wrote `runs\checkpoints\s2_gate_177_doctor.json`

## CUDA Status

- CUDA wrapper importable: `true`
- CUDA native extension loaded: `true`
- CUDA available: `true`
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver: `596.21`
- Point-in-time `nvidia-smi`: utilization `100%`, memory `49434 / 97887 MiB`

## Known Limitations

- This gate removes the resident integration result-contract/adoption gap only.
- Full release acceptance remains blocked because the Gate160 artifact is an
  integration-scope resident audit without calibration/master surface evidence.
- No new heavy 200-light processing was launched; existing Gate160/Gate169/Gate170
  artifacts were reused.

## Next Step

Remove the remaining default-promotion blockers by providing all-surface
StackEngine evidence for resident runs, especially calibration/master surface
records or an equivalent resident calibration contract.

## Clean-Room Compliance

Compliant. This gate consumes GLASS resident-result-contract JSON, GLASS
StackEngine contract JSON, GLASS run artifacts, and user-generated
benchmark/reference metadata only. It does not read external implementation
source, alter image calculations, modify input data, or run black-box software.
