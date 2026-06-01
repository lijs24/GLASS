# S2-Gate 92 Status: Pipeline Contract Pixel Verification

## Gate

S2-Gate 92: Pipeline Contract Pixel Verification

## Completed Content

- Added explicit `glass pipeline-contract --pixel-verify`.
- Added `--pixel-verify-tile-size` and `--pixel-tolerance`.
- Pipeline contract can now read integration DQ, coverage, low-rejection, and
  high-rejection FITS maps in tiles.
- DQ map pixel counts are compared with integration `dq_summary` counts.
- Coverage zero-or-less pixels are compared with DQ `no_data` counts.
- Rejection-map positive pixels are compared with DQ `low_rejected` and
  `high_rejected` counts.
- Policy-skipped or not-required maps are recorded as explicit passable states
  instead of implicit missing data.
- HTML reports now surface pipeline-contract pixel verification rows.
- Added passing synthetic CPU audit coverage and a failing corrupted-summary
  FITS fixture.
- Updated Phase 2 gate documentation and algorithm source tracking.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_pipeline_contract.py tests/test_cli_smoke.py::test_cli_report_summarizes_pipeline_contract tests/test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\python.exe -m ruff check src/glass/report/pipeline_contract.py src/glass/cli.py src/glass/report/html_report.py tests/test_pipeline_contract.py tests/test_cli_smoke.py
.\.venv\Scripts\glass.exe pipeline-contract --run "C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531" --out runs\checkpoints\s2_gate_92_pipeline_contract_gate32_pixel.json --markdown runs\checkpoints\s2_gate_92_pipeline_contract_gate32_pixel.md --pixel-verify --pixel-verify-tile-size 4096
.\.venv\Scripts\glass.exe report --run "C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531" --out runs\checkpoints\s2_gate_92_gate32_report.html --pipeline-contract runs\checkpoints\s2_gate_92_pipeline_contract_gate32_pixel.json
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_92_doctor.json
.\.venv\Scripts\glass.exe pipeline-contract --help
```

## Test Results

- Focused pytest: 6 passed.
- Full pytest: 300 passed in 13.76 s.
- Ruff: passed.
- Native CUDA build: passed, no rebuild needed.
- `glass doctor`: passed.

## CUDA Status

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Real Artifact Verification

- Preserved 200-light audit-map run:
  `C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531`
- Pixel-verification contract:
  `runs/checkpoints/s2_gate_92_pipeline_contract_gate32_pixel.json`
- Markdown summary:
  `runs/checkpoints/s2_gate_92_pipeline_contract_gate32_pixel.md`
- Regenerated HTML report:
  `runs/checkpoints/s2_gate_92_gate32_report.html`
- Result: passed. DQ, coverage, low-rejection, and high-rejection map pixel
  verification rows are all recorded as `verified` and `ok`.

## Known Limitations

- Pixel verification is explicit because large real maps add audit I/O.
- This gate verifies selected integration map invariants. It does not prove
  every stage-level DQ transition or full numerical equivalence.
- Gate87 minimal-output artifacts intentionally skip most maps; Gate32
  audit-map artifacts were used for real pixel verification because they retain
  the required FITS maps.

## Next Step

Use these stronger artifact checks before promoting additional resident CUDA
optimization or fused integration defaults. A good next gate is to add a report
summary that expands failed pixel mismatches into compact per-flag deltas, or to
resume performance work with pixel-verification guardrails enabled.

## Clean-Room Compliance

Compliant. This gate reads only GLASS-owned JSON/FITS artifacts and uses
project-defined DQ/output-map invariants. It does not read, copy, summarize, or
rework any proprietary implementation source.
