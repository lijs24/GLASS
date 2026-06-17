# S2-Gate 152 Status: Candidate-vs-Baseline Comparison

## Gate

- Gate: S2-Gate 152
- Status: green
- Completed at: 2026-06-17
- Scope: artifact-level comparison of the S2-Gate 151 `agreement_soft_downweight` retry candidate against the Gate119 historical GLASS resident baseline.

## Completed Content

- Added `glass candidate-comparison`.
- Added `src/glass/report/candidate_comparison.py`.
- Added focused tests in `tests/test_candidate_comparison.py`.
- Added CLI smoke coverage for `candidate-comparison`.
- Updated `docs/phase2_algorithm_hardening.md`.
- Updated `docs/algorithm_sources.md`.
- Generated real-data Gate152 artifacts under `C:\glass_runs\phase2_s2_gate_152_candidate_comparison`.

## Real-Data Artifacts

- `C:\glass_runs\phase2_s2_gate_152_candidate_comparison\baseline_no_border_vs_reference.json`
- `C:\glass_runs\phase2_s2_gate_152_candidate_comparison\baseline_no_border_vs_reference.html`
- `C:\glass_runs\phase2_s2_gate_152_candidate_comparison\candidate_vs_baseline.json`
- `C:\glass_runs\phase2_s2_gate_152_candidate_comparison\candidate_vs_baseline.html`
- `C:\glass_runs\phase2_s2_gate_152_candidate_comparison\candidate_comparison.json`
- `C:\glass_runs\phase2_s2_gate_152_candidate_comparison\candidate_comparison.md`
- `runs\checkpoints\s2_gate_152_doctor.json`

## Commands Run

- `.\.venv\Scripts\ruff.exe check src\glass\report\candidate_comparison.py tests\test_candidate_comparison.py src\glass\cli.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_candidate_comparison.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_152_candidate_comparison\baseline_no_border_vs_reference.html --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200\integration\resident_coverage_map_H.fits --min-coverage 190`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_151_repair\agreement_soft_downweight_retry1\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_152_candidate_comparison\candidate_vs_baseline.html --glass-coverage-map C:\glass_runs\phase2_s2_gate_151_repair\agreement_soft_downweight_retry1\integration\resident_coverage_map_H.fits --min-coverage 190`
- `.\.venv\Scripts\glass.exe candidate-comparison --baseline-run C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200 --candidate-run C:\glass_runs\phase2_s2_gate_151_repair\agreement_soft_downweight_retry1 --candidate-id agreement_soft_downweight --baseline-compare-json C:\glass_runs\phase2_s2_gate_152_candidate_comparison\baseline_no_border_vs_reference.json --candidate-compare-json C:\glass_runs\phase2_s2_gate_151_repair\agreement_soft_downweight_retry1_vs_reference.json --candidate-vs-baseline-json C:\glass_runs\phase2_s2_gate_152_candidate_comparison\candidate_vs_baseline.json --candidate-acceptance-json C:\glass_runs\phase2_s2_gate_151_repair\agreement_soft_downweight_retry1_acceptance.json --min-speedup-vs-reference 20 --out C:\glass_runs\phase2_s2_gate_152_candidate_comparison\candidate_comparison.json --markdown C:\glass_runs\phase2_s2_gate_152_candidate_comparison\candidate_comparison.md --fail-on-failed`
- `.\.venv\Scripts\ruff.exe check .`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_152_doctor.json`

## Test Results

- Focused pytest: 12 passed in 1.89 s.
- Full pytest: 384 passed in 22.38 s.
- Ruff: all checks passed.
- Doctor: completed successfully.

## CUDA Availability

- CUDA wrapper importable: true
- CUDA native extension loaded: true
- CUDA available: true
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21

## Candidate Comparison Result

- Candidate: `agreement_soft_downweight`
- Candidate acceptance: passed
- Candidate speedup versus reference: 42.011616681462776x
- Baseline elapsed: 17.907065800391138 s
- Candidate elapsed: 26.005688100121915 s
- Candidate/baseline elapsed ratio: 1.4522584766262423
- Baseline reference RMS: 0.0014936354909442769
- Candidate reference RMS: 0.0014945534429799121
- Reference RMS relative delta: 0.000614575672043593
- Baseline reference abs diff p99: 0.00044002941809594825
- Candidate reference abs diff p99: 0.00043544556712731865
- Reference abs diff p99 relative delta: -0.01041714662729686
- Candidate-vs-baseline RMS in GLASS units: 0.7104637774344961
- Candidate-vs-baseline abs diff p99 in GLASS units: 0.7220382690429688
- Frame accounting: unchanged at 200 light input, 193 integrated, 7 zero-weight.
- Recommendation: `eligible_but_needs_runtime_sweep`.

## Known Limitations

- This gate is an artifact/decision gate. It does not run new integration or change pipeline defaults.
- The candidate passes agreement checks, but it is slower than the Gate119 historical GLASS baseline and therefore is not promoted as the default.
- Candidate-vs-baseline drift is recorded in raw GLASS units and is diagnostic unless a future gate adds a hard drift threshold.
- Reference agreement depends on the supplied compare normalization, coverage map, and minimum coverage settings.

## Next Step

- S2-Gate 153 should run a small measured candidate sweep around agreement thresholds and runtime settings, keeping the same reference compare and frame-accounting contracts, to find whether the soft downweight behavior can be retained without the 1.45x runtime slowdown.

## Clean-Room Compliance

- This gate used GLASS-owned run, timing, frame-accounting, compare, and acceptance artifacts plus user-generated black-box reference output files.
- It did not read or summarize official PixInsight/WBPP source code.
- It did not modify input image directories.
- It did not alter CUDA kernels, resident integration defaults, or scientific formulas.
