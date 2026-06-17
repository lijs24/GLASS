# S2-Gate 176 Status: Release Contract Requires StackEngine Default Promotion

## Gate

S2-Gate 176: Release Contract Requires StackEngine Default Promotion.

## Completed

- Added benchmark-contract checks for StackEngine default-promotion evidence.
- Added `stack_engine_default_promotion` blocks to the M38 200-light release
  benchmark contracts.
- Added `glass acceptance-audit --stack-engine-contract-json`.
- Acceptance audits now embed:
  - `stack_engine_contract`
  - `release_contract_evidence.stack_engine_default_promotion`
- Acceptance Markdown now includes a `StackEngine Default Promotion Evidence`
  section.
- HTML reports now show both pipeline release evidence and StackEngine
  default-promotion release evidence.
- Candidate runtime sweep plans now generate `glass stack-engine-contract`
  artifacts and pass them into `acceptance-audit`.
- Candidate runtime sweep execution remains compatible with older plans that do
  not include the new `stack_engine_contract` step.
- Added regression tests for passing, missing, blocked, CLI, report, and sweep
  plan/execution cases.

## Real Artifacts

- Root:
  `C:\glass_runs\phase2_s2_gate_176_release_stack_default_contract`
- Acceptance JSON:
  `C:\glass_runs\phase2_s2_gate_176_release_stack_default_contract\acceptance_stack_default_contract.json`
- Acceptance Markdown:
  `C:\glass_runs\phase2_s2_gate_176_release_stack_default_contract\acceptance_stack_default_contract.md`
- HTML report:
  `C:\glass_runs\phase2_s2_gate_176_release_stack_default_contract\report_stack_default_contract.html`
- Runtime sweep plan:
  `C:\glass_runs\phase2_s2_gate_176_release_stack_default_contract\runtime_plan.json`
- Runtime sweep Markdown:
  `C:\glass_runs\phase2_s2_gate_176_release_stack_default_contract\runtime_plan.md`
- Runtime sweep dry-run execution:
  `C:\glass_runs\phase2_s2_gate_176_release_stack_default_contract\runtime_plan_execution_dry_run.json`
- Doctor report:
  `runs\checkpoints\s2_gate_176_doctor.json`

## Real Artifact Summary

- Acceptance status: `failed`
- This failure is intentional for this gate. The current Gate160 resident CUDA
  run is fast and pipeline-valid, but it is not ready for full StackEngine
  default promotion.
- Speedup versus black-box reference: `46.82815250883293x`
- Pipeline evidence status: `passed`
- StackEngine default-promotion evidence status: `failed`
- StackEngine contract passed: `true`
- Default promotion ready: `false`
- Default promotion status: `blocked`
- Default promotion gap count: `1`
- Default promotion blocker count: `4`
- Failed acceptance checks:
  - `contract_stack_engine_default_promotion_ready`
  - `contract_stack_engine_default_promotion_scope`
  - `contract_stack_engine_default_promotion_recommendation`
  - `contract_stack_engine_default_promotion_gap_count`
  - `contract_stack_engine_default_promotion_blocker_count`
- HTML report contains `stack_engine_default_promotion`,
  `contract_stack_engine_default_promotion_ready`, and `resident_cuda_surface`.
- Runtime sweep dry-run step order:
  `run -> compare_reference -> compare_baseline -> stack_engine_contract -> pipeline_contract -> acceptance_audit -> candidate_comparison`

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_acceptance_audit.py tests/test_candidate_runtime_sweep_plan.py tests/test_candidate_runtime_sweep_execute.py tests/test_cli_smoke.py::test_cli_report_includes_resident_artifacts tests/test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\ruff.exe check src/glass/report/benchmark_contract.py src/glass/report/acceptance_audit.py src/glass/report/html_report.py src/glass/report/candidate_runtime_sweep_plan.py src/glass/report/candidate_runtime_sweep_execute.py src/glass/cli.py tests/test_acceptance_audit.py tests/test_candidate_runtime_sweep_plan.py tests/test_candidate_runtime_sweep_execute.py tests/test_cli_smoke.py

$root = 'C:\glass_runs\phase2_s2_gate_176_release_stack_default_contract'
New-Item -ItemType Directory -Force -Path $root | Out-Null
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_160_preset_confirmation\compare\throughput_v1_vs_reference.json --benchmark-contract benchmarks\phase2_m38_h_200_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate_170_pipeline_resident_contract\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate_175_default_promotion_guard\resident_default_blocked_contract.json --out "$root\acceptance_stack_default_contract.json" --markdown "$root\acceptance_stack_default_contract.md"
.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1 --acceptance-audit "$root\acceptance_stack_default_contract.json" --pipeline-contract C:\glass_runs\phase2_s2_gate_170_pipeline_resident_contract\pipeline_contract.json --stack-engine-contract C:\glass_runs\phase2_s2_gate_175_default_promotion_guard\resident_default_blocked_contract.json --out "$root\report_stack_default_contract.html"

.\.venv\Scripts\glass.exe candidate-runtime-sweep-plan --comparison C:\glass_runs\phase2_s2_gate_160_preset_confirmation\comparison\throughput_v1_candidate_comparison.json --root "$root\runtime_plan" --base-run-command C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1\run_command.txt --baseline-run C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1 --baseline-compare-json C:\glass_runs\phase2_s2_gate_160_preset_confirmation\compare\throughput_v1_vs_baseline.json --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master_H.fits --manifest C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200\manifest.json --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --benchmark-contract benchmarks\phase2_m38_h_200_contract.json --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --min-coverage 190 --min-speedup-vs-reference 20 --variant retry_settings_control --out "$root\runtime_plan.json" --markdown "$root\runtime_plan.md"
.\.venv\Scripts\glass.exe candidate-runtime-sweep-execute --plan "$root\runtime_plan.json" --out "$root\runtime_plan_execution_dry_run.json" --dry-run

.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_176_doctor.json
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,driver_version --format=csv,noheader,nounits
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused pytest: `31 passed in 1.43s`
- Focused ruff: `All checks passed`
- Full ruff: `All checks passed`
- Full pytest: `310 passed, 127 skipped in 18.71s`
- Skips: CUDA tests skipped because the GPU was busy.
- GLASS doctor: passed and wrote `runs\checkpoints\s2_gate_176_doctor.json`

## CUDA Status

- CUDA wrapper importable: `true`
- CUDA native extension loaded: `true`
- CUDA available: `true`
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver: `596.21`
- Point-in-time `nvidia-smi`: utilization `100%`, memory `52737 / 97887 MiB`

## Known Limitations

- This gate is a release-contract hardening gate. It does not alter image
  processing, CUDA kernels, registration, calibration, or integration math.
- The updated release benchmark contracts now intentionally reject the current
  resident CUDA run as a release-grade StackEngine-default candidate until
  default-promotion blockers are removed.
- Runtime sweep execution was dry-run only because the GPU remained externally
  busy.

## Next Step

Remove the StackEngine default-promotion blockers. The clearest next gate is to
generate an all-surface StackEngine contract for resident runs, or to implement
resident CUDA result/default-promotion parity so `default_promotion.ready` can
become true without weakening the release contract.

## Clean-Room Compliance

Compliant. This gate consumes GLASS benchmark contracts, GLASS StackEngine
contract JSON, GLASS pipeline-contract JSON, GLASS run artifacts, and
user-generated benchmark/reference metadata only. It does not read external
implementation source, alter image calculations, modify input data, or run
black-box software.
