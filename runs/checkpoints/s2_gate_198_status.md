# S2-Gate 198 Status: Guardrails Acceptance Contract Bundle

## Gate

- Gate: S2-Gate 198
- Scope: make `glass guardrails` emit a reusable acceptance-audit contract
  bundle so StackEngine and pipeline contract paths are carried as one audited
  artifact.
- Status: green
- Date: 2026-06-18

## Completed

- Extended `glass guardrails` to write
  `acceptance_contract_bundle.json` beside `guardrails_summary.json`.
- Added the bundle path to `guardrails_summary.json`.
- The bundle records:
  - StackEngine contract JSON/Markdown.
  - Pipeline contract JSON/Markdown.
  - Guardrails summary and HTML report paths.
  - Pixel verification policy.
  - StackEngine default-promotion requirement and result.
  - Acceptance-audit argument vector for `--pipeline-contract-json` and
    `--stack-engine-contract-json`.
- Preserved existing guardrail pass/fail behavior; the bundle is diagnostic
  evidence and does not make a failing guardrail pass.
- Added CLI smoke assertions for the new bundle contract.
- Updated `docs/phase2_algorithm_hardening.md`.

## Commands Run

```powershell
.\.venv\Scripts\ruff.exe check src\glass\cli.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_cli_guardrails_generates_contracts_and_report tests\test_pipeline_contract.py::test_pipeline_contract_passes_for_cpu_audit_run tests\test_stack_engine_contract.py::test_stack_engine_contract_passes_for_cpu_audit_run
$root='C:\glass_runs\phase2_s2_gate_198_guardrails_contract_bundle'
$data=Join-Path $root 'synthetic'
$run=Join-Path $root 'run'
$guard=Join-Path $root 'guardrails'
Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $root | Out-Null
.\.venv\Scripts\glass.exe synthetic --out $data --frames 4 --width 32 --height 32 --filter H --known-shift
.\.venv\Scripts\glass.exe audit --root $data --out $run --backend cpu --tile-size 8
.\.venv\Scripts\glass.exe guardrails --run $run --out-dir $guard --expected-integration-engine stack_engine_cpu --require-stack-default-ready --pixel-verify --pixel-verify-tile-size 8
Copy-Item -LiteralPath (Join-Path $guard 'guardrails_summary.json') -Destination runs\checkpoints\s2_gate_198_guardrails_summary.json -Force
Copy-Item -LiteralPath (Join-Path $guard 'acceptance_contract_bundle.json') -Destination runs\checkpoints\s2_gate_198_acceptance_contract_bundle.json -Force
Copy-Item -LiteralPath (Join-Path $guard 'stack_engine_contract.json') -Destination runs\checkpoints\s2_gate_198_stack_engine_contract.json -Force
Copy-Item -LiteralPath (Join-Path $guard 'pipeline_contract.json') -Destination runs\checkpoints\s2_gate_198_pipeline_contract.json -Force
Copy-Item -LiteralPath (Join-Path $guard 'stack_engine_contract.md') -Destination runs\checkpoints\s2_gate_198_stack_engine_contract.md -Force
Copy-Item -LiteralPath (Join-Path $guard 'pipeline_contract.md') -Destination runs\checkpoints\s2_gate_198_pipeline_contract.md -Force
Copy-Item -LiteralPath (Join-Path $guard 'report.html') -Destination runs\checkpoints\s2_gate_198_guardrails_report.html -Force
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor --allow-cpu-only
```

## Test Results

- Focused ruff: passed.
- Focused pytest: `3 passed in 0.93s`.
- Full ruff: passed.
- Full pytest: `474 passed in 25.45s`.

## Artifact Result

- External root:
  `C:\glass_runs\phase2_s2_gate_198_guardrails_contract_bundle`
- Guardrails status: `passed`.
- Bundle artifact type: `glass_acceptance_contract_bundle`.
- Bundle passed: `true`.
- StackEngine contract: `passed`.
- Pipeline contract: `passed`.
- StackEngine default promotion: `ready=true`.
- Acceptance argument vector:
  `--pipeline-contract-json <pipeline_contract.json> --stack-engine-contract-json <stack_engine_contract.json>`.

## Checkpoint Artifacts

- `runs\checkpoints\s2_gate_198_guardrails_summary.json`
- `runs\checkpoints\s2_gate_198_acceptance_contract_bundle.json`
- `runs\checkpoints\s2_gate_198_stack_engine_contract.json`
- `runs\checkpoints\s2_gate_198_pipeline_contract.json`
- `runs\checkpoints\s2_gate_198_stack_engine_contract.md`
- `runs\checkpoints\s2_gate_198_pipeline_contract.md`
- `runs\checkpoints\s2_gate_198_guardrails_report.html`

## CUDA Status

- No CUDA compute path was changed in this gate.
- CUDA remains optional.
- `glass doctor --allow-cpu-only` reports CUDA wrapper importable, native
  extension loaded, and CUDA available.
- GPU 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition, compute capability
  12.0, VRAM 97886 MiB, driver 596.21.
- The Gate198 real artifact used CPU backend intentionally to validate
  StackEngine and pipeline contracts without consuming GPU time.

## Known Limitations

- This gate did not rerun the 200-light benchmark.
- The contract bundle records the paths produced by the guardrails run; the
  checkpoint copies are mirrors for audit/review.
- The bundle does not replace the acceptance audit. It supplies audited
  arguments that the acceptance audit can consume.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source was read, copied, summarized, or reworked.
- The synthetic dataset and generated GLASS artifacts are local project outputs.
- No original image directory was modified.

## Next Step

- Use the bundle in a real 200-light guardrail/acceptance run so benchmark
  contract, StackEngine contract, pipeline contract, and DQ evidence travel
  together through release acceptance.
