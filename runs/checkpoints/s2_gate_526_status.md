# S2-Gate 526 Status: Resident DQ Valid-Map Fast Path

## Gate

- Gate: S2-Gate 526
- Date: 2026-06-23
- Scope: resident DQ/mask pipeline runtime optimization

## Completed

- Added a guarded `assume_valid_master_weight` fast path for resident DQ map
  generation when `_output_diagnostics` proves:
  - master pixels are finite;
  - weight pixels are all positive;
  - zero-weight pixels are absent.
- Added a guarded `assume_nonnegative_count_maps` path for GLASS-generated
  finite, nonnegative coverage and rejection count maps.
- Avoided unnecessary no-data mask allocation/scans when post-rejection and
  geometric coverage maps have no zero pixels.
- Kept strict DQ helper behavior available for arbitrary arrays.
- Added a focused synthetic test proving the valid-master/nonnegative-count
  fast path matches the strict Python path bitwise.

## Real 200-Light Validation

- Baseline:
  `C:\glass_runs\phase2_s2_gate525_translation_refine_default\runs_20260623_111012\default`
- Gate526 run:
  `C:\glass_runs\phase2_s2_gate526_dq_fastpath_real\runs_20260623_120000\default`
- Command family:
  resident CUDA, `similarity_cuda_triangle`, Lanczos3 warp, winsorized sigma,
  audit output maps, shared master cache.

Measured results:

- Gate525 baseline shell: `6.75901 s`
- Gate526 shell: `6.290154 s`
- Gate525 baseline internal: `6.399099300033413 s`
- Gate526 internal: `5.946307100006379 s`
- `_resident_dq_map_python` profile cumulative time:
  - before: `1.3944242 s`
  - after: `0.9936101 s`

DQ summary stayed identical:

- valid: `22720993`
- warp_edge: `1690704`
- low_rejected: `12560911`
- high_rejected: `32082764`

## Numerical Validation

Gate526 vs Gate525 bitwise comparison:

- `resident_master_H.fits`: identical
- `resident_weight_map_H.fits`: identical
- `resident_coverage_map_H.fits`: identical
- `resident_low_rejection_map_H.fits`: identical
- `resident_high_rejection_map_H.fits`: identical
- `resident_dq_map_H.fits`: identical

For all six outputs, RMS, p99 absolute difference, and max absolute difference
were `0.0`.

Because Gate526 is bitwise identical to Gate525/Gate524, the prior WBPP
black-box comparison remains applicable:

- robust-fit RMS `0.0015009512947433384`
- p99 absolute difference `0.00034034321741462114`
- fit fraction `0.982980688129347`

## Commands Run

- `.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py tests\test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py -k "resident_dq_map"`
- `.\.venv\Scripts\python.exe -m glass.cli run --plan ... --out ... --backend cuda --memory-mode resident --until-stage integration ...`
- `.\.venv\Scripts\python.exe -m cProfile -o ... -m glass.cli run --plan ...`
- `.\.venv\Scripts\python.exe -m json.tool runs\checkpoints\s2_gate_526_dq_valid_map_fastpath_summary.json`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_526_doctor.json`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Ruff: passed.
- Focused DQ tests: `11 passed, 79 deselected`.
- Full pytest: `1170 passed in 42.71s`.

## CUDA Status

- CUDA wrapper importable: true.
- CUDA native extension loaded: true.
- CUDA available: true.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21

## Artifacts

- Checkpoint: `runs/checkpoints/s2_gate_526_status.md`
- Summary JSON:
  `runs/checkpoints/s2_gate_526_dq_valid_map_fastpath_summary.json`
- Doctor JSON: `runs/checkpoints/s2_gate_526_doctor.json`
- Before profile:
  `C:\glass_runs\phase2_s2_gate526_profile_current\runs_20260623_120000\profile_current.prof`
- After profile:
  `C:\glass_runs\phase2_s2_gate526_dq_fastpath_profile\runs_20260623_120000\profile_after.prof`
- Real run root:
  `C:\glass_runs\phase2_s2_gate526_dq_fastpath_real\runs_20260623_120000`

## Known Limitations

- This gate optimizes the Python DQ fallback for the verified resident pipeline
  case. It is not a new CUDA kernel.
- The strict general DQ path remains required for arbitrary user arrays with
  non-finite, fractional, or negative count maps.
- The next gate should avoid further narrow DQ/report cleanup and return to
  larger resident GPU work: registration/warp batching, host/device
  orchestration, and light-pipeline overlap.

## Clean-Room Compliance

- This gate used only GLASS code, GLASS-generated artifacts, the user-owned
  200-light benchmark data, and prior user-generated WBPP black-box comparison
  metrics.
- No official PixInsight/WBPP/PJSR source was read, copied, summarized, or
  reworked.
- Input image directories were not modified.
