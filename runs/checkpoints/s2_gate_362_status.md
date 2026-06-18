# S2-Gate 362 Status

- Gate: S2-Gate 362
- Scope: Windows release matrix quality metric compare guard
- Status: green
- Date: 2026-06-19

## Completed

- Added default-promotion `quality_metrics_compare` summary fields to
  `glass windows-release-matrix`.
- Added `default_promotion_quality_metrics_compare_handoff_passed`, which blocks
  Windows release readiness only when default-promotion supplies quality compare
  evidence and that handoff is not ready.
- Preserved backward compatibility for older default-promotion artifacts without
  `quality_metrics_compare`.
- Surfaced the quality compare handoff in Windows release matrix Markdown.
- Added focused ready, blocked, missing-compatible, and CLI Markdown tests.
- Documented the gate in Phase2 hardening and algorithm-source provenance docs.

## Commands

- `.\.venv\Scripts\python.exe -m ruff check src\glass\report\windows_release_matrix.py tests\test_windows_release_matrix.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_windows_release_matrix.py::test_windows_release_matrix_passes_blackwell_default tests\test_windows_release_matrix.py::test_windows_release_matrix_blocks_failed_quality_metrics_compare tests\test_windows_release_matrix.py::test_windows_release_matrix_allows_missing_quality_metrics_compare tests\test_windows_release_matrix.py::test_windows_release_matrix_cli_writes_json_and_markdown`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe -m glass.cli windows-release-matrix --doctor-json runs\checkpoints\s2_gate_361_cuda_doctor.json --release-decision runs\checkpoints\s2_gate_309_release_decision_direct_runtime_publication_guard.json --default-promotion-manifest runs\checkpoints\s2_gate_361_default_promotion_quality_compare_pass_guard.json --expected-primary-package cuda13 --out runs\checkpoints\s2_gate_362_windows_release_matrix_quality_compare_pass_guard.json --markdown runs\checkpoints\s2_gate_362_windows_release_matrix_quality_compare_pass_guard.md`
- `.\.venv\Scripts\python.exe -m glass.cli windows-release-matrix --doctor-json runs\checkpoints\s2_gate_361_cuda_doctor.json --release-decision runs\checkpoints\s2_gate_309_release_decision_direct_runtime_publication_guard.json --default-promotion-manifest runs\checkpoints\s2_gate_361_default_promotion_quality_compare_fail_guard.json --expected-primary-package cuda13 --out runs\checkpoints\s2_gate_362_windows_release_matrix_quality_compare_fail_guard.json --markdown runs\checkpoints\s2_gate_362_windows_release_matrix_quality_compare_fail_guard.md`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_362_cuda_doctor.json --allow-cpu-only`

## Test Results

- Ruff: passed.
- Focused pytest: 4 passed.
- Full pytest: 823 passed in 34.75 s.
- CLI guard diagnostics:
  - pass matrix: `default_promotion_quality_metrics_compare_handoff_passed` PASS
  - fail matrix: `default_promotion_quality_metrics_compare_handoff_passed`
    FAIL with `bad_median_ratio_within_limit`

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Artifacts

- `runs/checkpoints/s2_gate_362_windows_release_matrix_quality_compare_pass_guard.json`
- `runs/checkpoints/s2_gate_362_windows_release_matrix_quality_compare_pass_guard.md`
- `runs/checkpoints/s2_gate_362_windows_release_matrix_quality_compare_fail_guard.json`
- `runs/checkpoints/s2_gate_362_windows_release_matrix_quality_compare_fail_guard.md`
- `runs/checkpoints/s2_gate_362_cuda_doctor.json`

## Known Limitations

- This gate only protects Windows release-matrix readiness when
  default-promotion supplies a `quality_metrics_compare` handoff. It does not
  define new default quality thresholds.
- The generated release-matrix guard artifacts are diagnostics focused on the
  new quality-compare check. They are intentionally blocked overall because
  their default-promotion inputs are Gate361 guard fixtures, not full
  release-ready manifests.
- No real-data benchmark rerun was performed for this policy-handoff gate.

## Next Step

- Carry the same optional quality-compare handoff into Windows publish-preflight
  so final release-preflight artifacts preserve the quality-regression guard.

## Clean-Room Compliance

- Compliant. This gate uses only GLASS-owned doctor, release-decision, and
  default-promotion JSON artifacts plus project-defined release-matrix policy.
- No PixInsight/WBPP/PJSR source, proprietary implementation details, user raw
  image directories, or external benchmark outputs were read or modified.
