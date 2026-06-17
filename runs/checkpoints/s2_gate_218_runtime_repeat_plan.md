# Resident Runtime Repeat Plan

- Label: `gate218_default`
- Cache state: `warm`
- Repeats: `3`
- Baseline repeat: `2`

## Run Commands

### gate218_default_repeat01

```powershell
glass run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_218_runtime_repeat\runs\gate218_default_repeat01 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 28 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps audit --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158 --resident-triangle-grid-top-per-cell 2 --resident-triangle-nms-min-separation-px 96.0 --resident-triangle-agreement-action downweight --resident-star-catalog-deterministic --resident-triangle-min-agreement-score 0.6 --resident-triangle-agreement-rms-scale 200.0
```

### gate218_default_repeat02

```powershell
glass run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_218_runtime_repeat\runs\gate218_default_repeat02 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 28 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps audit --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158 --resident-triangle-grid-top-per-cell 2 --resident-triangle-nms-min-separation-px 96.0 --resident-triangle-agreement-action downweight --resident-star-catalog-deterministic --resident-triangle-min-agreement-score 0.6 --resident-triangle-agreement-rms-scale 200.0
```

### gate218_default_repeat03

```powershell
glass run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_218_runtime_repeat\runs\gate218_default_repeat03 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 28 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps audit --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158 --resident-triangle-grid-top-per-cell 2 --resident-triangle-nms-min-separation-px 96.0 --resident-triangle-agreement-action downweight --resident-star-catalog-deterministic --resident-triangle-min-agreement-score 0.6 --resident-triangle-agreement-rms-scale 200.0
```

## Compare Command

```powershell
glass resident-runtime-compare --run gate218_default_repeat01=C:\glass_runs\phase2_s2_gate_218_runtime_repeat\runs\gate218_default_repeat01 --run gate218_default_repeat02=C:\glass_runs\phase2_s2_gate_218_runtime_repeat\runs\gate218_default_repeat02 --run gate218_default_repeat03=C:\glass_runs\phase2_s2_gate_218_runtime_repeat\runs\gate218_default_repeat03 --baseline-label gate218_default_repeat02 --out C:\glass_runs\phase2_s2_gate_218_runtime_repeat\runtime_compare.json --markdown C:\glass_runs\phase2_s2_gate_218_runtime_repeat\runtime_compare.md
```
