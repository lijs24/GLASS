# S2-Gate 607 Status: Resident Batch Tile Download Surface

## Gate

S2-Gate 607.

## Completed

- Added native `ResidentCalibratedStack.download_frames_tile(indices, x0, y0, x1, y1)`.
- Added Python wrapper support with fallback to repeated `download_frame_tile`.
- Updated the segmented CPUStackEngine resident hardened fallback so over-limit groups download one resident stack tile per output tile when batch download is available.
- Preserved the single-frame download loop for older native builds and test doubles.
- Added focused tests for both batch and escape-hatch paths.
- Added a native resident stack tile-capture test for frame ordering and tile contents.
- Updated Phase 2 docs, integration model, limitations, and algorithm-source log.

## Commands Run

- `cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" && ".\.venv\Scripts\cmake.exe" --build build --config Release --target _glass_cuda_native'`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py -k "segmented_cpu_hardened or single_frame_download_escape_hatch"`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_tile_capture.py -k "download_frame"`
- `.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate606_segmented_hardened\processing_plan.json --out C:\glass_runs\phase2_s2_gate607_batch_tile_download\resident_260_batch_tile --backend cuda --memory-mode resident --until-stage integration --resident-registration off --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --resident-winsorized-mode auto --resident-output-maps audit --flat-floor 0.05 --resident-runtime-preset manual --resident-prefetch-frames 8 --resident-prefetch-workers 4 --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 8 --resident-calibration-streams 2`
- `.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate607_batch_tile_download\real_200_default_regression --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
- `.\.venv\Scripts\python.exe -m ruff check cpp src tests`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused resident segmented fallback tests: `2 passed, 113 deselected`.
- Focused resident tile capture tests: `2 passed, 2 deselected`.
- Ruff: `All checks passed`.
- Full pytest: `1288 passed in 52.39 s`.

## CUDA Availability

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Reported VRAM: 97886 MiB.
- Native backend: available.

## Synthetic 260-Light Validation

- Run path: `C:\glass_runs\phase2_s2_gate607_batch_tile_download\resident_260_batch_tile`.
- Route: `cpu_stack_engine_segmented_resident_download`.
- `resident_winsorized_mode`: `hardened_cpu_parity`.
- `batch_tile_download_native_available`: `true`.
- `batch_tile_download_used`: `true`.
- `batch_tile_download_call_count`: `1`.
- `single_frame_tile_download_call_count`: `0`.
- Hardened timing: `0.009082899894565344 s`.
- Six integration FITS outputs are SHA256-identical to Gate606:
  - `resident_master_H.fits`
  - `resident_weight_map_H.fits`
  - `resident_coverage_map_H.fits`
  - `resident_low_rejection_map_H.fits`
  - `resident_high_rejection_map_H.fits`
  - `resident_dq_map_H.fits`

## Real 200-Light Regression

- Run path: `C:\glass_runs\phase2_s2_gate607_batch_tile_download\real_200_default_regression`.
- Native route: `ResidentCalibratedStack.integrate_hardened_winsorized_sigma`.
- `total_elapsed_s`: `12.123008000082336`.
- `resident_integration_s`: `3.729795799939893`.
- Hardened native timing: `3.7297367000719532 s`.
- `pipeline_contract.json`: passed.
- `resident_result_contract.json`: passed.
- Six integration FITS outputs are SHA256-identical to Gate606.

## Known Limitations

- The Gate607 batch tile surface reduces Python/native call overhead for the over-limit correctness fallback, but it still downloads resident calibrated tiles to host.
- The final high-throughput solution remains a true all-device segmented CUDA hardened winsorized reduction.
- The native hardened CUDA path remains the default route for supported groups at or below 256 frames.

## Next Step

Implement a real CUDA segmented hardened winsorized reducer for groups above 256 frames, using the Gate607 batch tile surface as the current compatibility boundary and preserving CPUStackEngine parity tests.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned native resident storage, GLASS CPUStackEngine formulas, GLASS synthetic data, and user-owned real benchmark artifacts. No external or proprietary implementation source was inspected, copied, summarized, or reworked.
