# S2-Gate 39 Status: Quality Gate Reference Candidates

## Gate

S2-Gate 39 adds a first-pass quality gate to `frame_quality.json` so automatic
reference selection is auditable. Each calibrated light is now marked as an
accepted or rejected reference candidate before the reference frame is selected.

## Completed Content

- Added a quality-gate policy derived from `processing_plan.json`
  `registration_policy`:
  - `min_stars`
  - `quality_max_saturation_fraction`
  - `quality_min_score`
  - `quality_require_fwhm`
- Added per-frame quality fields:
  - `quality_gate_status`
  - `quality_gate_warnings`
  - `reference_candidate`
- Automatic reference selection now uses accepted quality-gate candidates
  first.
- If every frame fails the quality gate, selection falls back to all frames and
  records `reference_selection_fallback=true`.
- Added `quality_gate_policy` and `quality_gate_summary` to
  `frame_quality.json`.
- Surfaced quality-gate summary counts and policy in the HTML report.
- Added synthetic coverage proving a saturated high-star frame is rejected as a
  reference candidate in favor of a lower-star accepted frame.
- Updated:
  - `docs/phase2_algorithm_hardening.md`
  - `docs/algorithm_sources.md`

## Real-Data Report Regeneration

Command:

```powershell
.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531 --out C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\s2_gate_39_report.html
```

Result:

- Report path:
  `C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\s2_gate_39_report.html`
- Report size: `242312` bytes.
- Verified report content:
  - `Report navigation`: present once
  - benchmark speedup `34.3178020369665`: present
  - acceptance status `passed`: present

The preserved 200-light resident artifact directory does not contain a
`frame_quality.json`, so this regeneration validates backward-compatible report
rendering and benchmark-summary preservation rather than rerunning the quality
stage over the full dataset.

## Synthetic Quality-Gate Fixture

Command:

```powershell
.venv\Scripts\python.exe <synthetic quality-gate fixture script>
.venv\Scripts\glass.exe report --run runs\s2_gate_39_quality_fixture --out runs\s2_gate_39_quality_fixture\report.html
```

Result:

- Fixture report:
  `C:\Users\ljs\WORK\astro\gpuwbpp\runs\s2_gate_39_quality_fixture\report.html`
- Selected reference: `good`
- Quality gate summary:
  - accepted: `1`
  - rejected: `1`
  - reference candidates: `1`
  - fallback used: `false`
  - rejection reason: `saturation_fraction`
- The HTML report includes `reference_candidates`,
  `max_saturation_fraction`, and per-row `quality_gate_status` evidence.

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests\test_cpu_star_detect.py::test_calibrated_quality_gate_excludes_saturated_reference tests\test_pipeline_fixture.py::test_pipeline_fixture_run_quality_and_report`
- `.venv\Scripts\python.exe -m ruff check src\glass\engine\quality.py src\glass\report\html_report.py tests\test_cpu_star_detect.py tests\test_pipeline_fixture.py`
- `.venv\Scripts\python.exe -m ruff check .`
- `.venv\Scripts\python.exe -m pytest -q`
- CUDA device probe
- `git diff --check`
- real-data report regeneration command above
- synthetic quality-gate fixture and report generation command above

## Test Results

- Targeted quality/report tests: `2 passed in 0.79s`.
- Targeted lint: `All checks passed!`.
- Full lint: `All checks passed!`.
- Full pytest: `251 passed in 11.73s`.
- `git diff --check`: no whitespace errors.

## CUDA

CUDA is available.

- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver: `596.21`
- Native backend: `true`

## Performance And Numerical Regression Note

This gate changes CPU quality-stage artifact generation and automatic reference
candidate selection for future runs. It does not change calibration, warp,
local normalization, integration, resident CUDA kernels, compare metrics, or
FITS output math. A full 200-light rerun was not required for this gate because
the preserved resident benchmark artifacts were not reprocessed; the checkpoint
records the report compatibility check instead.

## Known Limitations

- The quality gate only affects automatic reference-frame selection today.
  Downstream zero-weighting or integration exclusion for rejected quality frames
  remains future work.
- Defaults are conservative and project-defined; data-set-specific tuning may
  need explicit `registration_policy` overrides.
- The 200-light preserved run did not have a quality artifact to upgrade in
  place, so real-data quality-gate behavior is represented by synthetic
  verification in this gate.

## Next Step

Proceed to the next Phase 2 gate in `docs/phase2_algorithm_hardening.md`.
The natural follow-up is to propagate quality-gate status into registration and
integration decisions so rejected frames are not merely annotated.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned quality metrics and calibration DQ
summaries. No external implementation source was read or used.
