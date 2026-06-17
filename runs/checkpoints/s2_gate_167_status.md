# S2-Gate 167 Status: StackEngine Contract Requires Result Contract

## Gate

S2-Gate 167: StackEngine Contract Requires Result Contract

## Completed

- Extended `glass stack-engine-contract` so CPU StackEngine calibration and
  integration records must include embedded `result_contract.passed=true`.
- Surfaced `result_contract_passed` in master and integration output audit
  records.
- Added regression coverage for StackEngine-looking records with legacy DQ
  provenance but no embedded result contract.
- Generated a synthetic CPU audit and StackEngine contract artifact.
- Updated Phase 2 and algorithm-source documentation.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_stack_engine_contract.py tests/test_stack_engine_result_contract.py tests/test_pipeline_contract.py
.\.venv\Scripts\glass.exe synthetic --out C:\glass_runs\phase2_s2_gate_167_stack_contract_result_gate\data --frames 3 --width 24 --height 24 --filter H --known-shift
.\.venv\Scripts\glass.exe audit --root C:\glass_runs\phase2_s2_gate_167_stack_contract_result_gate\data --out C:\glass_runs\phase2_s2_gate_167_stack_contract_result_gate\run --backend cpu --tile-size 8
.\.venv\Scripts\glass.exe stack-engine-contract --run C:\glass_runs\phase2_s2_gate_167_stack_contract_result_gate\run --out C:\glass_runs\phase2_s2_gate_167_stack_contract_result_gate\stack_engine_contract.json --markdown C:\glass_runs\phase2_s2_gate_167_stack_contract_result_gate\stack_engine_contract.md
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_167_doctor.json
```

## Test Results

- Focused tests: `11 passed in 0.90s`.
- Full tests: `291 passed, 127 skipped in 16.71s`.
- CUDA test skip reason: GPU busy at `100%` utilization with approximately
  `55820/97887 MiB` used.
- Ruff: `All checks passed!`.
- Doctor report: `runs/checkpoints/s2_gate_167_doctor.json`.

## Artifacts

- Synthetic dataset:
  `C:\glass_runs\phase2_s2_gate_167_stack_contract_result_gate\data`
- CPU audit run:
  `C:\glass_runs\phase2_s2_gate_167_stack_contract_result_gate\run`
- StackEngine contract JSON:
  `C:\glass_runs\phase2_s2_gate_167_stack_contract_result_gate\stack_engine_contract.json`
- StackEngine contract Markdown:
  `C:\glass_runs\phase2_s2_gate_167_stack_contract_result_gate\stack_engine_contract.md`

## Artifact Summary

- StackEngine contract status: `passed`.
- Master records: `3`.
- Integration output records: `1`.
- Master `result_contract_passed`: `[true, true, true]`.
- Integration `result_contract_passed`: `[true]`.

## CUDA Status

- CUDA wrapper importable: yes.
- Native CUDA extension loaded: yes.
- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Known Limitations

- Resident CUDA integration records are not required to carry the CPU
  StackEngine result contract yet.
- This gate enforces artifact-level presence and pass status; detailed FITS map
  pixel verification remains handled by `pipeline-contract` and
  `acceptance-audit`.

## Next Step

Add resident CUDA result-contract parity, or extend pipeline-contract summaries
to expose StackEngine result-contract status alongside DQ pixel verification.

## Clean-Room Compliance

Compliant. This gate uses GLASS-generated synthetic data and GLASS artifact
audits only. It does not read proprietary source code, modify user input data,
or change scientific formulas.
