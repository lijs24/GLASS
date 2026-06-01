# S2-Gate 90 Status: Pipeline Invariant Contract Audit

## Gate

S2-Gate 90: Pipeline Invariant Contract Audit

## Completed Content

- Added `glass pipeline-contract`, a standalone audit command for structural pipeline invariants.
- Added `src/glass/report/pipeline_contract.py` to audit:
  - integration output map paths and output-map policy
  - rejection low/high map availability or explicit policy skip
  - integration DQ map summaries and normalized DQ provenance summaries
  - local-normalization crop-box recording, coefficient-grid artifacts, DQ records, normalized paths, and coverage paths
  - warp registered paths, coverage maps, DQ maps, DQ summaries, and explained skipped-frame records
- Added JSON and optional Markdown outputs.
- Added focused tests for:
  - a passing synthetic CPU audit run
  - a failing fixture with missing maps and missing LN crop/DQ records
- Updated `docs/phase2_algorithm_hardening.md` and `docs/algorithm_sources.md`.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_pipeline_contract.py tests/test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\python.exe -m ruff check src/glass/report/pipeline_contract.py src/glass/cli.py tests/test_pipeline_contract.py tests/test_cli_smoke.py
.\.venv\Scripts\glass.exe pipeline-contract --run "C:\glass_runs\phase2_s2_gate_87_200\auto_triangle_bilinear_tuned_20260601" --out runs\checkpoints\s2_gate_90_pipeline_contract_gate87.json --markdown runs\checkpoints\s2_gate_90_pipeline_contract_gate87.md
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_90_doctor.json
```

## Test Result

- Focused tests: `3 passed in 0.38s`
- Full pytest: `297 passed in 13.53s`
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

- `runs/checkpoints/s2_gate_90_doctor.json`

## Real-Data / Preserved Artifact Check

No new 200-light benchmark was run because this gate is artifact-contract only and does not change image math, output pixels, or resident CUDA routing.

The new pipeline invariant contract was run against the latest preserved S2-Gate 87 200-light resident artifact:

- Run: `C:\glass_runs\phase2_s2_gate_87_200\auto_triangle_bilinear_tuned_20260601`
- Contract artifact: `runs/checkpoints/s2_gate_90_pipeline_contract_gate87.json`
- Markdown summary: `runs/checkpoints/s2_gate_90_pipeline_contract_gate87.md`
- Result: passed

The audit confirms that the resident minimal-output policy is explicit rather than silent: master output exists, skipped diagnostic maps are policy-recorded, and DQ provenance remains represented through the resident summary contract.

## Known Limitations

- The contract verifies artifact presence and schema-level invariants; it does not compare image pixels.
- The current audit treats absent warp or LN artifacts as allowed for resident fast-path runs, while validating them when present.
- The contract is intentionally policy-aware for resident output-map modes, so minimal/science runs can pass when skipped maps are explicitly recorded.

## Next Step

Consider adding a report section for `pipeline-contract` artifacts, or extend the contract with optional tiled FITS pixel verification for LN residual and integration map consistency.

## Clean-Room Compliance

Compliant. This gate consumes GLASS-owned artifacts and preserved user-generated run outputs only. It does not read, copy, summarize, or rework proprietary source code.
