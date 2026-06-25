# S2-Gate 652 Status: Resident Component Timing Surface

## Gate

- Gate: S2-Gate 652.
- Status: passed.
- Date: 2026-06-25.
- Scope: make resident hot-path component timings first-class mainline evidence.

## Completed Content

- Added `resident_component_timing.json` generation for resident `glass run`
  and `glass audit`.
- Added `resident_component_stages` and
  `resident_component_timing_summary` materialization in `run_timing.json`.
- Added `src/glass/engine/resident_component_timing.py` to extract measured
  component timings from `resident_artifacts.json` without inventing values.
- `glass phase2-mainline-audit` now treats
  `resident_component_timing.json` as a required resident core artifact.
- The `timing_components_available` mainline check now requires:
  - `resident_component_timing.json` exists;
  - the artifact reports `passed=true`;
  - no required component is missing;
  - measured timings exist for `light_read_upload_calibrate`,
    `resident_registration_warp`, and `resident_integration`.
- Updated minimal resident mainline fixtures so downstream postcondition tests
  exercise the same component timing contract.
- Updated:
  - `docs/phase2_algorithm_hardening.md`;
  - `docs/validation.md`;
  - `docs/algorithm_sources.md`.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_component_timing.py src\glass\cli.py src\glass\report\phase2_mainline_audit.py tests\test_resident_component_timing.py tests\test_phase2_mainline_audit.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_component_timing.py tests\test_phase2_mainline_audit.py tests\test_resident_stage_ledger.py
.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate652_component_timing_surface\runs_20260626_000000\candidate_component_timing_replay --acceptance-audit C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\gate649_acceptance_audit.json --compare-json C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\gate649_vs_wbpp_compare.json --out C:\glass_runs\phase2_s2_gate652_component_timing_surface\runs_20260626_000000\gate652_phase2_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate652_component_timing_surface\runs_20260626_000000\gate652_phase2_mainline_audit.md --min-speedup 50 --min-coverage-fraction 0.97 --max-rms-diff 0.006 --max-abs-diff-p99 0.003 --require-acceptance --require-compare --fail-on-not-green
.\.venv\Scripts\python.exe -m ruff check tests\test_resident_mainline_framework.py tests\test_phase2_mainline_audit.py tests\test_resident_component_timing.py src\glass\engine\resident_component_timing.py src\glass\report\phase2_mainline_audit.py src\glass\cli.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_mainline_framework.py tests\test_resident_component_timing.py tests\test_phase2_mainline_audit.py tests\test_resident_stage_ledger.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor
```

## Test Results

- Initial focused resident component/mainline/stage-ledger tests:
  `13 passed in 0.55 s`.
- After propagating the new contract into resident mainline fixtures:
  `23 passed in 0.83 s`.
- Ruff over touched files: passed.
- Full pytest: `1369 passed in 61.48 s`.

## Real 200-Light Validation

- Replay root:
  `C:\glass_runs\phase2_s2_gate652_component_timing_surface\runs_20260626_000000\candidate_component_timing_replay`.
- Source full run:
  `C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\candidate_from_calibration_boundary`.
- Gate652 mainline audit:
  `C:\glass_runs\phase2_s2_gate652_component_timing_surface\runs_20260626_000000\gate652_phase2_mainline_audit.json`.
- Status: passed.
- Failed checks: none.
- Input lights: `200`.
- Active frames: `193`.
- Masked frames: `7`.
- Speedup versus black-box reference: `95.12553269140832x`.
- Compare RMS: `0.005624135079195954`.
- Compare p99 absolute difference: `0.0021429822302888963`.
- Coverage fraction: `0.9749333995120938`.

## Component Timing Evidence

- `resident_component_timing.json`: passed.
- Required missing components: none.
- Largest resident component:
  `resident_light_read_upload_calibrate=3.5132379999849945 s`.
- Measured component split:
  - `light_read_upload_calibrate`: `3.5132379999849945 s`;
  - `resident_integration`: `3.2337921999860555 s`;
  - `resident_local_normalization`: `0.3582464000210166 s`;
  - `resident_registration_warp`: `0.26844110037200153 s`;
  - `output_write`: `0.23136649990919977 s`.
- Parent stage:
  `resident_calibration_integration=9.839130699983798 s`.

## CUDA

- CUDA optional install path remains intact.
- CUDA wrapper importable: true.
- CUDA native extension loaded: true.
- CUDA available: true.
- GPU 0:
  `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`,
  compute capability `12.0`, VRAM `97886 MiB`, driver `596.21`.

## Artifacts

- `C:\glass_runs\phase2_s2_gate652_component_timing_surface\runs_20260626_000000\candidate_component_timing_replay\resident_component_timing.json`
- `C:\glass_runs\phase2_s2_gate652_component_timing_surface\runs_20260626_000000\candidate_component_timing_replay\run_timing.json`
- `C:\glass_runs\phase2_s2_gate652_component_timing_surface\runs_20260626_000000\gate652_phase2_mainline_audit.json`
- `C:\glass_runs\phase2_s2_gate652_component_timing_surface\runs_20260626_000000\gate652_phase2_mainline_audit.md`

## Known Limitations

- This gate exposes and enforces component timings; it does not change CUDA
  kernels, pixel math, registration, warp, LN, rejection, DQ semantics, or
  output pixels.
- The replay copied JSON/MD/TXT evidence only. It did not rerun the full
  resident CUDA stack and did not duplicate large FITS output maps.
- The parent resident stage still remains monolithic for execution/resume
  purposes. Deeper checkpointable resident boundaries are still future work.

## Next Step

Use the new timing surface for a substantive hot-path gate. The strongest next
targets are:

- reduce `light_read_upload_calibrate` with deeper read/upload/calibration
  overlap and pinned/native queue accounting;
- reduce `resident_integration` with the next resident winsorized reducer
  optimization.

## Clean-Room Compliance

- This gate uses GLASS-owned timing materialization and audit logic.
- Validation uses GLASS-generated artifacts and user-generated black-box
  reference timing/output metadata only.
- No external/proprietary implementation source was read, copied, summarized,
  or reworked.
- Input image directories were treated as read-only.
