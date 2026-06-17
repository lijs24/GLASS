# S2-Gate 215 Status

- Gate: S2-Gate 215
- Scope: Resident Registration Fast-Path Release Provenance
- Status: green
- Date: 2026-06-18

## Completed

- Propagated resident registration fast-path evidence from acceptance-audit
  artifacts into Phase 2 status JSON and Markdown.
- Propagated the same fast-path provenance into Windows GitHub release handoff
  summaries, generated Markdown, and generated release notes.
- Added focused tests for Phase 2 status and Windows release-plan provenance.
- Documented the gate in `docs/phase2_algorithm_hardening.md`.

## Commands

- `.\.venv\Scripts\ruff.exe check src\glass\report\phase2_status.py src\glass\report\windows_github_release_plan.py tests\test_phase2_status.py tests\test_windows_github_release_plan.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_phase2_status.py tests/test_windows_github_release_plan.py`
- `.\.venv\Scripts\ruff.exe check .`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_215_doctor.json`
- `.\.venv\Scripts\glass.exe phase2-status --checkpoint-dir runs\checkpoints --acceptance-audit runs\checkpoints\s2_gate_214_acceptance_real_fastpath_contract.json --release-manifest runs\checkpoints\s2_gate_194_strict_windows_release_manifest.json --github-release-plan runs\checkpoints\s2_gate_214_github_release_plan.json --out runs\checkpoints\s2_gate_215_phase2_status.json --markdown runs\checkpoints\s2_gate_215_phase2_status.md --fail-on-not-green`
- `.\.venv\Scripts\glass.exe phase2-status-compare --baseline-status runs\checkpoints\s2_gate_214_phase2_status.json --candidate-status runs\checkpoints\s2_gate_215_phase2_status.json --out runs\checkpoints\s2_gate_215_phase2_status_compare.json --markdown runs\checkpoints\s2_gate_215_phase2_status_compare.md --fail-on-regression`
- `.\.venv\Scripts\glass.exe windows-github-release-plan --manifest runs\checkpoints\s2_gate_194_strict_windows_release_manifest.json --tag v0.1.0-phase2-gate215 --title "GLASS Phase 2 Gate 215 Windows packages" --out runs\checkpoints\s2_gate_215_github_release_plan.json --markdown runs\checkpoints\s2_gate_215_github_release_plan.md --notes runs\checkpoints\s2_gate_215_release_notes.md --script runs\checkpoints\s2_gate_215_publish_release.ps1 --phase2-status runs\checkpoints\s2_gate_215_phase2_status.json --phase2-status-compare runs\checkpoints\s2_gate_215_phase2_status_compare.json --require-same-source-stamp --fail-on-failure`

## Test Results

- Focused ruff: passed.
- Focused pytest: 11 passed in 0.37s.
- Full ruff: passed.
- Full pytest: 502 passed in 26.78s.
- Phase 2 status: green, latest gate 215, speedup vs reference 58.099101701945926.
- Phase 2 status compare: passed, baseline gate 214, candidate gate 215.
- Windows GitHub release plan: release_plan_ready, publication_ready true, 4 assets.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Native extension loaded: yes.

## Artifacts

- `runs/checkpoints/s2_gate_215_doctor.json`
- `runs/checkpoints/s2_gate_215_phase2_status.json`
- `runs/checkpoints/s2_gate_215_phase2_status.md`
- `runs/checkpoints/s2_gate_215_phase2_status_compare.json`
- `runs/checkpoints/s2_gate_215_phase2_status_compare.md`
- `runs/checkpoints/s2_gate_215_github_release_plan.json`
- `runs/checkpoints/s2_gate_215_github_release_plan.md`
- `runs/checkpoints/s2_gate_215_release_notes.md`
- `runs/checkpoints/s2_gate_215_publish_release.ps1`

## Known Limitations

- This gate is reporting and release-handoff provenance only; it does not change
  registration, warp, calibration, or integration algorithms.
- The real fast-path acceptance evidence is inherited from the green S2-Gate
  214 real resident CUDA run.

## Next Step

- Continue Phase 2 by turning the release-proven resident registration
  fast-path evidence into the next optimization/reporting gate.

## Clean-Room

- Compliant. No PixInsight/WBPP/PJSR source was read, copied, summarized, or
  reworked.
