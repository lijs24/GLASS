# S2-Gate 336 Status

## Gate

S2-Gate 336: HTML Release Contract Failure Evidence Columns

## Completed

- Expanded the HTML report release-contract check table with explicit
  `actual`, `required`, `status`, `available`, `failed_checks`, and `blockers`
  columns.
- Preserved the compact evidence string while making resident fastpath failures
  readable without parsing a dense evidence blob.
- Added focused HTML report coverage for a failed resident registration
  fastpath contract check.
- Generated a controlled failed resident-fastpath HTML report fixture.

## Commands

- `.venv\Scripts\ruff.exe check src\glass\report\html_report.py tests\test_pipeline_contract.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_contract.py -k "resident_fastpath_check_evidence or resident_registration_fastpath_release_evidence"`
- `.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_contract.py`
- `.venv\Scripts\python.exe - <<generate Gate336 failed resident fastpath HTML fixture>>`
- `.venv\Scripts\python.exe -m glass.cli doctor --allow-cpu-only --json runs\checkpoints\s2_gate_336_doctor.json`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Ruff: passed.
- Focused HTML report tests: `2 passed, 23 deselected`.
- Full pipeline-contract test file: `25 passed`.
- Full suite: `774 passed in 38.29s`.

## CUDA

- CUDA available: yes.
- CUDA wrapper importable: yes.
- CUDA native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Artifacts

- `runs/checkpoints/s2_gate_336_fixture/acceptance_audit_failed_resident_fastpath.json`
- `runs/checkpoints/s2_gate_336_report_failed_resident_fastpath.html`
- `runs/checkpoints/s2_gate_336_doctor.json`

## Known Limitations

- This gate is report-surface scoped only.
- It does not change registration math, CUDA kernels, runtime defaults,
  package assets, upload behavior, GitHub release creation, or real-data
  benchmark outputs.
- The generated report fixture is controlled JSON, not a new 200-light
  benchmark run.

## Next Step

- Continue Phase2 hardening with a narrow gate that improves runtime contract
  enforcement, DQ/mask auditability, or real benchmark regression visibility.

## Clean-Room Compliance

- Compliant. The gate consumes GLASS-owned acceptance-audit JSON only.
- No PixInsight/WBPP/PJSR source was read, copied, summarized, or modified.
- No user image input directory was modified.
