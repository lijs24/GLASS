# S2-Gate 582 Status: Resident Calibrated-Light DQ Ledger

## Gate

- Gate: S2-Gate 582
- Title: Resident calibrated-light DQ ledger
- Status: green
- Date: 2026-06-23

## Completed Content

- Extended resident `calibration_artifacts.json` calibrated-light rows with
  first-class DQ/mask contract evidence:
  - `source_dq_contract`
  - `frame_mask_contract`
  - `resident_dq_mask_contract`
  - `dq_contract_source`
  - `dq_contract_ok`
- Added `resident_calibrated_light_embedded_dq_mask_contract` to
  `pipeline-contract` when embedded row-level contracts are present.
- Preserved compatibility with older artifacts: when embedded row contracts are
  absent, pipeline-contract still falls back to external resident DQ evidence.
- Updated Phase 2 documentation and algorithm-source independence log.

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_contract.py -k "resident_native_calibration_artifacts or resident_source_dq or source_dq_fails"`
- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py -k "translation_aligns_shifted_pair or run_similarity_triangle"`
- `.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_calibration_artifacts.py src\glass\report\pipeline_contract.py tests\test_pipeline_contract.py tests\test_resident_cuda_run.py`
- `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate582_resident_calibration_ledger\default_v3 --backend cuda --memory-mode resident --resident-runtime-preset throughput-v3-io --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused pipeline-contract tests: `6 passed, 38 deselected`
- Focused resident CUDA tests: `2 passed, 102 deselected`
- Combined focused verification: `11 passed, 137 deselected`
- Ruff: `All checks passed!`
- Full pytest: `1249 passed in 52.57s`

## Real 200-Light Validation

- Run:
  `C:\glass_runs\phase2_s2_gate582_resident_calibration_ledger\default_v3`
- Hash parity artifact:
  `C:\glass_runs\phase2_s2_gate582_resident_calibration_ledger\hash_parity_vs_gate579.json`
- Runtime: `8.19045490003191 s`
- Runtime preset: `throughput-v3-io`
- `calibration_artifacts.json` resident calibrated-light rows: `200`
- Rows with passing `resident_dq_mask_contract`: `200 / 200`
- Rows with linked `resident_source_dq_execution`: `200 / 200`
- Rows with linked `resident_frame_masks`: `200 / 200`
- New pipeline-contract check:
  `resident_calibrated_light_embedded_dq_mask_contract` passed with
  `embedded_contract_count=200`.
- Existing resident frame-mask admission remained green:
  `193` active frames and `7` masked frames.
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

## Known Limitations

- This gate strengthens artifact contracts and pipeline invariants only.
- It does not add a new source-DQ detector, change frame admission, change
  registration/warp/LN/rejection/integration math, or optimize runtime.
- Older resident artifacts remain supported through fallback inference, so the
  new row-level contract becomes authoritative for newly generated artifacts.

## Next Step

- Continue default-path engineering: use the row-level resident calibration
  ledger in frame accounting/report surfaces, and continue tightening DQ/mask
  invariants without changing science pixels unless separately validated.

## Clean-Room Compliance

- Compliant. This gate uses only GLASS-generated resident source-DQ,
  frame-mask, calibration, pipeline, and integration artifacts.
- No official external stacking or PixInsight implementation source was read,
  summarized, copied, or reworked.
- Input image directories were treated as read-only.
