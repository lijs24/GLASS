# Gate 04 Resident Stack Status

## Gate

Resident CUDA stack extension for the high-VRAM M38 timing benchmark.

## Completed

- Added a native CUDA resident calibrated stack API.
- Added a resident weighted-mean integration kernel.
- Added a Python `glass_cuda.ResidentCalibratedStack` wrapper.
- Added CPU/GPU tests for resident calibration and weighted integration.
- Added a real-data benchmark script that keeps calibrated lights resident in VRAM.
- Updated the memory model for staged residency:
  `raw input -> calibrated -> aligned -> local-normalized -> integrated output`.
- Ran the M38 H benchmark with 200 lights, 20 bias, 20 dark, and 20 flat frames.

## Commands

```powershell
.venv\Scripts\python.exe -m pytest -q tests/test_cuda_import.py tests/test_cuda_device_info.py tests/test_cuda_smoke.py tests/test_gpu_calibration_vs_cpu.py tests/test_cuda_resident_stack.py
.venv\Scripts\python.exe benchmarks\bench_cuda_resident_stack.py --plan C:\glass_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\final_m38_h_200\glass_resident_cuda_smoke --limit 2
.venv\Scripts\python.exe benchmarks\bench_cuda_resident_stack.py --plan C:\glass_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\final_m38_h_200\glass_resident_cuda_200
.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Targeted CUDA tests: 8 passed in 0.91 s.
- Full test suite: 63 passed in 5.92 s.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Total VRAM reported by native backend: 97886 MiB.

## Real Benchmark

- Dataset: M38 H mono, 200 lights + 20 bias + 20 dark + 20 flat.
- Input and output staged on C:.
- WBPP black-box total: 1092.541 s.
- GLASS resident benchmark total: 68.617 s.
- Resident benchmark light read/upload/calibrate: 48.122 s.
- Resident benchmark integration: 0.131 s.
- Estimated resident peak VRAM: 47.31 GiB.
- Benchmark-path wall-clock speedup versus WBPP black-box total: 15.92x.

## Artifacts

- `C:\glass_runs\final_m38_h_200\glass_resident_cuda_200\resident_benchmark_result.json`
- `C:\glass_runs\final_m38_h_200\glass_resident_cuda_200\resident_master_mean.fits`
- `C:\glass_runs\final_m38_h_200\resident_vs_wbpp_summary.json`
- `C:\glass_runs\final_m38_h_200\resident_vs_wbpp_summary.md`
- `C:\glass_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json`

## Known Limitations

- This is an upper-bound resident benchmark path, not a full WBPP-equivalent run.
- It includes master build/load, CUDA light calibration, and resident mean integration.
- It does not yet include WBPP-equivalent star detection, registration, local normalization,
  rejection, autocrop, or XISF output semantics.
- Resident mode is implemented as a benchmark/API path and is not yet selected by
  `glass run`.

## Next Step

Integrate the resident memory planner into `glass run`, then add the same staged
residency pattern for registration, warp, optional LN, and rejection maps.

## Clean Room

Compliant. PixInsight/WBPP was used only as a black-box timing baseline. No official
WBPP/PJSR source was read or copied.
