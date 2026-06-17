# S2 Gate 243 Status - DQ Provenance Sample Closure Handoff

- Gate: S2-Gate 243
- Status: green
- Date: 2026-06-18
- Created: 2026-06-18
- Scope: DQ provenance/report-contract handoff

## Completed

- Extended StackEngine DQ provenance summaries with:
  - `input_valid_samples_before_rejection`;
  - `input_invalid_samples_before_rejection`;
  - `valid_samples_after_rejection`;
  - `low_rejected_samples`;
  - `high_rejected_samples`;
  - `rejected_samples`;
  - `sample_accounting_closure`.
- Added matching sample totals to raw StackEngine DQ provenance so summaries do
  not need to infer them from result contracts.
- Added resident coverage `rounded_sum` statistics so resident pre/post
  rejection coverage can expose sample sums in future artifacts.
- Extended resident DQ provenance summaries with optional
  `sample_accounting_closure`.
- Extended resident result contracts to accept old artifacts with missing sample
  closure while failing artifacts that explicitly report failed closure.
- Added DQ provenance and resident result-contract tests for passing and failed
  closure evidence.
- Updated Phase 2 gate documentation and algorithm-source tracking.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_dq_provenance.py tests\\test_stack_engine.py tests\\test_stack_engine_result_contract.py tests\\test_resident_result_contract.py`
- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\engine\\dq.py src\\glass\\engine\\stack_engine.py src\\glass\\engine\\resident_cuda.py src\\glass\\report\\resident_result_contract.py tests\\test_dq_provenance.py tests\\test_resident_result_contract.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_dq_provenance.py tests\\test_resident_result_contract.py tests\\test_pipeline_contract.py tests\\test_acceptance_audit.py tests\\test_stack_engine.py tests\\test_stack_engine_result_contract.py`
- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\engine\\dq.py src\\glass\\engine\\stack_engine.py src\\glass\\engine\\resident_cuda.py src\\glass\\report\\resident_result_contract.py tests\\test_dq_provenance.py tests\\test_resident_result_contract.py docs\\phase2_algorithm_hardening.md docs\\algorithm_sources.md`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\ruff.exe check .`
- `.\\.venv\\Scripts\\python.exe -c "import json; import glass_cuda; available=bool(glass_cuda.cuda_available()); print(json.dumps({'cuda_available': available, 'devices': glass_cuda.list_devices() if available else []}, ensure_ascii=False))"`

## Test Results

- DQ/resident/StackEngine targeted pytest: `29 passed in 0.51s`
- DQ/resident/pipeline/acceptance targeted pytest: `77 passed in 2.09s`
- Full pytest: `554 passed in 26.36s`
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

- This gate does not change image math, CUDA kernels, runtime defaults, package
  builds, upload behavior, or the 200-light benchmark artifacts.
- Resident sample closure remains optional for older resident artifacts. New
  resident artifacts can expose coverage `rounded_sum` values and will be
  checked when they provide `sample_accounting_closure`.

## Next Step

- Promote sample-closure visibility into pipeline-contract and HTML report
  summaries so auditors can see invalid-vs-rejected sample closure without
  opening raw DQ provenance JSON.

## Clean-Room Compliance

- Compliant. This gate uses GLASS-owned DQ provenance and resident result
  contract semantics only.
- No PixInsight, WBPP, PJSR, or proprietary implementation source was read,
  copied, summarized, or reworked.
- No input image directory was modified.
