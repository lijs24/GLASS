# S2-Gate 413 Status: Default-Promotion Publication-Audit Benchmark Profile Handoff

## Gate

S2-Gate 413

## Completed

- Carried S2-Gate412 Phase2 publication-audit benchmark profile chain into
  `glass default-promotion-manifest`.
- Added default-promotion check
  `stack_engine_publication_benchmark_profile_chain_passed`.
- Required raw publication-audit profile readiness, Phase2 profile readiness,
  Phase2/raw agreement, and the Phase2 benchmark-profile chain check before
  default promotion can pass.
- Surfaced raw and Phase2 publication-audit benchmark profile layers in
  default-promotion JSON and Markdown.
- Added focused tests for ready path, missing publication-audit evidence, and
  failed benchmark-profile chain.
- Updated Phase2 planning docs and the algorithm source ledger.

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests\test_default_promotion_manifest.py`
- `.venv\Scripts\python.exe -m ruff check src\glass\report\default_promotion_manifest.py tests\test_default_promotion_manifest.py`
- `.venv\Scripts\python.exe -m glass.cli default-promotion-manifest --help`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_413_cuda_doctor.json --allow-cpu-only`
- `git diff --check`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Result

- Focused default-promotion tests: `45 passed in 0.78s`
- Ruff: `All checks passed!`
- Full pytest: `981 passed in 39.29s`
- `git diff --check`: no whitespace errors; Git reported line-ending
  normalization warnings.

## CUDA

- CUDA available: yes
- Native extension loaded: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- Doctor artifact: `runs/checkpoints/s2_gate_413_cuda_doctor.json`

## Known Limitations

- This gate is default-promotion/report-contract only.
- It does not rerun the real 200-light benchmark.
- It does not change runtime execution, benchmark contract check semantics,
  CUDA kernels, registration math, quality metric math, DQ pixel semantics, or
  integration math.
- Default promotion now blocks when supplied Phase2 status lacks the
  publication-audit benchmark-profile chain evidence.

## Next Step

Continue Phase2 by carrying this default-promotion benchmark-profile
publication-audit evidence into the Windows release matrix if that layer still
does not enforce it.

## Clean-Room Compliance

- Only GLASS-owned source, tests, docs, and generated GLASS doctor/checkpoint
  artifacts were used.
- No PixInsight/WBPP/PJSR source was read, copied, summarized, or modified.
- No user image directory was modified or used for this gate.
