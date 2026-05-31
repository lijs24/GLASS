# S2 Gate 77 Status: Batched Resident Prefetch Slot Release

## Gate
- Gate: S2 Gate 77
- Name: Batched resident prefetch slot release
- Date: 2026-06-01
- Status: green

## Completed
- Added batched prefetch slot release for resident CUDA calibration scheduling.
- Preserved the existing single-frame `release(index)` API and routed it through `release_many`.
- Changed callback-queue, H2D-event, and synchronous batch release paths to release all completed slots with one refill pass.
- Added resident I/O diagnostics:
  - `prefetch_fill_call_count`
  - `prefetch_fill_submit_count`
  - `prefetch_release_batch_count`
  - `prefetch_release_fill_model`
- Updated resident CUDA tests to lock the new batching counters and model string.
- Updated Phase 2 plan and algorithm source ledger.

## Commands Run
- `.\.venv\Scripts\python.exe -m py_compile src\glass\engine\resident_cuda.py`
- `.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py tests\test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_batch_wave_releases_prefetch_slots tests\test_resident_cuda_run.py::test_cli_resident_cuda_callback_queue_releases_inside_native_batch`
- `.\.venv\Scripts\python.exe -m ruff check .`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_77_200\batched_release_callback_batch8_stream4_wave4_20260601\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_70_200\reused_calibration_events_b_20260601\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_77_200\compare_gate77_batched_release_vs_gate70b.html --glass-time-seconds 12.25082019995898 --reference-time-seconds 12.200752399861813 --glass-label Gate77_batched_release --reference-label Gate70_event_reuse_b --ignore-border-px 16`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_77_200\batched_release_callback_batch8_stream4_wave4_20260601\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_73_200\wave_batch8_stream4_wave2_20260601\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_77_200\compare_gate77_batched_release_vs_gate73.html --glass-time-seconds 12.25082019995898 --reference-time-seconds 12.239080199971795 --glass-label Gate77_batched_release --reference-label Gate73_wave2 --ignore-border-px 16`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_77_200\batched_release_callback_batch8_stream4_wave4_20260601\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_76_200\callback_queue_batch8_stream4_wave4_20260601\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_77_200\compare_gate77_batched_release_vs_gate76.html --glass-time-seconds 12.25082019995898 --reference-time-seconds 12.3291659001261 --glass-label Gate77_batched_release --reference-label Gate76_callback_queue --ignore-border-px 16`

## Test Results
- Ruff: passed.
- Full pytest: 280 passed in 11.85 s.
- Focused resident CUDA tests: 2 passed.

## CUDA
- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Native backend: available.

## 200-Light Real Dataset Run
- Run path: `C:\glass_runs\phase2_s2_gate_77_200\batched_release_callback_batch8_stream4_wave4_20260601`
- Backend: resident CUDA native callback queue.
- Lights: 200.
- Batch size: 8.
- Native stream count: 4.
- Callback wave size: 4.
- Integrated frames: 193.
- Zero-weight frames: 7.
- Total time: 12.25082019995898 s.
- Read/upload/calibration phase: 6.283592300023884 s.
- Light read wait wall time: 2.6760934004560113 s.
- Native H2D/calibration wall time: 2.7192865991964936 s.
- Native calibration total time: 2.7076691000000004 s.
- Native sync time: 0.012389899999999999 s.
- Callback time: 0.006470500000000001 s.
- Callback count: 200.
- Callback waves: 50.
- Prefetch release count: 200.
- Prefetch release batch count: 50.
- Prefetch fill call count: 51.
- Prefetch fill submit count: 200.
- Prefetch blocked-no-slot count: 23.

## Result Comparisons
- Gate77 vs Gate70B:
  - Shape match: true.
  - RMS diff: 0.0.
  - Max absolute diff: 0.0.
  - Speed vs Gate70B: 0.9959131062835013x.
  - Report: `C:\glass_runs\phase2_s2_gate_77_200\compare_gate77_batched_release_vs_gate70b.html`
- Gate77 vs Gate73:
  - Shape match: true.
  - RMS diff: 0.0.
  - Max absolute diff: 0.0.
  - Speed vs Gate73: 0.9990416968173915x.
  - Report: `C:\glass_runs\phase2_s2_gate_77_200\compare_gate77_batched_release_vs_gate73.html`
- Gate77 vs Gate76:
  - Shape match: true.
  - RMS diff: 0.0.
  - Max absolute diff: 0.0.
  - Speed vs Gate76: 1.0063951391734067x.
  - Report: `C:\glass_runs\phase2_s2_gate_77_200\compare_gate77_batched_release_vs_gate76.html`

## Known Limitations
- Gate77 improves prefetch slot churn and reduces blocked-no-slot events, but total runtime is still slightly slower than the best Gate70B baseline.
- Native H2D/calibration timing is higher than Gate76 in this run, likely due to scheduling variance and callback/refill interaction.
- Registration/warp and host I/O orchestration remain the main optimization targets.
- This gate does not change scientific math or output pixel values.

## Next Step
- Gate78 should sweep `--resident-prefetch-frames`, `--resident-prefetch-workers`, batch size, stream count, and callback wave size on the 200-light dataset.
- The immediate objective is to preserve the lower blocked-no-slot count while recovering or beating the Gate70B native calibration timing.

## Clean-Room Compliance
- Compliant.
- No PixInsight or WBPP/PJSR source code was read, copied, summarized, or reworked.
- Only GLASS source, generated test outputs, generated benchmark artifacts, and project documentation were used.
- Input image directories remain read-only.
