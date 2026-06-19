# S2-Gate 406 Status: Release Promotion Benchmark Profile Evidence

## Gate

S2-Gate 406: Release promotion benchmark profile evidence.

## Completed

- Added release-promotion evidence extraction for the acceptance audit benchmark
  contract source, path, profile, name, schema version, and required profile.
- Added release-blocking check `acceptance_benchmark_contract_profile`.
- Required release candidates to carry the built-in `resident_cuda_dq_v1`
  acceptance benchmark profile before `release_candidate_ready` can pass.
- Surfaced benchmark profile evidence in release-promotion Markdown.
- Added focused tests for the ready path and the missing/wrong-profile blocker.
- Updated Phase 2 gate documentation and algorithm source audit notes.

## Commands Run

- `.\.venv\Scripts\python.exe -m ruff check src\glass\report\release_promotion_decision.py tests\test_release_promotion_decision.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_release_promotion_decision.py`
- `.\.venv\Scripts\python.exe -m glass.cli release-promotion-decision --help`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_406_cuda_doctor.json --allow-cpu-only`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Ruff focused check: passed.
- Focused release-promotion tests: `39 passed in 0.54s`.
- Full pytest: `963 passed in 37.61s`.

## CUDA Status

- CUDA wrapper importable: yes.
- CUDA native extension loaded: yes.
- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor artifact: `runs/checkpoints/s2_gate_406_cuda_doctor.json`.

## Known Limitations

- This gate is release-policy scoped. It does not rerun real-data benchmarks,
  change CUDA kernels, change runtime defaults, or change scientific algorithms.
- The release-promotion decision now requires the resident CUDA DQ benchmark
  profile evidence to be present in the supplied acceptance audit.
- Existing legacy acceptance artifacts without `benchmark_contract.profile` will
  be blocked until regenerated with `--benchmark-contract-profile
  resident_cuda_dq_v1` or equivalent explicit profile evidence.

## Next Step

- Continue the Phase 2 release evidence chain by propagating this benchmark
  profile guard into downstream release/default-promotion surfaces if any path
  can still bypass `release-promotion-decision`.

## Clean-Room Compliance

- Compliant. This gate consumed and modified only GLASS-owned JSON evidence
  contracts, tests, and documentation.
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or used.
- No user image directory or external benchmark output was read for this gate.
