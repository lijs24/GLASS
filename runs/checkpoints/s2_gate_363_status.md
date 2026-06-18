# S2-Gate 363 Status

## Gate

- Gate: S2-Gate 363
- Name: Windows Publish Preflight Quality Metric Compare Guard
- Status: green
- Created: 2026-06-19

## Completed

- Carried `quality_metrics_compare` evidence into
  `glass windows-publish-preflight` from both Windows release-matrix and
  default-promotion artifacts.
- Added final publication-preflight checks:
  - `windows_release_matrix_quality_metrics_compare_handoff_passed`
  - `default_promotion_quality_metrics_compare_handoff_passed`
  - `matrix_quality_metrics_compare_matches_default_promotion`
- Preserved backward compatibility for older artifacts where
  `quality_metrics_compare` is absent.
- Added Markdown summary output for the quality-metrics compare handoff.
- Added pass, fail, missing-compatibility, and CLI Markdown tests.
- Updated Phase2 planning and algorithm-source audit documentation.

## Commands Run

- `.\.venv\Scripts\python.exe -m ruff check src\glass\report\windows_publish_preflight.py tests\test_windows_publish_preflight.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_windows_publish_preflight.py`
- `.\.venv\Scripts\python.exe -m glass.cli windows-publish-preflight --release-manifest runs\checkpoints\s2_gate_363_fixture\pass_release_manifest.json --github-release-plan runs\checkpoints\s2_gate_363_fixture\pass_github_release_plan.json --windows-release-matrix runs\checkpoints\s2_gate_363_fixture\pass_windows_release_matrix.json --default-promotion-manifest runs\checkpoints\s2_gate_363_fixture\pass_default_promotion_manifest.json --out runs\checkpoints\s2_gate_363_windows_publish_preflight_quality_compare_pass_guard.json --markdown runs\checkpoints\s2_gate_363_windows_publish_preflight_quality_compare_pass_guard.md --fail-on-failure`
- `.\.venv\Scripts\python.exe -m glass.cli windows-publish-preflight --release-manifest runs\checkpoints\s2_gate_363_fixture\fail_release_manifest.json --github-release-plan runs\checkpoints\s2_gate_363_fixture\fail_github_release_plan.json --windows-release-matrix runs\checkpoints\s2_gate_363_fixture\fail_windows_release_matrix.json --default-promotion-manifest runs\checkpoints\s2_gate_363_fixture\fail_default_promotion_manifest.json --out runs\checkpoints\s2_gate_363_windows_publish_preflight_quality_compare_fail_guard.json --markdown runs\checkpoints\s2_gate_363_windows_publish_preflight_quality_compare_fail_guard.md`
- `.\.venv\Scripts\python.exe -m glass.cli windows-publish-preflight --release-manifest runs\checkpoints\s2_gate_363_fixture\missing_release_manifest.json --github-release-plan runs\checkpoints\s2_gate_363_fixture\missing_github_release_plan.json --windows-release-matrix runs\checkpoints\s2_gate_363_fixture\missing_windows_release_matrix.json --default-promotion-manifest runs\checkpoints\s2_gate_363_fixture\missing_default_promotion_manifest.json --out runs\checkpoints\s2_gate_363_windows_publish_preflight_quality_compare_missing_guard.json --markdown runs\checkpoints\s2_gate_363_windows_publish_preflight_quality_compare_missing_guard.md --fail-on-failure`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_363_cuda_doctor.json --allow-cpu-only`

## Test Results

- Focused publish-preflight tests: `39 passed`
- Full test suite: `825 passed in 34.89s`
- Ruff: passed

## CUDA

- CUDA wrapper importable: yes
- CUDA native extension loaded: yes
- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- Recommended package: cuda13
- Fallback order: cuda13, cuda12, cuda11, cpu

## Artifacts

- `runs/checkpoints/s2_gate_363_cuda_doctor.json`
- `runs/checkpoints/s2_gate_363_fixture/pass_release_manifest.json`
- `runs/checkpoints/s2_gate_363_fixture/pass_github_release_plan.json`
- `runs/checkpoints/s2_gate_363_fixture/pass_windows_release_matrix.json`
- `runs/checkpoints/s2_gate_363_fixture/pass_default_promotion_manifest.json`
- `runs/checkpoints/s2_gate_363_fixture/fail_release_manifest.json`
- `runs/checkpoints/s2_gate_363_fixture/fail_github_release_plan.json`
- `runs/checkpoints/s2_gate_363_fixture/fail_windows_release_matrix.json`
- `runs/checkpoints/s2_gate_363_fixture/fail_default_promotion_manifest.json`
- `runs/checkpoints/s2_gate_363_fixture/missing_release_manifest.json`
- `runs/checkpoints/s2_gate_363_fixture/missing_github_release_plan.json`
- `runs/checkpoints/s2_gate_363_fixture/missing_windows_release_matrix.json`
- `runs/checkpoints/s2_gate_363_fixture/missing_default_promotion_manifest.json`
- `runs/checkpoints/s2_gate_363_windows_publish_preflight_quality_compare_pass_guard.json`
- `runs/checkpoints/s2_gate_363_windows_publish_preflight_quality_compare_pass_guard.md`
- `runs/checkpoints/s2_gate_363_windows_publish_preflight_quality_compare_fail_guard.json`
- `runs/checkpoints/s2_gate_363_windows_publish_preflight_quality_compare_fail_guard.md`
- `runs/checkpoints/s2_gate_363_windows_publish_preflight_quality_compare_missing_guard.json`
- `runs/checkpoints/s2_gate_363_windows_publish_preflight_quality_compare_missing_guard.md`

## Known Limitations

- This gate is a publication-preflight evidence guard only.
- It does not change quality metric calculations, thresholds, registration,
  local normalization, integration, CUDA kernels, runtime defaults, package
  builds, or GitHub release creation.
- The pass/fail/missing artifacts are controlled release-handoff fixtures used
  to isolate the quality-compare guard behavior.
- Real-data benchmark timing was not rerun in this gate.

## Next Step

- Continue the quality-evidence release chain into the next Phase2 status or
  publication-audit layer if the roadmap requires the final post-publish status
  to preserve this same guard.

## Clean-Room

- This gate consumed only GLASS-owned JSON release artifacts and controlled
  fixture artifacts.
- No external implementation source, proprietary source, image pixels, or user
  raw image directories were read.
- Input data directories remain read-only.
