# S2 Gate 424 Status - Resident Rejection Input Attribution

Date: 2026-06-19
Base commit: 09f48f5

## Gate Intent

Continue the Phase 2 mainline by acting on the Gate 423 blocker: inside the
declared common footprint, CPU and resident CUDA have matching pre-rejection
sample counts, but low/high rejection map decisions still differ. Gate 424
does not add release/default-promotion/report-only evidence. It builds an
algorithm attribution audit to determine whether the remaining delta comes
from the resident hardened winsorized rejection kernel or from upstream
resident registration/warp input differences.

## Implemented

- Added `glass resident-rejection-input-audit`.
- Added `src/glass/report/resident_rejection_input_audit.py`.
- The audit replays CPU `registered_cache` plus per-frame `coverage_cache`
  through:
  - CPU `weighted_integrate_stack(..., rejection="winsorized_sigma")`;
  - resident CUDA `ResidentCalibratedStack.integrate_hardened_winsorized_sigma`
    after uploading the exact same registered input samples.
- The audit then compares the already-produced resident CUDA output maps
  against the CPU output maps inside the declared compare-region footprint.
- Added `resident_output_parity` as a separate result from attribution:
  attribution can pass while resident output parity remains false.
- Added focused tests for the new report builder, CLI, and CUDA exact-input
  replay when CUDA is available.
- Updated `docs/phase2_algorithm_hardening.md` with S2-Gate 424 scope and
  acceptance.

## Validation Commands

- `.venv\Scripts\python.exe -m pytest -q tests/test_resident_rejection_input_audit.py tests/test_resident_rejection_sample_audit.py`
- `.venv\Scripts\python.exe -m glass.cli resident-rejection-input-audit --cpu-run runs\checkpoints\s2_gate_414_runtime_validation_cpu --resident-run runs\checkpoints\s2_gate_423_common_footprint_refF16_cuda_hardened --compare-json runs\checkpoints\s2_gate_423_common_footprint_compare.json --out runs\checkpoints\s2_gate_424_rejection_input_audit.json --markdown runs\checkpoints\s2_gate_424_rejection_input_audit.md --evaluation-region compare_region --max-same-pre-rejection-abs-delta 16`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_424_cuda_doctor.json`

## Results

- Targeted pytest: 7 passed in 0.57s.
- Full pytest: 1002 passed in 37.77s.
- Gate424 audit status: passed.
- Gate424 audit recommendation: `target_resident_registration_warp_input_parity`.
- CPU registered-cache replay versus CPU integration output:
  - coverage map delta: 0.
  - low rejection map delta: 0.
  - high rejection map delta: 0.
  - master max abs delta: 0.000244140625, accepted under the master-only
    floating accumulation tolerance of 0.0005.
- CUDA exact-input hardened winsorized replay versus CPU integration output:
  - master delta: 0.
  - coverage map delta: 0.
  - low rejection map delta: 0.
  - high rejection map delta: 0.
- Current resident output parity remains false inside the compare region:
  - pre-rejection abs delta: 0.
  - same-pre rejected-sample abs delta: 760.
  - low rejection abs delta: 381.
  - high rejection abs delta: 379.
  - coverage abs delta: 760.
  - attribution status: `resident_registration_warp_input_delta`.

## Interpretation

The hardened resident CUDA winsorized rejection kernel is not the source of the
Gate 423 same-pre rejection-map delta when it receives the same registered
input samples as the CPU baseline. The remaining mismatch comes from the
resident registration/warp input path: the resident run produces subtly
different warped sample values or frame/sample identities before rejection,
even where total pre-rejection sample counts match.

This is useful progress because it prevents wasting the next gate on the
already-proven rejection kernel and points the next fix at the resident
registration/warp path.

## CUDA

CUDA is available. Doctor output reports:

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- Recommended package path: cuda

Full report: `runs/checkpoints/s2_gate_424_cuda_doctor.json`

## Artifacts

- `runs/checkpoints/s2_gate_424_rejection_input_audit.json`
- `runs/checkpoints/s2_gate_424_rejection_input_audit.md`
- `runs/checkpoints/s2_gate_424_cuda_doctor.json`

## Known Limitations

- Gate424 is an attribution gate, not a final resident output parity closure.
- It uses the Gate414/Gate423 16-frame checkpoint harness, not the full
  200-light real regression.
- The resident output map still has 760 same-pre rejected-sample absolute
  delta inside the compare region. This is now attributed to resident
  registration/warp input parity, not to the hardened winsorized kernel.
- The audit loads the CPU registered checkpoint stack into RAM/VRAM for
  exact-input proof. It is intended for checkpoint-sized attribution runs, not
  as the production out-of-core integration path.

## Next Substantive Gate

S2 Gate 425 should target resident registration/warp input parity:

- Add a resident-vs-CPU warped-input audit for a small set of frames and tiles,
  comparing CPU registered_cache pixels against resident CUDA warped samples
  before rejection.
- Attribute the sample-value delta to matrix differences, bilinear
  interpolation differences, frame-validity identity differences, or edge
  coverage handling.
- Reduce the common-footprint same-pre rejection delta by improving matrix
  precision/warp interpolation parity or by explicitly defining a stricter
  common input-footprint contract.
- After warp-input parity improves, re-run the 16-frame parity gate and then
  the real 200-light regression/performance comparison.

## Clean-Room

Clean-room constraints remain satisfied. No PixInsight or WBPP/PJSR source was
read or used. This gate uses GLASS code, GLASS-generated checkpoint artifacts,
synthetic/checkpoint data, and public CUDA/Numpy-style numerical methods only.
