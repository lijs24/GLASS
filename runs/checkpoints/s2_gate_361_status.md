# S2-Gate 361 Status

- Gate: S2-Gate 361
- Scope: Default promotion quality metric compare guard
- Status: green
- Date: 2026-06-19

## Completed

- Added `quality_metrics_compare` summary extraction to
  `glass default-promotion-manifest`.
- Added `quality_metrics_compare_handoff_passed`, which blocks default
  promotion only when Phase2 status supplies quality compare evidence and that
  handoff is not passing.
- Preserved backward compatibility for older Phase2 status artifacts without
  `quality_metrics_compare`.
- Surfaced the quality compare handoff in default-promotion Markdown output.
- Added focused ready, blocked, and CLI Markdown tests.
- Documented the gate in Phase2 hardening and algorithm-source provenance docs.

## Commands

- `.\.venv\Scripts\python.exe -m ruff check src\glass\report\default_promotion_manifest.py tests\test_default_promotion_manifest.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_default_promotion_manifest.py::test_default_promotion_manifest_passes_ready_artifacts tests\test_default_promotion_manifest.py::test_default_promotion_manifest_blocks_failed_quality_metrics_compare tests\test_default_promotion_manifest.py::test_default_promotion_manifest_allows_missing_quality_metrics_compare tests\test_default_promotion_manifest.py::test_default_promotion_manifest_cli_writes_json_and_markdown`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe -m glass.cli default-promotion-manifest --release-decision runs\checkpoints\s2_gate_309_release_decision_direct_runtime_publication_guard.json --phase2-status runs\checkpoints\s2_gate_360_phase2_quality_metrics_compare_pass_status.json --doctor-json runs\checkpoints\s2_gate_360_cuda_doctor.json --out runs\checkpoints\s2_gate_361_default_promotion_quality_compare_pass_guard.json --markdown runs\checkpoints\s2_gate_361_default_promotion_quality_compare_pass_guard.md`
- `.\.venv\Scripts\python.exe -m glass.cli default-promotion-manifest --release-decision runs\checkpoints\s2_gate_309_release_decision_direct_runtime_publication_guard.json --phase2-status runs\checkpoints\s2_gate_360_phase2_quality_metrics_compare_fail_status.json --doctor-json runs\checkpoints\s2_gate_360_cuda_doctor.json --out runs\checkpoints\s2_gate_361_default_promotion_quality_compare_fail_guard.json --markdown runs\checkpoints\s2_gate_361_default_promotion_quality_compare_fail_guard.md`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_361_cuda_doctor.json --allow-cpu-only`

## Test Results

- Ruff: passed.
- Focused pytest: 4 passed.
- Full pytest: 821 passed in 34.70 s.
- CLI guard diagnostics:
  - pass guard: `quality_metrics_compare_handoff_passed` PASS
  - fail guard: `quality_metrics_compare_handoff_passed` FAIL with
    `bad_median_ratio_within_limit`

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Artifacts

- `runs/checkpoints/s2_gate_361_default_promotion_quality_compare_pass_guard.json`
- `runs/checkpoints/s2_gate_361_default_promotion_quality_compare_pass_guard.md`
- `runs/checkpoints/s2_gate_361_default_promotion_quality_compare_fail_guard.json`
- `runs/checkpoints/s2_gate_361_default_promotion_quality_compare_fail_guard.md`
- `runs/checkpoints/s2_gate_361_cuda_doctor.json`

## Known Limitations

- This gate only protects default-promotion readiness when Phase2 status
  supplies a `quality_metrics_compare` artifact. It does not define new default
  quality thresholds.
- The generated default-promotion guard artifacts are diagnostics focused on
  the new quality-compare check. They are intentionally blocked overall because
  their Phase2 inputs are Gate360 quality-compare status fixtures, not full
  release-ready Phase2 status bundles.
- No real-data benchmark rerun was performed for this policy-handoff gate.

## Next Step

- Carry the same optional quality-compare handoff into the Windows release
  matrix and publish-preflight chain so release artifacts can preserve this
  quality-regression guard end to end.

## Clean-Room Compliance

- Compliant. This gate uses only GLASS-owned release-decision and Phase2 status
  JSON artifacts plus project-defined promotion policy.
- No PixInsight/WBPP/PJSR source, proprietary implementation details, user raw
  image directories, or external benchmark outputs were read or modified.
