# S2-Gate 172 Status: Benchmark Contract Pipeline Evidence

## Gate

S2-Gate 172: Benchmark Contract Requires Pipeline Contract Evidence

## Completed

- Added a benchmark-contract `pipeline_contract` requirement block.
- Added benchmark checks for:
  - `contract_pipeline_contract_present`
  - `contract_pipeline_contract_audit_type`
  - `contract_pipeline_contract_passed`
  - `contract_pipeline_contract_min_check_count`
  - `contract_pipeline_contract_check:<name>`
  - `contract_pipeline_contract_no_failed_checks`
- Updated `benchmarks/phase2_m38_h_200_contract.json` and
  `benchmarks/phase2_m38_h_200_audit_maps_contract.json` so release-grade
  200-light acceptance requires a passing pipeline invariant contract.
- Extended candidate runtime sweep plans with a `pipeline_contract` command
  before `acceptance_audit`.
- Extended candidate runtime sweep execution to run the new step for new plans
  while remaining compatible with older plans that lack it.
- Generated real Gate160-based release-contract acceptance and dry-run runtime
  plan artifacts under `C:\glass_runs\phase2_s2_gate_172_release_contract_pipeline`.
- Updated Phase 2, algorithm-source, and Windows release documentation.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_acceptance_audit.py tests/test_candidate_runtime_sweep_plan.py tests/test_candidate_runtime_sweep_execute.py tests/test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_160_preset_confirmation\compare\throughput_v1_vs_reference.json --benchmark-contract benchmarks\phase2_m38_h_200_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate_170_pipeline_resident_contract\pipeline_contract.json --out C:\glass_runs\phase2_s2_gate_172_release_contract_pipeline\acceptance_release_contract.json --markdown C:\glass_runs\phase2_s2_gate_172_release_contract_pipeline\acceptance_release_contract.md
.\.venv\Scripts\glass.exe candidate-runtime-sweep-plan --comparison C:\glass_runs\phase2_s2_gate_160_preset_confirmation\comparison\throughput_v1_candidate_comparison.json --root C:\glass_runs\phase2_s2_gate_172_release_contract_pipeline\runtime_plan --base-run-command C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1\run_command.txt --baseline-run C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1 --baseline-compare-json C:\glass_runs\phase2_s2_gate_160_preset_confirmation\compare\throughput_v1_vs_baseline.json --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master_H.fits --manifest C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200\manifest.json --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --benchmark-contract benchmarks\phase2_m38_h_200_contract.json --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --min-coverage 190 --min-speedup-vs-reference 20 --variant retry_settings_control --out C:\glass_runs\phase2_s2_gate_172_release_contract_pipeline\runtime_plan.json --markdown C:\glass_runs\phase2_s2_gate_172_release_contract_pipeline\runtime_plan.md
.\.venv\Scripts\glass.exe candidate-runtime-sweep-execute --plan C:\glass_runs\phase2_s2_gate_172_release_contract_pipeline\runtime_plan.json --out C:\glass_runs\phase2_s2_gate_172_release_contract_pipeline\runtime_plan_execution_dry_run.json --dry-run
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_172_doctor.json
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,driver_version --format=csv,noheader,nounits
```

## Test Results

- Focused tests: `25 passed in 1.28s`.
- Ruff: `All checks passed!`.
- Full tests: `303 passed, 127 skipped in 16.91s`.
- CUDA skip reason in pytest: GPU busy, `100%` utilization and
  `55473/97887 MiB` used at test time.
- Doctor report: `runs/checkpoints/s2_gate_172_doctor.json`.

## Real Artifacts

- Release-contract acceptance JSON:
  `C:\glass_runs\phase2_s2_gate_172_release_contract_pipeline\acceptance_release_contract.json`
- Release-contract acceptance Markdown:
  `C:\glass_runs\phase2_s2_gate_172_release_contract_pipeline\acceptance_release_contract.md`
- Runtime sweep plan JSON:
  `C:\glass_runs\phase2_s2_gate_172_release_contract_pipeline\runtime_plan.json`
- Runtime sweep plan Markdown:
  `C:\glass_runs\phase2_s2_gate_172_release_contract_pipeline\runtime_plan.md`
- Runtime sweep dry-run execution:
  `C:\glass_runs\phase2_s2_gate_172_release_contract_pipeline\runtime_plan_execution_dry_run.json`

## Real Artifact Summary

- Acceptance status: `passed`.
- Acceptance checks: `98`.
- Benchmark pipeline-contract checks: `6`.
- Pipeline contract audit type: `pipeline_invariant_contract`.
- Pipeline contract status: `passed`.
- Pipeline contract check count: `7`.
- Required pipeline check found: `integration_resident_result_contract`.
- Failed pipeline checks: `0`.
- Speedup versus black-box reference: `46.82815250883293x`.
- Dry-run runtime sweep step order:
  `run -> compare_reference -> compare_baseline -> pipeline_contract -> acceptance_audit -> candidate_comparison`.

## CUDA Status

- CUDA wrapper importable: true.
- CUDA native extension loaded: true.
- CUDA available: true.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB` reported by doctor.
- Driver: `596.21`.
- Current telemetry after tests: `99%` utilization,
  `55398/97887 MiB` used. Heavy repeat benchmarks remain deferred until the
  GPU is under GLASS control.

## Known Limitations

- This gate hardens acceptance/release contracts and command planning; it does
  not rerun image processing or change numerical algorithms.
- The runtime sweep execution artifact is dry-run only, by design, because the
  GPU remains externally loaded.
- Older runtime sweep plans without a `pipeline_contract` command remain
  executable for compatibility, but new plans include the step.
- Other older experimental planners that manually emit acceptance commands may
  still need follow-up if they are promoted into the release path.

## Next Step

S2-Gate 173 should extend report/release summaries so acceptance artifacts show
the benchmark pipeline-contract checks prominently, and then continue toward the
larger Phase 2 objective of making StackEngine the default integration path.

## Clean-Room Compliance

Compliant. This gate consumes GLASS benchmark contracts, GLASS pipeline-contract
JSON, GLASS run artifacts, and user-generated black-box benchmark/reference
outputs only. It does not read proprietary implementation source, alter image
calculations, rerun image processing, modify input data, or change CUDA kernels.
