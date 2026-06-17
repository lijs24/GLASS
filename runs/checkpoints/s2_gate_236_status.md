# S2-Gate 236 Status

- Gate: S2-Gate 236
- Scope: Phase 2 rejection sample status handoff
- Status: green
- Date: 2026-06-18

## Completed

- Added pipeline-contract rejection sample accounting summary to `glass phase2-status`.
- Surfaced `integration_rejection_sample_counts_match_maps` status, check presence,
  accounted/required/verified/failed row counts, failed output items, rejection-map
  sample totals, provenance source counts, and failed source deltas in Phase 2 status JSON.
- Added `pipeline_rejection_sample_accounting_passed` to Phase 2 status checks.
- Added `glass phase2-status-compare` regression checks for preserving rejection sample
  accounting check presence and passing status.
- Added Markdown output for rejection sample accounting status and failed mismatch rows.
- Updated Phase 2 and algorithm-source documentation.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_phase2_status.py`
- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\report\\phase2_status.py tests\\test_phase2_status.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_phase2_status.py tests\\test_acceptance_audit.py tests\\test_pipeline_contract.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\ruff.exe check .`
- `.\\.venv\\Scripts\\python.exe -c "import json; import glass_cuda; available=bool(glass_cuda.cuda_available()); print(json.dumps({'cuda_available': available, 'devices': glass_cuda.list_devices() if available else []}, ensure_ascii=False))"`

## Test Results

- Phase 2 status targeted pytest: `12 passed in 0.35s`
- Focused status/acceptance/pipeline pytest: `60 passed in 1.96s`
- Full pytest: `542 passed in 25.95s`
- Ruff: `All checks passed!`

## CUDA Availability

- CUDA available: yes
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- Total VRAM: 97886 MiB
- Driver: 596.21
- Native backend available to GLASS: yes

## Artifacts

- Updated `src/glass/report/phase2_status.py`
- Updated `tests/test_phase2_status.py`
- Updated `docs/phase2_algorithm_hardening.md`
- Updated `docs/algorithm_sources.md`
- Checkpoint: `runs/checkpoints/s2_gate_236_status.md`

## Known Limitations

- This gate summarizes and compares existing pipeline-contract evidence only.
- It does not change image math, CUDA kernels, runtime defaults, package artifacts, or real-data benchmark outputs.
- The pipeline contract remains the authoritative low-level pixel verification artifact.

## Next Step

- Carry the same rejection sample accounting evidence into the release-promotion/default-promotion
  decision layer so promotion cannot proceed if the Phase 2 status handoff reports drift.

## Clean-Room Compliance

- Compliant. This gate consumes and summarizes GLASS-owned JSON artifacts only.
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or reworked.
- No input image directory was modified.
