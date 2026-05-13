# Gate 09 Tile Vs Resident Matrix Compare Status

Gate: 09 - matrix warp correctness and speed validation

Date: 2026-05-13

## Completed content

- Used the successful 12-light M38 tile-mode astroalign matrix set from
  `glass_tile_astroalign_subset12_ref_light001_flat005`.
- Ran tile-mode matrix warp and integration directly from the existing
  `registration_results.json` without repeating calibration/quality/registration.
- Compared tile-mode CPU/tile matrix-warp integration against resident CUDA
  `external_matrix` integration using the same registration matrices and the
  same flat-floor calibration policy.
- Updated `docs/validation.md` with the real-data matrix-warp comparison anchor.

## Commands run

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Result before this comparison checkpoint: 119 passed.

```powershell
@'
from pathlib import Path
from time import perf_counter
import json
from glass.engine.warp import warp_registered_frames
from glass.engine.integration import integrate_registered_frames
run = Path(r"C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset12_ref_light001_flat005")
plan = Path(r"C:\glass_runs\final_m38_h_200\glass_resident_ncc_stride4_subset12\processing_plan.json")
timing = {"command": "direct_tile_warp_integration", "stages": []}
for stage, fn in [
    ("warp", lambda: warp_registered_frames(run, tile_size=1024)),
    ("integration", lambda: integrate_registered_frames(run, plan_path=plan, backend="cuda", tile_size=1024, weighting_override="none", rejection_override="none")),
]:
    t0 = perf_counter()
    result = fn()
    timing["stages"].append({"stage": stage, "elapsed_s": perf_counter() - t0, "status": "ok"})
    print(stage, "ok")
timing["total_elapsed_s"] = sum(item["elapsed_s"] for item in timing["stages"])
(run / "direct_tile_warp_integration_timing.json").write_text(json.dumps(timing, indent=2), encoding="utf-8")
'@ | .\.venv\Scripts\python.exe -
```

Result: passed.

Tile direct timing:

- warp: 70.2199 s
- integration: 10.5823 s
- direct tile warp+integration total: 80.8022 s

Tile full reference timing used for comparison:

- tile calibration + quality + astroalign registration: 177.7369 s
- direct tile warp + integration: 80.8022 s
- total tile reference: 258.5391 s

Resident CUDA external-matrix timing:

- resident calibration + registration matrix application + integration: 14.4702 s
- resident registration mean per frame: 0.00711 s
- resident integration: 0.0753 s

```powershell
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\final_m38_h_200\glass_resident_external_matrix_astroalign_subset12_flat005\integration\resident_master_H.fits --reference C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset12_ref_light001_flat005\integration\master_H.fits --out C:\glass_runs\final_m38_h_200\resident_external_matrix_vs_tile_astroalign_subset12_compare.html --glass-label resident_cuda_external_matrix --reference-label tile_astroalign_cpu_warp --glass-time-seconds 14.470209099992644 --reference-time-seconds 258.53909080004087
```

Result: passed.

Compare metrics:

- shape match: true
- median absolute difference: 0.001812
- p90 absolute difference: 0.005798
- p99 absolute difference: 0.014648
- p99.9 absolute difference: 0.077774
- RMS difference: 0.059239
- relative RMS difference: 0.0001667
- robust fit scale: 1.00000013
- robust fit offset: -0.00000749
- resident CUDA speedup vs tile reference: 17.867x

## CUDA availability

CUDA was available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB

## Artifacts

- `C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset12_ref_light001_flat005\warp_results.json`
- `C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset12_ref_light001_flat005\integration\master_H.fits`
- `C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset12_ref_light001_flat005\direct_tile_warp_integration_timing.json`
- `C:\glass_runs\final_m38_h_200\glass_resident_external_matrix_astroalign_subset12_flat005\integration\resident_master_H.fits`
- `C:\glass_runs\final_m38_h_200\resident_external_matrix_vs_tile_astroalign_subset12_compare.json`
- `C:\glass_runs\final_m38_h_200\resident_external_matrix_vs_tile_astroalign_subset12_compare.html`

## Known limitations

- This comparison validates 12 real M38 light frames, not the final 200-light benchmark.
- The matrix source is still open-source astroalign running on CPU/tile-mode output.
- Differences are small in robust statistics but edge/coverage and interpolation details still produce larger max absolute differences.
- Local Normalization and rejection were disabled for this specific correctness comparison.

## Next step

Scale the same validation pattern to a larger subset, then the final 200-light run: generate or reuse accepted matrices, run resident CUDA `external_matrix`, and compare against tile/WBPP reference outputs with timing and image-difference reports.

## Clean-room compliance

This work used GLASS-owned code, user-provided M38 data, and open-source astroalign as an external reference. No PixInsight/WBPP/PJSR official source code was read, copied, summarized, or modified.
