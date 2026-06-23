# S2-Gate 519 Status: Native Host DQ Map Contract Fast Path

## Gate

- Gate: S2-Gate 519
- Date: 2026-06-23
- Scope: substantive Phase 2 runtime/DQ work, not release/default-promotion/report-only work.

## Completed

- Added native `_glass_cuda_native.resident_dq_map_host_f32`.
- Added `glass_cuda.resident_dq_map_host_f32_available()` and
  `glass_cuda.resident_dq_map_host_f32(...)`.
- Routed resident `_resident_dq_map(..., return_stats=True)` to the native
  host single-pass scanner when available, while retaining the Python fallback.
- Preserved downstream DQ provenance compatibility by keeping
  `stats_source="resident_dq_map_single_pass"` and adding
  `stats_backend="native_host"`.
- Added native-vs-Python DQ parity coverage.
- Ran a real 200-light M38 H-alpha A/B after implementation.
- Checked C: drive/project storage first: C: still had about 449 GB free, so no
  GLASS run artifacts or master caches were deleted.

## Commands

- `Get-PSDrive -PSProvider FileSystem`
- `git status --short`
- `.\.venv\Scripts\python.exe -m ruff check src\glass_cuda.py src\glass\engine\resident_cuda.py tests\test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py -k "resident_dq_map or resident_dq_coverage_provenance"`
- `cmd /c "call C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build --config Release"`
- `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache --out ...\warm_auto`
- Same command for `...\warm_repeat_auto`.
- Same command with `--resident-master-cache-policy run --out ...\full_run_cache_policy_run`.
- `.\.venv\Scripts\glass.exe compare --glass ...\warm_repeat_auto\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out ...\compare_current_vs_wbpp.html`
- `.\.venv\Scripts\glass.exe compare --glass ...\warm_repeat_auto\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\warm_repeat_auto\integration\resident_master_H.fits --out ...\compare_current_vs_gate518.html`
- `.\.venv\Scripts\glass.exe compare --glass ...\full_run_cache_policy_run\integration\resident_master_H.fits --reference ...\warm_repeat_auto\integration\resident_master_H.fits --out ...\compare_full_run_vs_warm_repeat.html`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe doctor`

## Test Results

- Ruff: passed.
- Focused DQ tests: `7 passed`.
- Full pytest: `1162 passed in 43.32s`.
- `glass doctor`: passed.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Local native build: CUDA Toolkit 13.2 through Visual Studio DevCmd.

## Real 200-Light A/B

- Run root: `C:\glass_runs\phase2_s2_gate519_native_dq_ab\runs_20260623_100321`.
- Input plan: `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`.
- Input light frames: 200.
- Active integrated frames: 193.
- WBPP black-box active integrated frames: 193.
- WBPP black-box elapsed time: `1092.541 s`.

Warm-repeat with shared master cache:

- Shell elapsed: `11.1992665 s`.
- Internal elapsed: `10.82136449997779 s`.
- Speedup vs WBPP: `100.96148226060053x` internal,
  `97.55469253276542x` shell.
- Component timings:
  - light read/upload/calibration: `2.5335453000152484 s`;
  - master build/load: `0.4051558000501245 s`;
  - resident registration component: `1.962568399430535 s`;
  - registration warp: `0.47296360082691535 s`;
  - resident integration: `0.3025613999925554 s`;
  - output write: `0.3603093000128865 s`.

Full run with per-run master cache policy:

- Shell elapsed: `15.6334588 s`.
- Internal elapsed: `15.253281100012828 s`.
- Speedup vs WBPP: `71.62662202554446x` internal,
  `69.88479094594217x` shell.
- Component timings:
  - light read/upload/calibration: `6.990396499983035 s`;
  - master build/load: `4.865560800011735 s`;
  - resident registration component: `1.951897299406118 s`;
  - registration warp: `0.47139239992247894 s`;
  - resident integration: `0.301384299993515 s`;
  - output write: `0.406052699952852 s`.

## Result Validation

- Gate519 warm-repeat master vs Gate518 warm-repeat master: RMS `0.0`, max
  absolute difference `0.0`.
- Gate519 full-run master vs Gate519 warm-repeat master: RMS `0.0`, max
  absolute difference `0.0`.
- Gate519 GLASS vs WBPP black-box master: shape matched. Robust linear fit on
  fit pixels: RMS `0.0015009512947433384`, p99 absolute difference
  `0.00034034321741462114`, max absolute difference `0.0669627725356087`.

## Artifacts

- Summary JSON:
  `runs/checkpoints/s2_gate_519_native_dq_real_ab_summary.json`.
- Full run summary:
  `C:\glass_runs\phase2_s2_gate519_native_dq_ab\runs_20260623_100321\gate519_native_dq_real_ab_summary.json`.
- Compare reports:
  - `C:\glass_runs\phase2_s2_gate519_native_dq_ab\runs_20260623_100321\compare_current_vs_wbpp.html`
  - `C:\glass_runs\phase2_s2_gate519_native_dq_ab\runs_20260623_100321\compare_current_vs_gate518.html`
  - `C:\glass_runs\phase2_s2_gate519_native_dq_ab\runs_20260623_100321\compare_full_run_vs_warm_repeat.html`

## Known Limitations

- The native DQ fast path is host-side. It reduces Python scanning and preserves
  contract fields, but it is not yet a fully GPU-resident DQ export kernel.
- Gate519 did not materially improve the full 200-light end-to-end wall time;
  the current bottlenecks are light pipeline orchestration/I/O overlap and
  resident registration/warp batching.
- The local native build emitted an existing MSVC signed/unsigned warning at
  `cpp/src/native_bindings.cpp(12192)`, unrelated to this gate.

## Next Step

- Return to substantive runtime work: reduce resident light pipeline
  Python-orchestration/unaccounted time and batch more of registration/warp
  while keeping the 200-light A/B and WBPP comparison as the acceptance loop.

## Clean-Room Compliance

- Compliant. This gate used GLASS code, GLASS-generated artifacts, user-owned
  200-light data, and user-generated WBPP black-box outputs/timing only.
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or used.
- Input image directories were treated as read-only.
