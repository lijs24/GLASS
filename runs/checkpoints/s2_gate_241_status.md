# S2 Gate 241 Status - Phase 2 Publish Preflight Rejection Status

- Gate: S2-Gate 241
- Status: green
- Date: 2026-06-18
- Created: 2026-06-18
- Scope: status/compare hardening only

## Completed

- Extended `glass phase2-status --publish-preflight` to preserve the Gate 240
  publish-preflight rejection sample accounting chain in Phase 2 status JSON.
- Added `windows_publish_preflight_rejection_sample_accounting_passed` so Phase 2
  status cannot stay green when a publish-preflight artifact is ready but lacks
  rejected-sample accounting evidence.
- Surfaced publish-preflight Phase 2, plan-matrix, direct matrix, and
  default-promotion accounting statuses and checks in Phase 2 Markdown.
- Extended `glass phase2-status-compare` with regression checks for
  publish-preflight rejection accounting checks and status preservation.
- Added tests for passing accounting, missing accounting, failed accounting,
  Markdown output, and compare regression detection.
- Updated Phase 2 gate documentation and algorithm-source tracking.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_phase2_status.py`
- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\report\\phase2_status.py tests\\test_phase2_status.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_phase2_status.py tests\\test_windows_publish_preflight.py`
- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\report\\phase2_status.py tests\\test_phase2_status.py docs\\phase2_algorithm_hardening.md docs\\algorithm_sources.md`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\ruff.exe check .`
- `.\\.venv\\Scripts\\python.exe -c "import json; import glass_cuda; available=bool(glass_cuda.cuda_available()); print(json.dumps({'cuda_available': available, 'devices': glass_cuda.list_devices() if available else []}, ensure_ascii=False))"`

## Test Results

- Phase 2 status targeted pytest: `14 passed in 0.36s`
- Gate 241 upstream/downstream targeted pytest: `20 passed in 0.39s`
- Full pytest: `550 passed in 26.08s`
- Ruff modified files: passed
- Ruff full repository: passed

## CUDA

- CUDA available: yes
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- Native backend: true

## Known Limitations

- This gate does not rebuild packages, upload a release, change image math,
  change CUDA kernels, change runtime defaults, or rerun the 200-light benchmark.
- Phase 2 status trusts the supplied publish-preflight artifact content, but now
  requires the Gate 240 accounting checks to be present and passing before green
  status can be preserved.

## Next Step

- Continue downstream release hardening if another publication artifact consumes
  Phase 2 status, or return to measured resident runtime/registration
  optimization work after this rejection-accounting handoff chain is closed.

## Clean-Room Compliance

- Compliant. This gate consumes GLASS-owned publish-preflight and Phase 2 status
  JSON artifacts only.
- No PixInsight, WBPP, PJSR, or proprietary implementation source was read,
  copied, summarized, or reworked.
- No input image directory was modified.
