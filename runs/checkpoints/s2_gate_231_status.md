# S2-Gate 231 Status

- Gate: S2-Gate 231
- Scope: StackEngine Rejection Sample Accounting Contract
- Status: green
- Date: 2026-06-18
- Commit: pending

## Completed

- Extended `build_stack_engine_result_contract` so low/high rejection maps are
  validated as per-pixel rejected-sample count maps.
- Added checks that rejection count maps are finite, non-negative, and
  near-integer.
- Added checks that rounded low/high rejection map sums match
  `metrics.low_rejected` and `metrics.high_rejected`.
- Added checks that rejection-map positive-pixel counts match DQ provenance
  `output_low_rejected_pixels` and `output_high_rejected_pixels`.
- Preserved the existing DQ semantics: DQ low/high flags mark pixels touched by
  rejection, not rejected-sample totals.
- Added focused tests for the case where two high-rejected samples occur in the
  same output pixel, plus a negative test for sample-metric drift.
- Documented the gate in `docs/phase2_algorithm_hardening.md`.
- Added the clean-room algorithm-source entry in `docs/algorithm_sources.md`.

## Commands

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_stack_engine_result_contract.py tests\\test_stack_engine.py`
- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\engine\\stack_contract.py tests\\test_stack_engine_result_contract.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_stack_engine_result_contract.py tests\\test_stack_engine.py tests\\test_stack_engine_contract.py`
- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\engine\\stack_contract.py tests\\test_stack_engine_result_contract.py`
- `git diff --check`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\ruff.exe check .`
- `.\\.venv\\Scripts\\python.exe -c "import json; import glass_cuda; print(json.dumps({'cuda_available': bool(glass_cuda.cuda_available()), 'devices': glass_cuda.list_devices() if glass_cuda.cuda_available() else []}, ensure_ascii=False))"`

## Test Results

- Targeted StackEngine result/engine pytest: 15 passed in 0.08 s.
- Targeted StackEngine contract pytest: 26 passed in 0.61 s.
- Targeted ruff: all checks passed.
- `git diff --check`: no whitespace errors; line-ending warnings only.
- Full pytest: 532 passed in 25.92 s.
- Full ruff: all checks passed.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- CUDA kernels exercised by this gate: no; this gate hardens CPU/StackEngine
  contract validation only.

## Artifacts

- `runs/checkpoints/s2_gate_231_status.md`

## Known Limitations

- This gate does not change image math, CUDA kernels, resident CUDA result
  generation, runtime defaults, release packaging, or real-data benchmark
  artifacts.
- Resident CUDA parity still depends on resident result contracts carrying the
  same sample-count versus touched-pixel distinction.

## Next Step

- Continue algorithm hardening by applying the same sample-versus-pixel
  accounting discipline to resident CUDA result-contract evidence and pipeline
  DQ handoff checks.

## Clean-Room Compliance

- This gate used only GLASS code, GLASS tests, and GLASS documentation.
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or modified.
- No input image directory was modified.
