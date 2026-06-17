# S2-Gate 207 Status: Calibration Pipeline Contract

- Gate: S2-Gate 207
- Status: green
- Date: 2026-06-18
- Scope: pipeline invariant contract coverage for calibration artifacts

## Completed

- Extended `glass pipeline-contract` to audit `calibration_artifacts.json` when
  it is present.
- Reused the Gate206 master calibration surface contract for local master
  bias/dark/flat rows.
- Added calibrated-light DQ contract rows requiring:
  - calibrated image path
  - DQ mask path
  - DQ summary with `valid`
  - positive tile count
  - positive tile size
- Added pipeline checks:
  - `calibration_master_surfaces_present`
  - `calibration_master_surface_contract`
  - `calibrated_lights_present`
  - `calibrated_light_dq_contract`
- Fixed `pipeline_contract` relative path resolution so workspace-relative and
  run-relative artifact paths both resolve correctly.
- Added HTML report rows for pipeline calibration master and calibrated-light
  contract evidence.
- Updated `docs/phase2_algorithm_hardening.md` with the Gate207 target.

## Commands Run

- `.venv\Scripts\ruff.exe check src\glass\report\pipeline_contract.py src\glass\report\stack_engine_contract.py src\glass\report\html_report.py tests\test_pipeline_contract.py tests\test_cli_smoke.py`
- `.venv\Scripts\python.exe -m pytest -q tests/test_pipeline_contract.py tests/test_cli_smoke.py::test_cli_guardrails_generates_contracts_and_report tests/test_stack_engine_contract.py`
- `.venv\Scripts\glass.exe synthetic --out runs\checkpoints\s2_gate_207_synthetic_data --frames 3 --width 24 --height 24 --known-shift`
- `.venv\Scripts\glass.exe audit --root runs\checkpoints\s2_gate_207_synthetic_data --out runs\checkpoints\s2_gate_207_synthetic_run --backend cpu --tile-size 8`
- `.venv\Scripts\glass.exe pipeline-contract --run runs\checkpoints\s2_gate_207_synthetic_run --out runs\checkpoints\s2_gate_207_pipeline_contract.json --markdown runs\checkpoints\s2_gate_207_pipeline_contract.md --pixel-verify --pixel-verify-tile-size 8`
- `.venv\Scripts\ruff.exe check .`
- `.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_207_doctor.json`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\glass.exe phase2-status --checkpoint-dir runs\checkpoints --acceptance-audit runs\checkpoints\s2_gate_202_acceptance_real_bundle.json --release-manifest runs\checkpoints\s2_gate_194_strict_windows_release_manifest.json --github-release-plan runs\checkpoints\s2_gate_197_github_release_plan_publish_script.json --out runs\checkpoints\s2_gate_207_phase2_status.json --markdown runs\checkpoints\s2_gate_207_phase2_status.md --fail-on-not-green`
- `.venv\Scripts\glass.exe phase2-status-compare --baseline-status runs\checkpoints\s2_gate_206_phase2_status.json --candidate-status runs\checkpoints\s2_gate_207_phase2_status.json --out runs\checkpoints\s2_gate_207_phase2_status_compare.json --markdown runs\checkpoints\s2_gate_207_phase2_status_compare.md --fail-on-regression`

## Test Result

- Focused contract/report tests: passed
- Synthetic CLI pipeline-contract artifact: passed
  - `calibration_master_surfaces_present=true`
  - `calibration_master_surface_contract=true`
  - `calibrated_lights_present=true`
  - `calibrated_light_dq_contract=true`
  - `master_count=3`
  - `calibrated_light_count=3`
- Ruff: passed
- Full pytest: `490 passed in 25.94s`
- Phase 2 status: green
- Phase 2 status compare against Gate206: passed, no regression

## CUDA

- CUDA available: yes
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- CUDA native extension loaded: yes

## Artifacts

- `runs/checkpoints/s2_gate_207_status.md`
- `runs/checkpoints/s2_gate_207_doctor.json`
- `runs/checkpoints/s2_gate_207_pipeline_contract.json`
- `runs/checkpoints/s2_gate_207_pipeline_contract.md`
- `runs/checkpoints/s2_gate_207_phase2_status.json`
- `runs/checkpoints/s2_gate_207_phase2_status.md`
- `runs/checkpoints/s2_gate_207_phase2_status_compare.json`
- `runs/checkpoints/s2_gate_207_phase2_status_compare.md`

## Known Limitations

- Calibration checks are active only when `calibration_artifacts.json` exists,
  preserving integration-only diagnostic fixtures and resident-result contract
  tests.
- Resident CUDA calibration remains represented by the separate resident
  calibration contract and StackEngine contract attachment path; this gate does
  not yet bridge resident calibration stats into `pipeline-contract`.
- No new real 200-light processing run was launched in this gate. The preserved
  acceptance baseline remains the Gate202/Gate200 200-light evidence.
- No new algorithm source was added; `docs/algorithm_sources.md` did not require
  an update for this contract-only gate.

## Next Step

- S2-Gate 208 should either make resident CUDA calibration expose the same
  master-surface evidence in pipeline contracts, or add a release/benchmark
  requirement that the 200-light acceptance contract requires the new
  calibration pipeline checks.

## Clean-Room

- Compliant. This gate used GLASS code, GLASS-generated synthetic data, and
  GLASS artifacts only. No PixInsight/WBPP/PJSR source was read or used.
