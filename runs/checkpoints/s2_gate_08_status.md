# S2-Gate 08 Status: Continuous Local Normalization

Date: 2026-05-31

## Gate

S2-Gate 8: Continuous Local Normalization.

## Completed

- Replaced the tile-mode Local Normalization apply path with a two-pass continuous coefficient-field model.
- Added CPU baseline helpers for coefficient-grid repair, bilinear tile-center interpolation, full/sliced coefficient-field generation, masked field apply, and residual summaries.
- The tile-mode pipeline now estimates per-tile masked source/reference mean/std coefficients, repairs empty cells from the nearest valid coefficient, interpolates `scale_field` and `offset_field`, and applies `O(x,y)=a(x,y)S(x,y)+b(x,y)` only on valid source/reference coverage pixels.
- Added per-frame coefficient JSON with raw/repaired grids, interpolation model, empty-tile fill count, residual summary, crop box, and diagnostic map paths.
- Added optional full-resolution diagnostic FITS maps for scale, offset, and residual fields. The default threshold writes these maps for small validation runs and records `omitted_due_to_size` for larger images.
- Preserved DQ propagation by marking invalid LN pixels with `LOCAL_NORMALIZATION_EXCLUDED`.
- Updated the local-normalization model document, algorithm-source log, and Phase 2 `/goal` anchor.

## Commands

- `.venv\Scripts\python.exe -m pytest -q tests\test_cpu_local_norm.py`
- `.venv\Scripts\python.exe -m ruff check src\glass\cpu\local_norm.py src\glass\engine\local_norm.py tests\test_cpu_local_norm.py tests\test_pipeline_fixture.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_fixture.py::test_pipeline_fixture_run_local_normalization`
- `.venv\Scripts\python.exe -m pytest -q tests\test_gpu_local_norm_vs_cpu.py`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -m pytest -q tests\test_cuda_import.py tests\test_cuda_device_info.py tests\test_cuda_smoke.py tests\test_gpu_local_norm_vs_cpu.py`
- `.venv\Scripts\glass.exe synthetic --out runs\s2_gate_08_smoke_data --frames 3 --width 32 --height 32 --known-shift`
- `.venv\Scripts\glass.exe audit --root runs\s2_gate_08_smoke_data --out runs\s2_gate_08_smoke --backend cpu --tile-size 8 --local-normalization on`

## Test Results

- CPU Local Normalization tests: 9 passed.
- Pipeline Local Normalization fixture: 1 passed.
- GPU Local Normalization CPU/GPU primitive tests: 5 passed.
- Full test suite: 223 passed in 12.19 s.
- CUDA import/device/smoke/GPU Local Normalization tests: 8 passed.
- Ruff check: passed.
- CLI synthetic audit with Local Normalization enabled: completed successfully.

## CUDA

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21

## Artifacts

- `runs/s2_gate_08_smoke_data/`
- `runs/s2_gate_08_smoke/local_norm_results.json`
- `runs/s2_gate_08_smoke/local_norm_cache/local_norm_*_coefficients.json`
- `runs/s2_gate_08_smoke/local_norm_cache/local_norm_*_scale_field.fits`
- `runs/s2_gate_08_smoke/local_norm_cache/local_norm_*_offset_field.fits`
- `runs/s2_gate_08_smoke/local_norm_cache/local_norm_*_residual.fits`
- `runs/s2_gate_08_smoke/dq_cache/dq_local_norm_*.fits`

## Known Limitations

- The continuous field currently uses per-tile mean/std coefficients and bilinear interpolation; robust nebulosity/background masks and higher-order surface fitting remain future work.
- Tile-mode continuous field application is CPU-audited. CUDA can provide pair-statistics primitives, but a fully resident CUDA continuous-field apply path is still a later optimization target.
- Full-resolution diagnostic scale/offset/residual maps are size-limited by `GLASS_LN_FULL_FIELD_MAP_MAX_PIXELS` to avoid producing hundreds of MiB per frame on large 200-light runs.
- The 200-light real-data benchmark was not rerun for this gate; this gate changed the optional LN path and was validated with synthetic and unit/pipeline coverage.

## Next Step

S2-Gate 9: complete rejection and variance integration, including winsorized sigma hardening, additional rejection modes, variance-aware weighting, and variance map output through the shared StackEngine contract.

## Clean-Room

Compliant. This gate used clean-room numerical background matching, standard mean/std statistics, nearest-cell coefficient repair, and bilinear interpolation formulas. No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or reworked.
