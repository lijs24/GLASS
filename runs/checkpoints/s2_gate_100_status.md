# S2-Gate 100 Status: Resident Registration Parameter Sweep

## Gate

S2-Gate 100: Resident Registration Parameter Sweep

## Completed Content

- Extended resident sweep variants beyond I/O parameters.
- Added registration tuning dimensions for:
  - triangle pixel-refine fast-coarse mode: `inherit`, `off`, `on`
  - triangle coarse pixel-refine stride
  - triangle final pixel-refine stride
  - resident star max candidates
- Encoded registration tuning dimensions in variant ids, for example
  `fcbase_cs4_fs8_sm48` and `fcfast_cs4_fs8_sm48`.
- Emitted the corresponding GLASS CLI arguments per variant:
  - `--resident-triangle-pixel-refine-coarse-stride`
  - `--resident-triangle-pixel-refine-final-stride`
  - `--resident-triangle-pixel-refine-fast-coarse`
  - `--resident-star-max-candidates`
- Preserved prior default behavior when no registration tuning dimensions are
  supplied.
- Added dry-run coverage for registration-grid command generation.
- Ran a two-variant 200-light guarded sweep comparing baseline pixel refinement
  against fast-coarse pixel refinement.
- Compared the fast-coarse candidate against both the external reference master
  and the baseline-refine GLASS output.
- Updated Phase 2 documentation and algorithm source tracking.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_benchmarks.py::test_bench_resident_prefetch_sweep_dry_run_registration_grid tests\test_benchmarks.py::test_bench_resident_prefetch_sweep_dry_run_outputs_matrix
.\.venv\Scripts\python.exe benchmarks\bench_resident_prefetch_sweep.py --plan "C:\gpwbpp_runs\final_m38_h_200\processing_plan.json" --out "C:\glass_runs\phase2_s2_gate_100_fast_coarse_sweep" --glass-command ".\.venv\Scripts\python.exe -m glass.cli" --common-run-args-from-command "C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\run_command.txt" --common-run-arg=--resident-output-maps --common-run-arg=science --prefetch-frames 16 --prefetch-workers 8 --batch-frames 8 --streams 4 --wave-frames 2 --release-modes callback_queue --refill-modes queued --triangle-fast-coarse-modes off,on --triangle-coarse-strides 4 --triangle-final-strides 8 --star-max-candidates 48 --baseline-total-seconds 15.523251200094819 --guardrails --guardrails-pixel-verify --guardrails-pixel-verify-tile-size 4096 --guardrails-stack-scope integration --guardrails-expected-integration-engine cuda_resident_stack --max-variant-seconds 180 --max-guardrails-seconds 180
.\.venv\Scripts\glass.exe compare --glass "C:\glass_runs\phase2_s2_gate_100_fast_coarse_sweep\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcfast_cs4_fs8_sm48\integration\resident_master_H.fits" --reference "C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out "C:\glass_runs\phase2_s2_gate_100_fast_coarse_sweep\compare_fast_coarse_best_vs_reference_scaled_coverage190.html" --glass-time-seconds 14.981564600020647 --reference-time-seconds 1092.541 --glass-label "GLASS S2-Gate100 fast-coarse" --reference-label "reference FastIntegration" --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map "C:\glass_runs\phase2_s2_gate_100_fast_coarse_sweep\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcfast_cs4_fs8_sm48\integration\resident_coverage_map_H.fits" --min-coverage 190 --ignore-border-px 0
.\.venv\Scripts\glass.exe compare --glass "C:\glass_runs\phase2_s2_gate_100_fast_coarse_sweep\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcfast_cs4_fs8_sm48\integration\resident_master_H.fits" --reference "C:\glass_runs\phase2_s2_gate_100_fast_coarse_sweep\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcbase_cs4_fs8_sm48\integration\resident_master_H.fits" --out "C:\glass_runs\phase2_s2_gate_100_fast_coarse_sweep\compare_fast_coarse_vs_base.html" --glass-time-seconds 14.981564600020647 --reference-time-seconds 15.493763700127602 --glass-label "fast-coarse" --reference-label "baseline refine" --glass-coverage-map "C:\glass_runs\phase2_s2_gate_100_fast_coarse_sweep\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcfast_cs4_fs8_sm48\integration\resident_coverage_map_H.fits" --min-coverage 190 --ignore-border-px 0
.\.venv\Scripts\python.exe -m pytest -q tests\test_benchmarks.py
.\.venv\Scripts\python.exe -m ruff check benchmarks\bench_resident_prefetch_sweep.py src\glass\report\resident_sweep.py tests\test_benchmarks.py docs\algorithm_sources.md docs\phase2_algorithm_hardening.md
.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_100_doctor.json
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
```

## Test Results

- Focused registration-grid tests: 2 passed in 0.48 s.
- Benchmark tests: 12 passed in 2.63 s.
- Full pytest: 306 passed in 14.49 s.
- Focused ruff and full `ruff check .`: passed.
- Native CUDA build: passed, no rebuild needed.
- `glass doctor`: passed and wrote
  `runs/checkpoints/s2_gate_100_doctor.json`.

## CUDA Status

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Real 200-Light Sweep Evidence

- Sweep output:
  `C:\glass_runs\phase2_s2_gate_100_fast_coarse_sweep`
- Summary JSON:
  `C:\glass_runs\phase2_s2_gate_100_fast_coarse_sweep\resident_prefetch_sweep_summary.json`
- Summary Markdown:
  `C:\glass_runs\phase2_s2_gate_100_fast_coarse_sweep\resident_prefetch_sweep_summary.md`
- Guardrails:
  `2 / 2` variants passed with pixel verification.
- Frame counts:
  both variants preserved `200` input lights, `193` active frames, and `7`
  zero-weight frames.

## Variant Results

| Rank | Variant | Total s | Reg/warp s | Catalog s | Pixel refine s | Warp s | Guardrails |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcfast_cs4_fs8_sm48` | `14.981565` | `2.288399` | `1.091948` | `0.522032` | `0.451602` | passed |
| 2 | `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcbase_cs4_fs8_sm48` | `15.493764` | `2.679796` | `1.084322` | `0.891946` | `0.451065` | passed |

## Comparison Evidence

- Fast-coarse versus external reference:
  - HTML:
    `C:\glass_runs\phase2_s2_gate_100_fast_coarse_sweep\compare_fast_coarse_best_vs_reference_scaled_coverage190.html`
  - JSON:
    `C:\glass_runs\phase2_s2_gate_100_fast_coarse_sweep\compare_fast_coarse_best_vs_reference_scaled_coverage190.json`
  - Speedup versus external reference:
    `72.9256942895333x`
  - Shape match:
    true
  - Coverage>=190 RMS:
    `0.0016476405903858926`
  - Coverage>=190 p99 absolute difference:
    `0.0004368863534182296`
- Fast-coarse versus baseline-refine GLASS:
  - HTML:
    `C:\glass_runs\phase2_s2_gate_100_fast_coarse_sweep\compare_fast_coarse_vs_base.html`
  - JSON:
    `C:\glass_runs\phase2_s2_gate_100_fast_coarse_sweep\compare_fast_coarse_vs_base.json`
  - Speedup versus baseline-refine variant:
    `1.0341886254060706x`
  - Raw coverage>=190 RMS:
    `21.351594154505744`
  - Raw coverage>=190 relative RMS:
    `0.08329535214003018`

## Interpretation

- Fast-coarse reduced pixel-refinement time from about `0.892 s` to `0.522 s`
  and improved total run time from `15.494 s` to `14.982 s` in this local hot
  run.
- It also changes the raw GLASS output versus baseline refinement, although the
  external-reference scaled coverage comparison remains in the same tolerance
  family as recent runs.
- Therefore fast-coarse is a promising candidate for further investigation, not
  a new default.

## Known Limitations

- This gate changes sweep orchestration only. It does not change resident CUDA
  kernels, registration formulas, accepted frames, or image math.
- The benchmark uses shared master cache and hot local data, so the absolute
  runtime is not a cold/package release baseline.
- Fast-coarse must be retested on a broader matrix and with additional image
  agreement checks before default promotion.

## Next Step

Use the new registration-grid sweep support to test star-candidate count and
pixel-refine stride combinations. If fast-coarse remains faster and image
agreement remains acceptable, then consider making it an explicit recommended
performance profile rather than a default.

## Clean-Room Compliance

Compliant. This gate orchestrates existing GLASS CLI parameters and consumes
GLASS-owned timing, guardrail, and compare artifacts only. It does not read,
copy, summarize, or rework any proprietary implementation source.
