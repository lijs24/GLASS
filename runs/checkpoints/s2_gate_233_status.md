# S2-Gate 233 Status

- Gate: S2-Gate 233
- Scope: Pipeline Rejection Sample Pixel Handoff
- Status: green
- Date: 2026-06-18
- Commit: pending

## Completed

- Extended `glass pipeline-contract --pixel-verify` so integration pixel
  verification now emits `rejection_sample_accounting` rows.
- Pipeline pixel verification now treats low/high rejection FITS maps as
  finite, non-negative, near-integer rejected-sample count maps.
- Added direct pipeline comparison between rounded low/high rejection-map
  sample sums and available resident provenance or StackEngine metrics.
- Added top-level check `integration_rejection_sample_counts_match_maps` so
  pipeline guardrails fail when DQ touched-pixel counts match but rejected
  sample totals drift.
- Preserved DQ semantics: DQ low/high flags count pixels touched by rejection,
  while low/high rejection maps count rejected samples.
- Added resident pipeline pixel-verification tests for pass, JSON sample-count
  drift, and fractional rejection-map values.
- Documented S2-Gate 233 in `docs/phase2_algorithm_hardening.md`.
- Added the clean-room algorithm-source entry in `docs/algorithm_sources.md`.

## Commands

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_pipeline_contract.py tests\\test_resident_result_contract.py tests\\test_dq_map_verify.py`
- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\report\\pipeline_contract.py tests\\test_pipeline_contract.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_pipeline_contract.py tests\\test_resident_result_contract.py tests\\test_stack_engine_contract.py tests\\test_cli_smoke.py`
- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\report\\pipeline_contract.py src\\glass\\report\\dq_map_verify.py tests\\test_pipeline_contract.py`
- `git diff --check`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\ruff.exe check .`
- `.\\.venv\\Scripts\\python.exe -c "import json; import glass_cuda; print(json.dumps({'cuda_available': bool(glass_cuda.cuda_available()), 'devices': glass_cuda.list_devices() if glass_cuda.cuda_available() else []}, ensure_ascii=False))"`

## Test Results

- Pipeline/resident/DQ targeted pytest: 24 passed in 1.15 s.
- Pipeline/StackEngine/CLI targeted pytest: 54 passed in 3.70 s.
- Targeted ruff: all checks passed.
- `git diff --check`: no whitespace errors; line-ending warnings only.
- Full pytest: 539 passed in 25.97 s.
- Full ruff: all checks passed.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- CUDA kernels exercised by this gate: no new CUDA kernel math; this gate
  changes pipeline-contract verification and reporting.

## Artifacts

- `runs/checkpoints/s2_gate_233_status.md`

## Known Limitations

- This gate does not change integration math, CUDA kernels, resident runtime
  defaults, release packaging, or real 200-light benchmark outputs.
- Pipeline sample-count pixel verification requires `--pixel-verify` and
  available low/high rejection FITS maps. Runs that skip those maps still rely
  on JSON contract checks from StackEngine or resident result-contract paths.

## Next Step

- Surface pipeline rejection sample accounting in HTML/guardrail report tables
  so failures are visible without opening the raw pipeline-contract JSON.

## Clean-Room Compliance

- This gate used only GLASS code, GLASS tests, and GLASS documentation.
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or modified.
- No input image directory was modified.
