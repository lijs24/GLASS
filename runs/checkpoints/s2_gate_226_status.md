# S2-Gate 226 Status

- Gate: S2-Gate 226
- Scope: Windows Release Matrix Promotion Provenance
- Status: green
- Date: 2026-06-18
- Commit: pending

## Completed

- Added `--default-promotion-manifest` to `glass windows-release-matrix`.
- Windows release matrix now requires default-promotion provenance by default:
  present, ready, passed, default-change ready, and backed by passing
  default-route route-contract evidence.
- Added `--allow-missing-default-promotion` as an explicit diagnostic escape
  hatch for old matrix artifacts.
- Added default-promotion summary to Windows release matrix JSON and Markdown.
- Added tests for passing, missing, failed, and CLI Markdown default-promotion
  evidence.
- Documented S2-Gate 226 in `docs/phase2_algorithm_hardening.md`.

## Commands

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_windows_release_matrix.py`
- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\report\\windows_release_matrix.py src\\glass\\cli.py tests\\test_windows_release_matrix.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\ruff.exe check .`
- `.\\.venv\\Scripts\\glass.exe doctor --json runs\\checkpoints\\s2_gate_226_doctor.json --allow-cpu-only`
- `.\\.venv\\Scripts\\glass.exe phase2-status --checkpoint-dir runs\\checkpoints --acceptance-audit runs\\checkpoints\\s2_gate_214_acceptance_real_fastpath_contract.json --default-route-acceptance-audit runs\\checkpoints\\s2_gate_222_default_route_acceptance_audit.json --release-manifest runs\\checkpoints\\s2_gate_194_strict_windows_release_manifest.json --github-release-plan runs\\checkpoints\\s2_gate_219_github_release_plan.json --pipeline-contract runs\\checkpoints\\s2_gate_211_pipeline_contract.json --release-decision runs\\checkpoints\\s2_gate_218_release_promotion_decision.json --out runs\\checkpoints\\s2_gate_226_phase2_status.json --markdown runs\\checkpoints\\s2_gate_226_phase2_status.md --fail-on-not-green`
- `.\\.venv\\Scripts\\glass.exe phase2-status-compare --baseline-status runs\\checkpoints\\s2_gate_225_phase2_status.json --candidate-status runs\\checkpoints\\s2_gate_226_phase2_status.json --out runs\\checkpoints\\s2_gate_226_phase2_status_compare.json --markdown runs\\checkpoints\\s2_gate_226_phase2_status_compare.md --fail-on-regression`
- `.\\.venv\\Scripts\\glass.exe default-promotion-manifest --release-decision runs\\checkpoints\\s2_gate_218_release_promotion_decision.json --phase2-status runs\\checkpoints\\s2_gate_226_phase2_status.json --doctor-json runs\\checkpoints\\s2_gate_226_doctor.json --require-doctor --min-runtime-runs 3 --out runs\\checkpoints\\s2_gate_226_default_promotion_manifest.json --markdown runs\\checkpoints\\s2_gate_226_default_promotion_manifest.md --fail-on-not-ready`
- `.\\.venv\\Scripts\\glass.exe windows-release-matrix --doctor-json runs\\checkpoints\\s2_gate_226_doctor.json --release-decision runs\\checkpoints\\s2_gate_218_release_promotion_decision.json --acceptance-audit runs\\checkpoints\\s2_gate_214_acceptance_real_fastpath_contract.json --default-promotion-manifest runs\\checkpoints\\s2_gate_226_default_promotion_manifest.json --expected-primary-package cuda13 --out runs\\checkpoints\\s2_gate_226_windows_release_matrix.json --markdown runs\\checkpoints\\s2_gate_226_windows_release_matrix.md --fail-on-not-ready`

## Test Results

- Windows release matrix pytest: 5 passed in 0.22 s.
- Targeted ruff: all checks passed.
- Full pytest: 521 passed in 25.47 s.
- Full ruff: all checks passed.
- Formal Phase 2 status: green, latest gate 226.
- Phase 2 status compare: passed, baseline gate 225, candidate gate 226.
- Default-promotion manifest: default_promotion_ready.
- Windows release matrix: release_matrix_ready, primary package cuda13.
- Windows release matrix default-promotion checks: present/ready/default-route
  all passed.

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Windows package try order: cuda13, cuda12, cuda11, cpu.

## Artifacts

- `runs/checkpoints/s2_gate_226_doctor.json`
- `runs/checkpoints/s2_gate_226_phase2_status.json`
- `runs/checkpoints/s2_gate_226_phase2_status.md`
- `runs/checkpoints/s2_gate_226_phase2_status_compare.json`
- `runs/checkpoints/s2_gate_226_phase2_status_compare.md`
- `runs/checkpoints/s2_gate_226_default_promotion_manifest.json`
- `runs/checkpoints/s2_gate_226_default_promotion_manifest.md`
- `runs/checkpoints/s2_gate_226_windows_release_matrix.json`
- `runs/checkpoints/s2_gate_226_windows_release_matrix.md`

## Known Limitations

- This gate changes release/status verification only; it does not change image
  processing algorithms, CUDA kernels, package builds, or CLI default routing.

## Next Step

- Propagate the default-route/default-promotion provenance into GitHub release
  handoff notes and publish scripts.

## Clean-Room Compliance

- This gate used only GLASS code, generated status artifacts, and prior GLASS
  checkpoint artifacts.
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or modified.
- Input image directories were not modified.
