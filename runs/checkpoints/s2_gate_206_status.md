# S2-Gate 206 Status: Master Calibration Surface Contract

- Gate: S2-Gate 206
- Status: green
- Date: 2026-06-18
- Scope: algorithm-core hardening for StackEngine master calibration audit

## Completed

- Added a master calibration surface contract to `glass stack-engine-contract`.
- Local master bias/dark/flat records now require:
  - existing output path
  - finite `min`, `max`, `mean`, `median`, and `std`
  - recorded tile size
  - recorded master rejection policy
  - dark bias semantics when applicable
  - flat per-frame normalization semantics when applicable
- Added `calibration_masters_science_auditable` as an explicit contract check.
- Added `master_calibration_science_contract_failed` as the adoption-gap reason for
  local master surfaces that used StackEngine but lack scientific audit metadata.
- Kept resident CUDA calibration compatible through the attached
  `resident_cuda_calibration_contract` path.
- Fixed StackEngine contract path resolution so artifacts written relative to the
  workspace or relative to the run directory are both accepted.
- Updated `docs/phase2_algorithm_hardening.md` with the Gate206 target.

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests/test_stack_engine_contract.py tests/test_pipeline_fixture.py::test_pipeline_fixture_run_calibration`
- `.venv\Scripts\ruff.exe check src\glass\report\stack_engine_contract.py tests\test_stack_engine_contract.py`
- `.venv\Scripts\python.exe -m pytest -q tests/test_pipeline_contract.py tests/test_cli_smoke.py::test_cli_guardrails_generates_contracts_and_report`
- `.venv\Scripts\python.exe -m pytest -q tests/test_acceptance_audit.py::test_acceptance_audit_accepts_contract_bundle tests/test_acceptance_audit.py::test_acceptance_audit_enforces_resident_contract_bundle_attachments tests/test_acceptance_audit.py::test_acceptance_audit_cli_accepts_contract_bundle`
- `.venv\Scripts\glass.exe synthetic --out runs\checkpoints\s2_gate_206_synthetic_data --frames 3 --width 24 --height 24 --known-shift`
- `.venv\Scripts\glass.exe audit --root runs\checkpoints\s2_gate_206_synthetic_data --out runs\checkpoints\s2_gate_206_synthetic_run --backend cpu --tile-size 8`
- `.venv\Scripts\glass.exe stack-engine-contract --run runs\checkpoints\s2_gate_206_synthetic_run --out runs\checkpoints\s2_gate_206_stack_engine_contract.json --markdown runs\checkpoints\s2_gate_206_stack_engine_contract.md --require-default-ready`
- `.venv\Scripts\ruff.exe check .`
- `.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_206_doctor.json`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\glass.exe phase2-status --checkpoint-dir runs\checkpoints --acceptance-audit runs\checkpoints\s2_gate_202_acceptance_real_bundle.json --release-manifest runs\checkpoints\s2_gate_194_strict_windows_release_manifest.json --github-release-plan runs\checkpoints\s2_gate_197_github_release_plan_publish_script.json --out runs\checkpoints\s2_gate_206_phase2_status.json --markdown runs\checkpoints\s2_gate_206_phase2_status.md --fail-on-not-green`
- `.venv\Scripts\glass.exe phase2-status-compare --baseline-status runs\checkpoints\s2_gate_205_phase2_status.json --candidate-status runs\checkpoints\s2_gate_206_phase2_status.json --out runs\checkpoints\s2_gate_206_phase2_status_compare.json --markdown runs\checkpoints\s2_gate_206_phase2_status_compare.md --fail-on-regression`

## Test Result

- Focused StackEngine/pipeline/acceptance tests: passed
- Ruff: passed
- Full pytest: `489 passed in 26.17s`
- Synthetic StackEngine contract artifact: passed
  - `default_promotion.ready=true`
  - `calibration_masters_science_auditable=true`
  - `calibration_masters_use_stack_engine=true`
- Phase 2 status: green
- Phase 2 status compare against Gate205: passed, no regression

## CUDA

- CUDA available: yes
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- CUDA native extension loaded: yes

## Artifacts

- `runs/checkpoints/s2_gate_206_status.md`
- `runs/checkpoints/s2_gate_206_doctor.json`
- `runs/checkpoints/s2_gate_206_stack_engine_contract.json`
- `runs/checkpoints/s2_gate_206_stack_engine_contract.md`
- `runs/checkpoints/s2_gate_206_phase2_status.json`
- `runs/checkpoints/s2_gate_206_phase2_status.md`
- `runs/checkpoints/s2_gate_206_phase2_status_compare.json`
- `runs/checkpoints/s2_gate_206_phase2_status_compare.md`

## Known Limitations

- Master calibration DQ FITS maps are still not emitted as standalone artifacts;
  Gate206 validates stats and semantics carried in `calibration_artifacts.json`.
- Resident CUDA master-calibration surfaces are accepted through the resident
  calibration contract rather than per-master CPU-style statistics.
- No new real 200-light run was launched in this gate; the existing accepted
  200-light benchmark remains preserved as prior evidence.

## Next Step

- S2-Gate 207 should continue algorithm-core hardening by either adding a
  calibration-artifact contract to the pipeline guardrails or bridging resident
  calibration statistics into the same master surface evidence model.

## Clean-Room

- Compliant. This gate used only GLASS source, synthetic GLASS fixtures, and
  GLASS-generated artifacts. No PixInsight/WBPP/PJSR source was read or used.
