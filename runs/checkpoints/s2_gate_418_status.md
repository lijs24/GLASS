# S2-Gate 418 Status: Resident Registration Matrix Compare

## Gate

S2-Gate 418: Resident Registration Matrix Compare.

## Completed Work

- Added `src/glass/report/resident_registration_matrix_compare.py`.
- Added `glass resident-registration-matrix-compare`.
- Added tests in `tests/test_resident_registration_matrix_compare.py`.
- Compared S2-Gate 414 CPU registration against:
  - S2-Gate 415 resident `external_matrix` CPU-transform handoff;
  - S2-Gate 417 quality-reference resident triangle registration.
- Updated Phase 2 gate documentation and algorithm-source records.

## Commands

- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_registration_matrix_compare.py`
- `.venv\Scripts\python.exe -m ruff check src\glass\report\resident_registration_matrix_compare.py tests\test_resident_registration_matrix_compare.py src\glass\cli.py`
- `.venv\Scripts\python.exe -m glass.cli resident-registration-matrix-compare --help`
- `.venv\Scripts\python.exe -m glass.cli resident-registration-matrix-compare --baseline-registration runs\checkpoints\s2_gate_414_runtime_validation_cpu --candidate-registration runs\checkpoints\s2_gate_415_runtime_validation_cuda_external_cpu_transform --baseline-label cpu_tile --candidate-label cuda_resident_external_cpu_transform --out runs\checkpoints\s2_gate_418_external_cpu_transform_matrix_compare.json --markdown runs\checkpoints\s2_gate_418_external_cpu_transform_matrix_compare.md --max-translation-delta-px 0.001 --max-matrix-delta-frobenius 0.001 --fail-on-failure`
- `.venv\Scripts\python.exe -m glass.cli resident-registration-matrix-compare --baseline-registration runs\checkpoints\s2_gate_414_runtime_validation_cpu --candidate-registration runs\checkpoints\s2_gate_417_quality_reference_cuda_hardened --baseline-label cpu_tile --candidate-label cuda_resident_triangle_quality_reference --out runs\checkpoints\s2_gate_418_quality_reference_triangle_matrix_compare.json --markdown runs\checkpoints\s2_gate_418_quality_reference_triangle_matrix_compare.md --max-translation-delta-px 0.5 --max-matrix-delta-frobenius 0.5`
- `.venv\Scripts\python.exe -m glass.cli resident-registration-matrix-compare --baseline-registration runs\checkpoints\s2_gate_414_runtime_validation_cpu --candidate-registration runs\checkpoints\s2_gate_417_quality_reference_cuda_hardened --baseline-label cpu_tile --candidate-label cuda_resident_triangle_quality_reference --out runs\checkpoints\s2_gate_418_quality_reference_triangle_matrix_compare_strict.json --markdown runs\checkpoints\s2_gate_418_quality_reference_triangle_matrix_compare_strict.md --max-translation-delta-px 0.1 --max-matrix-delta-frobenius 0.1`

Additional focused/full tests are run before commit:

- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_registration_matrix_compare.py tests\test_resident_cuda_run.py tests\test_resident_parity_summary.py`
- `.venv\Scripts\python.exe -m ruff check src\glass\report\resident_registration_matrix_compare.py tests\test_resident_registration_matrix_compare.py src\glass\cli.py`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- New matrix-compare tests: `3 passed in 0.21s`.
- Ruff: passed.
- CLI help: passed.
- Focused resident/matrix/parity tests: `51 passed in 4.57s`.
- Full test suite: `989 passed in 36.87s`.

## Runtime Validation

External CPU-transform control:

- Baseline: `runs/checkpoints/s2_gate_414_runtime_validation_cpu/registration_results.json`.
- Candidate: `runs/checkpoints/s2_gate_415_runtime_validation_cuda_external_cpu_transform/registration_results.json`.
- Status: passed.
- Reference frame: `F000016` vs `F000016`.
- Row counts: `16` vs `16`.
- Max translation delta: `0.0 px`.
- Max matrix Frobenius delta: `0.0`.
- Recommendation: `registration_matrices_ready`.

Quality-reference resident triangle:

- Baseline: `runs/checkpoints/s2_gate_414_runtime_validation_cpu/registration_results.json`.
- Candidate: `runs/checkpoints/s2_gate_417_quality_reference_cuda_hardened/registration_results.json`.
- Reference frame: `F000016` vs `F000016`.
- Row counts: `16` vs `16`.
- Status mismatch count: `0`.
- Reference mismatch count: `0`.
- Max translation delta: `0.18305392208191398 px`.
- Mean translation delta: `0.16714125666991966 px`.
- Max matrix Frobenius delta: `0.18305392208191398`.
- Wide 0.5 px threshold status: passed.
- Strict 0.1 px threshold status: attention required.
- Strict recommendation: `fix_resident_transform_estimation`.

## Findings

- S2-Gate 417 successfully removed reference-frame mismatch and row-accounting mismatch.
- The external-matrix path proves exact CPU matrices still produce the near-parity path measured in S2-Gate 416.
- Resident triangle registration under the same reference is close but quantized/offset by up to about `0.183 px` on the synthetic harness.
- That residual matrix delta is now a concrete next optimization target. It may explain or amplify the remaining master RMS and rejected-sample delta, especially around stars and sigma rejection boundaries.

## CUDA

- Gate418 did not run new CUDA kernels; it consumed existing Gate415/Gate417 CUDA artifacts.
- CUDA availability was already recorded in `runs/checkpoints/s2_gate_417_cuda_doctor.json`: NVIDIA RTX PRO 6000 Blackwell Workstation Edition, cc 12.0, VRAM 97886 MiB, driver 596.21.

## Artifacts

- `runs/checkpoints/s2_gate_418_external_cpu_transform_matrix_compare.json`
- `runs/checkpoints/s2_gate_418_external_cpu_transform_matrix_compare.md`
- `runs/checkpoints/s2_gate_418_quality_reference_triangle_matrix_compare.json`
- `runs/checkpoints/s2_gate_418_quality_reference_triangle_matrix_compare.md`
- `runs/checkpoints/s2_gate_418_quality_reference_triangle_matrix_compare_strict.json`
- `runs/checkpoints/s2_gate_418_quality_reference_triangle_matrix_compare_strict.md`
- `runs/checkpoints/s2_gate_418_status.md`

## Known Limitations

- This gate is diagnostic; it does not change registration fitting, pixel refinement, CUDA kernels, warp behavior, DQ, or rejection math.
- It validates the 16-frame synthetic harness, not the 200-light real-data benchmark.
- Matrix deltas alone do not prove final image parity; warp interpolation, coverage/DQ, and winsorized rejection still need direct validation.

## Next Gate

S2-Gate 419 should target the resident triangle subpixel refinement delta. A good first experiment is to run/compare stricter final pixel-refine stride or candidate-grid settings on the same synthetic harness, then rerun matrix compare and parity summary. The promotion criterion should be matrix max delta below `0.1 px` and reduced master/rejection deltas without breaking result contracts.

## Clean-Room Compliance

Compliant. This gate used only GLASS-owned registration/result artifacts and GLASS synthetic validation outputs. It did not read or derive from external proprietary implementation source and did not modify user image directories.
