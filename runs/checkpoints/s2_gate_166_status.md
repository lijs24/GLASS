# S2-Gate 166 Status: StackEngine Result DQ Contract

## Gate

S2-Gate 166: StackEngine Result DQ Contract

## Completed

- Added `src/glass/engine/stack_contract.py`.
- Embedded `build_stack_engine_result_contract()` into `CPUStackEngine.stack()`
  without changing pixel calculations.
- Added `result_contract` to `StackEngineResult.dq_provenance`.
- Added `result_contract_passed` to StackEngine metrics.
- Added focused tests in `tests/test_stack_engine_result_contract.py`.
- Generated a synthetic StackEngine result-contract artifact.
- Updated Phase 2 and algorithm-source documentation.

## Contract Checks

The in-memory contract validates:

- requested output maps are present
- optional maps match the master shape
- master pixels are finite
- zero coverage agrees with `NO_DATA` DQ pixels
- low/high rejection maps agree with DQ flags
- DQ summary agrees with provenance
- coverage sum agrees with StackEngine metrics
- coverage zero pixels agree with provenance
- request frame count and shape agree with provenance input samples

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_stack_engine_result_contract.py tests/test_stack_engine.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_stack_engine_result_contract.py tests/test_stack_engine.py tests/test_stack_engine_contract.py tests/test_pipeline_contract.py
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_166_doctor.json
```

## Test Results

- Initial focused tests after fixture repair: `13 passed in 0.06s`.
- Contract/pipeline focused tests: `19 passed in 0.80s`.
- Full tests: `290 passed, 127 skipped in 16.01s`.
- CUDA test skip reason: GPU busy at `100%` utilization with approximately
  `53150/97887 MiB` used.
- Ruff: `All checks passed!`.
- Doctor report: `runs/checkpoints/s2_gate_166_doctor.json`.

## Artifacts

- Synthetic result-contract sample:
  `C:\glass_runs\phase2_s2_gate_166_stack_result_contract\stack_result_contract.json`

## Artifact Summary

- Contract passed: `true`.
- Check count: `10`.
- Sample metrics include `result_contract_passed=true`.

## CUDA Status

- CUDA wrapper importable: yes.
- Native CUDA extension loaded: yes.
- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Known Limitations

- This gate validates CPU StackEngine result contracts only.
- Resident CUDA result-contract parity is not implemented in this gate.
- The contract validates in-memory result consistency; downstream FITS pixel
  verification remains covered by pipeline-contract and acceptance-audit tools.

## Next Step

Extend equivalent result-contract summaries to resident CUDA integration
artifacts, or use the new CPU contract as a stricter source for pipeline
contract checks.

## Clean-Room Compliance

Compliant. This gate uses GLASS in-memory StackEngine results and synthetic test
arrays only. It does not read proprietary source code, modify input data, inspect
external implementations, or change scientific formulas.
