# S2-Gate 407 Status: Default Promotion Benchmark Profile Handoff

## Gate

S2-Gate 407: Default promotion benchmark profile handoff.

## Completed

- Added `benchmark_contract_profile_handoff` to
  `default-promotion-manifest`.
- Added release-blocking check
  `release_benchmark_contract_profile_handoff_passed`.
- Required the release decision, Phase2 acceptance summary, and default-route
  acceptance summary to agree on `resident_cuda_dq_v1` before default promotion
  can pass.
- Surfaced the benchmark profile handoff in default-promotion Markdown.
- Extended default-promotion tests for the ready path, Markdown visibility, and
  a legacy/wrong-profile blocker.
- Updated Phase 2 gate documentation and algorithm source audit notes.

## Commands Run

- `.\.venv\Scripts\python.exe -m ruff check src\glass\report\default_promotion_manifest.py tests\test_default_promotion_manifest.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_default_promotion_manifest.py`
- `.\.venv\Scripts\python.exe -m glass.cli default-promotion-manifest --help`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_407_cuda_doctor.json --allow-cpu-only`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Ruff focused check: passed.
- Focused default-promotion tests: `44 passed in 0.75s`.
- Full pytest: `964 passed in 37.98s`.

## CUDA Status

- CUDA wrapper importable: yes.
- CUDA native extension loaded: yes.
- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor artifact: `runs/checkpoints/s2_gate_407_cuda_doctor.json`.

## Known Limitations

- This gate is default-promotion-policy scoped. It does not rerun real-data
  benchmarks, change CUDA kernels, change runtime defaults, or change
  scientific algorithms.
- Legacy release-decision or Phase2/default-route artifacts that do not carry
  `resident_cuda_dq_v1` benchmark profile evidence will be blocked until
  regenerated with the resident CUDA DQ benchmark profile handoff.

## Next Step

- Continue propagating benchmark-profile evidence into Windows release matrix,
  publish preflight, and Phase2 publication-chain surfaces if any downstream
  publication path can still bypass the default-promotion manifest guard.

## Clean-Room Compliance

- Compliant. This gate consumed and modified only GLASS-owned JSON evidence
  contracts, tests, and documentation.
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or used.
- No user image directory or external benchmark output was read for this gate.
