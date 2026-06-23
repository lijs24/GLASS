# S2-Gate 542 Status: Ready-First Resident Calibration Batches

## Gate

- Gate: S2-Gate 542
- Date: 2026-06-23
- Scope: CUDA resident read/upload/calibration scheduling on the real 200-light benchmark.

## Completed

- Added `_LightPrefetcher.ready_index()` to select a completed candidate read future.
- Enabled ready-first resident calibration batch filling only for homogeneous single-master calibration groups.
- Preserved original resident frame indices for calibrated output storage, registration, DQ, rejection, and integration.
- Left multi-master groups on the previous sequential-index scheduling path.
- Recorded `calibration_order_mode`, ready-order eligibility, master-group count, out-of-order count, sample order, and ready-selection wait in resident artifacts.
- Fixed timing accounting so ready-selection wait is included in `light_read_wait_wall`.
- Updated the resident light pipeline profile with ready-order knobs.
- Added a unit test proving a completed later candidate can be selected before a blocked lower index.

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_light_prefetcher_ready_index_selects_completed_candidate tests/test_resident_cuda_run.py::test_cli_resident_cuda_default_fits_read_mode_is_guarded_auto`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate542_ready_batch\runs_20260623_142334\ready_batch_default_timed --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- `Get-FileHash` SHA256 comparison for master, weight, coverage, low/high rejection, and DQ maps versus Gate541.
- `.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate542_ready_batch\runs_20260623_142334\ready_batch_default_timed\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate542_ready_batch\runs_20260623_142334\ready_batch_default_timed\compare_vs_wbpp_fastintegration_scaled_coverage190.json --glass-time-seconds 5.22964 --reference-time-seconds 1092.541 --glass-label "GLASS Gate542 resident ready-batch" --reference-label "WBPP black-box fastIntegration" --glass-scale=1.545301547671945e-05 --glass-offset=-9.765786009702931e-05 --ignore-border-px 128 --glass-coverage-map C:\glass_runs\phase2_s2_gate542_ready_batch\runs_20260623_142334\ready_batch_default_timed\integration\resident_coverage_map_H.fits --min-coverage 190`

## Test Results

- Focused pytest: passed.
- Full pytest: `1179 passed in 42.99s`.
- `git diff --check`: no whitespace errors; only expected Windows LF-to-CRLF warnings.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Real 200-Light Result

- Run path: `C:\glass_runs\phase2_s2_gate542_ready_batch\runs_20260623_142334\ready_batch_default_timed`.
- Shell elapsed: `5.22964 s`.
- Internal elapsed: `4.869791700039059 s`.
- Calibration order mode: `ready_first_single_master_group`.
- Ready-order enabled: true.
- Ready-order master group count: `1`.
- Out-of-order consumed frames: `62`.
- Ready-selection wait included in read wait: `1.1719279001117684 s`.
- Light read/upload/calibrate: `2.5747510999790393 s`.
- Resident registration/warp: `0.25434350047726184 s`.
- Resident integration: `0.30348869995214045 s`.
- Output write: `0.23077540000667796 s`.
- FITS read mode: `native_u16_gpu`.
- FITS spec cache hits: `200`.

## Numerical Validation

- SHA256 bitwise equality versus Gate541 for:
  - `resident_master_H.fits`
  - `resident_weight_map_H.fits`
  - `resident_coverage_map_H.fits`
  - `resident_low_rejection_map_H.fits`
  - `resident_high_rejection_map_H.fits`
  - `resident_dq_map_H.fits`
- WBPP compare:
  - speedup versus WBPP FastIntegration timing: `208.91323303324893x`;
  - compared pixels: `56997300`;
  - coverage fraction: `0.9892770479074376`;
  - RMS diff: `0.0004279821839256963`;
  - p99 abs diff: `0.0001313822576776147`;
  - robust-fit RMS diff on fit pixels: `4.2529498303511286e-05`.

## Artifacts

- Summary JSON: `runs/checkpoints/s2_gate_542_ready_batch_summary.json`.
- Real run: `C:\glass_runs\phase2_s2_gate542_ready_batch\runs_20260623_142334\ready_batch_default_timed`.
- Hash comparison: `C:\glass_runs\phase2_s2_gate542_ready_batch\runs_20260623_142334\ready_batch_default_timed\hash_compare_gate541.json`.
- WBPP compare JSON/HTML:
  - `C:\glass_runs\phase2_s2_gate542_ready_batch\runs_20260623_142334\ready_batch_default_timed\compare_vs_wbpp_fastintegration_scaled_coverage190.json`
  - `C:\glass_runs\phase2_s2_gate542_ready_batch\runs_20260623_142334\ready_batch_default_timed\compare_vs_wbpp_fastintegration_scaled_coverage190.html`

## Known Limitations

- Ready-first scheduling is enabled only for homogeneous single-master calibration groups.
- The gain is modest; it improves scheduling behavior but does not remove Python/Future orchestration.
- Remaining dominant target is native multi-file read batching or direct read-to-calibration stream feeding.
- Timing is still a warm-cache Windows run and should be repeated before release claims.

## Next Step

- Move the resident FITS read queue and batch filling deeper into native code so the CPU scheduler feeds pinned buffers/calibration streams with less Python orchestration.

## Clean-Room Compliance

- Compliant. This gate uses GLASS-owned scheduler logic, GLASS artifacts, FITS headers/data, and user-generated benchmark/reference outputs only.
- No external proprietary implementation source was read, copied, summarized, or reworked.
