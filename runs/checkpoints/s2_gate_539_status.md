# S2-Gate 539 Status: Resident Prefetch-24 Default Retune

## Gate

- Gate: S2-Gate 539
- Scope: real 200-light resident CUDA default-path performance, focused on the
  I/O + upload + calibration pipeline.
- Status: green

## Completed

- Profiled the current default resident route on the M38 H-alpha 200-light
  benchmark with the shared master cache.
- Ran same-cache prefetch probes at 16, 24, and 32 frames.
- Changed the default `throughput-v3-io` resident preset from 32 to 24 prefetch
  frames.
- Kept the rest of the preset unchanged: 16 workers, queued refill, pinned-ring
  H2D, calibration batch 16, 4 streams, wave 4, callback-queue release.
- Updated benchmark-contract expectations and CLI/acceptance tests.
- Ran a real default 200-light validation without an explicit
  `--resident-prefetch-frames` override.
- Compared Gate539 output against Gate538 by SHA-256 for all six resident maps.
- Ran a fresh WBPP black-box compare for the Gate539 default output.

## Commands

- `.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py::test_resident_runtime_preset_throughput_v3_io_applies_probe_values tests/test_cli_smoke.py::test_resident_runtime_preset_defaults_to_throughput_v3_io tests/test_acceptance_audit.py::test_acceptance_audit_accepts_io_runtime_preset_from_artifact`
- `.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate539_prefetch24_default\runs_20260623_135359\default_prefetch24 --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- `.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate539_prefetch24_default\runs_20260623_135359\default_prefetch24\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate539_prefetch24_default\runs_20260623_135359\default_prefetch24\compare_vs_wbpp_fastintegration_scaled_coverage190.json --glass-time-seconds 5.4351132999999994 --reference-time-seconds 1092.541 --glass-label "GLASS Gate539 resident CUDA default prefetch24" --reference-label "WBPP black-box fastIntegration" --glass-scale=1.545301547671945e-05 --glass-offset=-9.765786009702931e-05 --ignore-border-px 128 --glass-coverage-map C:\glass_runs\phase2_s2_gate539_prefetch24_default\runs_20260623_135359\default_prefetch24\integration\resident_coverage_map_H.fits --min-coverage 190`
- `.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py::test_resident_runtime_preset_throughput_v3_io_applies_probe_values tests/test_cli_smoke.py::test_resident_runtime_preset_defaults_to_throughput_v3_io tests/test_acceptance_audit.py::test_acceptance_audit_accepts_io_runtime_preset_from_artifact tests/test_acceptance_audit.py::test_acceptance_audit_accepts_fused_runtime_preset_from_artifact tests/test_speedup_report.py`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused preset/acceptance/speedup tests: `7 passed in 0.26s`.
- Full suite: `1178 passed in 43.14s`.

## Real 200-Light Evidence

- Default validation run:
  `C:\glass_runs\phase2_s2_gate539_prefetch24_default\runs_20260623_135359\default_prefetch24`.
- Shell elapsed: `5.435113299999999 s`.
- Internal elapsed: `5.064197100000456 s`.
- Effective preset: `throughput-v3-io`.
- Explicit overrides: none.
- Effective prefetch frames: `24`.
- Pinned host buffer: `2.756023406982422 GiB`.

## Probe Results

- Prefetch 16: `5.083839799975976 s` internal, pinned host
  `1.8373489379882812 GiB`.
- Prefetch 24: `4.96331859997008 s` internal, pinned host
  `2.756023406982422 GiB`.
- Prefetch 32: `5.106228700024076 s` internal, pinned host
  `3.6746978759765625 GiB`.
- All probe outputs were bitwise identical to Gate538 for master, weight,
  coverage, low rejection, high rejection, and DQ maps.

## Stage Timing

- Light read/upload/calibrate: `2.5950499000027776 s`.
- Light read wait wall: `1.0576936997822486 s`.
- Light read worker cumulative: `28.187955199857242 s`.
- Master build/load: `0.3202941999770701 s`.
- Resident registration/warp: `0.25548409996554255 s`.
- Resident integration: `0.3045270000002347 s`.
- Output write: `0.2477364999940619 s`.

## Numerical Results

- Gate539 master, weight map, coverage map, low/high rejection maps, and DQ map
  are bitwise identical to Gate538.
- WBPP black-box compare:
  - RMS diff: `0.0004279821839256963`.
  - p99 abs diff: `0.0001313822576776147`.
  - coverage fraction: `0.9892770479074376`.
  - compared pixels: `56997300`.
  - WBPP elapsed: `1092.541 s`.
  - Gate539 shell speedup versus WBPP: `201.01531278106017x`.

## CUDA

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Native backend: yes.

## Known Limits

- This gate is a default scheduling retune, not a new science algorithm.
- The read/upload/calibration pipeline remains the largest material target.
- Different storage, CPU contention, or datasets may prefer a different depth;
  explicit `--resident-prefetch-frames` remains available.

## Next Step

- Implement a more material multi-buffer read/upload/calibrate optimization or
  deeper resident batching while preserving bitwise 200-light outputs.

## Clean-Room Compliance

- Compliant.
- This gate used only GLASS timing artifacts, GLASS output hashes, and
  user-generated WBPP black-box output/timing.
- No external implementation source was read, copied, summarized, or reworked.
