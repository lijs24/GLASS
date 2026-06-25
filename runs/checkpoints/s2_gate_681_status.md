# S2-Gate 681 Status: RAM-Budget Native Completion Ring Policy

## Gate

- Gate: S2-Gate 681
- Status: green
- Date: 2026-06-26 Asia/Shanghai
- Scope: resident CUDA read/H2D/calibration resource-model hardening

## Completed

- Added `ram_budget_gb` to `run_resident_calibration_integration`.
- Routed `glass run --ram-budget-gb` and `glass audit --ram-budget-gb` into
  the resident CUDA runner.
- Added a conservative resident native-completion raw-ring policy:
  - explicit `--resident-native-completion-queue-buffer-frames` still wins;
  - otherwise `--ram-budget-gb` may reserve up to 25% of RAM budget for pinned
    raw FITS completion buffers;
  - RAM-budget expansion is capped by light-frame count and never shrinks the
    established runtime base.
- Added resident artifact/profile fields for raw frame bytes, RAM budget,
  budget fraction, budget cap bytes/frames, policy source, budget reason,
  planned frames, effective native queue buffer count, and bytes.
- Added focused CUDA resident test coverage for RAM-budget ring expansion.
- Updated Phase 2, integration, memory-model, validation, and algorithm-source
  docs.

## Commands Run

- `.venv\Scripts\python.exe -m compileall -q src\glass\engine\resident_cuda.py src\glass\engine\resident_light_pipeline_profile.py src\glass\cli.py tests\test_resident_cuda_run.py`
- `.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py::test_resident_native_completion_queue_buffer_frames_arg_is_preserved tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_completion_queue_buffer_frames_are_explicit tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_completion_queue_buffer_uses_ram_budget`
- `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate681_ram_budget_ring\runs_20260626_170000\ram24_auto --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --ram-budget-gb 24`
- `.venv\Scripts\glass.exe resident-runtime-compare --run queue32_default=C:\glass_runs\phase2_s2_gate680_completion_ring\runs_20260626_160000\queue32_default --run ram24_auto=C:\glass_runs\phase2_s2_gate681_ram_budget_ring\runs_20260626_170000\ram24_auto --baseline-label queue32_default --out C:\glass_runs\phase2_s2_gate681_ram_budget_ring\gate681_ram_budget_runtime_compare.json --markdown C:\glass_runs\phase2_s2_gate681_ram_budget_ring\gate681_ram_budget_runtime_compare.md`
- `.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate680_completion_ring\runs_20260626_160000\queue32_default --candidate-run C:\glass_runs\phase2_s2_gate681_ram_budget_ring\runs_20260626_170000\ram24_auto --out C:\glass_runs\phase2_s2_gate681_ram_budget_ring\gate681_ram_budget_regression_gate.json --markdown C:\glass_runs\phase2_s2_gate681_ram_budget_ring\gate681_ram_budget_regression_gate.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure`
- `.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate681_ram_budget_ring\runs_20260626_170000\ram24_auto --out C:\glass_runs\phase2_s2_gate681_ram_budget_ring\gate681_ram_budget_phase2_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate681_ram_budget_ring\gate681_ram_budget_phase2_mainline_audit.md --min-lights 200 --min-active-frames 190 --max-masked-frames 10 --fail-on-not-green`
- Direct FITS comparison script against Gate680 32-buffer default.
- `.venv\Scripts\python.exe -m ruff check src/glass/cli.py src/glass/engine/resident_cuda.py src/glass/engine/resident_light_pipeline_profile.py tests/test_resident_cuda_run.py`
- `.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_completion_queue_buffer_frames_are_explicit tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_completion_queue_buffer_uses_ram_budget tests/test_cli_smoke.py::test_resident_native_completion_queue_buffer_frames_arg_is_preserved tests/test_resident_runtime_compare.py tests/test_resident_regression_gate.py tests/test_phase2_mainline_audit.py`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused native-completion RAM-budget tests: `3 passed in 1.16 s`.
- Focused gate/audit tests: `18 passed in 1.73 s`.
- Ruff: passed.
- Full pytest: `1423 passed in 65.77 s`.

## Real 200-Light Validation

- Baseline: `C:\glass_runs\phase2_s2_gate680_completion_ring\runs_20260626_160000\queue32_default`
- Candidate: `C:\glass_runs\phase2_s2_gate681_ram_budget_ring\runs_20260626_170000\ram24_auto`
- Dataset plan: `C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json`
- Input lights: `200`
- Active/masked frames: `193 / 7`
- Candidate RAM budget: `24 GiB`
- Candidate policy source: `ram_budget_auto`
- Candidate budget reason: `ram_budget_expanded`
- Candidate raw frame bytes: `123302400`
- Candidate planned/effective raw ring buffers: `52 / 52`
- Candidate estimated/effective pinned raw bytes:
  `6411724800 / 6411724800`
- Candidate total elapsed: `12.437605500104837 s`
- Baseline total elapsed: `12.245715199969709 s`
- Candidate/baseline elapsed ratio: `1.0156699953413586`
- Candidate `light_read_upload_calibrate`: `3.8902179000433534 s`
- Baseline `light_read_upload_calibrate`: `3.391568800085224 s`
- Runtime compare best label: `queue32_default`
- Phase 2 mainline audit: passed, failed checks `[]`
- Resident regression gate: passed, failed checks `[]`
- Direct FITS comparison: `resident_master_H.fits`, weight map, coverage map,
  low rejection map, high rejection map, and DQ map were bitwise identical.

## Artifacts

- Runtime compare:
  `C:\glass_runs\phase2_s2_gate681_ram_budget_ring\gate681_ram_budget_runtime_compare.json`
- Regression gate:
  `C:\glass_runs\phase2_s2_gate681_ram_budget_ring\gate681_ram_budget_regression_gate.json`
- Phase 2 mainline audit:
  `C:\glass_runs\phase2_s2_gate681_ram_budget_ring\gate681_ram_budget_phase2_mainline_audit.json`
- FITS result comparison:
  `C:\glass_runs\phase2_s2_gate681_ram_budget_ring\gate681_result_compare_queue32_vs_ram24.json`
- Candidate run directory:
  `C:\glass_runs\phase2_s2_gate681_ram_budget_ring\runs_20260626_170000\ram24_auto`

## CUDA

- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- Driver: 596.21
- VRAM reported to GLASS: 97886 MiB

## Known Limitations

- RAM-budget expansion is not promoted as the default on this workstation:
  the 32-buffer runtime base remains the best observed path.
- The budget fraction is a conservative project default, not an adaptive live
  OS-memory-pressure controller.
- The artifact reports planned/effective raw-ring bytes, not a full process
  peak-RAM trace.
- This gate does not implement deeper double-buffered disk/decode/H2D overlap
  or a new CUDA reducer.

## Next Step

- Move from single-ring capacity tuning to a substantive read/decode/H2D
  overlap design: pinned multi-buffer staging with CPU pre-read/decode of the
  next wave while CUDA calibrates the current wave, guarded by the same real
  200-light mainline/regression/FITS-comparison evidence chain.

## Clean-Room Compliance

- No external or proprietary implementation source was inspected, copied,
  summarized, or reworked.
- Validation used GLASS-owned code, GLASS-generated artifacts, and user-owned
  benchmark data only.
- Input image directories were treated as read-only.
