# S2 Gate 425 Status - Resident Warp Input Parity Attribution

Date: 2026-06-19
Base commit: f9284bc

## Gate Intent

Continue from Gate 424 by moving upstream from rejection-map semantics to the
resident registration/warp input path. Gate 424 proved that the resident
hardened winsorized rejection kernel matches the CPU baseline when it receives
the same registered samples. Gate 425 determines whether the remaining
same-pre rejection-map delta is caused by the resident warp kernel contract or
by resident registration matrix precision.

This gate is runtime-validation scoped. It does not add release/default
promotion/report-only evidence and does not modify input data.

## Implemented

- Added `glass resident-warp-input-audit`.
- Added `src/glass/report/resident_warp_input_audit.py`.
- The audit loads CPU calibrated checkpoint frames, uploads them into
  `ResidentCalibratedStack`, and replays resident CUDA bilinear warp twice:
  - once with the CPU registration matrix;
  - once with the resident CUDA registration matrix.
- The audit compares both resident CUDA warped outputs against the CPU
  `registered_cache` and `coverage_cache` inside the declared compare/common
  footprint.
- The artifact records per-frame:
  - CPU and resident matrices;
  - translation and Frobenius matrix deltas;
  - resident warp method;
  - RMS/mean/P99/max pixel deltas;
  - coverage sample deltas.
- Added focused CUDA tests for the CLI and the matrix-delta attribution path.
- Updated `docs/phase2_algorithm_hardening.md`.
- Updated `docs/algorithm_sources.md`.

## Validation Commands

- `.venv\Scripts\python.exe -m pytest -q tests/test_resident_warp_input_audit.py`
- `.venv\Scripts\python.exe -m glass.cli resident-warp-input-audit --cpu-run runs\checkpoints\s2_gate_414_runtime_validation_cpu --resident-run runs\checkpoints\s2_gate_423_common_footprint_refF16_cuda_hardened --compare-json runs\checkpoints\s2_gate_423_common_footprint_compare.json --out runs\checkpoints\s2_gate_425_warp_input_audit.json --markdown runs\checkpoints\s2_gate_425_warp_input_audit.md --max-frames 16 --cpu-matrix-rms-tolerance 5e-4 --resident-matrix-rms-tolerance 0.1`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_425_cuda_doctor.json`

## Results

- Targeted pytest: 2 passed in 0.28s.
- Full pytest: 1004 passed in 37.81s.
- Gate425 audit status: passed.
- Gate425 audit recommendation: `target_resident_registration_matrix_precision`.
- Audited frames: 16.
- CUDA warp replay completed for all audited frames.

### CPU Matrix Replay

Using the CPU registration matrix but the resident CUDA warp kernel:

- CPU-matrix resident warp RMS max: 0.0002772813662932653.
- CPU-matrix resident warp RMS mean: 0.000191432803370453.
- Coverage sample delta: 0 for the inspected frames in the compare footprint.
- Result: resident CUDA bilinear warp is close enough to the CPU registered
  cache under the CPU matrix contract for this checkpoint.

### Resident Matrix Replay

Using the resident CUDA registration matrix:

- Resident-matrix resident warp RMS max: 0.19260848801144254.
- Resident-matrix resident warp RMS mean: 0.08695099070490556.
- Resident matrix warp parity: false.
- Matrix translation delta max: 0.008781854250385976 px.
- Matrix translation delta mean: 0.0039021745376517994 px.
- Worst frames:
  - F000024: matrix delta 0.008781854250385976 px, resident-matrix RMS 0.19260848801144254.
  - F000013: matrix delta 0.008740052972894322 px, resident-matrix RMS 0.18657174565052745.
  - F000023: matrix delta 0.007045797277192498 px, resident-matrix RMS 0.16288839493579732.

## Interpretation

The resident CUDA warp kernel is not the main blocker when it is fed the CPU
matrix: it agrees with CPU registered-cache pixels at sub-millimag RMS scale
and preserves coverage. The major remaining mismatch is caused by resident
registration matrices being slightly different from CPU matrices. In this
checkpoint the resident triangle path is effectively snapping/rounding to
integer translations, while CPU registration keeps subpixel translation terms.

This explains why Gate423/Gate424 saw matching pre-rejection sample counts but
different low/high rejection samples: tiny subpixel registration differences
change warped star-edge/background sample values enough to flip some
winsorized rejection decisions.

## CUDA

CUDA is available. Doctor output reports:

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- Recommended package path: cuda

Full report: `runs/checkpoints/s2_gate_425_cuda_doctor.json`

## Artifacts

- `runs/checkpoints/s2_gate_425_warp_input_audit.json`
- `runs/checkpoints/s2_gate_425_warp_input_audit.md`
- `runs/checkpoints/s2_gate_425_cuda_doctor.json`

## Known Limitations

- Gate425 is an attribution gate, not the final registration fix.
- It uses the Gate414/Gate423 16-frame checkpoint harness, not the full
  200-light real-data regression.
- The audit loads checkpoint-sized calibrated frames into RAM/VRAM and is not
  the production out-of-core execution path.
- The audit currently supports resident bilinear warp. Lanczos3/fused-matrix
  attribution remains future work.
- The resident output still needs a registration-matrix precision fix before
  re-running the 16-frame parity and 200-light regression gates.

## Next Substantive Gate

S2 Gate 426 should fix resident registration matrix precision:

- Preserve and apply the subpixel translation estimated by resident triangle
  matching instead of allowing the default resident path to collapse to integer
  translations.
- Keep the fix inside resident registration logic, not in rejection or
  integration.
- Re-run Gate425 to confirm resident-matrix RMS drops toward CPU-matrix RMS.
- Re-run Gate423/Gate424 parity artifacts to confirm same-pre rejection delta
  shrinks.
- Only after the 16-frame checkpoint is green, re-run the real 200-light
  resident performance/numerical regression.

## Clean-Room

Clean-room constraints remain satisfied. No PixInsight or WBPP/PJSR source was
read or used. This gate uses GLASS code, GLASS-generated checkpoint artifacts,
and generic matrix/warp comparison math only.
