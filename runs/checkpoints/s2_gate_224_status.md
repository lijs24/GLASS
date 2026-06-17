# S2-Gate 224 Status

- Gate: S2-Gate 224
- Scope: Default Route Supplemental Handoff Evidence
- Status: green
- Date: 2026-06-18
- Commit: pending

## Completed

- Added `--default-route-acceptance-audit` to `glass phase2-status`.
- Added a separate `default_route_acceptance` summary so the primary
  `acceptance_audit` can remain the 200-light fast-path/science artifact while
  the guarded default-route artifact is still carried in release handoff.
- Added default-route acceptance checks for resident memory mode, CUDA backend,
  resident registration mode, and resident runtime preset/group evidence.
- Added `glass phase2-status-compare` preservation checks so a candidate cannot
  drop or regress default-route acceptance evidence once a baseline contains it.
- Documented S2-Gate 224 in `docs/phase2_algorithm_hardening.md`.

## Commands

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_phase2_status.py`
- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\report\\phase2_status.py src\\glass\\cli.py tests\\test_phase2_status.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\ruff.exe check .`
- `.\\.venv\\Scripts\\glass.exe doctor --json runs\\checkpoints\\s2_gate_224_doctor.json --allow-cpu-only`
- `.\\.venv\\Scripts\\glass.exe phase2-status --checkpoint-dir runs\\checkpoints --acceptance-audit runs\\checkpoints\\s2_gate_214_acceptance_real_fastpath_contract.json --default-route-acceptance-audit runs\\checkpoints\\s2_gate_222_default_route_acceptance_audit.json --release-manifest runs\\checkpoints\\s2_gate_194_strict_windows_release_manifest.json --github-release-plan runs\\checkpoints\\s2_gate_219_github_release_plan.json --pipeline-contract runs\\checkpoints\\s2_gate_211_pipeline_contract.json --release-decision runs\\checkpoints\\s2_gate_218_release_promotion_decision.json --out runs\\checkpoints\\s2_gate_224_phase2_status.json --markdown runs\\checkpoints\\s2_gate_224_phase2_status.md --fail-on-not-green`
- `.\\.venv\\Scripts\\glass.exe phase2-status-compare --baseline-status runs\\checkpoints\\s2_gate_223_phase2_status.json --candidate-status runs\\checkpoints\\s2_gate_224_phase2_status.json --out runs\\checkpoints\\s2_gate_224_phase2_status_compare.json --markdown runs\\checkpoints\\s2_gate_224_phase2_status_compare.md --fail-on-regression`

## Test Results

- Phase 2 status pytest: 9 passed in 0.32 s.
- Targeted ruff: all checks passed.
- Full pytest: 517 passed in 27.66 s.
- Full ruff: all checks passed.
- Formal Phase 2 status: green, latest gate 224.
- Default-route acceptance status: passed.
- Formal Phase 2 status compare: passed, baseline gate 223, candidate gate 224.

## Acceptance Evidence Model

- Primary acceptance artifact: `runs/checkpoints/s2_gate_214_acceptance_real_fastpath_contract.json`
- Default-route acceptance artifact: `runs/checkpoints/s2_gate_222_default_route_acceptance_audit.json`
- The primary artifact preserves the 200-light benchmark, numerical comparison,
  and resident registration fast-path contract evidence.
- The default-route artifact proves the guarded resident CUDA default route
  without weakening the primary 200-light acceptance artifact.

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Windows package try order: cuda13, cuda12, cuda11, cpu.

## Artifacts

- `runs/checkpoints/s2_gate_224_doctor.json`
- `runs/checkpoints/s2_gate_224_phase2_status.json`
- `runs/checkpoints/s2_gate_224_phase2_status.md`
- `runs/checkpoints/s2_gate_224_phase2_status_compare.json`
- `runs/checkpoints/s2_gate_224_phase2_status_compare.md`

## Known Limitations

- This gate changes release/status reporting only; it does not change image
  processing algorithms, CUDA kernels, or registration defaults.
- The default-route acceptance artifact is supplemental release evidence, not a
  substitute for the 200-light fast-path/science acceptance artifact.

## Next Step

- Continue hardening default-route release handoff and decide whether resident
  registration receives its own guarded default profile.

## Clean-Room Compliance

- This gate used only GLASS code, generated status artifacts, and prior GLASS
  checkpoint artifacts.
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or modified.
- Input image directories were not modified.
