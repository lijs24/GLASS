# S2-Gate 175 Status: StackEngine Default Promotion Guard

## Gate

S2-Gate 175: StackEngine Default Promotion Guard.

## Completed

- Added `default_promotion` evidence to `glass stack-engine-contract` JSON.
- Promotion readiness now requires:
  - `scope=all`
  - at least one calibration/master surface
  - at least one integration surface
  - all StackEngine contract checks passing
  - zero Phase 2 StackEngine default gaps
  - adoption recommendation `stack_engine_default_ready`
- Added `glass stack-engine-contract --require-default-ready`.
- Added `glass guardrails --require-stack-default-ready`.
- Preserved existing contract behavior when the new requirement flags are not
  supplied.
- Added HTML report fields for default-promotion readiness, status, blocker
  count, and blocker rows.
- Added regression tests for CPU promotion-ready runs, resident CUDA
  contract-passed but promotion-blocked runs, guardrails enforcement, and report
  rendering.
- Updated Phase 2 planning and algorithm-source documentation.

## Real And Synthetic Artifacts

- Root:
  `C:\glass_runs\phase2_s2_gate_175_default_promotion_guard`
- Synthetic CPU dataset:
  `C:\glass_runs\phase2_s2_gate_175_default_promotion_guard\synthetic_cpu_ready`
- CPU ready run:
  `C:\glass_runs\phase2_s2_gate_175_default_promotion_guard\cpu_ready_run`
- CPU promotion-ready contract:
  `C:\glass_runs\phase2_s2_gate_175_default_promotion_guard\cpu_default_ready_contract.json`
- CPU promotion-ready Markdown:
  `C:\glass_runs\phase2_s2_gate_175_default_promotion_guard\cpu_default_ready_contract.md`
- CPU guardrails summary:
  `C:\glass_runs\phase2_s2_gate_175_default_promotion_guard\cpu_ready_guardrails\guardrails_summary.json`
- CPU guardrails HTML report:
  `C:\glass_runs\phase2_s2_gate_175_default_promotion_guard\cpu_ready_guardrails\report.html`
- Gate160 resident blocked contract:
  `C:\glass_runs\phase2_s2_gate_175_default_promotion_guard\resident_default_blocked_contract.json`
- Gate160 resident blocked Markdown:
  `C:\glass_runs\phase2_s2_gate_175_default_promotion_guard\resident_default_blocked_contract.md`
- Gate160 resident blocked HTML report:
  `C:\glass_runs\phase2_s2_gate_175_default_promotion_guard\resident_default_blocked_report.html`
- Doctor report:
  `runs\checkpoints\s2_gate_175_doctor.json`

## Artifact Summary

- CPU StackEngine contract passed: `true`
- CPU default promotion ready: `true`
- CPU promotion blocker count: `0`
- CPU guardrails passed with `--require-stack-default-ready`: `true`
- Resident CUDA integration contract passed: `true`
- Resident default promotion ready: `false`
- Resident default promotion status: `blocked`
- Resident `--require-default-ready` exit code: `3`
- Resident blockers:
  - `scope_not_all`
  - `missing_calibration_surface`
  - `phase2_stack_engine_default_gaps`
  - `adoption_recommendation_not_ready`
- Resident adoption gap reason:
  - `resident_cuda_surface`

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_stack_engine_contract.py tests/test_cli_smoke.py::test_cli_guardrails_generates_contracts_and_report tests/test_cli_smoke.py::test_cli_report_summarizes_stack_engine_contract tests/test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\ruff.exe check src/glass/report/stack_engine_contract.py src/glass/report/html_report.py src/glass/cli.py tests/test_stack_engine_contract.py tests/test_cli_smoke.py

$root = 'C:\glass_runs\phase2_s2_gate_175_default_promotion_guard'
New-Item -ItemType Directory -Force -Path $root | Out-Null
.\.venv\Scripts\glass.exe synthetic --out "$root\synthetic_cpu_ready" --frames 4 --width 32 --height 32 --filter H --known-shift
.\.venv\Scripts\glass.exe audit --root "$root\synthetic_cpu_ready" --out "$root\cpu_ready_run" --backend cpu --tile-size 8
.\.venv\Scripts\glass.exe stack-engine-contract --run "$root\cpu_ready_run" --require-default-ready --out "$root\cpu_default_ready_contract.json" --markdown "$root\cpu_default_ready_contract.md"
.\.venv\Scripts\glass.exe guardrails --run "$root\cpu_ready_run" --out-dir "$root\cpu_ready_guardrails" --expected-integration-engine stack_engine_cpu --require-stack-default-ready --pixel-verify --pixel-verify-tile-size 8

.\.venv\Scripts\glass.exe stack-engine-contract --run C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1 --scope integration --expected-integration-engine cuda_resident_stack --require-default-ready --out "$root\resident_default_blocked_contract.json" --markdown "$root\resident_default_blocked_contract.md"
.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1 --stack-engine-contract "$root\resident_default_blocked_contract.json" --pipeline-contract C:\glass_runs\phase2_s2_gate_170_pipeline_resident_contract\pipeline_contract.json --acceptance-audit C:\glass_runs\phase2_s2_gate_173_release_evidence_report\acceptance_release_evidence.json --out "$root\resident_default_blocked_report.html"

.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_175_doctor.json
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,driver_version --format=csv,noheader,nounits
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused pytest: `8 passed in 1.26s`
- Focused ruff: `All checks passed`
- Full ruff: `All checks passed`
- Full pytest: `306 passed, 127 skipped in 17.03s`
- Skips: CUDA tests skipped because the GPU was busy.
- GLASS doctor: passed and wrote `runs\checkpoints\s2_gate_175_doctor.json`

## CUDA Status

- CUDA wrapper importable: `true`
- CUDA native extension loaded: `true`
- CUDA available: `true`
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver: `596.21`
- Point-in-time `nvidia-smi`: utilization `100%`, memory `48923 / 97887 MiB`

## Known Limitations

- This gate adds a release/CI guard and report evidence; it does not convert
  resident CUDA integration into the CPU StackEngine result-contract path.
- A resident CUDA integration-only audit can still pass its resident contract,
  but `--require-default-ready` intentionally blocks default promotion until the
  all-surface StackEngine default criteria are met.
- No new heavy 200-light processing run was launched because the GPU was already
  busy; the Gate160 resident run was reused as an existing real-data artifact.

## Next Step

Use the promotion guard in release-grade benchmark/acceptance flows, then reduce
the current blockers by either adding all-surface default evidence for the
resident path or implementing StackEngine-backed resident/result-contract parity
so `phase2_stack_engine_default_gap_count` can reach zero.

## Clean-Room Compliance

Compliant. This gate consumes GLASS-generated synthetic data, GLASS run
artifacts, StackEngine contracts, resident contracts, and guardrail reports only.
It does not read external implementation source, alter scientific formulas,
modify input directories, or run black-box software.
