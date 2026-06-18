# S2-Gate 355 Status

- Gate: S2-Gate 355
- Scope: Quality saturation report surface
- Status: green
- Date: 2026-06-19

## Completed Content

- Added a dedicated `Quality saturation` section to the main HTML report.
- The report now summarizes frame count, saturated-frame count,
  saturation-rejected count, maximum/mean saturation fraction, maximum
  saturated-pixel count, saturation level, source, and worst frame id from
  `frame_quality.json`.
- The report now lists only frames with saturation counts or saturation
  quality-gate warnings in a compact detail table.
- Added CLI report smoke coverage using a controlled `frame_quality.json`
  artifact with one threshold-saturated rejected frame and one accepted frame.
- Documented the gate in `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m ruff check src\\glass\\report\\html_report.py tests\\test_cli_smoke.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_cli_smoke.py::test_cli_report_surfaces_quality_saturation_summary`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\python.exe -m glass.cli report --run runs\\checkpoints\\s2_gate_354_quality_saturation_run --out runs\\checkpoints\\s2_gate_355_quality_saturation_report.html`
- `.\\.venv\\Scripts\\python.exe -m glass.cli doctor --json runs\\checkpoints\\s2_gate_355_cuda_doctor.json --allow-cpu-only`
- `Select-String -Path runs\\checkpoints\\s2_gate_355_quality_saturation_report.html -Pattern 'Quality saturation|saturated_frame_count|quality_gate_saturation_rejected_count|bad|threshold'`

## Test Results

- Ruff: passed.
- Focused pytest: `1 passed in 0.24s`.
- Full pytest: `806 passed in 34.26s`.
- HTML artifact check: passed; the report includes the new section, summary
  fields, `bad` saturated frame, and threshold source evidence.

## CUDA Status

- CUDA available: yes.
- CUDA extension importable: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor artifact: `runs/checkpoints/s2_gate_355_cuda_doctor.json`.

## Artifacts

- `runs/checkpoints/s2_gate_355_quality_saturation_report.html`
- `runs/checkpoints/s2_gate_355_cuda_doctor.json`
- `runs/checkpoints/s2_gate_355_status.md`

## Artifact Summary

- Source quality artifact:
  `runs/checkpoints/s2_gate_354_quality_saturation_run/frame_quality.json`.
- Report summary row: `frame_count=2`, `saturated_frame_count=1`,
  `quality_gate_saturation_rejected_count=1`,
  `max_saturation_fraction=0.00878906`, `max_saturated_pixel_count=36`,
  `saturation_sources=threshold`, `worst_frame_id=bad`.

## Known Limitations

- This gate surfaces the Gate354 metric but does not add a new saturation
  detector, default threshold, DQ rule, or visualization plot.
- The saturation detail table remains text/table based; image thumbnails or
  saturated-pixel masks can be added in a later diagnostics gate.
- This gate does not change quality metric math, star detection, registration,
  integration, CUDA kernels, runtime defaults, packaging, publication, or
  real-data benchmark outputs.

## Next Step

- Continue Phase2 quality hardening by adding the next missing science
  diagnostic or by carrying saturation evidence into Phase2 status/acceptance
  reports if release gates need it.

## Clean-Room Compliance

- Compliant. This gate used only GLASS-owned `frame_quality.json` artifacts,
  report code, tests, docs, and generated checkpoint artifacts.
- No official PixInsight/WBPP/PJSR source code or proprietary implementation
  material was read, copied, summarized, or reworked.
- Input image directories were not modified.
