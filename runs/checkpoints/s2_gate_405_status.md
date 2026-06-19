# S2-Gate 405 Status

- Gate: S2-Gate 405
- Scope: Phase2 Status Benchmark Profile Evidence
- Status: green
- Date: 2026-06-19

## Completed

- Surfaced acceptance-audit benchmark contract source, path, profile, name, and
  schema version as first-class Phase2 status fields.
- Added the same benchmark contract metadata to default-route acceptance
  summaries.
- Updated Phase2 status Markdown so primary acceptance and default-route
  acceptance show the benchmark contract source/profile.
- Extended `phase2-status-compare` with
  `acceptance_benchmark_contract_profile_preserved`, preventing candidates from
  losing an acceptance benchmark profile present in the baseline status.
- Added tests for summary extraction, Markdown visibility, non-regression
  preservation, and profile-loss regression detection.
- Documented the gate in `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Commands

- `.\.venv\Scripts\python.exe -m ruff check src\glass\report\phase2_status.py tests\test_phase2_status.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_phase2_status.py`
- `.\.venv\Scripts\python.exe -m glass.cli phase2-status --help`
- `.\.venv\Scripts\python.exe -m glass.cli phase2-status-compare --help`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_405_cuda_doctor.json --allow-cpu-only`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Results

- Ruff: passed.
- Focused pytest: 99 passed in 1.38 s.
- CLI help: `phase2-status` and `phase2-status-compare` passed.
- Full pytest: 962 passed in 37.59 s.
- CUDA doctor JSON: `runs/checkpoints/s2_gate_405_cuda_doctor.json`.

## CUDA

- CUDA wrapper importable: yes.
- CUDA native extension loaded: yes.
- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Windows package try order: cuda13, cuda12, cuda11, cpu.

## Known Limitations

- This gate surfaces and guards acceptance benchmark profile evidence in status
  artifacts; it does not execute a new real-data benchmark.
- The compare guard preserves the profile identity when present in the
  baseline. It does not require a profile for older baseline statuses that lack
  one.
- No runtime execution behavior, benchmark contract check semantics, DQ pixel
  semantics, quality metric math, star detection, registration, integration,
  CUDA kernels, package artifacts, GitHub releases, or real-data benchmark
  outputs changed.

## Next Step

- Continue Phase 2 by carrying this benchmark profile evidence into release
  promotion/publication summaries, or return to resident runtime hardening for
  registration/warp orchestration and H2D pipeline efficiency.

## Clean-Room Compliance

- This gate used only GLASS-owned Phase2 status code, tests, generated doctor
  output, and GLASS fixture artifacts.
- It did not read PixInsight/WBPP/PJSR source code, proprietary implementation
  details, package contents, user image directories, or external reference
  outputs.
- Input image directories remain untouched.
