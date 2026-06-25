# S2-Gate 650 Status: Resident Component Stage Ledger

## Gate

- Gate: S2-Gate 650.
- Status: passed.
- Date: 2026-06-25.
- Scope: fix resident component-stage ledger evidence so resume/checkpoint boundaries can trust `resident_calibration` state.

## Completed Content

- Canonicalized `resident_light_calibration` to `resident_calibration` in the resident stage ledger.
- Let known `run_state.artifacts` rows start defined resident stages in `resident_stage_ledger.json`.
- Preserved the overlap guard: a stray artifact file alone still does not start a resident stage.
- Suppressed auxiliary artifact stages such as `resident_calibration_contract` from becoming standalone zero-artifact ledger stages.
- Added CLI:
  `glass resident-stage-ledger --run RUN [--out OUT] [--fail-on-missing]`.
- Updated:
  - `docs/phase2_algorithm_hardening.md`;
  - `docs/validation.md`;
  - `docs/algorithm_sources.md`.

## Why This Gate Matters

The Gate649 real 200-light run exposed a concrete contract contradiction:

- `run_state.json` recorded `resident_light_calibration` and resident calibration artifacts.
- `resident_stage_ledger.json` showed `resident_calibration=not_started`.
- The same ledger also appended `resident_light_calibration` as a zero-artifact complete stage.

Gate650 makes the resident stage ledger align with the real component state, which is required before later gates can safely split `resident_calibration_integration` or resume from deeper resident checkpoints.

## Real 200-Light Artifact Replay

- Replay root:
  `C:\glass_runs\phase2_s2_gate650_component_stage_ledger\runs_20260625_220000\gate649_component_ledger_replay`.
- Source evidence:
  `C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\candidate_from_calibration_boundary`.
- No large FITS files were copied and no pipeline stage was rerun.

Old Gate649 ledger evidence:

- `resident_calibration=not_started`.
- `resident_light_calibration` present as a zero-artifact complete stage.
- `complete_stage_count=16`.
- `expected_artifact_count=24`.
- `missing_artifact_count=0`.
- `can_noop_resume=true`.

Gate650 ledger evidence:

- `resident_calibration=complete`.
- `resident_light_calibration` absent.
- `resident_calibration_contract` absent as a standalone stage.
- `complete_stage_count=18`.
- `expected_artifact_count=27`.
- `missing_artifact_count=0`.
- `can_noop_resume=true`.

## Commands Run

```powershell
.\.venv\Scripts\glass.exe resident-stage-ledger --run C:\glass_runs\phase2_s2_gate650_component_stage_ledger\runs_20260625_220000\gate649_component_ledger_replay --out C:\glass_runs\phase2_s2_gate650_component_stage_ledger\runs_20260625_220000\gate650_component_stage_ledger_cli.json --fail-on-missing
.\.venv\Scripts\glass.exe resume --run C:\glass_runs\phase2_s2_gate650_component_stage_ledger\runs_20260625_220000\gate649_component_ledger_replay
.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\candidate_from_calibration_boundary --acceptance-audit C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\gate649_acceptance_audit.json --compare-json C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\gate649_vs_wbpp_compare.json --out C:\glass_runs\phase2_s2_gate650_component_stage_ledger\runs_20260625_220000\gate650_phase2_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate650_component_stage_ledger\runs_20260625_220000\gate650_phase2_mainline_audit.md --min-lights 200 --min-active-frames 190 --max-masked-frames 10 --min-speedup 50 --min-coverage-fraction 0.97 --max-rms-diff 0.01 --max-abs-diff-p99 0.003 --require-acceptance --require-compare --fail-on-not-green
.\.venv\Scripts\glass.exe resident-stage-ledger --help
.\.venv\Scripts\python.exe -m ruff check src\glass\cli.py src\glass\engine\resident_stage_ledger.py tests\test_resident_stage_ledger.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_stage_ledger.py tests\test_resident_resume.py tests\test_resident_reentry_boundary.py
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- New CLI help: passed.
- Ruff over touched files: passed.
- Focused tests: `13 passed in 0.56 s`.
- Full pytest: `1363 passed in 60.69 s`.

## Resume And Mainline Results

- `glass resident-stage-ledger --fail-on-missing`: exit code `0`.
- `glass resume` on the replay bundle: `resume_action=noop_complete`; no pipeline stages repeated.
- Phase 2 mainline audit against the full Gate649 real run: passed.
- Mainline audit summary:
  - input lights: `200`;
  - active frames: `193`;
  - masked frames: `7`;
  - speedup versus black-box reference: `95.12553269140832x`;
  - compare RMS: `0.005624135079195954`;
  - compare p99 absolute difference: `0.0021429822302888963`;
  - coverage fraction: `0.9749333995120938`.

## CUDA

- CUDA remains optional for installation and tests.
- CUDA was available on this machine for the referenced Gate649 real run.
- GPU recorded by Gate649 doctor:
  `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`, compute capability `12.0`, VRAM `97886 MiB`, driver `596.21`.

## Artifacts

- `C:\glass_runs\phase2_s2_gate650_component_stage_ledger\runs_20260625_220000\gate649_component_ledger_replay\gate650_component_stage_ledger.json`
- `C:\glass_runs\phase2_s2_gate650_component_stage_ledger\runs_20260625_220000\gate650_component_stage_ledger_cli.json`
- `C:\glass_runs\phase2_s2_gate650_component_stage_ledger\runs_20260625_220000\gate649_component_ledger_replay\resident_stage_ledger.json`
- `C:\glass_runs\phase2_s2_gate650_component_stage_ledger\runs_20260625_220000\gate649_component_ledger_replay\resident_resume_preflight.json`
- `C:\glass_runs\phase2_s2_gate650_component_stage_ledger\runs_20260625_220000\gate650_phase2_mainline_audit.json`
- `C:\glass_runs\phase2_s2_gate650_component_stage_ledger\runs_20260625_220000\gate650_phase2_mainline_audit.md`

## Known Limitations

- This gate changes the resume/audit ledger, not image math or runtime performance.
- It does not persist calibrated light pixels or continue inside an interrupted VRAM-only stage.
- It prepares the contract surface needed for a future split of `resident_calibration_integration`.

## Next Step

Use the corrected component ledger to split resident calibration/admission into a deeper checkpointable boundary, or return directly to the measured hot path: `light_read_upload_calibrate` and `resident_integration`.

## Clean-Room Compliance

- This gate uses GLASS-owned state/ledger logic and GLASS-generated artifacts.
- Validation uses user-owned real-data artifacts and user-generated black-box reference metadata only.
- No external/proprietary implementation source was read, copied, summarized, or reworked.
- Input image directories were treated as read-only.
