# S2-Gate 433 Status: Automatic Resident Registration Quality Gate

## Gate

- Gate: S2-Gate 433
- Scope: Phase 2 runtime algorithm and auditability, not release/default-promotion/report-contract-only handoff.
- Objective: replace the Gate432 manual resident frame mask with an automatic, auditable resident registration-quality decision path.

## Completed

- Added `src/glass/engine/resident_registration_quality.py`.
- Added resident CLI/run options:
  - `--resident-registration-quality-gate auto|off|warn|exclude`;
  - `--resident-registration-quality-min-inliers`;
  - `--resident-registration-quality-max-rms-px`.
- Default behavior:
  - `auto` resolves to `exclude` for `similarity_cuda_triangle`;
  - `auto` resolves to `off` for non-triangle resident registration modes;
  - default minimum inliers is `4`;
  - RMS is recorded but not a default hard threshold;
  - capacity-limited tiny catalogs are not hard-rejected merely because they have fewer than 4 available stars.
- Integrated the decision before accepted resident triangle frames enter warp or fused integration.
- Wrote a first-class `resident_registration_quality.json` contract and linked its summary from `resident_artifacts.json`.
- Updated `docs/algorithm_sources.md` and `docs/phase2_algorithm_hardening.md`.

## Commands

- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_registration_quality.py`
- `.\.venv\Scripts\python.exe -m glass.cli run --help`
- `.\.venv\Scripts\python.exe -m glass.cli audit --help`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_registration_quality.py tests\test_resident_cuda_run.py tests\test_resident_result_contract.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m glass.cli run --plan "C:\glass_runs\final_m38_h_200\glass_current_20260514_154556\processing_plan.json" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate433_auto_quality_20260619" --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit`
- `.\.venv\Scripts\python.exe -m glass.cli report --run "C:\glass_runs\final_m38_h_200\glass_s2_gate433_auto_quality_20260619" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate433_auto_quality_20260619\report.html"`
- `.\.venv\Scripts\python.exe -m glass.cli compare --glass "C:\glass_runs\final_m38_h_200\glass_s2_gate433_auto_quality_20260619\integration\resident_master_H.fits" --reference "C:\glass_runs\final_m38_h_200\glass_s2_gate432_auto_grid_masked_20260619\integration\resident_master_H.fits" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate433_auto_quality_vs_gate432_masked_compare.html" --glass-time-seconds 28.39727759998641 --reference-time-seconds 27.910495800024364 --glass-label "Gate433 auto quality" --reference-label "Gate432 explicit mask"`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_433_cuda_doctor.json`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Results

- Focused new unit tests: `6 passed in 0.05 s`.
- Focused resident/CLI regression set: `100 passed in 9.52 s`.
- Full pytest: `1013 passed in 38.12 s`.
- Real run directory:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate433_auto_quality_20260619`.
- Real run frame counts:
  `192 ok`, `7 excluded`, `1 reference`.
- Auto-rejected frame IDs:
  `F000160`, `F000213`, `F000214`, `F000215`, `F000216`, `F000217`, `F000218`.
- Rejected-frame reason:
  all seven had `registration_inliers_below_min` with 2-3 inliers, 48 reference stars, 48 moving stars, and `triangle_translation_refine_status=insufficient_inliers`.
- Total elapsed: `28.397278 s`.
- Stage timings:
  - `light_read_upload_calibrate`: `17.485519 s`;
  - `resident_registration_warp`: `1.633846 s`;
  - `resident_integration`: `0.291435 s`;
  - output write: `2.577477 s`.
- Estimated peak VRAM: `47.311736 GiB`.
- Gate433 auto-quality vs Gate432 explicit-mask compare:
  - shape match: true;
  - p50/p90/p99 absolute delta: `0.0` / `0.0` / `0.0` ADU;
  - RMS delta: `0.0`;
  - relative RMS: `0.0`.

## CUDA

- CUDA wrapper importable: yes.
- Native extension loaded: yes.
- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.
- CUDA doctor artifact: `runs/checkpoints/s2_gate_433_cuda_doctor.json`.

## Artifacts

- Checkpoint summary:
  `runs/checkpoints/s2_gate_433_auto_quality_summary.json`.
- CUDA doctor:
  `runs/checkpoints/s2_gate_433_cuda_doctor.json`.
- Real run quality contract:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate433_auto_quality_20260619\resident_registration_quality.json`.
- Real run report:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate433_auto_quality_20260619\report.html`.
- Real run master:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate433_auto_quality_20260619\integration\resident_master_H.fits`.
- Compare report:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate433_auto_quality_vs_gate432_masked_compare.html`.

## Known Limitations

- The Gate433 default is a project-defined resident triangle admission policy derived from GLASS Gate431/Gate432 evidence. It is not a claim of PixInsight-equivalent frame rejection.
- RMS thresholding is available but disabled by default because the real M38 run retained some frames near or above 2 px RMS while still matching the desired accepted set.
- HTML report currently includes the run artifacts, but the new `resident_registration_quality.json` deserves a first-class compact table in the next gate.

## Next Step

- S2-Gate 434: promote resident registration quality decisions into frame accounting/report/contract surfaces so users can distinguish automatic quality exclusions from manual excludes, generic failures, and ordinary zero-weight frames.

## Clean-Room Compliance

- No PixInsight/WBPP source code was read, copied, summarized, or reworked.
- Validation used GLASS-owned run artifacts and the user's local input dataset as read-only data.
- No input image directory was modified.
