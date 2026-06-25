# S2-Gate 640 Status

- Gate: S2-Gate 640
- Title: Reference Health CPU Scout Reuse
- Status: green
- Date: 2026-06-25

## Completed

- Reused CPU `resident_reference_scout.json` rows inside
  `build_resident_reference_health()` when the guarded CUDA-attempt scout has
  already fallen back to CPU.
- Preserved the previous measured CPU crosscheck fallback for CUDA or incomplete
  scout artifacts.
- Preserved calibrated and CUDA-calibrated reference-health crosschecks.
- Added `summary.cpu_crosscheck_reused` and `cpu_crosscheck.reuse` evidence to
  `resident_reference_health.json`.
- Updated Phase 2 mainline audit priorities so the remaining P2 target becomes
  calibrated-health resident reuse when CPU scout rows are already reused.
- Updated Phase 2 docs, validation, and algorithm-source log.

## Commands

- `ruff check src\glass\engine\resident_reference_health.py src\glass\report\phase2_mainline_audit.py tests\test_cli_smoke.py tests\test_phase2_mainline_audit.py`
- `python -m pytest -q tests\test_cli_smoke.py -k "resident_reference_health or reference_scout_auto or auto_cuda_attempt" tests\test_phase2_mainline_audit.py`
- `glass run ...` on the real M38 200-light resident CUDA dataset
- `glass resident-regression-gate ...` versus Gate639
- `glass compare ...` against the black-box reference master
- `glass acceptance-audit ...`
- `glass phase2-mainline-audit ... --require-acceptance --require-compare --fail-on-not-green`
- `python -m pytest -q`
- `glass doctor --json C:\glass_runs\phase2_s2_gate640_reference_health_reuse\gate640_doctor.json --allow-cpu-only`

## Test Results

- Ruff: passed.
- Focused reference-health/mainline tests: `10 passed, 74 deselected`.
- Full pytest: `1340 passed in 56.91 s`.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Real 200-Light Validation

- Run:
  `C:\glass_runs\phase2_s2_gate640_reference_health_reuse\runs_20260625_161859\candidate_reference_health_reuse`
- Evidence root:
  `C:\glass_runs\phase2_s2_gate640_reference_health_reuse\runs_20260625_161859`
- GLASS elapsed: `11.895640000118874 s`.
- WBPP black-box elapsed: `1092.541 s`.
- Acceptance speedup: `91.8438184064987x`.
- Planned lights: `200`.
- Active / masked frames: `193 / 7`.
- `resident_reference_health.json` reuse:
  - `cpu_crosscheck.reuse.used=true`;
  - reason `scout_cpu_frame_quality_reused`;
  - reused rows `64`.
- Stage timings:
  - reference scout: `0.7367958000395447 s`;
  - reference health: `1.11221730010584 s`;
  - resident calibration/integration: `9.585057299933396 s`.
- Regression versus Gate639: passed, elapsed ratio `0.9757562912341817`.
- Compare at coverage >= `190`:
  - shape match: true;
  - RMS: `0.0056241382952344435`;
  - p99 absolute difference: `0.002143551869085057`;
  - coverage fraction: `0.9749333995120938`;
  - compared pixels: `60105814`.
- Mainline audit:
  `C:\glass_runs\phase2_s2_gate640_reference_health_reuse\runs_20260625_161859\gate640_mainline_audit.json`
- Mainline audit status: passed, no failed checks.

## Known Limitations

- This gate removes duplicate raw CPU scout work only. It does not change
  calibration, registration, warp, local normalization, rejection, integration
  formulas, or CUDA kernels.
- Calibrated and CUDA-calibrated reference-health crosschecks still read bounded
  samples and remain a correctness overhead.
- The largest measured stage remains resident calibration/integration.

## Next Step

- Target resident calibration/integration execution under
  `phase2-mainline-audit`, or reduce calibrated reference-health overhead
  without weakening the CUDA-attempt safety gate.

## Clean-Room

- Compliant. This gate uses GLASS-owned scout/health artifact schemas, GLASS
  FITS/star metrics, GLASS tests, and user-owned benchmark/reference outputs.
- No external/proprietary implementation source was inspected, copied,
  summarized, or reworked.
- Input image directories were treated as read-only.
