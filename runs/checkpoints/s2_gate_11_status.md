# S2-Gate 11 Status: Benchmark Contract And Regression Guard

## Gate

S2-Gate 11: codify the Phase 1/2 200-light benchmark recipe as a machine-readable contract and make acceptance audit fail on silent parameter, runtime, coverage, or numerical drift.

## Completed

- Added `benchmarks/phase2_m38_h_200_contract.json`.
- Added `src/glass/report/benchmark_contract.py` for benchmark-contract loading and checks.
- Extended `glass acceptance-audit` with `--benchmark-contract`.
- Contract checks now validate:
  - minimum light/bias/dark/flat counts;
  - minimum active light frames;
  - max runtime versus the release baseline;
  - minimum speedup versus the external reference timing;
  - required run-command tokens, including `--flat-floor 0.05`;
  - required compare scale/offset;
  - required min coverage threshold;
  - RMS/P99/coverage limits.
- Added tests proving the contract passes accepted parameters and fails missing/incorrect benchmark parameters.
- Added S2-Gate 11 to `docs/phase2_algorithm_hardening.md`.
- Updated `docs/algorithm_sources.md`.

## Commands Run

- `.\.venv\Scripts\python.exe -m pytest -q tests\test_acceptance_audit.py`
- `.\.venv\Scripts\python.exe -m ruff check src\glass\report\benchmark_contract.py src\glass\report\acceptance_audit.py src\glass\cli.py tests\test_acceptance_audit.py`
- `.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_10_200\glass_flatfloor005_20260531_183101 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_10_200\glass_flatfloor005_20260531_183101\compare_vs_reference_scaled_coverage190.json --benchmark-contract benchmarks\phase2_m38_h_200_contract.json --out C:\glass_runs\phase2_s2_gate_10_200\glass_flatfloor005_20260531_183101\phase2_contract_acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate_10_200\glass_flatfloor005_20260531_183101\phase2_contract_acceptance_audit.md --min-active-frames 190 --min-speedup 20 --max-rms-diff 0.01 --max-abs-diff-p99 0.01`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_import.py tests\test_cuda_device_info.py tests\test_cuda_smoke.py tests\test_gpu_calibration_vs_cpu.py`

## Test Results

- Focused acceptance tests: `4 passed in 0.27s`.
- Targeted ruff: `All checks passed!`.
- Full pytest: `229 passed in 17.25s`.
- Targeted CUDA pytest: `6 passed in 0.18s`.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU from the accepted S2-Gate 10 doctor artifact: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Real-Data Contract Audit

- Contract: `benchmarks/phase2_m38_h_200_contract.json`.
- Run audited: `C:\glass_runs\phase2_s2_gate_10_200\glass_flatfloor005_20260531_183101`.
- Acceptance JSON: `C:\glass_runs\phase2_s2_gate_10_200\glass_flatfloor005_20260531_183101\phase2_contract_acceptance_audit.json`.
- Acceptance Markdown: `C:\glass_runs\phase2_s2_gate_10_200\glass_flatfloor005_20260531_183101\phase2_contract_acceptance_audit.md`.
- Status: passed.
- GLASS runtime: `39.01369709987193 s`.
- Release baseline runtime: `30.361440100008622 s`.
- Max allowed runtime by contract: `39.46987213001121 s`.
- External reference runtime: `1092.541 s`.
- Speedup vs external reference: `28.004036561907544x`.
- Active light frames: `193`.
- Coverage fraction: `0.9574594492889027`.
- Coverage threshold token and compare threshold: `min_coverage=190`.
- Scaled RMS: `0.0015580353573173447`.
- Scaled P99 absolute difference: `0.0004309411160647869`.

## Known Limitations

- This contract is specific to the M38 H-alpha 200-light benchmark and must be versioned if the dataset, reference, or accepted recipe changes.
- The runtime envelope is intentionally narrow enough to catch drift but still allows the current editable tree's slower 39-second run. The next optimization target remains returning closer to the 30-second release baseline.
- The contract validates existing artifacts; it does not itself execute the benchmark.
- The resident CUDA path remains a specialized high-VRAM path and is not yet the shared StackEngine implementation.

## Next Step

Use the contract as the guardrail while optimizing resident master preparation, read/decode/upload overlap, and registration/warp scheduling. A future gate should either recover the 200-light runtime toward the 30-second release baseline or record a stronger explanation backed by fine timing.

## Clean-Room Compliance

Compliant. The contract consumes GLASS artifacts, command records, user-generated benchmark/reference outputs, and numeric thresholds derived from Phase 1/2 measurements. No proprietary implementation source was read, copied, summarized, or reworked.
