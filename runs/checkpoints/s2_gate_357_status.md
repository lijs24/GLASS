# S2-Gate 357 Status

- Gate: S2-Gate 357
- Scope: Quality metric distribution report surface
- Status: green
- Date: 2026-06-19

## Completed Content

- Added a dedicated `Quality metrics` section to the main HTML report.
- The report now summarizes core `frame_quality.json` metric distributions for
  `star_count`, `fwhm_px`, `eccentricity`, `background_rms`, `snr`,
  `quality_score`, and `weight`.
- Each metric summary records valid frame count, min, median, mean, max, bad
  direction, worst frame id, and worst value.
- Added a compact worst-frame table with up to three worst rows per metric,
  preserving quality-gate status and adjacent diagnostic values.
- Added CLI report smoke coverage using a controlled quality artifact with
  sharp, soft, and noisy frames.
- Documented the gate in `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m ruff check src\\glass\\report\\html_report.py tests\\test_cli_smoke.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_cli_smoke.py::test_cli_report_surfaces_quality_metric_summary tests\\test_cli_smoke.py::test_cli_report_surfaces_quality_saturation_summary`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\python.exe -m glass.cli report --run runs\\checkpoints\\s2_gate_354_quality_saturation_run --out runs\\checkpoints\\s2_gate_357_quality_metrics_report.html`
- `.\\.venv\\Scripts\\python.exe -m glass.cli doctor --json runs\\checkpoints\\s2_gate_357_cuda_doctor.json --allow-cpu-only`
- `Select-String -Path runs\\checkpoints\\s2_gate_357_quality_metrics_report.html -Pattern 'Quality metrics|worst_frame_id|fwhm_px|background_rms|quality_score|bad|good'`

## Test Results

- Ruff: passed.
- Focused pytest: `2 passed in 0.27s`.
- Full pytest: `810 passed in 34.32s`.
- HTML artifact check: passed; the report includes `Quality metrics`,
  `worst_frame_id`, core metric names, and controlled `bad`/`good` frame ids.

## CUDA Status

- CUDA available: yes.
- CUDA extension importable: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor artifact: `runs/checkpoints/s2_gate_357_cuda_doctor.json`.

## Artifacts

- `runs/checkpoints/s2_gate_357_quality_metrics_report.html`
- `runs/checkpoints/s2_gate_357_cuda_doctor.json`
- `runs/checkpoints/s2_gate_357_status.md`

## Artifact Summary

- Source quality artifact:
  `runs/checkpoints/s2_gate_354_quality_saturation_run/frame_quality.json`.
- Report summary includes quality distributions for star count, FWHM,
  eccentricity, background RMS, SNR, quality score, and weight.
- The controlled artifact correctly identifies `bad` as the worst frame for
  high background RMS, low quality score, and low weight.

## Known Limitations

- This gate surfaces existing frame-quality metrics only; it does not change
  star detection, FWHM/eccentricity estimation, SNR estimation, weighting, or
  quality-gate thresholds.
- Outlier rows are simple worst-value slices, not robust statistical outlier
  classifications.
- This gate does not change registration, integration, CUDA kernels, runtime
  defaults, packaging, publication, or real-data benchmark outputs.

## Next Step

- Continue quality/report hardening by carrying the core metric distribution
  summary into Phase2 status if release gates should compare quality-drift
  evidence between runs.

## Clean-Room Compliance

- Compliant. This gate used only GLASS-owned `frame_quality.json` artifacts,
  report code, tests, docs, and generated checkpoint artifacts.
- No official PixInsight/WBPP/PJSR source code or proprietary implementation
  material was read, copied, summarized, or reworked.
- Input image directories were not modified.
