# S2-Gate 174 Status: StackEngine Adoption Evidence

## Gate

S2-Gate 174: StackEngine Adoption Evidence / Default Gap Audit.

## Completed

- Added a StackEngine adoption summary to `glass stack-engine-contract`.
- Classified every audited master/integration surface by engine family:
  `stack_engine_cpu`, `cuda_resident_stack`, or legacy/unknown.
- Reported result-contract readiness, fallback state, Phase 2 default gap state,
  gap reason, and adoption recommendation.
- Preserved resident CUDA acceptance for integration-only audits with
  `--expected-integration-engine cuda_resident_stack` while explicitly reporting
  the remaining `resident_cuda_surface` default gap.
- Surfaced adoption counts and per-surface gap rows in HTML reports.
- Added regression tests for all-ready CPU StackEngine surfaces, legacy/fallback
  surfaces, missing result contracts, resident CUDA adoption gaps, and report
  rendering.
- Updated Phase 2 planning and algorithm-source documentation.

## Real Artifacts

- Adoption contract JSON:
  `C:\glass_runs\phase2_s2_gate_174_stack_engine_adoption\stack_engine_adoption_contract.json`
- Adoption contract Markdown:
  `C:\glass_runs\phase2_s2_gate_174_stack_engine_adoption\stack_engine_adoption_contract.md`
- HTML report:
  `C:\glass_runs\phase2_s2_gate_174_stack_engine_adoption\report_stack_engine_adoption.html`
- Doctor report:
  `runs\checkpoints\s2_gate_174_doctor.json`

## Real Artifact Summary

- StackEngine contract status: `passed`
- Scope: `integration`
- Expected integration engine: `cuda_resident_stack`
- Audited surfaces: `1`
- CPU StackEngine surfaces: `0`
- Resident CUDA surfaces: `1`
- Phase 2 StackEngine default gaps: `1`
- Recommendation: `resident_cuda_surfaces_remain`
- Gap reason: `resident_cuda_surface`
- HTML report contains the adoption recommendation, gap-count label, and gap
  reason.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_stack_engine_contract.py tests/test_cli_smoke.py::test_cli_report_summarizes_stack_engine_contract tests/test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\ruff.exe check src/glass/report/stack_engine_contract.py src/glass/report/html_report.py tests/test_stack_engine_contract.py tests/test_cli_smoke.py

New-Item -ItemType Directory -Force -Path C:\glass_runs\phase2_s2_gate_174_stack_engine_adoption | Out-Null
.\.venv\Scripts\glass.exe stack-engine-contract --run C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1 --scope integration --expected-integration-engine cuda_resident_stack --out C:\glass_runs\phase2_s2_gate_174_stack_engine_adoption\stack_engine_adoption_contract.json --markdown C:\glass_runs\phase2_s2_gate_174_stack_engine_adoption\stack_engine_adoption_contract.md

.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1 --stack-engine-contract C:\glass_runs\phase2_s2_gate_174_stack_engine_adoption\stack_engine_adoption_contract.json --pipeline-contract C:\glass_runs\phase2_s2_gate_170_pipeline_resident_contract\pipeline_contract.json --acceptance-audit C:\glass_runs\phase2_s2_gate_173_release_evidence_report\acceptance_release_evidence.json --out C:\glass_runs\phase2_s2_gate_174_stack_engine_adoption\report_stack_engine_adoption.html

.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_174_doctor.json
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,driver_version --format=csv,noheader,nounits
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused pytest: `6 passed in 1.05s`
- Focused ruff: `All checks passed`
- Full ruff: `All checks passed`
- Full pytest: `432 passed in 24.82s`
- GLASS doctor: passed and wrote `runs\checkpoints\s2_gate_174_doctor.json`

## CUDA Status

- CUDA wrapper importable: `true`
- CUDA native extension loaded: `true`
- CUDA available: `true`
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver: `596.21`
- Point-in-time `nvidia-smi`: utilization `100%`, memory `48679 / 97887 MiB`

## Known Limitations

- This gate is an adoption audit/reporting gate; it does not convert the
  resident CUDA integration path into CPU StackEngine semantics.
- Resident CUDA result-contract parity is handled by the resident result
  contract and pipeline-contract gates, not by CPU StackEngine
  `result_contract` embedding.
- No new heavy 200-light run was launched because the GPU was externally busy
  at the checkpoint moment.

## Next Step

Use the adoption evidence to plan the next StackEngine-default hardening gate:
either implement resident CUDA result-contract parity in the same default
surface language, or add a default-selection guard that refuses to promote
StackEngine while `phase2_stack_engine_default_gap_count` is nonzero.

## Clean-Room Compliance

Compliant. This gate consumes GLASS-generated calibration, integration,
contract, and report artifacts only. It does not read external implementation
source, copy proprietary behavior, alter image calculations, modify input
directories, or rerun black-box software.
