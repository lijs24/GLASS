# S2-Gate 306 Status: Windows Release Matrix Direct Runtime Evidence

## Gate

- Gate: S2-Gate 306
- Scope: release/default-route evidence only
- Status: green

## Completed

- Added `runtime_default_direct_evidence` to `default-promotion-manifest`.
- The manifest now reads the release decision's direct acceptance and pipeline
  artifacts and summarizes:
  - explicit resident-artifacts registration fastpath evidence,
  - resident fastpath contract check count/failures,
  - direct resident calibration fallback from `resident_artifacts.json`,
  - resident native calibration status and calibrated-light count.
- Hardened `windows-release-matrix` so ready default-promotion manifests are
  blocked unless they preserve direct acceptance fastpath and direct pipeline
  resident calibration evidence.
- Added CLI escape hatch
  `--allow-missing-direct-runtime-evidence` for historical/debug artifacts.
- Updated `docs/phase2_algorithm_hardening.md` with Gate306.
- Generated Gate306 artifacts from existing 200-light Gate304/Gate305 evidence.

## Commands Run

- `.venv\Scripts\ruff.exe check src\glass\report\default_promotion_manifest.py src\glass\report\windows_release_matrix.py src\glass\cli.py tests\test_windows_release_matrix.py tests\test_default_promotion_manifest.py`
- `.venv\Scripts\python.exe -m pytest tests\test_windows_release_matrix.py tests\test_default_promotion_manifest.py -q`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_306_doctor.json --allow-cpu-only`
- `.venv\Scripts\python.exe -m glass.cli default-promotion-manifest --release-decision runs\checkpoints\s2_gate_305_release_decision_direct_acceptance_fastpath.json --phase2-status runs\checkpoints\s2_gate_305_phase2_status_direct_acceptance_fastpath.json --doctor-json runs\checkpoints\s2_gate_306_doctor.json --require-doctor --min-runtime-runs 2 --out runs\checkpoints\s2_gate_306_default_promotion_direct_runtime_evidence.json --markdown runs\checkpoints\s2_gate_306_default_promotion_direct_runtime_evidence.md`
- `.venv\Scripts\python.exe -m glass.cli windows-release-matrix --doctor-json runs\checkpoints\s2_gate_306_doctor.json --release-decision runs\checkpoints\s2_gate_305_release_decision_direct_acceptance_fastpath.json --acceptance-audit runs\checkpoints\s2_gate_305_acceptance_direct_fastpath_runtime_default.json --default-promotion-manifest runs\checkpoints\s2_gate_306_default_promotion_direct_runtime_evidence.json --expected-primary-package cuda13 --out runs\checkpoints\s2_gate_306_windows_release_matrix_direct_runtime_evidence.json --markdown runs\checkpoints\s2_gate_306_windows_release_matrix_direct_runtime_evidence.md`
- `.venv\Scripts\python.exe -m pytest -q`
- `git diff --check`

## Test Results

- Focused tests: `40 passed in 0.48s`
- Full tests: `709 passed in 29.99s`
- Ruff: passed
- `git diff --check`: passed with expected CRLF warnings only

## CUDA

- CUDA available: yes
- Native extension loaded: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- Windows package order: cuda13, cuda12, cuda11, cpu

## Artifacts

- `runs/checkpoints/s2_gate_306_doctor.json`
- `runs/checkpoints/s2_gate_306_default_promotion_direct_runtime_evidence.json`
- `runs/checkpoints/s2_gate_306_default_promotion_direct_runtime_evidence.md`
- `runs/checkpoints/s2_gate_306_windows_release_matrix_direct_runtime_evidence.json`
- `runs/checkpoints/s2_gate_306_windows_release_matrix_direct_runtime_evidence.md`

## Real 200-Light Evidence

- No new image benchmark was run.
- Gate306 reuses the existing real 200-light Gate304/Gate305 evidence.
- Direct acceptance fastpath source:
  `explicit_resident_artifacts_json`.
- Resident registration fastpath contract checks: 24 passed, 0 failed.
- Direct pipeline calibration source:
  `resident_artifacts_json_fallback`.
- Resident calibrated light count: 200.
- Windows release matrix status: `release_matrix_ready`.

## Known Limitations

- This gate does not change image math, CUDA kernels, runtime defaults, package
  builds, or release upload behavior.
- Direct evidence is checked from supplied artifacts. A historical manifest can
  still be inspected with `--allow-missing-direct-runtime-evidence`, but strict
  release-matrix readiness requires the new evidence.
- The default route still uses previously generated 200-light run artifacts;
  performance and numerical values were not rerun in this gate.

## Next Step

- Carry Gate306 direct release-matrix evidence forward into
  `windows-publish-preflight`, `phase2-status`, and publication-audit artifacts
  so the final publish path no longer relies on older handoff bundles.

## Clean-Room Compliance

- Compliant. This gate only reads GLASS-generated JSON/Markdown artifacts and
  local CUDA capability data.
- No PixInsight or WBPP source code was read, summarized, copied, or modified.
- Original image directories were not modified.
