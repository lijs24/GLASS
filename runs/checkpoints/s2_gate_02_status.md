# S2-Gate 2 Status: CPU/Tiled StackEngine

Date: 2026-05-31

## Gate

S2-Gate 2: CPU/tiled StackEngine baseline.

## Completed Content

- Added `src/glass/engine/stack_engine.py` with:
  - `CPUStackEngine`
  - `StackEngineResult`
  - tiled `StackRequest` execution over `ImageSource` inputs
  - mean, median, sum, and weighted mean combination
  - coverage map
  - weight map
  - variance map
  - low/high rejection maps
  - optional output DQ mask
  - first-pass rejection policies: `none`, `minmax`, `percentile`, `sigma`,
    `mad`, `median_sigma`, and `winsorized_sigma`
- Exported `CPUStackEngine` and `StackEngineResult` from `glass.engine`.
- Added `tests/test_stack_engine.py` covering:
  - full-frame vs tiled mean equivalence
  - weighted mean with DQ input masks
  - median combination
  - sigma rejection
  - winsorized sigma rejection
  - min/max rejection
  - shape mismatch diagnostics
- Updated `docs/algorithm_sources.md` for StackEngine combine and rejection
  policies.

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests\test_stack_engine.py`
- `.venv\Scripts\python.exe -m pytest -q`
- CUDA probe through `.venv\Scripts\python.exe` importing `glass_cuda`.
- `git diff --stat`
- `git status --short`

## Test Result

- Focused StackEngine tests: `7 passed in 0.06s`
- Full test suite: `204 passed in 11.48s`

## CUDA Availability

CUDA is available to GLASS in the current environment.

- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- Driver version: `596.21`
- Total VRAM: `97886 MiB`
- Multiprocessors: `188`
- Native backend loaded: yes

## Known Limitations

- This is the CPU/tiled reference StackEngine. CUDA parity and resident-memory
  execution are later gates.
- Master frame generation and light integration are not yet rewired to use
  StackEngine by default; that is S2-Gate 3.
- Rejection defaults are project-defined first-pass behavior and will need more
  scientific tuning against synthetic and real data.
- The DQ output mask currently records output-level no-data/rejection summaries;
  full stage-by-stage DQ propagation is S2-Gate 4.

## Next Step

Proceed to S2-Gate 3: wire StackEngine into master frame creation and light
integration while keeping the existing path as fallback, then run regression and
representative benchmark checks.

## Clean-Room / Independence Status

StackEngine combine and rejection behavior was implemented from standard
statistical definitions and project-owned interfaces. No proprietary
PixInsight/WBPP/PJSR source code was read, copied, summarized, or modified.
