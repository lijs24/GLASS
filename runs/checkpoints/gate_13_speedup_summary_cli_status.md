# Gate 13 Status: Speedup Summary CLI

## Gate

Gate 13: PixInsight/WBPP black-box comparison CLI increment.

## Completed

- Added `glass speedup-summary` as a first-class CLI command.
- The command reads:
  - a GLASS run directory with `run_timing.json`;
  - a user-generated PixInsight/WBPP black-box result JSON;
  - an optional compare JSON;
  - a configurable minimum speedup threshold.
- It writes a JSON summary and optional Markdown summary using the existing clean-room speedup report module.
- Added CLI help coverage and an output-writing smoke test.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\cli.py tests\test_cli_smoke.py tests\test_speedup_report.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_speedup_report.py tests\test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\glass.exe speedup-summary --help
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe speedup-summary --glass-run C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3 --wbpp-result C:\glass_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3\compare_vs_wbpp_fastintegration_scaled_coverage190.json --out runs\benchmarks\m38_wbpp_speedup_summary_cli.json --markdown runs\benchmarks\m38_wbpp_speedup_summary_cli.md --min-speedup 2.0
```

## Test Result

- Targeted CLI/report tests: `4 passed`.
- Full pytest: `176 passed in 7.61s`.
- Ruff: passed.

## Real M38 CLI Summary Result

- Speedup: `9.75928982978054x`.
- Minimum threshold: `2.0x`.
- Threshold met: true.
- Output JSON: `runs\benchmarks\m38_wbpp_speedup_summary_cli.json`.
- Output Markdown: `runs\benchmarks\m38_wbpp_speedup_summary_cli.md`.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: true.

## Known Limitations

- The command summarizes existing artifacts. It does not run GLASS or WBPP itself.

## Next Step

- Use `glass speedup-summary` as the stable user-facing timing summary command for subsequent real-data benchmark runs.

## Clean-room

- Compliant. The command consumes only GLASS artifacts and user-generated WBPP black-box timing/output metadata.
