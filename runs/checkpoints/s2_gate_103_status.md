# S2-Gate 103 Status: Resident Triangle Catalog Sweep Knobs

- Status: green
- Date: 2026-06-01T10:09:31+08:00
- Scope: resident CUDA triangle catalog tuning, sweep orchestration, and artifact auditability

## Completed

- Added resident CLI overrides for triangle catalog tuning:
  - `--resident-triangle-grid-top-per-cell`
  - `--resident-triangle-nms-scan-candidates`
  - `--resident-triangle-nms-min-separation-px`
- Routed the new overrides through `glass run`, `glass audit`, and `run_resident_calibration_integration`.
- Added validation for positive/non-negative override values.
- Recorded effective values in resident registration artifacts:
  - `triangle_grid_top_per_cell`
  - `triangle_nms_scan_candidates`
  - `triangle_nms_min_separation_px`
- Added per-frame registration warnings for the same effective values.
- Added resident sweep dimensions for the new knobs and encoded them into variant ids and generated command lines.
- Preserved imported command behavior by appending sweep-owned overrides after imported science arguments.
- Updated Phase 2 and algorithm-source documentation.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_benchmarks.py -q
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair -q
.\.venv\Scripts\python.exe -m ruff check benchmarks\bench_resident_prefetch_sweep.py src\glass\report\resident_sweep.py src\glass\cli.py src\glass\engine\resident_cuda.py tests\test_benchmarks.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe benchmarks\bench_resident_prefetch_sweep.py --plan "C:\gpwbpp_runs\final_m38_h_200\processing_plan.json" --out "C:\glass_runs\phase2_s2_gate_103_catalog_sweep" --glass-command ".\.venv\Scripts\python.exe -m glass.cli" --common-run-args-from-command "C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\run_command.txt" --common-run-arg=--resident-output-maps --common-run-arg=science --prefetch-frames 16 --prefetch-workers 8 --batch-frames 8 --streams 4 --wave-frames 2 --release-modes callback_queue --refill-modes queued --triangle-fast-coarse-modes off --triangle-grid-top-per-cell 2,4 --baseline-total-seconds 15.493763700127602 --guardrails --guardrails-pixel-verify --guardrails-pixel-verify-tile-size 4096 --guardrails-stack-scope integration --guardrails-expected-integration-engine cuda_resident_stack --max-variant-seconds 180 --max-guardrails-seconds 180 --reference-master "C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --reference-time-seconds 1092.541 --reference-label "reference FastIntegration" --compare-glass-scale 8.764434957115609e-06 --compare-glass-offset 0.0006274500691899127 --compare-use-candidate-coverage-map --compare-min-coverage 190 --ignore-border-px 0 --compare-require-shape-match --compare-max-rms 0.0016 --compare-max-p99 0.00042
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q tests\test_benchmarks.py tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair
.\.venv\Scripts\glass.exe run --help
.\.venv\Scripts\glass.exe audit --help
.\.venv\Scripts\python.exe benchmarks\bench_resident_prefetch_sweep.py --plan "C:\gpwbpp_runs\final_m38_h_200\processing_plan.json" --out runs\checkpoints\s2_gate_103_dry_run --prefetch-frames 16 --prefetch-workers 8 --batch-frames 8 --streams 4 --wave-frames 2 --release-modes callback_queue --triangle-fast-coarse-modes off --triangle-grid-top-per-cell 2,4 --triangle-nms-min-separation-px 32.5 --dry-run
.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_103_doctor.json
.\.venv\Scripts\python.exe -m pytest -q
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
```

## Test Results

- Focused benchmark tests: 14 passed.
- Focused resident CUDA triangle test: passed.
- Combined focused tests: 15 passed.
- Ruff full check: passed.
- Full pytest: 308 passed in 14.78 s.
- Native CUDA build: passed; Ninja reported no work to do.
- Doctor JSON: `runs/checkpoints/s2_gate_103_doctor.json`.

## 200-Light Evidence

- Real 200-light resident CUDA sweep output: `C:\glass_runs\phase2_s2_gate_103_catalog_sweep`.
- Both variants preserved 200 input lights, 193 active frames, 7 zero-weight frames, and passing guardrails.
- Strict compare gate: shape match required, `max_rms_diff=0.0016`, `max_abs_diff_p99=0.00042`.

| Variant | Total s | Guardrails | Compare gate | Moving catalog s | Reg/warp s | Ref RMS | Ref p99 | Ref speedup |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcbase_gt2` | 15.600916900206357 | passed | failed | 0.7481854963116348 | 2.315043199341744 | 0.0016520084627175229 | 0.0004209110047668236 | 70.03056339499818 |
| `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcbase_gt4` | 15.823564800433815 | passed | failed | 1.094390296842903 | 2.6571022011339664 | 0.0016451822934056798 | 0.00041896674782037485 | 69.04518759072843 |

Observation: `triangle_grid_top_per_cell=2` reduced moving-catalog time substantially versus 4 in this run, but it failed the strict image-agreement gate. It remains a candidate for further tuning, not a default.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Package recommendation: cuda.

## Known Limitations

- This gate exposes and audits existing catalog parameters; it does not change CUDA catalog kernels.
- Lower catalog capacity can alter downstream descriptor fits and final pixels, so compare-gated ranking remains required.
- The top-per-cell sweep used the hot/shared-cache 200-light benchmark and should not be treated as a cold-start packaging benchmark.

## Next Step

- Use these knobs to run a slightly broader compare-gated catalog sweep, likely combining top-per-cell and grid dimensions, then implement a safer catalog selection rule if one region gives both lower catalog time and passing image agreement.

## Clean-Room Compliance

- No official PixInsight or PJSR source code was read or used.
- This gate consumes only GLASS-generated artifacts and a user-generated external reference master.
- Input image directories remain read-only.
