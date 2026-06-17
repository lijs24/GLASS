# S2-Gate 170 Status: Pipeline Contract Exposes Resident Result Contract

## Gate

S2-Gate 170: Pipeline Contract Exposes Resident Result Contract

## Completed

- Added public `build_resident_output_contract()` helper.
- Extended `glass pipeline-contract` integration rows with
  `resident_result_contract`.
- Added `integration_resident_result_contract`.
- Required resident CUDA integration outputs to satisfy the resident
  result-contract audit.
- Added tests for passing resident output and missing source-term provenance.
- Ran the updated pipeline-contract against the real Gate160 `throughput-v1`
  resident run.
- Updated Phase 2 and algorithm-source documentation.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_pipeline_contract.py tests/test_resident_result_contract.py
.\.venv\Scripts\glass.exe pipeline-contract --run C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1 --out C:\glass_runs\phase2_s2_gate_170_pipeline_resident_contract\pipeline_contract.json --markdown C:\glass_runs\phase2_s2_gate_170_pipeline_resident_contract\pipeline_contract.md
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_170_doctor.json
```

## Test Results

- Focused tests: `10 passed in 0.66s`.
- Full tests: `297 passed, 127 skipped in 16.34s`.
- CUDA test skip reason: GPU busy at `100%` utilization with approximately
  `69224/97887 MiB` used.
- Ruff: `All checks passed!`.
- Doctor report: `runs/checkpoints/s2_gate_170_doctor.json`.

## Artifacts

- Pipeline contract JSON:
  `C:\glass_runs\phase2_s2_gate_170_pipeline_resident_contract\pipeline_contract.json`
- Pipeline contract Markdown:
  `C:\glass_runs\phase2_s2_gate_170_pipeline_resident_contract\pipeline_contract.md`

## Real Artifact Summary

- Pipeline contract status: `passed`.
- `integration_resident_result_contract`: passed.
- Required resident outputs: `1`.
- Failed resident outputs: `0`.
- Resident contract check count: `9`.
- Active frame count: `193`.
- Input frame count: `200`.

## CUDA Status

- CUDA wrapper importable: yes.
- Native CUDA extension loaded: yes.
- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Known Limitations

- Pipeline-contract uses resident result-contract JSON checks only here; large
  FITS map pixel verification remains opt-in through dedicated commands.
- This gate audits existing resident artifacts and does not rerun the 200-light
  benchmark.

## Next Step

When the GPU and disk window are controlled, execute the guarded 200-light
repeat plan or run resident result-contract pixel verification deliberately on
the selected large benchmark output.

## Clean-Room Compliance

Compliant. This gate consumes GLASS integration JSON and existing GLASS output
paths only. It does not read proprietary source code, alter CUDA kernels, rerun
image processing, modify input data, or change defaults.
