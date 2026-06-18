# S2-Gate 352 Status: Registration Admission Report Surface

## Gate

S2-Gate 352: Registration Admission Report Surface

## Completed Content

- Added a dedicated `Registration admission` section to the HTML report.
- Surfaced `reference_admission` metadata from `registration_results.json`:
  status, reference frame id, quality-gate status, enforcement flag,
  reference fallback flag, quality-rejected-reference override flag, reason,
  and requested/quality reference ids.
- Added a compact report table for registration rows affected by admission
  decisions, including `quality_reference_admission` rows.
- Extended CLI smoke coverage so a failed registration-admission run can still
  produce a report that explains why registration stopped.
- Documented the gate in `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m ruff check src\\glass\\report\\html_report.py tests\\test_cli_smoke.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_cli_smoke.py::test_cli_audit_and_run_write_state_for_registration_admission_block tests/test_pipeline_fixture.py::test_pipeline_fixture_run_registration tests/test_frame_accounting.py::test_report_renders_frame_accounting`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\python.exe -m glass.cli report --run runs\\checkpoints\\s2_gate_351_resume_admission_run --out runs\\checkpoints\\s2_gate_352_registration_admission_report.html`
- `.\\.venv\\Scripts\\python.exe -m glass.cli doctor --json runs\\checkpoints\\s2_gate_352_cuda_doctor.json --allow-cpu-only`

## Test Results

- Ruff: passed.
- Focused pytest: `3 passed in 1.86s`.
- Full pytest: `800 passed in 33.86s`.

## CUDA Status

- CUDA available: yes.
- CUDA extension importable: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor artifact: `runs/checkpoints/s2_gate_352_cuda_doctor.json`.

## Artifacts

- `runs/checkpoints/s2_gate_352_registration_admission_report.html`
- `runs/checkpoints/s2_gate_352_cuda_doctor.json`
- `runs/checkpoints/s2_gate_352_status.md`

## Known Limitations

- This gate is report-surface only.
- It does not change registration transform math, quality metric math,
  integration math, CUDA kernels, runtime defaults, packaging, publication, or
  real-data benchmark outputs.
- The report summarizes GLASS-owned registration artifacts; it does not infer
  missing upstream diagnostics beyond the fields already present.

## Next Step

- Continue Phase 2 with the next scoped gate, likely extending the
  registration-admission evidence into a higher-level Phase 2 status or
  publication-readiness surface if that remains the most useful audit gap.

## Clean-Room Compliance

- Compliant. This gate consumed only GLASS-owned source files, tests, docs, and
  generated run artifacts.
- No official PixInsight/WBPP/PJSR source code or proprietary implementation
  material was read, copied, summarized, or reworked.
- Input image directories were not modified.
