# S2-Gate 223 Status

- Gate: S2-Gate 223
- Scope: Fast-Path Contract Status Preservation
- Status: green
- Date: 2026-06-18
- Commit: pending

## Completed

- Added a Phase 2 status guard that requires resident registration fast-path
  contract checks to be present and passed whenever the release decision is
  ready to promote the default candidate.
- Added Phase 2 status comparison checks that preserve
  `resident_registration_fastpath_contract_status=passed` and prevent the
  resident registration fast-path contract check count from dropping.
- Kept the Gate 222 default-route acceptance fixture valid as a behavioral
  contract test, but no longer strong enough to serve as release-ready Phase 2
  status evidence by itself.
- Documented S2-Gate 223 in `docs/phase2_algorithm_hardening.md`.

## Commands

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_phase2_status.py`
- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\report\\phase2_status.py tests\\test_phase2_status.py`
- `.\\.venv\\Scripts\\glass.exe doctor --json runs\\checkpoints\\s2_gate_223_doctor.json --allow-cpu-only`
- `.\\.venv\\Scripts\\glass.exe phase2-status --checkpoint-dir runs\\checkpoints --acceptance-audit runs\\checkpoints\\s2_gate_222_default_route_acceptance_audit.json --release-manifest runs\\checkpoints\\s2_gate_194_strict_windows_release_manifest.json --github-release-plan runs\\checkpoints\\s2_gate_219_github_release_plan.json --pipeline-contract runs\\checkpoints\\s2_gate_211_pipeline_contract.json --release-decision runs\\checkpoints\\s2_gate_218_release_promotion_decision.json --out runs\\checkpoints\\s2_gate_223_weak_default_route_phase2_status.json --markdown runs\\checkpoints\\s2_gate_223_weak_default_route_phase2_status.md`
- `.\\.venv\\Scripts\\glass.exe phase2-status --checkpoint-dir runs\\checkpoints --acceptance-audit runs\\checkpoints\\s2_gate_214_acceptance_real_fastpath_contract.json --release-manifest runs\\checkpoints\\s2_gate_194_strict_windows_release_manifest.json --github-release-plan runs\\checkpoints\\s2_gate_219_github_release_plan.json --pipeline-contract runs\\checkpoints\\s2_gate_211_pipeline_contract.json --release-decision runs\\checkpoints\\s2_gate_218_release_promotion_decision.json --out runs\\checkpoints\\s2_gate_223_phase2_status.json --markdown runs\\checkpoints\\s2_gate_223_phase2_status.md --fail-on-not-green`
- `.\\.venv\\Scripts\\glass.exe phase2-status-compare --baseline-status runs\\checkpoints\\s2_gate_221_phase2_status.json --candidate-status runs\\checkpoints\\s2_gate_223_weak_default_route_phase2_status.json --out runs\\checkpoints\\s2_gate_223_weak_default_route_status_compare.json --markdown runs\\checkpoints\\s2_gate_223_weak_default_route_status_compare.md`
- `.\\.venv\\Scripts\\glass.exe phase2-status-compare --baseline-status runs\\checkpoints\\s2_gate_222_phase2_status.json --candidate-status runs\\checkpoints\\s2_gate_223_phase2_status.json --out runs\\checkpoints\\s2_gate_223_phase2_status_compare.json --markdown runs\\checkpoints\\s2_gate_223_phase2_status_compare.md --fail-on-regression`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\ruff.exe check .`

## Test Results

- Phase 2 status pytest: 7 passed in 0.26 s.
- Targeted ruff: all checks passed.
- Full pytest: 515 passed in 27.85 s.
- Full ruff: all checks passed.
- Weak default-route status diagnostic: attention_required as expected because
  `resident_registration_fastpath_contract_status` was `not_requested`.
- Formal Phase 2 status: green, latest gate 223, speedup 58.099101701945926x.
- Weak default-route compare: regressed, with fast-path contract status/count
  preservation checks failing as expected.
- Formal Phase 2 status compare: passed, baseline gate 222, candidate gate 223.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Windows package try order: cuda13, cuda12, cuda11, cpu.

## Artifacts

- `runs/checkpoints/s2_gate_223_doctor.json`
- `runs/checkpoints/s2_gate_223_weak_default_route_phase2_status.json`
- `runs/checkpoints/s2_gate_223_weak_default_route_phase2_status.md`
- `runs/checkpoints/s2_gate_223_weak_default_route_status_compare.json`
- `runs/checkpoints/s2_gate_223_weak_default_route_status_compare.md`
- `runs/checkpoints/s2_gate_223_phase2_status.json`
- `runs/checkpoints/s2_gate_223_phase2_status.md`
- `runs/checkpoints/s2_gate_223_phase2_status_compare.json`
- `runs/checkpoints/s2_gate_223_phase2_status_compare.md`

## Known Limitations

- This gate changes release/status verification only; it does not change image
  processing algorithms, CUDA kernels, or registration defaults.
- The weak default-route fixture remains useful for testing default-route token
  evidence, but formal release handoff should use the preserved 200-light
  fast-path acceptance audit.

## Next Step

- Continue hardening release/default handoff with the preserved 200-light
  benchmark artifacts, then decide whether resident registration should receive
  its own guarded default profile.

## Clean-Room Compliance

- This gate used only GLASS code, generated status artifacts, and prior GLASS
  checkpoint artifacts.
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or modified.
- Input image directories were not modified.
