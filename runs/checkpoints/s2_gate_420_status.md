# S2-Gate 420 Status: Resident Triangle Pixel-Refine Default Guard

## Gate

S2-Gate 420: Resident Triangle Pixel-Refine Default Guard.

## Completed Work

- Changed resident CUDA triangle registration so `cuda_triangle_pixel_refine` defaults to `false`.
- Preserved the existing pixel-refine implementation as an explicit opt-in through plan policy or `--resident-triangle-pixel-refine`.
- Updated resident registration artifact metadata and CPU registration preview metadata to report the guarded default.
- Added CUDA regression coverage proving the default skips triangle pixel-refine while triangle descriptor registration still aligns the small shifted-star fixture.
- Kept existing pixel-refine fast-path tests by explicitly opting them into `cuda_triangle_pixel_refine=true`.
- Validated the S2-Gate 414 synthetic 16-light harness against the CPU registration baseline with the guarded default.

## Commands

- `.venv\Scripts\python.exe -m glass.cli run --plan runs\checkpoints\s2_gate_420_no_pixel_refine_plan.json --out runs\checkpoints\s2_gate_420_no_pixel_refine_refF16_cuda_hardened --backend cuda --tile-size 128 --memory-mode resident --resident-registration similarity_cuda_triangle --reference-frame-id F000016 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-winsorized-mode hardened_cpu_parity --resident-output-maps audit`
- `.venv\Scripts\python.exe -m glass.cli resident-registration-matrix-compare --baseline-registration runs\checkpoints\s2_gate_414_runtime_validation_cpu --candidate-registration runs\checkpoints\s2_gate_420_no_pixel_refine_refF16_cuda_hardened --baseline-label cpu_tile --candidate-label cuda_resident_triangle_no_pixel_refine_refF16 --out runs\checkpoints\s2_gate_420_no_pixel_refine_refF16_matrix_compare.json --markdown runs\checkpoints\s2_gate_420_no_pixel_refine_refF16_matrix_compare.md --max-translation-delta-px 0.1 --max-matrix-delta-frobenius 0.1`
- `.venv\Scripts\python.exe -m glass.cli resident-result-contract --run runs\checkpoints\s2_gate_420_no_pixel_refine_refF16_cuda_hardened --out runs\checkpoints\s2_gate_420_no_pixel_refine_refF16_result_contract.json --markdown runs\checkpoints\s2_gate_420_no_pixel_refine_refF16_result_contract.md --pixel-verify --pixel-verify-tile-size 128 --fail-on-failed`
- `.venv\Scripts\python.exe -m glass.cli compare --glass runs\checkpoints\s2_gate_420_no_pixel_refine_refF16_cuda_hardened\integration\resident_master_H.fits --reference runs\checkpoints\s2_gate_414_runtime_validation_cpu\integration\master_H.fits --out runs\checkpoints\s2_gate_420_no_pixel_refine_refF16_compare.html --glass-label cuda_resident_triangle_no_pixel_refine_refF16 --reference-label cpu_tile --glass-coverage-map runs\checkpoints\s2_gate_420_no_pixel_refine_refF16_cuda_hardened\integration\resident_coverage_map_H.fits --min-coverage 1 --diagnostics-dir runs\checkpoints\s2_gate_420_no_pixel_refine_refF16_compare_diagnostics --ignore-border-px 8`
- `.venv\Scripts\python.exe -m glass.cli resident-parity-summary --cpu-run runs\checkpoints\s2_gate_414_runtime_validation_cpu --resident-run runs\checkpoints\s2_gate_420_no_pixel_refine_refF16_cuda_hardened --compare-json runs\checkpoints\s2_gate_420_no_pixel_refine_refF16_compare.json --out runs\checkpoints\s2_gate_420_no_pixel_refine_refF16_parity_summary.json --markdown runs\checkpoints\s2_gate_420_no_pixel_refine_refF16_parity_summary.md --resident-label cuda_resident_triangle_no_pixel_refine_refF16 --max-rms-diff 0.1 --max-relative-rms-diff 0.001 --max-rejected-sample-delta 64`
- `.venv\Scripts\python.exe -m glass.cli resident-registration-matrix-sweep --matrix-compare triangle_gate417=runs\checkpoints\s2_gate_418_quality_reference_triangle_matrix_compare_strict.json --matrix-compare triangle_fine03125=runs\checkpoints\s2_gate_419_fine_step_03125_matrix_compare.json --matrix-compare translation_ncc_step00625=runs\checkpoints\s2_gate_419_translation_ncc_step00625_matrix_compare.json --matrix-compare triangle_no_pixel_refine=runs\checkpoints\s2_gate_420_no_pixel_refine_refF16_matrix_compare.json --parity-summary triangle_gate417=runs\checkpoints\s2_gate_417_quality_reference_parity_summary.json --parity-summary triangle_fine03125=runs\checkpoints\s2_gate_419_fine_step_03125_parity_summary.json --parity-summary triangle_no_pixel_refine=runs\checkpoints\s2_gate_420_no_pixel_refine_refF16_parity_summary.json --out runs\checkpoints\s2_gate_420_triangle_refine_default_sweep.json --markdown runs\checkpoints\s2_gate_420_triangle_refine_default_sweep.md`
- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair tests\test_resident_cuda_run.py::test_cli_resident_cuda_triangle_default_skips_pixel_refine tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_uses_quality_reference tests\test_resident_cuda_run.py::test_cli_resident_cuda_triangle_fused_matrix_matches_stack_dispatch tests\test_resident_cuda_run.py::test_cli_resident_cuda_auto_dispatch_selects_verified_bilinear_fused_path tests\test_resident_cuda_run.py::test_cli_resident_cuda_auto_dispatch_keeps_lanczos_rejection_on_stack`
- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_registration_matrix_compare.py tests\test_resident_registration_matrix_sweep.py tests\test_cpu_registration.py`
- `.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py src\glass\engine\registration.py src\glass\cli.py tests\test_resident_cuda_run.py`
- `.venv\Scripts\python.exe -m glass.cli run --help`

Additional full test before commit:

- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused resident triangle registration tests: `6 passed in 1.47s`.
- Full resident CUDA run tests: `46 passed in 5.24s`.
- Matrix/sweep/CPU registration tests: `21 passed in 1.28s`.
- Ruff: passed.
- CLI help: passed.
- Full pytest: `992 passed in 37.22s`.

## Runtime Experiment Results

Dataset: S2-Gate 414 synthetic mono H, 16 lights, 512 x 512, known shifts.

| Variant | Strict matrix status | Max translation delta | Mean translation delta | RMS diff | Rejected sample delta |
| --- | --- | ---: | ---: | ---: | ---: |
| `triangle_gate417` | attention_required | `0.18305392208191398` | `0.16714125666991966` | `2.568470708484397` | `1580` |
| `triangle_fine03125` | attention_required | `0.18305392208191398` | `0.16714125666991966` | `2.568470708484397` | `1580` |
| `translation_ncc_step00625` | attention_required | `0.18305392208191398` | `0.16734804795648386` | not run | not run |
| `triangle_no_pixel_refine` | passed | `0.008781854250385976` | `0.0039021745376517335` | `0.0996942253107213` | `117` |

Sweep recommendation: `matrix_ready_but_image_parity_blocked`.

## Findings

- The S2-Gate 419 blocker was caused by the resident triangle pixel-refine metric pulling otherwise correct descriptor-fit matrices by roughly `0.125 px`.
- Disabling triangle pixel-refine by default makes the synthetic strict matrix contract pass and reduces image RMS below the current `0.1` limit.
- Full image parity still fails because rejected-sample delta is `117`, above the strict `64` threshold.
- The next substantive gate should focus on warp/rejection/DQ sample accounting rather than registration matrix estimation.

## CUDA

- CUDA was available for the resident runs.
- GPU previously recorded in Gate417 doctor: NVIDIA RTX PRO 6000 Blackwell Workstation Edition, cc 12.0, VRAM 97886 MiB, driver 596.21.

## Artifacts

- `runs/checkpoints/s2_gate_420_no_pixel_refine_plan.json`
- `runs/checkpoints/s2_gate_420_no_pixel_refine_refF16_matrix_compare.json`
- `runs/checkpoints/s2_gate_420_no_pixel_refine_refF16_matrix_compare.md`
- `runs/checkpoints/s2_gate_420_no_pixel_refine_refF16_result_contract.json`
- `runs/checkpoints/s2_gate_420_no_pixel_refine_refF16_result_contract.md`
- `runs/checkpoints/s2_gate_420_no_pixel_refine_refF16_compare.json`
- `runs/checkpoints/s2_gate_420_no_pixel_refine_refF16_compare.html`
- `runs/checkpoints/s2_gate_420_no_pixel_refine_refF16_parity_summary.json`
- `runs/checkpoints/s2_gate_420_no_pixel_refine_refF16_parity_summary.md`
- `runs/checkpoints/s2_gate_420_triangle_refine_default_sweep.json`
- `runs/checkpoints/s2_gate_420_triangle_refine_default_sweep.md`
- `runs/checkpoints/s2_gate_420_status.md`

## Known Limitations

- This is still the 16-frame synthetic harness, not the 200-light real-data benchmark.
- No CUDA kernel was changed in this gate.
- Pixel-refine is not removed; it remains opt-in while its metric/model is under suspicion.
- Rejection sample parity remains incomplete.
- Local normalization remains disabled in the validation run.

## Next Gate

S2-Gate 421 should compare CPU and resident rejection/sample accounting with the now matrix-ready registration path, then decide whether the remaining `117` rejected-sample delta is caused by warp interpolation edge semantics, coverage/DQ accounting, or hardened winsorized rejection.

## Clean-Room Compliance

Compliant. This gate used only GLASS-owned synthetic inputs and GLASS-generated artifacts. It did not inspect external proprietary source and did not modify user image directories.
