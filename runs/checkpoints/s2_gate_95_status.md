# S2-Gate 95 Status: Guarded Resident Sweep

## Gate

S2-Gate 95: Guarded Resident Sweep

## Completed Content

- Extended `benchmarks/bench_resident_prefetch_sweep.py` with optional
  per-variant `glass guardrails` execution.
- Added dry-run guardrail command planning so sweep plans show both the GLASS
  resident run command and the follow-up guardrail command.
- Added sweep summary fields for guardrail status, summary path, report path,
  failed contract names, passed/failed/planned counts, and guardrail command
  lines.
- Updated sweep ranking so a completed variant with failed guardrails ranks
  behind a completed guardrail-passed variant. The `best_variant` field no
  longer silently selects a contract-broken run.
- Preserved existing sweep behavior when `--guardrails` is not requested.
- Updated Phase 2 documentation and algorithm source tracking.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_benchmarks.py::test_bench_resident_prefetch_sweep_dry_run_outputs_matrix tests/test_benchmarks.py::test_resident_sweep_ranking_prefers_guardrail_passed_variant
.\.venv\Scripts\python.exe -m ruff check benchmarks/bench_resident_prefetch_sweep.py src/glass/report/resident_sweep.py tests/test_benchmarks.py docs/algorithm_sources.md docs/phase2_algorithm_hardening.md
.\.venv\Scripts\python.exe benchmarks\bench_resident_prefetch_sweep.py --plan "C:\gpwbpp_runs\final_m38_h_200\processing_plan.json" --out runs\checkpoints\s2_gate_95_guarded_sweep_dry_run --glass-command ".\.venv\Scripts\glass.exe" --prefetch-frames 16,24 --prefetch-workers 8 --batch-frames 8 --streams 4 --wave-frames 2 --release-modes callback_queue --baseline-total-seconds 30.361 --common-run-args "--resident-output-maps audit --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-registration similarity_cuda_triangle --resident-warp-interpolation bilinear --resident-integration-dispatch auto" --guardrails --guardrails-pixel-verify --guardrails-pixel-verify-tile-size 4096 --guardrails-stack-scope integration --guardrails-expected-integration-engine cuda_resident_stack --dry-run
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_95_doctor.json
```

## Test Results

- Focused pytest: 2 passed.
- Full pytest: 302 passed in 13.97 s.
- Ruff: passed.
- Native CUDA build: passed, no rebuild needed.
- `glass doctor`: passed.

## CUDA Status

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Real Benchmark Planning Artifact

- 200-light plan:
  `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`
- Dry-run sweep output:
  `runs/checkpoints/s2_gate_95_guarded_sweep_dry_run/`
- Summary:
  `runs/checkpoints/s2_gate_95_guarded_sweep_dry_run/resident_prefetch_sweep_summary.json`
- Markdown:
  `runs/checkpoints/s2_gate_95_guarded_sweep_dry_run/resident_prefetch_sweep_summary.md`
- Result: generated two resident CUDA variant commands and two matching
  `glass guardrails` commands with pixel verification planned.

## Known Limitations

- This gate changes sweep orchestration and ranking only. It does not execute a
  new 200-light benchmark and does not change resident CUDA kernels, image math,
  accepted frames, or output pixels.
- Guardrails add extra I/O and report-generation work when enabled; benchmark
  runtime comparisons still use each variant's `run_timing.json`, not guardrail
  wall time.

## Next Step

Run a small guarded resident sweep on the 200-light dataset when GPU time is
available, then use the guardrail-passed fastest variant as the next performance
baseline before modifying resident registration/warp internals.

## Clean-Room Compliance

Compliant. This gate orchestrates GLASS-owned run, sweep, and guardrail
artifacts only and does not read, copy, summarize, or rework any proprietary
implementation source.
