# S2-Gate 416 Status: Resident Result-Contract Path Resolution

## Gate

S2-Gate 416: Resident Result-Contract Path Resolution.

## Why This Gate Exists

S2-Gate 415 proved the most important synthetic resident validation split:

- resident triangle registration still chose a different reference frame and produced large image differences;
- resident `external_matrix` using CPU registration results plus hardened winsorized rejection reached near numerical parity;
- that near-parity run was still blocked because the resident result contract could not resolve map paths written by GLASS as current-working-directory-relative paths.

Gate416 fixes that concrete runtime-validation blocker so the next optimization gate can rely on automated contract/parity status instead of manual inspection.

## Gate400-413 Core-Goal Value Summary

- Gate400-413 mostly hardened release, default-promotion, publication-audit, and benchmark-profile evidence handoff.
- Their real value for the core Phase 2 target is limited but not zero: they prevent a future release from hiding a missing `resident_cuda_dq_v1` acceptance chain, DQ contract profile, or publication evidence mismatch.
- They did not improve StackEngine default routing, DQ pixel semantics, registration, CUDA resident performance, or 200-light numerical agreement directly.
- Gate414 correctly stopped that report/contract-only chain and returned work to runtime validation.

## Completed Work

- Updated `src/glass/report/resident_result_contract.py` path resolution.
- The resolver now accepts absolute paths, existing run-root-relative paths, and existing current-working-directory-relative paths.
- Added a regression test covering cwd-relative resident map paths in `tests/test_resident_result_contract.py`.
- Regenerated compact Gate416 resident result-contract and parity-summary artifacts from the S2-Gate 415 external-transform CUDA resident run.
- Updated Phase 2 gate documentation and algorithm-source audit notes.

## Validation Commands

- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_result_contract.py`
- `.venv\Scripts\python.exe -m ruff check src\glass\report\resident_result_contract.py tests\test_resident_result_contract.py`
- `.venv\Scripts\python.exe -m glass.cli resident-result-contract --run runs\checkpoints\s2_gate_415_runtime_validation_cuda_external_cpu_transform --out runs\checkpoints\s2_gate_415_runtime_validation_cuda_external_cpu_transform\resident_result_contract.json --markdown runs\checkpoints\s2_gate_415_runtime_validation_cuda_external_cpu_transform\resident_result_contract.md --pixel-verify --pixel-verify-tile-size 128 --fail-on-failed`
- `.venv\Scripts\python.exe -m glass.cli resident-result-contract --run runs\checkpoints\s2_gate_415_runtime_validation_cuda_external_cpu_transform --out runs\checkpoints\s2_gate_416_external_cpu_transform_resident_result_contract.json --markdown runs\checkpoints\s2_gate_416_external_cpu_transform_resident_result_contract.md --pixel-verify --pixel-verify-tile-size 128 --fail-on-failed`
- `.venv\Scripts\python.exe -m glass.cli resident-parity-summary --cpu-run runs\checkpoints\s2_gate_414_runtime_validation_cpu --resident-run runs\checkpoints\s2_gate_415_runtime_validation_cuda_external_cpu_transform --compare-json runs\checkpoints\s2_gate_415_external_cpu_transform_compare.json --out runs\checkpoints\s2_gate_416_external_cpu_transform_parity_summary.json --markdown runs\checkpoints\s2_gate_416_external_cpu_transform_parity_summary.md --resident-label cuda_resident_external_cpu_transform --max-rms-diff 0.1 --max-relative-rms-diff 0.001 --max-rejected-sample-delta 64 --fail-on-failure`

Additional verification is run before commit:

- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_result_contract.py tests\test_resident_parity_summary.py`
- `.venv\Scripts\python.exe -m ruff check src\glass\report\resident_result_contract.py tests\test_resident_result_contract.py src\glass\report\resident_parity_summary.py tests\test_resident_parity_summary.py`
- `.venv\Scripts\python.exe -m glass.cli resident-result-contract --help`
- `.venv\Scripts\python.exe -m glass.cli resident-parity-summary --help`
- `.venv\Scripts\python.exe -m glass.cli doctor`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused result-contract test before checkpoint: `14 passed in 0.45s`.
- Focused ruff before checkpoint: passed.
- Final focused tests: `17 passed in 0.55s`.
- Final ruff check: passed.
- CLI help checks for `resident-result-contract` and `resident-parity-summary`: passed.
- Full test suite: `985 passed in 38.25s`.

## Runtime / Numerical Validation

Using the synthetic 16-frame external-matrix resident validation from S2-Gate 415:

- CPU tiled elapsed: `41.93859020000673 s`.
- CUDA resident external-transform elapsed: `0.2904634000151418 s`.
- CPU reference frame: `F000016`.
- CUDA resident external-transform reference frame: `F000016`.
- RMS diff: `0.06858672377130552`.
- Relative RMS diff: `0.0003118613896233379`.
- P99 absolute diff: `0.1982856750488282`.
- Rejected sample delta: `-19`.
- Parity summary status after Gate416 fix: `passed`.
- Resident result-contract status after Gate416 fix: `passed`.

## CUDA Availability

- CUDA was available for the validation run.
- Doctor result: CUDA wrapper importable, native extension loaded, CUDA available.
- Recorded GPU from this environment: NVIDIA RTX PRO 6000 Blackwell Workstation Edition, compute capability 12.0, driver 596.21, VRAM approximately 97886 MiB.

## Artifacts

- `runs/checkpoints/s2_gate_416_external_cpu_transform_resident_result_contract.json`
- `runs/checkpoints/s2_gate_416_external_cpu_transform_resident_result_contract.md`
- `runs/checkpoints/s2_gate_416_external_cpu_transform_parity_summary.json`
- `runs/checkpoints/s2_gate_416_external_cpu_transform_parity_summary.md`
- `runs/checkpoints/s2_gate_416_status.md`

## Known Limitations

- This gate uses the existing synthetic 16-frame validation, not the 200-light real-data benchmark.
- It does not fix resident triangle registration/reference selection.
- It does not change CUDA kernels, resident memory residency, StackEngine default routing, or integration math.
- LN remains disabled in this focused validation.

## Next Gate

The next substantive gate should fix the resident default registration/reference path so the resident CUDA run can reach parity without external CPU transform handoff. After that, rerun the 200-light real-data benchmark under the resident CUDA path and compare timing plus output maps against the accepted CPU/WBPP reference chain.

## Clean-Room Compliance

Compliant. This gate used only GLASS-owned code, GLASS-generated artifacts, and synthetic validation outputs. It did not read or derive from proprietary implementation source and did not modify user image directories.
