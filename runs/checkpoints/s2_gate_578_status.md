# S2-Gate 578 Status: Resident Calibrated-Light DQ Contract Closure

## Gate

S2-Gate 578

## Completed

- Closed a resident CUDA DQ/mask contract gap in `pipeline_contract.json`.
- Resident calibrated-light rows can now satisfy their DQ contract through
  passing `resident_source_dq_execution.json` evidence when calibrated light
  FITS and per-frame DQ-mask disk caches are intentionally not materialized.
- Added row-level evidence:
  - `dq_contract_source`;
  - `disk_dq_contract_ok`;
  - `resident_source_dq_contract_ok`;
  - `resident_source_dq_contract`.
- Added `resident_calibrated_light_dq_contract`, enabled when resident
  source-DQ execution evidence exists.
- Added positive and negative pipeline-contract tests.
- Updated Phase 2 hardening notes and algorithm independence log.

## Commands

- `.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_contract.py -q`
- `.venv\Scripts\glass.exe pipeline-contract --run C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass --out C:\glass_runs\phase2_s2_gate578_resident_calibrated_dq_contract\pipeline_contract.json --markdown C:\glass_runs\phase2_s2_gate578_resident_calibrated_dq_contract\pipeline_contract.md`
- `.venv\Scripts\glass.exe pipeline-contract --run C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass --out C:\glass_runs\phase2_s2_gate578_resident_calibrated_dq_contract\pipeline_contract_pixel_verify.json --markdown C:\glass_runs\phase2_s2_gate578_resident_calibrated_dq_contract\pipeline_contract_pixel_verify.md --pixel-verify --pixel-verify-tile-size 2048`
- `.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_contract.py`
- `.venv\Scripts\python.exe -m pytest -q`
- `git diff --check`

Note: `.venv\Scripts\glass.exe cuda-info` was tried as a convenience command,
but this CLI does not currently expose `cuda-info`; CUDA status was read
through the existing `glass_cuda` Python wrapper instead.

## Test Results

- Focused pipeline-contract tests: `44 passed in 1.60s`.
- Full test suite: `1241 passed in 48.53s`.
- `git diff --check`: passed.

## Real 200-Light Validation

- Source run:
  `C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass`
- Regenerated contract:
  `C:\glass_runs\phase2_s2_gate578_resident_calibrated_dq_contract\pipeline_contract.json`
- Markdown:
  `C:\glass_runs\phase2_s2_gate578_resident_calibrated_dq_contract\pipeline_contract.md`
- Pipeline contract status: `passed`.
- Pixel-verified pipeline contract:
  `C:\glass_runs\phase2_s2_gate578_resident_calibrated_dq_contract\pipeline_contract_pixel_verify.json`
- Pixel-verified status: `passed`, `25` checks, `0` failed.
- Resident calibrated-light rows: `200`.
- `dq_contract_ok`: `200 / 200`.
- `resident_source_dq_contract_ok`: `200 / 200`.
- `disk_dq_contract_ok`: `0 / 200`.
- `dq_contract_source`: `resident_source_dq_execution`.
- New check `resident_calibrated_light_dq_contract`: `passed`.
- Pixel checks:
  - `integration_dq_map_pixels_match_summary`: `passed`;
  - `integration_rejection_sample_counts_match_maps`: `passed`;
  - `integration_sample_accounting_closure`: `passed`.

## CUDA

- CUDA available: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.
- This gate did not change CUDA kernels or image math.

## Known Limitations

- This gate closes the audit contract for resident calibrated-light DQ
  semantics; it does not add new source-DQ detection modes.
- It does not change calibration, registration, warp, LN, rejection,
  integration, frame admission, CUDA kernels, or output pixels.
- The next substantive work should return to StackEngine default-path
  completeness, real 200-light regression, or resident registration/warp
  throughput and numerical consistency.

## Next Step

Run the next substantive Phase 2 gate against the default StackEngine/resident
path: prefer a real 200-light regression that exercises DQ/mask pipeline
contracts and then targets registration/warp resident throughput or numerical
parity if the validation remains green.

## Clean-Room Compliance

- Used only GLASS source code, GLASS-generated artifacts, and user-owned
  200-light run outputs.
- Did not read, copy, summarize, or rework external proprietary source code.
- Did not modify input image directories.
- Did not change public claims beyond measured GLASS artifacts.
