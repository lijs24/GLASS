# S2-Gate 478 Status: Workspace Cleanup and Fresh 200-Light A/B

- Gate: S2-Gate 478
- Status: green checkpoint
- Date: 2026-06-22

## Completed

- Checked C: drive pressure before continuing the 200-light benchmark.
- Removed only workspace-local regenerated Python/test/build caches.
- Preserved historical benchmark evidence under `C:\glass_runs` and the
  M38 200-light reference/input artifact set under
  `C:\gpwbpp_runs\final_m38_h_200`.
- Re-ran the real M38 H-alpha 200-light A/B matrix after a clean GPU readiness
  sample.
- Confirmed the real run uses the native raw-u16 GPU decode path:
  - effective FITS mode: `native_u16_gpu`
  - backend counts: `native_u16be_raw: 200`
  - raw H2D payload: `24660480000` bytes
  - avoided CPU float32 host payload: `49320960000` bytes

## Cleanup Result

- C: free before cleanup: about `56.69 GB`.
- Removed cache entries: `478`.
- Project size after cleanup: about `2.324 GiB`.
- New A/B run size: about `3.230 GiB`.
- C: free after A/B: about `53.57 GB`.

If C: becomes tight, the best cleanup target is old, regenerable
`C:\glass_runs\phase2_s2_gate_*` probe output directories. Do not remove
`C:\gpwbpp_runs\final_m38_h_200` while it is still the active benchmark
reference/input set.

## Commands Run

```powershell
Get-PSDrive C
.\.venv\Scripts\glass.exe resident-ab-matrix-plan --root C:\glass_runs\phase2_s2_gate478_cleanup_ab_real --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out runs\checkpoints\s2_gate_478_ab_matrix_plan.json --markdown runs\checkpoints\s2_gate_478_ab_matrix_plan.md --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --min-coverage 190.0 --min-speedup 2.0 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --min-gpu-free-mib 65000 --max-gpu-utilization 20 --min-disk-free-gib 8
.\.venv\Scripts\glass.exe resident-ab-matrix-execute --plan runs\checkpoints\s2_gate_478_ab_matrix_plan.json --out runs\checkpoints\s2_gate_478_ab_matrix_execution_real.json --wait-ready-timeout-s 180 --wait-ready-interval-s 5 --wait-ready-consecutive-samples 3 --fail-on-failed --fail-on-blocked
.\.venv\Scripts\python.exe -m ruff check src tests docs
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_ab_matrix_plan.py tests\test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff: passed.
- Focused pytest: `11 passed in 1.67s`.
- Full pytest: `1118 passed in 45.09s`.

## Real A/B Result

Reference WBPP black-box elapsed time:

- `1092.541 s`

Baseline `throughput_v1_lanczos3_parity`:

- GLASS elapsed: `30.788683499966282 s`
- Speedup vs WBPP: `35.485148301361974x`
- Acceptance: passed
- Weighted frames: `193`
- Zero-weight frames: `7`
- Estimated peak VRAM: `49.608429938554764 GiB`
- WBPP-reference coverage fraction: `0.960532609259836`
- WBPP-reference RMS: `0.0017794216505176163`
- WBPP-reference p99 abs diff: `0.00042621337808668863`

Candidate `throughput_v2_fused_bilinear`:

- GLASS elapsed: `30.46608580002794 s`
- Speedup vs WBPP: `35.86089158847567x`
- Acceptance: passed
- Weighted frames: `193`
- Zero-weight frames: `7`
- Estimated peak VRAM: `47.3117358982563 GiB`
- WBPP-reference coverage fraction: `0.9680247262015986`
- WBPP-reference RMS: `0.0018004970117125889`
- WBPP-reference p99 abs diff: `0.0004224973497912281`

Candidate vs baseline:

- Coverage fraction: `0.9680247262015986`
- RMS: `4.5849533818006405` ADU
- Relative RMS: `0.016454569155982254`
- p50 abs diff: `0.6654815673828125` ADU
- p99 abs diff: `2.975449752807606` ADU
- p99.9 abs diff: `9.921587371827627` ADU
- Max abs diff: `1601.62109375` ADU

## Timing Interpretation

- Native FITS read remains the main cumulative worker cost:
  - baseline cumulative file read: `20.442127399999997 s`
  - candidate cumulative file read: `20.4087263 s`
- The overlapped light read/upload/calibrate wall time remains around 14 s:
  - baseline: `13.956307400017977 s`
  - candidate: `14.25223049998749 s`
- GPU calibration itself is already small:
  - baseline H2D/decode/calibrate/store batch time: `0.7212191047668457 s`
  - candidate H2D/decode/calibrate/store batch time: `0.7112090587615968 s`
- Registration and warp are no longer the dominant measured component in this
  run, but the large `light_loop_unaccounted` bucket still points at resident
  loop orchestration and synchronization as the next optimization target.

## Artifacts

- `runs/checkpoints/s2_gate_478_ab_matrix_plan.json`
- `runs/checkpoints/s2_gate_478_ab_matrix_plan.md`
- `runs/checkpoints/s2_gate_478_ab_matrix_execution_real.json`
- `runs/checkpoints/s2_gate_478_real_ab_summary.json`
- `C:\glass_runs\phase2_s2_gate478_cleanup_ab_real\reports\throughput_v1_lanczos3_parity_report.html`
- `C:\glass_runs\phase2_s2_gate478_cleanup_ab_real\reports\throughput_v2_fused_bilinear_report.html`
- `C:\glass_runs\phase2_s2_gate478_cleanup_ab_real\compare\throughput_v2_fused_bilinear_vs_throughput_v1_lanczos3_parity.html`

## Known Limitations

- The fused bilinear candidate is faster and passes WBPP-reference acceptance,
  but it is not pixel-parity-equivalent to the Lanczos3 baseline. It remains
  opt-in.
- This gate did not change CUDA kernels or default algorithms. It is a real
  benchmark validation plus cleanup checkpoint.
- The raw-u16 GPU decode path is already active on the 200-light dataset, so
  the next substantive optimization should target resident loop orchestration,
  synchronization, and file-read scheduling rather than just flipping FITS
  reader mode.

## Next Step

Proceed with the next Phase 2 substantive gate against the 200-light benchmark:
reduce `light_loop_unaccounted` and native read scheduling overhead while
preserving the `throughput-v1` Lanczos3 numerical baseline.

## Clean-Room Compliance

- This gate used GLASS-owned code and artifacts plus user-generated WBPP
  black-box timing/output metadata.
- No official PixInsight/WBPP/PJSR source was read, copied, summarized, or
  reworked.
- Original image directories were not modified.
