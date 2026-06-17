# S2-Gate 199 Status: Acceptance Audit Contract Bundle Ingestion

## Gate

- Gate: S2-Gate 199
- Scope: let `glass acceptance-audit` consume the Gate198 guardrails
  `acceptance_contract_bundle.json` directly.
- Status: green
- Date: 2026-06-18

## Completed

- Added `glass acceptance-audit --contract-bundle`.
- `build_acceptance_audit()` now accepts `contract_bundle_json`.
- A contract bundle supplies `pipeline_contract_json` and
  `stack_engine_contract_json` from its `artifacts` or
  `acceptance_audit_argument_map`.
- Explicit `--pipeline-contract-json` and `--stack-engine-contract-json`
  remain higher priority than bundle-provided paths.
- Acceptance audit JSON now records `contract_bundle` evidence.
- Acceptance audit Markdown now reports contract-bundle status.
- Missing or wrong-type bundle paths fail clearly via
  `contract_bundle_present` and `contract_bundle_type` checks.
- Added API and CLI tests for bundle ingestion, explicit override behavior, and
  missing-bundle failure.
- Updated `docs/phase2_algorithm_hardening.md`.

## Commands Run

```powershell
.\.venv\Scripts\ruff.exe check src\glass\report\acceptance_audit.py src\glass\cli.py tests\test_acceptance_audit.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_acceptance_audit.py::test_acceptance_audit_accepts_contract_bundle tests\test_acceptance_audit.py::test_acceptance_audit_explicit_contract_paths_override_bundle tests\test_acceptance_audit.py::test_acceptance_audit_fails_missing_contract_bundle tests\test_acceptance_audit.py::test_acceptance_audit_cli_accepts_contract_bundle
$root='C:\glass_runs\phase2_s2_gate_199_acceptance_bundle_ingestion'
Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $root | Out-Null
$wbpp = @{ elapsed_s = 10.0; dataset = 'synthetic_bundle_ingestion_fixture' }
$wbpp | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $root 'wbpp_result.json') -Encoding UTF8
$compare = @{
  shape_match = $true
  rms_diff = 0.001
  abs_diff_p99 = 0.002
  coverage_fraction = 1.0
  candidate_transform = @{ applied = $false; scale = $null; offset = $null; clip_low = $null; clip_high = $null }
  comparison_region = @{ coverage_fraction = 1.0; compared_pixels = 1024; min_coverage = 2.0 }
}
$compare | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $root 'compare.json') -Encoding UTF8
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate_198_guardrails_contract_bundle\run\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_198_guardrails_contract_bundle\run --wbpp-result (Join-Path $root 'wbpp_result.json') --compare-json (Join-Path $root 'compare.json') --contract-bundle C:\glass_runs\phase2_s2_gate_198_guardrails_contract_bundle\guardrails\acceptance_contract_bundle.json --out (Join-Path $root 'acceptance_audit_bundle.json') --markdown (Join-Path $root 'acceptance_audit_bundle.md') --min-lights 1 --min-bias 1 --min-dark 1 --min-flat 1 --min-active-frames 2 --min-speedup 2 --min-coverage-fraction 0.95 --max-rms-diff 0.01 --max-abs-diff-p99 0.01
Copy-Item -LiteralPath (Join-Path $root 'acceptance_audit_bundle.json') -Destination runs\checkpoints\s2_gate_199_acceptance_audit_bundle.json -Force
Copy-Item -LiteralPath (Join-Path $root 'acceptance_audit_bundle.md') -Destination runs\checkpoints\s2_gate_199_acceptance_audit_bundle.md -Force
Copy-Item -LiteralPath (Join-Path $root 'wbpp_result.json') -Destination runs\checkpoints\s2_gate_199_wbpp_fixture.json -Force
Copy-Item -LiteralPath (Join-Path $root 'compare.json') -Destination runs\checkpoints\s2_gate_199_compare_fixture.json -Force
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor --allow-cpu-only
```

## Test Results

- Focused ruff: passed.
- Focused pytest: `5 passed in 1.13s`.
- Full ruff: passed.
- Full pytest: `478 passed in 25.84s`.

## Artifact Result

- External root:
  `C:\glass_runs\phase2_s2_gate_199_acceptance_bundle_ingestion`
- Acceptance audit status: `passed`.
- Acceptance audit speedup vs fixture WBPP timing: `25.484992143062193`.
- Contract bundle check: `contract_bundle_present=true`,
  `contract_bundle_type=true`.
- Pipeline contract: `passed`.
- StackEngine contract: `passed`.
- StackEngine default promotion: `ready=true`.
- Markdown includes `Contract bundle: passed`.

## Checkpoint Artifacts

- `runs\checkpoints\s2_gate_199_acceptance_audit_bundle.json`
- `runs\checkpoints\s2_gate_199_acceptance_audit_bundle.md`
- `runs\checkpoints\s2_gate_199_wbpp_fixture.json`
- `runs\checkpoints\s2_gate_199_compare_fixture.json`

## CUDA Status

- CUDA compute code was not changed in this gate.
- CUDA remains optional.
- `glass doctor --allow-cpu-only` reports CUDA wrapper importable, native
  extension loaded, and CUDA available.
- GPU 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition, compute capability
  12.0, VRAM 97886 MiB, driver 596.21.

## Known Limitations

- This gate did not rerun the 200-light benchmark.
- The WBPP timing and compare JSON used here are small fixture artifacts to
  validate bundle ingestion, not a real PixInsight/WBPP performance claim.
- Real release acceptance still needs the 200-light manifest, real WBPP result,
  real compare JSON, benchmark contract, and the generated contract bundle.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source was read, copied, summarized, or reworked.
- The gate consumed GLASS synthetic-run artifacts plus fixture black-box timing
  and comparison JSON.
- No original image directory was modified.

## Next Step

- Run the same `--contract-bundle` acceptance flow against the 200-light
  benchmark artifacts so StackEngine, pipeline, DQ, benchmark, and comparison
  evidence are verified together.
