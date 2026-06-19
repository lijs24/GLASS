# S2-Gate 414 Runtime Validation Status

Gate: S2-Gate 414 - Resident StackEngine Parity And Regression Harness

Status: validation completed; runtime/parity blockers identified

## Completed Work

- Paused the release/default-promotion/report-contract-only handoff chain.
- Re-scoped S2-Gate 414 in `docs/phase2_algorithm_hardening.md` toward runtime parity and regression validation.
- Ran focused StackEngine, DQ, result-contract, and CUDA resident tests.
- Generated one synthetic mono H dataset and ran the same source through:
  - CPU tiled audit with `winsorized_sigma`
  - CUDA resident audit with `winsorized_sigma` fast approximation
  - CUDA resident audit with `winsorized_sigma` hardened CPU-parity mode
- Compared CUDA resident masters against the CPU tiled master using GLASS compare and the resident coverage map.

## Commands

- `.venv\Scripts\python.exe -m pytest -q tests\test_stack_engine.py tests\test_stack_engine_result_contract.py tests\test_stack_engine_contract.py tests\test_cuda_resident_stack.py`
- `.venv\Scripts\python.exe -m glass.cli synthetic --out runs\checkpoints\s2_gate_414_runtime_validation_source --frames 16 --width 512 --height 512 --known-shift`
- `.venv\Scripts\python.exe -m glass.cli audit --root runs\checkpoints\s2_gate_414_runtime_validation_source --out runs\checkpoints\s2_gate_414_runtime_validation_cpu --backend cpu --tile-size 128 --memory-mode tile --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma`
- `.venv\Scripts\python.exe -m glass.cli audit --root runs\checkpoints\s2_gate_414_runtime_validation_source --out runs\checkpoints\s2_gate_414_runtime_validation_cuda --backend cuda --tile-size 128 --memory-mode resident --resident-registration similarity_cuda_triangle --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps audit`
- `.venv\Scripts\python.exe -m glass.cli compare --glass runs\checkpoints\s2_gate_414_runtime_validation_cuda\integration\resident_master_H.fits --reference runs\checkpoints\s2_gate_414_runtime_validation_cpu\integration\master_H.fits --out runs\checkpoints\s2_gate_414_runtime_validation_compare.html --glass-label cuda_resident --reference-label cpu_tile --glass-coverage-map runs\checkpoints\s2_gate_414_runtime_validation_cuda\integration\resident_coverage_map_H.fits --min-coverage 1 --diagnostics-dir runs\checkpoints\s2_gate_414_runtime_validation_compare_diagnostics --ignore-border-px 8`
- `.venv\Scripts\python.exe -m glass.cli audit --root runs\checkpoints\s2_gate_414_runtime_validation_source --out runs\checkpoints\s2_gate_414_runtime_validation_cuda_hardened --backend cuda --tile-size 128 --memory-mode resident --resident-registration similarity_cuda_triangle --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-winsorized-mode hardened_cpu_parity --resident-output-maps audit`
- `.venv\Scripts\python.exe -m glass.cli compare --glass runs\checkpoints\s2_gate_414_runtime_validation_cuda_hardened\integration\resident_master_H.fits --reference runs\checkpoints\s2_gate_414_runtime_validation_cpu\integration\master_H.fits --out runs\checkpoints\s2_gate_414_runtime_validation_compare_hardened.html --glass-label cuda_resident_hardened --reference-label cpu_tile --glass-coverage-map runs\checkpoints\s2_gate_414_runtime_validation_cuda_hardened\integration\resident_coverage_map_H.fits --min-coverage 1 --diagnostics-dir runs\checkpoints\s2_gate_414_runtime_validation_compare_hardened_diagnostics --ignore-border-px 8`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_414_substantive_cuda_doctor.json --allow-cpu-only`

## Test Result

- Focused pytest: 62 passed in 1.06 s.

## Runtime Results

Dataset: synthetic mono H, 16 lights, 512 x 512, known shifts.

| Run | Backend | Total Time | Key Stage Time | Valid Pixels | Rejected Samples | Notes |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| CPU tiled | `cpu` | 41.939 s | calibration 29.822 s, integration 10.093 s | 248399 | 14796 | CPU StackEngine baseline. |
| CUDA resident fast | `cuda_resident_stack` | 98.518 s | resident calibration/integration 98.482 s | 254921 | 2641 | Uses fast winsorized approximation; contract notes non-parity. |
| CUDA resident hardened | `cuda_resident_stack` | 126.067 s | resident calibration/integration 126.033 s | 241923 | 17463 | Uses median/IQR CPU-parity rejection prototype. |

## Compare Results

| Compare | Shape Match | RMS Diff | Relative RMS Diff | P90 Abs Diff | P99 Abs Diff | Max Abs Diff |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| CUDA resident fast vs CPU tiled | true | 41.0106 | 0.186474 | 4.43494 | 8.42429 | 1846.78 |
| CUDA resident hardened vs CPU tiled | true | 40.9129 | 0.186030 | 4.45299 | 8.44282 | 1839.63 |

## Findings

- The current tiny synthetic case is not a speed proof for CUDA resident; resident overhead dominates at 16 x 512 x 512.
- The fast resident winsorized path is explicitly non-parity: `known_non_parity_pending_cuda_update`.
- Hardened resident winsorized mode changes rejection counts toward CPU semantics, but master RMS remains high, so the remaining difference is not only the winsorized kernel.
- CPU and resident runs selected different registration/reference paths in this validation. The next parity harness must force or record matching reference frame and transform inputs before judging numerical parity.
- Resident DQ/coverage reports warp-edge pixels separately while the CPU tiled result reports source no-data samples; the harness must reconcile these semantics explicitly.
- `resident_result_contract.json` for the fast run failed `resident_outputs_pass_contract`, so result-contract failure must remain visible rather than being hidden by release readiness gates.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Artifacts

- Synthetic source: `runs/checkpoints/s2_gate_414_runtime_validation_source`
- CPU run: `runs/checkpoints/s2_gate_414_runtime_validation_cpu`
- CUDA fast run: `runs/checkpoints/s2_gate_414_runtime_validation_cuda`
- CUDA hardened run: `runs/checkpoints/s2_gate_414_runtime_validation_cuda_hardened`
- Fast compare: `runs/checkpoints/s2_gate_414_runtime_validation_compare.html`
- Hardened compare: `runs/checkpoints/s2_gate_414_runtime_validation_compare_hardened.html`
- CUDA doctor: `runs/checkpoints/s2_gate_414_substantive_cuda_doctor.json`

## Known Limitations

- This is a small synthetic validation, not the 200-light benchmark.
- The validation did not force identical registration transforms between CPU and resident paths.
- Local normalization was disabled to isolate StackEngine, registration, warp, DQ, and rejection behavior.
- No CUDA kernel was changed in this gate.

## Next Step

Implement the S2-Gate 414 harness/fix path:

1. Add a parity runner or test fixture that can force the same reference frame and transform set for CPU tiled and CUDA resident runs.
2. Compare master, coverage, DQ, low/high rejection maps, and rejected-sample accounting under identical registration inputs.
3. Decide whether the first fix belongs in resident registration handoff, resident DQ/coverage semantics, or winsorized rejection parity.
4. Re-run the harness on synthetic data, then promote it to the 200-light benchmark subset/full run.

## Clean-Room Compliance

This validation used only GLASS-generated synthetic data and GLASS-owned artifacts. It did not read, copy, summarize, or rework external proprietary implementation source. User image directories were not modified.
