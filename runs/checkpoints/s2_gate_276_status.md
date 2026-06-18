# S2-Gate 276 Status: StackEngine Publication Audit Resident Winsorized Sweep Guard

## Gate

- Gate: S2-Gate 276
- Status: green
- Scope: StackEngine publication-audit evidence guard only

## Completed

- Extended `glass stack-engine-publication-audit` to summarize resident
  winsorized sweep evidence from both raw publish-preflight and Phase 2 status
  handoff artifacts.
- Added publication-audit blockers for missing or failed resident winsorized
  sweep evidence in either artifact.
- Added an agreement check so Phase 2 status cannot drift from the supplied raw
  publish-preflight resident winsorized sweep evidence.
- Added focused tests for ready evidence, failed resident winsorized evidence,
  Phase 2/raw publish-preflight mismatch detection, and CLI Markdown output.
- Added Gate276 planning text in `docs/phase2_algorithm_hardening.md` and the
  clean-room source entry in `docs/algorithm_sources.md`.
- Generated Gate276 artifacts:
  - `runs/checkpoints/s2_gate_276_phase2_status.json`
  - `runs/checkpoints/s2_gate_276_phase2_status.md`
  - `runs/checkpoints/s2_gate_276_stack_engine_publication_audit.json`
  - `runs/checkpoints/s2_gate_276_stack_engine_publication_audit.md`

## Commands

- `.\.venv\Scripts\ruff.exe check src\glass\report\stack_engine_publication_audit.py tests\test_stack_engine_publication_audit.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_stack_engine_publication_audit.py`
- `.\.venv\Scripts\python.exe -m glass.cli phase2-status --checkpoint-dir runs\checkpoints --acceptance-audit runs\checkpoints\s2_gate_214_acceptance_real_fastpath_contract.json --default-route-acceptance-audit runs\checkpoints\s2_gate_222_default_route_acceptance_audit.json --release-manifest runs\checkpoints\s2_gate_274_windows_release_manifest.json --github-release-plan runs\checkpoints\s2_gate_274_github_release_plan.json --publish-preflight runs\checkpoints\s2_gate_274_windows_publish_preflight.json --stack-engine-contract runs\checkpoints\s2_gate_211_stack_engine_contract.json --resident-winsorized-sweep-audit runs\checkpoints\s2_gate_269_resident_winsorized_sweep_audit.json --out runs\checkpoints\s2_gate_276_phase2_status.json --markdown runs\checkpoints\s2_gate_276_phase2_status.md --fail-on-not-green`
- `.\.venv\Scripts\python.exe -m glass.cli stack-engine-publication-audit --stack-engine-contract runs\checkpoints\s2_gate_211_stack_engine_contract.json --phase2-status runs\checkpoints\s2_gate_276_phase2_status.json --default-promotion-manifest runs\checkpoints\s2_gate_272_default_promotion_manifest.json --windows-release-matrix runs\checkpoints\s2_gate_273_windows_release_matrix.json --github-release-plan runs\checkpoints\s2_gate_274_github_release_plan.json --publish-preflight runs\checkpoints\s2_gate_274_windows_publish_preflight.json --out runs\checkpoints\s2_gate_276_stack_engine_publication_audit.json --markdown runs\checkpoints\s2_gate_276_stack_engine_publication_audit.md --fail-on-failure`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_stack_engine_publication_audit.py tests\test_phase2_status.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Ruff: passed.
- Focused publication-audit tests: `5 passed`.
- Related publication/status/CLI tests: `57 passed`.
- Full suite: `635 passed in 27.42s`.

## CUDA

- CUDA available: `true`
- Native extension loaded: `true`
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver version: `596.21`
- Windows package recommendation: primary `cuda13`, fallback order
  `cuda13,cuda12,cuda11,cpu`.

## Artifact Result

- `runs/checkpoints/s2_gate_276_phase2_status.json`
  - status: `green`
  - latest checkpoint gate: `275`
  - StackEngine contract status: `passed`
  - publish-preflight status: `publish_preflight_ready`
  - resident winsorized sweep audit status: `passed`
- `runs/checkpoints/s2_gate_276_stack_engine_publication_audit.json`
  - status: `passed`
  - passed: `true`
  - failed checks: `0`
  - phase2 publish-preflight resident winsorized ready: `true`
  - matrix resident winsorized sweep status: `passed`
  - matrix required frame count: `200`
  - matrix sweep check count: `27`
  - default-promotion resident winsorized sweep status: `passed`
  - default-promotion required frame count: `200`
  - default-promotion sweep check count: `27`

## Known Limitations

- This gate does not change image math, CUDA kernels, runtime defaults, package
  contents, GitHub release state, or publish-preflight behavior.
- Real-data and 200-light benchmark runs were not repeated.
- The audit validates GLASS-owned publication evidence artifacts; it does not
  regenerate StackEngine contracts, release matrices, packages, or GitHub
  releases.

## Next Step

- Continue Phase 2 by moving from release-evidence hardening back into
  algorithm hardening: the highest-value next gate is to reduce remaining
  StackEngine/default-route gaps in actual runtime behavior rather than adding
  another publication handoff layer.

## Clean-Room

- This gate consumed GLASS-owned StackEngine contract, Phase 2 status,
  default-promotion, release-matrix, GitHub release-plan, and publish-preflight
  JSON artifacts only.
- No external implementation source, proprietary source, PixInsight/WBPP source,
  user image directories, or input image pixels were read.
- Input image directories were not modified.
