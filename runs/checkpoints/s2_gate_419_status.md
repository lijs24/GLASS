# S2-Gate 419 Status: Resident Subpixel Refinement Sweep Audit

## Gate

S2-Gate 419: Resident Subpixel Refinement Sweep Audit.

## Completed Work

- Added `glass resident-registration-matrix-sweep`.
- Added `src/glass/report/resident_registration_matrix_sweep.py`.
- Added tests in `tests/test_resident_registration_matrix_sweep.py`.
- Ran bounded synthetic resident CUDA refinement experiments against the S2-Gate 414 CPU registration baseline.
- Confirmed that simply reducing triangle `fine_step` or switching to existing resident translation-NCC controls does not resolve the strict `0.1 px` matrix delta blocker.
- Updated Phase 2 gate documentation and algorithm-source records.

## Commands

- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_registration_matrix_sweep.py tests\test_resident_registration_matrix_compare.py`
- `.venv\Scripts\python.exe -m ruff check src\glass\report\resident_registration_matrix_sweep.py tests\test_resident_registration_matrix_sweep.py src\glass\cli.py`
- `.venv\Scripts\python.exe -m glass.cli resident-registration-matrix-sweep --help`
- Created `runs\checkpoints\s2_gate_419_fine_step_03125_plan.json` by copying the S2-Gate 414 CPU processing plan and setting `registration_policy.cuda_triangle_pixel_refine_fine_step=0.03125`.
- `.venv\Scripts\python.exe -m glass.cli run --plan runs\checkpoints\s2_gate_419_fine_step_03125_plan.json --out runs\checkpoints\s2_gate_419_fine_step_03125_cuda_hardened --backend cuda --tile-size 128 --memory-mode resident --resident-registration similarity_cuda_triangle --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-winsorized-mode hardened_cpu_parity --resident-output-maps audit`
- `.venv\Scripts\python.exe -m glass.cli resident-registration-matrix-compare --baseline-registration runs\checkpoints\s2_gate_414_runtime_validation_cpu --candidate-registration runs\checkpoints\s2_gate_419_fine_step_03125_cuda_hardened --baseline-label cpu_tile --candidate-label cuda_resident_triangle_fine_step_03125 --out runs\checkpoints\s2_gate_419_fine_step_03125_matrix_compare.json --markdown runs\checkpoints\s2_gate_419_fine_step_03125_matrix_compare.md --max-translation-delta-px 0.1 --max-matrix-delta-frobenius 0.1`
- `.venv\Scripts\python.exe -m glass.cli resident-result-contract --run runs\checkpoints\s2_gate_419_fine_step_03125_cuda_hardened --out runs\checkpoints\s2_gate_419_fine_step_03125_result_contract.json --markdown runs\checkpoints\s2_gate_419_fine_step_03125_result_contract.md --pixel-verify --pixel-verify-tile-size 128 --fail-on-failed`
- `.venv\Scripts\python.exe -m glass.cli compare --glass runs\checkpoints\s2_gate_419_fine_step_03125_cuda_hardened\integration\resident_master_H.fits --reference runs\checkpoints\s2_gate_414_runtime_validation_cpu\integration\master_H.fits --out runs\checkpoints\s2_gate_419_fine_step_03125_compare.html --glass-label cuda_resident_triangle_fine_step_03125 --reference-label cpu_tile --glass-coverage-map runs\checkpoints\s2_gate_419_fine_step_03125_cuda_hardened\integration\resident_coverage_map_H.fits --min-coverage 1 --diagnostics-dir runs\checkpoints\s2_gate_419_fine_step_03125_compare_diagnostics --ignore-border-px 8`
- `.venv\Scripts\python.exe -m glass.cli resident-parity-summary --cpu-run runs\checkpoints\s2_gate_414_runtime_validation_cpu --resident-run runs\checkpoints\s2_gate_419_fine_step_03125_cuda_hardened --compare-json runs\checkpoints\s2_gate_419_fine_step_03125_compare.json --out runs\checkpoints\s2_gate_419_fine_step_03125_parity_summary.json --markdown runs\checkpoints\s2_gate_419_fine_step_03125_parity_summary.md --resident-label cuda_resident_triangle_fine_step_03125 --max-rms-diff 0.1 --max-relative-rms-diff 0.001 --max-rejected-sample-delta 64`
- `.venv\Scripts\python.exe -m glass.cli run --plan runs\checkpoints\s2_gate_414_runtime_validation_cpu\processing_plan.json --out runs\checkpoints\s2_gate_419_translation_ncc_cuda_hardened --backend cuda --tile-size 128 --memory-mode resident --resident-registration translation_ncc_subpixel --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-winsorized-mode hardened_cpu_parity --resident-output-maps audit`
- `.venv\Scripts\python.exe -m glass.cli run --plan runs\checkpoints\s2_gate_414_runtime_validation_cpu\processing_plan.json --out runs\checkpoints\s2_gate_419_translation_ncc_step00625_cuda_hardened --backend cuda --tile-size 128 --memory-mode resident --resident-registration translation_ncc_subpixel --resident-subpixel-step 0.0625 --resident-subpixel-radius-steps 4 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-winsorized-mode hardened_cpu_parity --resident-output-maps audit`
- Matrix compares for both translation-NCC controls.
- `.venv\Scripts\python.exe -m glass.cli resident-registration-matrix-sweep --matrix-compare triangle_gate417=runs\checkpoints\s2_gate_418_quality_reference_triangle_matrix_compare_strict.json --matrix-compare triangle_fine03125=runs\checkpoints\s2_gate_419_fine_step_03125_matrix_compare.json --matrix-compare translation_ncc=runs\checkpoints\s2_gate_419_translation_ncc_matrix_compare.json --matrix-compare translation_ncc_step00625=runs\checkpoints\s2_gate_419_translation_ncc_step00625_matrix_compare.json --parity-summary triangle_gate417=runs\checkpoints\s2_gate_417_quality_reference_parity_summary.json --parity-summary triangle_fine03125=runs\checkpoints\s2_gate_419_fine_step_03125_parity_summary.json --out runs\checkpoints\s2_gate_419_subpixel_matrix_sweep.json --markdown runs\checkpoints\s2_gate_419_subpixel_matrix_sweep.md`

Additional focused/full tests run before commit:

- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_registration_matrix_sweep.py tests\test_resident_registration_matrix_compare.py tests\test_resident_cuda_run.py`
- `.venv\Scripts\python.exe -m ruff check src\glass\report\resident_registration_matrix_sweep.py tests\test_resident_registration_matrix_sweep.py src\glass\cli.py`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- New sweep and matrix tests: `5 passed in 0.26s`.
- Focused resident regression set: `50 passed in 4.56s`.
- Ruff: passed.
- CLI help: passed.
- Full pytest: `991 passed in 37.09s`.

## Runtime Experiment Results

Dataset: S2-Gate 414 synthetic mono H, 16 lights, 512 x 512, known shifts.

| Variant | Strict matrix status | Max translation delta | Mean translation delta | RMS diff | Rejected sample delta |
| --- | --- | ---: | ---: | ---: | ---: |
| `triangle_gate417` | attention_required | `0.18305392208191398` | `0.16714125666991966` | `2.568470708484397` | `1580` |
| `triangle_fine03125` | attention_required | `0.18305392208191398` | `0.16714125666991966` | `2.568470708484397` | `1580` |
| `translation_ncc` | attention_required | `0.2562184973123085` | `0.23488917697034084` | not run | not run |
| `translation_ncc_step00625` | attention_required | `0.18305392208191398` | `0.16734804795648386` | not run | not run |

Sweep recommendation: `subpixel_refinement_still_blocked`.

## Findings

- Reducing triangle fine-step from `0.0625` to `0.03125` produced identical matrices and identical parity metrics.
- Existing resident `translation_ncc_subpixel` does not outperform the triangle path on this synthetic strict matrix comparison.
- The blocker is not merely fine-grid density. The next fix must change the refinement metric/model, candidate scoring, or add a stronger resident matrix-polish stage rather than only tuning step sizes.
- Result contract still passes for the fine-step variant, so artifact completeness is not the blocker.

## CUDA

- CUDA was available for the resident runs.
- GPU previously recorded in Gate417 doctor: NVIDIA RTX PRO 6000 Blackwell Workstation Edition, cc 12.0, VRAM 97886 MiB, driver 596.21.

## Artifacts

- `runs/checkpoints/s2_gate_419_fine_step_03125_plan.json`
- `runs/checkpoints/s2_gate_419_fine_step_03125_matrix_compare.json`
- `runs/checkpoints/s2_gate_419_fine_step_03125_matrix_compare.md`
- `runs/checkpoints/s2_gate_419_fine_step_03125_result_contract.json`
- `runs/checkpoints/s2_gate_419_fine_step_03125_result_contract.md`
- `runs/checkpoints/s2_gate_419_fine_step_03125_compare.json`
- `runs/checkpoints/s2_gate_419_fine_step_03125_compare.html`
- `runs/checkpoints/s2_gate_419_fine_step_03125_parity_summary.json`
- `runs/checkpoints/s2_gate_419_fine_step_03125_parity_summary.md`
- `runs/checkpoints/s2_gate_419_translation_ncc_matrix_compare.json`
- `runs/checkpoints/s2_gate_419_translation_ncc_matrix_compare.md`
- `runs/checkpoints/s2_gate_419_translation_ncc_step00625_matrix_compare.json`
- `runs/checkpoints/s2_gate_419_translation_ncc_step00625_matrix_compare.md`
- `runs/checkpoints/s2_gate_419_subpixel_matrix_sweep.json`
- `runs/checkpoints/s2_gate_419_subpixel_matrix_sweep.md`
- `runs/checkpoints/s2_gate_419_status.md`

## Known Limitations

- This is still the 16-frame synthetic harness, not the 200-light real-data benchmark.
- No CUDA kernel or registration formula was changed in this gate.
- The translation-NCC controls were evaluated by matrix compare only; full parity was run for the triangle fine-step variant.
- Local normalization remains disabled.

## Next Gate

S2-Gate 420 should change the resident matrix refinement model rather than tune step density. Candidate directions:

- add a CPU-baseline-compatible matrix-polish reference for translation-only synthetic data, then port it to CUDA;
- add a continuous/parabolic peak interpolation over the matrix metric scores;
- compare resident matrix metric minima against CPU phase-correlation/registration matrices per frame and choose the better validated model under contract.

## Clean-Room Compliance

Compliant. This gate used only GLASS-owned synthetic inputs and GLASS-generated artifacts. It did not inspect external proprietary source and did not modify user image directories.
