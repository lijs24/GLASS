# S2-Gate 313 Status: Local Normalization Continuous Contract Audit

## Gate

- S2-Gate 313
- Scope: Local-normalization continuous coefficient-field contract audit
- Status: green
- Date: 2026-06-18

## Completed Work

- Added `glass.report.local_norm_contract`.
- Added CLI command `glass local-norm-contract`.
- The contract audits `local_norm_results.json` and per-frame coefficient JSON
  without reading large FITS pixel data.
- Enabled LN now has an auditable contract for:
  - `continuous_grid_mean_std_v1`
  - `bilinear_tile_center_v1`
  - `bilinear_tile_center`
  - crop-box recording
  - coefficient grid dimensions
  - valid-pixel and status grids
  - residual summaries
  - DQ summaries
  - full-field diagnostic map path policy
- Disabled LN now has an explicit `disabled_passthrough` contract.
- Updated the local-normalization capability report to advertise the audited CPU
  continuous coefficient-field baseline while keeping fully resident/windowed
  continuous LN marked incomplete.
- Updated `docs/local_normalization_model.md` and
  `docs/phase2_algorithm_hardening.md`.
- Added focused tests in `tests/test_local_norm_contract.py`.

## Commands

- `.venv\Scripts\python.exe -m glass.cli local-norm-contract --run runs\checkpoints\s2_gate_313_local_norm_contract_fixture_run --out runs\checkpoints\s2_gate_313_local_norm_contract.json --markdown runs\checkpoints\s2_gate_313_local_norm_contract.md --fail-on-failed`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_313_doctor.json --allow-cpu-only`
- `.venv\Scripts\python.exe -m glass.cli local-norm-contract --help`
- `.venv\Scripts\python.exe -m pytest -q tests\test_local_norm_contract.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_local_norm_contract.py tests\test_cpu_local_norm.py tests\test_pipeline_contract.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_capabilities.py tests\test_local_norm_contract.py`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\ruff.exe check src\glass\report\local_norm_contract.py src\glass\cli.py src\glass\capabilities.py tests\test_local_norm_contract.py`
- `.venv\Scripts\ruff.exe check src tests`
- `git diff --check`

## Results

- Focused `test_local_norm_contract.py`: 5 passed.
- Focused LN/contract/pipeline tests: 37 passed.
- Capability/local-norm regression tests: 7 passed.
- Full pytest: 739 passed.
- Ruff: passed.
- `git diff --check`: passed.
- Gate313 local-normalization contract: `passed`, output count 1, failed output
  count 0.
- `local-norm-contract --help`: available.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Artifacts

- `runs/checkpoints/s2_gate_313_status.md`
- `runs/checkpoints/s2_gate_313_doctor.json`
- `runs/checkpoints/s2_gate_313_local_norm_contract.json`
- `runs/checkpoints/s2_gate_313_local_norm_contract.md`
- `runs/checkpoints/s2_gate_313_local_norm_contract_fixture_run/local_norm_results.json`
- `runs/checkpoints/s2_gate_313_local_norm_contract_fixture_run/local_norm_cache/local_norm_L1_coefficients.json`

## Known Limitations

- This gate is metadata contract hardening only.
- It does not change local-normalization math, CUDA kernels, registration,
  integration, output pixels, package build/upload, or GitHub release state.
- The audit validates coefficient-grid artifacts and diagnostic map paths; it
  intentionally does not read large FITS pixel payloads.
- Fully resident continuous/windowed local normalization remains incomplete and
  is still reported as a future optimization target.
- No new real-data benchmark was run because this gate does not change image
  math or fast-path scheduling.

## Next Step

- Feed the local-normalization contract into broader pipeline/acceptance
  guardrails, then continue toward resident CUDA continuous/windowed LN once the
  contract is enforced across run-level artifacts.

## Clean-Room Compliance

- This gate consumes only GLASS-owned local-normalization artifacts, generated
  checkpoint fixtures, and local test artifacts.
- No PixInsight/WBPP/PJSR implementation source, proprietary scripts, or
  external implementation code were read, summarized, copied, or modified.
