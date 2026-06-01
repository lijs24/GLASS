# S2-Gate 88 Status: StackEngine Default Contract Audit

## Gate

S2-Gate 88: StackEngine Default Contract Audit

## Completed Content

- Added `glass stack-engine-contract`, a standalone audit command for verifying StackEngine default routing and DQ provenance.
- Added `src/glass/report/stack_engine_contract.py` to audit:
  - master calibration artifacts in `calibration_artifacts.json`
  - integration outputs in `integration_results.json`
  - StackEngine routing flags
  - StackEngine DQ provenance
  - normalized `dq_provenance_summary` records
- Added JSON and optional Markdown outputs for the audit.
- Kept resident CUDA explicit through `--expected-integration-engine cuda_resident_stack`; the default audit checks tile/CPU StackEngine integration.
- Added tests for a passing synthetic CPU audit run and a failing legacy/provenance-missing fixture.
- Updated Phase 2 plan and `docs/algorithm_sources.md`.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_stack_engine_contract.py tests/test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\python.exe -m ruff check src/glass/report/stack_engine_contract.py src/glass/cli.py tests/test_stack_engine_contract.py tests/test_cli_smoke.py
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_88_doctor.json
.\.venv\Scripts\glass.exe stack-engine-contract --run "C:\glass_runs\phase2_s2_gate_87_200\auto_triangle_bilinear_tuned_20260601" --scope integration --expected-integration-engine cuda_resident_stack --out runs\checkpoints\s2_gate_88_resident_contract_gate87.json --markdown runs\checkpoints\s2_gate_88_resident_contract_gate87.md
```

## Test Result

- Focused tests: `3 passed in 0.42s`
- Full pytest: `294 passed in 13.11s`
- Ruff: passed
- Native CUDA build: passed, `ninja: no work to do`

## CUDA Availability

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- Native extension loaded: true

Diagnostic JSON:

- `runs/checkpoints/s2_gate_88_doctor.json`

## Real-Data / Preserved Artifact Check

No new 200-light benchmark was run because this gate is diagnostic-only and does not change image math, resident CUDA routing, or output pixels.

The new audit was run against the latest preserved S2-Gate 87 200-light resident artifact:

- Run: `C:\glass_runs\phase2_s2_gate_87_200\auto_triangle_bilinear_tuned_20260601`
- Contract artifact: `runs/checkpoints/s2_gate_88_resident_contract_gate87.json`
- Markdown summary: `runs/checkpoints/s2_gate_88_resident_contract_gate87.md`
- Result: passed for `--scope integration --expected-integration-engine cuda_resident_stack`

## Known Limitations

- The default contract currently audits artifact routing and DQ provenance; it does not recompute image pixels.
- The default expected integration engine is `stack_engine_cpu`; resident CUDA runs must be audited with `--expected-integration-engine cuda_resident_stack`.
- Master calibration checks require `calibration_artifacts.json`; resident-only fast-path runs without tile calibration artifacts should use `--scope integration`.

## Next Step

Continue Phase 2 with the next gate focused on either promoting more resident fused routes with hard numerical evidence or adding a similar explicit contract for remaining DQ/crop/LN artifact invariants.

## Clean-Room Compliance

Compliant. This gate consumes only GLASS-owned JSON artifacts and preserved user-generated benchmark outputs. It does not read, copy, summarize, or rework proprietary source code.
