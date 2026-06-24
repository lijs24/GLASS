# S2-Gate 609 Status: Dual-Capacity Hardened Winsorized CUDA Kernel

## Gate

- Gate: S2-Gate 609
- Theme: preserve the 200-light default-path speed after Gate608's 512-frame native capacity increase.
- Status: green

## Completed

- Split the resident native hardened winsorized CUDA reducer into two template
  instantiations:
  - `small_256` for frame groups with at most 256 frames.
  - `large_512` for frame groups with 257-512 frames.
- Kept the Gate608 512-frame native limit unchanged.
- Added timing fields:
  - `native_kernel_frame_capacity`
  - `native_kernel_capacity_selector`
- Added tests proving small and large kernel selection is surfaced through the
  native Python wrapper and CLI resident artifacts.
- Updated Phase 2 docs, integration model, known limitations, and algorithm
  source log.

## Commands Run

```powershell
cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" && ".\.venv\Scripts\cmake.exe" --build build --config Release --target _glass_cuda_native'

.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py -k "hardened_winsorized_sigma"
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py -k "hardened_winsorized_matches_cpu_baseline"

.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate606_segmented_hardened\processing_plan.json --out C:\glass_runs\phase2_s2_gate609_dual_capacity_hardened\resident_260_dual_capacity --backend cuda --memory-mode resident --until-stage integration --resident-registration off --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --resident-winsorized-mode auto --resident-output-maps audit --flat-floor 0.05 --resident-runtime-preset manual --resident-prefetch-frames 8 --resident-prefetch-workers 4 --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 8 --resident-calibration-streams 2

.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate609_dual_capacity_hardened\real_200_default_regression --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final

.\.venv\Scripts\python.exe -m ruff check cpp src tests
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Native rebuild: passed.
- Focused hardened CUDA tests: `4 passed, 50 deselected`.
- Focused resident CLI hardened parity test: `1 passed, 114 deselected`.
- Ruff: `All checks passed`.
- Full pytest: `1289 passed in 53.38 s`.

## Synthetic 260-Light Validation

- Run path:
  `C:\glass_runs\phase2_s2_gate609_dual_capacity_hardened\resident_260_dual_capacity`
- Effective route: `native_cuda_resident_stack`.
- Effective mode: `hardened_cpu_parity`.
- Kernel selector: `large_512`.
- Native hardened timing: `0.011102600023150444 s`.
- `pipeline_contract.json`: passed.
- `resident_result_contract.json`: passed.
- Pixel comparison against Gate608 native 260 output:
  - master: SHA256 identical, `max_abs=0.0`, `rms=0.0`
  - weight: SHA256 identical, `max_abs=0.0`, `rms=0.0`
  - coverage: SHA256 identical, `max_abs=0.0`, `rms=0.0`
  - low rejection: SHA256 identical, `max_abs=0.0`, `rms=0.0`
  - high rejection: SHA256 identical, `max_abs=0.0`, `rms=0.0`
  - DQ map: SHA256 identical, `max_abs=0.0`, `rms=0.0`

## Real 200-Light Validation

- Run path:
  `C:\glass_runs\phase2_s2_gate609_dual_capacity_hardened\real_200_default_regression`
- Total elapsed: `11.787260199896991 s`.
- `resident_calibration_integration`: `10.944278200040571 s`.
- Effective route: `native_cuda_resident_stack`.
- Kernel selector: `small_256`.
- Native hardened timing: `3.7481071000220254 s`.
- Gate608 native hardened timing: `3.8001173000084236 s`.
- `pipeline_contract.json`: passed.
- `resident_result_contract.json`: passed.
- Six integration FITS outputs are SHA256-identical to Gate608.
- C drive free space before real run: `197317607424` bytes.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Build toolkit observed during native rebuild: CUDA 13.2.

## Known Limitations

- This gate does not implement the final scalable segmented CUDA hardened
  reducer.
- Groups above 512 frames still use the segmented CPUStackEngine resident-tile
  fallback when parity is required.
- The 260-light synthetic timing is tiny and dominated by launch/sync noise; it
  is used primarily as a correctness and routing proof.

## Next Step

- Continue Phase 2 with a substantive mainline gate:
  - either implement a scalable device-side segmented/selection reducer for
    resident hardened winsorized groups above 512 frames;
  - or return to resident registration/warp orchestration, which remains a
    major real 200-light cost area.

## Clean-Room Compliance

- This gate uses GLASS-owned CUDA kernels, GLASS-owned CPUStackEngine formulas,
  GLASS synthetic data, and user-owned real benchmark artifacts.
- No external or proprietary implementation source was inspected, copied,
  summarized, or reworked.
- Input image directories were treated as read-only.
