# S2 Gate 178 Status: Resident Calibration-Contract Parity In StackEngine Audit

## Gate

- Gate: S2-Gate 178
- Status: green
- Commit: pending at checkpoint write time
- Clean-room: compliant. This gate consumes GLASS-owned resident artifacts and user-generated benchmark/reference outputs only; it does not read or derive from external proprietary implementation source.

## Completed

- Added `glass resident-calibration-contract`.
- Validates resident CUDA master-calibration evidence from `resident_artifacts.json`:
  resident artifact presence, master set records, bias/dark/flat source counts,
  master statistics, cache file presence, shape metadata, light frame IDs,
  calibration timing, and downstream resident master output existence.
- Extended `glass stack-engine-contract` with
  `--resident-calibration-contract-json`.
- Converts a passing resident calibration contract into a resident CUDA
  master-calibration surface for all-surface default-promotion checks.
- Updated candidate runtime sweep plans/executor so every candidate can generate
  `resident-calibration-contract`, `resident-result-contract`, and then
  `stack-engine-contract` with both resident contract inputs.
- Updated HTML/Markdown/JSON report surfaces and algorithm source docs.

## Real Artifact Results

- Artifact root:
  `C:\glass_runs\phase2_s2_gate_178_resident_calibration_parity`
- Resident calibration contract:
  `resident_calibration_contract.json` / `.md`
- Resident result contract:
  `resident_result_contract.json` / `.md`
- StackEngine parity contract:
  `resident_stack_calibration_parity_contract.json` / `.md`
- Acceptance audit:
  `acceptance_resident_stack_calibration_parity.json` / `.md`
- HTML report:
  `report_resident_stack_calibration_parity.html`
- Runtime plan:
  `runtime_plan.json` / `.md`
- Runtime dry run:
  `runtime_plan_execution_dry_run.json`

Key real-data outcomes:

- Resident calibration contract: passed.
- Resident result contract: passed.
- StackEngine contract: passed.
- `resident_calibration_contract_attached`: true.
- `resident_result_contract_attached`: true.
- `default_promotion.ready`: true.
- StackEngine default-promotion blocker count: 0.
- Calibration surfaces: 1 resident CUDA surface.
- Integration surfaces: 1 resident CUDA surface.
- Acceptance audit: passed.
- Speedup versus black-box reference: `46.82815250883293x`.

## Commands Run

```powershell
.\.venv\Scripts\ruff.exe check src/glass/report/resident_calibration_contract.py src/glass/report/stack_engine_contract.py src/glass/report/candidate_runtime_sweep_plan.py src/glass/report/candidate_runtime_sweep_execute.py src/glass/report/html_report.py src/glass/cli.py tests/test_resident_calibration_contract.py tests/test_stack_engine_contract.py tests/test_candidate_runtime_sweep_plan.py tests/test_candidate_runtime_sweep_execute.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_calibration_contract.py tests/test_stack_engine_contract.py tests/test_candidate_runtime_sweep_plan.py tests/test_candidate_runtime_sweep_execute.py tests/test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\glass.exe resident-calibration-contract --run C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1 --out C:\glass_runs\phase2_s2_gate_178_resident_calibration_parity\resident_calibration_contract.json --markdown C:\glass_runs\phase2_s2_gate_178_resident_calibration_parity\resident_calibration_contract.md --fail-on-failed
.\.venv\Scripts\glass.exe resident-result-contract --run C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1 --out C:\glass_runs\phase2_s2_gate_178_resident_calibration_parity\resident_result_contract.json --markdown C:\glass_runs\phase2_s2_gate_178_resident_calibration_parity\resident_result_contract.md --fail-on-failed
.\.venv\Scripts\glass.exe stack-engine-contract --run C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1 --scope all --expected-integration-engine cuda_resident_stack --resident-calibration-contract-json C:\glass_runs\phase2_s2_gate_178_resident_calibration_parity\resident_calibration_contract.json --resident-result-contract-json C:\glass_runs\phase2_s2_gate_178_resident_calibration_parity\resident_result_contract.json --out C:\glass_runs\phase2_s2_gate_178_resident_calibration_parity\resident_stack_calibration_parity_contract.json --markdown C:\glass_runs\phase2_s2_gate_178_resident_calibration_parity\resident_stack_calibration_parity_contract.md --require-default-ready
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_160_preset_confirmation\compare\throughput_v1_vs_reference.json --benchmark-contract benchmarks\phase2_m38_h_200_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate_170_pipeline_resident_contract\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate_178_resident_calibration_parity\resident_stack_calibration_parity_contract.json --out C:\glass_runs\phase2_s2_gate_178_resident_calibration_parity\acceptance_resident_stack_calibration_parity.json --markdown C:\glass_runs\phase2_s2_gate_178_resident_calibration_parity\acceptance_resident_stack_calibration_parity.md
.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1 --acceptance-audit C:\glass_runs\phase2_s2_gate_178_resident_calibration_parity\acceptance_resident_stack_calibration_parity.json --pipeline-contract C:\glass_runs\phase2_s2_gate_170_pipeline_resident_contract\pipeline_contract.json --stack-engine-contract C:\glass_runs\phase2_s2_gate_178_resident_calibration_parity\resident_stack_calibration_parity_contract.json --out C:\glass_runs\phase2_s2_gate_178_resident_calibration_parity\report_resident_stack_calibration_parity.html
.\.venv\Scripts\glass.exe candidate-runtime-sweep-plan --comparison C:\glass_runs\phase2_s2_gate_160_preset_confirmation\comparison\throughput_v1_candidate_comparison.json --root C:\glass_runs\phase2_s2_gate_178_resident_calibration_parity\runtime_plan --base-run-command C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1\run_command.txt --baseline-run C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1 --baseline-compare-json C:\glass_runs\phase2_s2_gate_160_preset_confirmation\compare\throughput_v1_vs_baseline.json --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master_H.fits --manifest C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200\manifest.json --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --benchmark-contract benchmarks\phase2_m38_h_200_contract.json --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --min-coverage 190 --min-speedup-vs-reference 20 --variant retry_settings_control --out C:\glass_runs\phase2_s2_gate_178_resident_calibration_parity\runtime_plan.json --markdown C:\glass_runs\phase2_s2_gate_178_resident_calibration_parity\runtime_plan.md
.\.venv\Scripts\glass.exe candidate-runtime-sweep-execute --plan C:\glass_runs\phase2_s2_gate_178_resident_calibration_parity\runtime_plan.json --out C:\glass_runs\phase2_s2_gate_178_resident_calibration_parity\runtime_plan_execution_dry_run.json --dry-run
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_178_doctor.json
.\.venv\Scripts\glass.exe resident-calibration-contract --help
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,driver_version --format=csv,noheader,nounits
```

## Test Results

- Focused pytest: `20 passed in 1.30s`.
- Full ruff: `All checks passed`.
- Full pytest: `443 passed in 24.68s`.

## CUDA Status

- CUDA available: yes.
- Native CUDA extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB reported by GLASS doctor.
- Driver: 596.21.
- `nvidia-smi` at checkpoint time: GPU utilization 100%, memory 46930 / 97887 MiB used by external workload.

## Known Limitations

- The resident calibration contract validates artifact/cache evidence; it does
  not re-read full calibration image pixels or compare calibration masters
  numerically against the CPU path.
- Resident calibration uses the existing resident master-cache metadata and
  cache files. If future resident modes stop writing cache files, this contract
  should be updated with an equivalent in-memory/exported proof.
- This gate promotes the contract evidence to default-ready for the measured
  resident run, but it does not change the runtime preset/defaults.

## Next Step

- S2-Gate 179 should decide whether default-ready resident evidence is enough
  to promote a release preset/default, or whether another repeat benchmark in a
  controlled low-GPU-load / warm-cache window is required first.
