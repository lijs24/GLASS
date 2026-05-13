# Optimization Gate 04: Triangle Pixel-Refine Stride Control

## Gate

Optimization Gate 04.

## Completed content

- Added CLI/runtime overrides for resident triangle pixel-refine sampling:
  - `--resident-triangle-pixel-refine-coarse-stride`
  - `--resident-triangle-pixel-refine-final-stride`
- Wired the overrides through both `gpwbpp run` and `gpwbpp audit`.
- Recorded the resolved final stride in `resident_artifacts.json` under `resident_registration`.
- Added a resident triangle smoke test that exercises the final-stride override.

## Commands

```powershell
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp\engine\resident_cuda.py src\gpwbpp\cli.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair
.\.venv\Scripts\gpwbpp.exe run --help
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q
```

## Test result

- Ruff: all checks passed.
- Targeted triangle test: 1 passed.
- Resident CUDA run tests: 14 passed.
- Full pytest: 180 passed in 8.13 s.

## CUDA availability

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: yes.

## Known limitations

- This gate exposes an optimization control; it does not change the default parity behavior.
- Real-data quality/speed tradeoff still needs M38 benchmarking against the current final-stride 1 baseline.
- The underlying native pixel-refine kernel is not yet batched across frames.

## Next step

- Run M38 200-light with `--resident-triangle-pixel-refine-final-stride 2`.
- Compare against the current `prefetch=2`/final-stride 1 baseline for timing and exact/coverage-masked image difference.
- If acceptable, try stride 4. If too much image drift appears, implement confidence-gated full refinement only for suspicious frames.

## Clean-room compliance

- Compliant. No PixInsight/WBPP/PJSR source files were read, copied, summarized, or modified.
- No original data directory was modified.
