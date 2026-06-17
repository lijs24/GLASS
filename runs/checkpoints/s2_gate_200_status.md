# S2-Gate 200 Status: Real 200-Light Bundle Acceptance

## Gate

- Gate: S2-Gate 200
- Scope: close the Gate198/199 contract-bundle flow on the real M38 H-alpha
  200-light resident CUDA benchmark.
- Status: green
- Date: 2026-06-18

## Completed

- Extended `glass guardrails` with:
  - `--resident-calibration-contract-json`
  - `--resident-result-contract-json`
- Guardrails now passes those resident contract payloads into
  `build_stack_engine_contract_audit()`.
- Guardrails summary and acceptance contract bundle now record resident
  contract input paths and attachment status.
- Rebuilt guardrails for the Gate181 real 200-light resident CUDA default run.
- Ran `glass acceptance-audit --contract-bundle` against the real M38 H-alpha
  200-light benchmark artifacts and formal benchmark contract.
- Mirrored guardrails, contract bundle, StackEngine contract, pipeline contract,
  HTML report, and acceptance audit artifacts into `runs\checkpoints`.
- Updated `docs/phase2_algorithm_hardening.md`.

## Commands Run

```powershell
.\.venv\Scripts\ruff.exe check src\glass\cli.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_cli_guardrails_generates_contracts_and_report tests\test_cli_smoke.py::test_cli_help_commands
$root='C:\glass_runs\phase2_s2_gate_200_real_bundle_acceptance'
$guard=Join-Path $root 'guardrails'
Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $guard | Out-Null
.\.venv\Scripts\glass.exe guardrails --run C:\glass_runs\phase2_s2_gate_181_default_runtime\default_resident --out-dir $guard --expected-integration-engine cuda_resident_stack --resident-calibration-contract-json C:\glass_runs\phase2_s2_gate_181_default_runtime\resident_calibration_contract.json --resident-result-contract-json C:\glass_runs\phase2_s2_gate_181_default_runtime\resident_result_contract.json --require-stack-default-ready --pixel-verify --pixel-verify-tile-size 2048
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate_181_default_runtime\default_resident\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_181_default_runtime\default_resident --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_181_default_runtime\default_vs_reference.json --benchmark-contract benchmarks\phase2_m38_h_200_contract.json --contract-bundle C:\glass_runs\phase2_s2_gate_200_real_bundle_acceptance\guardrails\acceptance_contract_bundle.json --out (Join-Path $root 'acceptance_real_bundle.json') --markdown (Join-Path $root 'acceptance_real_bundle.md')
Copy-Item -LiteralPath (Join-Path $guard 'guardrails_summary.json') -Destination runs\checkpoints\s2_gate_200_guardrails_summary.json -Force
Copy-Item -LiteralPath (Join-Path $guard 'acceptance_contract_bundle.json') -Destination runs\checkpoints\s2_gate_200_acceptance_contract_bundle.json -Force
Copy-Item -LiteralPath (Join-Path $guard 'stack_engine_contract.json') -Destination runs\checkpoints\s2_gate_200_stack_engine_contract.json -Force
Copy-Item -LiteralPath (Join-Path $guard 'pipeline_contract.json') -Destination runs\checkpoints\s2_gate_200_pipeline_contract.json -Force
Copy-Item -LiteralPath (Join-Path $guard 'stack_engine_contract.md') -Destination runs\checkpoints\s2_gate_200_stack_engine_contract.md -Force
Copy-Item -LiteralPath (Join-Path $guard 'pipeline_contract.md') -Destination runs\checkpoints\s2_gate_200_pipeline_contract.md -Force
Copy-Item -LiteralPath (Join-Path $guard 'report.html') -Destination runs\checkpoints\s2_gate_200_guardrails_report.html -Force
Copy-Item -LiteralPath (Join-Path $root 'acceptance_real_bundle.json') -Destination runs\checkpoints\s2_gate_200_acceptance_real_bundle.json -Force
Copy-Item -LiteralPath (Join-Path $root 'acceptance_real_bundle.md') -Destination runs\checkpoints\s2_gate_200_acceptance_real_bundle.md -Force
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor --allow-cpu-only
```

## Test Results

- Focused ruff: passed.
- Focused pytest: `2 passed in 1.31s`.
- Full ruff: passed.
- Full pytest: `478 passed in 25.88s`.

## Real 200-Light Result

- External root:
  `C:\glass_runs\phase2_s2_gate_200_real_bundle_acceptance`
- Source run:
  `C:\glass_runs\phase2_s2_gate_181_default_runtime\default_resident`
- Benchmark contract:
  `benchmarks\phase2_m38_h_200_contract.json`
- WBPP black-box result:
  `C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json`
- Compare JSON:
  `C:\glass_runs\phase2_s2_gate_181_default_runtime\default_vs_reference.json`
- Guardrails status: `passed`.
- Acceptance audit status: `passed`.
- Speedup versus WBPP: `58.099101701945926x`.
- Frame counts: `light=200`, `bias=20`, `dark=20`, `flat=20`.
- Active integrated frames: `193`.
- Coverage fraction: `0.9577924192878646`.
- RMS diff: `0.0014945534429799121`.
- abs diff p99: `0.00043544556712731865`.
- Contract bundle: `passed`.
- Pipeline contract: `passed`.
- StackEngine contract: `passed`.
- StackEngine default promotion: `ready=true`.
- Resident calibration contract attached: `true`.
- Resident result contract attached: `true`.
- DQ provenance records: `2`.

## Checkpoint Artifacts

- `runs\checkpoints\s2_gate_200_guardrails_summary.json`
- `runs\checkpoints\s2_gate_200_acceptance_contract_bundle.json`
- `runs\checkpoints\s2_gate_200_stack_engine_contract.json`
- `runs\checkpoints\s2_gate_200_pipeline_contract.json`
- `runs\checkpoints\s2_gate_200_stack_engine_contract.md`
- `runs\checkpoints\s2_gate_200_pipeline_contract.md`
- `runs\checkpoints\s2_gate_200_guardrails_report.html`
- `runs\checkpoints\s2_gate_200_acceptance_real_bundle.json`
- `runs\checkpoints\s2_gate_200_acceptance_real_bundle.md`

## CUDA Status

- CUDA compute code was not changed in this gate.
- The validated real run is the existing resident CUDA 200-light run from
  Gate181.
- CUDA remains optional for CPU-only installs and tests.
- `glass doctor --allow-cpu-only` reports CUDA wrapper importable, native
  extension loaded, and CUDA available.
- GPU 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition, compute capability
  12.0, VRAM 97886 MiB, driver 596.21.

## Known Limitations

- This gate reuses the existing Gate181 real 200-light run rather than
  recomputing the full stack.
- Performance evidence is therefore a bundled revalidation of existing output
  artifacts, not a new wall-clock processing run.
- The acceptance audit reports a performance-regression warning for output
  write policy diagnostics, while the formal acceptance status still passes and
  runtime is below the benchmark contract maximum.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source was read, copied, summarized, or reworked.
- The gate consumed GLASS run artifacts, GLASS contracts, GLASS comparison
  output, and user-generated WBPP black-box timing/output metadata only.
- No original image directory was modified.

## Next Step

- Use this Gate200 bundled acceptance artifact as the release/default guardrail
  evidence for future runtime or packaging promotion decisions.
