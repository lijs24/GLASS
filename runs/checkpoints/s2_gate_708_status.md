# S2-Gate 708 Status: CPU Master Helper StackEngine Default

## Gate

S2-Gate 708: move the public CPU master-frame helpers onto the Phase 2
StackEngine contract surface by default.

## Completed Content

- Updated `glass.cpu.master_frames.mean_stack(...)` to open FITS/XISF
  `ImageSource` adapters and execute `CPUStackEngine` with mean combine and
  no-rejection policy.
- Extended `MasterFrameResult` with backward-compatible metadata fields:
  `engine`, `metrics`, `dq_provenance`, and `dq_mask`.
- Updated `make_master_bias`, `make_master_dark`, and `make_master_flat` to
  preserve StackEngine metrics/provenance and record their postprocess
  operation.
- Added test coverage proving:
  - synthetic bias/dark/flat helpers still produce expected values;
  - the public helper reports `engine=stack_engine_cpu`;
  - StackEngine result contracts pass;
  - non-finite source samples are treated as invalid input samples instead of
    being silently averaged.
- Added synthetic validation artifact:
  `runs/checkpoints/s2_gate_708_cpu_master_stack_engine_helper/validation.json`.
- Updated documentation:
  - `docs/phase2_algorithm_hardening.md`;
  - `docs/calibration_model.md`;
  - `docs/known_limitations.md`;
  - `docs/validation.md`;
  - `docs/algorithm_sources.md`.

## Commands Run

- Focused tests:
  `.\.venv\Scripts\python.exe -m pytest -q tests/test_cpu_master_frames.py tests/test_gpu_master_frames_vs_cpu.py`
- Ruff:
  `.\.venv\Scripts\python.exe -m ruff check src/glass/cpu/master_frames.py tests/test_cpu_master_frames.py`
- Synthetic validation artifact script:
  generated `runs/checkpoints/s2_gate_708_cpu_master_stack_engine_helper/validation.json`
- Full tests:
  `.\.venv\Scripts\python.exe -m pytest -q`
- CUDA device probe through `glass_cuda`.

## Test Results

- Focused tests: `5 passed in 0.46s`.
- Ruff: passed.
- Full pytest: `1453 passed in 73.65s`.

## Validation Artifact

Artifact:

`runs/checkpoints/s2_gate_708_cpu_master_stack_engine_helper/validation.json`

Recorded evidence:

- Invalid-sample fixture:
  - `engine=stack_engine_cpu`;
  - invalid/non-finite input samples before rejection: `2`;
  - valid samples after rejection: `6`;
  - result contract passed: `true`;
  - output DQ summary: `{"valid": 4}`.
- Synthetic bias fixture:
  - `engine=stack_engine_cpu`;
  - shape: `24 x 32`;
  - mean: `999.8694458007812`;
  - result contract passed: `true`;
  - postprocess operation: `bias_mean`;
  - output DQ summary: `{"valid": 768}`.

## Real 200-Light Status

Not rerun for this gate. Gate708 changes the public CPU baseline/API helper and
does not touch the resident CUDA 200-light hot path, resident calibration,
registration, warp, LN, rejection, or integration kernels. The correct
validation scope is focused CPU/GPU master-frame parity plus synthetic
StackEngine/DQ contract evidence.

## CUDA Availability

CUDA available: yes.

Detected device:

- Name: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver: `596.21`
- Native backend: `true`

## Known Limitations

- Public CPU master helpers still return a full `MasterFrameResult.data` array
  for API compatibility. The large-data pipeline remains the sink-oriented
  StackEngine master-frame path.
- GPU master-frame helper contract unification remains future work.
- This gate does not change resident CUDA performance or the 200-light default
  runtime.

## Next Step

Continue with a substantive mainline gate: either unify GPU master-frame helper
contract surfaces, reduce actual resident read/H2D/calibration overlap cost, or
batch resident registration/warp orchestration under the existing Phase 2
mainline A/B guard.

## Clean-Room Compliance

Compliant. This gate used GLASS-owned StackEngine contracts, image-source
adapters, CPU/GPU parity tests, and GLASS-generated synthetic fixtures only. No
external or proprietary implementation source was inspected, copied,
summarized, or reworked. Original image directories remained read-only.
