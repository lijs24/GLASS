# S2-Gate 709 Status: GPU Master Helper Metadata Contract

## Gate

S2-Gate 709: correct the public GPU master-frame helper metadata after
S2-Gate 708 introduced `MasterFrameResult.engine` and StackEngine provenance
fields.

## Completed Content

- Updated `glass.gpu.master_frames.mean_stack_paths_tile_streaming(...)` to
  report the actual helper execution engine:
  - `cuda_tile_streaming_mean` when the native CUDA mean accumulator wrapper is
    available and used;
  - `cpu_tile_streaming_mean_fallback` when CUDA/native accumulation is not
    available.
- Added helper metrics:
  - `cuda_native_available`;
  - `cuda_accumulator_used`;
  - `tile_count`;
  - `tile_size`;
  - frame count and shape;
  - combine/rejection labels;
  - DQ capability flags.
- Added minimal DQ provenance explaining that this GPU helper path is a
  CUDA-vs-CPU parity helper and does not produce DQ masks.
- Updated `make_master_bias`, `make_master_dark`, and `make_master_flat` to
  preserve helper metadata and record postprocess operation names.
- Added tests for:
  - no-CUDA fallback metadata;
  - fake-native CUDA accumulator usage;
  - actual CUDA helper shape/stat metadata.
- Added synthetic validation artifact:
  `runs/checkpoints/s2_gate_709_gpu_master_helper_contract/validation.json`.
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
  generated `runs/checkpoints/s2_gate_709_gpu_master_helper_contract/validation.json`
- Full tests:
  `.\.venv\Scripts\python.exe -m pytest -q`
- CUDA device probe through `glass_cuda`.

## Test Results

- Focused tests: `6 passed in 0.51s`.
- Ruff: passed.
- Full pytest: `1454 passed in 73.33s`.

## Validation Artifact

Artifact:

`runs/checkpoints/s2_gate_709_gpu_master_helper_contract/validation.json`

Recorded evidence:

- CPU baseline:
  - `engine=stack_engine_cpu`;
  - result contract passed: `true`;
  - mean: `999.8694458007812`.
- No-CUDA fallback:
  - `engine=cpu_tile_streaming_mean_fallback`;
  - `cuda_native_available=false`;
  - `cuda_accumulator_used=false`;
  - `tile_count=12`;
  - max absolute difference versus CPU baseline: `0.0`;
  - `dq_mask_produced=false`.
- Fake native CUDA:
  - `engine=cuda_tile_streaming_mean`;
  - native calls: `60`;
  - `cuda_native_available=true`;
  - `cuda_accumulator_used=true`;
  - `tile_count=20`;
  - max absolute difference versus CPU baseline: `6.103515625e-05`;
  - DQ provenance engine: `cuda_tile_streaming_mean`.
- Actual native CUDA:
  - `engine=cuda_tile_streaming_mean`;
  - `cuda_native_available=true`;
  - `cuda_accumulator_used=true`;
  - `tile_count=9`;
  - max absolute difference versus CPU baseline: `6.103515625e-05`;
  - DQ provenance engine: `cuda_tile_streaming_mean`.

## Real 200-Light Status

Not rerun for this gate. Gate709 corrects helper metadata and contract surfaces
for public GPU master-frame helpers. It does not touch resident CUDA calibration,
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

- The public GPU master-frame helper still does not emit DQ masks. Its
  provenance now says this explicitly.
- Full master-frame DQ remains owned by the CPU/tile StackEngine sink path and
  the resident master DQ sidecar path.
- This is a helper metadata/contract fix, not a resident CUDA performance
  optimization.

## Next Step

Continue with a substantive mainline gate: either add DQ-mask emission to the
GPU helper where useful, reduce actual resident read/H2D/calibration overlap
cost, or batch resident registration/warp orchestration under the Phase 2
mainline A/B guard.

## Clean-Room Compliance

Compliant. This gate used GLASS-owned GPU helper code, GLASS CUDA wrapper
behavior, CPU/GPU parity tests, and GLASS-generated synthetic fixtures only. No
external or proprietary implementation source was inspected, copied,
summarized, or reworked. Original image directories remained read-only.
