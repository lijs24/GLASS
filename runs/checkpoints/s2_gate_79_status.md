# S2 Gate 79 Status: Queued Resident Prefetch Refill

## Gate
- Gate: S2 Gate 79
- Name: Queued resident prefetch refill
- Date: 2026-06-01
- Status: green

## Completed
- Added `--resident-prefetch-refill-mode` to `glass run` and `glass audit`.
- Supported refill modes:
  - `immediate`: existing default behavior;
  - `queued`: release H2D-complete pinned slots in the callback path, then submit prefetch refill work through a lightweight refill executor;
  - `deferred`: diagnostic mode that delays refill until the next consumer flush.
- Added thread-safe prefetch bookkeeping around pending futures, free pinned slots, inflight slot ownership, and queued refill submission.
- Added artifact diagnostics in `resident_io_pipeline`:
  - `prefetch_refill_mode`
  - `prefetch_release_refill_request_count`
  - `prefetch_release_refill_queued_submit_count`
  - `prefetch_release_refill_queued_execute_count`
  - `prefetch_release_refill_queued_coalesced_count`
  - `prefetch_release_refill_wait_s`
  - updated `prefetch_release_fill_model`
- Extended the resident prefetch sweep harness with `--refill-modes` so queued refill can be swept alongside prefetch depth, workers, batch size, stream count, wave size, and release mode.
- Added focused CLI test coverage for queued refill.
- Updated Phase 2 plan and algorithm source ledger.

## Commands Run
- `.\.venv\Scripts\python.exe -m py_compile src\glass\engine\resident_cuda.py src\glass\cli.py src\glass\report\resident_sweep.py benchmarks\bench_resident_prefetch_sweep.py`
- `.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py src\glass\cli.py src\glass\report\resident_sweep.py benchmarks\bench_resident_prefetch_sweep.py tests\test_resident_cuda_run.py tests\test_benchmarks.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_callback_queue_queued_prefetch_refill tests\test_benchmarks.py::test_bench_resident_prefetch_sweep_dry_run_outputs_matrix`
- `.\.venv\Scripts\python.exe -m ruff check .`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe benchmarks\bench_resident_prefetch_sweep.py --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_79_200\queued_refill_20260601 --glass-command .\.venv\Scripts\glass.exe --prefetch-frames 16 --prefetch-workers 8 --batch-frames 8 --streams 4 --wave-frames 2 --release-modes callback_queue --refill-modes queued --baseline-total-seconds 12.200752399861813 --reference-master C:\glass_runs\phase2_s2_gate_70_200\reused_calibration_events_b_20260601\integration\resident_master_H.fits --reference-time-seconds 12.200752399861813 --reference-label Gate70_event_reuse_b --ignore-border-px 16 --common-run-args "<common M38 resident registration, rejection, flat-floor, cache, and exclusion args>"`
- `.\.venv\Scripts\python.exe -c "import glass_cuda, json; print(json.dumps({'cuda_available': glass_cuda.cuda_available(), 'devices': glass_cuda.list_devices()}, indent=2))"`

## Test Results
- Focused queued-refill and sweep dry-run tests: 2 passed.
- Ruff: passed.
- Full pytest: 282 passed in 12.02 s.

## CUDA
- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Native backend: available.

## 200-Light Real Dataset Run
- Run path: `C:\glass_runs\phase2_s2_gate_79_200\queued_refill_20260601\pf16_pw8_b8_s4_w2_callback_queue_rfqueued`
- Sweep summary: `C:\glass_runs\phase2_s2_gate_79_200\queued_refill_20260601\resident_prefetch_sweep_summary.json`
- Baseline for speed ranking: Gate70B, 12.200752399861813 s.
- Compared reference master: Gate70B resident master.
- Variant:
  - `prefetch_frames=16`
  - `prefetch_workers=8`
  - `batch_frames=8`
  - `streams=4`
  - `wave_frames=2`
  - `release_mode=callback_queue`
  - `refill_mode=queued`
- Total elapsed: 12.324775999877602 s.
- Speed vs Gate70B: 0.9899370503758429x.
- Speed vs Gate78 best: 0.992291x approximately.
- Light read/upload/calibration: 6.240909399930388 s.
- Light read wait wall time: 2.7371005984023213 s.
- H2D/calibration/store: 2.6198084983043373 s.
- Native calibration total: 2.6091771999999995 s.
- Native calibration sync: 0.0157111 s.
- Callback wave count: 100.
- Callback release count: 200.
- Callback release time: 0.0063188 s.
- Prefetch blocked-no-slot count: 69.
- Prefetch release batch count: 100.
- Queued refill submit count: 100.
- Queued refill execute count: 100.
- Queued refill coalesced count: 0.
- Queued refill wait time: 0.000001700129359960556 s.
- Input light frames: 200.
- Active frames: 193.
- Zero-weight frames: 7.

## Result Comparison
- Compare report: `C:\glass_runs\phase2_s2_gate_79_200\queued_refill_20260601\compare_pf16_pw8_b8_s4_w2_callback_queue_rfqueued_vs_reference.html`
- Shape match: true.
- Compared pixels after 16 px border ignore: 61139520.
- RMS diff: 0.0.
- Max absolute diff: 0.0.
- P99 absolute diff: 0.0.

## Interpretation
- Queued refill preserves output identity and host-buffer lifetime safety.
- The queued refill wait time is effectively zero, so the consumer does not block waiting for the refill task at batch boundaries.
- On this 200-light run, queued refill does not improve wall time:
  - Gate78 best immediate refill: 12.229778400156647 s.
  - Gate79 queued refill: 12.324775999877602 s.
- The slowdown is mostly native H2D/calibration timing variance/overhead, not read-wait improvement.
- Because the default remains `immediate`, this is not a runtime regression in the production path.

## Known Limitations
- `queued` refill currently submits one refill task per native callback wave in this workload, so it does not coalesce requests on the observed 200-light run.
- The extra refill executor can add scheduling overhead that cancels the tiny callback-time saving.
- `deferred` exists only as a diagnostic mode and is not recommended for throughput runs.
- This gate does not change image math, CUDA kernels, calibration formulas, registration, rejection, or default resident routing.

## Next Step
- S2-Gate 80 should avoid per-wave Python refill task churn if this path is pursued further, for example by coalescing refill notifications over a short window or by moving the ingest queue deeper into native code.
- A more promising high-impact optimization remains resident registration/warp batching and reducing per-frame Python orchestration, because the Gate78/Gate79 refill experiments show only small timing movement around the read/upload/calibration stage.

## Clean-Room Compliance
- Compliant.
- No PixInsight or WBPP/PJSR source code was read, copied, summarized, or reworked.
- The implementation uses GLASS-owned Python scheduling, GLASS CUDA wrapper behavior, and GLASS-generated timing/compare artifacts only.
- Input image directories remain read-only.
