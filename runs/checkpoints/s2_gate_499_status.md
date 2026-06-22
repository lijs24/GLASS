# S2-Gate 499 Status: Resident Minimal Batch Warp Coverage Scratch Skip

## Gate

S2-Gate 499

## Summary

Implemented the next resident CUDA speed-path optimization after Gate498.
Minimal output mode already skipped the global geometric warp coverage
accumulator; Gate499 also skips allocating and writing per-frame
`batch_coverage` scratch in batch bilinear/Lanczos3 warp when
`track_coverage=false`.

Audit/science output modes keep the original coverage behavior. The pixel
sampling formula, registration transforms, rejection math, accepted-frame
decisions, and final integration math are unchanged.

## Completed Work

- Updated `cpp/cuda/warp_kernels.cu`:
  - batch bilinear warp accepts `batch_coverage=nullptr`;
  - batch Lanczos3 warp accepts `batch_coverage=nullptr`;
  - coverage writes are skipped only when the pointer is null.
- Updated `cpp/src/native_bindings.cpp`:
  - `allocate_batch_warp_workspace(..., include_coverage)` can skip coverage
    scratch allocation;
  - `track_coverage=false` now passes `include_coverage=false`;
  - native timing reports `batch_coverage_bytes=0` for the no-scratch path.
- Added CUDA regression coverage in `tests/test_gpu_warp_vs_cpu.py`:
  - no-scratch path returns `batch_coverage_bytes=0`;
  - `warp_coverage_frame_count` remains `0`;
  - integrated master/weight output matches the coverage-tracking path exactly.
- Updated:
  - `docs/phase2_algorithm_hardening.md`
  - `docs/algorithm_sources.md`

## Commands Run

```powershell
# native build
cmd /c "VsDevCmd.bat -arch=x64 && cmake --build build --config Release --target _glass_cuda_native"

# focused tests
.\.venv\Scripts\python.exe -m pytest -q tests/test_gpu_warp_vs_cpu.py::test_resident_stack_matrix_lanczos3_batch_can_skip_coverage_scratch_without_pixel_change
.\.venv\Scripts\python.exe -m pytest -q tests/test_gpu_warp_vs_cpu.py::test_resident_stack_matrix_bilinear_batch_warp_matches_cpu_reference tests/test_gpu_warp_vs_cpu.py::test_resident_stack_matrix_bilinear_batch_respects_max_chunk_capacity tests/test_gpu_warp_vs_cpu.py::test_resident_stack_matrix_lanczos3_batch_warp_matches_cpu_reference tests/test_gpu_warp_vs_cpu.py::test_resident_stack_matrix_lanczos3_batch_respects_max_chunk_capacity
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_resident_registration_matrix_batch_can_skip_warp_coverage_tracking

# real 200-light run
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate499_no_coverage_scratch_ab_real\runs\stack_minimal_no_coverage_scratch --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps minimal --resident-master-cache-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache

# compare report
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate499_no_coverage_scratch_ab_real\runs\stack_minimal_no_coverage_scratch\integration\resident_master_H.fits --reference "C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out C:\glass_runs\phase2_s2_gate499_no_coverage_scratch_ab_real\compare\gate499_vs_wbpp_scaled_no_coverage.json --glass-time-seconds 7.620175199990626 --reference-time-seconds 1092.541 --glass-label "GLASS Gate499 resident CUDA minimal no coverage scratch" --reference-label "PixInsight WBPP FastIntegration" --glass-scale 1.5259021896696422e-05 --clip-low 0 --clip-high 1

# full suite
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- New CUDA no-scratch warp test: `1 passed`.
- Focused batch warp CPU-reference tests: `4 passed`.
- Resident helper no-coverage propagation test: `1 passed`.
- Full pytest: `1144 passed in 41.81s`.

## CUDA Status

- CUDA available: yes.
- GPU from Gate498/499 validation host:
  - name: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
  - compute capability: `12.0`
  - total memory: `97886 MiB`
  - multiprocessors: `188`
  - driver: `596.21`

## Real 200-Light A/B

- Run root:
  `C:\glass_runs\phase2_s2_gate499_no_coverage_scratch_ab_real\runs\stack_minimal_no_coverage_scratch`
- Total elapsed:
  `7.620175199990626 s`
- WBPP black-box elapsed:
  `1092.541 s`
- Speedup versus WBPP:
  `143.37478749850055x`
- Active frames:
  `193 / 200`
- Output policy:
  - `download_mode=master_only`
  - `weight_map_downloaded=false`
  - `diagnostic_maps_downloaded=false`
  - public integration output: final master only
- Warp path:
  - `triangle_warp_batch_track_coverage=false`
  - `triangle_warp_batch_coverage_accumulator_policy=skipped_by_minimal_output_policy`
  - `triangle_warp_batch_native_postprocess_mode=scatter_only_no_coverage_accumulator`
  - `triangle_warp_batch_native_coverage_bytes=0`
  - `triangle_warp_batch_native_workspace_bytes=1972846848`
  - `triangle_warp_batch_native_output_bytes=1972838400`

## Performance Delta

- Gate498 coverage scratch bytes:
  `493209600`
- Gate499 coverage scratch bytes:
  `0`
- Gate498 batch workspace bytes:
  `2466056448`
- Gate499 batch workspace bytes:
  `1972846848`
- Gate498 native triangle warp sync/total:
  `0.465614 / 0.4856435 s`
- Gate499 native triangle warp sync/total:
  `0.4639118 / 0.4807978 s`
- Gate498 resident registration warp total:
  `0.5552570992149413 s`
- Gate499 resident registration warp total:
  `0.5493012004881166 s`

## Numerical Validation

- Gate499 master vs Gate498 master:
  - finite pixels: `61,651,200`
  - shape: `(6422, 9600)`
  - RMS: `0.0`
  - p99 abs: `0.0`
  - max abs: `0.0`
  - bitwise equal including NaN mask: yes
- Gate499 no-coverage-mask compare vs WBPP:
  - report: `C:\glass_runs\phase2_s2_gate499_no_coverage_scratch_ab_real\compare\gate499_vs_wbpp_scaled_no_coverage.json`
  - RMS: `0.012331019662283473`
  - p99 abs: `0.0007338226120918931`
  - shape match: yes
- Because Gate499, Gate498, and Gate497 masters are bitwise identical, the
  established WBPP scaled coverage-190 comparison remains unchanged:
  - RMS: `0.0017794216505176163`
  - p99 abs: `0.00042621337808668863`
  - coverage fraction: `0.960532609259836`

## Artifacts

- Real run:
  `C:\glass_runs\phase2_s2_gate499_no_coverage_scratch_ab_real\runs\stack_minimal_no_coverage_scratch`
- Master:
  `C:\glass_runs\phase2_s2_gate499_no_coverage_scratch_ab_real\runs\stack_minimal_no_coverage_scratch\integration\resident_master_H.fits`
- Compare:
  `C:\glass_runs\phase2_s2_gate499_no_coverage_scratch_ab_real\compare\gate499_vs_wbpp_scaled_no_coverage.json`
- Compare HTML:
  `C:\glass_runs\phase2_s2_gate499_no_coverage_scratch_ab_real\compare\gate499_vs_wbpp_scaled_no_coverage.html`

## Known Limitations

- Minimal mode intentionally does not write coverage, rejection, weight, or DQ
  diagnostic maps. Use audit/science modes for evidence-rich artifacts.
- This gate removes batch coverage scratch only when `track_coverage=false`.
  Audit/science modes keep coverage scratch and geometric coverage
  accumulation.
- The end-to-end improvement is small because the main remaining costs are
  I/O/upload/calibration and resident registration orchestration.

## Next Step

Move from output-policy cleanup to larger substantive bottlenecks:

1. I/O + upload + calibration overlap with pinned/multi-buffer scheduling.
2. Resident registration/catalog/warp orchestration, reducing per-frame Python
   control and host/device round trips.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or
  reworked.
- PixInsight/WBPP was used only through existing user-generated black-box
  outputs and timing artifacts.
- Input image directories were treated as read-only.
- The optimization is GLASS-owned CUDA workspace/kernel scheduling code and
  does not use proprietary implementation details.
