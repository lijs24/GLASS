# S2-Gate 173 Status: Release Evidence Report Surface

## Gate

S2-Gate 173: Release Evidence Report Surface

## Completed

- Added `release_contract_evidence.pipeline_contract` to acceptance-audit JSON.
- Added a `Pipeline Contract Evidence` section to acceptance-audit Markdown.
- Added a `Release contract evidence` section to HTML reports.
- The new report section shows passing pipeline-contract evidence, not only
  failures.
- Added regression tests for acceptance JSON/Markdown and HTML rendering.
- Generated real Gate160-based acceptance and HTML report artifacts under
  `C:\glass_runs\phase2_s2_gate_173_release_evidence_report`.
- Updated Phase 2, algorithm-source, and Windows release documentation.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_acceptance_audit.py tests/test_cli_smoke.py::test_cli_report_includes_resident_artifacts tests/test_cli_smoke.py::test_cli_report_lists_failed_acceptance_checks tests/test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_160_preset_confirmation\compare\throughput_v1_vs_reference.json --benchmark-contract benchmarks\phase2_m38_h_200_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate_170_pipeline_resident_contract\pipeline_contract.json --out C:\glass_runs\phase2_s2_gate_173_release_evidence_report\acceptance_release_evidence.json --markdown C:\glass_runs\phase2_s2_gate_173_release_evidence_report\acceptance_release_evidence.md
.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1 --acceptance-audit C:\glass_runs\phase2_s2_gate_173_release_evidence_report\acceptance_release_evidence.json --pipeline-contract C:\glass_runs\phase2_s2_gate_170_pipeline_resident_contract\pipeline_contract.json --out C:\glass_runs\phase2_s2_gate_173_release_evidence_report\report_release_evidence.html
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_173_doctor.json
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,driver_version --format=csv,noheader,nounits
```

## Test Results

- Focused tests: `20 passed in 1.19s`.
- Ruff: `All checks passed!`.
- Full tests: `304 passed, 127 skipped in 17.16s`.
- CUDA skip reason in pytest: GPU busy, `100%` utilization and
  `55742/97887 MiB` used at test time.
- Doctor report: `runs/checkpoints/s2_gate_173_doctor.json`.

## Real Artifacts

- Acceptance JSON:
  `C:\glass_runs\phase2_s2_gate_173_release_evidence_report\acceptance_release_evidence.json`
- Acceptance Markdown:
  `C:\glass_runs\phase2_s2_gate_173_release_evidence_report\acceptance_release_evidence.md`
- HTML report:
  `C:\glass_runs\phase2_s2_gate_173_release_evidence_report\report_release_evidence.html`
- Pipeline-contract input:
  `C:\glass_runs\phase2_s2_gate_170_pipeline_resident_contract\pipeline_contract.json`

## Real Artifact Summary

- Acceptance status: `passed`.
- Acceptance checks: `98`.
- Release evidence status: `passed`.
- Required by benchmark contract: true.
- Direct pipeline checks: `2`.
- Benchmark pipeline checks: `6`.
- Passed pipeline checks: `8`.
- Failed pipeline checks: `0`.
- Pipeline contract status: `passed`.
- Pipeline contract check count: `7`.
- Speedup versus black-box reference: `46.82815250883293x`.
- Markdown contains `Pipeline Contract Evidence`.
- HTML contains `Release contract evidence` and the
  `contract_pipeline_contract_passed` row.

## CUDA Status

- CUDA wrapper importable: true.
- CUDA native extension loaded: true.
- CUDA available: true.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB` reported by doctor.
- Driver: `596.21`.
- Current telemetry after tests: `100%` utilization,
  `70977/97887 MiB` used. Heavy repeat benchmarks remain deferred until the
  GPU is under GLASS control.

## Known Limitations

- This gate is a reporting/audit-surface gate. It does not change image
  processing, CUDA kernels, or numerical results.
- The real HTML report is built over existing Gate160/Gate170 artifacts and does
  not rerun the 200-light pipeline.
- GPU-heavy benchmark repeats remain blocked by external GPU load.

## Next Step

S2-Gate 174 should resume the larger Phase 2 algorithm objective by tightening
the StackEngine default path: first expose release/report evidence showing which
master/integration surfaces are still resident-CUDA-specific versus shared
StackEngine, then move one remaining CPU-safe integration surface toward the
StackEngine contract.

## Clean-Room Compliance

Compliant. This gate consumes GLASS acceptance inputs, GLASS pipeline-contract
JSON, GLASS run artifacts, and user-generated black-box benchmark/reference
outputs only. It does not read proprietary implementation source, alter image
calculations, rerun image processing, modify input data, or change CUDA kernels.
