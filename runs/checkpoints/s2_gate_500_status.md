# S2-Gate 500 Status: Resident v3 I/O Preset Default

## Gate

S2-Gate 500

## Completed Content

- Checked C: space before continuing the real A/B path.
  - C: free space: `436.84 GB`.
  - Project-local reclaimable size was small (`runs` about `1.802 GB`, `.venv` about `0.367 GB`, `build` about `0.046 GB`).
  - The large reclaimable items are historical `C:\glass_runs` evidence directories. No cleanup was needed, so no run evidence was deleted.
- Promoted resident CUDA default runtime scheduling from `throughput-v1` to `throughput-v3-io`.
- Kept explicit `--resident-runtime-preset throughput-v1` as a lower-memory fallback.
- Updated:
  - `src/glass/cli.py`
  - `src/glass/report/benchmark_contract.py`
  - `src/glass/report/default_promotion_manifest.py`
  - `src/glass/report/windows_release_matrix.py`
  - `tests/test_cli_smoke.py`
  - `tests/test_acceptance_audit.py`
  - `tests/test_windows_release_matrix.py`
  - `docs/phase2_algorithm_hardening.md`
  - `docs/algorithm_sources.md`

## Real 200-Light A/B

Run root:

`C:\glass_runs\phase2_s2_gate500_io_prefetch_ab_real`

Same-window explicit scheduling A/B:

| Variant | Preset | GLASS run timing total |
| --- | --- | ---: |
| `control_v1` | `throughput-v1` | `7.616734 s` |
| `control_v1_repeat` | `throughput-v1` | `7.604248 s` |
| `candidate_v3_io` | `throughput-v3-io` | `6.813073 s` |
| `candidate_v3_io_repeat` | `throughput-v3-io` | `6.788299 s` |

Average v1: `7.610491 s`.

Average v3-io: `6.800686 s`.

Average same-window improvement: about `10.64%`.

Pipeline evidence:

- read-wait average: `2.289033 s` -> `0.978885 s`;
- prefetch slot blocking: `70` -> `31`;
- pinned host ring: about `1.378 GiB` -> `3.675 GiB`.

Default-route validation after code change:

- Command intentionally omitted `--resident-runtime-preset`.
- Run: `C:\glass_runs\phase2_s2_gate500_io_prefetch_ab_real\runs\default_v3_io_after_code`
- `run_timing.json` recorded `resident_runtime_preset=throughput-v3-io`.
- `resident_io_pipeline` recorded `prefetch_frames=32`, `prefetch_workers=12`, `calibration_batch_requested_frames=16`, `calibration_wave_requested_frames=4`.
- GLASS run timing total: `7.274755600024946 s`.
- Conservative shell wall for compare report: `7.631 s`.
- WBPP black-box time: `1092.541 s`.
- Speedup by GLASS run timing: about `150.184x`.
- Speedup by conservative shell wall compare: `143.17140610667016x`.

## Numerical Results

- Default v3-io vs Gate499 master:
  - bitwise equal: `true`
  - NaN mask equal: `true`
  - RMS/p99/max absolute difference: `0.0 / 0.0 / 0.0`
- Default v3-io vs explicit v3-io master:
  - bitwise equal: `true`
  - NaN mask equal: `true`
  - RMS/p99/max absolute difference: `0.0 / 0.0 / 0.0`
- Explicit v3-io vs same-window v1 master:
  - bitwise equal: `true`
  - NaN mask equal: `true`
  - RMS/p99/max absolute difference: `0.0 / 0.0 / 0.0`
- Default v3-io vs WBPP black-box full-frame/no-coverage compare:
  - RMS: `0.012336290253351909`
  - p99 absolute difference: `0.0007338253874331693`
  - shape match: `true`

Compare artifacts:

- `C:\glass_runs\phase2_s2_gate500_io_prefetch_ab_real\compare\gate500_glass_internal_diffs.json`
- `C:\glass_runs\phase2_s2_gate500_io_prefetch_ab_real\compare\gate500_default_v3_vs_wbpp.json`
- `C:\glass_runs\phase2_s2_gate500_io_prefetch_ab_real\compare\gate500_default_v3_vs_wbpp.html`

## Commands Run

- `nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,memory.free,utilization.gpu --format=csv,noheader`
- `.\.venv\Scripts\glass.exe run ... --resident-runtime-preset throughput-v1 --out C:\glass_runs\phase2_s2_gate500_io_prefetch_ab_real\runs\control_v1`
- `.\.venv\Scripts\glass.exe run ... --resident-runtime-preset throughput-v3-io --out C:\glass_runs\phase2_s2_gate500_io_prefetch_ab_real\runs\candidate_v3_io`
- `.\.venv\Scripts\glass.exe run ... --resident-runtime-preset throughput-v3-io --out C:\glass_runs\phase2_s2_gate500_io_prefetch_ab_real\runs\candidate_v3_io_repeat`
- `.\.venv\Scripts\glass.exe run ... --resident-runtime-preset throughput-v1 --out C:\glass_runs\phase2_s2_gate500_io_prefetch_ab_real\runs\control_v1_repeat`
- `.\.venv\Scripts\glass.exe run ... --out C:\glass_runs\phase2_s2_gate500_io_prefetch_ab_real\runs\default_v3_io_after_code`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate500_io_prefetch_ab_real\runs\default_v3_io_after_code\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate500_io_prefetch_ab_real\compare\gate500_default_v3_vs_wbpp.html --glass-time-seconds 7.631 --reference-time-seconds 1092.541 --glass-label GLASS-default-v3-io --reference-label WBPP-blackbox --glass-scale 0.000015259021896696421`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py::test_resident_runtime_preset_defaults_to_throughput_v3_io tests/test_cli_smoke.py::test_cli_audit_resident_cuda_smoke tests/test_acceptance_audit.py::test_acceptance_audit_accepts_default_route_evidence_for_resident_tokens tests/test_acceptance_audit.py::test_acceptance_audit_accepts_io_runtime_preset_from_artifact tests/test_windows_release_matrix.py::test_windows_release_matrix_passes_blackwell_default`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused tests: `5 passed in 0.50s`.
- Full test suite: `1144 passed in 41.62s`.

## CUDA Status

- CUDA available: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Driver: `596.21`.
- VRAM: `97887 MiB` total, about `95775 MiB` free at the start of the A/B probe.

## Known Limits

- `throughput-v3-io` uses more pinned host memory than `throughput-v1`. On smaller RAM systems, users can explicitly select `--resident-runtime-preset throughput-v1`.
- This gate optimizes the resident I/O/upload/calibration supply path. It does not address the remaining resident registration/warp orchestration overhead.
- Minimal output-map mode remains a speed path. Audit/science modes should be used when full diagnostic maps are required.

## Next Step

Continue the Phase 2 mainline with resident registration/warp orchestration optimization: reduce per-frame CPU/Python launch control, keep star catalogs/descriptors resident where possible, and preserve bitwise output agreement on the 200-light regression.

## Clean-Room Compliance

Compliant. This gate used GLASS-owned code, GLASS-generated artifacts, user-staged input data, and user-generated WBPP black-box timing/output references only. It did not read, copy, summarize, or rework PixInsight/WBPP/PJSR source code and did not modify input image directories.
