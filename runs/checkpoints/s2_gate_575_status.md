# S2-Gate 575 Status: CUDA Calibrated Reference-Health Diagnostic

## Gate

- Gate: S2-Gate 575
- Objective: add an optional CUDA calibrated-sample diagnostic to resident reference health without promoting or enforcing CUDA reference scouting.
- Status: green
- Clean-room status: compliant. The implementation uses GLASS-owned scout artifacts, GLASS resident master cache arrays, GLASS calibration policy, GLASS CUDA primitives, and user data only. It does not inspect external implementation source or modify input image directories.

## Completed

- Added `cuda_calibrated_crosscheck` to `resident_reference_health.json`.
- The diagnostic uses `calibrate_tile_f32` followed by `star_grid_top_nms_candidates_f32` on the same bounded calibrated samples used by the existing reference-health check.
- Added explicit diagnostic thresholds:
  - `--resident-reference-health-cuda-calibrated-min-star-ratio`
  - `--resident-reference-health-cuda-calibrated-max-rank-fraction`
- Kept CUDA calibrated checks diagnostic-only:
  - `enforced = false`
  - recorded in artifact summaries and failed checks
  - not appended to `effective_checks`
  - cannot block a run by itself
- Fixed policy serialization for slots dataclass `CalibrationPolicy` by passing `dataclasses.asdict(policy)` to the CUDA wrapper.
- Added fake-CUDA unit coverage proving a failed CUDA calibrated diagnostic does not block a health result when CPU and CPU-calibrated effective checks pass.
- Updated registration and algorithm-source documentation.

## Commands Run

- `.venv\Scripts\python.exe -m py_compile src\glass\engine\resident_reference_health.py src\glass\cli.py tests\test_cli_smoke.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py -k "resident_reference_health"`
- `.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py`
- `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\explicit_cuda_catalog_should_fail_cuda_calibrated_early --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache --resident-reference-scout-backend cuda`
- `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_575_doctor.json`

## Test Results

- Focused resident reference-health tests: `5 passed, 64 deselected`
- CLI smoke tests: `69 passed`
- Full pytest: `1238 passed in 51.14s`
- Doctor: passed

## Real 200-Light Validation

Bad explicit CUDA scout run:

- Path: `C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\explicit_cuda_catalog_should_fail_cuda_calibrated_early`
- Exit code: `2`
- Failed stage: `resident_reference_health`
- Total elapsed: `1.755732399993576 s`
- Completed stages: `resident_reference_scout`
- CPU raw reference: `F000225`
- Bad selected reference: `F000215`
- CPU selected star ratio: `40/51 = 0.7843137254901961`
- CPU selected rank fraction: `0.5238095238095238`
- CPU-calibrated reference: `F000079`
- CPU-calibrated selected star ratio: `13/30 = 0.43333333333333335`
- CPU-calibrated selected rank fraction: `0.8412698412698413`
- CUDA-calibrated diagnostic reference: `F000114`
- CUDA-calibrated selected star ratio: `0.8125`
- CUDA-calibrated selected rank fraction: `0.746031746031746`
- CUDA-calibrated failed checks: `selected_reference_cuda_calibrated_rank_fraction`
- Effective blocking checks remain CPU raw and CPU-calibrated checks only.

Safe default run:

- Path: `C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass`
- Exit code: `0`
- `resident_reference_health.json`: not written, because default CPU scout resolves reference-health `auto` to `off`
- Total elapsed: `7.975543199805543 s`
- Accepted frames: `193/200`
- Rejected frames: `F000160`, `F000213`, `F000214`, `F000215`, `F000216`, `F000217`, `F000218`
- Master path: `C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass\integration\resident_master_H.fits`
- Master SHA256: `3c5f942f3be7fe629c6be55c1e2d14a94b8f23128c057384f03df8f09a38333d`
- Output maps written: master, weight, coverage, low rejection, high rejection, DQ
- Stage timing highlights:
  - light read/upload/calibrate: `2.4911861000582576 s`
  - resident registration/warp: `0.26176169991958886 s`
  - resident local normalization: `1.2233816999942064 s`
  - resident integration: `0.35036330006551 s`

## CUDA

- CUDA available: yes
- Native extension loaded: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- Doctor recommendation: `cuda`

## Artifacts

- Checkpoint: `runs/checkpoints/s2_gate_575_status.md`
- Doctor report: `runs/checkpoints/s2_gate_575_doctor.json`
- Bad scout run: `C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\explicit_cuda_catalog_should_fail_cuda_calibrated_early`
- Safe default run: `C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass`
- Updated docs:
  - `docs/registration_model.md`
  - `docs/algorithm_sources.md`

## Known Limitations

- CUDA calibrated reference-health is diagnostic-only in this gate and is not enforced.
- The CUDA catalog primitive still has grid/top-k semantics, so it can rank frames differently from CPU calibrated star detection.
- This gate does not promote CUDA reference scouting to default.
- This gate does not optimize the main 200-light execution path; it adds evidence needed before a future reference-selector promotion.

## Next Step

Return to the Phase 2 main line with a substantive gate: real 200-light A/B and StackEngine/DQ pipeline completeness, or a promotion candidate that improves default execution while preserving the established master SHA and accepted-frame contract.
