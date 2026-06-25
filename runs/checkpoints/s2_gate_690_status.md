# S2-Gate 690 Status: Phase 2 Mainline A/B Validation Harness

## Gate

S2-Gate 690.

## Completed Content

- Added a hard mainline validation command: `glass phase2-mainline-ab`.
- The command compares a baseline resident CUDA run and a candidate resident
  CUDA run, then reports/fails on:
  - missing baseline or candidate run directories;
  - missing or failed required candidate contracts;
  - elapsed ratio above budget;
  - active frame count below budget;
  - missing resident integration output classes;
  - tracked FITS output hash or size drift.
- The tracked resident integration output classes are:
  - `resident_master_*.fits`;
  - `resident_weight_map_*.fits`;
  - `resident_coverage_map_*.fits`;
  - `resident_low_rejection_map_*.fits`;
  - `resident_high_rejection_map_*.fits`;
  - `resident_dq_map_*.fits`.
- Added focused tests for pass, hash-drift failure, and CLI failure exit code.
- Updated Phase 2 and validation documentation with the Gate690 real 200-light
  result.
- Fixed resident CUDA completion-queue frame-weight alignment. Batch
  calibration now writes `frame_weight_values` by stack frame index instead of
  completion order, so integration weights and frame-mask contracts use the
  same coordinate system.

## Real 200-Light Validation

- Baseline run:
  `C:\glass_runs\phase2_s2_gate689_identity_warp_bypass\runs_20260627_013000\identity_bypass_default`.
- Candidate run:
  `C:\glass_runs\phase2_s2_gate690_mainline_ab\runs_20260627_023000\mainline_weight_aligned`.
- Phase 2 mainline audit:
  `C:\glass_runs\phase2_s2_gate690_mainline_ab\gate690_weight_aligned_mainline_audit.json`.
- Resident regression gate:
  `C:\glass_runs\phase2_s2_gate690_mainline_ab\gate690_weight_aligned_regression_gate.json`.
- New A/B gate:
  `C:\glass_runs\phase2_s2_gate690_mainline_ab\gate690_weight_aligned_phase2_mainline_ab.json`.
- New A/B Markdown:
  `C:\glass_runs\phase2_s2_gate690_mainline_ab\gate690_weight_aligned_phase2_mainline_ab.md`.

Results:

- Mainline audit: passed, failed checks `[]`.
- Regression gate versus Gate689: passed, failed checks `[]`.
- Phase 2 mainline A/B: passed, failed checks `[]`.
- Candidate active frames: `193`.
- Candidate tracked map count: `6`.
- Missing required map patterns: `0`.
- Hash mismatch count: `0`.
- Hash missing-map count: `0`.
- Baseline-to-candidate elapsed ratio: `0.9895780022628549`.
- Candidate total elapsed: `12.393503400264308 s`.

Resident component timing:

- `resident_light_read_upload_calibrate`: `3.44842360005714 s`.
- `resident_registration_warp`: `0.26703780062962323 s`.
- `resident_local_normalization`: `0.3525654999539256 s`.
- `resident_integration`: `3.2566704000346363 s`.
- `resident_output_write`: `0.28603319998364896 s`.

## Commands Run

```powershell
.venv\Scripts\python.exe -m pytest -q tests\test_phase2_mainline_ab.py
.venv\Scripts\python.exe -m pytest -q tests\test_phase2_mainline_ab.py tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_active_registered_inline_cosmetic_cuda_skips_excluded_frame
.venv\Scripts\ruff.exe check src\glass\report\phase2_mainline_ab.py src\glass\cli.py tests\test_phase2_mainline_ab.py
.venv\Scripts\ruff.exe check src\glass\report\phase2_mainline_ab.py src\glass\engine\resident_cuda.py src\glass\cli.py tests\test_phase2_mainline_ab.py
.venv\Scripts\glass.exe phase2-mainline-ab --baseline-run C:\glass_runs\phase2_s2_gate689_identity_warp_bypass\runs_20260627_013000\identity_bypass_default --candidate-run C:\glass_runs\phase2_s2_gate690_mainline_ab\runs_20260627_023000\mainline_weight_aligned --out C:\glass_runs\phase2_s2_gate690_mainline_ab\gate690_weight_aligned_phase2_mainline_ab.json --markdown C:\glass_runs\phase2_s2_gate690_mainline_ab\gate690_weight_aligned_phase2_mainline_ab.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --fail-on-failed
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -c "import glass_cuda, json; print(json.dumps({'cuda_available': glass_cuda.cuda_available(), 'devices': glass_cuda.list_devices()}, ensure_ascii=False, default=str))"
```

Previously generated Gate690 real-run evidence also used:

```powershell
.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate690_mainline_ab\runs_20260627_023000\mainline_weight_aligned --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final
.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate690_mainline_ab\runs_20260627_023000\mainline_weight_aligned --out C:\glass_runs\phase2_s2_gate690_mainline_ab\gate690_weight_aligned_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate690_mainline_ab\gate690_weight_aligned_mainline_audit.md --fail-on-not-green
.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate689_identity_warp_bypass\runs_20260627_013000\identity_bypass_default --candidate-run C:\glass_runs\phase2_s2_gate690_mainline_ab\runs_20260627_023000\mainline_weight_aligned --out C:\glass_runs\phase2_s2_gate690_mainline_ab\gate690_weight_aligned_regression_gate.json --markdown C:\glass_runs\phase2_s2_gate690_mainline_ab\gate690_weight_aligned_regression_gate.md --fail-on-failure
```

## Test Results

- Focused A/B tests: `3 passed in 0.25 s`.
- Ruff: passed.
- Full pytest: `1434 passed in 66.48 s`.

## CUDA Status

- CUDA available: yes.
- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver version: `596.21`.
- Native backend: available.

## Known Limitations

- Gate690 is a validation harness and evidence gate. It does not change
  calibration, registration, warp, local normalization, rejection, or
  integration math.
- The current largest measured components remain light read/upload/calibrate
  and resident integration.
- Hash stability is required by default for the tracked resident FITS maps, but
  future numeric experiments can explicitly use `--allow-hash-drift` and must
  document why drift is expected.

## Next Step

Return to a substantive Phase 2 mainline gate:

- either reduce `resident_light_read_upload_calibrate` through deeper native
  read/H2D/calibration overlap;
- or redesign resident integration around a deterministic cooperative or
  segmented CUDA reducer while preserving the Gate690 A/B contract.

## Clean-Room Compliance

- No external proprietary implementation source was read, copied, summarized,
  or reworked.
- The real data directories were used read-only.
- The new code is a GLASS-owned validation harness over GLASS-generated
  artifacts and user-owned benchmark outputs.
- CUDA remains optional; CPU-only tests still pass.
