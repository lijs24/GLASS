# S2-Gate 117 Status: Deterministic Catalog Sweep Control

## Gate

- Gate: S2-Gate 117
- Completed at: 2026-06-01T12:24:24+08:00
- Scope: make resident star-catalog deterministic mode a first-class resident
  sweep dimension and verify repeated 200-light deterministic runs.

## Completed

- Added `--star-catalog-deterministic-modes inherit,off,on` to
  `benchmarks/bench_resident_prefetch_sweep.py`.
- Added `star_catalog_deterministic_modes` to
  `build_resident_sweep_variants`.
- Added deterministic variant ids:
  - `catfast` for explicit fast/non-deterministic catalog mode.
  - `catdet` for deterministic catalog mode.
- Added command generation for `--resident-star-catalog-deterministic` only
  when a variant explicitly requests deterministic mode.
- When the deterministic mode dimension is explicitly provided, the sweep
  strips any imported `--resident-star-catalog-deterministic` common arg so an
  `off` variant is genuinely off.
- Added dry-run benchmark coverage in `tests/test_benchmarks.py`.
- Updated `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.
- Generated a 200-light dry-run matrix proving `off/on` command generation.
- Ran two repeated 200-light `catdet` resident CUDA variants.
- Compared the repeated `catdet` variants with `glass resident-determinism
  --fail-on-mismatch`.

## Commands

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\report\resident_sweep.py benchmarks\bench_resident_prefetch_sweep.py tests\test_benchmarks.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_benchmarks.py -k "resident_prefetch_sweep"

.\.venv\Scripts\python.exe benchmarks\bench_resident_prefetch_sweep.py `
  --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json `
  --out C:\glass_runs\phase2_s2_gate_117_deterministic_catalog\dry_run `
  --common-run-args-from-command C:\glass_runs\phase2_s2_gate_110_grid_shape_sweep\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcbase_g28x16_gt2_sep96\run_command.txt `
  --prefetch-frames 16 `
  --prefetch-workers 8 `
  --batch-frames 8 `
  --streams 4 `
  --wave-frames 2 `
  --release-modes callback_queue `
  --refill-modes queued `
  --star-catalog-deterministic-modes off,on `
  --dry-run

.\.venv\Scripts\python.exe benchmarks\bench_resident_prefetch_sweep.py `
  --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json `
  --out C:\glass_runs\phase2_s2_gate_117_deterministic_catalog\repeat_a `
  --common-run-args-from-command C:\glass_runs\phase2_s2_gate_110_grid_shape_sweep\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcbase_g28x16_gt2_sep96\run_command.txt `
  --prefetch-frames 16 `
  --prefetch-workers 8 `
  --batch-frames 8 `
  --streams 4 `
  --wave-frames 2 `
  --release-modes callback_queue `
  --refill-modes queued `
  --star-catalog-deterministic-modes on `
  --max-variant-seconds 300

.\.venv\Scripts\python.exe benchmarks\bench_resident_prefetch_sweep.py `
  --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json `
  --out C:\glass_runs\phase2_s2_gate_117_deterministic_catalog\repeat_b `
  --common-run-args-from-command C:\glass_runs\phase2_s2_gate_110_grid_shape_sweep\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcbase_g28x16_gt2_sep96\run_command.txt `
  --prefetch-frames 16 `
  --prefetch-workers 8 `
  --batch-frames 8 `
  --streams 4 `
  --wave-frames 2 `
  --release-modes callback_queue `
  --refill-modes queued `
  --star-catalog-deterministic-modes on `
  --max-variant-seconds 300

glass resident-determinism `
  --baseline-run C:\glass_runs\phase2_s2_gate_117_deterministic_catalog\repeat_a\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet `
  --candidate-run C:\glass_runs\phase2_s2_gate_117_deterministic_catalog\repeat_b\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet `
  --out C:\glass_runs\phase2_s2_gate_117_deterministic_catalog\resident_determinism.json `
  --markdown C:\glass_runs\phase2_s2_gate_117_deterministic_catalog\resident_determinism.md `
  --fail-on-mismatch

.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
glass doctor --json runs\checkpoints\s2_gate_117_doctor.json
```

## Real 200-Light Result

- Dry-run variants:
  - `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catfast`
  - `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet`
- Repeated deterministic run A:
  - Variant: `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet`
  - Elapsed: `15.424829199910164` s.
  - Active / zero-weight frames: `193 / 7`.
  - Resident registration/warp: `1.8862406988628209` s.
  - Moving catalog: `0.18638940528035164` s.
- Repeated deterministic run B:
  - Variant: `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet`
  - Elapsed: `16.2655635997653` s.
  - Active / zero-weight frames: `193 / 7`.
  - Resident registration/warp: `1.9528553988784552` s.
  - Moving catalog: `0.18889939738437533` s.

`glass resident-determinism --fail-on-mismatch` passed:

- Artifact signatures: 0 differences.
- Frame signatures: 0 differences.
- Registration results: 0 differences.
- Frame accounting: 0 differences.
- Output pixels/maps: 0 differences.
- Output numerical drifts: 0.

## Artifacts

- Gate root:
  `C:\glass_runs\phase2_s2_gate_117_deterministic_catalog`
- Dry-run summary:
  `C:\glass_runs\phase2_s2_gate_117_deterministic_catalog\dry_run\resident_prefetch_sweep_summary.json`
- Repeated deterministic run A:
  `C:\glass_runs\phase2_s2_gate_117_deterministic_catalog\repeat_a`
- Repeated deterministic run B:
  `C:\glass_runs\phase2_s2_gate_117_deterministic_catalog\repeat_b`
- Determinism audit:
  `C:\glass_runs\phase2_s2_gate_117_deterministic_catalog\resident_determinism.json`
- Doctor:
  `runs\checkpoints\s2_gate_117_doctor.json`

## Test Result

- Focused `ruff`: passed.
- Focused benchmark tests: `8 passed, 11 deselected in 1.90s`.
- Full `ruff check .`: passed.
- Full `python -m pytest -q`: `320 passed in 17.47s`.
- Native CUDA build: passed, `ninja: no work to do`.
- `glass doctor`: passed.

## CUDA

- CUDA wrapper importable: true.
- CUDA native extension loaded: true.
- CUDA available: true.
- GPU 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Package recommendation: cuda.

## Known Limitations

- This gate does not change the default fast catalog path.
- It proves that explicit `catdet` repeated runs are deterministic for the
  current 200-light command, but it does not yet rerun agreement-threshold
  variants under `catdet`.
- `catdet` should now be used for follow-up agreement threshold experiments so
  candidate changes can be attributed to threshold logic rather than catalog
  nondeterminism.

## Next Step

- S2-Gate 118 should rerun the agreement-threshold sweep under
  `--star-catalog-deterministic-modes on`, then repeat the S2-Gate 116 triage
  to decide whether `0.05` still rejects only true low-agreement frames and
  whether strict image agreement improves without signature drift.

## Clean-Room Compliance

- This gate used GLASS-owned sweep commands, resident artifacts, determinism
  audits, and user-generated benchmark data only.
- No PixInsight or WBPP/PJSR source code was read, copied, summarized, or
  modified.
- Original image directories remained read-only.
