# S2-Gate 337 Status

## Gate

S2-Gate 337: HTML Resident Result-Contract Failure Rows

## Completed

- Expanded the HTML Pipeline contract audit section with resident CUDA
  result-contract failure rows.
- Surfaced nested failed resident integration checks with output item, backend,
  memory mode, resident contract status, required/pass state, check name,
  actual/required values, availability, note, and compact evidence.
- Added focused HTML report coverage for a failed resident result-contract
  fixture.
- Generated a controlled resident pipeline contract failure fixture and HTML
  report.

## Commands

- `.venv\Scripts\ruff.exe check src\glass\report\html_report.py tests\test_pipeline_contract.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_contract.py -k "resident_result_contract_failures or fails_resident_result_contract"`
- `.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_contract.py`
- `.venv\Scripts\python.exe - <<generate Gate337 resident result-contract failure fixture>>`
- `.venv\Scripts\python.exe -m glass.cli doctor --allow-cpu-only --json runs\checkpoints\s2_gate_337_doctor.json`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Ruff: passed.
- Focused resident result-contract tests: `2 passed, 24 deselected`.
- Full pipeline-contract test file: `26 passed`.
- Full suite: `775 passed in 38.16s`.

## CUDA

- CUDA available: yes.
- CUDA wrapper importable: yes.
- CUDA native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Artifacts

- `runs/checkpoints/s2_gate_337_fixture/pipeline_contract_failed_resident_result.json`
- `runs/checkpoints/s2_gate_337_report_resident_result_contract_failure.html`
- `runs/checkpoints/s2_gate_337_doctor.json`

## Known Limitations

- This gate is report-surface scoped only.
- It does not change resident result-contract generation, registration math,
  CUDA kernels, runtime defaults, package assets, upload behavior, GitHub
  release creation, or real-data benchmark outputs.
- The generated report fixture is controlled synthetic data, not a new
  200-light benchmark run.

## Next Step

- Continue Phase2 hardening with a narrow gate that improves runtime contract
  enforcement, DQ/mask auditability, or real benchmark regression visibility.

## Clean-Room Compliance

- Compliant. The gate consumes GLASS-owned pipeline-contract JSON and synthetic
  GLASS fixture artifacts only.
- No PixInsight/WBPP/PJSR source was read, copied, summarized, or modified.
- No user image input directory was modified.
