# S2-Gate 45 Status: Resident Warp Scratch Reuse

## Gate

S2-Gate 45: Resident Warp Scratch Reuse

## Completed Content

- Reused resident CUDA warp scratch buffers inside `ResidentCalibratedStack` for:
  - translation warp output
  - matrix bilinear warp output
  - matrix Lanczos3 warp output
  - per-frame warp coverage
  - matrix inverse storage
- Added native and Python `warp_scratch_bytes` reporting.
- Recorded resident warp scratch bytes in `resident_artifacts.json`.
- Surfaced scratch memory in the HTML resident CUDA summary.
- Added direct CUDA resident-stack coverage for scratch reuse.
- Extended resident CUDA run tests to assert scratch diagnostics.
- Updated Phase 2 gate plan and algorithm source log.

## Commands Run

```powershell
cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" && "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" --build build\native-cuda-glass --target _glass_cuda_native'
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_reuses_warp_scratch_buffers tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_45_200\resident_warp_scratch_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps audit --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_45_200\resident_warp_scratch_20260601\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_45_200\resident_warp_scratch_20260601\s2_gate_45_compare.html --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_45_200\resident_warp_scratch_20260601\integration\resident_coverage_map_H.fits --min-coverage 190 --glass-time-seconds 24.390292499680072 --reference-time-seconds 1092.541 --glass-label GLASS-S2G45-resident-warp-scratch --reference-label WBPP-blackbox
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_45_200\resident_warp_scratch_20260601 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_45_200\resident_warp_scratch_20260601\s2_gate_45_compare.json --benchmark-contract benchmarks\phase2_m38_h_200_audit_maps_contract.json --out C:\glass_runs\phase2_s2_gate_45_200\resident_warp_scratch_20260601\phase2_contract_acceptance_audit_s2_gate_45.json --markdown C:\glass_runs\phase2_s2_gate_45_200\resident_warp_scratch_20260601\phase2_contract_acceptance_audit_s2_gate_45.md --min-active-frames 190 --min-speedup 2.0
.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate_45_200\resident_warp_scratch_20260601 --acceptance-audit C:\glass_runs\phase2_s2_gate_45_200\resident_warp_scratch_20260601\phase2_contract_acceptance_audit_s2_gate_45.json --out C:\glass_runs\phase2_s2_gate_45_200\resident_warp_scratch_20260601\s2_gate_45_report.html
```

## Test Results

- Focused CUDA resident tests: `2 passed`
- Focused resident/report/CLI suite: `49 passed`
- Full suite: `258 passed`
- Ruff: `All checks passed`
- Real 200-light acceptance audit: `passed`

## CUDA Availability

- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21

## Real-Data Result

- Run directory:
  `C:\glass_runs\phase2_s2_gate_45_200\resident_warp_scratch_20260601`
- Total resident CUDA runtime: `24.390292499680072 s`
- Reference runtime: `1092.541 s`
- Speedup vs reference: `44.794091748359754x`
- Coverage-masked RMS difference: `0.001558294284488301`
- Coverage-masked P99 absolute difference: `0.00043095467146486016`
- Coverage fraction: `0.9574613308418977`
- Resident registration/warp total: `10.084066001232713 s`
- Triangle warp component: `0.4012037990614772 s`
- I/O + upload + calibration: `6.468410999979824 s`
- Output write: `0.6139638000167906 s`
- Resident warp scratch bytes: `493209636`

## Artifacts

- `C:\glass_runs\phase2_s2_gate_45_200\resident_warp_scratch_20260601\resident_artifacts.json`
- `C:\glass_runs\phase2_s2_gate_45_200\resident_warp_scratch_20260601\s2_gate_45_compare.html`
- `C:\glass_runs\phase2_s2_gate_45_200\resident_warp_scratch_20260601\s2_gate_45_compare.json`
- `C:\glass_runs\phase2_s2_gate_45_200\resident_warp_scratch_20260601\phase2_contract_acceptance_audit_s2_gate_45.json`
- `C:\glass_runs\phase2_s2_gate_45_200\resident_warp_scratch_20260601\phase2_contract_acceptance_audit_s2_gate_45.md`
- `C:\glass_runs\phase2_s2_gate_45_200\resident_warp_scratch_20260601\s2_gate_45_report.html`

## Known Limits

- This gate removes resident warp allocation churn, but does not yet batch
  triangle descriptor scoring, pixel refinement, or warp launches across frames.
- `performance_regression.status` remains non-blocking `regressed` from the
  benchmark diagnostic contract, but all ranked optimization targets are `ok`
  in the S2-Gate 45 audit.
- The scratch buffer is intentionally retained until stack destruction; this
  improves repeated warp performance at the cost of about two full-frame float
  buffers plus a matrix inverse buffer in VRAM.

## Next Step

S2-Gate 46 should attack the remaining resident registration/warp cost by
batching triangle descriptor fit/refine/warp orchestration and reducing
per-frame host-device synchronization.

## Clean-Room Compliance

Compliant. The gate changes only GLASS-owned CUDA allocation strategy and
diagnostics, uses user-generated benchmark outputs as reference data, and does
not read, copy, summarize, or rework proprietary implementation source.
