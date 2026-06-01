# S2-Gate 128 Status: Registration-Motion Weighting Candidate

- Gate: S2-Gate 128
- Date: 2026-06-01
- Status: green, not promoted

## Completed

- Added explicit resident registration-motion weighting controls:
  - `--resident-registration-motion-weighting off|translation_mad`
  - `--resident-registration-motion-threshold-sigma`
  - `--resident-registration-motion-min-weight`
  - `--resident-registration-motion-power`
  - `--resident-registration-motion-scale-floor-px`
- Added a clean-room `translation_mad` policy:
  - groups registration matrices by orientation cluster (`trace`/`determinant` sign)
  - computes robust translation center and MAD scale per cluster
  - applies a smooth multiplier floor to high-score motion outliers
  - composes after ordinary integration weighting and triangle agreement downweighting
- Added per-frame and per-run artifacts in `resident_artifacts.json`.
- Added registration warnings for motion-downweighted frames so `frame_accounting.json` can expose the cause.
- Added unit and CUDA-smoke coverage in `tests/test_resident_cuda_run.py`.
- Updated Phase 2 gate plan and algorithm source attribution.

## Real 200-Light Candidate Runs

### Naive Global Translation Candidate

- Output:
  `C:\glass_runs\phase2_s2_gate_128_motion_weighting\motion_t16_min005`
- Result:
  - completed
  - 193 integrated frames, 7 zero-weight frames
  - runtime: `24.7100` s
  - motion downweighted frames: `90`
- Interpretation:
  - rejected as a policy candidate
  - global translation MAD mixed different matrix orientation/trace clusters and placed the center near the full-frame wrapped transform family

### Cluster-Aware Translation Candidate

- Output:
  `C:\glass_runs\phase2_s2_gate_128_motion_weighting\motion_cluster_t16_min005`
- Outlier audit:
  `C:\glass_runs\phase2_s2_gate_128_motion_weighting\motion_cluster_t16_min005_outliers.json`
- Markdown:
  `C:\glass_runs\phase2_s2_gate_128_motion_weighting\motion_cluster_t16_min005_outliers.md`
- Scope:
  - same science/tuning settings as S2-Gate 119 `agr0p5`
  - 200-light M38 H-alpha benchmark
  - `translation_mad`
  - threshold sigma `16`
  - minimum multiplier `0.05`
  - power `2`
  - scale floor `1 px`
- Result:
  - completed
  - runtime: `18.6795` s
  - 193 integrated frames, 7 zero-weight frames
  - two motion clusters:
    - `trace_neg_det_pos`: 104 eligible frames
    - `trace_pos_det_pos`: 89 eligible frames
  - motion-downweighted frames: `1`
  - downweighted frame: `F000061`
  - triangle agreement downweighted frames: `73`
- Compare-outliers result:
  - target exceedance pixels: `599324`
  - Gate120 `agr0p5` baseline target exceedance pixels: `599340`
  - improvement: `16` pixels
  - tail p99: `0.0387044642`
  - negative tail fraction: `0.999993226`
- Interpretation:
  - not promotable
  - cluster-aware global motion outlier weighting is safe enough as opt-in infrastructure, but it does not materially fix the localized F000100-F000110 residual family from S2-Gate 127

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py -k "registration_motion_weighting or external_matrix_registration"
.\.venv\Scripts\ruff.exe check src\glass\engine\resident_cuda.py src\glass\cli.py tests\test_resident_cuda_run.py
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_128_motion_weighting\motion_t16_min005 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 28 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps audit --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158 --resident-triangle-grid-top-per-cell 2 --resident-triangle-nms-min-separation-px 96.0 --resident-triangle-agreement-action downweight --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-prefetch-refill-mode queued --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 8 --resident-calibration-streams 4 --resident-calibration-wave-frames 2 --resident-calibration-release-mode callback_queue --resident-star-catalog-deterministic --resident-triangle-min-agreement-score 0.5 --resident-triangle-agreement-rms-scale 200.0 --resident-registration-motion-weighting translation_mad --resident-registration-motion-threshold-sigma 16 --resident-registration-motion-min-weight 0.05 --resident-registration-motion-power 2 --resident-registration-motion-scale-floor-px 1.0
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_128_motion_weighting\motion_cluster_t16_min005 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 28 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps audit --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158 --resident-triangle-grid-top-per-cell 2 --resident-triangle-nms-min-separation-px 96.0 --resident-triangle-agreement-action downweight --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-prefetch-refill-mode queued --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 8 --resident-calibration-streams 4 --resident-calibration-wave-frames 2 --resident-calibration-release-mode callback_queue --resident-star-catalog-deterministic --resident-triangle-min-agreement-score 0.5 --resident-triangle-agreement-rms-scale 200.0 --resident-registration-motion-weighting translation_mad --resident-registration-motion-threshold-sigma 16 --resident-registration-motion-min-weight 0.05 --resident-registration-motion-power 2 --resident-registration-motion-scale-floor-px 1.0
.\.venv\Scripts\glass.exe compare-outliers --glass C:\glass_runs\phase2_s2_gate_128_motion_weighting\motion_cluster_t16_min005\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_128_motion_weighting\motion_cluster_t16_min005_outliers.json --markdown C:\glass_runs\phase2_s2_gate_128_motion_weighting\motion_cluster_t16_min005_outliers.md --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_128_motion_weighting\motion_cluster_t16_min005\integration\resident_coverage_map_H.fits --min-coverage 190 --ignore-border-px 16 --tail-percentile 99 --target-abs-diff 0.00042000063695013523 --tile-size 512 --top-tiles 16 --top-pixels 32 --edge-band-px 64
.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_128_doctor.json
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
```

## Test Results

- Focused tests: `3 passed`
- Full ruff: passed
- Full pytest: `339 passed in 19.92s`
- Native CUDA build: passed, `ninja: no work to do`

## CUDA

- CUDA available: yes
- CUDA wrapper importable: yes
- CUDA native extension loaded: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- Recommendation: cuda
- Doctor artifact:
  `runs/checkpoints/s2_gate_128_doctor.json`

## Known Limitations

- The policy is opt-in and defaults to `off`.
- It only uses global registration-matrix motion statistics; it does not use localized tile contribution evidence.
- The cluster-aware candidate downweighted only F000061 and did not materially reduce the S2-Gate 120 localized residual tail.
- The naive unclustered run is retained as negative evidence only and must not be used for promotion.

## Next Step

- S2-Gate 129 should use the S2-Gate 127 localized contribution evidence directly, for example via an explicit frame-family multiplier experiment or a local contribution-aware weighting audit, rather than relying on global registration-motion distance alone.

## Clean-Room Compliance

- Compliant.
- The policy uses only GLASS registration matrices, GLASS frame weights, GLASS artifacts, and user-generated reference comparison artifacts.
- No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or used.
- Original image directories were treated as read-only.
