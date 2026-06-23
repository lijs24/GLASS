# S2-Gate 538 Status: Resident Compact Artifact Serialization

## Gate

S2-Gate 538

## Completed

- Added an explicit compact JSON mode to `glass.io.json_io.write_json()`.
- Kept pretty JSON as the default behavior for normal callers.
- Routed large resident CUDA machine artifacts through compact JSON:
  - `calibration_artifacts.json`;
  - `frame_accounting.json`;
  - `registration_results.json`;
  - `resident_artifacts.json`;
  - `resident_frame_masks.json`;
  - `resident_registration_quality.json`;
  - `integration_results.json`.
- Left smaller resident contract/cache files in pretty format for direct human
  inspection.
- Added JSON I/O tests for default pretty output and compact round-trip output.
- Ran a real 200-light A/B against Gate537 and confirmed all six FITS output
  maps remain bit-identical.

## Commands Run

- `.venv\Scripts\python.exe -m compileall -q src\glass\io\json_io.py src\glass\engine\frame_accounting.py src\glass\engine\resident_calibration_artifacts.py src\glass\engine\resident_cuda.py`
- `.venv\Scripts\python.exe -m pytest -q tests/test_json_io.py tests/test_frame_accounting.py tests/test_resident_calibration_artifacts.py tests/test_resident_cuda_run.py::test_cli_resident_cuda_callback_queue_clamps_fetch_batch_to_prefetch_depth tests/test_resident_cuda_run.py::test_cli_resident_cuda_shared_master_cache_reuses_across_runs`
- `.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate538_compact_artifacts\runs_20260623_134508\compact_default --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused tests: `11 passed in 0.84s`.
- Full pytest: `1178 passed in 42.86s`.

## Real 200-Light Results

- Baseline Gate537:
  `C:\glass_runs\phase2_s2_gate537_real_ab\runs_20260623_133539\current_head_default`.
- Gate538:
  `C:\glass_runs\phase2_s2_gate538_compact_artifacts\runs_20260623_134508\compact_default`.
- Shell elapsed:
  - Gate537: `5.3052115 s`;
  - Gate538: `5.4324295 s`.
- Internal `run_timing.json`:
  - Gate537: `4.940610599995125 s`;
  - Gate538: `5.0686043000314385 s`.
- No runtime speedup is claimed for this gate. The compact run is slightly
  slower within observed disk/system variance.

## Artifact Footprint

- Selected resident JSON artifacts:
  - Gate537 total: `4,797,890` bytes;
  - Gate538 total: `3,626,742` bytes;
  - reduction: `1,171,148` bytes;
  - reduction fraction: `0.24409646740546365`.
- Largest reductions:
  - `resident_artifacts.json`: `1,233,736` to `775,141` bytes;
  - `frame_accounting.json`: `1,572,658` to `1,302,384` bytes;
  - `registration_results.json`: `1,434,189` to `1,164,202` bytes.

## Numerical Validation

- Gate538 was compared against Gate537 by SHA-256.
- Master, weight map, coverage map, low rejection map, high rejection map, and
  DQ map are all bitwise identical.
- Because the FITS outputs are bit-identical to Gate537, the Gate537
  coverage-masked WBPP compare remains applicable:
  - shape match: true;
  - RMS: `0.0004279821839256963`;
  - p99 abs diff: `0.0001313822576776147`;
  - coverage fraction: `0.9892770479074376`.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Known Limits

- This gate reduces resident artifact size, but does not improve measured
  200-light wall time.
- Compact JSON is intended for machine artifacts; small contract/cache files
  still use pretty output for inspection.
- The main Phase 2 performance targets remain I/O/upload/calibration overlap,
  resident orchestration, and any future pixel-path optimization that preserves
  numerical evidence.

## Next

- Return to resident light-loop and I/O/upload/calibration optimization. Do not
  spend more gates on serialization/report paths unless they demonstrably block
  the default runtime or correctness evidence chain.

## Clean-Room

- Compliant. This gate uses GLASS code, GLASS-generated artifacts, and
  user-owned benchmark images only. It does not inspect or copy
  PixInsight/WBPP/PJSR source or modify input directories.
