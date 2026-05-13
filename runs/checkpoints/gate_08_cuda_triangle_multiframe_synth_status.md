# Gate 08 CUDA triangle multiframe synthetic status

Date: 2026-05-13 14:37:46 +08:00

## Gate

Gate 08: Registration

## Completed

- Ran a full CLI chain on a new controlled synthetic dataset:
  synthetic data generation, metadata scan, planning, CUDA calibration, quality
  measurement, and `cuda_triangle` registration.
- Verified that `glass run --until-stage registration --registration-method
  cuda_triangle` writes a valid `registration_results.json`.
- Verified that the report command can consume the resulting registration
  artifact.

## Commands Run

```powershell
.\.venv\Scripts\glass.exe synthetic --out runs\gate_08_cuda_triangle_pipeline_synth_data --frames 12 --width 256 --height 256 --filter H --known-shift
.\.venv\Scripts\glass.exe scan --root runs\gate_08_cuda_triangle_pipeline_synth_data --out runs\gate_08_cuda_triangle_pipeline_synth_manifest.json
.\.venv\Scripts\glass.exe plan --manifest runs\gate_08_cuda_triangle_pipeline_synth_manifest.json --out runs\gate_08_cuda_triangle_pipeline_synth_plan.json
.\.venv\Scripts\glass.exe run --plan runs\gate_08_cuda_triangle_pipeline_synth_plan.json --out runs\gate_08_cuda_triangle_pipeline_synth_run --backend cuda --until-stage registration --registration-method cuda_triangle --registration-preview-max-dimension 512 --tile-size 128
.\.venv\Scripts\glass.exe report --run runs\gate_08_cuda_triangle_pipeline_synth_run --out runs\gate_08_cuda_triangle_pipeline_synth_run\report.html
```

## Test Results

- Synthetic scan: 21 frames total.
  - Bias: 3.
  - Dark: 3.
  - Flat: 3.
  - Light: 12.
  - Shape: 256x256.
- Plan executable: yes, with zero planner warnings.
- Run stages:
  - Calibration: ok, 0.223592100024689 s.
  - Quality: ok, 0.14073139999527484 s.
  - Registration: ok, 0.19979819998843595 s.
  - Total through registration: 0.5641217000083998 s.
- Registration results:
  - Method: `cuda_triangle`.
  - Reference frame: `F000010`.
  - Status counts: 11 ok, 1 reference.
  - Solution source counts: 12
    `cuda_triangle_descriptor_similarity_preview`.
  - First non-reference row: 21 inliers, 104/104 triangle descriptors,
    preview RMS 0.2182178944349289 px.
- Report generated at
  `runs\gate_08_cuda_triangle_pipeline_synth_run\report.html`.

## CUDA

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: available.

## Artifacts

Ignored run artifacts were written under:

- `runs\gate_08_cuda_triangle_pipeline_synth_data`
- `runs\gate_08_cuda_triangle_pipeline_synth_manifest.json`
- `runs\gate_08_cuda_triangle_pipeline_synth_plan.json`
- `runs\gate_08_cuda_triangle_pipeline_synth_run`

Tracked checkpoint:

- `runs\checkpoints\gate_08_cuda_triangle_multiframe_synth_status.md`

## Known Limitations

- This is a small synthetic validation, not the final 200-light real-data
  benchmark.
- Registration is still preview-based and uses the existing streaming warp path
  downstream; the full resident high-VRAM triangle descriptor path remains
  pending.
- Triangle descriptors are sufficient for this controlled dataset but remain
  weaker than a future polygon descriptor model for difficult real fields.

## Next Step

Bridge `cuda_triangle` into the high-VRAM resident path, first as a compact
catalog/descriptor bridge that keeps calibrated frames resident for matrix
application and integration, then replace remaining host catalog round trips
with resident descriptor primitives.

## Clean-room Compliance

Compliant. The validation used GLASS-generated synthetic FITS data and
GLASS-owned CUDA/Python code. No PixInsight/WBPP/PJSR source code was read,
copied, summarized, or modified.
