# S2-Gate 335 Status

## Gate

S2-Gate 335: HTML Resident Fastpath Release Evidence

## Completed

- Surfaced `release_contract_evidence.resident_registration_fastpath` in the
  main HTML report's release-contract evidence table.
- Added resident fastpath fields for source, availability, artifact count,
  registration mode, descriptor/pixel/warp batch modes, pixel-refine metric
  mode, warp batch frame count, warp copy modes, scratch-byte evidence,
  pass/fail counts, failed-check names, and artifact path.
- Added resident fastpath release-contract checks to the HTML release-contract
  check table.
- Corrected Gate334 documentation wording from `green Phase2 handoff statuses`
  to the actual `passed Phase2 handoff statuses` used by publish-preflight
  artifacts.
- Added focused HTML report coverage for resident registration fastpath
  release evidence.
- Generated a controlled Gate335 HTML report fixture.

## Commands

- `.venv\Scripts\ruff.exe check src\glass\report\html_report.py tests\test_pipeline_contract.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_contract.py -k "html_report_surfaces_resident_registration_fastpath or html_report_surfaces_pipeline_sample_accounting"`
- `.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_contract.py`
- `.venv\Scripts\python.exe - <<generate Gate335 resident fastpath HTML fixture>>`
- `.venv\Scripts\python.exe -m glass.cli doctor --allow-cpu-only --json runs\checkpoints\s2_gate_335_doctor.json`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Ruff: passed.
- Focused HTML report tests: `2 passed, 22 deselected`.
- Full pipeline-contract test file: `24 passed`.
- Full suite: `773 passed in 37.93s`.

## CUDA

- CUDA available: yes.
- CUDA wrapper importable: yes.
- CUDA native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Artifacts

- `runs/checkpoints/s2_gate_335_fixture/acceptance_audit_resident_fastpath.json`
- `runs/checkpoints/s2_gate_335_report_resident_fastpath.html`
- `runs/checkpoints/s2_gate_335_doctor.json`

## Known Limitations

- This gate is report-surface scoped only.
- It does not change registration math, CUDA kernels, runtime defaults,
  package assets, upload behavior, GitHub release creation, or real-data
  benchmark outputs.
- The generated report fixture is controlled JSON, not a new 200-light
  benchmark run.

## Next Step

- Continue Phase2 hardening with another narrow gate that improves auditability
  or closes a runtime/default/DQ contract gap while preserving the resident CUDA
  fastpath and 200-light benchmark baseline.

## Clean-Room Compliance

- Compliant. The gate consumes GLASS-owned acceptance-audit JSON only.
- No PixInsight/WBPP/PJSR source was read, copied, summarized, or modified.
- No user image input directory was modified.
