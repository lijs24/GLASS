# Gate 13 Status: PixInsight/WBPP Black-box Comparison

- Gate: 13
- Date: 2026-05-13
- Status: completed
- Latest commit evidence: `32bc8bf gate-13: add speedup summary cli`

## Completed

- Preserved the clean-room WBPP handoff workflow for user-generated PixInsight
  runs.
- Added black-box WBPP result ingestion, FastIntegration history parsing, FITS
  / XISF compare diagnostics, coverage-masked comparison, and machine-readable
  speedup summaries.
- Ran the final real M38 H-alpha benchmark on a same-target data set with 200
  planned light frames and matched calibration frames.
- Used the WBPP FastIntegration accepted-frame set for parity: 193 active
  frames and 7 excluded frames.
- Verified GPWBPP resident CUDA triangle registration + Lanczos3 warp +
  winsorized rejection produced a final master with high-coverage residuals
  dominated by boundary/coverage policy differences.
- Exposed the result through the user-facing command:
  `gpwbpp speedup-summary`.

## Real-data Timing Result

- Data root: user-provided acquisition directories under
  `E:\摄影素材\天协远程台原始素材`.
- Benchmark workspace: `C:\gpwbpp_runs\final_m38_h_200`.
- WBPP black-box result:
  `C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json`.
- WBPP elapsed time: `1092.541 s`.
- WBPP reported time: `18:03.17`.
- GPWBPP run:
  `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3`.
- GPWBPP elapsed time: `111.94882199994754 s`.
- Speedup: `9.75928982978054x`.
- Minimum acceptance threshold used by the summary command: `2.0x`.
- Threshold met: true.

## Numerical Comparison

- Compare artifact:
  `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3\compare_vs_wbpp_fastintegration_scaled_coverage190.json`.
- Shape match: true.
- Coverage threshold: `190`.
- Compared pixels: `59264430`.
- Coverage fraction: `0.9612859117097478`.
- Coverage-masked RMS difference: `0.0017183155193652361`.
- Coverage-masked absolute-difference p99:
  `0.00045279982034117025`.
- Coverage-masked absolute-difference p99.9:
  `0.00448366389935935`.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp\cli.py tests\test_cli_smoke.py tests\test_speedup_report.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_speedup_report.py tests\test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\gpwbpp.exe speedup-summary --help
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\gpwbpp.exe speedup-summary --gpwbpp-run C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3\compare_vs_wbpp_fastintegration_scaled_coverage190.json --out runs\benchmarks\m38_wbpp_speedup_summary_cli.json --markdown runs\benchmarks\m38_wbpp_speedup_summary_cli.md --min-speedup 2.0
```

## Test Result

- Latest focused Gate 13 CLI/report tests: `4 passed`.
- Latest full suite: `176 passed in 8.07s`.
- Ruff: passed.

## CUDA Availability

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Native backend: true.

## Artifacts

- `docs/validation.md`
- `docs/pixinsight_blackbox_reference.md`
- `runs\benchmarks\m38_wbpp_speedup_summary.json`
- `runs\benchmarks\m38_wbpp_speedup_summary.md`
- `runs\benchmarks\m38_wbpp_speedup_summary_cli.json`
- `runs\benchmarks\m38_wbpp_speedup_summary_cli.md`
- `runs\checkpoints\gate_13_wbpp_speedup_summary_status.md`
- `runs\checkpoints\gate_13_validation_speedup_summary_docs_status.md`
- `runs\checkpoints\gate_13_speedup_summary_cli_status.md`

## Known Limitations

- GPWBPP does not claim PixInsight-equivalent algorithms. Known remaining
  differences include star matching, boundary/crop policy, exact interpolation
  and clamping behavior, local normalization, rejection details, and output
  scaling.
- The fastest validated parity run disables local normalization to match the
  observed WBPP FastIntegration parity target more closely.
- The comparison relies on user-generated WBPP black-box outputs and logs, not
  on PixInsight source code.

## Next Step

- Keep the real M38 benchmark as the current acceptance evidence.
- Next engineering work should either harden the resident CUDA registration
  path on additional real pairs or add the optional Gate 14 PixInsight launcher
  front-end without modifying or copying official PixInsight scripts.

## Clean-room Compliance

- Compliant.
- No official PixInsight WBPP/PJSR source was read, copied, summarized, or
  modified.
- The project consumed only user-generated WBPP output/timing metadata,
  public behavioral documentation/discussion, FITS/XISF headers, and
  project-owned/open-source code.
- Original input directories were not modified.
