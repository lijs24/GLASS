# S2-Gate 56 Status: Resident Registration Determinism Signatures

## Gate

S2-Gate 56: Resident Registration Determinism Signatures.

## Completed Content

- Added exact SHA-256 signatures for resident triangle-registration catalogs,
  descriptors, selected descriptor fits, and threshold trial lists.
- Recorded detailed per-frame signatures under
  `resident_artifacts.json -> artifacts[] -> resident_registration ->
  triangle_determinism`.
- Added compact combined hashes for reference catalogs/descriptors, moving
  catalogs, selected fits, and threshold trials in the resident registration
  summary.
- Added per-frame registration warnings for catalog, descriptor, selected-fit,
  and trial signatures so repeated real-data runs can identify which stage
  diverged.
- Surfaced compact determinism fields in the HTML resident CUDA summary.
- Added helper tests proving signatures are stable and sensitive to array
  changes.
- Added repeated resident CUDA grid catalog batch checks to catch obvious
  same-stack catalog nondeterminism.
- Updated `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Commands Run

- `.\.venv\Scripts\python.exe -m ruff check src tests`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_resident_triangle_determinism_signatures_are_stable_and_sensitive tests\test_cuda_resident_stack.py::test_resident_stack_grid_star_catalog_batch_reports_native_timing tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe -c "import glass_cuda; print('cuda_available', glass_cuda.cuda_available()); print(glass_cuda.list_devices())"`

## Test Results

- Ruff: `All checks passed!`
- Focused tests: `3 passed in 0.43s`.
- Full pytest: `264 passed in 11.24s`.

## CUDA Availability

- CUDA available: yes.
- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver version: `596.21`.
- Native backend loaded: yes.

## 200-Light Benchmark Note

- This gate is diagnostic-only and does not modify CUDA kernels, registration
  selection rules, pixel-refine scoring, warp behavior, accepted frame counts,
  or output pixel math.
- A fresh 200-light benchmark was not rerun for this gate.
- The preserved S2-Gate 55 accepted benchmark remains the current performance
  and numerical baseline:
  `C:\glass_runs\phase2_s2_gate_55_200\resident_pixel_refine_flattened_metric_retry_20260601`.
- S2-Gate 55 accepted metrics: `16.410817299969494 s`, speedup
  `66.57444172521687x`, RMS `0.001592865209089461`, P99 absolute difference
  `0.0004341281461529463`, coverage fraction `0.9607661164746185`,
  acceptance audit `99` passed and `0` failed.

## Regression Note

- No image-math regression is expected because the change only hashes existing
  GLASS-generated arrays and metadata after they are selected.
- Small resident triangle-registration smoke tests prove the new artifact fields
  are emitted without changing the expected shifted-pair registration result.
- Repeated resident grid catalog batch tests now compare exact `x`, `y`, and
  `flux` arrays across back-to-back calls on the same resident stack.

## Artifacts

- New code path writes determinism details into future
  `resident_artifacts.json` files for `similarity_cuda_triangle` runs.
- Focused smoke tests generated temporary pytest run directories only.
- No new persistent 200-light run artifacts were generated in this gate.

## Known Limitations

- The signatures make drift localizable but do not by themselves remove the
  underlying nondeterminism observed during the first S2-Gate 55 real-data run.
- Detailed per-frame hashes increase `resident_artifacts.json` size for large
  triangle-registration runs.
- The signatures are exact float32 byte hashes, so any deliberate future change
  to catalog ordering, descriptor generation, or fit scoring will change them.

## Next Step

Use these signatures in the next real 200-light retry or dedicated audit to
compare two runs frame-by-frame. If catalog hashes differ, S2-Gate 57 should
introduce a strict deterministic resident catalog mode or replace the
lock-free/top-k precheck with a deterministic candidate compaction path for
acceptance runs.

## Clean-Room Compliance

Compliant. This gate hashes GLASS-owned resident CUDA outputs and registration
metadata only. It does not use proprietary implementation source and does not
copy or derive behavior from external closed-source tools.
