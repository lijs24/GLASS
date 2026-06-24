# S2-Gate 612 Status: Resident Local-Normalization In-Place Apply

## Gate

- Gate: S2-Gate 612
- Status: green
- Date: 2026-06-24
- Objective: reduce default resident CUDA local-normalization memory/copy cost while preserving LN formulas, DQ contracts, and real 200-light output parity.

## Completed Content

- Changed native resident global/grid LN application to update the resident device frame in place.
- Removed the previous full-frame temporary device output allocation and device-to-device copy from `apply_global_normalization_frame` and `apply_grid_normalization_frame`.
- Returned native LN application profiles with `mode=in_place_device_update`, temporary output bytes, coefficient upload timing, kernel/sync timing, and total timing.
- Normalized those profiles in `glass_cuda.py`.
- Recorded per-frame `application_profile`, group-level `application.mode_counts`, `application.temporary_output_bytes`, and `resident_local_normalization.application` in run artifacts.
- Updated CUDA resident stack tests and resident CLI tests to require the in-place application profile.
- Updated Phase 2, local-normalization, known-limitations, and algorithm-source documentation.

## Commands Run

```powershell
cmd /d /s /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" && ".\.venv\Scripts\cmake.exe" --build build --config Release --target _glass_cuda_native'
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py -k "local_norm or normalization"
.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_local_norm_vs_cpu.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py -k "ncc_subpixel_registration_smoke"
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate612_ln_inplace\real_200_default_regression --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
nvidia-smi --query-gpu=name,driver_version,memory.total,compute_cap --format=csv,noheader
```

## Test Results

- Native CUDA rebuild: passed; warnings only from CUDA/MSVC headers and one existing signed/unsigned warning.
- Focused resident stack LN tests: `3 passed, 51 deselected`.
- GPU/CPU local-normalization tests: `5 passed`.
- Focused resident CLI LN smoke: `1 passed, 114 deselected`.
- Ruff: `All checks passed`.
- Full pytest: `1289 passed in 52.19 s`.

## CUDA Availability

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Driver: 596.21.
- VRAM: 97887 MiB reported by `nvidia-smi`.

## Validation Artifacts

- Real 200-light candidate run:
  `C:\glass_runs\phase2_s2_gate612_ln_inplace\real_200_default_regression`
- Gate611 parity summary:
  `C:\glass_runs\phase2_s2_gate612_ln_inplace\real_200_vs_gate611_compare.json`

Real 200-light output parity against S2-Gate 611:

- master: SHA256 identical.
- weight map: SHA256 identical.
- coverage map: SHA256 identical.
- low rejection map: SHA256 identical.
- high rejection map: SHA256 identical.
- DQ map: SHA256 identical.

Real 200-light timing:

- Gate611 total elapsed: `11.453746799845248 s`.
- Gate612 total elapsed: `11.157036500168033 s`.
- Gate611 resident calibration/integration stage: `10.61795759992674 s`.
- Gate612 resident calibration/integration stage: `10.296283699921332 s`.
- Gate611 resident LN: `1.0661148000508547 s`.
- Gate612 resident LN: `0.5070594000862911 s`.
- Gate611 resident integration: `3.402352000004612 s`.
- Gate612 resident integration: `3.410337399924174 s`.
- Gate611 resident registration component: `1.6029904003201811 s`.
- Gate612 resident registration component: `1.6074519004984855 s`.

Resident LN application artifact:

- `applied_frame_count=192`.
- `mode_counts={"in_place_device_update": 192}`.
- `temporary_output_bytes=0`.
- `device_to_device_copy_s=0.0`.
- `frame_bytes=47348121600` worth of per-frame temporary output avoided across applied frames.

Contracts in the real 200-light candidate:

- `pipeline_contract.json`: passed.
- `resident_result_contract.json`: passed.
- `local_norm_contract.json`: passed.
- `stack_engine_contract.json`: passed.
- `warp_quality_contract.json`: passed.

## Known Limitations

- Grid LN statistics are still evaluated one source frame at a time.
- The next LN optimization should batch frame-pair grid stats and coefficient application, rather than only improving the apply copy path.
- Remaining larger default-path costs are hardened winsorized integration, resident registration/warp orchestration, and light read/upload/calibration scheduling.

## Next Step

- Continue the substantive Phase 2 mainline by batching resident grid-LN stats/application, improving resident registration/warp orchestration, or replacing the bounded 512-frame hardened reducer with a scalable device-side segmented/order-statistics reducer.

## Clean-Room Compliance

- This gate uses GLASS-owned CUDA kernels, GLASS-owned resident artifact contracts, GLASS tests, and user-owned real benchmark artifacts.
- No external or proprietary implementation source was inspected, copied, summarized, or reworked.
- Input image directories were not modified.
