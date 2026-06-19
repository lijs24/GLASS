# S2-Gate 415 Status

Gate: S2-Gate 415 - Resident Parity Summary Artifact

Status: completed; parity blocker localized

## Completed Work

- Added `glass resident-parity-summary`.
- Added `src/glass/report/resident_parity_summary.py`.
- Added focused tests in `tests/test_resident_parity_summary.py`.
- Updated `docs/phase2_algorithm_hardening.md` with S2-Gate 415.
- Updated `docs/algorithm_sources.md` with the runtime-validation harness source record.
- Ran the new command on the S2-Gate 414 CPU/resident synthetic validation artifacts.
- Ran an additional CUDA resident `external_matrix` validation using the CPU `registration_results.json` transform set.

## Commands

- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_parity_summary.py`
- `.venv\Scripts\python.exe -m ruff check src\glass\report\resident_parity_summary.py tests\test_resident_parity_summary.py src\glass\cli.py`
- `.venv\Scripts\python.exe -m glass.cli audit --root runs\checkpoints\s2_gate_414_runtime_validation_source --out runs\checkpoints\s2_gate_415_runtime_validation_cuda_external_cpu_transform --backend cuda --tile-size 128 --memory-mode resident --resident-registration external_matrix --resident-registration-results runs\checkpoints\s2_gate_414_runtime_validation_cpu\registration_results.json --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-winsorized-mode hardened_cpu_parity --resident-output-maps audit`
- `.venv\Scripts\python.exe -m glass.cli compare --glass runs\checkpoints\s2_gate_415_runtime_validation_cuda_external_cpu_transform\integration\resident_master_H.fits --reference runs\checkpoints\s2_gate_414_runtime_validation_cpu\integration\master_H.fits --out runs\checkpoints\s2_gate_415_external_cpu_transform_compare.html --glass-label cuda_resident_external_cpu_transform --reference-label cpu_tile --glass-coverage-map runs\checkpoints\s2_gate_415_runtime_validation_cuda_external_cpu_transform\integration\resident_coverage_map_H.fits --min-coverage 1 --diagnostics-dir runs\checkpoints\s2_gate_415_external_cpu_transform_compare_diagnostics --ignore-border-px 8`
- `.venv\Scripts\python.exe -m glass.cli resident-parity-summary --cpu-run runs\checkpoints\s2_gate_414_runtime_validation_cpu --resident-run runs\checkpoints\s2_gate_414_runtime_validation_cuda_hardened --compare-json runs\checkpoints\s2_gate_414_runtime_validation_compare_hardened.json --out runs\checkpoints\s2_gate_415_triangle_registration_parity_summary.json --markdown runs\checkpoints\s2_gate_415_triangle_registration_parity_summary.md --resident-label cuda_resident_triangle_hardened --max-rms-diff 0.1 --max-relative-rms-diff 0.001 --max-rejected-sample-delta 64`
- `.venv\Scripts\python.exe -m glass.cli resident-parity-summary --cpu-run runs\checkpoints\s2_gate_414_runtime_validation_cpu --resident-run runs\checkpoints\s2_gate_415_runtime_validation_cuda_external_cpu_transform --compare-json runs\checkpoints\s2_gate_415_external_cpu_transform_compare.json --out runs\checkpoints\s2_gate_415_external_cpu_transform_parity_summary.json --markdown runs\checkpoints\s2_gate_415_external_cpu_transform_parity_summary.md --resident-label cuda_resident_external_cpu_transform --max-rms-diff 0.1 --max-relative-rms-diff 0.001 --max-rejected-sample-delta 64`
- `.venv\Scripts\python.exe -m glass.cli resident-parity-summary --help`

## Test Results

- Focused pytest: 3 passed.
- Ruff: passed.

## Runtime Validation Results

Synthetic source: `runs/checkpoints/s2_gate_414_runtime_validation_source`

CPU baseline:

- Run: `runs/checkpoints/s2_gate_414_runtime_validation_cpu`
- Backend: `cpu`
- Reference frame: `F000016`
- Rejection: `winsorized_sigma`
- Total elapsed: `41.93859020000673` s

Resident triangle hardened:

- Run: `runs/checkpoints/s2_gate_414_runtime_validation_cuda_hardened`
- Reference frame: `F000013`
- `parity_passed`: false
- Failed checks:
  - `registration_reference_match`
  - `compare_rms_within_limit`
  - `compare_relative_rms_within_limit`
  - `rejected_sample_delta_within_limit`
  - `resident_result_contract_passed`
- RMS diff vs CPU: `40.91291220023316`
- Relative RMS diff vs CPU: `0.18602955427418083`
- Rejected-sample delta vs CPU: `2667`

Resident external CPU transform hardened:

- Run: `runs/checkpoints/s2_gate_415_runtime_validation_cuda_external_cpu_transform`
- Registration source: CPU `registration_results.json`
- Reference frame: `F000016`
- `parity_passed`: true
- Top-level `passed`: false, because `resident_result_contract_passed` remains false.
- RMS diff vs CPU: `0.06858672377130552`
- Relative RMS diff vs CPU: `0.0003118613896233379`
- P99 absolute diff vs CPU: `0.1982856750488282`
- Rejected-sample delta vs CPU: `-19`
- Total elapsed: `0.2904634000151418` s

## Findings

- The dominant synthetic mismatch from S2-Gate 414 was resident triangle registration/reference selection, not calibration or hardened winsorized rejection.
- With the CPU transform set forced into resident `external_matrix`, CUDA resident reaches near-parity against CPU tiled output under the gate thresholds.
- The resident result contract still fails on the external-transform run. That failure is now visible as a separate contract blocker, not conflated with numerical parity.
- The next runtime fix should make the default resident registration path preserve/adopt the same accepted reference-frame policy or provide an auditable transform handoff, then repair the resident result-contract failure for external-matrix near-parity outputs.

## CUDA

- CUDA available during the validation.
- Native extension loaded.
- GPU from previous doctor artifact: NVIDIA RTX PRO 6000 Blackwell Workstation Edition, compute capability 12.0, VRAM 97886 MiB, driver 596.21.

## Artifacts

- Triangle parity JSON: `runs/checkpoints/s2_gate_415_triangle_registration_parity_summary.json`
- Triangle parity Markdown: `runs/checkpoints/s2_gate_415_triangle_registration_parity_summary.md`
- External transform run: `runs/checkpoints/s2_gate_415_runtime_validation_cuda_external_cpu_transform`
- External transform compare: `runs/checkpoints/s2_gate_415_external_cpu_transform_compare.html`
- External transform parity JSON: `runs/checkpoints/s2_gate_415_external_cpu_transform_parity_summary.json`
- External transform parity Markdown: `runs/checkpoints/s2_gate_415_external_cpu_transform_parity_summary.md`

## Known Limitations

- The run is still synthetic, not the 200-light benchmark.
- Local normalization stayed disabled to isolate registration, warp, DQ, and rejection behavior.
- No CUDA kernel changed in this gate.
- Large runtime validation directories are ignored by Git; committed artifacts are the compact compare/parity summaries.

## Next Step

S2-Gate 416 should fix the resident runtime path now localized by this gate:

1. Make resident default registration/reference selection agree with accepted CPU/quality reference policy or consume a formal transform handoff before integration.
2. Fix `resident_result_contract` so near-parity external-matrix resident outputs can pass contract checks when all required maps/provenance are present.
3. Re-run `resident-parity-summary` on synthetic data, then on the 200-light benchmark or a documented 200-light subset/full run.

## Clean-Room Compliance

This gate consumed only GLASS-generated synthetic data and GLASS-owned run/compare artifacts. It did not read or modify user image directories and did not inspect external proprietary source.
