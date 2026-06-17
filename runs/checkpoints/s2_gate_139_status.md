# S2-Gate 139 Status: Localized Tile-Local Apply Verification

## Gate

S2-Gate 139: Localized Tile-Local Apply Verification.

## Completed

- Added `glass tile-local-apply-verify`.
- The command measures selected tile-local replay/subset extents directly from
  baseline master, candidate master, and reference master images.
- It applies the same GLASS-to-reference scale/offset/clip transform used by
  benchmark compare.
- It can mask tile pixels by coverage and minimum coverage.
- It emits per-tile signed mean, mean absolute residual, median absolute
  residual, RMS, p90/p99, max absolute residual, compared pixels, and measured
  improvement flags.
- It emits summary-level measured before/after mean absolute residual, RMS,
  improved tile counts, pass/fail status, and recommendation.
- Pass logic is tied to the policy signal used by the replay: all selected
  tiles must move signed mean residual toward zero, all selected tiles must
  improve RMS, and the selected-tile aggregate mean absolute residual and RMS
  must improve.

## Real-Data Artifacts

- Verification JSON:
  `C:\glass_runs\phase2_s2_gate_139_tile_local_verify\subset2_local_verify.json`
- Verification Markdown:
  `C:\glass_runs\phase2_s2_gate_139_tile_local_verify\subset2_local_verify.md`
- Candidate run verified:
  `C:\glass_runs\phase2_s2_gate_138_tile_local_subset\agr0p8_apply_signed_mean_subset2`
- Replay subset verified:
  `C:\glass_runs\phase2_s2_gate_138_tile_local_subset\f100_f110_signed_mean_nonoverlap_subset.json`
- Doctor:
  `runs/checkpoints/s2_gate_139_doctor.json`

## Commands

- `.\.venv\Scripts\python.exe -m pytest -q tests\test_tile_local_apply_verify.py tests\test_cli_smoke.py::test_cli_help_commands`
- `.\.venv\Scripts\ruff.exe check src\glass\report\tile_local_apply_verify.py tests\test_tile_local_apply_verify.py src\glass\cli.py`
- `.\.venv\Scripts\glass.exe tile-local-apply-verify --baseline C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200\integration\resident_master_H.fits --candidate C:\glass_runs\phase2_s2_gate_138_tile_local_subset\agr0p8_apply_signed_mean_subset2\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --replay C:\glass_runs\phase2_s2_gate_138_tile_local_subset\f100_f110_signed_mean_nonoverlap_subset.json --coverage-map C:\glass_runs\phase2_s2_gate_138_tile_local_subset\agr0p8_apply_signed_mean_subset2\integration\resident_coverage_map_H.fits --min-coverage 190 --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --out C:\glass_runs\phase2_s2_gate_139_tile_local_verify\subset2_local_verify.json --markdown C:\glass_runs\phase2_s2_gate_139_tile_local_verify\subset2_local_verify.md --fail-on-failed`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\ruff.exe check .`
- `.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_139_doctor.json`

## Test Results

- Focused tests: 3 passed.
- Full suite: 366 passed in 20.32 s.
- Ruff: all checks passed.

## Real-Data Results

- Verified tiles: 2.
- Coverage mask: candidate coverage map, min coverage 190.
- Summary status: passed.
- Recommendation: `measured_local_improvement`.
- Signed mean improved tiles: 2 / 2.
- RMS improved tiles: 2 / 2.
- Mean absolute residual improved tiles: 1 / 2.
- Aggregate mean absolute residual before: 0.00031415285365338577.
- Aggregate mean absolute residual after: 0.00030439992008371566.
- Aggregate mean absolute residual delta: -0.000009752933569670108.
- Aggregate RMS before: 0.0012370662946636945.
- Aggregate RMS after: 0.0012260909500796018.
- Aggregate RMS delta: -0.000010975344584092687.
- Tile 0 signed-mean abs delta: -0.00004257350787773543.
- Tile 0 mean-abs delta: -0.00003508457759369976.
- Tile 0 RMS delta: -0.000013335016901076411.
- Tile 1 signed-mean abs delta: -0.00004201708582866277.
- Tile 1 mean-abs delta: +0.000015578710454359546.
- Tile 1 RMS delta: -0.000008615672267108963.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Native CUDA backend: loaded.

## Known Limitations

- This verification reads bounded tile pixels for diagnostics and does not
  mutate pipeline outputs.
- Tile 1 improved signed mean and RMS but had a slight mean-absolute-residual
  increase, so future promotion logic should remain multi-metric and avoid
  relying on a single residual statistic.
- Verification covers the selected non-overlapping replay subset only; it does
  not prove unbounded global tile-local policies are safe.
- Tile-local apply remains opt-in. The resident default remains `record`.

## Next Step

S2-Gate 140 should use measured verification results to rank and accept/reject
candidate tile-local subsets automatically, then run a small sweep over
strategy and max-tile settings with a hard measured-improvement contract.

## Clean-Room Compliance

Compliant. This gate used GLASS artifacts, user-generated black-box reference
outputs, benchmark contracts, and image comparisons only. It did not read,
copy, summarize, or rework proprietary implementation source.
