# S2-Gate 101 Status: Resident Sweep Compare Contract

- Status: green
- Date: 2026-06-01T09:52:06+08:00
- Scope: resident CUDA sweep reporting and benchmark orchestration

## Completed

- Added per-variant compare forwarding to `benchmarks/bench_resident_prefetch_sweep.py`.
- Added compare options for candidate scale, offset, clip bounds, candidate coverage map, and minimum coverage.
- Attached compare JSON/HTML paths, shape match, RMS, relative RMS, p99 absolute difference, max absolute difference, compared pixels, coverage fraction, minimum coverage, and external speedup to each sweep run summary.
- Added resident coverage-map path extraction to sweep summaries so compare can use the candidate coverage map.
- Added Ref RMS, Ref p99, and Ref speedup columns to resident sweep Markdown output.
- Documented S2-Gate 101 in the Phase 2 plan and algorithm source ledger.
- Added focused tests for compare command construction, compare-summary extraction, missing compare handling, coverage-map extraction, and Markdown rendering.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_benchmarks.py -q
git diff --check
.\.venv\Scripts\python.exe -m ruff check benchmarks\bench_resident_prefetch_sweep.py src\glass\report\resident_sweep.py tests\test_benchmarks.py
.\.venv\Scripts\python.exe benchmarks\bench_resident_prefetch_sweep.py --plan "C:\gpwbpp_runs\final_m38_h_200\processing_plan.json" --out "C:\glass_runs\phase2_s2_gate_100_fast_coarse_sweep" --glass-command ".\.venv\Scripts\python.exe -m glass.cli" --common-run-args-from-command "C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\run_command.txt" --common-run-arg=--resident-output-maps --common-run-arg=science --prefetch-frames 16 --prefetch-workers 8 --batch-frames 8 --streams 4 --wave-frames 2 --release-modes callback_queue --refill-modes queued --triangle-fast-coarse-modes off,on --triangle-coarse-strides 4 --triangle-final-strides 8 --star-max-candidates 48 --baseline-total-seconds 15.523251200094819 --guardrails --guardrails-pixel-verify --guardrails-pixel-verify-tile-size 4096 --guardrails-stack-scope integration --guardrails-expected-integration-engine cuda_resident_stack --max-variant-seconds 180 --max-guardrails-seconds 180 --reuse-existing --reference-master "C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --reference-time-seconds 1092.541 --reference-label "reference FastIntegration" --compare-glass-scale 8.764434957115609e-06 --compare-glass-offset 0.0006274500691899127 --compare-use-candidate-coverage-map --compare-min-coverage 190 --ignore-border-px 0
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_101_doctor.json
.\.venv\Scripts\python.exe -m pytest -q
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
```

## Test Results

- Focused benchmark tests: 13 passed.
- Ruff focused check: passed.
- Ruff full check: passed.
- Full pytest: 307 passed in 14.51 s.
- Native CUDA build: passed; Ninja reported no work to do.
- Doctor JSON: `runs/checkpoints/s2_gate_101_doctor.json`.

## 200-Light Evidence

- Reused existing Gate 100 resident CUDA run outputs; no new stack run was launched.
- Regenerated guardrails and reference compare metrics for both variants.
- Sweep summary: `C:\glass_runs\phase2_s2_gate_100_fast_coarse_sweep\resident_prefetch_sweep_summary.json`.
- Markdown summary: `C:\glass_runs\phase2_s2_gate_100_fast_coarse_sweep\resident_prefetch_sweep_summary.md`.

| Variant | Total s | Guardrails | Ref RMS | Ref p99 | Ref speedup |
| --- | ---: | --- | ---: | ---: | ---: |
| `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcfast_cs4_fs8_sm48` | 14.981565 | passed | 0.0016476405903858926 | 0.0004368863534182296 | 72.9256942895333 |
| `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcbase_cs4_fs8_sm48` | 15.493764 | passed | 0.0015609034496484341 | 0.00041120961075648624 | 70.51488722465814 |

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Package recommendation: cuda.

## Known Limitations

- Compare metrics depend on the selected scale/offset, coverage map, and minimum coverage contract; they are benchmark-specific, not universal equivalence claims.
- Fast-coarse remains a candidate path because it is faster but still changes raw GLASS output relative to baseline refinement.
- This gate reused existing resident stack outputs to validate reporting/orchestration; it did not introduce new CUDA kernels.
- The sweep harness records compare status after successful `glass compare`; failed compare subprocesses still fail the sweep command.

## Next Step

- Use the compare-aware sweep contract for the next registration optimization gate so candidate selection is driven by guardrails, timing, and reference-image agreement together.

## Clean-Room Compliance

- No official PixInsight or PJSR source code was read or used.
- This gate consumes only GLASS-generated run artifacts, GLASS compare outputs, and a user-generated external reference master.
- Input image directories remain read-only.
