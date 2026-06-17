# S2-Gate 227 Status

- Gate: S2-Gate 227
- Scope: GitHub Release Handoff Matrix Provenance
- Status: green
- Date: 2026-06-18
- Commit: pending

## Completed

- Added `--windows-release-matrix` to `glass windows-github-release-plan`.
- GitHub release handoff plans now require Windows release-matrix provenance by
  default, with `--allow-missing-windows-release-matrix` as an explicit legacy
  escape hatch.
- Release handoff checks now require a ready Windows matrix, ready
  default-promotion evidence, passing default-route contract evidence, CPU
  fallback in the install order, and matching release-manifest assets for all
  matrix package labels.
- Release-plan JSON, Markdown, generated release notes, and generated
  PowerShell publish scripts now carry Windows matrix/default-route evidence.
- Documented S2-Gate 227 in `docs/phase2_algorithm_hardening.md`.

## Commands

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_windows_github_release_plan.py`
- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\report\\windows_github_release_plan.py src\\glass\\cli.py tests\\test_windows_github_release_plan.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\ruff.exe check .`
- `.\\.venv\\Scripts\\glass.exe windows-github-release-plan --manifest runs\\checkpoints\\s2_gate_194_strict_windows_release_manifest.json --tag v0.1.0-phase2-gate227 --title "GLASS Phase 2 Gate 227 Windows packages" --out runs\\checkpoints\\s2_gate_227_github_release_plan.json --markdown runs\\checkpoints\\s2_gate_227_github_release_plan.md --notes runs\\checkpoints\\s2_gate_227_github_release_notes.md --script runs\\checkpoints\\s2_gate_227_publish_release.ps1 --phase2-status runs\\checkpoints\\s2_gate_226_phase2_status.json --phase2-status-compare runs\\checkpoints\\s2_gate_226_phase2_status_compare.json --windows-release-matrix runs\\checkpoints\\s2_gate_226_windows_release_matrix.json --require-same-source-stamp --fail-on-failure`
- `.\\.venv\\Scripts\\glass.exe phase2-status --checkpoint-dir runs\\checkpoints --acceptance-audit runs\\checkpoints\\s2_gate_214_acceptance_real_fastpath_contract.json --default-route-acceptance-audit runs\\checkpoints\\s2_gate_222_default_route_acceptance_audit.json --release-manifest runs\\checkpoints\\s2_gate_194_strict_windows_release_manifest.json --github-release-plan runs\\checkpoints\\s2_gate_227_github_release_plan.json --pipeline-contract runs\\checkpoints\\s2_gate_211_pipeline_contract.json --release-decision runs\\checkpoints\\s2_gate_218_release_promotion_decision.json --out runs\\checkpoints\\s2_gate_227_phase2_status.json --markdown runs\\checkpoints\\s2_gate_227_phase2_status.md --fail-on-not-green`
- `.\\.venv\\Scripts\\glass.exe phase2-status-compare --baseline-status runs\\checkpoints\\s2_gate_226_phase2_status.json --candidate-status runs\\checkpoints\\s2_gate_227_phase2_status.json --out runs\\checkpoints\\s2_gate_227_phase2_status_compare.json --markdown runs\\checkpoints\\s2_gate_227_phase2_status_compare.md --fail-on-regression`

## Test Results

- Windows GitHub release-plan pytest: 8 passed in 0.29 s.
- Targeted ruff: all checks passed.
- Full pytest: 523 passed in 25.62 s.
- Full ruff: all checks passed.
- GitHub release handoff plan: `release_plan_ready`.
- GitHub release handoff assets: cuda13, cuda12, cuda11, cpu.
- Windows release matrix handoff: `release_matrix_ready`.
- Default-promotion/default-route evidence: present and passed.
- Formal Phase 2 status: green, latest gate 227.
- Phase 2 status compare: passed, baseline gate 226, candidate gate 227.

## CUDA

- CUDA available: yes, from Gate 226 doctor artifact.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Windows package try order: cuda13, cuda12, cuda11, cpu.

## Artifacts

- `runs/checkpoints/s2_gate_227_github_release_plan.json`
- `runs/checkpoints/s2_gate_227_github_release_plan.md`
- `runs/checkpoints/s2_gate_227_github_release_notes.md`
- `runs/checkpoints/s2_gate_227_publish_release.ps1`
- `runs/checkpoints/s2_gate_227_phase2_status.json`
- `runs/checkpoints/s2_gate_227_phase2_status.md`
- `runs/checkpoints/s2_gate_227_phase2_status_compare.json`
- `runs/checkpoints/s2_gate_227_phase2_status_compare.md`

## Known Limitations

- This gate changes release/status verification only; it does not change image
  processing algorithms, CUDA kernels, package builds, or CLI default routing.
- The generated PowerShell script remains a dry-run by default and only
  publishes when rerun with `-Publish`.

## Next Step

- Carry the strict matrix/default-promotion handoff into the release manifest or
  package-suite layer so the package artifacts themselves can reference the same
  publication contract before GitHub handoff.

## Clean-Room Compliance

- This gate used only GLASS code, generated release artifacts, and prior GLASS
  checkpoint artifacts.
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or modified.
- Input image directories were not modified.
