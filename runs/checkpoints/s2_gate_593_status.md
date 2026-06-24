# S2-Gate 593 Status: Source-DQ Sidecar Scan Contract

Status: passed
Date: 2026-06-24

## Completed

- Added a conservative metadata-scan skip rule for explicit source-DQ sidecar
  directories.
- Files under a path component named `source_dq` or `source-dq` are skipped
  before frame ids are assigned.
- Manifest output now records:
  - top-level `skipped` diagnostics;
  - `summary.skipped_count`.
- Frame ids remain contiguous for included science/calibration frames.
- `glass plan --source-dq-manifest` still binds skipped source-DQ sidecars to
  the matching light frame through the explicit manifest.
- Added metadata, planner, and CLI tests proving sidecars no longer pollute the
  manifest as unknown frames.
- Updated Phase 2 hardening docs and the algorithm-source independence log.

## Commands Run

- Focused tests:
  `.\.venv\Scripts\python.exe -m pytest -q tests/test_fits_metadata.py::test_scan_tree_skips_source_dq_sidecar_directory tests/test_plan_builder.py::test_processing_plan_binds_source_dq_manifest_to_light_frame tests/test_cli_smoke.py::test_cli_synthetic_source_dq_manifest_binds_into_plan`
- Lint:
  `.\.venv\Scripts\python.exe -m ruff check src\glass\metadata\scanner.py tests\test_fits_metadata.py tests\test_plan_builder.py tests\test_cli_smoke.py`
- Full test suite:
  `.\.venv\Scripts\python.exe -m pytest -q`
- Synthetic CLI validation:
  `glass synthetic --out C:\glass_runs\phase2_s2_gate593_source_dq_scan_contract\synthetic_data --frames 4 --width 32 --height 24 --filter H --source-dq-sidecars --source-dq-light-index 1 --source-dq-y 5 --source-dq-x 7`
- Synthetic scan:
  `glass scan --root C:\glass_runs\phase2_s2_gate593_source_dq_scan_contract\synthetic_data --out C:\glass_runs\phase2_s2_gate593_source_dq_scan_contract\manifest.json`
- Synthetic plan:
  `glass plan --manifest C:\glass_runs\phase2_s2_gate593_source_dq_scan_contract\manifest.json --out C:\glass_runs\phase2_s2_gate593_source_dq_scan_contract\processing_plan.json --source-dq-manifest C:\glass_runs\phase2_s2_gate593_source_dq_scan_contract\synthetic_data\source_dq_manifest.json`

## Test Results

- Focused tests: 3 passed in 0.51 s.
- Ruff: all checks passed.
- Full pytest: 1264 passed in 55.62 s.

## Synthetic Validation

- Artifact directory:
  `C:\glass_runs\phase2_s2_gate593_source_dq_scan_contract`
- Validation summary:
  `C:\glass_runs\phase2_s2_gate593_source_dq_scan_contract\gate593_validation_summary.json`
- Manifest frame count: 13.
- Manifest skipped count: 1.
- Skipped reason: `source_dq_sidecar_directory`.
- Unknown frame count: 0.
- Bound source-DQ light count: 1.
- Bound light:
  `C:\glass_runs\phase2_s2_gate593_source_dq_scan_contract\synthetic_data\light\light_001.fits`
- Bound mask:
  `C:\glass_runs\phase2_s2_gate593_source_dq_scan_contract\synthetic_data\source_dq\light_001_dq.fits`
- Processing plan executable: true.

## Real 200-Light Baseline

The 200-light resident benchmark was not rerun for this gate because the change
only affects metadata scan behavior when an explicit `source_dq` / `source-dq`
sidecar directory exists under the scan root. It does not change resident CUDA
calibration, registration, local normalization, rejection, or integration
execution on the existing M38 benchmark plan. Gate592 remains the latest fresh
200-light runtime/result evidence.

## CUDA

- CUDA not required for this gate.
- CUDA remains optional; CPU-only scan/plan behavior is covered by tests.

## Artifacts

- `C:\glass_runs\phase2_s2_gate593_source_dq_scan_contract\synthetic_data`
- `C:\glass_runs\phase2_s2_gate593_source_dq_scan_contract\manifest.json`
- `C:\glass_runs\phase2_s2_gate593_source_dq_scan_contract\processing_plan.json`
- `C:\glass_runs\phase2_s2_gate593_source_dq_scan_contract\gate593_validation_summary.json`

## Known Limitations

- The scanner only skips explicit `source_dq` / `source-dq` directories. It does
  not skip every `*_dq.fits` filename because that could accidentally exclude
  real user frames.
- Nonstandard sidecar layouts should continue to use explicit source-DQ
  manifests; future work can add CLI include/ignore policies for those layouts.
- This gate does not change scientific image math or resident CUDA performance.

## Next Step

Return to a substantive StackEngine or resident execution-path gate: either
advance StackEngine as the default master-frame/light-integration surface, or
reduce resident registration/LN orchestration while preserving the Gate592
200-light baseline.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned metadata scanning and DQ input-contract
logic plus GLASS-generated synthetic artifacts. It does not read, copy,
summarize, or rework proprietary source code.
