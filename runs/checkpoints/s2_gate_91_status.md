# S2-Gate 91 Status: Pipeline Contract Reporting

## Gate

S2-Gate 91: Pipeline Contract Reporting

## Completed Content

- Extended `glass report` to consume pipeline invariant contract audit JSON.
- Added auto-discovery for `*pipeline_contract*.json` and `*pipeline-contract*.json` in the run directory.
- Added explicit `glass report --pipeline-contract <path>` override.
- Added a main-report `Pipeline contract audit` section with:
  - pass/fail status
  - source artifact path
  - artifact presence summary for warp, LN, and integration
  - failed checks only
  - integration map policy/path rows
  - local-normalization invariant rows
  - warp invariant rows
- Kept `pipeline_contract.json` as the authoritative artifact; HTML is a readable triage layer.
- Updated `docs/phase2_algorithm_hardening.md` and `docs/algorithm_sources.md`.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py::test_cli_report_summarizes_pipeline_contract tests/test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\python.exe -m ruff check src/glass/report/html_report.py src/glass/cli.py tests/test_cli_smoke.py
.\.venv\Scripts\glass.exe report --run "C:\glass_runs\phase2_s2_gate_87_200\auto_triangle_bilinear_tuned_20260601" --out runs\checkpoints\s2_gate_91_gate87_report.html --pipeline-contract runs\checkpoints\s2_gate_90_pipeline_contract_gate87.json --stack-engine-contract runs\checkpoints\s2_gate_88_resident_contract_gate87.json
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_91_doctor.json
```

## Test Result

- Focused report tests: `2 passed in 0.20s`
- Full pytest: `298 passed in 13.56s`
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

- `runs/checkpoints/s2_gate_91_doctor.json`

## Real-Data / Preserved Artifact Check

No new 200-light benchmark was run because this gate is report-only and does not change image math, output pixels, or resident CUDA routing.

The report was regenerated against the latest preserved S2-Gate 87 200-light resident artifact using the Gate88 StackEngine contract JSON and Gate90 pipeline contract JSON:

- Run: `C:\glass_runs\phase2_s2_gate_87_200\auto_triangle_bilinear_tuned_20260601`
- StackEngine contract: `runs/checkpoints/s2_gate_88_resident_contract_gate87.json`
- Pipeline contract: `runs/checkpoints/s2_gate_90_pipeline_contract_gate87.json`
- Report: `runs/checkpoints/s2_gate_91_gate87_report.html`
- Result: the generated report includes the `Pipeline contract audit` section and shows the Gate90 contract as passed.

## Known Limitations

- The report summarizes pipeline contract JSON; it does not recompute the contract itself.
- Auto-discovery requires a pipeline contract artifact name matching `*pipeline_contract*.json` or `*pipeline-contract*.json`; other names should use `--pipeline-contract`.
- The standalone JSON remains authoritative for automated pass/fail decisions.

## Next Step

Continue Phase 2 by adding optional tiled FITS pixel verification for selected pipeline contract rows, especially LN residual maps and integration count-map consistency.

## Clean-Room Compliance

Compliant. This gate consumes GLASS-owned JSON artifacts and preserved user-generated run outputs only. It does not read, copy, summarize, or rework proprietary source code.
