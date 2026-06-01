# S2-Gate 120 Status: Compare Tail Outlier Audit

## Gate

S2-Gate 120: Compare Tail Outlier Audit.

## Completed Work

- Added `glass compare-outliers` for localized comparison-tail audits.
- Implemented machine-readable JSON and optional Markdown output.
- The audit applies the same comparison transform controls used by benchmark comparisons:
  GLASS scale/offset, clipping, ignored borders, coverage map masking, and
  minimum coverage.
- Reported p99 tail threshold, top residual tiles, top residual pixels, signed
  tail counts, edge-band fraction, and an automatic triage recommendation.
- Added focused tests for direct API usage and CLI output.
- Updated the Phase 2 gate plan and algorithm-source ledger.

## Real 200-Light Audit

Artifacts:

- `C:\glass_runs\phase2_s2_gate_120_compare_outliers\catdet_baseline_outliers.json`
- `C:\glass_runs\phase2_s2_gate_120_compare_outliers\catdet_baseline_outliers.md`
- `C:\glass_runs\phase2_s2_gate_120_compare_outliers\agr0p5_outliers.json`
- `C:\glass_runs\phase2_s2_gate_120_compare_outliers\agr0p5_outliers.md`

Inputs:

- Baseline GLASS master:
  `C:\glass_runs\phase2_s2_gate_118_deterministic_agreement_sweep\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agrs200\integration\resident_master_H.fits`
- Best Gate119 downweight GLASS master:
  `C:\glass_runs\phase2_s2_gate_119_agreement_downweight_extended\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p5_agrs200\integration\resident_master_H.fits`
- User-generated external reference:
  `C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf`

Result summary:

| Variant | Tail threshold | Target exceedance pixels at 0.00042 | Tail edge fraction | Tail sign | Recommendation |
| --- | ---: | ---: | ---: | --- | --- |
| deterministic baseline | 0.0004375878465361898 | 612930 | 0.006431935457102649 | 590491 negative, 0 positive | localized_tail |
| agreement downweight 0.5 | 0.0004268628358840981 | 599340 | 0.006428548445276897 | 590487 negative, 4 positive | localized_tail |

The downweight candidate reduced strict-threshold exceedance by 13,590 pixels,
but the p99 tail stayed in the same localized residual tiles. The top tail tile
remained around x=1552..2064, y=3600..4112, with about 39% of valid pixels in
the tail. This blocks another blind global agreement-weight tweak. The next
target should inspect localized residual tiles and per-frame contribution or
rejection maps.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\report\compare_outliers.py src\glass\cli.py tests\test_compare_outliers.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_compare_outliers.py tests\test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\glass.exe compare-outliers --glass "C:\glass_runs\phase2_s2_gate_119_agreement_downweight_extended\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p5_agrs200\integration\resident_master_H.fits" --reference "C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out "C:\glass_runs\phase2_s2_gate_120_compare_outliers\agr0p5_outliers.json" --markdown "C:\glass_runs\phase2_s2_gate_120_compare_outliers\agr0p5_outliers.md" --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map "C:\glass_runs\phase2_s2_gate_119_agreement_downweight_extended\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p5_agrs200\integration\resident_coverage_map_H.fits" --min-coverage 190 --ignore-border-px 16 --tail-percentile 99 --target-abs-diff 0.00042 --tile-size 512 --top-tiles 24 --top-pixels 64 --edge-band-px 64
.\.venv\Scripts\glass.exe compare-outliers --glass "C:\glass_runs\phase2_s2_gate_118_deterministic_agreement_sweep\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agrs200\integration\resident_master_H.fits" --reference "C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out "C:\glass_runs\phase2_s2_gate_120_compare_outliers\catdet_baseline_outliers.json" --markdown "C:\glass_runs\phase2_s2_gate_120_compare_outliers\catdet_baseline_outliers.md" --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map "C:\glass_runs\phase2_s2_gate_118_deterministic_agreement_sweep\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agrs200\integration\resident_coverage_map_H.fits" --min-coverage 190 --ignore-border-px 16 --tail-percentile 99 --target-abs-diff 0.00042 --tile-size 512 --top-tiles 24 --top-pixels 64 --edge-band-px 64
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_120_doctor.json
```

## Test Result

- Focused ruff: passed.
- Focused pytest: 3 passed.
- Full ruff: passed.
- Full pytest: 323 passed in 17.76 s.
- Native CUDA build: passed; Ninja reported no work to do.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor artifact: `runs\checkpoints\s2_gate_120_doctor.json`.

## Known Limitations

- This gate is diagnostic only and does not change integration, weighting, or
  registration defaults.
- The recommendation is heuristic triage over comparison residuals, not a
  scientific proof of root cause.
- The audit localizes output residuals but does not yet attribute them to
  individual frames, rejection decisions, or LN coefficients.

## Next Step

S2-Gate 121 should inspect localized residual tiles with per-frame contribution
and/or rejection-map evidence before designing any non-linear agreement weight
or multi-signal acceptance rule.

## Clean-Room Compliance

This gate uses only GLASS-generated artifacts and user-generated external
reference outputs. It does not read, copy, summarize, or rework proprietary
implementation source code.
