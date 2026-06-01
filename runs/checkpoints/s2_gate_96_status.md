# S2-Gate 96 Status: Resident Sweep Runtime Guard

## Gate

S2-Gate 96: Resident Sweep Runtime Guard

## Completed Content

- Added `--max-variant-seconds` and `--max-guardrails-seconds` to
  `benchmarks/bench_resident_prefetch_sweep.py`.
- Converted per-variant run failures and timeouts into structured sweep summary
  records instead of crashing the whole sweep.
- Skipped per-variant guardrails when the GLASS run itself fails or times out,
  and recorded the skipped guardrail status explicitly.
- Converted guardrail command failures/timeouts into per-run guardrail failure
  records while preserving the completed run summary.
- Updated the resident sweep Markdown table with status and timeout columns.
- Added a controlled timeout test that proves timed-out variants are recorded,
  excluded from `best_variant`, and counted as failed guardrail candidates.
- Updated Phase 2 planning and algorithm source documentation.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_benchmarks.py
.\.venv\Scripts\python.exe -m ruff check benchmarks\bench_resident_prefetch_sweep.py src\glass\report\resident_sweep.py tests\test_benchmarks.py
.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_96_doctor.json
.\.venv\Scripts\python.exe -m pytest -q
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
```

## Test Results

- Focused benchmark tests: 9 passed in 2.21 s.
- Ruff: passed.
- Full pytest: 303 passed in 14.30 s.
- Native CUDA build: passed, no rebuild needed.
- `glass doctor`: passed and wrote
  `runs/checkpoints/s2_gate_96_doctor.json`.

## CUDA Status

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Real Benchmark Note

- The first 200-light guarded sweep attempt used
  `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json` and output directory
  `C:\glass_runs\phase2_s2_gate_96_guarded_sweep_v2`.
- The first variant was still running after more than ten minutes, while the
  current Phase 1/2 baseline family is about 30 seconds for the full run.
- That attempt was stopped manually before completion. No runtime or science
  result from the interrupted run is accepted as a green benchmark.
- This gate intentionally fixes the harness first so future sweeps can bound
  each variant and preserve diagnostic records for slow or failed runs.

## Known Limitations

- Python `subprocess.run(..., timeout=...)` is a process-level guard. It is
  sufficient for the current direct GLASS invocation path. If a future launcher
  creates detached child processes, the harness may need a Windows job-object
  kill path.
- Compare-report commands still use the existing direct `subprocess.run` path;
  this gate guards resident variants and guardrail bundles, which are the GPU
  monopolization risk observed in the interrupted sweep.
- This gate changes benchmark orchestration only. It does not change resident
  CUDA kernels, image math, accepted frames, or output pixels.

## Next Step

Run the 200-light guarded resident sweep again with a conservative
`--max-variant-seconds` value, then use only guardrail-passed completed variants
to select the next registration/warp optimization target.

## Clean-Room Compliance

Compliant. This gate handles GLASS-owned process orchestration and GLASS run
artifacts only. It does not read, copy, summarize, or rework any proprietary
implementation source.
