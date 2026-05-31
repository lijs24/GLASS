# S2-Gate 40 Status: Registration Honors Quality Gate

## Gate

S2-Gate 40 makes registration consume the S2-Gate 39 quality-gate contract.
Quality-rejected non-reference frames are now skipped before registration work
and therefore cannot silently enter warp or integration.

## Completed Content

- Added `reject_quality_gate_failed_frames` registration-policy enforcement,
  defaulting to enabled for quality artifacts that carry gate status.
- Registration rows now record:
  - `quality_gate_status`
  - `quality_gate_warnings`
  - `quality_gate_enforced`
- `registration_results.json` now records:
  - `quality_gate_enforced`
  - `quality_gate_rejected_frames`
  - `quality_gate_summary`
- Non-reference frames with `quality_gate_status=rejected` receive:
  - `status=quality_rejected`
  - `registration_solution_source=quality_gate`
  - no preview/registration work
  - explicit warnings copied from the quality gate
- Existing warp behavior skips non-accepted registration rows, so
  quality-rejected frames are reported in `warp_results.json` `skipped_frames`
  and do not enter integration.
- Older quality artifacts without gate fields remain compatible because only an
  explicit `quality_gate_status=rejected` triggers the skip.
- End-to-end benchmark output now includes:
  - `input_light_frame_count`
  - `quality_gate_enforced`
  - `quality_gate_rejected_frames`
  - `registered_or_integrated_frame_count`
- Updated:
  - `docs/phase2_algorithm_hardening.md`
  - `docs/algorithm_sources.md`

## Regression Found And Fixed

The first full pytest run failed:

```text
test_bench_end_to_end_cpu_outputs_required_fields
assert payload["frame_count"] == 2
E assert 1 == 2
```

This was a real behavior change: the tiny 2-light CPU benchmark had one frame
rejected by the quality gate before registration. The fix was to make the
benchmark output the input light count and quality-gate rejected count, then
test the auditable invariant:

```text
frame_count + quality_gate_rejected_frames == input_light_frame_count
```

This preserves the new gate behavior while making frame-count changes explicit
instead of silent.

## Real-Data Report Regeneration

Command:

```powershell
.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531 --out C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\s2_gate_40_report.html
```

Result:

- Report path:
  `C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\s2_gate_40_report.html`
- Report size: `242312` bytes.
- Verified report content:
  - `Report navigation`: present once
  - benchmark speedup `34.3178020369665`: present
  - acceptance status `passed`: present
  - `Registration table`: present

The preserved 200-light resident artifact directory predates the new
quality-gate registration fields, so this validates report backward
compatibility and benchmark-summary preservation.

## Small Benchmark Audit Evidence

Command:

```powershell
.venv\Scripts\python.exe benchmarks\bench_end_to_end.py --out runs\s2_gate_40_bench_end_to_end.json --frames 2 --width 16 --height 16 --tile-size 8 --backend cpu
```

Result:

- Benchmark JSON:
  `C:\Users\ljs\WORK\astro\gpuwbpp\runs\s2_gate_40_bench_end_to_end.json`
- Input light frames: `2`
- Integrated frame count: `1`
- Quality-gate rejected frames: `1`
- Registration rows:
  - `F000010`: `quality_rejected`, source `quality_gate`
  - `F000011`: `reference`
- Warp skipped frames include `F000010` with
  `status=quality_rejected` and the quality warning
  `star_count 1 below min_stars=8`.

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests\test_cpu_registration.py::test_register_calibrated_frames_skips_quality_rejected_frames tests\test_pipeline_fixture.py::test_pipeline_fixture_run_registration tests\test_pipeline_fixture.py::test_pipeline_fixture_run_warp`
- `.venv\Scripts\python.exe -m ruff check src\glass\engine\registration.py tests\test_cpu_registration.py tests\test_pipeline_fixture.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_benchmarks.py::test_bench_end_to_end_cpu_outputs_required_fields tests\test_cpu_registration.py::test_register_calibrated_frames_skips_quality_rejected_frames tests\test_pipeline_fixture.py::test_pipeline_fixture_run_registration tests\test_pipeline_fixture.py::test_pipeline_fixture_run_warp`
- `.venv\Scripts\python.exe -m ruff check src\glass\engine\registration.py benchmarks\bench_end_to_end.py tests\test_cpu_registration.py tests\test_pipeline_fixture.py tests\test_benchmarks.py`
- `.venv\Scripts\python.exe -m ruff check .`
- `.venv\Scripts\python.exe -m pytest -q`
- CUDA device probe
- `git diff --check`
- real-data report regeneration command above
- small benchmark command above

## Test Results

- First targeted registration/pipeline tests: `3 passed in 1.57s`.
- First full pytest: `1 failed, 251 passed in 11.14s`.
- Fixed benchmark audit fields and reran targeted tests:
  `4 passed in 2.20s`.
- Targeted lint after fix: `All checks passed!`.
- Full lint: `All checks passed!`.
- Full pytest: `252 passed in 11.02s`.
- `git diff --check`: no whitespace errors.

## CUDA

CUDA is available.

- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver: `596.21`
- Native backend: `true`

## Performance And Numerical Regression Note

This gate affects CPU registration routing for future runs when quality-gate
artifacts explicitly reject a frame. It does not change calibration, quality
measurement, warp kernels, local normalization, integration math, resident CUDA
kernels, or compare metrics. The small benchmark now records quality-gate frame
exclusion as an explicit performance/result input. The preserved 200-light
resident benchmark was not rerun because this gate does not change the resident
CUDA fast path or existing preserved artifacts.

## Known Limitations

- The quality-gate enforcement currently applies to the CPU registration path.
  Resident CUDA has separate quality/weight handling and still needs a parity
  bridge.
- Quality-rejected reference frames are allowed when a user explicitly requests
  one or when the quality stage fell back to all frames; the registration row
  records a warning.
- This gate skips quality-rejected frames before registration. It does not yet
  expose a user-facing CLI switch beyond plan policy JSON.

## Next Step

Proceed to the next Phase 2 gate in `docs/phase2_algorithm_hardening.md`.
The natural follow-up is to add a shared accepted-frame accounting summary so
quality, registration, warp, LN, and integration can report exactly why each
input light was used, skipped, or zero-weighted.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned quality metrics and registration
artifacts. No external implementation source was read or used.
