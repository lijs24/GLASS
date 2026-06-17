# S2-Gate 220 Status

- Gate: S2-Gate 220
- Scope: Default Promotion Manifest
- Status: green
- Date: 2026-06-18
- Commit: pending

## Completed

- Added `glass default-promotion-manifest`.
- Added an auditable default-promotion manifest that converts the Gate218
  `default_change_ready` release decision and Gate219 green Phase 2 handoff into
  an explicit resident CUDA default-promotion contract.
- The manifest verifies stable runtime-repeat evidence, pipeline DQ/mask
  handoff, StackEngine/resident result contracts, pixel verification, resident
  calibration artifacts, 200 resident calibrated lights, CUDA availability,
  native extension loading, Windows package primary selection, and CPU fallback
  order.
- Refreshed the Windows release matrix with the same Gate218/219 evidence.
- Documented S2-Gate 220 in `docs/phase2_algorithm_hardening.md`.

## Commands

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_default_promotion_manifest.py tests\\test_windows_release_matrix.py tests\\test_release_promotion_decision.py tests\\test_phase2_status.py`
- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\report\\default_promotion_manifest.py tests\\test_default_promotion_manifest.py src\\glass\\cli.py`
- `.\\.venv\\Scripts\\glass.exe default-promotion-manifest --release-decision runs\\checkpoints\\s2_gate_218_release_promotion_decision.json --phase2-status runs\\checkpoints\\s2_gate_219_phase2_status.json --doctor-json runs\\checkpoints\\s2_gate_219_doctor.json --require-doctor --min-runtime-runs 3 --out runs\\checkpoints\\s2_gate_220_default_promotion_manifest.json --markdown runs\\checkpoints\\s2_gate_220_default_promotion_manifest.md --fail-on-not-ready`
- `.\\.venv\\Scripts\\glass.exe windows-release-matrix --doctor-json runs\\checkpoints\\s2_gate_219_doctor.json --release-decision runs\\checkpoints\\s2_gate_218_release_promotion_decision.json --acceptance-audit runs\\checkpoints\\s2_gate_214_acceptance_real_fastpath_contract.json --expected-primary-package cuda13 --out runs\\checkpoints\\s2_gate_220_windows_release_matrix.json --markdown runs\\checkpoints\\s2_gate_220_windows_release_matrix.md --fail-on-not-ready`
- `.\\.venv\\Scripts\\ruff.exe check .`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\glass.exe doctor --json runs\\checkpoints\\s2_gate_220_doctor.json --allow-cpu-only`
- `.\\.venv\\Scripts\\glass.exe default-promotion-manifest --help`
- `.\\.venv\\Scripts\\glass.exe phase2-status --checkpoint-dir runs\\checkpoints --acceptance-audit runs\\checkpoints\\s2_gate_214_acceptance_real_fastpath_contract.json --release-manifest runs\\checkpoints\\s2_gate_194_strict_windows_release_manifest.json --github-release-plan runs\\checkpoints\\s2_gate_219_github_release_plan.json --pipeline-contract runs\\checkpoints\\s2_gate_211_pipeline_contract.json --release-decision runs\\checkpoints\\s2_gate_218_release_promotion_decision.json --out runs\\checkpoints\\s2_gate_220_phase2_status.json --markdown runs\\checkpoints\\s2_gate_220_phase2_status.md --fail-on-not-green`
- `.\\.venv\\Scripts\\glass.exe phase2-status-compare --baseline-status runs\\checkpoints\\s2_gate_219_phase2_status.json --candidate-status runs\\checkpoints\\s2_gate_220_phase2_status.json --out runs\\checkpoints\\s2_gate_220_phase2_status_compare.json --markdown runs\\checkpoints\\s2_gate_220_phase2_status_compare.md --fail-on-regression`

## Test Results

- Focused pytest: 17 passed in 0.47 s.
- Focused ruff: all checks passed.
- Full ruff: all checks passed.
- Full pytest: 506 passed in 27.71 s.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Windows package try order: cuda13, cuda12, cuda11, cpu.

## Artifacts

- `runs/checkpoints/s2_gate_220_default_promotion_manifest.json`
- `runs/checkpoints/s2_gate_220_default_promotion_manifest.md`
- `runs/checkpoints/s2_gate_220_windows_release_matrix.json`
- `runs/checkpoints/s2_gate_220_windows_release_matrix.md`
- `runs/checkpoints/s2_gate_220_doctor.json`
- `runs/checkpoints/s2_gate_220_phase2_status.json`
- `runs/checkpoints/s2_gate_220_phase2_status.md`
- `runs/checkpoints/s2_gate_220_phase2_status_compare.json`
- `runs/checkpoints/s2_gate_220_phase2_status_compare.md`

## Known Limitations

- This gate proves readiness for resident CUDA default promotion but does not
  change CLI defaults.
- The tile and CPU fallback paths must remain available when the actual default
  switch is implemented.
- Runtime evidence is based on the existing controlled 200-light repeat run from
  S2-Gate 218.

## Next Step

- S2-Gate 221 should perform the actual guarded default switch or release
  handoff update using the S2-Gate 220 manifest as the promotion contract.

## Clean-Room Compliance

- This gate used only GLASS artifacts, local generated logs, and project code.
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or modified.
- Input image directories were not modified.
