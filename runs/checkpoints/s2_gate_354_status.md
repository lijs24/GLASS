# S2-Gate 354 Status

- Gate: S2-Gate 354
- Scope: Streaming saturation quality metric
- Status: green
- Date: 2026-06-19

## Completed Content

- Added optional threshold-based saturation counting to streaming quality
  measurement.
- `_scan_quality_stats()` now counts saturated finite pixels while reading
  tiles when a `saturation_level` is supplied.
- `measure_quality_streaming()` now records `saturated_pixel_count`,
  `saturation_level`, and `saturation_source`.
- Existing DQ saturation counts remain supported; DQ and threshold counts are
  combined conservatively by taking the larger count.
- `measure_calibrated_quality()` now passes
  `registration_policy.quality_saturation_level` /
  `registration_policy.saturation_level` to streaming quality measurement.
- Added focused tests for direct tile-threshold saturation counting and
  calibrated quality-gate rejection by saturation threshold.
- Documented the gate in `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m ruff check src\\glass\\engine\\quality.py tests\\test_cpu_star_detect.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_cpu_star_detect.py::test_streaming_quality_counts_saturation_threshold_by_tile tests/test_cpu_star_detect.py::test_calibrated_quality_gate_uses_saturation_threshold_policy tests/test_cpu_star_detect.py::test_streaming_quality_matches_cpu_metrics tests/test_cpu_star_detect.py::test_calibrated_quality_gate_excludes_saturated_reference`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- Controlled artifact generation with GLASS Python APIs under
  `runs/checkpoints/s2_gate_354_quality_saturation_run`
- `.\\.venv\\Scripts\\python.exe -m glass.cli doctor --json runs\\checkpoints\\s2_gate_354_cuda_doctor.json --allow-cpu-only`

## Test Results

- Ruff: passed.
- Focused pytest: `4 passed in 0.18s`.
- Full pytest: `805 passed in 34.09s`.

## CUDA Status

- CUDA available: yes.
- CUDA extension importable: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor artifact: `runs/checkpoints/s2_gate_354_cuda_doctor.json`.

## Artifacts

- `runs/checkpoints/s2_gate_354_quality_saturation_run/frame_quality.json`
- `runs/checkpoints/s2_gate_354_quality_saturation_run/bad_threshold.fits`
- `runs/checkpoints/s2_gate_354_quality_saturation_run/good_threshold.fits`
- `runs/checkpoints/s2_gate_354_quality_saturation_run/calibration_artifacts.json`
- `runs/checkpoints/s2_gate_354_quality_saturation_run/processing_plan.json`
- `runs/checkpoints/s2_gate_354_cuda_doctor.json`
- `runs/checkpoints/s2_gate_354_status.md`

## Artifact Summary

- Controlled bad frame: `saturated_pixel_count=36`,
  `saturation_source=threshold`, `quality_gate_status=rejected`.
- Controlled good frame: `saturated_pixel_count=0`,
  `saturation_source=threshold`, `quality_gate_status=accepted`.
- Selected reference frame: `good`.

## Known Limitations

- Threshold saturation counting is opt-in through registration policy; no
  default saturation level is assumed for calibrated float images.
- This gate does not change the star detector, quality weighting formula,
  registration, integration, CUDA kernels, runtime defaults, packaging,
  publication, or real-data benchmark outputs.

## Next Step

- Continue hardening quality metrics, likely by adding a saturation summary to
  reports or by introducing the next missing quality metric from the Phase 2
  list, such as a stronger SNR/noise or eccentricity diagnostic.

## Clean-Room Compliance

- Compliant. This gate used only GLASS-owned calibrated-frame artifacts,
  synthetic test images, source files, tests, docs, and generated artifacts.
- No official PixInsight/WBPP/PJSR source code or proprietary implementation
  material was read, copied, summarized, or reworked.
- Input image directories were not modified.
