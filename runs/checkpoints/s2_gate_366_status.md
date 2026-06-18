# S2-Gate 366 Status: Release Promotion Decision Quality Metric Compare Guard

## Gate

- Gate: S2-Gate 366
- Title: Release Promotion Decision Quality Metric Compare Guard
- Date: 2026-06-19
- Status: green

## Completed

- Added release-decision evidence extraction for StackEngine publication-audit
  `quality_metrics_compare` layers.
- Added release-blocking check
  `stack_engine_publication_quality_metrics_compare_passed`.
- Preserved compatibility for older StackEngine publication-audit artifacts that
  do not contain optional quality compare layers/checks.
- Blocked release-candidate readiness when supplied quality compare evidence is
  failed or raw/Phase2 publication-audit evidence diverges.
- Surfaced publication quality compare status in release-promotion Markdown.
- Added focused tests for ready, missing-compatible, failed, Phase2 mismatch,
  and CLI Markdown paths.
- Updated Phase 2 plan and algorithm-source audit documentation.

## Commands

- `.\.venv\Scripts\python.exe -m ruff check src\glass\report\release_promotion_decision.py tests\test_release_promotion_decision.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_release_promotion_decision.py`
- `.\.venv\Scripts\python.exe -m glass.cli release-promotion-decision ... --out runs\checkpoints\s2_gate_366_release_promotion_quality_compare_pass.json --markdown runs\checkpoints\s2_gate_366_release_promotion_quality_compare_pass.md`
- `.\.venv\Scripts\python.exe -m glass.cli release-promotion-decision ... --out runs\checkpoints\s2_gate_366_release_promotion_quality_compare_missing.json --markdown runs\checkpoints\s2_gate_366_release_promotion_quality_compare_missing.md`
- `.\.venv\Scripts\python.exe -m glass.cli release-promotion-decision ... --out runs\checkpoints\s2_gate_366_release_promotion_quality_compare_failed.json --markdown runs\checkpoints\s2_gate_366_release_promotion_quality_compare_failed.md`
- `.\.venv\Scripts\python.exe -m glass.cli release-promotion-decision ... --out runs\checkpoints\s2_gate_366_release_promotion_quality_compare_mismatch.json --markdown runs\checkpoints\s2_gate_366_release_promotion_quality_compare_mismatch.md`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_366_cuda_doctor.json --allow-cpu-only`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused release-decision tests: 24 passed.
- Full suite: 835 passed in 34.86 s.
- Ruff: all checks passed.
- Negative fixture CLI runs returned non-zero status while writing `blocked`
  release-decision artifacts, as expected.

## CUDA

- CUDA wrapper importable: true.
- CUDA native extension loaded: true.
- CUDA available: true.
- GPU 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor artifact: `runs/checkpoints/s2_gate_366_cuda_doctor.json`.

## Artifacts

- `runs/checkpoints/s2_gate_366_fixtures/`
- `runs/checkpoints/s2_gate_366_release_promotion_quality_compare_pass.json`
- `runs/checkpoints/s2_gate_366_release_promotion_quality_compare_pass.md`
- `runs/checkpoints/s2_gate_366_release_promotion_quality_compare_missing.json`
- `runs/checkpoints/s2_gate_366_release_promotion_quality_compare_missing.md`
- `runs/checkpoints/s2_gate_366_release_promotion_quality_compare_failed.json`
- `runs/checkpoints/s2_gate_366_release_promotion_quality_compare_failed.md`
- `runs/checkpoints/s2_gate_366_release_promotion_quality_compare_mismatch.json`
- `runs/checkpoints/s2_gate_366_release_promotion_quality_compare_mismatch.md`
- `runs/checkpoints/s2_gate_366_cuda_doctor.json`

## Known Limitations

- This gate is a release-decision guard only; it does not change quality metric
  math, thresholds, star detection, registration, integration, CUDA kernels,
  runtime defaults, packaging, or GitHub release publication.
- The compatibility path intentionally allows older publication-audit artifacts
  with no quality compare evidence. Once quality compare layers/checks are
  present, they must be ready.
- No real-data benchmark was rerun for this gate.

## Next Step

- Continue the Phase 2 publication chain by carrying the final release-decision
  quality compare guard into the next downstream release/default-promotion
  artifact, or move from guard hardening back to measured GPU pipeline work when
  the release chain is sufficiently closed.

## Clean-Room Compliance

- The gate consumes GLASS-owned JSON artifacts only.
- It does not read image pixels, user raw image directories, external
  implementation source, proprietary code, package contents, or reference
  outputs.
- It does not inspect or summarize PixInsight/WBPP/PJSR source.
