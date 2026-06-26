# S2-Gate 710 Status: GPU Master Helper Finite-Sample DQ

## Gate

S2-Gate 710: add finite-sample DQ/coverage semantics to the public GPU
master-frame helper.

## Completed Content

- Updated `glass.gpu.master_frames.mean_stack_paths_tile_streaming(...)` to
  compute a per-pixel coverage map while streaming tiles.
- Updated the CUDA helper path to call the existing
  `integrate_accumulate_mean_tile_f32` wrapper with:
  - `safe_frame = where(isfinite(frame), frame, 0)`;
  - `weight_tile = isfinite(frame)`.
- Updated the no-CUDA fallback to use the same finite-sample weighting model.
- Added output `DQMask` production:
  - pixels with no finite input samples are marked `NO_DATA`;
  - finite-covered pixels remain valid.
- Added metrics/provenance:
  - input sample count;
  - valid/invalid/non-finite sample counts;
  - valid samples after rejection;
  - coverage-zero pixel count;
  - DQ summary;
  - `result_contract_passed`.
- Added a StackEngine result contract over the helper's master/coverage/DQ
  surfaces without relabeling the helper as CPUStackEngine.
- Updated focused tests to prove:
  - no-CUDA fallback emits DQ and passes the result contract;
  - fake-native CUDA uses finite-sample weights and marks `NO_DATA`;
  - actual CUDA helper emits DQ/contract metadata on synthetic data.
- Added synthetic validation artifact:
  `runs/checkpoints/s2_gate_710_gpu_master_dq_contract/validation.json`.
- Updated documentation:
  - `docs/phase2_algorithm_hardening.md`;
  - `docs/calibration_model.md`;
  - `docs/known_limitations.md`;
  - `docs/validation.md`;
  - `docs/algorithm_sources.md`.

## Commands Run

- Focused tests:
  `.\.venv\Scripts\python.exe -m pytest -q tests/test_gpu_master_frames_vs_cpu.py tests/test_cpu_master_frames.py`
- Ruff:
  `.\.venv\Scripts\python.exe -m ruff check src/glass/gpu/master_frames.py tests/test_gpu_master_frames_vs_cpu.py`
- Synthetic validation artifact script:
  generated `runs/checkpoints/s2_gate_710_gpu_master_dq_contract/validation.json`
- Full tests:
  `.\.venv\Scripts\python.exe -m pytest -q`
- CUDA device probe through `glass_cuda`.

## Test Results

- Focused tests: `7 passed in 0.57s`.
- Ruff: passed.
- Full pytest: `1455 passed in 73.32s`.

## Validation Artifact

Artifact:

`runs/checkpoints/s2_gate_710_gpu_master_dq_contract/validation.json`

The fixture has two 2x2 frames with four finite samples and four non-finite
samples. Expected master:

`[[0.0, 9.0], [5.0, 9.0]]`

Recorded evidence for CPUStackEngine, no-CUDA fallback, fake-native CUDA, and
actual-native CUDA:

- max absolute difference versus expected: `0.0`;
- input samples: `8`;
- valid samples: `4`;
- invalid samples: `4`;
- coverage-zero pixels: `1`;
- DQ summary: `{"valid": 3, "no_data": 1}`;
- `NO_DATA` pixels: `1`;
- result contract passed: `true`.

Fake-native CUDA recorded `8` native calls. Actual-native CUDA recorded
`cuda_native_available=true` and `cuda_accumulator_used=true`.

## Real 200-Light Status

Not rerun for this gate. Gate710 changes the public GPU master-frame helper's
finite-sample DQ semantics. It does not touch resident CUDA calibration,
registration, warp, LN, rejection, integration kernels, or the 200-light default
runtime path.

## CUDA Availability

CUDA available: yes.

Detected device:

- Name: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver: `596.21`
- Native backend: `true`

## Known Limitations

- The GPU helper handles non-finite sample validity only.
- It still does not consume source DQ sidecars.
- Full source-DQ-aware master-frame handling remains owned by CPU/tile
  StackEngine sink calibration and resident DQ sidecar paths until a future
  gate explicitly extends the helper.
- This is a DQ/mask contract gate, not a resident CUDA performance gate.

## Next Step

Return to a larger mainline gate: reduce resident read/H2D/calibration overlap
cost, batch resident registration/warp orchestration, or extend source-DQ
sidecar consumption where it affects the real pipeline.

## Clean-Room Compliance

Compliant. This gate used GLASS-owned DQ semantics, GPU helper code, CUDA
wrapper behavior, tests, and GLASS-generated synthetic fixtures only. No
external or proprietary implementation source was inspected, copied,
summarized, or reworked. Original image directories remained read-only.
