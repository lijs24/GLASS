# Gate 12 Status: Resident CUDA Audit Entry

## Gate

Gate 12: End-to-end CUDA WBPP-like pipeline entrypoint increment.

## Completed

- Added `glass audit --memory-mode resident` so scan -> plan -> resident CUDA run -> report can be executed as one command.
- Resident audit currently requires `--backend cuda` and uses the same resident CUDA calibration/integration engine as `glass run`.
- Exposed key resident audit controls:
  - `--resident-registration`
  - `--resident-registration-results`
  - `--resident-warp-interpolation`
  - `--resident-warp-clamping-threshold`
  - `--resident-registration-max-shift`
  - `--resident-local-normalization-mode`
  - `--resident-local-normalization-tile-size`
  - `--reference-frame-id`
  - repeated `--exclude-frame-id`
- Added CLI smoke coverage that verifies resident audit writes manifest, plan, resident artifacts, integration results, report, timing, and run state.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\cli.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_cli_audit_resident_cuda_smoke tests\test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe audit --help
.\.venv\Scripts\python.exe -c "import glass_cuda; print(glass_cuda.cuda_available()); print(glass_cuda.get_device_info(0) if glass_cuda.cuda_available() else {})"
```

## Test Result

- Targeted resident audit/help tests: `2 passed`.
- CLI/resident subset: `18 passed`.
- Full pytest: `173 passed in 8.31s`.
- Ruff: passed.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: true.

## Known Limitations

- Resident audit does not yet expose every fine-grained resident registration tuning flag available on `glass run`; it exposes the core entrypoint and commonly needed controls.
- `--memory-mode resident` currently requires `--backend cuda` rather than falling back to CPU.
- This checkpoint validates a small FITS smoke dataset, not the full 200-light M38 real-data benchmark.

## Next Step

- Use resident audit for a controlled real-data subset, then expand toward the M38 200-light parity/timing workflow with the already established WBPP reference.

## Clean-room

- Compliant. No official PixInsight/WBPP/PJSR source was read or copied.
- This change only wires project-owned CLI orchestration around existing GLASS resident CUDA code.
