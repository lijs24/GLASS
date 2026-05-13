# Gate 12 Status: Resident End-to-End Benchmark Entry

## Gate

Gate 12: End-to-end CUDA benchmark/audit increment.

## Completed

- Extended `benchmarks/bench_end_to_end.py` with resident CUDA options:
  - `--memory-mode {tile,resident}`
  - `--resident-registration`
  - `--local-normalization`
  - `--integration-weighting`
  - `--integration-rejection`
- The benchmark now records resident-specific fields when available:
  - memory mode
  - resident GPU device name
  - resident estimated peak GiB
  - integration weighting and rejection
- Ran a small synthetic resident CUDA benchmark smoke successfully.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check benchmarks\bench_end_to_end.py
.\.venv\Scripts\python.exe benchmarks\bench_end_to_end.py --out runs\benchmarks\bench_end_to_end_resident_smoke.json --frames 3 --width 32 --height 32 --tile-size 16 --backend cuda --memory-mode resident --local-normalization off --integration-weighting none --integration-rejection none --resident-registration off
Get-Content runs\benchmarks\bench_end_to_end_resident_smoke.json
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Result

- Ruff: passed.
- Resident benchmark smoke: completed and wrote `runs/benchmarks/bench_end_to_end_resident_smoke.json`.
- Full pytest: `173 passed in 7.97s`.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: true.

## Benchmark Smoke Result

- Backend: `cuda_resident_stack`.
- Memory mode: `resident`.
- Frame count: 3.
- Shape: 32x32.
- Elapsed: 0.24102890002541244 s.
- Peak RAM: 1.3148279190063477 MiB.
- Peak VRAM sampled by nvidia-smi: 1651 MiB.
- Output master: `runs\benchmarks\bench_end_to_end_resident_smoke\audit\integration\resident_master_H.fits`.

## Known Limitations

- The smoke benchmark is intentionally tiny; it verifies the benchmark entrypoint but is not a performance claim.
- The final M38/WBPP comparison still needs to use the real-data command path and report the same stages/settings.

## Next Step

- Use the resident benchmark wrapper for larger controlled timing runs, including the established M38 193/200-light scenarios.

## Clean-room

- Compliant. No official PixInsight/WBPP/PJSR source was read or copied.
