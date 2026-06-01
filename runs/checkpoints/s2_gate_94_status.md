# S2-Gate 94 Status: Run Guardrail Bundle

## Gate

S2-Gate 94: Run Guardrail Bundle

## Completed Content

- Added `glass guardrails`.
- The command writes a review bundle for an existing GLASS run:
  - `stack_engine_contract.json`
  - `stack_engine_contract.md`
  - `pipeline_contract.json`
  - `pipeline_contract.md`
  - `guardrails_summary.json`
  - `report.html`
- The bundle can enable `pipeline-contract --pixel-verify` internally.
- The bundle supports `--expected-integration-engine stack_engine_cpu`,
  `cuda_resident_stack`, or `any`.
- The bundle supports `--stack-scope all|calibration|integration`, which lets
  older resident artifacts that lack calibration JSON still be guarded at the
  integration/pipeline-map layer.
- The command returns exit code 2 if either contract fails, making it usable as
  a regression guard before and after resident CUDA optimization work.
- Added focused CLI tests and help coverage.
- Updated Phase 2 documentation and algorithm source tracking.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py::test_cli_guardrails_generates_contracts_and_report tests/test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\python.exe -m ruff check src/glass/cli.py tests/test_cli_smoke.py docs/algorithm_sources.md docs/phase2_algorithm_hardening.md
.\.venv\Scripts\glass.exe guardrails --run "C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531" --out-dir runs\checkpoints\s2_gate_94_guardrails_gate32 --stack-scope integration --expected-integration-engine cuda_resident_stack --pixel-verify --pixel-verify-tile-size 4096
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_94_doctor.json
```

## Test Results

- Focused pytest: 2 passed.
- Full pytest: 301 passed in 14.06 s.
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
- Guardrail bundle:
  `runs/checkpoints/s2_gate_94_guardrails_gate32/`
- Result: passed with `--stack-scope integration`,
  `--expected-integration-engine cuda_resident_stack`, and `--pixel-verify`.
- Bundle artifacts:
  - `runs/checkpoints/s2_gate_94_guardrails_gate32/guardrails_summary.json`
  - `runs/checkpoints/s2_gate_94_guardrails_gate32/stack_engine_contract.json`
  - `runs/checkpoints/s2_gate_94_guardrails_gate32/pipeline_contract.json`
  - `runs/checkpoints/s2_gate_94_guardrails_gate32/report.html`

## Known Limitations

- This gate orchestrates existing audits and report generation. It does not add
  new image-math checks beyond the underlying contracts.
- Older resident-only artifacts may not contain `calibration_artifacts.json`;
  use `--stack-scope integration` for those runs and retain full `all` scope for
  complete CPU/tile runs.
- No new 200-light benchmark was run because this gate does not change CUDA
  kernels, image math, accepted frames, or pipeline routing.

## Next Step

Use `glass guardrails` before and after the next resident CUDA performance gate.
The next performance-focused gate can now fail fast if it breaks StackEngine
routing, DQ/pipeline contracts, or integration output-map pixel consistency.

## Clean-Room Compliance

Compliant. This gate only orchestrates GLASS-owned audit/report artifacts and
does not read, copy, summarize, or rework any proprietary implementation source.
