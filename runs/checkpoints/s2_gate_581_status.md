# S2-Gate 581 Status: Native Completion Runtime Preset

## Gate

- Gate: S2-Gate 581
- Title: Native completion runtime preset
- Status: green
- Date: 2026-06-23

## Completed Content

- Added explicit resident runtime preset `throughput-v4-native-completion`.
- Added CLI controls:
  - `--resident-native-completion-calibration off|on`
  - `--resident-native-completion-wave-fill-us N`
- Kept default resident runtime preset as `throughput-v3-io`.
- Updated resident CUDA reporting so CLI opt-in records
  `native_completion_calibration_policy=cli_enabled`.
- Preserved legacy environment-variable opt-in for:
  - `GLASS_RESIDENT_NATIVE_COMPLETION_CALIBRATION`
  - `GLASS_RESIDENT_NATIVE_COMPLETION_WAVE_FILL_US`
- Updated benchmark-contract route matching so future contracts can recognize
  `--resident-runtime-preset throughput-v4-native-completion` from
  `resident_artifacts.json`.
- Updated Phase 2 documentation and algorithm-source log.

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py -k "resident_runtime_preset"`
- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py -k "native_u16_completion_calibration or native_completion_runtime_preset"`
- `.venv\Scripts\python.exe -m pytest -q tests\test_acceptance_audit.py -k "runtime_preset_from_artifact"`
- `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate581_native_completion_preset\throughput_v4_native_completion --backend cuda --memory-mode resident --resident-runtime-preset throughput-v4-native-completion --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- `.venv\Scripts\python.exe -m ruff check src\glass\cli.py src\glass\engine\resident_cuda.py src\glass\report\benchmark_contract.py tests\test_acceptance_audit.py tests\test_cli_smoke.py tests\test_resident_cuda_run.py`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused CLI preset tests: `7 passed, 63 deselected`
- Focused CUDA completion tests: `2 passed, 102 deselected`
- Focused acceptance-audit runtime-preset tests: `3 passed, 47 deselected`
- Ruff: `All checks passed!`
- Full pytest: `1249 passed in 52.89s`

## Real 200-Light Validation

- Candidate run:
  `C:\glass_runs\phase2_s2_gate581_native_completion_preset\throughput_v4_native_completion`
- Baseline run:
  `C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default`
- Hash parity artifact:
  `C:\glass_runs\phase2_s2_gate581_native_completion_preset\hash_parity_vs_gate579.json`
- Candidate runtime: `7.867076899972744 s`
- Gate579 default runtime: `7.746504300041124 s`
- Candidate light read/upload/calibrate: `3.095646100002341 s`
- Gate579 default light read/upload/calibrate: `2.508018699940294 s`
- Candidate registration/warp: `0.2611523000523448 s`
- Candidate local normalization: `1.0705019999295473 s`
- Candidate integration: `0.31247899995651096 s`
- All six integration FITS outputs matched Gate579 SHA256:
  - `resident_master_H.fits`
  - `resident_coverage_map_H.fits`
  - `resident_dq_map_H.fits`
  - `resident_weight_map_H.fits`
  - `resident_low_rejection_map_H.fits`
  - `resident_high_rejection_map_H.fits`

## CUDA Status

- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- Driver version: 596.21
- VRAM: 97886 MiB

## Decision

- `throughput-v4-native-completion` is accepted as a reproducible explicit A/B
  preset.
- It is not promoted to default because the real 200-light validation was about
  `1.6%` slower than `throughput-v3-io` on this workstation.
- The default route remains `throughput-v3-io`.

## Known Limitations

- This gate does not improve default runtime; it makes a previously hidden
  completion-queue route auditable and reproducible.
- The completion route may still be useful on different storage/CPU scheduling
  conditions, but it requires fresh real benchmark evidence before promotion.
- No calibration, registration, LN, rejection, or integration math changed.

## Next Step

- Return to default-path engineering work: StackEngine default surfaces,
  DQ/mask pipeline contract, resident registration/warp orchestration, and
  200-light numerical/performance regression checks.

## Clean-Room Compliance

- Compliant. This gate uses only GLASS runtime code, GLASS artifacts, and
  user-owned 200-light benchmark outputs.
- No official external stacking or PixInsight implementation source was read,
  summarized, copied, or reworked.
- Input image directories were treated as read-only.
