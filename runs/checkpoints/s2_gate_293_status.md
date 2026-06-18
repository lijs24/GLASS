# S2-Gate 293 Status: Pipeline Contract StackEngine Runtime Default Surface

Status: green

## Gate

S2-Gate 293 returns from publication-chain closure to runtime artifact
hardening by extending `glass pipeline-contract` with a combined StackEngine
runtime-default surface.

## Completed Work

- Extended `src/glass/report/pipeline_contract.py` with
  `stack_engine_runtime_default_path`.
- Added a `stack_engine_runtime_default` JSON section summarizing:
  - StackEngine CPU master count
  - resident CUDA master count
  - legacy master count
  - StackEngine default integration output count
  - resident integration output count
  - explicit CUDA fast-path output count
  - failed master/output runtime-default rows
- The new check blocks legacy master accumulator artifacts even when their
  master science metadata is otherwise valid.
- The existing explicit opt-in CUDA streaming accumulator path remains allowed
  and is counted separately from true StackEngine default outputs.
- Extended pipeline-contract Markdown with a `StackEngine Runtime Default Path`
  section.
- Updated `tests/test_pipeline_contract.py` with focused coverage for:
  - a real tiny synthetic CPU audit run
  - an explicit non-resident CUDA fast-path artifact
  - a legacy-master runtime-default regression
- Documented the gate in `docs/phase2_algorithm_hardening.md`.
- Added an algorithm-source entry in `docs/algorithm_sources.md`.

## Generated Artifacts

- `runs/checkpoints/s2_gate_293_pipeline_contract_stack_engine_runtime_default_ready.json`
- `runs/checkpoints/s2_gate_293_pipeline_contract_stack_engine_runtime_default_ready.md`
- `runs/checkpoints/s2_gate_293_pipeline_contract_stack_engine_runtime_default_explicit_cuda.json`
- `runs/checkpoints/s2_gate_293_pipeline_contract_stack_engine_runtime_default_explicit_cuda.md`
- `runs/checkpoints/s2_gate_293_pipeline_contract_stack_engine_runtime_default_legacy_master.json`
- `runs/checkpoints/s2_gate_293_pipeline_contract_stack_engine_runtime_default_legacy_master.md`

Artifact outcomes:

- synthetic CPU audit ready: `passed=true`, failed checks `[]`
- explicit CUDA fast path: `passed=true`, failed checks `[]`,
  `explicit_cuda_fast_path_count=1`
- legacy master accumulator: `passed=false`, failed check
  `stack_engine_runtime_default_path`

Temporary fixture paths were scrubbed to `GATE293_FIXTURE`, and the temporary
fixture directory was removed.

## Commands Run

- `.venv\Scripts\ruff.exe check src\glass\report\pipeline_contract.py tests\test_pipeline_contract.py`
- `.venv\Scripts\python.exe -m pytest -q tests/test_pipeline_contract.py`
- `git diff --check`
- `.venv\Scripts\python.exe -m pytest -q`
- CUDA capability probe through `glass.capabilities.capability_report()` and
  `glass.gpu.device.list_devices()`

## Test Results

- Ruff: passed
- Focused pytest: `21 passed in 1.04s`
- Full pytest: `673 passed in 33.43s`
- `git diff --check`: passed with CRLF normalization warnings only

## CUDA

CUDA available: yes

Detected GPU:

- Name: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Multiprocessors: 188
- Native backend: true
- Driver version: 596.21

## Real Data

No user real image directory was read or modified for this gate. The ready
artifact uses a tiny synthetic CPU audit run generated under a temporary
checkpoint fixture and then removed after scrubbed audit artifacts were written.

## Known Limitations

- No image math, CUDA kernels, runtime defaults, package artifacts, GitHub
  release creation, uploads, or 200-light benchmark outputs were changed.
- The new runtime-default surface audits existing artifacts; it does not rerun a
  real-data benchmark or independently recompute calibration/integration outputs.
- Explicit non-resident CUDA streaming accumulator diagnostics remain allowed
  when the integration engine policy records the opt-in.

## Next Step

S2-Gate 294 should propagate the new pipeline-contract runtime-default surface
into acceptance/Phase 2 status evidence, or return to the next calibration,
quality, registration, LN, rejection, report, or real-data regression hardening
item with this runtime-default check as a reusable guardrail.

## Clean-Room Compliance

Compliant. The gate uses GLASS-owned pipeline contract code, GLASS synthetic
fixtures, and GLASS run artifacts only. No external or proprietary source code
was read, summarized, copied, or used.
