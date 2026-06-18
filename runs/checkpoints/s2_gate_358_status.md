# S2-Gate 358 Status

- Gate: S2-Gate 358
- Scope: Phase2 quality metric summary handoff
- Status: green
- Date: 2026-06-19

## Completed Content

- Reused `glass phase2-status --quality-results` to summarize core
  `frame_quality.json` metric distributions in Phase2 status JSON and
  Markdown.
- Added `quality_metrics` payload with frame count, metric count, metric names,
  and per-metric min/median/mean/max/worst-frame summaries for `star_count`,
  `fwhm_px`, `eccentricity`, `background_rms`, `snr`, `quality_score`, and
  `weight`.
- Added Phase2 check `quality_metric_summary_available`; explicitly supplied
  quality artifacts now require at least one configured metric summary.
- Added `quality_metric_summary_available_preserved` to
  `glass phase2-status-compare` so candidates cannot drop previously available
  quality metric summary evidence.
- Added Phase2 Markdown and CLI console output for quality metric status and
  metric count.
- Added focused build, CLI, Markdown, and compare tests.
- Documented the gate in `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m ruff check src\\glass\\report\\phase2_status.py src\\glass\\cli.py tests\\test_phase2_status.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_phase2_status.py::test_phase2_status_surfaces_quality_metric_summary tests\\test_phase2_status.py::test_phase2_status_surfaces_quality_saturation_summary tests\\test_phase2_status.py::test_phase2_status_compare_flags_quality_metric_summary_regression tests\\test_phase2_status.py::test_cli_phase2_status_writes_outputs`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\python.exe -m glass.cli phase2-status --checkpoint-dir runs\\checkpoints --quality-results runs\\checkpoints\\s2_gate_358_quality_metrics_frame_quality.json --out runs\\checkpoints\\s2_gate_358_phase2_quality_metrics_pass_status.json --markdown runs\\checkpoints\\s2_gate_358_phase2_quality_metrics_pass_status.md`
- `.\\.venv\\Scripts\\python.exe -m glass.cli phase2-status --checkpoint-dir runs\\checkpoints --quality-results runs\\checkpoints\\s2_gate_356_quality_saturation_pass_frame_quality.json --out runs\\checkpoints\\s2_gate_358_phase2_quality_metrics_missing_status.json --markdown runs\\checkpoints\\s2_gate_358_phase2_quality_metrics_missing_status.md`
- `.\\.venv\\Scripts\\python.exe -m glass.cli phase2-status-compare --baseline-status runs\\checkpoints\\s2_gate_358_phase2_quality_metrics_pass_status.json --candidate-status runs\\checkpoints\\s2_gate_358_phase2_quality_metrics_missing_status.json --out runs\\checkpoints\\s2_gate_358_phase2_quality_metrics_compare.json --markdown runs\\checkpoints\\s2_gate_358_phase2_quality_metrics_compare.md`
- `.\\.venv\\Scripts\\python.exe -m glass.cli doctor --json runs\\checkpoints\\s2_gate_358_cuda_doctor.json --allow-cpu-only`
- `Select-String` checks over Gate358 Phase2 status and compare Markdown
  artifacts for `Quality Metrics`, `metrics=7`, `metrics=0`,
  `quality_metric_summary_available`, and
  `quality_metric_summary_available_preserved`.

## Test Results

- Ruff: passed.
- Focused pytest: `4 passed in 0.45s`.
- Full pytest: `812 passed in 34.50s`.
- Phase2 pass artifact: `status=green`,
  `quality_metrics_status=passed`, metric count `7`.
- Phase2 missing-metric artifact: `status=attention_required`,
  `quality_metrics_status=not_available`, metric count `0`.
- Phase2 compare artifact: `status=regressed` with failed
  `quality_metric_summary_available_preserved`.

## CUDA Status

- CUDA available: yes.
- CUDA extension importable: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor artifact: `runs/checkpoints/s2_gate_358_cuda_doctor.json`.

## Artifacts

- `runs/checkpoints/s2_gate_358_quality_metrics_frame_quality.json`
- `runs/checkpoints/s2_gate_358_phase2_quality_metrics_pass_status.json`
- `runs/checkpoints/s2_gate_358_phase2_quality_metrics_pass_status.md`
- `runs/checkpoints/s2_gate_358_phase2_quality_metrics_missing_status.json`
- `runs/checkpoints/s2_gate_358_phase2_quality_metrics_missing_status.md`
- `runs/checkpoints/s2_gate_358_phase2_quality_metrics_compare.json`
- `runs/checkpoints/s2_gate_358_phase2_quality_metrics_compare.md`
- `runs/checkpoints/s2_gate_358_cuda_doctor.json`
- `runs/checkpoints/s2_gate_358_status.md`

## Artifact Summary

- Passing quality artifact: 2 frames, 7 configured quality metrics, worst
  `fwhm_px` and `snr` frame `F_SAT`.
- Missing-metric quality artifact: reused
  `runs/checkpoints/s2_gate_356_quality_saturation_pass_frame_quality.json`,
  2 frames, 0 configured quality metrics.
- Compare regression evidence shows a previously available metric summary
  cannot regress to missing metric evidence without a failed compare check.

## Known Limitations

- This gate summarizes existing metrics only; it does not add quality
  thresholds, quality-drift tolerances, or acceptance rules for FWHM/SNR/noise.
- The compare check preserves metric summary availability/count, not numerical
  improvement or degradation.
- This gate does not change quality metric math, star detection, registration,
  integration, CUDA kernels, runtime defaults, packaging, publication, or
  real-data benchmark outputs.

## Next Step

- Continue quality hardening by defining explicit quality-drift contracts only
  after we have enough real-run evidence for acceptable FWHM/SNR/background
  variation.

## Clean-Room Compliance

- Compliant. This gate used only GLASS-owned `frame_quality.json` artifacts,
  Phase2 status/compare code, CLI code, tests, docs, and generated checkpoint
  artifacts.
- No official PixInsight/WBPP/PJSR source code or proprietary implementation
  material was read, copied, summarized, or reworked.
- Input image directories were not modified.
