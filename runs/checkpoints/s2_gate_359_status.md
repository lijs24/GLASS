# S2-Gate 359 Status

- Gate: S2-Gate 359
- Scope: Quality metric compare artifact
- Status: green
- Date: 2026-06-19

## Completed Content

- Added `glass quality-metrics-compare` for baseline/candidate
  `frame_quality.json` artifacts.
- Added `src/glass/report/quality_metrics_compare.py`, which compares quality
  metric availability, frame counts, quality-gate status counts, median/mean
  deltas, bad-direction ratios, and worst-frame ids.
- Default checks require both artifacts to be readable and require candidate
  quality metrics to preserve the metrics available in the baseline.
- Added optional `--max-bad-median-ratio` and `--max-bad-mean-ratio`
  thresholds for controlled experiments and future benchmark contracts.
- Added CLI `--fail-on-failed` for CI/release-gate use.
- Added focused module and CLI tests.
- Documented the gate in `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m ruff check src\\glass\\report\\quality_metrics_compare.py src\\glass\\cli.py tests\\test_quality_metrics_compare.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_quality_metrics_compare.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\python.exe -m glass.cli quality-metrics-compare --baseline runs\\checkpoints\\s2_gate_359_quality_metrics_baseline_frame_quality.json --candidate runs\\checkpoints\\s2_gate_359_quality_metrics_candidate_frame_quality.json --out runs\\checkpoints\\s2_gate_359_quality_metrics_compare.json --markdown runs\\checkpoints\\s2_gate_359_quality_metrics_compare.md --max-bad-median-ratio 1.2`
- `.\\.venv\\Scripts\\python.exe -m glass.cli doctor --json runs\\checkpoints\\s2_gate_359_cuda_doctor.json --allow-cpu-only`
- `Select-String -Path runs\\checkpoints\\s2_gate_359_quality_metrics_compare.md -Pattern 'GLASS Quality Metrics Compare|bad_median_ratio_within_limit|fwhm_px|snr|FAIL|1.4'`

## Test Results

- Ruff: passed after removing one unused import.
- Focused pytest: `4 passed in 0.16s`.
- Full pytest: `816 passed in 34.58s`.
- Controlled compare artifact: `status=failed` because the optional
  `--max-bad-median-ratio 1.2` check detected 1.4x worse-direction median
  drift. Metric-preservation itself passed.

## CUDA Status

- CUDA available: yes.
- CUDA extension importable: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor artifact: `runs/checkpoints/s2_gate_359_cuda_doctor.json`.

## Artifacts

- `runs/checkpoints/s2_gate_359_quality_metrics_baseline_frame_quality.json`
- `runs/checkpoints/s2_gate_359_quality_metrics_candidate_frame_quality.json`
- `runs/checkpoints/s2_gate_359_quality_metrics_compare.json`
- `runs/checkpoints/s2_gate_359_quality_metrics_compare.md`
- `runs/checkpoints/s2_gate_359_cuda_doctor.json`
- `runs/checkpoints/s2_gate_359_status.md`

## Artifact Summary

- Baseline/candidate both preserve all seven configured quality metrics:
  `star_count`, `fwhm_px`, `eccentricity`, `background_rms`, `snr`,
  `quality_score`, and `weight`.
- Candidate quality metrics are intentionally degraded by about 1.4x in the
  controlled artifact.
- The optional median badness threshold correctly reports
  `bad_median_ratio_within_limit` as failed while
  `candidate_metric_summary_preserved` remains passed.

## Known Limitations

- Default behavior does not impose science thresholds; it only preserves
  metric availability. Threshold checks are opt-in until real-data evidence
  justifies benchmark-contract limits.
- This gate compares distribution summaries, not per-frame matched metric
  drift or image-pixel differences.
- This gate does not change quality metric math, star detection, registration,
  integration, CUDA kernels, runtime defaults, packaging, publication, or
  real-data benchmark outputs.

## Next Step

- Feed quality-metrics-compare artifacts into acceptance or Phase2 status once
  the 200-light benchmark has enough repeated evidence to justify specific
  quality-drift limits.

## Clean-Room Compliance

- Compliant. This gate used only GLASS-owned `frame_quality.json` artifacts,
  comparison/report code, CLI code, tests, docs, and generated checkpoint
  artifacts.
- No official PixInsight/WBPP/PJSR source code or proprietary implementation
  material was read, copied, summarized, or reworked.
- Input image directories were not modified.
