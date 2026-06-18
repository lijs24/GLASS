# S2-Gate 275 Status: Phase 2 Publish Preflight Resident Winsorized Sweep Status Handoff

## Gate

- Gate: S2-Gate 275
- Status: green
- Scope: Phase 2 status and status-compare handoff only

## Completed

- Extended `glass phase2-status --publish-preflight` to preserve the Gate274
  resident winsorized sweep publication evidence.
- Added a Phase 2 blocker for missing or failed publish-preflight resident
  winsorized sweep evidence.
- Extended `glass phase2-status-compare` so a candidate cannot lose a previously
  passing publish-preflight resident winsorized sweep chain.
- Added focused tests for green handoff, missing/failed publish-preflight
  evidence, CLI Markdown output, and compare regression detection.
- Added Gate275 planning text in `docs/phase2_algorithm_hardening.md` and the
  clean-room source entry in `docs/algorithm_sources.md`.
- Generated Gate275 status artifacts:
  - `runs/checkpoints/s2_gate_275_phase2_status.json`
  - `runs/checkpoints/s2_gate_275_phase2_status.md`
  - `runs/checkpoints/s2_gate_275_phase2_status_compare.json`
  - `runs/checkpoints/s2_gate_275_phase2_status_compare.md`

## Commands

- `.\.venv\Scripts\ruff.exe check src\glass\report\phase2_status.py tests\test_phase2_status.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_phase2_status.py`
- `.\.venv\Scripts\python.exe -m glass.cli phase2-status --checkpoint-dir runs\checkpoints --acceptance-audit runs\checkpoints\s2_gate_214_acceptance_real_fastpath_contract.json --default-route-acceptance-audit runs\checkpoints\s2_gate_222_default_route_acceptance_audit.json --release-manifest runs\checkpoints\s2_gate_274_windows_release_manifest.json --github-release-plan runs\checkpoints\s2_gate_274_github_release_plan.json --publish-preflight runs\checkpoints\s2_gate_274_windows_publish_preflight.json --resident-winsorized-sweep-audit runs\checkpoints\s2_gate_269_resident_winsorized_sweep_audit.json --out runs\checkpoints\s2_gate_275_phase2_status.json --markdown runs\checkpoints\s2_gate_275_phase2_status.md --fail-on-not-green`
- `.\.venv\Scripts\python.exe -m glass.cli phase2-status-compare --baseline runs\checkpoints\s2_gate_271_phase2_status.json --candidate runs\checkpoints\s2_gate_275_phase2_status.json --out runs\checkpoints\s2_gate_275_phase2_status_compare.json --markdown runs\checkpoints\s2_gate_275_phase2_status_compare.md --fail-on-regression`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_phase2_status.py tests\test_windows_publish_preflight.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Ruff: passed.
- Focused Phase 2 status tests: `31 passed`.
- Related Phase 2/publish-preflight/CLI tests: `70 passed`.
- Full suite: `633 passed in 27.62s`.

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

- `runs/checkpoints/s2_gate_275_phase2_status.json`
  - status: `green`
  - publish-preflight status: `publish_preflight_ready`
  - resident winsorized sweep audit status: `passed`
  - matrix publish-preflight sweep status: `passed`
  - matrix required frame count: `200`
  - matrix sweep check count: `27`
  - default-promotion sweep status: `passed`
  - default-promotion required frame count: `200`
  - default-promotion sweep check count: `27`
- `runs/checkpoints/s2_gate_275_phase2_status_compare.json`
  - status: `passed`
  - baseline gate: `271`
  - candidate latest checkpoint gate: `274`

## Known Limitations

- This gate does not change image math, CUDA kernels, runtime defaults, package
  contents, GitHub release state, or publish-preflight behavior.
- Real-data and 200-light benchmark runs were not repeated.
- The compare artifact uses the latest available pre-Gate275 Phase 2 status as
  baseline; the new publish-preflight resident winsorized regression behavior is
  covered by focused unit tests.

## Next Step

- Continue Phase 2 release hardening by deciding the next publication audit or
  release-note handoff that should consume the Gate275 status artifact.

## Clean-Room

- This gate consumed GLASS-owned status and publish-preflight JSON artifacts
  only.
- No external implementation source, proprietary source, PixInsight/WBPP source,
  or user input image pixels were read.
- Input image directories were not modified.
