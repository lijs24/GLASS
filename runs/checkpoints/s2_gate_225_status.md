# S2-Gate 225 Status

- Gate: S2-Gate 225
- Scope: Default Route Promotion Manifest Provenance
- Status: green
- Date: 2026-06-18
- Commit: pending

## Completed

- Extended `glass default-promotion-manifest` to consume
  `phase2_status.default_route_acceptance`.
- Default promotion now requires default-route acceptance evidence to be present,
  passed, route-contract passed, and backed by at least four route checks.
- Added default-route acceptance summary to the default-promotion manifest JSON
  and Markdown.
- Added tests for pass, missing default-route evidence, failed default-route
  evidence, and CLI Markdown output.
- Documented S2-Gate 225 in `docs/phase2_algorithm_hardening.md`.

## Commands

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_default_promotion_manifest.py`
- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\report\\default_promotion_manifest.py tests\\test_default_promotion_manifest.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\ruff.exe check .`
- `.\\.venv\\Scripts\\glass.exe doctor --json runs\\checkpoints\\s2_gate_225_doctor.json --allow-cpu-only`
- `.\\.venv\\Scripts\\glass.exe phase2-status --checkpoint-dir runs\\checkpoints --acceptance-audit runs\\checkpoints\\s2_gate_214_acceptance_real_fastpath_contract.json --default-route-acceptance-audit runs\\checkpoints\\s2_gate_222_default_route_acceptance_audit.json --release-manifest runs\\checkpoints\\s2_gate_194_strict_windows_release_manifest.json --github-release-plan runs\\checkpoints\\s2_gate_219_github_release_plan.json --pipeline-contract runs\\checkpoints\\s2_gate_211_pipeline_contract.json --release-decision runs\\checkpoints\\s2_gate_218_release_promotion_decision.json --out runs\\checkpoints\\s2_gate_225_phase2_status.json --markdown runs\\checkpoints\\s2_gate_225_phase2_status.md --fail-on-not-green`
- `.\\.venv\\Scripts\\glass.exe phase2-status-compare --baseline-status runs\\checkpoints\\s2_gate_224_phase2_status.json --candidate-status runs\\checkpoints\\s2_gate_225_phase2_status.json --out runs\\checkpoints\\s2_gate_225_phase2_status_compare.json --markdown runs\\checkpoints\\s2_gate_225_phase2_status_compare.md --fail-on-regression`
- `.\\.venv\\Scripts\\glass.exe default-promotion-manifest --release-decision runs\\checkpoints\\s2_gate_218_release_promotion_decision.json --phase2-status runs\\checkpoints\\s2_gate_225_phase2_status.json --doctor-json runs\\checkpoints\\s2_gate_225_doctor.json --require-doctor --min-runtime-runs 3 --out runs\\checkpoints\\s2_gate_225_default_promotion_manifest.json --markdown runs\\checkpoints\\s2_gate_225_default_promotion_manifest.md --fail-on-not-ready`

## Test Results

- Default-promotion manifest pytest: 5 passed in 0.21 s.
- Targeted ruff: all checks passed.
- Full pytest: 519 passed in 25.49 s.
- Full ruff: all checks passed.
- Formal Phase 2 status: green, latest gate 225.
- Phase 2 status compare: passed, baseline gate 224, candidate gate 225.
- Default-promotion manifest: default_promotion_ready.
- Default-route manifest checks: present/pass/route-contract/check-count all
  passed.

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Windows package try order: cuda13, cuda12, cuda11, cpu.

## Artifacts

- `runs/checkpoints/s2_gate_225_doctor.json`
- `runs/checkpoints/s2_gate_225_phase2_status.json`
- `runs/checkpoints/s2_gate_225_phase2_status.md`
- `runs/checkpoints/s2_gate_225_phase2_status_compare.json`
- `runs/checkpoints/s2_gate_225_phase2_status_compare.md`
- `runs/checkpoints/s2_gate_225_default_promotion_manifest.json`
- `runs/checkpoints/s2_gate_225_default_promotion_manifest.md`

## Known Limitations

- This gate changes release/status verification only; it does not change image
  processing algorithms, CUDA kernels, or CLI default routing.

## Next Step

- Propagate the default-route promotion manifest provenance into Windows release
  matrix and GitHub release handoff artifacts.

## Clean-Room Compliance

- This gate used only GLASS code, generated status artifacts, and prior GLASS
  checkpoint artifacts.
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or modified.
- Input image directories were not modified.
