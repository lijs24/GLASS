# S2-Gate 494 Status

## Gate

- Gate: S2-Gate 494
- Scope: structure-aware CPU baseline for opt-in resident inline `cosmetic`
  source-DQ, plus default 200-light regression.
- Status: green

## Completed

- Added `glass.cpu.cosmetic.detect_isolated_cosmetic_defects`.
- The detector marks a hot/cold pixel only when it is:
  - a strong global median/MAD outlier;
  - a strong local 8-neighbor median outlier;
  - lacking enough same-sign 8-neighbor support.
- Compact star-like structure is protected because neighboring pixels provide
  support; isolated hot/cold defects remain marked.
- Resident `--resident-inline-source-dq cosmetic` now uses the structure-aware
  CPU detector instead of the older global-only cosmetic detector.
- Resident artifacts now record:
  - `source_model=inline_structure_cosmetic_source_dq`;
  - `inline_source_dq_detector=glass.cpu.cosmetic.detect_isolated_cosmetic_defects`.
- Combined source-DQ rows now promote a single inline detector to the top-level
  row, so artifacts are easier to audit.
- Updated Phase 2 hardening and algorithm-source documentation.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m py_compile src\glass\cpu\cosmetic.py src\glass\engine\resident_source_dq.py src\glass\engine\resident_cuda.py src\glass\engine\resident_source_dq_strategy.py
.\.venv\Scripts\python.exe -m ruff check src\glass\cpu\cosmetic.py src\glass\engine\resident_source_dq.py src\glass\engine\resident_cuda.py src\glass\engine\resident_source_dq_strategy.py tests\test_cpu_calibration.py tests\test_resident_source_dq.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_cpu_calibration.py::test_structure_aware_cosmetic_detection_protects_star_cores tests\test_resident_source_dq.py::test_source_invalid_mask_from_inline_cosmetic_flags_hot_and_cold_samples_without_replacement tests\test_resident_source_dq.py::test_source_invalid_mask_from_inline_cosmetic_protects_star_like_structure tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_applies_inline_cosmetic_source_dq_without_cache
.\.venv\Scripts\python.exe -m pytest -q tests\test_cpu_calibration.py tests\test_resident_source_dq.py tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_applies_inline_cosmetic_source_dq_without_cache tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_applies_inline_cosmetic_cuda_source_dq_without_mask_upload tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_skips_inline_cosmetic_cuda_high_fraction_guard
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total --format=csv,noheader
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate494_structure_cosmetic_ab_real\runs\default_runtime_stack_ab_current --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache
.\.venv\Scripts\glass.exe pipeline-contract --run C:\glass_runs\phase2_s2_gate494_structure_cosmetic_ab_real\runs\default_runtime_stack_ab_current --out C:\glass_runs\phase2_s2_gate494_structure_cosmetic_ab_real\contracts\ab_current_pipeline_contract.json --markdown C:\glass_runs\phase2_s2_gate494_structure_cosmetic_ab_real\contracts\ab_current_pipeline_contract.md --pixel-verify
.\.venv\Scripts\glass.exe stack-engine-contract --run C:\glass_runs\phase2_s2_gate494_structure_cosmetic_ab_real\runs\default_runtime_stack_ab_current --out C:\glass_runs\phase2_s2_gate494_structure_cosmetic_ab_real\contracts\ab_current_stack_engine_contract.json --markdown C:\glass_runs\phase2_s2_gate494_structure_cosmetic_ab_real\contracts\ab_current_stack_engine_contract.md --expected-integration-engine cuda_resident_stack --require-default-ready
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate494_structure_cosmetic_ab_real\runs\default_runtime_stack_ab_current\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate493_guard001_ab_real\runs\default_runtime_stack_ab_current\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate494_structure_cosmetic_ab_real\compare\ab_current_vs_gate493_master.html --glass-label GLASS-Gate494 --reference-label GLASS-Gate493
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused structure-aware source-DQ tests: `4 passed in 0.38s`.
- Related CPU/source-DQ/resident CLI regression set: `23 passed in 0.72s`.
- Ruff: all edited Python/test files passed.
- Full pytest: `1138 passed in 40.77s`.

## CUDA

- CUDA available: yes.
- GPU observed before real run:
  `NVIDIA RTX PRO 6000 Blackwell Workstation Edition, 0 %, 825 MiB, 97887 MiB`.

## Synthetic / CLI Validation

- CPU baseline detects an isolated hot pixel while protecting a compact
  star-like 3x3 structure.
- Resident source-DQ invalid-mask helper preserves that same behavior.
- Resident CUDA CLI smoke test proves opt-in inline `cosmetic` still excludes a
  finite hot pixel without materializing a calibrated DQ cache, while recording
  the new detector and model in artifacts.

## Real 200-Light Default Regression

- Run:
  `C:\glass_runs\phase2_s2_gate494_structure_cosmetic_ab_real\runs\default_runtime_stack_ab_current`.
- GLASS elapsed: `17.611496199970134 s`.
- Active frames: `193 / 200`.
- Current vs Gate493 master:
  - RMS: `0.0`.
  - P99 absolute diff: `0.0`.
  - Max absolute diff: `0.0`.
- Pipeline contract: passed with pixel verification.
- StackEngine contract: passed.

## Artifacts

- Default pipeline contract:
  `C:\glass_runs\phase2_s2_gate494_structure_cosmetic_ab_real\contracts\ab_current_pipeline_contract.json`.
- Default StackEngine contract:
  `C:\glass_runs\phase2_s2_gate494_structure_cosmetic_ab_real\contracts\ab_current_stack_engine_contract.json`.
- Default vs Gate493 compare:
  `C:\glass_runs\phase2_s2_gate494_structure_cosmetic_ab_real\compare\ab_current_vs_gate493_master.json`.

## Known Limitations

- The structure-aware detector is CPU baseline only in this gate. The resident
  `cosmetic_cuda` path still uses scalar CUDA thresholding plus the Gate493
  high-fraction guard.
- The detector is deliberately conservative and only targets isolated
  8-neighborhood defects. Broader bad columns, clusters, and camera-specific
  defect maps remain later DQ gates.
- The default production route remains inline source-DQ off, so this gate does
  not change default pixels.

## Next Step

- Port the structure-aware isolated-defect model to resident CUDA so
  `cosmetic_cuda` can apply useful masks on real light frames instead of only
  skipping unsafe global threshold masks.
- After the CUDA port, rerun the 200-light guarded diagnostic and verify that
  applied source-DQ samples remain sparse, active frame count stays >= `190`,
  and the master remains consistent with the default/WBPP comparison envelope.

## Clean-Room Compliance

- Compliant. This gate used GLASS code/artifacts, GLASS-generated tests,
  synthetic fixtures, user-owned M38 H-alpha data, and GLASS default regression
  artifacts.
- No official PixInsight/WBPP/PJSR implementation source was read, summarized,
  copied, or modified.
- Input image directories were treated as read-only.
