# S2-Gate445 Status: StackEngine Default Path Audit And Gap Closure

## Gate

S2-Gate445

## Result

Passed. `glass stack-engine-contract` now reports a stricter `default_path`
audit that separates native `stack_engine_cpu` default surfaces from resident
CUDA contract-emulation surfaces. CPU/tiled synthetic runs can pass the strict
native default gate, while resident CUDA remains contract-audited but explicitly
not strict-native StackEngine ready.

## Completed Work

- Added `default_path` to StackEngine contract audits.
- Added `--require-native-stack-engine-default` to `glass stack-engine-contract`.
- Preserved existing adoption/default-promotion fields for compatibility with
  older status/release tooling.
- Fixed resident calibration contract path resolution for:
  - absolute paths;
  - current-working-directory-relative artifact paths;
  - run-root-relative artifact paths.
- Prevented attached resident calibration contracts from duplicating
  per-master `calibration_artifacts.json` surfaces.
- Updated focused tests and docs.
- Updated `docs/algorithm_sources.md`.

## Commands Run

- `.\.venv\Scripts\python.exe -m ruff check src\glass\report\stack_engine_contract.py src\glass\report\resident_calibration_contract.py src\glass\cli.py tests\test_stack_engine_contract.py tests\test_resident_calibration_contract.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_stack_engine_contract.py tests\test_resident_calibration_contract.py`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_445_cuda_doctor.json`
- `.\.venv\Scripts\python.exe -m glass.cli synthetic --out runs\checkpoints\s2_gate_445_stackengine_work\cpu_synthetic\data --frames 3 --width 24 --height 24 --filter H`
- `.\.venv\Scripts\python.exe -m glass.cli audit --root runs\checkpoints\s2_gate_445_stackengine_work\cpu_synthetic\data --out runs\checkpoints\s2_gate_445_stackengine_work\cpu_synthetic\run --backend cpu --tile-size 8`
- `.\.venv\Scripts\python.exe -m glass.cli stack-engine-contract --run runs\checkpoints\s2_gate_445_stackengine_work\cpu_synthetic\run --out runs\checkpoints\s2_gate_445_cpu_native_stackengine_contract.json --markdown runs\checkpoints\s2_gate_445_cpu_native_stackengine_contract.md --require-native-stack-engine-default`
- `.\.venv\Scripts\python.exe -m glass.cli resident-calibration-contract --run runs\checkpoints\s2_gate_444_matrix_work\compatible_u16\run_default --out runs\checkpoints\s2_gate_445_resident_calibration_contract.json --markdown runs\checkpoints\s2_gate_445_resident_calibration_contract.md`
- `.\.venv\Scripts\python.exe -m glass.cli stack-engine-contract --run runs\checkpoints\s2_gate_444_matrix_work\compatible_u16\run_default --out runs\checkpoints\s2_gate_445_resident_contract_emulation.json --markdown runs\checkpoints\s2_gate_445_resident_contract_emulation.md --expected-integration-engine cuda_resident_stack --resident-calibration-contract-json runs\checkpoints\s2_gate_445_resident_calibration_contract.json --resident-result-contract-json runs\checkpoints\s2_gate_444_matrix_work\compatible_u16\run_default\resident_result_contract.json --require-native-stack-engine-default`
- `.\.venv\Scripts\python.exe -m pytest -q`

Expected nonzero validation:

- The resident `--require-native-stack-engine-default` command returned exit
  code `4`, proving the new strict-native gate rejects resident CUDA
  contract-emulation surfaces even when the normal contract passes.

## Test Results

- Focused StackEngine/resident calibration tests: `16 passed in 0.75s`
- Full suite: `1057 passed in 42.75s`
- Ruff: passed

## CUDA Availability

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- CUDA native extension: loaded
- Doctor artifact: `runs/checkpoints/s2_gate_445_cuda_doctor.json`

## Validation Artifacts

- CPU strict native StackEngine contract:
  `runs/checkpoints/s2_gate_445_cpu_native_stackengine_contract.json`
- CPU strict native StackEngine Markdown:
  `runs/checkpoints/s2_gate_445_cpu_native_stackengine_contract.md`
- Resident calibration contract:
  `runs/checkpoints/s2_gate_445_resident_calibration_contract.json`
- Resident calibration Markdown:
  `runs/checkpoints/s2_gate_445_resident_calibration_contract.md`
- Resident contract-emulation StackEngine contract:
  `runs/checkpoints/s2_gate_445_resident_contract_emulation.json`
- Resident contract-emulation Markdown:
  `runs/checkpoints/s2_gate_445_resident_contract_emulation.md`

## Key Evidence

CPU/tiled synthetic run:

- `default_path.status = native_stack_engine_ready`
- `strict_native_stack_engine_ready = true`
- Native StackEngine surfaces: 4
- Resident contract-emulation surfaces: 0
- Strict native gap count: 0

Resident CUDA synthetic run:

- `default_path.status = resident_cuda_contract_emulation`
- `strict_native_stack_engine_ready = false`
- Native StackEngine surfaces: 0
- Resident contract-emulation surfaces: 4
- Strict native gap count: 4
- Surfaces: 3 resident master-calibration surfaces and 1 resident integration
  surface.

## 200-Light Benchmark Note

The 200-light benchmark was not rerun for Gate445. This gate changes contract
classification and artifact path resolution only; it does not change image
math, frame admission, CUDA kernels, resident scheduling, registration, warp,
rejection, or output pixels. The current 200-light default-path performance
baseline remains Gate443:
`C:\glass_runs\final_m38_h_200\glass_s2_gate443_default_guarded_auto_warm_20260619_235200`.

## Known Limitations

- Resident CUDA is still not a strict native StackEngine backend. It is now
  explicitly classified as contract-emulation.
- The old `default_promotion` fields are preserved for compatibility and can
  still report ready for resident contract-emulation. The new authoritative
  strict gate for Phase 2 default-path work is `default_path`.
- The small CPU/resident run directories under
  `runs/checkpoints/s2_gate_445_stackengine_work` and the reused Gate444 work
  directory are local diagnostics and are not intended as committed golden data.

## Next Step

S2-Gate446 should start closing the resident strict gap by defining the minimal
resident CUDA StackEngine surface contract and comparing resident master/final
maps against CPU StackEngine fixtures without sacrificing the current resident
performance path.

## Source Boundary

This gate used GLASS source code, GLASS-generated synthetic fixtures, and
GLASS-generated resident/CPU contract artifacts. It did not read or derive code
from official PixInsight/WBPP/PJSR source, did not modify user image
directories, and did not create release or publication artifacts.
