# S2-Gate 675 Status: Unit-Weight Map From Coverage

## Gate

S2-Gate 675 - resident CUDA unit-positive weight-map transfer reduction.

## Completed

- Implemented a native CUDA resident hardened winsorized `uint16` count-map optimization for unit-positive `0/1` weights.
- When full audit maps are requested and `weight_map == coverage_map.astype(float32)`, the native path now:
  - skips device `float32` weight-map allocation;
  - passes `nullptr` for the device weight-map output;
  - downloads the existing `uint16` coverage map;
  - synthesizes the host-returned `float32` weight map from coverage.
- Added native timing/profile fields:
  - `unit_positive_weight_map_from_coverage`;
  - `weight_map_device_materialized`;
  - `weight_map_download_source`;
  - `returned_arrays`;
  - `device_downloaded_arrays`;
  - `device_download_s`;
  - `weight_map_host_synthesis_s`;
  - `host_synthesized_bytes`.
- Preserved previous behavior for non-unit weights, `float32` count maps, `master_weight`, and `master_only`.
- Added CUDA/CLI tests and updated algorithm, integration, validation, and limitation docs.

## Commands Run

- `.\.venv\Scripts\cmake.exe --build build --config Release --target _glass_cuda_native`
  - failed before VS environment initialization because `cl.exe` could not find `limits.h`.
- `cmd.exe /d /s /c "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && ".\.venv\Scripts\cmake.exe" --build build --config Release --target _glass_cuda_native`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_map_from_coverage tests/test_resident_cuda_run.py::test_cli_resident_cuda_hardened_winsorized_matches_cpu_baseline`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py tests/test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate675_unit_weight_map_from_coverage\runs_20260626_090000\default_unit_weight_map_from_coverage --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
- `.\.venv\Scripts\python.exe -m glass.cli phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate675_unit_weight_map_from_coverage\runs_20260626_090000\default_unit_weight_map_from_coverage --out C:\glass_runs\phase2_s2_gate675_unit_weight_map_from_coverage\runs_20260626_090000\gate675_phase2_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate675_unit_weight_map_from_coverage\runs_20260626_090000\gate675_phase2_mainline_audit.md --min-lights 200 --min-active-frames 190 --max-masked-frames 10 --fail-on-not-green`
- `.\.venv\Scripts\python.exe -m glass.cli resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate674_lifecycle_mainline\runs_20260626_080000\default_lifecycle_guard_final --candidate-run C:\glass_runs\phase2_s2_gate675_unit_weight_map_from_coverage\runs_20260626_090000\default_unit_weight_map_from_coverage --out C:\glass_runs\phase2_s2_gate675_unit_weight_map_from_coverage\runs_20260626_090000\gate675_vs_gate674_regression.json --markdown C:\glass_runs\phase2_s2_gate675_unit_weight_map_from_coverage\runs_20260626_090000\gate675_vs_gate674_regression.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused CUDA/CLI tests: `2 passed in 1.42s`.
- Resident CUDA files: `207 passed in 21.13s`.
- Full pytest: `1419 passed in 64.74s`.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver version: 596.21.
- Build CUDA toolkit used by the current native build: CUDA 13.2.

## Real 200-Light Validation

- Candidate run:
  `C:\glass_runs\phase2_s2_gate675_unit_weight_map_from_coverage\runs_20260626_090000\default_unit_weight_map_from_coverage`.
- Phase 2 mainline audit:
  `C:\glass_runs\phase2_s2_gate675_unit_weight_map_from_coverage\runs_20260626_090000\gate675_phase2_mainline_audit.json`.
  - Status: passed.
  - Failed checks: `[]`.
  - Input lights: `200`.
  - Active frames: `193`.
- Gate674 regression:
  `C:\glass_runs\phase2_s2_gate675_unit_weight_map_from_coverage\runs_20260626_090000\gate675_vs_gate674_regression.json`.
  - Status: passed.
  - Failed checks: `[]`.
  - Elapsed ratio: `1.0077329966094555`.
  - Determinism summary: no artifact, frame-accounting, frame-signature, registration, output, or numerical drift.

## Timing And Transfer Evidence

Gate674 baseline:

- Total elapsed: `12.066693499917164 s`.
- Resident integration: `3.323810000088997 s`.
- Hardened native total: `3.3237519999966025 s`.
- Native kernel sync: `3.192917 s`.
- Native `downloaded_arrays`: `5`.
- Native `downloaded_bytes`: `863116800`.

Gate675 candidate:

- Total elapsed: `12.160005199839361 s`.
- Resident integration: `3.2761442000046372 s`.
- Hardened native total: `3.276064500096254 s`.
- Native kernel sync: `3.1436261 s`.
- Native `downloaded_arrays`: `4`.
- Native `returned_arrays`: `5`.
- Native `downloaded_bytes`: `616512000`.
- Native `host_synthesized_bytes`: `246604800`.
- `weight_map_download_source`: `coverage_map_uint16_host_expand`.
- `weight_map_device_materialized`: `false`.

Interpretation:

- The integration component improved to `0.985659288562498x` of Gate674.
- Native kernel sync improved to `0.9845624236395748x` of Gate674.
- Total runtime was `1.0077329966094555x` of Gate674 because the upstream `light_read_upload_calibrate` component was slower in this single run (`1.0392005805329838x`).
- The gate is accepted as a transfer/memory simplification with verified output parity, not as a broad end-to-end speed breakthrough.

## Known Limitations

- The optimization only applies when unit-positive `0/1` weights, full diagnostic maps, and `uint16` count maps make `weight_map` exactly derivable from coverage.
- The Python/API result still returns a `float32` `weight_map` for compatibility.
- This does not solve the larger resident order-statistic reducer cost.
- The single real run shows integration-stage improvement but not total-runtime improvement due to unrelated upstream variance.

## Next Step

Return to a larger Phase 2 mainline target:

- light I/O + upload + calibration overlap with pinned/multi-buffer scheduling, or
- a redesigned resident winsorized order-statistic reducer with less per-pixel frame-axis rescanning.

## Clean-Room Compliance

Compliant. This gate modifies GLASS-owned CUDA/native wrapper code, tests, and docs only. It does not inspect, copy, summarize, or rework external implementation source. User image directories were treated as read-only; all outputs were written under `C:\glass_runs`.
