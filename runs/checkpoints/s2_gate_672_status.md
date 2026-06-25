# S2-Gate 672 Status: Resident Master DQ Sidecars And High-VRAM Runtime Check

## Gate

- Gate: S2-Gate 672
- Status: green checkpoint
- Scope: resident CUDA master calibration DQ artifacts plus real high-VRAM
  scheduling check
- Branch: `main`

## Completed Work

- Added resident CUDA master DQ FITS sidecar materialization when
  `calibration_artifacts.json` is written through the resident writer path.
- Resident master bias/dark/flat records now include:
  - `dq_mask_path`
  - `dq_summary`
  - `resident_master_dq_contract`
  - `stack_engine_dq_provenance.output_dq_summary`
  - `dq_provenance_summary.output_dq_summary`
- The sidecar marks non-finite output master pixels as `NO_DATA`. It does not
  synthesize per-pixel low/high master rejection touches; those remain in
  resident DQ provenance.
- `glass resident-calibration-artifacts` now uses the writer path for the
  default output and materializes the same sidecars.
- Unreadable legacy/fixture resident master cache placeholders now produce a
  failed sidecar contract instead of aborting calibration artifact generation.
- Ran a real 200-light high-VRAM deep-queue candidate and rejected it as a
  default strategy because it regressed runtime.

## Commands Run

- Syntax:
  `.\.venv\Scripts\python.exe -m py_compile src\glass\engine\resident_calibration_artifacts.py src\glass\cli.py`
- Ruff:
  `.\.venv\Scripts\ruff.exe check src\glass\engine\resident_calibration_artifacts.py src\glass\cli.py tests\test_resident_calibration_artifacts.py tests\test_resident_cuda_run.py`
- Focused resident calibration artifact tests:
  `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_calibration_artifacts.py tests\test_resident_stack_surface.py`
- Resident CUDA smoke:
  `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke`
- Failed high-VRAM deep-queue candidate:
  `.\.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-prefetch-frames 64 --resident-prefetch-workers 24 --resident-calibration-batch-frames 32 --resident-native-completion-wave-fill-us 50 --out C:\glass_runs\phase2_s2_gate672_high_vram_runtime\runs_20260626_060000\candidate_deep_queue`
- Deep-queue regression:
  `.\.venv\Scripts\python.exe -m glass.cli resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate671_master_dq_artifacts\runs_20260626_050000\resident_default_guard --candidate-run C:\glass_runs\phase2_s2_gate672_high_vram_runtime\runs_20260626_060000\candidate_deep_queue --out C:\glass_runs\phase2_s2_gate672_high_vram_runtime\runs_20260626_060000\gate672_deep_queue_vs_gate671.json --markdown C:\glass_runs\phase2_s2_gate672_high_vram_runtime\runs_20260626_060000\gate672_deep_queue_vs_gate671.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure`
- Real 200-light default with resident master DQ:
  `.\.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --out C:\glass_runs\phase2_s2_gate672_high_vram_runtime\runs_20260626_060000\default_with_resident_master_dq`
- Default regression:
  `.\.venv\Scripts\python.exe -m glass.cli resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate671_master_dq_artifacts\runs_20260626_050000\resident_default_guard --candidate-run C:\glass_runs\phase2_s2_gate672_high_vram_runtime\runs_20260626_060000\default_with_resident_master_dq --out C:\glass_runs\phase2_s2_gate672_high_vram_runtime\runs_20260626_060000\gate672_default_master_dq_vs_gate671.json --markdown C:\glass_runs\phase2_s2_gate672_high_vram_runtime\runs_20260626_060000\gate672_default_master_dq_vs_gate671.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure`
- Phase 2 mainline audit:
  `.\.venv\Scripts\python.exe -m glass.cli phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate672_high_vram_runtime\runs_20260626_060000\default_with_resident_master_dq --out C:\glass_runs\phase2_s2_gate672_high_vram_runtime\runs_20260626_060000\gate672_phase2_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate672_high_vram_runtime\runs_20260626_060000\gate672_phase2_mainline_audit.md --fail-on-not-green`
- StackEngine resident contract:
  `.\.venv\Scripts\python.exe -m glass.cli stack-engine-contract --run C:\glass_runs\phase2_s2_gate672_high_vram_runtime\runs_20260626_060000\default_with_resident_master_dq --out C:\glass_runs\phase2_s2_gate672_high_vram_runtime\runs_20260626_060000\gate672_stack_engine_contract_resident.json --markdown C:\glass_runs\phase2_s2_gate672_high_vram_runtime\runs_20260626_060000\gate672_stack_engine_contract_resident.md --scope all --expected-integration-engine cuda_resident_stack`
- Pipeline-contract compatibility rerun:
  `.\.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_contract.py::test_pipeline_contract_accepts_resident_native_calibration_artifacts tests\test_pipeline_contract.py::test_pipeline_contract_maps_resident_source_dq_to_resident_calibrated_lights tests\test_pipeline_contract.py::test_pipeline_contract_fails_frame_accounting_resident_dq_ledger_drift tests\test_pipeline_contract.py::test_pipeline_contract_fails_frame_accounting_resident_dq_lifecycle_drift tests\test_pipeline_contract.py::test_pipeline_contract_fails_resident_calibrated_light_dq_when_source_dq_fails`
- Full pytest:
  `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Syntax check: passed.
- Ruff: passed.
- Resident calibration artifact/stack-surface focused tests: `7 passed`.
- Resident CUDA smoke: `1 passed`.
- Pipeline-contract compatibility rerun: `5 passed`.
- Focused resident calibration/CUDA/StackEngine suite: `6 passed`.
- Full pytest: `1411 passed in 64.01 s`.

## Real 200-Light Evidence

- Evidence root:
  `C:\glass_runs\phase2_s2_gate672_high_vram_runtime\runs_20260626_060000`
- Candidate default run:
  `C:\glass_runs\phase2_s2_gate672_high_vram_runtime\runs_20260626_060000\default_with_resident_master_dq`
- Master DQ sidecars:
  - `dq_master_resident_bias_H_H_9600x6422_bias-G4ed2155578_dark-G59e41ba802_flat-G4f1de65e6a.fits`
  - `dq_master_resident_dark_H_H_9600x6422_bias-G4ed2155578_dark-G59e41ba802_flat-G4f1de65e6a.fits`
  - `dq_master_resident_flat_H_H_9600x6422_bias-G4ed2155578_dark-G59e41ba802_flat-G4f1de65e6a.fits`
- Each sidecar exists, has size `123307200` bytes, and records
  `dq_summary={"valid": 61651200}` with `resident_master_dq_contract.passed=true`.
- Default regression versus Gate671:
  - status: passed
  - failed checks: `[]`
  - elapsed ratio: `1.0533260571398728`
  - artifact differences: `0`
  - frame-accounting differences: `0`
  - frame-signature differences: `0`
  - registration differences: `0`
  - output differences: `0`
  - output numerical drift: `0`
- Default run component timing:
  - light read/upload/calibrate: `3.0705415999982506 s`
  - registration/warp: `0.26889019936788827 s`
  - local normalization: `0.35174410010222346 s`
  - resident integration: `3.317358099971898 s`
  - output write: `0.23670729994773865 s`
- Phase 2 mainline audit:
  - status: passed
  - input light frames: `200`
  - active frames: `193`
- StackEngine resident contract:
  - status: passed
  - expected integration engine: `cuda_resident_stack`
  - pipeline DQ ledger ready: `true`
  - default promotion ready: `true`

## Rejected High-VRAM Candidate

- Run:
  `C:\glass_runs\phase2_s2_gate672_high_vram_runtime\runs_20260626_060000\candidate_deep_queue`
- Changed scheduling:
  - prefetch frames: `64`
  - prefetch workers: `24`
  - calibration batch frames: `32`
  - native completion wave fill: `50 us`
- Regression versus Gate671:
  - status: failed
  - failed checks: `runtime_within_threshold`
  - elapsed ratio: `1.17939080551414`
- Component timing:
  - light read/upload/calibrate: `4.3863005000166595 s`
  - resident integration: `3.2730879000155255 s`
- Interpretation: deeper queues and larger batches are not a safe default on
  this dataset/hardware. The candidate preserved frame accounting but was too
  slow, so no preset/default change was promoted.

## CUDA

- CUDA available: yes.
- Native backend: available.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.

## Known Limitations

- Resident master DQ sidecars currently mark output-master validity only:
  non-finite pixels become `NO_DATA`.
- Resident per-pixel master low/high rejection-touched maps are not yet
  materialized; rejection sample accounting remains in resident DQ provenance.
- If a legacy diagnostic cache path is present but not readable as `.npy`, the
  sidecar contract fails audibly while the broader calibration artifact remains
  buildable.
- The deep-queue candidate is explicitly rejected and must not be described as
  a speed optimization.

## Next Step

- Return to the measured hot path: resident hardened winsorized reducer
  scalability/performance, or a targeted light pipeline overlap change backed
  by real A/B evidence.

## Clean-Room Compliance

Compliant. This gate used GLASS-owned DQ flags, resident calibration artifacts,
FITS writers, tests, and user-owned 200-light benchmark artifacts. It did not
inspect, copy, summarize, or rework external proprietary implementation source,
and it did not modify input directories.
