# S2-Gate 479 Status: Resident Source-DQ Fast-Skip for Raw-U16 Runs

- Gate: S2-Gate 479
- Status: green checkpoint
- Date: 2026-06-22

## Completed

- Added an explicit resident source-DQ no-input fast-skip path.
- The fast-skip is enabled only when all of these are true:
  - resident FITS mode is effectively `native_u16_gpu`;
  - inline source-DQ mode is `off`;
  - no plan-frame or calibration-artifact source-DQ sidecar is present.
- The path skips per-frame empty source-DQ row construction for raw integer
  FITS payloads while preserving the source-DQ contract summary.
- Resident artifacts now record:
  - `source_dq_fast_skip_enabled`
  - `source_dq_fast_skipped_frame_count`
  - `source_dq_fast_skip_reason`
  - `source_dq_sidecar_frame_count`
- `source_dq_summary` now records `no_source_dq_fast_skip` source/status
  counts when the skip applies.
- Updated `docs/algorithm_sources.md` with the clean-room origin and
  limitations for this scheduling optimization.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py src\glass\engine\resident_source_dq.py tests\test_resident_source_dq.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_source_dq.py::test_resident_source_dq_summary_records_no_source_dq_fast_skip tests\test_resident_cuda_run.py::test_cli_resident_cuda_records_native_u16_gpu_decode_backend
.\.venv\Scripts\glass.exe resident-ab-matrix-plan --root C:\glass_runs\phase2_s2_gate479_source_dq_fastskip_ab_real --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out runs\checkpoints\s2_gate_479_ab_matrix_plan.json --markdown runs\checkpoints\s2_gate_479_ab_matrix_plan.md --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --min-coverage 190.0 --min-speedup 2.0 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --min-gpu-free-mib 65000 --max-gpu-utilization 20 --min-disk-free-gib 8
.\.venv\Scripts\glass.exe resident-ab-matrix-execute --plan runs\checkpoints\s2_gate_479_ab_matrix_plan.json --out runs\checkpoints\s2_gate_479_ab_matrix_execution_baseline.json --variant throughput_v1_lanczos3_parity --wait-ready-timeout-s 180 --wait-ready-interval-s 5 --wait-ready-consecutive-samples 3 --fail-on-failed --fail-on-blocked
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate479_source_dq_fastskip_ab_real\runs\throughput_v1_lanczos3_parity\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate478_cleanup_ab_real\runs\throughput_v1_lanczos3_parity\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate479_source_dq_fastskip_ab_real\compare\gate479_vs_gate478_baseline.html --glass-label "Gate479 source-DQ fast-skip" --reference-label "Gate478 baseline" --glass-coverage-map C:\glass_runs\phase2_s2_gate479_source_dq_fastskip_ab_real\runs\throughput_v1_lanczos3_parity\integration\resident_coverage_map_H.fits --min-coverage 190.0
.\.venv\Scripts\python.exe -m ruff check src tests docs
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_source_dq.py tests\test_resident_cuda_run.py::test_cli_resident_cuda_records_native_u16_gpu_decode_backend tests\test_resident_cuda_run.py::test_cli_resident_cuda_auto_selects_native_u16_gpu_for_compatible_group tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_applies_plan_source_dq_sidecar tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_applies_calibration_artifact_dq_sidecar
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff targeted: passed.
- Initial focused tests: `2 passed in 0.75s`.
- Final focused tests: `16 passed in 0.84s`.
- Full pytest: `1119 passed in 40.77s`.

## Real 200-Light Result

Reference WBPP black-box elapsed time:

- `1092.541 s`

Gate479 baseline `throughput_v1_lanczos3_parity`:

- GLASS elapsed: `30.656666999973822 s`
- Speedup vs WBPP: `35.637957642327294x`
- Acceptance: passed
- Weighted frames: `193`
- Zero-weight frames: `7`
- Estimated peak VRAM: `49.608429938554764 GiB`
- WBPP-reference coverage fraction: `0.960532609259836`
- WBPP-reference RMS: `0.0017794216505176163`
- WBPP-reference p99 abs diff: `0.00042621337808668863`

## Gate478 Comparison

- Gate478 baseline elapsed: `30.788683499966282 s`
- Gate479 elapsed delta: `-0.13201649999246 s`
- Gate479 speedup delta: `+0.1528093409653195x`
- Source-DQ row count: `200 -> 0`
- Fast-skip frame count: `200`
- Gate479 vs Gate478 baseline pixel diff:
  - RMS: `0.0`
  - p99: `0.0`
  - max abs diff: `0.0`
  - shape match: `true`

## Timing Interpretation

- This gate removes empty source-DQ bookkeeping for the common raw-u16/no-DQ
  resident benchmark path and proves the output is pixel-identical.
- It does not reduce physical FITS read time. The real run still reports
  cumulative native FITS file read around `20.4046346 s`.
- The total elapsed improvement is small and within real storage/scheduler
  variability. Treat this gate as contract-preserving loop cleanup, not as the
  main I/O breakthrough.
- The next substantive optimization should target native FITS read scheduling,
  resident loop synchronization, and the remaining `light_loop_unaccounted`
  bucket.

## Artifacts

- `runs/checkpoints/s2_gate_479_ab_matrix_plan.json`
- `runs/checkpoints/s2_gate_479_ab_matrix_plan.md`
- `runs/checkpoints/s2_gate_479_ab_matrix_execution_baseline.json`
- `runs/checkpoints/s2_gate_479_real_baseline_summary.json`
- `C:\glass_runs\phase2_s2_gate479_source_dq_fastskip_ab_real\reports\throughput_v1_lanczos3_parity_report.html`
- `C:\glass_runs\phase2_s2_gate479_source_dq_fastskip_ab_real\compare\throughput_v1_lanczos3_parity_vs_wbpp.html`
- `C:\glass_runs\phase2_s2_gate479_source_dq_fastskip_ab_real\compare\gate479_vs_gate478_baseline.html`

## Known Limitations

- No CUDA kernel math changed in this gate.
- The optimization is intentionally disabled when sidecar DQ masks, inline
  source-DQ, or floating source arrays require per-frame inspection.
- It does not solve disk-read bottlenecks or resident orchestration timing by
  itself.

## Next Step

Proceed to the next substantive Gate: split or reduce the remaining resident
light-loop unaccounted time by separating Python batch preparation,
prefetch-result waits, native callback release scheduling, and post-calibration
resident bookkeeping, then use a fresh 200-light baseline probe to decide which
part deserves a CUDA/native scheduler rewrite.

## Clean-Room Compliance

- This gate used GLASS-owned code and artifacts plus user-generated WBPP
  black-box timing/output metadata.
- No official PixInsight/WBPP/PJSR source was read, copied, summarized, or
  reworked.
- Original image directories were not modified.
