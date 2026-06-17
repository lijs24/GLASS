# S2-Gate 232 Status

- Gate: S2-Gate 232
- Scope: Resident Rejection Sample Accounting Parity
- Status: green
- Date: 2026-06-18
- Commit: pending

## Completed

- Extended resident result-contract JSON checks so resident CUDA rejection
  provenance must record rejected-sample totals separately from DQ pixel counts.
- Required `dq_coverage_provenance.rejected_sample_count` and
  `dq_provenance_summary.rejected_samples` to agree when low/high rejection
  source terms are present.
- Extended `resident-result-contract --pixel-verify` so tiled reads of
  low/high rejection FITS maps verify finite, non-negative, near-integer count
  map values.
- Added pixel-verify accounting that compares rounded low/high rejection map
  sample sums against both resident rejected-sample provenance fields.
- Preserved DQ semantics: DQ low/high flags count pixels touched by rejection,
  while low/high rejection maps count rejected samples.
- Added positive, JSON sample-mismatch, fractional count-map, and sample-vs-DQ
  pixel tests.
- Updated pipeline-contract resident fixture to satisfy the new resident output
  contract evidence.
- Documented S2-Gate 232 in `docs/phase2_algorithm_hardening.md`.
- Added the clean-room algorithm-source entry in `docs/algorithm_sources.md`.

## Commands

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_resident_result_contract.py tests\\test_dq_map_verify.py`
- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\report\\resident_result_contract.py src\\glass\\report\\dq_map_verify.py tests\\test_resident_result_contract.py tests\\test_dq_map_verify.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_resident_result_contract.py tests\\test_dq_map_verify.py tests\\test_stack_engine_contract.py tests\\test_resident_cuda_run.py`
- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\report\\resident_result_contract.py src\\glass\\report\\dq_map_verify.py tests\\test_resident_result_contract.py tests\\test_dq_map_verify.py`
- `git diff --check`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_pipeline_contract.py`
- `.\\.venv\\Scripts\\ruff.exe check tests\\test_pipeline_contract.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\ruff.exe check .`
- `.\\.venv\\Scripts\\python.exe -c "import json; import glass_cuda; print(json.dumps({'cuda_available': bool(glass_cuda.cuda_available()), 'devices': glass_cuda.list_devices() if glass_cuda.cuda_available() else []}, ensure_ascii=False))"`

## Test Results

- Initial resident contract pytest: 10 passed in 0.34 s.
- Resident/DQ/StackEngine/resident CUDA targeted pytest: 62 passed in 5.01 s.
- Initial full pytest exposed four pipeline-contract fixture failures caused by
  old resident JSON fixtures missing rejected-sample provenance; the fixture was
  updated and retested before continuing.
- Pipeline-contract pytest after fix: 11 passed in 0.87 s.
- Full pytest after fix: 536 passed in 25.70 s.
- Full ruff: all checks passed.
- `git diff --check`: no whitespace errors; line-ending warnings only.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- CUDA kernels exercised by this gate: resident CUDA tests were included in the
  targeted suite; this gate changes result-contract validation, not CUDA math.

## Artifacts

- `runs/checkpoints/s2_gate_232_status.md`

## Known Limitations

- This gate does not change resident CUDA rejection kernels, runtime defaults,
  release packaging, or real 200-light benchmark outputs.
- Pixel-level rejected-sample verification requires `--pixel-verify` and
  available low/high rejection FITS maps; science-mode runs that intentionally
  skip those maps still rely on JSON provenance checks.

## Next Step

- Extend pipeline pixel verification with the same rejection sample accounting
  summary for all integration outputs, not only the resident-result-contract
  path, so guardrails can report sample-count parity directly.

## Clean-Room Compliance

- This gate used only GLASS code, GLASS tests, and GLASS documentation.
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or modified.
- No input image directory was modified.
