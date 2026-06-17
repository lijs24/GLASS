# S2-Gate 171 Status: Acceptance Audit Pipeline Contract Evidence

## Gate

S2-Gate 171: Acceptance Audit Requires Pipeline Contract Evidence

## Completed

- Added `--pipeline-contract-json` to `glass acceptance-audit`.
- Added acceptance hard checks:
  - `pipeline_contract_present`
  - `pipeline_contract_passed`
- Added pipeline-contract summary fields to acceptance JSON and Markdown.
- Added regression tests for passing and failing pipeline-contract artifacts.
- Generated a real 200-light acceptance artifact using the Gate160 resident run
  and Gate170 pipeline-contract artifact.
- Updated Phase 2 planning docs and algorithm-source traceability docs.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_acceptance_audit.py tests/test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_160_preset_confirmation\compare\throughput_v1_vs_reference.json --benchmark-contract benchmarks\phase2_m38_h_200_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate_170_pipeline_resident_contract\pipeline_contract.json --out C:\glass_runs\phase2_s2_gate_171_acceptance_pipeline_contract\acceptance_with_pipeline_contract.json --markdown C:\glass_runs\phase2_s2_gate_171_acceptance_pipeline_contract\acceptance_with_pipeline_contract.md
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_171_doctor.json
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,driver_version --format=csv,noheader,nounits
```

One earlier acceptance command used a stale optional resident-determinism path
and failed before any image processing or artifact mutation. The successful
Gate171 command keeps the previous Gate160 acceptance inputs unchanged and adds
only the Gate170 pipeline-contract JSON.

## Test Results

- Focused tests: `15 passed in 1.09s`.
- Ruff: `All checks passed!`.
- Full tests: `300 passed, 127 skipped in 16.70s`.
- CUDA skip reason in pytest: GPU busy, `96%` utilization and
  `69838/97887 MiB` used at test time.
- Doctor report: `runs/checkpoints/s2_gate_171_doctor.json`.

## Real Artifacts

- Acceptance JSON:
  `C:\glass_runs\phase2_s2_gate_171_acceptance_pipeline_contract\acceptance_with_pipeline_contract.json`
- Acceptance Markdown:
  `C:\glass_runs\phase2_s2_gate_171_acceptance_pipeline_contract\acceptance_with_pipeline_contract.md`
- Pipeline-contract input:
  `C:\glass_runs\phase2_s2_gate_170_pipeline_resident_contract\pipeline_contract.json`
- Source resident run:
  `C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1`

## Real Artifact Summary

- Acceptance status: `passed`.
- Acceptance checks: `92`.
- Pipeline contract audit type: `pipeline_invariant_contract`.
- Pipeline contract status: `passed`.
- Pipeline contract check count: `7`.
- Failed pipeline checks: `0`.
- Speedup versus black-box reference: `46.82815250883293x`.
- Frame accounting remains the Gate160 reference case:
  `200` light frames, `193` active/integrated frames, and `7` zero-weight
  frames under the existing benchmark contract.

## CUDA Status

- CUDA wrapper importable: true.
- CUDA native extension loaded: true.
- CUDA available: true.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB` reported by doctor.
- Driver: `596.21`.
- Current telemetry after tests: `100%` utilization,
  `48992/97887 MiB` used. Heavy repeat benchmarks remain deferred until the
  GPU is under GLASS control.

## Known Limitations

- Gate171 is an acceptance-layer hardening gate; it does not rerun image
  processing or improve runtime.
- The real artifact is JSON/Markdown audit evidence over existing Gate160 and
  Gate170 outputs.
- Acceptance only requires pipeline-contract evidence when
  `--pipeline-contract-json` is supplied. This preserves legacy audit
  compatibility while allowing benchmark contracts and release checks to opt in.
- GPU-heavy 200-light repeat timing is still blocked by external GPU load.

## Next Step

S2-Gate 172 should promote pipeline-contract evidence into the release or
benchmark checklist so future 200-light acceptance runs cannot be considered
release-grade without both acceptance and pipeline invariant contracts passing.

## Clean-Room Compliance

Compliant. This gate consumes GLASS-generated run artifacts, GLASS pipeline
contract JSON, and user-generated black-box benchmark/reference outputs only.
It does not read proprietary implementation source, alter image calculations,
rerun PixInsight/WBPP internals, modify input data, or change CUDA kernels.
