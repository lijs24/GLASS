# S2-Gate 451 Status: Resident Source-DQ Cache Runtime Route

## Gate

S2-Gate 451

## Gate400-413 Core-Goal Value Summary

- Gate400-403 created reusable acceptance/benchmark contract profiles for the
  resident CUDA DQ route. Real value: they made 200-light minima, DQ/map
  evidence, speedup thresholds, and source-DQ requirements machine-checkable.
  They did not change runtime execution, CUDA kernels, registration, or image
  math.
- Gate404-407 carried that profile through runtime-sweep planning,
  Phase2-status, release-promotion, and default-promotion artifacts. Real
  value: they reduced the chance that a candidate loses required DQ benchmark
  evidence during handoff. They did not run new benchmarks or improve speed.
- Gate408-413 propagated the same evidence through Windows release matrix,
  publish-preflight, Phase2 publication-audit, and default-promotion layers.
  Real value: they closed publication-readiness bypasses. These gates were
  report/contract/promotion scoped and did not advance StackEngine defaults,
  DQ pixel semantics, 200-light runtime, or resident CUDA performance.
- Decision after this gate: stop extending release/default-promotion/report-only
  gates unless a missing evidence link directly blocks StackEngine defaults,
  DQ/mask runtime contracts, 200-light regression, resident CUDA optimization,
  or numerical agreement validation.

## Completed

- Added `glass run --resident-source-dq-cache {off,generate-calibration}`.
- Kept the route default off so the existing 200-light resident fast path is
  unchanged until a dedicated benchmark proves the overhead.
- When `generate-calibration` is selected, resident CUDA `run` first executes
  GLASS CPU/tile calibration with the active calibration policy, generating
  `calibration_artifacts.json` and DQ sidecars.
- Added `resident_source_dq_cache_route.json` with route status, calibrated
  light count, DQ sidecar count, missing sidecar count, cosmetic frame count,
  and DQ summary totals.
- Added top-level `resident_source_dq_cache` timing metadata and a separate
  `resident_source_dq_cache_calibration` timing stage.
- Attached the route audit artifact to `run_state.json`.
- Added a focused CUDA CLI regression proving a single `glass run` command can
  generate DQ sidecars and have resident CUDA consume them.
- Updated Phase 2 gate documentation and the algorithm source ledger.

## Commands Run

- `.venv\Scripts\python.exe -m ruff check src\glass\cli.py tests\test_resident_cuda_run.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py -k "source_dq_cache_route or two_phase_cosmetic"`
- Synthetic validation script generating:
  `runs/checkpoints/s2_gate_451_perf/resident_source_dq_cache_route_two_phase.json`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_451_cuda_doctor.json --allow-cpu-only`
- `.venv\Scripts\python.exe -m glass.cli run --help | Select-String -Pattern "resident-source-dq-cache"`

## Test Result

- Ruff focused check: passed.
- Focused resident CUDA tests: `2 passed, 59 deselected in 0.93 s`.
- Full pytest: `1072 passed in 40.66 s`.
- CLI help exposes `--resident-source-dq-cache {off,generate-calibration}`.

## Synthetic Performance And Result Validation

- Dataset: 16 light, 3 bias, 3 dark, 3 flat, shape `64x64`.
- Injected finite hot pixels: 4 samples across 4 light frames.
- Route: `--backend cuda --memory-mode resident --resident-source-dq-cache generate-calibration`.
- Wall elapsed: `0.915656 s`.
- Timing stages:
  - `resident_source_dq_cache_calibration`: `0.681858 s`;
  - `resident_calibration_integration`: `0.181601 s`.
- Route audit:
  - calibrated lights: `16`;
  - DQ sidecars: `16`;
  - missing DQ sidecars: `0`;
  - DQ totals: `hot_pixel=4`, `cosmetic_corrected=4`, `valid=65532`.
- Resident source-DQ summary:
  - applied invalid samples: `4`;
  - input invalid samples before rejection: `4`;
  - sidecar source: `calibration_artifacts`.
- Result agreement against expected valid-sample semantics:
  - `master_max_abs=0.0`;
  - `weight_max_abs=0.0`;
  - hot-pixel master values: `100.0`;
  - hot-pixel weights: `15.0`.

## CUDA

- CUDA wrapper importable: yes.
- CUDA native extension loaded: yes.
- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor artifact: `runs/checkpoints/s2_gate_451_cuda_doctor.json`.

## Known Limitations

- The new DQ-cache route is default-off and opt-in only.
- The pre-cache stage currently uses CPU/tile calibration; it is correct and
  auditable but not the final resident-GPU cosmetic/DQ implementation.
- This gate used a synthetic performance/result validation, not the real
  200-light dataset.
- `glass audit` has not yet been given the same one-command DQ-cache option.
- No CUDA kernels, registration fitting, rejection math, or resident default
  fast path were changed.

## Next Substantive Gate

S2-Gate452 should run a real 200-light regression around the current resident
default path and the new opt-in DQ-cache route:

- verify the default resident fast path still matches the Phase 1 baseline
  timing and numerical envelope;
- run a measured opt-in DQ-cache route on the same or a documented
  representative 200-light subset if full 200-light cosmetic pre-cache time is
  too expensive;
- report per-stage timing, source-DQ counts, map outputs, active frames, and
  image agreement;
- decide whether the next optimization target is CPU/tile DQ pre-cache
  overhead, GPU-resident cosmetic/DQ generation, or registration/warp resident
  orchestration.

## Clean-Room Compliance

- This gate used only GLASS-owned source, tests, generated FITS fixtures, and
  GLASS-generated JSON/FITS artifacts.
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, modified,
  or used.
- No user image input directory was modified.
