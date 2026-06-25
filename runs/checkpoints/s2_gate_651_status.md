# S2-Gate 651 Status: Component Ledger Mainline Gate

## Gate

- Gate: S2-Gate 651.
- Status: passed.
- Date: 2026-06-25.
- Scope: promote the resident component-stage ledger into the Phase 2 mainline acceptance gate.

## Completed Content

- `glass phase2-mainline-audit` now treats `resident_stage_ledger.json` as a required resident core artifact.
- The audit recomputes the resident stage ledger and adds the hard check:
  `resident_stage_ledger_component_contract`.
- The new check requires:
  - `resident_calibration=complete`;
  - `resident_registration=complete`;
  - `resident_local_normalization=complete`;
  - `resident_integration=complete`;
  - `missing_artifact_count=0`;
  - `can_noop_resume=true`;
  - no legacy/auxiliary rows such as `resident_light_calibration` or `resident_calibration_contract`.
- `resident_mainline_framework` writes a current stage ledger before invoking the mainline audit, then the outer resident postcondition path still writes the final ledger.
- `resident_mainline_framework` keeps its `source_dq_positive` relaxation for synthetic/source-DQ validation, so non-default source-DQ fixtures are not blocked by the default resident route or default component-ledger contract.
- Updated:
  - `docs/phase2_algorithm_hardening.md`;
  - `docs/validation.md`;
  - `docs/algorithm_sources.md`.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\report\phase2_mainline_audit.py tests\test_phase2_mainline_audit.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_phase2_mainline_audit.py tests\test_resident_stage_ledger.py
.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\candidate_from_calibration_boundary --acceptance-audit C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\gate649_acceptance_audit.json --compare-json C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\gate649_vs_wbpp_compare.json --out C:\glass_runs\phase2_s2_gate651_stage_ledger_mainline_gate\runs_20260625_230000\gate651_phase2_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate651_stage_ledger_mainline_gate\runs_20260625_230000\gate651_phase2_mainline_audit.md --min-lights 200 --min-active-frames 190 --max-masked-frames 10 --min-speedup 50 --min-coverage-fraction 0.97 --max-rms-diff 0.01 --max-abs-diff-p99 0.003 --require-acceptance --require-compare --fail-on-not-green
.\.venv\Scripts\python.exe -m ruff check src\glass\cli.py src\glass\engine\resident_mainline_framework.py tests\test_resident_mainline_framework.py src\glass\report\phase2_mainline_audit.py tests\test_phase2_mainline_audit.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_mainline_framework.py tests\test_phase2_mainline_audit.py tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_generates_source_dq_cache_route
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused phase2-mainline/resident-stage-ledger tests: `8 passed in 0.35 s`.
- Focused resident-mainline/source-DQ regression set: `15 passed in 1.12 s`.
- Ruff over touched files: passed.
- Full pytest: `1364 passed in 60.52 s`.

## Real 200-Light Validation

- Full source run:
  `C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\candidate_from_calibration_boundary`.
- Gate651 mainline audit:
  `C:\glass_runs\phase2_s2_gate651_stage_ledger_mainline_gate\runs_20260625_230000\gate651_phase2_mainline_audit.json`.
- Status: passed.
- Failed checks: none.
- New hard check: `resident_stage_ledger_component_contract=passed`.
- Component ledger evidence:
  - `resident_calibration=complete`;
  - `resident_registration=complete`;
  - `resident_local_normalization=complete`;
  - `resident_integration=complete`;
  - `complete_stage_count=18`;
  - `expected_artifact_count=27`;
  - `missing_artifact_count=0`;
  - `can_noop_resume=true`.
- Mainline metrics:
  - input lights: `200`;
  - active frames: `193`;
  - masked frames: `7`;
  - speedup versus black-box reference: `95.12553269140832x`;
  - compare RMS: `0.005624135079195954`;
  - compare p99 absolute difference: `0.0021429822302888963`;
  - coverage fraction: `0.9749333995120938`.

## CUDA

- CUDA remains optional for installation and tests.
- The real reference run used CUDA on:
  `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`, compute capability `12.0`, VRAM `97886 MiB`, driver `596.21`.

## Artifacts

- `C:\glass_runs\phase2_s2_gate651_stage_ledger_mainline_gate\runs_20260625_230000\gate651_phase2_mainline_audit.json`
- `C:\glass_runs\phase2_s2_gate651_stage_ledger_mainline_gate\runs_20260625_230000\gate651_phase2_mainline_audit.md`

## Known Limitations

- This gate enforces component-stage evidence; it does not change image math, CUDA kernels, or runtime scheduling.
- It does not persist calibrated light pixels or continue inside an interrupted VRAM-only stage.
- It prepares the acceptance surface for a future split of `resident_calibration_integration`.

## Next Step

Use the now-enforced component ledger to split the monolithic resident stage into deeper checkpointable boundaries, or return directly to the measured hot components: `light_read_upload_calibrate` and `resident_integration`.

## Clean-Room Compliance

- This gate uses GLASS-owned audit and stage-ledger logic.
- Validation uses GLASS-generated artifacts and user-generated black-box reference metadata only.
- No external/proprietary implementation source was read, copied, summarized, or reworked.
- Input image directories were treated as read-only.
