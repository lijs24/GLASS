# S2-Gate 639 Status

- Gate: S2-Gate 639
- Title: Phase 2 Mainline Audit
- Status: green
- Date: 2026-06-25

## Completed

- Added `glass phase2-mainline-audit`.
- Added `src/glass/report/phase2_mainline_audit.py`.
- Added focused unit/CLI tests in `tests/test_phase2_mainline_audit.py`.
- Updated Phase 2 development, validation, and algorithm-source docs.
- Preserved default resident CUDA image math and runtime behavior.

## Commands

- `ruff check src\glass\report\phase2_mainline_audit.py src\glass\cli.py tests\test_phase2_mainline_audit.py`
- `python -m pytest -q tests\test_phase2_mainline_audit.py`
- `glass phase2-mainline-audit ...` against Gate638 artifacts
- `glass run ...` on the real M38 200-light resident CUDA dataset
- `glass resident-regression-gate ...` against Gate638
- `glass compare ...` against the black-box reference master
- `glass acceptance-audit ...`
- `glass phase2-mainline-audit ... --require-acceptance --require-compare --fail-on-not-green`
- `python -m pytest -q`
- `glass doctor --json C:\glass_runs\phase2_s2_gate639_mainline_audit\gate639_doctor.json --allow-cpu-only`

## Test Results

- Ruff: passed.
- Focused mainline/CLI smoke: `4 passed, 80 deselected`.
- Full pytest: `1340 passed in 56.54 s`.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Real 200-Light Validation

- Run:
  `C:\glass_runs\phase2_s2_gate639_mainline_audit\runs_20260625_161056\candidate_mainline_audit`
- Evidence root:
  `C:\glass_runs\phase2_s2_gate639_mainline_audit\runs_20260625_161056`
- GLASS elapsed: `12.191199900000356 s`.
- WBPP black-box elapsed: `1092.541 s`.
- Acceptance speedup: `89.61718362111084x`.
- Planned lights: `200`.
- Active / masked frames: `193 / 7`.
- Regression versus Gate638: passed, elapsed ratio `0.9706228158749438`.
- Compare at coverage >= `190`:
  - shape match: true;
  - RMS: `0.0056241382952344435`;
  - p99 absolute difference: `0.002143551869085057`;
  - coverage fraction: `0.9749333995120938`;
  - compared pixels: `60105814`.
- Mainline audit:
  `C:\glass_runs\phase2_s2_gate639_mainline_audit\runs_20260625_161056\gate639_mainline_audit.json`
- Mainline audit status: passed, no failed checks.

## Known Limitations

- This gate adds a mainline acceptance/audit surface; it does not change
  calibration, registration, warp, local normalization, rejection, integration
  formulas, or CUDA kernels.
- The current real benchmark still has no nonzero sidecar/inline source-DQ
  invalid samples, so broader source-DQ semantics need synthetic or targeted
  real-data coverage.
- The largest measured stage remains resident calibration/integration.

## Next Step

- Return to execution-path work under the new mainline audit guard:
  resident calibration/integration throughput first, then reference
  scout/health resident reuse, then nonzero source-DQ coverage.

## Clean-Room

- Compliant. This gate uses GLASS-owned artifact schemas, GLASS default-route
  semantics, GLASS tests, and user-owned benchmark/reference outputs only.
- No external/proprietary implementation source was inspected, copied,
  summarized, or reworked.
- Input image directories were treated as read-only.
