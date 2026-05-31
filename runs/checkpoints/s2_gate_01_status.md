# S2-Gate 1 Status: Core Contracts

Date: 2026-05-31

## Gate

S2-Gate 1: minimal core contracts and adapters.

## Completed Content

- Added `src/glass/engine/contracts.py` with:
  - `TileWindow`
  - `DQFlag`
  - `DQMask`
  - `ImageSource`
  - `FrameTransform`
  - `TransformResult`
  - `IdentityTransform`
  - `CombinePolicy`
  - `RejectionPolicy`
  - `OutputMapPolicy`
  - `StackRequest`
- Added `src/glass/io/image_source.py` with `FitsImageSource`, a FITS-backed
  adapter for the new `ImageSource` contract.
- Exported the contracts from `glass.engine`.
- Exported `FitsImageSource` from `glass.io`.
- Added `tests/test_phase2_contracts.py` for the new schema and adapter
  behavior.
- Updated `docs/algorithm_sources.md` with the implementation and test files
  for the Phase 2 core contracts and DQ bitfield.

## Compatibility Notes

- The existing pipeline was not rewired in this gate.
- Existing FITS IO, pipeline, resident CUDA, and report paths remain unchanged.
- The old path is preserved while S2-Gate 2 adds the CPU/tiled StackEngine.

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests\test_phase2_contracts.py`
- `.venv\Scripts\python.exe -m pytest -q`
- CUDA probe through `.venv\Scripts\python.exe` importing `glass_cuda`.
- `git diff --stat`
- `git status --short`

## Test Result

- Focused contract tests: `10 passed in 0.05s`
- Full test suite: `197 passed in 10.74s`

## CUDA Availability

CUDA is available to GLASS in the current environment.

- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- Driver version: `596.21`
- Total VRAM: `97886 MiB`
- Multiprocessors: `188`
- Native backend loaded: yes

## Known Limitations

- `StackEngine` execution is not implemented in this gate.
- `DQMask` is a CPU-side contract and diagnostic structure in this gate; CUDA DQ
  propagation is a later gate.
- `FitsImageSource` is a safe contract adapter around existing FITS tile IO. It
  is not yet used as the default pipeline source.
- XISF `ImageSource` support remains future work.

## Next Step

Proceed to S2-Gate 2: implement the CPU/tiled StackEngine for mean, median,
weighted mean, coverage, weight maps, rejection maps, and basic rejection
policies with full-frame vs tiled equivalence tests.

## Clean-Room / Independence Status

This gate added project-owned interfaces and tests derived from the Phase 2
execution plan and existing GLASS IO needs. No proprietary PixInsight/WBPP/PJSR
source code was read, copied, summarized, or modified.
