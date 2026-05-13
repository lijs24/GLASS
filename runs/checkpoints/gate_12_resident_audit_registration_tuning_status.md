# Gate 12 Status: Resident Audit Registration Tuning

## Gate

Gate 12: End-to-end CUDA audit reproducibility increment.

## Completed

- Extended `glass audit --memory-mode resident` so it can pass the resident registration tuning parameters used by detailed real-data runs.
- Added audit options:
  - `--resident-ncc-sample-stride`
  - `--resident-ncc-fallback-score-threshold`
  - `--resident-subpixel-radius-steps`
  - `--resident-subpixel-step`
  - `--resident-star-threshold`
  - `--resident-star-max-candidates`
  - `--resident-star-tolerance-px`
  - `--resident-star-grid-cols`
  - `--resident-star-grid-rows`
  - `--resident-star-prior`
  - `--resident-star-prior-radius-px`
  - `--resident-star-core-preselect-top-k`
- Verified the resident audit smoke test records these values into `resident_artifacts.json`.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\cli.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_cli_audit_resident_cuda_smoke tests\test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\glass.exe audit --help
.\.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Result

- Targeted audit/help tests: `2 passed`.
- CLI/resident subset: `18 passed`.
- Full pytest: `175 passed in 8.36s`.
- Ruff: passed.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: true.

## Known Limitations

- Resident audit still intentionally exposes only stable resident controls. Very specialized debug switches should remain on `glass run` unless needed for reproducible benchmark workflows.

## Next Step

- Reuse resident audit for real-data benchmark reruns when a complete scan/plan/run/report artifact is preferred over the lower-level `glass run` command.

## Clean-room

- Compliant. No official PixInsight/WBPP/PJSR source was read or copied.
