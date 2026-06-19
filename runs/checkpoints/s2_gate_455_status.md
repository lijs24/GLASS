# S2-Gate 455 Status: Resident Inline Source-DQ Masks

## Gate

- Gate: S2-Gate 455
- Scope: Opt-in resident inline source-DQ mask generation plus 200-light default-path regression.
- Status: passed
- Date: 2026-06-20 local

## Completed Work

- Added `source_invalid_mask_from_inline_cosmetic` to build hot/cold/nonfinite
  resident source-DQ masks with the existing GLASS CPU cosmetic baseline.
- Added `--resident-inline-source-dq off|cosmetic`,
  `--resident-inline-source-dq-hot-sigma`, and
  `--resident-inline-source-dq-cold-sigma` to `glass run` and `glass audit`.
- Threaded the inline source-DQ mode into resident CUDA load/calibrate paths.
- Resident artifacts, timing, and source-DQ strategy now record inline mode,
  thresholds, and no-cache semantics.
- Added focused tests proving inline cosmetic masks flag finite hot/cold
  samples and that resident CUDA excludes a hot pixel without generating a
  calibrated+DQ cache.
- Reran the real 200-light contract-parity benchmark with inline source-DQ
  defaulted off to prove no default-path performance or numerical regression.

## Real 200-Light Results

- Run: `C:\glass_runs\phase2_s2_gate_455_200\contract_parity_20260620`
- Input: M38 H-alpha 200 lights, 20 bias, 20 dark, 20 flat.
- Resident inline source-DQ mode: `off` for default-path regression.
- GLASS elapsed: `20.611956 s`.
- WBPP black-box elapsed: `1092.541 s`.
- Speedup vs WBPP: `53.005208x`.
- Integrated frames: `193/200`.
- Zero-weight quality-rejected frames: `7`.
- Compare:
  - shape match: true
  - coverage fraction: `0.9608048505`
  - RMS diff: `0.0016850645`
  - P99 absolute diff: `0.0004561036`
- Acceptance audit: passed, zero failed checks.

## Commands Run

- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_resident_source_dq.py tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_applies_inline_cosmetic_source_dq_without_cache`
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_source_dq.py src\glass\engine\resident_source_dq_strategy.py src\glass\engine\resident_cuda.py src\glass\cli.py tests\test_resident_source_dq.py tests\test_resident_cuda_run.py`
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py tests/test_resident_source_dq.py`
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q`
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m glass.cli run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_455_200\contract_parity_20260620 --backend cuda --until-stage integration --memory-mode resident ...`
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m glass.cli compare ... --out C:\glass_runs\phase2_s2_gate_455_200\contract_parity_20260620\s2_gate_455_compare.html ...`
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m glass.cli resident-calibration-contract ... --fail-on-failed`
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m glass.cli resident-result-contract ... --pixel-verify --fail-on-failed`
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m glass.cli pipeline-contract ... --pixel-verify`
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m glass.cli stack-engine-contract ... --expected-integration-engine cuda_resident_stack`
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m glass.cli acceptance-audit ... --benchmark-contract benchmarks\phase2_m38_h_200_audit_maps_contract.json ...`

## Test Results

- Focused inline/source-DQ pytest: `8 passed`.
- Focused ruff: passed.
- Resident/source-DQ regression pytest: `71 passed`.
- Full pytest: `1081 passed in 41.10 s`.

## Artifacts

- `runs/checkpoints/s2_gate_455_real_regression_summary.json`
- `runs/checkpoints/s2_gate_455_status.md`
- `C:\glass_runs\phase2_s2_gate_455_200\contract_parity_20260620\resident_source_dq_execution.json`
- `C:\glass_runs\phase2_s2_gate_455_200\contract_parity_20260620\s2_gate_455_compare.json`
- `C:\glass_runs\phase2_s2_gate_455_200\contract_parity_20260620\phase2_contract_acceptance_audit_s2_gate_455.json`

## CUDA Status

- CUDA available: yes.
- Real resident CUDA 200-light run completed successfully on this machine.

## Known Limitations

- Inline source-DQ generation currently uses the CPU cosmetic baseline while
  resident CUDA consumes the resulting mask in memory. The detector itself is
  not yet a pure CUDA kernel.
- Inline cosmetic mode is opt-in and defaults to `off`; the real 200-light
  regression proves no default-path drift, while synthetic resident CUDA tests
  prove enabled-mode finite hot-pixel exclusion.
- The real 200-light dataset used for this gate did not enable inline cosmetic
  source-DQ because that would intentionally change sample admission.
- Strict native StackEngine default readiness remains separate from the
  resident CUDA StackEngine-shaped surface.

## Next Gate

- S2-Gate456 should move the inline source-DQ detector from CPU-control mask
  generation toward a CUDA resident detector/kernel path, or batch source-DQ
  generation across resident frames to reduce per-frame CPU orchestration while
  preserving the Gate455 no-cache contract.

## Clean-Room Compliance

- Compliant. This gate used GLASS source, GLASS synthetic fixtures,
  GLASS-generated artifacts, and user-owned 200-light outputs.
- Original image directories remained read-only.
- No official PixInsight/WBPP/PJSR implementation source was read, copied,
  summarized, or modified.
