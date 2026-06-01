# S2-Gate 98 Status: Resident Sweep Provenance And Mini Matrix

## Gate

S2-Gate 98: Resident Sweep Provenance And Mini Matrix

## Completed Content

- Added resident sweep common-run-argument provenance to
  `resident_prefetch_sweep_summary.json` and Markdown summaries.
- Provenance records source type, imported command path, source argument count,
  imported argument count, inline/repeated argument counts, total argument
  count, filtered token count, and filtered sweep-managed options.
- Added test coverage proving imported command provenance is emitted and that
  sweep-managed parameters remain owned by the sweep.
- Ran a four-variant imported 200-light sweep matrix over:
  - `prefetch_frames`: `16`, `24`
  - `refill_mode`: `immediate`, `queued`
  - fixed `prefetch_workers=8`, `batch_frames=8`, `streams=4`,
    `wave_frames=2`, `release_mode=callback_queue`
- Each variant used timeout guards and per-variant `glass guardrails` with
  tiled pixel verification.
- Compared the best variant against the external reference master with the
  release-family scale/offset and coverage>=190 mask.
- Updated Phase 2 planning and algorithm source tracking.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_benchmarks.py::test_bench_resident_prefetch_sweep_imports_baseline_run_command tests\test_benchmarks.py::test_bench_resident_prefetch_sweep_dry_run_outputs_matrix
.\.venv\Scripts\python.exe benchmarks\bench_resident_prefetch_sweep.py --plan "C:\gpwbpp_runs\final_m38_h_200\processing_plan.json" --out "C:\glass_runs\phase2_s2_gate_98_imported_sweep_matrix" --glass-command ".\.venv\Scripts\python.exe -m glass.cli" --common-run-args-from-command "C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\run_command.txt" --common-run-arg=--resident-output-maps --common-run-arg=science --prefetch-frames 16,24 --prefetch-workers 8 --batch-frames 8 --streams 4 --wave-frames 2 --release-modes callback_queue --refill-modes immediate,queued --baseline-total-seconds 31.835984100122005 --guardrails --guardrails-pixel-verify --guardrails-pixel-verify-tile-size 4096 --guardrails-stack-scope integration --guardrails-expected-integration-engine cuda_resident_stack --max-variant-seconds 180 --max-guardrails-seconds 180
.\.venv\Scripts\glass.exe compare --glass "C:\glass_runs\phase2_s2_gate_98_imported_sweep_matrix\pf16_pw8_b8_s4_w2_callback_queue_rfqueued\integration\resident_master_H.fits" --reference "C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out "C:\glass_runs\phase2_s2_gate_98_imported_sweep_matrix\compare_best_vs_reference_scaled_coverage190.html" --glass-time-seconds 15.523251200094819 --reference-time-seconds 1092.541 --glass-label "GLASS S2-Gate98 best imported sweep" --reference-label "reference FastIntegration" --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map "C:\glass_runs\phase2_s2_gate_98_imported_sweep_matrix\pf16_pw8_b8_s4_w2_callback_queue_rfqueued\integration\resident_coverage_map_H.fits" --min-coverage 190 --ignore-border-px 0
.\.venv\Scripts\python.exe -m pytest -q tests\test_benchmarks.py
.\.venv\Scripts\python.exe -m ruff check benchmarks\bench_resident_prefetch_sweep.py src\glass\report\resident_sweep.py tests\test_benchmarks.py docs\algorithm_sources.md docs\phase2_algorithm_hardening.md
.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_98_doctor.json
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
```

## Test Results

- Focused provenance tests: 2 passed in 0.47 s.
- Benchmark tests: 10 passed in 2.50 s.
- Full pytest: 304 passed in 14.42 s.
- Focused ruff and full `ruff check .`: passed.
- Native CUDA build: passed, no rebuild needed.
- `glass doctor`: passed and wrote
  `runs/checkpoints/s2_gate_98_doctor.json`.

## CUDA Status

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Real 200-Light Sweep Evidence

- Sweep output:
  `C:\glass_runs\phase2_s2_gate_98_imported_sweep_matrix`
- Summary JSON:
  `C:\glass_runs\phase2_s2_gate_98_imported_sweep_matrix\resident_prefetch_sweep_summary.json`
- Summary Markdown:
  `C:\glass_runs\phase2_s2_gate_98_imported_sweep_matrix\resident_prefetch_sweep_summary.md`
- Imported command:
  `C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\run_command.txt`
- Common-run-argument provenance:
  - source: `command_file`
  - source args: `62`
  - imported args: `46`
  - repeated override args: `2`
  - total args: `48`
  - filtered tokens: `16`
- Guardrails:
  `4 / 4` variants passed.
- Frame counts:
  every variant preserved `200` input lights, `193` active frames, and `7`
  zero-weight frames.

## Variant Ranking

| Rank | Variant | Total s | Speedup vs 31.835984 s baseline | Guardrails |
| ---: | --- | ---: | ---: | --- |
| 1 | `pf16_pw8_b8_s4_w2_callback_queue_rfqueued` | `15.523251` | `2.050858x` | passed |
| 2 | `pf16_pw8_b8_s4_w2_callback_queue` | `15.811795` | `2.013433x` | passed |
| 3 | `pf24_pw8_b8_s4_w2_callback_queue_rfqueued` | `16.077046` | `1.980214x` | passed |
| 4 | `pf24_pw8_b8_s4_w2_callback_queue` | `16.351797` | `1.946941x` | passed |

## Best Variant Compare

- Best master:
  `C:\glass_runs\phase2_s2_gate_98_imported_sweep_matrix\pf16_pw8_b8_s4_w2_callback_queue_rfqueued\integration\resident_master_H.fits`
- Compare HTML:
  `C:\glass_runs\phase2_s2_gate_98_imported_sweep_matrix\compare_best_vs_reference_scaled_coverage190.html`
- Compare JSON:
  `C:\glass_runs\phase2_s2_gate_98_imported_sweep_matrix\compare_best_vs_reference_scaled_coverage190.json`
- External reference runtime:
  `1092.541 s`
- Best GLASS runtime:
  `15.523251200094819 s`
- Speedup versus external reference:
  `70.38093927084853x`
- Shape match:
  true
- Coverage>=190 compared pixels:
  `59210247`
- Coverage>=190 RMS:
  `0.0016219628276072312`
- Coverage>=190 p99 absolute difference:
  `0.000425706743262708`

## Known Limitations

- The mini matrix used shared master cache and hot local data. It is valid for
  relative resident parameter tuning, but it does not replace cold/package
  release baselines.
- The science output-map override intentionally skips low/high rejection FITS
  count files while preserving master, weight, coverage, and DQ maps. Use
  `audit` mode for full diagnostic-map artifact checks.
- The queued-refill win is small and should be treated as a candidate setting,
  not a universal default, until repeated on a broader benchmark matrix.

## Next Step

Carry `prefetch_frames=16`, `refill_mode=queued`, `batch_frames=8`,
`streams=4`, `wave_frames=2`, and `callback_queue` forward as the current
guardrail-passed tuning candidate. The next high-value algorithmic work remains
resident registration/warp batching and host/device orchestration reduction.

## Clean-Room Compliance

Compliant. This gate consumes GLASS-owned command, sweep, guardrail, timing, and
compare artifacts only. It does not read, copy, summarize, or rework any
proprietary implementation source.
