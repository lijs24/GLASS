# Acceptance Audit CLI Status

## Scope

Validation/Gate 13 increment: make the final real-data acceptance audit
reproducible from existing artifacts instead of relying on a hand-written
checklist.

## Completed

- Added `gpwbpp acceptance-audit`.
- The command reads:
  - benchmark `manifest.json`;
  - GPWBPP run directory;
  - user-generated PixInsight/WBPP black-box result JSON;
  - compare JSON.
- It verifies configurable acceptance checks:
  - minimum light, bias, dark, and flat counts;
  - minimum active integrated frames;
  - minimum speedup;
  - shape match;
  - minimum coverage fraction;
  - maximum RMS difference;
  - maximum absolute p99 difference.
- It writes JSON plus optional Markdown and returns nonzero when any acceptance
  check fails.
- Added unit coverage for passing and failing audits plus CLI help coverage.
- Ran the command against the final M38 H-alpha benchmark artifacts.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp\report\acceptance_audit.py src\gpwbpp\cli.py tests\test_acceptance_audit.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_acceptance_audit.py tests\test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\gpwbpp.exe acceptance-audit --help
.\.venv\Scripts\gpwbpp.exe acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3\manifest.json --gpwbpp-run C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3\compare_vs_wbpp_fastintegration_scaled_coverage190.json --out runs\benchmarks\m38_acceptance_audit_cli.json --markdown runs\benchmarks\m38_acceptance_audit_cli.md --min-active-frames 190 --min-speedup 2.0 --min-coverage-fraction 0.95 --max-rms-diff 0.01 --max-abs-diff-p99 0.01
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Result

- Focused tests: `3 passed in 0.15s`.
- Full suite: `178 passed in 8.24s`.
- Ruff: passed.

## Real M38 Acceptance CLI Result

- Status: `passed`.
- Speedup: `9.75928982978054x`.
- Output JSON: `runs\benchmarks\m38_acceptance_audit_cli.json`.
- Output Markdown: `runs\benchmarks\m38_acceptance_audit_cli.md`.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Native backend: true.

## Known Limitations

- The command verifies existing artifacts. It does not run GPWBPP or WBPP.
- It validates explicit acceptance thresholds, not PixInsight/WBPP algorithmic
  identity.

## Next Step

- Use `gpwbpp acceptance-audit` for future real-data acceptance runs and
  regression evidence.

## Clean-room

- Compliant. The command consumes project artifacts and user-generated
  PixInsight/WBPP black-box metadata only.
