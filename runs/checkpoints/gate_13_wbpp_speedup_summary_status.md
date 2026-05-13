# Gate 13 Status: WBPP Speedup Summary Artifact

## Gate

Gate 13: PixInsight/WBPP black-box comparison and timing summary increment.

## Completed

- Added `gpwbpp.report.speedup_report` to summarize GPWBPP run timing against a user-generated WBPP black-box result JSON.
- Added `benchmarks/summarize_wbpp_speedup.py` wrapper for reproducible speedup summaries.
- The summary records:
  - GPWBPP elapsed time, backend, memory mode, planned frame count, active weighted frame count, zero-weight frame count.
  - WBPP elapsed time, dataset, reported WBPP time, final master files.
  - Speedup vs WBPP and threshold pass/fail.
  - Optional compare metrics including RMS, p99, coverage fraction, and compared pixels.
  - Clean-room compliance note.
- Wrote real M38 summary artifacts from existing read-only GPWBPP/WBPP outputs:
  - `runs/benchmarks/m38_wbpp_speedup_summary.json`
  - `runs/benchmarks/m38_wbpp_speedup_summary.md`

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp\report\speedup_report.py benchmarks\summarize_wbpp_speedup.py tests\test_speedup_report.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_speedup_report.py
.\.venv\Scripts\python.exe benchmarks\summarize_wbpp_speedup.py --gpwbpp-run C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3\compare_vs_wbpp_fastintegration_scaled_coverage190.json --out runs\benchmarks\m38_wbpp_speedup_summary.json --markdown runs\benchmarks\m38_wbpp_speedup_summary.md --min-speedup 2.0
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Result

- Speedup summary tests: `2 passed`.
- Full pytest: `175 passed in 8.14s`.
- Ruff: passed.

## Real M38 Timing Summary

- WBPP black-box elapsed: 1092.541 s.
- GPWBPP resident CUDA elapsed: 111.94882199994754 s.
- Speedup: 9.75928982978054x.
- Speedup threshold: 2.0x.
- Threshold met: true.
- Planned GPWBPP frames: 200.
- Active weighted frames: 193.
- Zero-weight frames: 7.
- Compare artifact: coverage-masked scaled comparison against WBPP FastIntegration.
- Coverage fraction: 0.9612859117097478.
- Coverage-masked RMS diff: 0.0017183155193652361.
- Coverage-masked p99 abs diff: 0.00045279982034117025.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: true.

## Known Limitations

- This summary consumes existing GPWBPP/WBPP artifacts; it does not re-run the full real-data pipeline.
- The comparison uses the coverage-masked scaled result for the WBPP-accepted frame set; border/coverage differences remain documented separately.

## Next Step

- Keep this summary as the stable final benchmark artifact, and use it when new real-data runs are generated so timing and parity evidence stay machine-readable.

## Clean-room

- Compliant. The WBPP input is user-generated black-box timing/output metadata only.
- No official PixInsight/WBPP/PJSR source was read or copied.
