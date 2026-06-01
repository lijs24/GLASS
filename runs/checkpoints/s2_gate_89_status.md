# S2-Gate 89 Status: StackEngine Contract Reporting

## Gate

S2-Gate 89: StackEngine Contract Reporting

## Completed Content

- Extended `glass report` to consume StackEngine contract audit JSON.
- Added auto-discovery for `*stack_engine_contract*.json` and `*stack-engine-contract*.json` in the run directory.
- Added explicit `glass report --stack-engine-contract <path>` override.
- Added a main-report `StackEngine contract audit` section with:
  - pass/fail status
  - audit source path
  - audit scope
  - expected integration engine
  - failed checks only
  - audited master calibration and integration surfaces
- Kept `stack_engine_contract.json` as the authoritative artifact; HTML is a readable triage layer.
- Updated `docs/phase2_algorithm_hardening.md` and `docs/algorithm_sources.md`.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py::test_cli_report_summarizes_stack_engine_contract tests/test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\python.exe -m ruff check src/glass/report/html_report.py src/glass/cli.py tests/test_cli_smoke.py
.\.venv\Scripts\glass.exe report --run "C:\glass_runs\phase2_s2_gate_87_200\auto_triangle_bilinear_tuned_20260601" --out runs\checkpoints\s2_gate_89_gate87_report.html --stack-engine-contract runs\checkpoints\s2_gate_88_resident_contract_gate87.json
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_89_doctor.json
```

## Test Result

- Focused report tests: `2 passed in 0.20s`
- Full pytest: `295 passed in 13.39s`
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

- `runs/checkpoints/s2_gate_89_doctor.json`

## Real-Data / Preserved Artifact Check

No new 200-light benchmark was run because this gate is report-only and does not change image math, output artifacts, or resident CUDA routing.

The report was regenerated against the latest preserved S2-Gate 87 200-light resident artifact using the Gate88 contract JSON:

- Run: `C:\glass_runs\phase2_s2_gate_87_200\auto_triangle_bilinear_tuned_20260601`
- Contract: `runs/checkpoints/s2_gate_88_resident_contract_gate87.json`
- Report: `runs/checkpoints/s2_gate_89_gate87_report.html`
- Result: the generated report includes the `StackEngine contract audit` section and shows the resident integration contract as passed for `cuda_resident_stack`.

## Known Limitations

- The report summarizes contract audit JSON; it does not recompute the contract itself.
- Auto-discovery requires a stack-engine contract artifact name matching `*stack_engine_contract*.json` or `*stack-engine-contract*.json`; other names should use `--stack-engine-contract`.
- The standalone JSON remains authoritative for automated pass/fail decisions.

## Next Step

Continue Phase 2 by turning more of the DQ/LN/rejection invariants into machine-readable contracts, or by resuming resident fused-route optimization with a 200-light A/B benchmark when image math changes.

## Clean-Room Compliance

Compliant. This gate consumes GLASS-owned JSON artifacts and preserved user-generated run outputs only. It does not read, copy, summarize, or rework proprietary source code.
