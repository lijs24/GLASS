# S2-Gate 307 Status: Windows Publish Preflight Direct Runtime Evidence Handoff

## Gate

S2-Gate 307: Windows Publish Preflight Direct Runtime Evidence Handoff

## Completed Work

- Extended `glass windows-publish-preflight` so the final Windows publication
  preflight requires direct runtime-default evidence from both the Windows
  release matrix and default-promotion manifest.
- Added publish-preflight checks for:
  - `windows_release_matrix_direct_acceptance_fastpath_evidence`
  - `windows_release_matrix_direct_pipeline_calibration_evidence`
  - `default_promotion_direct_acceptance_fastpath_evidence`
  - `default_promotion_direct_pipeline_calibration_evidence`
  - `matrix_direct_runtime_evidence_matches_default_promotion`
- Surfaced direct runtime evidence readiness, fastpath source/check count,
  pipeline calibration source, and resident calibrated-light count in
  publish-preflight JSON and Markdown.
- Added focused tests for passing direct evidence, missing matrix direct
  evidence, and stale default-promotion fastpath source.
- Generated Gate307 release-manifest, GitHub release-plan, release notes,
  publish script, and publish-preflight artifacts using the existing package
  suite plus Gate306 matrix/default-promotion evidence.
- The first Gate307 publish-preflight run correctly blocked when the regenerated
  GitHub release plan omitted Phase2 status. The plan was regenerated with the
  Gate305 Phase2 status artifact, and the final preflight passed.
- Updated `docs/phase2_algorithm_hardening.md`.

## Commands Run

- `.venv\Scripts\ruff.exe check src\glass\report\windows_publish_preflight.py tests\test_windows_publish_preflight.py`
- `.venv\Scripts\python.exe -m pytest tests\test_windows_publish_preflight.py -q`
- `.venv\Scripts\python.exe -m glass.cli windows-release-manifest --suite runs\checkpoints\s2_gate_194_strict_windows_package_suite.json --windows-release-matrix runs\checkpoints\s2_gate_306_windows_release_matrix_direct_runtime_evidence.json --require-same-source-stamp --out runs\checkpoints\s2_gate_307_windows_release_manifest_direct_runtime_evidence.json --markdown runs\checkpoints\s2_gate_307_windows_release_manifest_direct_runtime_evidence.md --fail-on-failure`
- `.venv\Scripts\python.exe -m glass.cli windows-github-release-plan --manifest runs\checkpoints\s2_gate_307_windows_release_manifest_direct_runtime_evidence.json --windows-release-matrix runs\checkpoints\s2_gate_306_windows_release_matrix_direct_runtime_evidence.json --phase2-status runs\checkpoints\s2_gate_305_phase2_status_direct_acceptance_fastpath.json --tag v0.1.0-gate307-preflight --title "GLASS Windows Gate307 Preflight" --out runs\checkpoints\s2_gate_307_github_release_plan_direct_runtime_evidence.json --markdown runs\checkpoints\s2_gate_307_github_release_plan_direct_runtime_evidence.md --notes runs\checkpoints\s2_gate_307_github_release_notes_direct_runtime_evidence.md --script runs\checkpoints\s2_gate_307_publish_release_direct_runtime_evidence.ps1 --require-same-source-stamp --fail-on-failure`
- `.venv\Scripts\python.exe -m glass.cli windows-publish-preflight --release-manifest runs\checkpoints\s2_gate_307_windows_release_manifest_direct_runtime_evidence.json --github-release-plan runs\checkpoints\s2_gate_307_github_release_plan_direct_runtime_evidence.json --windows-release-matrix runs\checkpoints\s2_gate_306_windows_release_matrix_direct_runtime_evidence.json --default-promotion-manifest runs\checkpoints\s2_gate_306_default_promotion_direct_runtime_evidence.json --out runs\checkpoints\s2_gate_307_windows_publish_preflight_direct_runtime_evidence.json --markdown runs\checkpoints\s2_gate_307_windows_publish_preflight_direct_runtime_evidence.md --fail-on-failure`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\ruff.exe check src tests`
- `git diff --check`
- CUDA capability/device probe through `glass.capabilities`, `glass.gpu.device`, and `glass_cuda`.

## Test Results

- Targeted ruff: passed.
- Targeted pytest: `28 passed in 0.63s`.
- Full pytest: `711 passed in 30.20s`.
- Full ruff: passed.
- `git diff --check`: passed with CRLF conversion warnings only.
- Final Gate307 publish preflight: `publish_preflight_ready`, `passed=true`,
  `failed_checks=[]`, 59 checks.

## CUDA Status

- CUDA extension importable: true.
- CUDA available: true.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver version: 596.21.
- Native feature flags report smoke add, tile calibration, bilinear/Lanczos3
  warp, local normalization grid apply/stats, resident stack, resident simple
  SNR weighting, and resident sigma rejection support.

## Artifacts

- `runs/checkpoints/s2_gate_307_windows_release_manifest_direct_runtime_evidence.json`
- `runs/checkpoints/s2_gate_307_windows_release_manifest_direct_runtime_evidence.md`
- `runs/checkpoints/s2_gate_307_github_release_plan_direct_runtime_evidence.json`
- `runs/checkpoints/s2_gate_307_github_release_plan_direct_runtime_evidence.md`
- `runs/checkpoints/s2_gate_307_github_release_notes_direct_runtime_evidence.md`
- `runs/checkpoints/s2_gate_307_publish_release_direct_runtime_evidence.ps1`
- `runs/checkpoints/s2_gate_307_windows_publish_preflight_direct_runtime_evidence.json`
- `runs/checkpoints/s2_gate_307_windows_publish_preflight_direct_runtime_evidence.md`
- `runs/checkpoints/s2_gate_307_status.md`

## Real 200-Light Evidence Reused

- Release matrix: `runs/checkpoints/s2_gate_306_windows_release_matrix_direct_runtime_evidence.json`.
- Default-promotion manifest: `runs/checkpoints/s2_gate_306_default_promotion_direct_runtime_evidence.json`.
- Phase2 status: `runs/checkpoints/s2_gate_305_phase2_status_direct_acceptance_fastpath.json`.
- Direct acceptance fastpath source: `explicit_resident_artifacts_json`.
- Direct acceptance fastpath contract checks: 24.
- Direct pipeline calibration source: `resident_artifacts_json_fallback`.
- Resident calibrated lights surfaced by preflight: 200.

## Known Limitations

- This gate is publication-preflight scoped. It does not change image math,
  CUDA kernels, runtime defaults, package contents, GitHub release publication,
  or benchmark outputs.
- Package zip artifacts reused the existing Windows package suite from
  S2-Gate 194; no new package build was performed.
- No new 200-light real-data benchmark run was performed because the change is
  an evidence handoff guard.

## Next Step

S2-Gate 308 should carry the Gate307 direct runtime publish-preflight evidence
back into Phase2 status and any publication audit layer that still relies on
older aggregate publish-preflight readiness fields.

## Clean-Room Compliance

- This gate consumed only GLASS-owned package-suite, release-manifest, GitHub
  release-plan, Windows release-matrix, default-promotion, Phase2 status, and
  generated publish-preflight artifacts.
- No PixInsight/WBPP/PJSR implementation source, proprietary scripts, or
  external implementation code were read, summarized, copied, or modified.
- User image directories were not modified.
