# S2-Gate 431 Status: Real 200-Light Auto-Grid Regression

## Gate

S2-Gate 431

## Scope

Substantive Phase 2 runtime-validation gate. This gate verifies that the
S2-Gate430 resident triangle auto-grid default transfers from the 16-frame
synthetic harness to the real M38 H 200-light dataset.

No release/default-promotion/report-only gate work was performed.

## Dataset

Plan:

- `C:\glass_runs\final_m38_h_200\glass_current_20260514_154556\processing_plan.json`

Frame counts from the plan:

- Light: 200
- Bias: 20
- Dark: 20
- Flat: 20
- Total: 260
- Shape: `9600x6422`

All frame paths referenced by the plan existed at validation time. Original
input directories were read-only from GLASS's perspective.

## Completed

- Ran the real 200-light M38 H dataset with current GLASS code and Gate430
  default auto-grid resident triangle registration.
- Did not pass `--resident-star-grid-cols`,
  `--resident-star-grid-rows`, or `--resident-triangle-grid-top-per-cell` for
  the formal auto-grid runs, proving the default path selected:
  - `triangle_catalog_grid_auto=True`;
  - `star_grid_cols=8`;
  - `star_grid_rows=8`;
  - `triangle_grid_top_per_cell=8`;
  - `star_catalog_deterministic=True`;
  - `triangle_catalog_batch=True`.
- Ran a same-code explicit `24x16` grid control to separate default-route
  effects from disk/cache/output-write variation.
- Generated GLASS report for the formal repeat run.
- Generated GLASS-vs-GLASS compare reports:
  - auto-repeat vs same-code explicit 24x16;
  - auto-repeat vs historical current run.
- Generated repo-local summary JSON:
  - `runs/checkpoints/s2_gate_431_real_200_regression_summary.json`

## Commands Run

Formal first auto-grid run:

```powershell
.\.venv\Scripts\python.exe -m glass.cli run --plan "C:\glass_runs\final_m38_h_200\glass_current_20260514_154556\processing_plan.json" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate431_auto_grid_top8_20260619" --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit
```

Same-code explicit grid control:

```powershell
.\.venv\Scripts\python.exe -m glass.cli run --plan "C:\glass_runs\final_m38_h_200\glass_current_20260514_154556\processing_plan.json" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate431_explicit_grid24x16_20260619" --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-star-grid-cols 24 --resident-star-grid-rows 16
```

Formal repeat auto-grid run used for Gate431 metrics:

```powershell
.\.venv\Scripts\python.exe -m glass.cli run --plan "C:\glass_runs\final_m38_h_200\glass_current_20260514_154556\processing_plan.json" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate431_auto_grid_top8_repeat_20260619" --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit
```

Report:

```powershell
.\.venv\Scripts\python.exe -m glass.cli report --run "C:\glass_runs\final_m38_h_200\glass_s2_gate431_auto_grid_top8_repeat_20260619" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate431_auto_grid_top8_repeat_20260619\report.html"
```

Compare auto-repeat vs explicit 24x16:

```powershell
.\.venv\Scripts\python.exe -m glass.cli compare --glass "C:\glass_runs\final_m38_h_200\glass_s2_gate431_auto_grid_top8_repeat_20260619\integration\resident_master_H.fits" --reference "C:\glass_runs\final_m38_h_200\glass_s2_gate431_explicit_grid24x16_20260619\integration\resident_master_H.fits" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate431_auto_repeat_vs_explicit24x16_compare.html" --glass-time-seconds 28.351825499994447 --reference-time-seconds 34.812349899992114 --glass-label "Gate431 auto 8x8 top8 repeat" --reference-label "Gate431 explicit 24x16"
```

Compare auto-repeat vs historical current:

```powershell
.\.venv\Scripts\python.exe -m glass.cli compare --glass "C:\glass_runs\final_m38_h_200\glass_s2_gate431_auto_grid_top8_repeat_20260619\integration\resident_master_H.fits" --reference "C:\glass_runs\final_m38_h_200\glass_current_20260514_154556\integration\resident_master_H.fits" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate431_auto_repeat_vs_old_current_compare.html" --glass-time-seconds 28.351825499994447 --reference-time-seconds 31.516450299997814 --glass-label "Gate431 auto 8x8 top8 repeat" --reference-label "Historical current 24x16"
```

Other commands:

```powershell
.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_431_cuda_doctor.json
```

## Runtime Results

| Run | Total | Light read/upload/calibrate | Registration+warp | Moving catalog | Integration | Output write |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Gate431 auto repeat 8x8/top8 | 28.351825 s | 17.248630 s | 1.640994 s | 0.983094 s | 0.310590 s | 2.442102 s |
| Gate431 auto first 8x8/top8 | 41.933876 s | 27.643468 s | 1.642395 s | 0.982756 s | 0.369516 s | 4.702399 s |
| Gate431 explicit 24x16 | 34.812350 s | 22.169482 s | 1.801728 s | 1.145424 s | 0.301618 s | 3.236944 s |
| Historical current 24x16 | 31.516450 s | 16.504704 s | 11.223865 s | 5.370839 s | 0.295160 s | 0.847980 s |

Interpretation:

- The first auto run had slower disk/upload and output-write timing.
- The repeat run demonstrates the auto-grid default is faster than both the
  same-code explicit 24x16 control and the historical current run.
- Registration/catalog speedup transfers to real data:
  - historical current `resident_registration_warp`: `11.223865 s`;
  - Gate431 auto repeat: `1.640994 s`;
  - historical current `triangle_moving_catalog`: `5.370839 s`;
  - Gate431 auto repeat: `0.983094 s`.

## Frame Acceptance

| Run | Status counts |
| --- | --- |
| Gate431 auto repeat | `199 ok`, `1 reference` |
| Gate431 explicit 24x16 | `199 ok`, `1 reference` |
| Historical current | `192 ok`, `7 excluded`, `1 reference` |

The acceptance-set difference is real and becomes the next scientific parity
target. Gate431 records it instead of hiding it.

## Numerical Compare

Auto-repeat vs same-code explicit 24x16:

- Shape match: true.
- p50/p90/p99 absolute delta: `1.7867` / `4.5519` / `15.6943` ADU.
- RMS difference: `16.1538`.
- Relative RMS difference: `0.04869`.
- Speedup vs explicit 24x16: `1.22787x`.

Auto-repeat vs historical current:

- Shape match: true.
- p50/p90/p99 absolute delta: `2.3856` / `5.9828` / `19.0665` ADU.
- RMS difference: `23.2823`.
- Relative RMS difference: `0.07014`.
- Speedup vs historical current: `1.11162x`.

Historical WBPP black-box timing:

- Recorded WBPP time: `1092.541 s`.
- Gate431 auto-repeat speedup vs historical WBPP timing: `38.53512x`.
- The historical WBPP XISF reference file is not present at the expected path
  in this environment, so Gate431 did not regenerate the WBPP output compare.

## Output Artifacts

Formal Gate431 run:

- `C:\glass_runs\final_m38_h_200\glass_s2_gate431_auto_grid_top8_repeat_20260619`
- `C:\glass_runs\final_m38_h_200\glass_s2_gate431_auto_grid_top8_repeat_20260619\integration\resident_master_H.fits`
- `C:\glass_runs\final_m38_h_200\glass_s2_gate431_auto_grid_top8_repeat_20260619\integration\resident_coverage_map_H.fits`
- `C:\glass_runs\final_m38_h_200\glass_s2_gate431_auto_grid_top8_repeat_20260619\integration\resident_low_rejection_map_H.fits`
- `C:\glass_runs\final_m38_h_200\glass_s2_gate431_auto_grid_top8_repeat_20260619\integration\resident_high_rejection_map_H.fits`
- `C:\glass_runs\final_m38_h_200\glass_s2_gate431_auto_grid_top8_repeat_20260619\report.html`

Compare reports:

- `C:\glass_runs\final_m38_h_200\glass_s2_gate431_auto_repeat_vs_explicit24x16_compare.html`
- `C:\glass_runs\final_m38_h_200\glass_s2_gate431_auto_repeat_vs_explicit24x16_compare.json`
- `C:\glass_runs\final_m38_h_200\glass_s2_gate431_auto_repeat_vs_old_current_compare.html`
- `C:\glass_runs\final_m38_h_200\glass_s2_gate431_auto_repeat_vs_old_current_compare.json`

Repo-local summary:

- `runs/checkpoints/s2_gate_431_real_200_regression_summary.json`

## CUDA Status

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- Native extension loaded: yes

Doctor artifact:

- `runs/checkpoints/s2_gate_431_cuda_doctor.json`

## Known Limitations

- The historical WBPP reference XISF is not currently available at the recorded
  path, so direct WBPP compare was not regenerated.
- Local normalization remains disabled.
- The accepted-frame set differs from the historical current run.
- Strict synthetic same-pre-rejection parity remains a separate blocker from
  Gate430.
- Full-frame resident mode is appropriate for this 96 GiB GPU and this dataset;
  this gate does not validate out-of-core behavior on smaller GPUs.

## Next Gate

S2-Gate 432 should target accepted-frame parity and resident warp/rejection
value parity:

- record accepted/excluded frame IDs on real M38 200-light data;
- explain or reproduce the historical/WBPP-like excluded-frame set;
- reduce strict synthetic same-pre-rejection deltas if changing warp/rejection;
- rerun full pytest and checkpoint before moving on.

## Clean-Room Compliance

Compliant.

- No PixInsight or WBPP/PJSR source was read, copied, summarized, or reworked.
- The historical WBPP timing came from prior user-generated black-box evidence.
- No user input image directory was modified.
- No release or package publication action was performed.
