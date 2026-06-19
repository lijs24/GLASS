# S2-Gate 453 Status: Resident Source-DQ Strategy Artifact

## Gate

- Gate: S2-Gate 453
- Scope: Resident source-DQ cache/in-memory strategy for the Phase 2 DQ/mask
  pipeline.
- Status: passed
- Date: 2026-06-20 local

## Completed Work

- Added `src/glass/engine/resident_source_dq_strategy.py`.
- Resident CUDA `glass run` now writes `resident_source_dq_strategy.json`.
- `run_state.json` records a `resident_source_dq_strategy` pipeline artifact.
- Gate452 `resident_source_dq_cache_preflight.json` remains compatible but now
  includes:
  - `recommended_route`;
  - nested `disk_cache`;
  - nested `resident_mask_streaming`.
- Oversized on-disk calibrated+DQ cache routes now recommend
  `resident_in_vram_mask_streaming` instead of silently encouraging cache
  materialization.
- Synthetic tests cover:
  - small cache allowed;
  - oversized cache recommends resident in-memory mask streaming;
  - unknown light shapes block cache planning;
  - real resident CUDA synthetic run writes and registers the strategy artifact.
- Updated:
  - `docs/phase2_algorithm_hardening.md`;
  - `docs/algorithm_sources.md`.

## Real 200-Light Strategy Artifact

- Artifact: `runs/checkpoints/s2_gate_453_real_source_dq_strategy.json`
- Input: `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`
- Pixel read: no; metadata/plan-only.
- Ready light frames: 200.
- Calibrated+DQ cache estimate:
  - payload bytes: 73,981,440,000
  - output bytes with safety multiplier: 77,680,512,000
  - current 75% disk budget: 29,628,515,328
  - result: blocked with `estimated_cache_exceeds_disk_budget`
- Resident invalid-mask streaming estimate:
  - batch frames: 8
  - estimated batch bytes: 493,209,600
  - all-frame mask bytes if materialized: 12,330,240,000
  - memory budget used for strategy check: 96 GiB
  - result: fits memory budget
- Recommended route: `resident_in_vram_mask_streaming`

## Commands Run

- `.venv\Scripts\python.exe -m ruff check src\glass\cli.py src\glass\engine\resident_source_dq_strategy.py tests\test_resident_source_dq_strategy.py tests\test_resident_cuda_run.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_source_dq_strategy.py tests\test_resident_cuda_run.py -k "source_dq_strategy or source_dq_cache_preflight or source_dq_cache_route"`
- `.venv\Scripts\python.exe -m pytest -q`
- A metadata-only Python probe generated
  `runs/checkpoints/s2_gate_453_real_source_dq_strategy.json`.

## Test Results

- Focused ruff: passed.
- Focused pytest: 6 passed, 60 deselected.
- Full pytest: 1078 passed in 40.84 s.

## CUDA Status

- CUDA remains optional.
- This gate did not change CUDA kernels or numerical integration behavior.
- Synthetic resident CUDA test path ran on the local CUDA backend during the
  focused pytest selection.
- Last recorded local device from Gate452:
  NVIDIA RTX PRO 6000 Blackwell Workstation Edition, compute capability 12.0,
  97,886 MiB VRAM, driver 596.21.

## Known Limitations

- This gate adds strategy and runtime artifacting; it does not yet generate
  cosmetic/source-DQ masks entirely on GPU.
- The strategy estimates resident invalid-mask memory as uint8 masks. It does
  not yet reserve or schedule a persistent all-frame DQ tensor in VRAM.
- `glass audit` does not yet emit `resident_source_dq_strategy.json`; this gate
  covers `glass run`.
- The 200-light default quality-gate policy drift identified in Gate452 remains
  unresolved.

## Next Gate

- S2-Gate454 should implement a true resident source-DQ/mask execution step:
  - keep DQ masks in resident memory or stream them in pinned batches;
  - avoid calibrated+DQ disk cache for the 200-light case;
  - preserve CPU StackEngine valid-sample semantics;
  - run synthetic CPU-vs-resident DQ parity and a real 200-light acceptance or
    metadata-plus-runtime regression without exceeding the Gate452
    `30.900435 s` contract-parity baseline without explanation.

## Clean-Room Compliance

- Compliant. This gate used only GLASS source, GLASS synthetic data/tests, and
  user-owned processing-plan metadata.
- No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or
  modified.
- Original image directories remained read-only.
