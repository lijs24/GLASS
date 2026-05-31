# S2 Gate 78 Status: Resident Prefetch Parameter Sweep

## Gate
- Gate: S2 Gate 78
- Name: Resident prefetch parameter sweep
- Date: 2026-06-01
- Status: green

## Completed
- Added a reusable resident CUDA prefetch sweep harness:
  - `benchmarks/bench_resident_prefetch_sweep.py`
  - `src/glass/report/resident_sweep.py`
- The harness expands parameter grids for:
  - resident prefetch depth;
  - prefetch worker count;
  - calibration batch size;
  - native stream count;
  - calibration wave size;
  - calibration release mode.
- Added `--dry-run`, `--reuse-existing`, JSON summary, Markdown summary, and optional per-variant compare report support.
- Added compact resident run ranking from `run_timing.json`, `resident_artifacts.json`, and `frame_accounting.json`.
- Updated `docs/phase2_algorithm_hardening.md` with S2-Gate 78.
- Updated `docs/algorithm_sources.md` with the clean-room source ledger entry.
- Added benchmark dry-run test coverage.

## Commands Run
- `.\.venv\Scripts\python.exe -m py_compile src\glass\report\resident_sweep.py benchmarks\bench_resident_prefetch_sweep.py`
- `.\.venv\Scripts\python.exe -m ruff check src\glass\report\resident_sweep.py benchmarks\bench_resident_prefetch_sweep.py tests\test_benchmarks.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_benchmarks.py::test_bench_resident_prefetch_sweep_dry_run_outputs_matrix`
- `.\.venv\Scripts\python.exe -m ruff check .`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe benchmarks\bench_resident_prefetch_sweep.py --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_78_200\prefetch_sweep_20260601 --glass-command .\.venv\Scripts\glass.exe --prefetch-frames 16,32 --prefetch-workers 8 --batch-frames 8 --streams 4 --wave-frames 2,4 --release-modes callback_queue --baseline-total-seconds 12.200752399861813 --reference-master C:\glass_runs\phase2_s2_gate_70_200\reused_calibration_events_b_20260601\integration\resident_master_H.fits --reference-time-seconds 12.200752399861813 --reference-label Gate70_event_reuse_b --ignore-border-px 16 --common-run-args "<common M38 resident registration, rejection, flat-floor, cache, and exclusion args>"`
- `.\.venv\Scripts\python.exe benchmarks\bench_resident_prefetch_sweep.py --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_78_200\prefetch_sweep_20260601 --glass-command .\.venv\Scripts\glass.exe --prefetch-frames 16,32 --prefetch-workers 8 --batch-frames 8 --streams 4 --wave-frames 2,4 --release-modes callback_queue --baseline-total-seconds 12.200752399861813 --reuse-existing`

## Test Results
- Focused benchmark dry-run test: passed.
- Ruff: passed.
- Full pytest: 281 passed in 11.95 s.

## CUDA
- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Native backend: available.

## 200-Light Sweep
- Sweep path: `C:\glass_runs\phase2_s2_gate_78_200\prefetch_sweep_20260601`
- Plan: `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`
- Baseline for speed ranking: Gate70B, 12.200752399861813 s.
- Reference master: `C:\glass_runs\phase2_s2_gate_70_200\reused_calibration_events_b_20260601\integration\resident_master_H.fits`
- Common recipe:
  - resident CUDA;
  - pinned-ring H2D;
  - similarity CUDA triangle registration;
  - Lanczos3 resident warp;
  - winsorized sigma rejection;
  - no local normalization;
  - minimal output maps;
  - shared resident master cache;
  - seven known excluded light frames.

| Rank | Variant | Total s | Speed vs Gate70B | Read wait s | Native cal s | Blocked slots | Callback waves | Active/zero-weight |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `pf16_pw8_b8_s4_w2_callback_queue` | 12.229778400156647 | 0.9976266127361341x | 2.816707699559629 | 2.5324103999999994 | 69 | 100 | 193 / 7 |
| 2 | `pf16_pw8_b8_s4_w4_callback_queue` | 12.345894400030375 | 0.9882437030914338x | 2.76397850131616 | 2.6045495 | 23 | 50 | 193 / 7 |
| 3 | `pf32_pw8_b8_s4_w4_callback_queue` | 12.683982899878174 | 0.9619023059372775x | 2.559103200212121 | 2.7235733000000004 | 21 | 50 | 193 / 7 |
| 4 | `pf32_pw8_b8_s4_w2_callback_queue` | 12.749392100144178 | 0.9569673835448076x | 2.55919600231573 | 2.7285350999999998 | 63 | 100 | 193 / 7 |

## Result Comparisons
- All four Gate78 variants compared against Gate70B with:
  - shape match: true;
  - RMS diff: 0.0;
  - max absolute diff: 0.0;
  - ignored border: 16 px.
- Compare artifacts:
  - `C:\glass_runs\phase2_s2_gate_78_200\prefetch_sweep_20260601\compare_pf16_pw8_b8_s4_w2_callback_queue_vs_reference.html`
  - `C:\glass_runs\phase2_s2_gate_78_200\prefetch_sweep_20260601\compare_pf16_pw8_b8_s4_w4_callback_queue_vs_reference.html`
  - `C:\glass_runs\phase2_s2_gate_78_200\prefetch_sweep_20260601\compare_pf32_pw8_b8_s4_w2_callback_queue_vs_reference.html`
  - `C:\glass_runs\phase2_s2_gate_78_200\prefetch_sweep_20260601\compare_pf32_pw8_b8_s4_w4_callback_queue_vs_reference.html`

## Interpretation
- The fastest Gate78 variant is wave 2 with 16 prefetch slots.
- It nearly matches Gate70B but does not beat it: 12.2298 s vs 12.2008 s.
- Wave 2 improves native calibration time versus Gate77 wave 4, but read-wait time remains high.
- Increasing prefetch slots from 16 to 32 reduces blocked-slot counts and read wait, but worsens native calibration time and total runtime in this run.
- This gate therefore keeps callback-queue tuning as evidence, not a new default.

## Known Limitations
- The sweep is hardware, filesystem-cache, and dataset dependent.
- The harness ranks measured runs but does not perform statistical repetitions yet.
- `--common-run-args` is a convenience string for benchmark scripting; complex paths with spaces should use repeated `--common-run-arg=<token>` form or a future config-file mode.
- No image math, CUDA kernels, calibration formulas, registration behavior, or default routing changed in this gate.

## Next Step
- S2-Gate 79 should use the sweep evidence to reduce read-wait variance rather than simply increasing ring depth.
- The most promising next implementation target is decoupling callback-time prefetch refill from native scheduling, for example a background refill notification/queue so callback release returns quickly while the reader pool refills slots outside the native callback path.
- A secondary target is adding repeated-run statistics to the sweep harness so small 0.2-1.0 percent differences are not overinterpreted.

## Clean-Room Compliance
- Compliant.
- No PixInsight or WBPP/PJSR source code was read, copied, summarized, or reworked.
- The harness uses only GLASS commands and GLASS-generated timing, artifact, frame-accounting, and compare files.
- Input image directories remain read-only.
