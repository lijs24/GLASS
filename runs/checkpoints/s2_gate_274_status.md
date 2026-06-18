# S2-Gate 274 Status: Windows Publish Preflight Resident Winsorized Sweep Guard

## Gate

- Gate: S2-Gate 274
- Status: green
- Scope: publication-preflight evidence guard only

## Completed

- Extended `glass windows-publish-preflight` to summarize resident winsorized sweep evidence from the supplied Windows release matrix and default-promotion manifest.
- Added hard preflight checks for matrix-side resident winsorized sweep audit pass, required 200-frame row pass, non-empty sweep-audit check count, direct default-promotion sweep pass, default-promotion required row pass, and matrix/default-promotion sweep agreement.
- Added focused tests for passing, missing, failed, and mismatched resident winsorized sweep evidence.
- Added Gate274 documentation in `docs/phase2_algorithm_hardening.md` and the clean-room source entry in `docs/algorithm_sources.md`.
- Generated Gate274 local handoff/preflight artifacts:
  - `runs/checkpoints/s2_gate_274_windows_release_manifest.json`
  - `runs/checkpoints/s2_gate_274_windows_release_manifest.md`
  - `runs/checkpoints/s2_gate_274_github_release_plan.json`
  - `runs/checkpoints/s2_gate_274_github_release_plan.md`
  - `runs/checkpoints/s2_gate_274_github_release_notes.md`
  - `runs/checkpoints/s2_gate_274_publish_release.ps1`
  - `runs/checkpoints/s2_gate_274_windows_publish_preflight.json`
  - `runs/checkpoints/s2_gate_274_windows_publish_preflight.md`

## Commands

- `.\.venv\Scripts\ruff.exe check src\glass\report\windows_publish_preflight.py tests\test_windows_publish_preflight.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_windows_publish_preflight.py`
- `.\.venv\Scripts\python.exe -m glass.cli windows-release-manifest --suite runs\checkpoints\s2_gate_194_strict_windows_package_suite.json --windows-release-matrix runs\checkpoints\s2_gate_273_windows_release_matrix.json --require-same-source-stamp --out runs\checkpoints\s2_gate_274_windows_release_manifest.json --markdown runs\checkpoints\s2_gate_274_windows_release_manifest.md --fail-on-failure`
- `.\.venv\Scripts\python.exe -m glass.cli windows-github-release-plan --manifest runs\checkpoints\s2_gate_274_windows_release_manifest.json --tag v0.1.0-gate274-preflight --title "GLASS Gate274 publish preflight dry run" --windows-release-matrix runs\checkpoints\s2_gate_273_windows_release_matrix.json --phase2-status runs\checkpoints\s2_gate_272_phase2_status_fixture.json --phase2-status-compare runs\checkpoints\s2_gate_271_phase2_status_compare.json --require-same-source-stamp --out runs\checkpoints\s2_gate_274_github_release_plan.json --markdown runs\checkpoints\s2_gate_274_github_release_plan.md --notes runs\checkpoints\s2_gate_274_github_release_notes.md --script runs\checkpoints\s2_gate_274_publish_release.ps1 --fail-on-failure`
- `.\.venv\Scripts\python.exe -m glass.cli windows-publish-preflight --release-manifest runs\checkpoints\s2_gate_274_windows_release_manifest.json --github-release-plan runs\checkpoints\s2_gate_274_github_release_plan.json --windows-release-matrix runs\checkpoints\s2_gate_273_windows_release_matrix.json --default-promotion-manifest runs\checkpoints\s2_gate_272_default_promotion_manifest.json --out runs\checkpoints\s2_gate_274_windows_publish_preflight.json --markdown runs\checkpoints\s2_gate_274_windows_publish_preflight.md --fail-on-failure`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_windows_publish_preflight.py tests\test_windows_release_matrix.py tests\test_default_promotion_manifest.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Ruff: passed.
- Focused publish-preflight tests: `18 passed`.
- Related release/default/CLI tests: `61 passed`.
- Full suite: `630 passed in 28.59s`.

## CUDA

- CUDA availability was not reprobed in this gate.
- Gate273 Windows release matrix evidence reports:
  - `cuda_available=true`
  - `native_extension_loaded=true`
  - primary package `cuda13`
  - try order `cuda13,cuda12,cuda11,cpu`

## Artifact Result

- `runs/checkpoints/s2_gate_274_windows_publish_preflight.json`
  - status: `publish_preflight_ready`
  - passed: `true`
  - failed checks: `0`
  - resident winsorized sweep matrix status: `passed`
  - required frame count: `200`
  - sweep check count: `27`

## Known Limitations

- This gate does not change image math, CUDA kernels, runtime defaults, package contents, or GitHub release state.
- The generated GitHub release plan and publish script are dry-run handoff artifacts; no upload or release creation was performed.
- Real-data and 200-light benchmark runs were not repeated.

## Next Step

- Continue the Phase 2 release-evidence chain by deciding whether resident winsorized sweep evidence must also be surfaced in stack publication audits or Phase 2 public release notes.

## Clean-Room

- This gate consumed GLASS-owned JSON artifacts only.
- No external implementation source, proprietary source, PixInsight/WBPP source, or user input image pixels were read.
- Input image directories were not modified.
