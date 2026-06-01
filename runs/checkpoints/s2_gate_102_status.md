# S2-Gate 102 Status: Compare-Gated Resident Sweep Ranking

- Status: green
- Date: 2026-06-01T09:59:37+08:00
- Scope: resident CUDA sweep selection policy

## Completed

- Added optional compare-gate policy to resident sweep ranking.
- Supported `require_shape_match`, `max_rms_diff`, `max_relative_rms_diff`, and `max_abs_diff_p99`.
- Added per-variant `compare_gate` status, pass/fail boolean, policy echo, and failure reasons.
- Added top-level compare-gate summary with policy, pass count, fail count, and planned count.
- Added Markdown compare-gate summary and table column.
- Added benchmark CLI options:
  - `--compare-require-shape-match`
  - `--compare-max-rms`
  - `--compare-max-relative-rms`
  - `--compare-max-p99`
- Preserved default behavior when no compare gate is supplied.
- Added tests proving a faster variant can be demoted when image agreement fails the selected contract.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_benchmarks.py -q
.\.venv\Scripts\python.exe -m ruff check benchmarks\bench_resident_prefetch_sweep.py src\glass\report\resident_sweep.py tests\test_benchmarks.py
git diff --check
.\.venv\Scripts\python.exe benchmarks\bench_resident_prefetch_sweep.py --plan "C:\gpwbpp_runs\final_m38_h_200\processing_plan.json" --out "C:\glass_runs\phase2_s2_gate_100_fast_coarse_sweep" --glass-command ".\.venv\Scripts\python.exe -m glass.cli" --common-run-args-from-command "C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\run_command.txt" --common-run-arg=--resident-output-maps --common-run-arg=science --prefetch-frames 16 --prefetch-workers 8 --batch-frames 8 --streams 4 --wave-frames 2 --release-modes callback_queue --refill-modes queued --triangle-fast-coarse-modes off,on --triangle-coarse-strides 4 --triangle-final-strides 8 --star-max-candidates 48 --baseline-total-seconds 15.523251200094819 --guardrails --guardrails-pixel-verify --guardrails-pixel-verify-tile-size 4096 --guardrails-stack-scope integration --guardrails-expected-integration-engine cuda_resident_stack --max-variant-seconds 180 --max-guardrails-seconds 180 --reuse-existing --reference-master "C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --reference-time-seconds 1092.541 --reference-label "reference FastIntegration" --compare-glass-scale 8.764434957115609e-06 --compare-glass-offset 0.0006274500691899127 --compare-use-candidate-coverage-map --compare-min-coverage 190 --ignore-border-px 0 --compare-require-shape-match --compare-max-rms 0.0016 --compare-max-p99 0.00042
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_102_doctor.json
.\.venv\Scripts\python.exe -m pytest -q
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
```

## Test Results

- Focused benchmark tests: 14 passed.
- Ruff full check: passed.
- Full pytest: 308 passed in 14.77 s.
- Native CUDA build: passed; Ninja reported no work to do.
- Doctor JSON: `runs/checkpoints/s2_gate_102_doctor.json`.

## 200-Light Evidence

- Reused existing resident CUDA outputs from the Gate 100 two-variant run.
- Reran guardrails and reference compare for both variants.
- Compare gate policy:
  - `require_shape_match=true`
  - `max_rms_diff=0.0016`
  - `max_abs_diff_p99=0.00042`
- Sweep summary: `C:\glass_runs\phase2_s2_gate_100_fast_coarse_sweep\resident_prefetch_sweep_summary.json`.
- Markdown summary: `C:\glass_runs\phase2_s2_gate_100_fast_coarse_sweep\resident_prefetch_sweep_summary.md`.

| Rank | Variant | Total s | Guardrails | Compare gate | Ref RMS | Ref p99 | Ref speedup |
| ---: | --- | ---: | --- | --- | ---: | ---: | ---: |
| 1 | `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcbase_cs4_fs8_sm48` | 15.493764 | passed | passed | 0.0015609034496484341 | 0.00041120961075648624 | 70.51488722465814 |
| 2 | `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcfast_cs4_fs8_sm48` | 14.981565 | passed | failed | 0.0016476405903858926 | 0.0004368863534182296 | 72.9256942895333 |

Fast-coarse remains a useful performance candidate, but this gate proves the sweep can demote it under a stricter image-agreement contract.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Package recommendation: cuda.

## Known Limitations

- Compare-gate thresholds are benchmark-contract parameters and must be chosen per dataset/output contract.
- The gate changes selection policy and reporting only; it does not change registration, warp, or integration image math.
- The 200-light validation reused existing stack outputs, then reran guardrails and compare.

## Next Step

- Use compare-gated sweeps for resident registration catalog/grid and pixel-refine optimization so a faster path cannot be promoted unless it also preserves benchmark image agreement.

## Clean-Room Compliance

- No official PixInsight or PJSR source code was read or used.
- This gate consumes only GLASS-generated sweep, guardrail, and compare artifacts plus a user-generated external reference master.
- Input image directories remain read-only.
