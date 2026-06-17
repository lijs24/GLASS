# S2-Gate 216 Status

- Gate: S2-Gate 216
- Scope: Pipeline DQ Contract Handoff Provenance
- Status: green
- Date: 2026-06-18

## Completed

- Added `glass phase2-status --pipeline-contract` so Phase 2 handoff artifacts
  can carry the pipeline invariant contract as first-class evidence.
- Summarized pipeline DQ/mask contract state in Phase 2 status JSON and
  Markdown, including integration output/map counts, DQ contract status,
  StackEngine/resident result-contract status, pixel-verification state, and
  DQ/coverage/rejection pixel-match checks.
- Added Phase 2 status-compare preservation checks for pipeline contract pass
  state, integration DQ contract state, and pixel-verification state.
- Propagated pipeline contract provenance into Windows GitHub release-plan
  JSON, Markdown, and generated release notes.
- Updated focused tests and Phase 2 hardening documentation.

## Commands

- `.\.venv\Scripts\ruff.exe check src\glass\report\phase2_status.py src\glass\report\windows_github_release_plan.py src\glass\cli.py tests\test_phase2_status.py tests\test_windows_github_release_plan.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_phase2_status.py tests/test_windows_github_release_plan.py`
- `.\.venv\Scripts\ruff.exe check .`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_216_doctor.json`
- `.\.venv\Scripts\glass.exe phase2-status --checkpoint-dir runs\checkpoints --acceptance-audit runs\checkpoints\s2_gate_214_acceptance_real_fastpath_contract.json --pipeline-contract runs\checkpoints\s2_gate_211_pipeline_contract.json --release-manifest runs\checkpoints\s2_gate_194_strict_windows_release_manifest.json --github-release-plan runs\checkpoints\s2_gate_215_github_release_plan.json --out runs\checkpoints\s2_gate_216_phase2_status.json --markdown runs\checkpoints\s2_gate_216_phase2_status.md --fail-on-not-green`
- `.\.venv\Scripts\glass.exe phase2-status-compare --baseline-status runs\checkpoints\s2_gate_215_phase2_status.json --candidate-status runs\checkpoints\s2_gate_216_phase2_status.json --out runs\checkpoints\s2_gate_216_phase2_status_compare.json --markdown runs\checkpoints\s2_gate_216_phase2_status_compare.md --fail-on-regression`
- `.\.venv\Scripts\glass.exe windows-github-release-plan --manifest runs\checkpoints\s2_gate_194_strict_windows_release_manifest.json --tag v0.1.0-phase2-gate216 --title "GLASS Phase 2 Gate 216 Windows packages" --out runs\checkpoints\s2_gate_216_github_release_plan.json --markdown runs\checkpoints\s2_gate_216_github_release_plan.md --notes runs\checkpoints\s2_gate_216_release_notes.md --script runs\checkpoints\s2_gate_216_publish_release.ps1 --phase2-status runs\checkpoints\s2_gate_216_phase2_status.json --phase2-status-compare runs\checkpoints\s2_gate_216_phase2_status_compare.json --require-same-source-stamp --fail-on-failure`

## Test Results

- Focused ruff: passed.
- Focused pytest: 11 passed in 0.34s.
- Full ruff: passed.
- Full pytest: 502 passed in 27.18s.
- Phase 2 status: green, latest gate 216, pipeline contract passed.
- Phase 2 status compare: passed, baseline gate 215, candidate gate 216.
- Windows GitHub release plan: release_plan_ready, publication_ready true, 4 assets.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Native extension loaded: yes.

## Real Benchmark / Contract Evidence

- Real acceptance evidence source: `runs/checkpoints/s2_gate_214_acceptance_real_fastpath_contract.json`.
- Real pipeline contract source: `runs/checkpoints/s2_gate_211_pipeline_contract.json`.
- Pipeline contract status: passed.
- Pipeline integration DQ contract: passed.
- Pipeline DQ pixel verification: enabled and passed for DQ, coverage, and rejection maps.

## Artifacts

- `runs/checkpoints/s2_gate_216_doctor.json`
- `runs/checkpoints/s2_gate_216_phase2_status.json`
- `runs/checkpoints/s2_gate_216_phase2_status.md`
- `runs/checkpoints/s2_gate_216_phase2_status_compare.json`
- `runs/checkpoints/s2_gate_216_phase2_status_compare.md`
- `runs/checkpoints/s2_gate_216_github_release_plan.json`
- `runs/checkpoints/s2_gate_216_github_release_plan.md`
- `runs/checkpoints/s2_gate_216_release_notes.md`
- `runs/checkpoints/s2_gate_216_publish_release.ps1`

## Known Limitations

- This gate is reporting and release-handoff provenance only; it does not change
  calibration, registration, integration, DQ generation, or CUDA kernels.
- The real pipeline DQ contract is inherited from the green S2-Gate 211
  resident CUDA contract view; raw images were not reprocessed in this gate.

## Next Step

- Continue tightening the StackEngine/DQ default promotion path by requiring
  this handoff evidence in any later release-promotion gate.

## Clean-Room

- Compliant. No PixInsight/WBPP/PJSR source was read, copied, summarized, or
  reworked.
