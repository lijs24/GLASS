# S2-Gate 168 Status: Pipeline Contract Exposes StackEngine Result Contract

## Gate

S2-Gate 168: Pipeline Contract Exposes StackEngine Result Contract

## Completed

- Extended `glass pipeline-contract` integration rows with
  `stack_result_contract` status.
- Added the `integration_stack_result_contract` check.
- Required `result_contract.passed=true` when an integration output declares CPU
  StackEngine provenance or `tile_stack_mode=stack_engine_cpu`.
- Preserved resident CUDA behavior by not requiring the CPU StackEngine result
  contract for non-CPU-StackEngine outputs.
- Added regression coverage for StackEngine-looking integration artifacts that
  lack an embedded result contract.
- Generated a synthetic CPU audit and pixel-verifying pipeline-contract
  artifact.
- Updated Phase 2 and algorithm-source documentation.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_pipeline_contract.py tests/test_stack_engine_contract.py tests/test_stack_engine_result_contract.py
.\.venv\Scripts\glass.exe synthetic --out C:\glass_runs\phase2_s2_gate_168_pipeline_result_contract\data --frames 3 --width 24 --height 24 --filter H --known-shift
.\.venv\Scripts\glass.exe audit --root C:\glass_runs\phase2_s2_gate_168_pipeline_result_contract\data --out C:\glass_runs\phase2_s2_gate_168_pipeline_result_contract\run --backend cpu --tile-size 8
.\.venv\Scripts\glass.exe pipeline-contract --run C:\glass_runs\phase2_s2_gate_168_pipeline_result_contract\run --out C:\glass_runs\phase2_s2_gate_168_pipeline_result_contract\pipeline_contract.json --markdown C:\glass_runs\phase2_s2_gate_168_pipeline_result_contract\pipeline_contract.md --pixel-verify --pixel-verify-tile-size 7
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_168_doctor.json
```

## Test Results

- Focused tests: `12 passed in 0.81s`.
- Full tests: `292 passed, 127 skipped in 16.81s`.
- CUDA test skip reason: GPU busy at `100%` utilization with approximately
  `56899/97887 MiB` used.
- Ruff: `All checks passed!`.
- Doctor report: `runs/checkpoints/s2_gate_168_doctor.json`.

## Artifacts

- Synthetic dataset:
  `C:\glass_runs\phase2_s2_gate_168_pipeline_result_contract\data`
- CPU audit run:
  `C:\glass_runs\phase2_s2_gate_168_pipeline_result_contract\run`
- Pipeline contract JSON:
  `C:\glass_runs\phase2_s2_gate_168_pipeline_result_contract\pipeline_contract.json`
- Pipeline contract Markdown:
  `C:\glass_runs\phase2_s2_gate_168_pipeline_result_contract\pipeline_contract.md`

## Artifact Summary

- Pipeline contract status: `passed`.
- `integration_stack_result_contract`: passed.
- Required CPU StackEngine result-contract outputs: `1`.
- Failed result-contract outputs: `0`.
- Integration output `stack_result_contract.status`: `passed`.
- Integration output result-contract check count: `10`.
- Pixel verification: enabled.

## CUDA Status

- CUDA wrapper importable: yes.
- Native CUDA extension loaded: yes.
- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Known Limitations

- Resident CUDA integration outputs are not yet required to provide an
  equivalent result-contract summary.
- This gate validates artifact contracts and optional FITS map pixels for a
  small synthetic CPU run; it does not execute the 200-light repeat benchmark.

## Next Step

Add resident CUDA result-contract parity, or execute the guarded 200-light repeat
benchmark when the GPU and disks are in a controlled window.

## Clean-Room Compliance

Compliant. This gate uses GLASS-generated synthetic data and GLASS pipeline
artifacts only. It does not read proprietary source code, modify user input
data, inspect external implementations, or change scientific formulas.
