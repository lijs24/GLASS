# S2 Gate 242 Status - StackEngine Invalid Sample Accounting Contract

- Gate: S2-Gate 242
- Status: green
- Date: 2026-06-18
- Created: 2026-06-18
- Scope: StackEngine/DQ result-contract hardening

## Completed

- Added StackEngine provenance fields:
  - `input_valid_samples_before_rejection`;
  - `input_invalid_samples_before_rejection`.
- Added StackEngine metrics:
  - `input_valid_samples`;
  - `input_invalid_samples`;
  - `rejected_samples`.
- Added result-contract checks proving:
  - initial valid plus initial invalid samples equals total input samples;
  - final valid samples plus low/high rejected samples equals initially valid
    samples;
  - StackEngine metrics match DQ provenance for input valid/invalid samples.
- Added tests proving DQ-flagged and non-finite input samples are invalid input
  samples and are not counted as rejected samples.
- Added a contract drift test for broken input/rejection sample closure.
- Updated Phase 2 gate documentation and algorithm-source tracking.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_stack_engine.py tests\\test_stack_engine_result_contract.py`
- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\engine\\stack_engine.py src\\glass\\engine\\stack_contract.py tests\\test_stack_engine.py tests\\test_stack_engine_result_contract.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_stack_engine.py tests\\test_stack_engine_result_contract.py tests\\test_pipeline_contract.py tests\\test_cpu_integration.py`
- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\engine\\stack_engine.py src\\glass\\engine\\stack_contract.py tests\\test_stack_engine.py tests\\test_stack_engine_result_contract.py docs\\phase2_algorithm_hardening.md docs\\algorithm_sources.md`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\ruff.exe check .`
- `.\\.venv\\Scripts\\python.exe -c "import json; import glass_cuda; available=bool(glass_cuda.cuda_available()); print(json.dumps({'cuda_available': available, 'devices': glass_cuda.list_devices() if available else []}, ensure_ascii=False))"`

## Test Results

- StackEngine targeted pytest: `17 passed in 0.11s`
- StackEngine/pipeline targeted pytest: `36 passed in 1.02s`
- Full pytest: `552 passed in 26.16s`
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
- The new accounting is currently enforced by the CPU StackEngine result
  contract; resident CUDA parity should continue to be verified through
  resident-result and pipeline-contract artifacts.

## Next Step

- Carry the same invalid-vs-rejected sample closure into resident CUDA result
  contracts or pipeline-contract summaries so the CPU StackEngine and resident
  paths expose the same DQ/rejection accounting vocabulary.

## Clean-Room Compliance

- Compliant. This gate uses GLASS-owned DQ bitfield and StackEngine semantics
  only.
- No PixInsight, WBPP, PJSR, or proprietary implementation source was read,
  copied, summarized, or reworked.
- No input image directory was modified.
