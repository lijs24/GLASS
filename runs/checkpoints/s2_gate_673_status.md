# S2-Gate 673 Status: Resident Memory Lifecycle Artifact

- Gate: S2-Gate 673
- Status: green
- Date: 2026-06-26
- Branch: main

## Completed

- Added `resident_memory_lifecycle.json` as a first-class resident CUDA runtime
  artifact.
- Added `src/glass/engine/resident_memory_lifecycle.py`.
- Resident CUDA `glass run` and `glass audit` paths now write the lifecycle
  artifact after component timing.
- `run_timing.json` records `resident_memory_lifecycle_path` and
  `resident_memory_lifecycle_summary`.
- `run_state.json` records a `resident_memory_lifecycle` pipeline artifact.
- Added CPU-only lifecycle builder/writer tests.
- Extended resident CUDA smoke coverage so the runtime path must generate,
  summarize, and register the lifecycle artifact.
- Updated Phase 2 hardening, memory model, validation, algorithm source, and
  known-limitation docs.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m py_compile src\glass\engine\resident_memory_lifecycle.py src\glass\cli.py
.\.venv\Scripts\ruff.exe check src\glass\engine\resident_memory_lifecycle.py src\glass\cli.py tests\test_resident_memory_lifecycle.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_memory_lifecycle.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke
.\.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --out C:\glass_runs\phase2_s2_gate673_memory_lifecycle\runs_20260626_070000\default_with_lifecycle
.\.venv\Scripts\python.exe -m glass.cli resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate672_high_vram_runtime\runs_20260626_060000\default_with_resident_master_dq --candidate-run C:\glass_runs\phase2_s2_gate673_memory_lifecycle\runs_20260626_070000\default_with_lifecycle --out C:\glass_runs\phase2_s2_gate673_memory_lifecycle\runs_20260626_070000\gate673_vs_gate672_regression.json --markdown C:\glass_runs\phase2_s2_gate673_memory_lifecycle\runs_20260626_070000\gate673_vs_gate672_regression.md --min-active-frame-count 193 --max-masked-frame-count 7 --fail-on-failure
.\.venv\Scripts\python.exe -m glass.cli phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate673_memory_lifecycle\runs_20260626_070000\default_with_lifecycle --out C:\glass_runs\phase2_s2_gate673_memory_lifecycle\runs_20260626_070000\gate673_phase2_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate673_memory_lifecycle\runs_20260626_070000\gate673_phase2_mainline_audit.md --min-lights 200 --min-active-frames 193 --max-masked-frames 7 --fail-on-not-green
.\.venv\Scripts\python.exe -m glass.cli stack-engine-contract --run C:\glass_runs\phase2_s2_gate673_memory_lifecycle\runs_20260626_070000\default_with_lifecycle --scope all --expected-integration-engine cuda_resident_stack --out C:\glass_runs\phase2_s2_gate673_memory_lifecycle\runs_20260626_070000\gate673_stack_engine_contract_resident.json --markdown C:\glass_runs\phase2_s2_gate673_memory_lifecycle\runs_20260626_070000\gate673_stack_engine_contract_resident.md --require-default-ready
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Syntax check: passed.
- Ruff: passed.
- `tests/test_resident_memory_lifecycle.py`: `3 passed in 0.08 s`.
- `tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke`:
  `1 passed in 1.20 s`.
- Full pytest: `1414 passed in 64.50 s`.

## Real 200-Light Evidence

- Run:
  `C:\glass_runs\phase2_s2_gate673_memory_lifecycle\runs_20260626_070000\default_with_lifecycle`
- Lifecycle artifact:
  `C:\glass_runs\phase2_s2_gate673_memory_lifecycle\runs_20260626_070000\default_with_lifecycle\resident_memory_lifecycle.json`
- Lifecycle status: passed.
- Lifecycle group count: `1`.
- Estimated calibrated resident stack: `45.93372344970703 GiB`.
- Estimated peak: `49.608429938554764 GiB`.
- `raw_all_frames_resident=false`.
- `calibrated_stack_resident=true`.
- `registered_cache_materialized_on_disk=false`.
- Resident calibration/integration elapsed: `9.95322650007438 s`.
- Total timing elapsed: `11.585727000143379 s`.

## Regression Against Gate672

- Regression artifact:
  `C:\glass_runs\phase2_s2_gate673_memory_lifecycle\runs_20260626_070000\gate673_vs_gate672_regression.json`
- Status: passed.
- Failed checks: `[]`.
- Elapsed ratio: `0.9911025449355981`.
- Active/masked frames: `193/7`.
- Artifact/frame-accounting/frame-signature/registration/output/numerical drift
  counts: all zero.
- Component deltas:
  - light read/upload/calibrate: `3.0705415999982506 s` -> `3.0804688000353053 s`
  - resident registration/warp: `0.26889019936788827 s` -> `0.2576377998339012 s`
  - resident integration: `3.317358099971898 s` -> `3.2572361999191344 s`
  - output write: `0.23670729994773865 s` -> `0.24197500001173466 s`

## Contracts

- Phase 2 mainline audit:
  `C:\glass_runs\phase2_s2_gate673_memory_lifecycle\runs_20260626_070000\gate673_phase2_mainline_audit.json`
  - Status: passed.
  - Input light frames: `200`.
  - Active frames: `193`.
- StackEngine resident contract:
  `C:\glass_runs\phase2_s2_gate673_memory_lifecycle\runs_20260626_070000\gate673_stack_engine_contract_resident.json`
  - Status: passed.
  - Expected integration engine: `cuda_resident_stack`.
  - `pipeline_contract_dq_ledger_ready=true`.
  - `default_promotion_ready=true`.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.

## Known Limitations

- `resident_memory_lifecycle.json` is an estimated lifecycle contract derived
  from artifacts, not a live CUDA allocator trace.
- The current resident path streams raw FITS frames through reusable host/device
  buffers; it does not preload all raw frames into VRAM.
- Calibrated light frames are the primary resident stack. Future gates can use
  this artifact to prove allocator telemetry, all-raw preload experiments, or
  stronger release behavior.

## Next Step

- Continue with a substantive resident performance/correctness gate, preferably
  measured overlap for light read/H2D/calibration or a resident registration/
  integration kernel improvement guarded by the new lifecycle artifact and the
  200-light regression gate.

## Clean-Room Compliance

- Compliant.
- This gate uses only GLASS-owned runtime artifacts, timing, tests, and memory
  model rules.
- No external/proprietary source was read, summarized, copied, or reworked.
- Input image directories were not modified.
