# S2-Gate 97 Status: Resident Sweep Baseline Command Import

## Gate

S2-Gate 97: Resident Sweep Baseline Command Import

## Completed Content

- Added `--common-run-args-from-command` to
  `benchmarks/bench_resident_prefetch_sweep.py`.
- The importer reads a GLASS `run_command.txt`, finds the `run` subcommand,
  and preserves shared science/tuning flags for the sweep.
- Sweep-managed flags are filtered out before import: plan, output directory,
  backend, stage, memory mode, prefetch, H2D, calibration batch, stream, wave,
  and release-mode options.
- Added regression coverage proving imported baseline commands keep reference,
  output-map policy, flat floor, and excluded-frame settings while the sweep
  owns the parameters being swept.
- Ran a bounded 200-light single-variant guarded sweep using the proven Gate32
  audit-map command as the import source.
- Compared the resulting master against the external reference master with the
  same scale/offset and coverage>=190 mask used by the release benchmark
  family.
- Updated Phase 2 documentation and algorithm source tracking.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_benchmarks.py::test_bench_resident_prefetch_sweep_imports_baseline_run_command tests\test_benchmarks.py::test_bench_resident_prefetch_sweep_dry_run_outputs_matrix tests\test_benchmarks.py::test_bench_resident_prefetch_sweep_records_variant_timeout
.\.venv\Scripts\python.exe benchmarks\bench_resident_prefetch_sweep.py --plan "C:\gpwbpp_runs\final_m38_h_200\processing_plan.json" --out "C:\glass_runs\phase2_s2_gate_97_imported_guarded_sweep" --glass-command ".\.venv\Scripts\python.exe -m glass.cli" --common-run-args-from-command "C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\run_command.txt" --prefetch-frames 16 --prefetch-workers 8 --batch-frames 8 --streams 4 --wave-frames 2 --release-modes callback_queue --baseline-total-seconds 31.835984100122005 --guardrails --guardrails-pixel-verify --guardrails-pixel-verify-tile-size 4096 --guardrails-stack-scope integration --guardrails-expected-integration-engine cuda_resident_stack --max-variant-seconds 180 --max-guardrails-seconds 180
.\.venv\Scripts\glass.exe compare --glass "C:\glass_runs\phase2_s2_gate_97_imported_guarded_sweep\pf16_pw8_b8_s4_w2_callback_queue\integration\resident_master_H.fits" --reference "C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out "C:\glass_runs\phase2_s2_gate_97_imported_guarded_sweep\compare_vs_reference_scaled_coverage190.html" --glass-time-seconds 15.445240100380033 --reference-time-seconds 1092.541 --glass-label "GLASS S2-Gate97 imported guarded sweep" --reference-label "reference FastIntegration" --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map "C:\glass_runs\phase2_s2_gate_97_imported_guarded_sweep\pf16_pw8_b8_s4_w2_callback_queue\integration\resident_coverage_map_H.fits" --min-coverage 190 --ignore-border-px 0
.\.venv\Scripts\python.exe -m pytest -q tests\test_benchmarks.py
.\.venv\Scripts\python.exe -m ruff check benchmarks\bench_resident_prefetch_sweep.py tests\test_benchmarks.py docs\algorithm_sources.md docs\phase2_algorithm_hardening.md
.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_97_doctor.json
.\.venv\Scripts\python.exe -m pytest -q
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
```

## Test Results

- Focused import/timeout/dry-run tests: 3 passed in 0.73 s.
- Full benchmark tests: 10 passed in 2.40 s.
- Ruff: passed.
- Full pytest: 304 passed in 14.27 s.
- Native CUDA build: passed, no rebuild needed.
- `glass doctor`: passed and wrote
  `runs/checkpoints/s2_gate_97_doctor.json`.

## CUDA Status

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Real 200-Light Evidence

- Imported command source:
  `C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\run_command.txt`
- Sweep output:
  `C:\glass_runs\phase2_s2_gate_97_imported_guarded_sweep`
- Variant:
  `pf16_pw8_b8_s4_w2_callback_queue`
- Runtime:
  `15.445240100380033 s`
- Baseline total supplied to sweep:
  `31.835984100122005 s`
- Speedup versus supplied GLASS baseline:
  `2.0612165232276753x`
- External reference runtime:
  `1092.541 s`
- Speedup versus external reference in compare report:
  `70.73642059945172x`
- Input light frames:
  `200`
- Active/integrated frames:
  `193`
- Zero-weight frames:
  `7`
- Guardrails:
  passed with StackEngine and Pipeline contracts, including pixel verification.
- Compare report:
  `C:\glass_runs\phase2_s2_gate_97_imported_guarded_sweep\compare_vs_reference_scaled_coverage190.html`
- Compare JSON:
  `C:\glass_runs\phase2_s2_gate_97_imported_guarded_sweep\compare_vs_reference_scaled_coverage190.json`
- Coverage>=190 comparison RMS:
  `0.0015362242464986263`
- Coverage>=190 p99 absolute difference:
  `0.0004338623140938535`
- Shape match:
  true

## Known Limitations

- The 15.45 s result is a hot-cache/shared-master-cache bounded run and should
  not replace the release cold/package benchmark baseline without a fresh cold
  matrix run.
- The importer intentionally expects a plain GLASS command token stream. If a
  future command file uses shell pipes, redirects, or command separators, the
  importer should be extended before accepting it.
- This gate changes benchmark orchestration and evidence quality only. It does
  not change resident CUDA kernels, image math, accepted frames, or output
  pixels.

## Next Step

Use `--common-run-args-from-command` for the next multi-variant resident sweep,
then tune only prefetch depth, refill mode, batch size, stream count, and wave
size against guardrail-passed variants. The next algorithmic optimization target
remains resident registration/warp batching after stable sweep evidence.

## Clean-Room Compliance

Compliant. The importer consumes GLASS-owned `run_command.txt` artifacts and
GLASS benchmark outputs only. It does not read, copy, summarize, or rework any
proprietary implementation source.
