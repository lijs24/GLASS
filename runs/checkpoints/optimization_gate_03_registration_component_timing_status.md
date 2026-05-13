# Optimization Gate 03: Resident Registration Component Timing

## Gate

Optimization Gate 03.

## Completed content

- Added component-level timing for resident `similarity_cuda_triangle` registration.
- Timing now separates:
  - threshold selection
  - reference catalog detection
  - moving catalog detection
  - reference triangle descriptors
  - moving triangle descriptors
  - triangle descriptor fitting
  - pixel refinement
  - resident matrix warp
  - Python orchestration or uninstru­mented remainder
- Added `fine_timing.registration_component_seconds` to resident artifacts.
- Added top-level `timing_s` fields:
  - `resident_registration_component_accounted`
  - `resident_registration_orchestration`
- Exposed registration accounted/orchestration timings in HTML reports.
- Added tests covering triangle component timing schema and report columns.

## Commands

```powershell
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp\engine\resident_cuda.py src\gpwbpp\report\html_report.py tests\test_resident_cuda_run.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair tests\test_cli_smoke.py::test_cli_report_includes_resident_artifacts
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q
```

## Test result

- Ruff: all checks passed.
- Targeted timing/report tests: 2 passed.
- Resident CUDA run tests: 14 passed.
- Full pytest: 180 passed in 8.13 s.

## CUDA availability

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: yes.

## Known limitations

- This checkpoint instruments the registration bottleneck but does not yet batch native calls or change algorithms.
- Timings are collected at Python/native binding boundaries; deeper kernel-internal timing still requires native instrumentation.
- The real M38 benchmark must be rerun to populate the new component buckets.

## Next step

- Run the M38 200-light `prefetch=2` resident parity command with the new registration component timing.
- Use the resulting component breakdown to choose the first high-impact batching target: catalog detection, descriptor generation, descriptor fitting, pixel refinement, or warp.

## Clean-room compliance

- Compliant. No PixInsight/WBPP/PJSR source files were read, copied, summarized, or modified.
- No original data directory was modified.
