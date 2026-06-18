# S2-Gate 367 Status: Default Promotion Release Quality Compare Guard

## Gate

- Gate: S2-Gate 367
- Title: Default Promotion Release Quality Compare Guard
- Date: 2026-06-19
- Status: green

## Completed

- Added default-promotion evidence extraction for release-decision
  `stack_engine_publication_quality_metrics_compare`.
- Added default-promotion blocker
  `release_decision_quality_compare_publication_guard_passed`.
- Preserved compatibility for older release-decision artifacts without the
  optional quality compare publication guard.
- Blocked default promotion when supplied release-decision quality compare
  evidence is failed or raw/Phase2 evidence diverges.
- Surfaced release quality compare publication guard details in
  default-promotion Markdown.
- Added focused tests for ready, missing-compatible, failed, Phase2 mismatch,
  and CLI Markdown paths.
- Updated Phase 2 plan and algorithm-source audit documentation.

## Commands

- `.\.venv\Scripts\python.exe -m ruff check src\glass\report\default_promotion_manifest.py tests\test_default_promotion_manifest.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_default_promotion_manifest.py`
- `.\.venv\Scripts\python.exe -m glass.cli default-promotion-manifest ... --out runs\checkpoints\s2_gate_367_default_promotion_quality_guard_pass.json --markdown runs\checkpoints\s2_gate_367_default_promotion_quality_guard_pass.md`
- `.\.venv\Scripts\python.exe -m glass.cli default-promotion-manifest ... --out runs\checkpoints\s2_gate_367_default_promotion_quality_guard_missing.json --markdown runs\checkpoints\s2_gate_367_default_promotion_quality_guard_missing.md`
- `.\.venv\Scripts\python.exe -m glass.cli default-promotion-manifest ... --out runs\checkpoints\s2_gate_367_default_promotion_quality_guard_failed.json --markdown runs\checkpoints\s2_gate_367_default_promotion_quality_guard_failed.md`
- `.\.venv\Scripts\python.exe -m glass.cli default-promotion-manifest ... --out runs\checkpoints\s2_gate_367_default_promotion_quality_guard_mismatch.json --markdown runs\checkpoints\s2_gate_367_default_promotion_quality_guard_mismatch.md`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_367_cuda_doctor.json --allow-cpu-only`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused default-promotion tests: 29 passed.
- Full suite: 838 passed in 34.83 s.
- Ruff: all checks passed.
- CLI fixture outcomes:
  - pass: `default_promotion_ready`
  - missing quality guard: `default_promotion_ready`
  - failed quality guard: `blocked`
  - Phase2 quality mismatch: `blocked`

## CUDA

- CUDA wrapper importable: true.
- CUDA native extension loaded: true.
- CUDA available: true.
- GPU 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor artifact: `runs/checkpoints/s2_gate_367_cuda_doctor.json`.

## Artifacts

- `runs/checkpoints/s2_gate_367_fixtures/`
- `runs/checkpoints/s2_gate_367_default_promotion_quality_guard_pass.json`
- `runs/checkpoints/s2_gate_367_default_promotion_quality_guard_pass.md`
- `runs/checkpoints/s2_gate_367_default_promotion_quality_guard_missing.json`
- `runs/checkpoints/s2_gate_367_default_promotion_quality_guard_missing.md`
- `runs/checkpoints/s2_gate_367_default_promotion_quality_guard_failed.json`
- `runs/checkpoints/s2_gate_367_default_promotion_quality_guard_failed.md`
- `runs/checkpoints/s2_gate_367_default_promotion_quality_guard_mismatch.json`
- `runs/checkpoints/s2_gate_367_default_promotion_quality_guard_mismatch.md`
- `runs/checkpoints/s2_gate_367_cuda_doctor.json`

## Known Limitations

- This gate is a default-promotion guard only; it does not change quality metric
  math, thresholds, star detection, registration, integration, CUDA kernels,
  runtime defaults, packaging, or GitHub release publication.
- The compatibility path intentionally allows older release-decision artifacts
  with no quality compare publication guard. Once the guard appears, it must be
  ready.
- No real-data benchmark was rerun for this gate.

## Next Step

- Continue the publication chain by carrying default-promotion release quality
  guard evidence into the Windows release matrix, or switch back to measured GPU
  pipeline optimization if the guard chain is sufficiently closed.

## Clean-Room Compliance

- The gate consumes GLASS-owned JSON artifacts only.
- It does not read image pixels, user raw image directories, external
  implementation source, proprietary code, package contents, or reference
  outputs.
- It does not inspect or summarize PixInsight/WBPP/PJSR source.
