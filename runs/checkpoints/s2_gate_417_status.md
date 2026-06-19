# S2-Gate 417 Status: Resident Quality Reference Handoff

## Gate

S2-Gate 417: Resident Quality Reference Handoff.

## Completed Work

- Added resident CUDA reference selection handoff from an existing GLASS `frame_quality.json`.
- Preserved reference priority order:
  1. explicit `--reference-frame-id`;
  2. external-matrix `reference_frame_id`;
  3. quality-stage `frame_quality.json` reference;
  4. first-light fallback.
- Added auditable resident registration artifact fields:
  - `selected_reference_frame_id`
  - `reference_selection_source`
  - `quality_reference_frame_id`
  - `quality_reference_status`
  - `quality_reference_path`
- Added a CUDA CLI regression test proving resident triangle registration uses the quality-selected reference without an explicit reference argument.
- Re-ran the S2-Gate 414 synthetic 16-frame validation with the CPU quality reference handed to resident CUDA triangle registration.
- Updated Phase 2 gate documentation and algorithm-source records.

## Validation Commands

- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_uses_quality_reference`
- `.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py tests\test_resident_cuda_run.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_uses_quality_reference tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_external_matrix_registration`
- `Copy-Item runs\checkpoints\s2_gate_414_runtime_validation_cpu\frame_quality.json runs\checkpoints\s2_gate_417_quality_reference_cuda_hardened\frame_quality.json`
- `.venv\Scripts\python.exe -m glass.cli run --plan runs\checkpoints\s2_gate_414_runtime_validation_cpu\processing_plan.json --out runs\checkpoints\s2_gate_417_quality_reference_cuda_hardened --backend cuda --tile-size 128 --memory-mode resident --resident-registration similarity_cuda_triangle --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-winsorized-mode hardened_cpu_parity --resident-output-maps audit`
- `.venv\Scripts\python.exe -m glass.cli resident-result-contract --run runs\checkpoints\s2_gate_417_quality_reference_cuda_hardened --out runs\checkpoints\s2_gate_417_quality_reference_resident_result_contract.json --markdown runs\checkpoints\s2_gate_417_quality_reference_resident_result_contract.md --pixel-verify --pixel-verify-tile-size 128 --fail-on-failed`
- `.venv\Scripts\python.exe -m glass.cli compare --glass runs\checkpoints\s2_gate_417_quality_reference_cuda_hardened\integration\resident_master_H.fits --reference runs\checkpoints\s2_gate_414_runtime_validation_cpu\integration\master_H.fits --out runs\checkpoints\s2_gate_417_quality_reference_compare.html --glass-label cuda_resident_quality_reference --reference-label cpu_tile --glass-coverage-map runs\checkpoints\s2_gate_417_quality_reference_cuda_hardened\integration\resident_coverage_map_H.fits --min-coverage 1 --diagnostics-dir runs\checkpoints\s2_gate_417_quality_reference_compare_diagnostics --ignore-border-px 8`
- `.venv\Scripts\python.exe -m glass.cli resident-parity-summary --cpu-run runs\checkpoints\s2_gate_414_runtime_validation_cpu --resident-run runs\checkpoints\s2_gate_417_quality_reference_cuda_hardened --compare-json runs\checkpoints\s2_gate_417_quality_reference_compare.json --out runs\checkpoints\s2_gate_417_quality_reference_parity_summary.json --markdown runs\checkpoints\s2_gate_417_quality_reference_parity_summary.md --resident-label cuda_resident_triangle_quality_reference --max-rms-diff 0.1 --max-relative-rms-diff 0.001 --max-rejected-sample-delta 64`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_417_cuda_doctor.json --allow-cpu-only`

Additional focused/full tests are run before commit:

- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py tests\test_resident_result_contract.py tests\test_resident_parity_summary.py`
- `.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py tests\test_resident_cuda_run.py`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- New CUDA reference-handoff test: `1 passed in 0.58s`.
- Adjacent resident priority tests: `3 passed in 0.77s`.
- Focused resident/result/parity tests: `62 passed in 4.96s`.
- Ruff: passed.
- Full test suite: `986 passed in 39.69s`.

## Runtime / Numerical Validation

Dataset: S2-Gate 414 synthetic mono H, 16 lights, 512 x 512, known shifts.

CPU tiled baseline:

- Run: `runs/checkpoints/s2_gate_414_runtime_validation_cpu`
- Reference frame: `F000016`
- Total elapsed: `41.93859020000673 s`
- Rejected samples: `14796`
- Valid pixels: `248399`

CUDA resident triangle with quality reference:

- Run: `runs/checkpoints/s2_gate_417_quality_reference_cuda_hardened`
- Reference frame: `F000016`
- `reference_selection_source`: `frame_quality`
- `quality_reference_status`: `frame_quality`
- Total elapsed: `80.44664629999897 s`
- Rejected samples: `16376`
- Valid pixels: `242227`
- Resident result contract: passed.

Compare/parity against CPU:

- `registration_reference_match`: passed.
- `registration_row_count_match`: passed.
- `resident_result_contract_passed`: passed.
- RMS diff: `2.568470708484397`.
- Relative RMS diff: `0.011678744811104374`.
- P99 absolute diff: `2.059838104248047`.
- Rejected-sample delta: `1580`.
- Parity summary status: `attention_required`.

## Findings

- This gate removes the reference-frame mismatch found in S2-Gate 414/415: resident triangle now uses the same quality-selected reference frame as the CPU run when that quality artifact is present.
- The resident output contract is no longer the blocker for this path.
- Full numerical parity is still not reached. The next blocker is now narrower: triangle transform estimation, resident warp behavior, DQ/coverage semantics, or rejection sample accounting under the same reference frame.
- The tiny synthetic case is still not a speed proof. CUDA resident is slower than CPU tiled on this 16 x 512 validation because registration/orchestration overhead dominates.

## CUDA Availability

- CUDA wrapper importable: yes.
- CUDA native extension loaded: yes.
- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Artifacts

- Resident validation run: `runs/checkpoints/s2_gate_417_quality_reference_cuda_hardened`
- Compare JSON: `runs/checkpoints/s2_gate_417_quality_reference_compare.json`
- Compare HTML: `runs/checkpoints/s2_gate_417_quality_reference_compare.html`
- Result contract JSON: `runs/checkpoints/s2_gate_417_quality_reference_resident_result_contract.json`
- Result contract Markdown: `runs/checkpoints/s2_gate_417_quality_reference_resident_result_contract.md`
- Parity summary JSON: `runs/checkpoints/s2_gate_417_quality_reference_parity_summary.json`
- Parity summary Markdown: `runs/checkpoints/s2_gate_417_quality_reference_parity_summary.md`
- CUDA doctor: `runs/checkpoints/s2_gate_417_cuda_doctor.json`
- Gate status: `runs/checkpoints/s2_gate_417_status.md`

## Known Limitations

- This gate validates synthetic data, not the 200-light real-data benchmark.
- It consumes an existing quality artifact; resident one-shot audit still needs a later gate to produce or hand off quality/reference artifacts without a separate preseed step.
- It does not change triangle descriptor formulas, transform fitting, CUDA kernels, warp interpolation, DQ semantics, or rejection math.
- Local normalization remains disabled in this validation.

## Next Gate

S2-Gate 418 should compare CPU registration matrices against resident triangle matrices under the same `F000016` reference, then either fix transform estimation/refinement or add a formal resident registration triage artifact that identifies the frames causing the RMS and rejection-sample delta. The target is to move the default resident triangle path closer to the external-matrix near-parity result from S2-Gate 416.

## Clean-Room Compliance

Compliant. This gate used only GLASS-owned code, GLASS synthetic data, and GLASS-generated CPU/resident artifacts. It did not read or derive from external proprietary implementation source and did not modify user image directories.
