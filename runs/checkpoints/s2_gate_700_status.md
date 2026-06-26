# S2 Gate 700 Status

Date: 2026-06-26
Branch: `main`
Status: green

## Gate

S2-Gate 700: Mainline active-coverage gate.

## Completed

- Added a shared `resident_active_coverage_contract` report helper that reads
  resident `integration_results.json` outputs and validates applicable
  `stack_engine_surface_contract` checks.
- Wired the helper into `phase2-mainline-audit` as the required check
  `resident_active_coverage_stack_surface_contract`.
- Wired the helper into `phase2-mainline-ab` as the required check
  `candidate_active_coverage_stack_surface_contract`.
- Preserved source-DQ-only and other small validation paths by marking outputs
  without coverage/weight-map support as not applicable, while full audit-map
  resident outputs remain hard-gated.
- Updated mainline A/B, mainline audit, and resident framework tests and
  fixtures.

## Commands Run

- `.\.venv\Scripts\python.exe -m pytest -q tests/test_phase2_mainline_ab.py tests/test_phase2_mainline_audit.py`
- `.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate699_resident_surface_active_coverage\runs_20260627_100000\active_coverage_contract_candidate --out C:\glass_runs\phase2_s2_gate700_active_coverage_gate\gate700_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate700_active_coverage_gate\gate700_mainline_audit.md`
- `.\.venv\Scripts\glass.exe phase2-mainline-ab --baseline-run C:\glass_runs\phase2_s2_gate698_default_prestart\runs_20260627_090000\default_prestart_candidate --candidate-run C:\glass_runs\phase2_s2_gate699_resident_surface_active_coverage\runs_20260627_100000\active_coverage_contract_candidate --out C:\glass_runs\phase2_s2_gate700_active_coverage_gate\gate700_vs_gate698_ab.json --markdown C:\glass_runs\phase2_s2_gate700_active_coverage_gate\gate700_vs_gate698_ab.md`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_phase2_mainline_ab.py tests/test_phase2_mainline_audit.py tests/test_resident_mainline_framework.py tests/test_resident_cuda_run.py::test_cli_resident_cuda_triangle_source_dq_feeds_registration_runtime_contract tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_generates_source_dq_cache_route`
- `.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate699_resident_surface_active_coverage\runs_20260627_100000\active_coverage_contract_candidate --out C:\glass_runs\phase2_s2_gate700_active_coverage_gate\gate700_mainline_audit_v2.json --markdown C:\glass_runs\phase2_s2_gate700_active_coverage_gate\gate700_mainline_audit_v2.md`
- `.\.venv\Scripts\glass.exe phase2-mainline-ab --baseline-run C:\glass_runs\phase2_s2_gate698_default_prestart\runs_20260627_090000\default_prestart_candidate --candidate-run C:\glass_runs\phase2_s2_gate699_resident_surface_active_coverage\runs_20260627_100000\active_coverage_contract_candidate --out C:\glass_runs\phase2_s2_gate700_active_coverage_gate\gate700_vs_gate698_ab_v2.json --markdown C:\glass_runs\phase2_s2_gate700_active_coverage_gate\gate700_vs_gate698_ab_v2.md`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Initial focused mainline audit/A-B tests: passed.
- Focused mainline/framework/source-DQ regression tests after scope fix:
  `33 passed`.
- Full pytest: `1448 passed in 70.49 s`.

## Real 200-Light Result

- Candidate run:
  `C:\glass_runs\phase2_s2_gate699_resident_surface_active_coverage\runs_20260627_100000\active_coverage_contract_candidate`
- Mainline audit:
  `C:\glass_runs\phase2_s2_gate700_active_coverage_gate\gate700_mainline_audit_v2.json`
- A/B versus Gate698:
  `C:\glass_runs\phase2_s2_gate700_active_coverage_gate\gate700_vs_gate698_ab_v2.json`
- Audit passed: `True`.
- New audit active/coverage check passed: `True`.
- A/B passed: `True`.
- A/B active/coverage contract status: `passed`.
- Elapsed ratio: `0.9818270795336204`.
- Hash mismatch/missing counts: `0 / 0`.

## CUDA

- CUDA was available for the real validation run.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- This gate did not require a native CUDA rebuild because it changes Python
  report/guardrail logic and tests only.

## Known Limitations

- This is a mainline gate-enforcement change, not a new speed optimization.
- Source-DQ-only paths without coverage/weight-map surface support are marked
  not applicable for this specific active/coverage gate; they remain covered by
  their source-DQ propagation checks.
- No science pixels, CUDA kernels, calibration math, registration, local
  normalization, rejection thresholds, or integration math changed.

## Next Step

S2-Gate 701 should return to measured runtime or algorithm work, preferably a
resident registration/warp batching improvement or a larger resident reducer
architecture change with real 200-light A/B evidence.

## Clean-Room

Compliant. The gate is derived from GLASS-owned resident artifacts, DQ/mask
contracts, tests, and user-owned 200-light benchmark outputs. It does not
inspect, copy, summarize, or rework external proprietary implementation source,
and it does not modify input image directories.
